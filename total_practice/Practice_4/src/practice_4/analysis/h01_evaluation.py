from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import xgboost as xgb

from practice_4.analysis.metrics import calculate_metrics
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
    inverse_scale_load,
    transform_causal,
)
from practice_4.models.lstm_model import MultivariateLSTM, predict_single_window
from practice_4.models.var_model import predict_var_one_step
from practice_4.runtime import sha256_file, write_json


def run_locked_test_walk_forward(
    root: Path,
    config: dict[str, Any],
    artifacts_dir: Path,
) -> dict[str, Any]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    ds_cfg = config["dataset"]
    feat_cfg = config["features"]
    split = json.loads((root / "datasets/processed/split_manifest.json").read_text(encoding="utf-8"))
    scaler = json.loads((root / "runs/v2/s4_prep/scaler.json").read_text(encoding="utf-8"))
    test_start = int(split["splits"]["test"]["start_row"])
    test_end = int(split["splits"]["test"]["end_row"])

    prepared_prefix = pd.read_csv(root / "datasets/processed/prepared_hourly.csv")
    prepared_prefix["timestamp_utc"] = pd.to_datetime(prepared_prefix["timestamp_utc"], utc=True)
    if len(prepared_prefix) != test_start:
        raise ValueError(f"Prepared prefix length {len(prepared_prefix)} != test_start {test_start}")

    canonical_full = pd.read_csv(root / "datasets/processed/canonical_hourly.csv")
    canonical_full["timestamp_utc"] = pd.to_datetime(canonical_full["timestamp_utc"], utc=True)
    test_raw_df = canonical_full.iloc[test_start : test_end + 1].reset_index(drop=True)

    stream_state = CausalStreamState(
        last_values={
            "load": float(prepared_prefix["load_input"].iloc[-1]),
            "temp": float(prepared_prefix["temp_input"].iloc[-1]),
            "humidity": float(prepared_prefix["humidity_input"].iloc[-1]),
            "wind_speed": float(prepared_prefix["wind_speed_input"].iloc[-1]),
        },
        missing_runs={"load": 0, "temp": 0, "humidity": 0, "wind_speed": 0},
        last_timestamp=prepared_prefix["timestamp_utc"].iloc[-1].isoformat(),
    )

    with np.load(root / "runs/v2/s5_var/artifacts/var_model.npz", allow_pickle=False) as var_npz:
        var_coefs = var_npz["coefs"].copy()
        var_intercept = var_npz["intercept"].copy()
        var_p = int(var_npz["p"])
        var_d = int(var_npz["diff_order"])

    xgb_meta = json.loads((root / "runs/v2/s6_xgb/artifacts/xgb_metrics.json").read_text(encoding="utf-8"))
    xgb_best_name = xgb_meta["best_subset"]
    subsets = xgb_ablation_subsets()
    xgb_boosters: dict[str, tuple[xgb.Booster, list[int], list[str]]] = {}
    for label, subset_key in (("XGB_best", xgb_best_name), ("XGB_4var", "XGB_24h_4var")):
        b = xgb.Booster()
        b.load_model(root / "runs/v2/s6_xgb/artifacts" / f"{subset_key}.json")
        xgb_boosters[label] = (b, feature_subset_indices(subsets[subset_key]), subsets[subset_key])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    lstm_models: dict[str, tuple[MultivariateLSTM, dict[str, Any]]] = {}
    for label, stem in (("LSTM_best", "lstm_best"), ("LSTM_core", "lstm_core")):
        arch = json.loads((root / "runs/v2/s7_lstm/artifacts" / f"{stem}_arch.json").read_text(encoding="utf-8"))
        net = MultivariateLSTM(
            input_size=int(arch["input_size"]),
            hidden1=int(arch["hidden1"]),
            hidden2=int(arch["hidden2"]),
            dropout=float(arch["dropout"]),
            future_cal_dim=int(arch.get("future_cal_dim", 0)),
        ).to(device)
        net.load_state_dict(
            torch.load(root / "runs/v2/s7_lstm/artifacts" / f"{stem}.pt", map_location=device, weights_only=True)
        )
        net.eval()
        lstm_models[label] = (net, arch)

    model_hashes_before = {
        "var": sha256_file(root / "runs/v2/s5_var/artifacts/var_model.npz"),
        "xgb_best": sha256_file(root / "runs/v2/s6_xgb/artifacts" / f"{xgb_best_name}.json"),
        "lstm_best": sha256_file(root / "runs/v2/s7_lstm/artifacts/lstm_best.pt"),
    }

    hist_df = prepared_prefix.iloc[-CONTEXT_HOURS:].copy().reset_index(drop=True)
    scaled_buf = list(hist_df[SCALED_VARS].to_numpy(dtype=np.float64))
    work_buf = list(hist_df[WORK_VARS].to_numpy(dtype=np.float64))
    cal_buf = list(hist_df[CALENDAR_COLS].to_numpy(dtype=np.float64))
    ts_buf = list(hist_df["timestamp_utc"])

    model_names = ("persistence", "seasonal24", "seasonal168", "VAR", "XGB_best", "XGB_4var", "LSTM_best", "LSTM_core")
    preds_store: dict[str, list[float]] = {m: [] for m in model_names}
    truths_store: list[float] = []
    prediction_rows = []
    diagnostic_rows = []
    missing_excluded = 0
    input_excluded = 0

    for step in range(len(test_raw_df)):
        row_df = test_raw_df.iloc[[step]].copy()
        target_ts = pd.Timestamp(row_df["timestamp_utc"].iloc[0])
        origin_ts = ts_buf[-1]
        if target_ts != origin_ts + pd.Timedelta(hours=1):
            raise ValueError(f"Chronology mismatch at test step {step}: {origin_ts} -> {target_ts}")

        # Calendar of target_ts is deterministically known at origin_ts without observing load/weather
        from practice_4.data.preprocessing import compute_calendar_features

        target_cal = compute_calendar_features(
            pd.DatetimeIndex([target_ts]),
            tz_local=ds_cfg["timezone_local"],
            country_code=ds_cfg["country_holiday_code"],
        )[CALENDAR_COLS].to_numpy(dtype=np.float64)[0]

        ctx_scaled = np.asarray(scaled_buf[-CONTEXT_HOURS:], dtype=np.float64)
        ctx_work = np.asarray(work_buf[-CONTEXT_HOURS:], dtype=np.float64)
        ctx_cal = np.asarray(cal_buf[-CONTEXT_HOURS:], dtype=np.float64)
        context_valid = bool(np.isfinite(ctx_scaled).all() and np.isfinite(ctx_work).all())

        step_preds: dict[str, float] | None = None
        if context_valid:
            arr_scaled = np.vstack([ctx_scaled, np.zeros((1, 4), dtype=np.float64)])
            arr_work = np.vstack([ctx_work, np.zeros((1, 4), dtype=np.float64)])
            arr_cal = np.vstack([ctx_cal, target_cal[None, :]])
            _, _, xgb_full_vec = build_feature_row_from_arrays(
                arr_scaled,
                arr_work,
                arr_cal,
                CONTEXT_HOURS,
                hdd_base_c=float(feat_cfg["hdd_base_c"]),
                cdd_base_c=float(feat_cfg["cdd_base_c"]),
            )

            p_pers = float(ctx_work[-1, 0])
            p_s24 = float(ctx_work[-24, 0])
            p_s168 = float(ctx_work[-168, 0])

            need = var_p + var_d
            var_s = predict_var_one_step(ctx_scaled[-need:], var_coefs, var_intercept, var_d)[0]
            p_var = float(inverse_scale_load(np.array([var_s]), scaler)[0])

            step_preds = {
                "persistence": p_pers,
                "seasonal24": p_s24,
                "seasonal168": p_s168,
                "VAR": p_var,
            }

            for label, (booster, col_idx, feat_names) in xgb_boosters.items():
                vec = xgb_full_vec[col_idx].reshape(1, -1)
                dmat = xgb.DMatrix(vec, feature_names=feat_names)
                step_preds[label] = float(booster.predict(dmat)[0])

            full_seq_ctx = np.concatenate([ctx_scaled, ctx_cal], axis=1).astype(np.float32)
            tcal_f32 = target_cal.astype(np.float32)
            for label, (net, arch) in lstm_models.items():
                wlen = int(arch["window_len"])
                cidx = arch["col_indices"]
                fdim = int(arch.get("future_cal_dim", 0))
                win = full_seq_ctx[-wlen:, cidx]
                if win.shape[0] != wlen:
                    raise ValueError(f"Window length mismatch for {label}: {win.shape[0]} != {wlen}")
                pred_s = predict_single_window(net, win, device, future_cal=tcal_f32 if fdim > 0 else None)
                step_preds[label] = float(inverse_scale_load(np.array([pred_s]), scaler)[0])

        # Reveal observed row strictly AFTER forecasts are issued
        observed = bool(row_df["load_observed"].iloc[0])
        raw_truth = float(row_df["load"].iloc[0]) if observed else float("nan")
        dst_flag = bool(row_df["dst_fallback_split"].iloc[0])

        if not observed or not np.isfinite(raw_truth):
            missing_excluded += 1
        elif not context_valid or step_preds is None:
            input_excluded += 1
        else:
            truths_store.append(raw_truth)
            diagnostic_rows.append(
                {
                    "target_row": test_start + step,
                    "origin": origin_ts.isoformat(),
                    "target_timestamp": target_ts.isoformat(),
                    "y_true": raw_truth,
                    "origin_temp": float(ctx_work[-1, 1]),
                    "origin_humidity": float(ctx_work[-1, 2]),
                    "origin_wind_speed": float(ctx_work[-1, 3]),
                    "is_holiday": float(target_cal[CALENDAR_COLS.index("is_holiday")]),
                    "dst_fallback_split": dst_flag,
                }
            )
            for m in model_names:
                val = step_preds[m]
                if not np.isfinite(val):
                    raise ValueError(f"Non-finite forecast for {m} at step {step}")
                preds_store[m].append(val)
                prediction_rows.append(
                    {
                        "schema_version": "2",
                        "model": m,
                        "origin": origin_ts.isoformat(),
                        "target_timestamp": target_ts.isoformat(),
                        "y_true": raw_truth,
                        "y_pred": val,
                        "split": "test",
                    }
                )

        transformed_row, _ = transform_causal(
            row_df,
            scaler,
            stream_state,
            tz_local=ds_cfg["timezone_local"],
            country_code=ds_cfg["country_holiday_code"],
        )
        scaled_buf.append(transformed_row[SCALED_VARS].to_numpy(dtype=np.float64)[0])
        work_buf.append(transformed_row[WORK_VARS].to_numpy(dtype=np.float64)[0])
        cal_buf.append(transformed_row[CALENDAR_COLS].to_numpy(dtype=np.float64)[0])
        ts_buf.append(target_ts)
        if len(scaled_buf) > CONTEXT_HOURS + 10:
            scaled_buf.pop(0)
            work_buf.pop(0)
            cal_buf.pop(0)
            ts_buf.pop(0)

    model_hashes_after = {
        "var": sha256_file(root / "runs/v2/s5_var/artifacts/var_model.npz"),
        "xgb_best": sha256_file(root / "runs/v2/s6_xgb/artifacts" / f"{xgb_best_name}.json"),
        "lstm_best": sha256_file(root / "runs/v2/s7_lstm/artifacts/lstm_best.pt"),
    }
    if model_hashes_before != model_hashes_after:
        raise ValueError("Locked model artifacts changed during walk-forward evaluation")

    n_considered = len(test_raw_df)
    n_scored = len(truths_store)
    if n_scored + missing_excluded + input_excluded != n_considered:
        raise ValueError("Test count conservation failed")

    metrics_summary = {
        m: calculate_metrics(truths_store, preds_store[m], missing_excluded, input_excluded)
        for m in model_names
    }
    pred_df = pd.DataFrame(prediction_rows)
    diag_df = pd.DataFrame(diagnostic_rows)
    metrics_rows = [
        {"model": m, **metrics_summary[m]}
        for m in model_names
    ]
    metrics_df = pd.DataFrame(metrics_rows).sort_values("rmse_kw").reset_index(drop=True)

    pred_df.to_csv(artifacts_dir / "test_predictions.csv", index=False)
    diag_df.to_csv(artifacts_dir / "diagnostic_context.csv", index=False)
    metrics_df.to_csv(artifacts_dir / "test_metrics.csv", index=False)

    (root / "outputs/predictions").mkdir(parents=True, exist_ok=True)
    (root / "outputs/tables").mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(root / "outputs/predictions/test_predictions.csv", index=False)
    metrics_df.to_csv(root / "outputs/tables/test_metrics.csv", index=False)

    manifest = {
        "schema_version": "2",
        "stage_id": "S8",
        "counts": {
            "n_considered": n_considered,
            "n_scored": n_scored,
            "n_missing_excluded": missing_excluded,
            "n_input_excluded": input_excluded,
        },
        "model_hashes": model_hashes_before,
        "xgb_best_subset": xgb_best_name,
        "xgb_4var_subset": "XGB_24h_4var",
        "lstm_best_variant": lstm_models["LSTM_best"][1]["variant"],
        "var_spec": {"p": var_p, "d": var_d},
        "metrics": metrics_summary,
    }
    write_json(artifacts_dir / "evaluation_manifest.json", manifest)
    return manifest
