from __future__ import annotations

import json

import numpy as np
import pandas as pd

from practice_4.data.features import (
    CONTEXT_HOURS,
    XGB_FULL_FEATURES,
    build_feature_row_from_arrays,
    feature_subset_indices,
    xgb_ablation_subsets,
)
from practice_4.data.preprocessing import (
    CALENDAR_COLS,
    CausalStreamState,
    SCALED_VARS,
    WORK_VARS,
    fit_scaler_on_train,
    inverse_scale_load,
    transform_causal,
)
from practice_4.runtime import PRACTICE_ROOT, load_config, read_file_map


def test_s4_anti_leakage_future_perturbation_and_calendar():
    cfg = load_config()
    n = 260
    ts = pd.date_range("2012-01-01T00:00:00Z", periods=n, freq="h")
    rng = np.random.default_rng(7)
    df = pd.DataFrame(
        {
            "timestamp_utc": ts,
            "load": 100000.0 + np.arange(n, dtype=np.float64) * 50.0,
            "temp": 15.0 + 5.0 * np.sin(np.arange(n) / 12.0),
            "humidity": 60.0 + rng.normal(scale=2.0, size=n),
            "wind_speed": 3.0 + np.abs(rng.normal(scale=0.5, size=n)),
            "load_observed": True,
            "dst_fallback_split": False,
            "weather_physical_anomaly": False,
        }
    )
    df.loc[50, "wind_speed"] = 133.0
    scaler = fit_scaler_on_train(df.iloc[:200], cfg, {"synthetic": "ok"})
    prep1, filled1 = transform_causal(df, scaler, CausalStreamState.empty(), "Europe/Lisbon", "PT")
    assert filled1["wind_speed"] == 1
    assert prep1.loc[50, "wind_speed_input"] == prep1.loc[49, "wind_speed_input"]

    df_mut = df.copy()
    target_row = 210
    df_mut.loc[target_row:, "load"] = 9999999.0
    df_mut.loc[target_row:, "temp"] = 45.0
    df_mut.loc[target_row:, "humidity"] = 99.0
    df_mut.loc[target_row:, "wind_speed"] = 25.0
    prep2, _ = transform_causal(df_mut, scaler, CausalStreamState.empty(), "Europe/Lisbon", "PT")

    s1, c1, x1 = build_feature_row_from_arrays(
        prep1[SCALED_VARS].to_numpy(), prep1[WORK_VARS].to_numpy(), prep1[CALENDAR_COLS].to_numpy(), target_row
    )
    s2, c2, x2 = build_feature_row_from_arrays(
        prep2[SCALED_VARS].to_numpy(), prep2[WORK_VARS].to_numpy(), prep2[CALENDAR_COLS].to_numpy(), target_row
    )
    assert np.array_equal(s1, s2), "LSTM core leaked target/future observations"
    assert np.array_equal(c1, c2), "LSTM calendar leaked target/future observations"
    assert np.array_equal(x1, x2), "XGB features leaked target/future observations"

    # Strict 24h window invariance for XGB_24h_4var (must not read before t-23)
    df_past_mut = df.copy()
    df_past_mut.loc[: target_row - 25, "load"] = 8888888.0
    df_past_mut.loc[: target_row - 25, "temp"] = 40.0
    prep_past, _ = transform_causal(df_past_mut, scaler, CausalStreamState.empty(), "Europe/Lisbon", "PT")
    _, _, x_past = build_feature_row_from_arrays(
        prep_past[SCALED_VARS].to_numpy(),
        prep_past[WORK_VARS].to_numpy(),
        prep_past[CALENDAR_COLS].to_numpy(),
        target_row,
    )
    subsets = xgb_ablation_subsets()
    idx_24h = feature_subset_indices(subsets["XGB_24h_4var"])
    assert np.array_equal(x1[idx_24h], x_past[idx_24h]), "XGB_24h_4var leaked observations older than 24h"
    assert set(subsets["XGB_load_only"]) < set(subsets["XGB_load_weather"]) < set(subsets["XGB_full"])
    assert set(subsets["XGB_load_only"]) < set(subsets["XGB_load_calendar"]) < set(subsets["XGB_full"])
    assert set(subsets["XGB_24h_4var"]) < set(subsets["XGB_load_weather"])

    roundtrip = inverse_scale_load(prep1["load_scaled"].to_numpy(), scaler)
    assert np.max(np.abs(roundtrip - prep1["load_input"].to_numpy())) < 1e-8


def test_s4_real_materialized_inputs_and_shapes():
    npz_path = PRACTICE_ROOT / "datasets/processed/model_inputs.npz"
    origins_path = PRACTICE_ROOT / "datasets/processed/origin_manifest.csv"
    scaler_path = PRACTICE_ROOT / "runs/v2/s4_prep/scaler.json"
    assert npz_path.exists() and origins_path.exists() and scaler_path.exists()

    origins = pd.read_csv(origins_path)
    split = json.loads((PRACTICE_ROOT / "datasets/processed/split_manifest.json").read_text(encoding="utf-8"))
    val_end = split["splits"]["validation"]["end_row"]
    assert origins["target_row"].max() == val_end, "Test rows leaked into S4 origins"

    with np.load(npz_path, allow_pickle=False) as data:
        assert int(data["schema_version"]) == 2
        n_elig = int(origins["eligible"].sum())
        assert data["x_lstm_core"].shape == (n_elig, 24, 4)
        assert data["x_lstm_cal"].shape == (n_elig, 24, 13)
        assert data["target_cal"].shape == (n_elig, 9)
        assert data["x_xgb"].shape == (n_elig, len(XGB_FULL_FEATURES))
        assert data["y_true"].shape == (n_elig,)
        assert data["var_train_levels"].shape == (split["splits"]["train"]["row_count"], 4)
        assert np.isfinite(data["x_xgb"]).all()
        assert np.isfinite(data["x_lstm_cal"]).all()
        assert np.isfinite(data["var_train_levels"]).all()

    subsets = xgb_ablation_subsets()
    assert len(subsets["XGB_full"]) == len(XGB_FULL_FEATURES)
    fmap = {r["path"]: r for r in read_file_map()}
    assert fmap["datasets/processed/model_inputs.npz"]["existence"] == "EXISTING"
