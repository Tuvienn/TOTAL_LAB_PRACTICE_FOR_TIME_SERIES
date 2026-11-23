from __future__ import annotations

import numpy as np
import pandas as pd

from practice_4.data.integration import (
    CANONICAL_COLUMNS,
    build_weighted_weather,
    uci_local_to_utc_hourly,
)
from practice_4.runtime import PRACTICE_ROOT, load_config, read_file_map


def test_s2_synthetic_dst_spring_and_fall_and_weather_anomaly():
    times_spring = pd.date_range("2012-03-25 00:15:00", periods=16, freq="15min")
    df_spring = pd.DataFrame(
        {
            "ts": times_spring.strftime("%Y-%m-%d %H:%M:%S"),
            "MT_001": [100.0] * 4 + [0.0] * 4 + [120.0] * 4 + [130.0] * 4,
        }
    )
    out_spring, _ = uci_local_to_utc_hourly(
        df_spring,
        tz_local="Europe/Lisbon",
        start_utc="2012-03-25T00:00:00+00:00",
        end_utc="2012-03-25T02:00:00+00:00",
        stable_client_filter=False,
    )
    assert len(out_spring) == 3
    assert np.allclose(out_spring["load"].to_numpy(), [100.0, 120.0, 130.0])

    times_fall = pd.date_range("2012-10-28 00:15:00", periods=12, freq="15min")
    df_fall = pd.DataFrame(
        {
            "ts": times_fall.strftime("%Y-%m-%d %H:%M:%S"),
            "MT_001": [100.0] * 4 + [240.0] * 4 + [90.0] * 4,
        }
    )
    out_fall, det_fall = uci_local_to_utc_hourly(
        df_fall,
        tz_local="Europe/Lisbon",
        start_utc="2012-10-27T23:00:00+00:00",
        end_utc="2012-10-28T02:00:00+00:00",
        stable_client_filter=False,
    )
    assert len(out_fall) == 4
    assert det_fall["dst_fallback_split_hours"] == 2
    assert np.allclose(out_fall["load"].to_numpy(), [100.0, 120.0, 120.0, 90.0])
    assert list(out_fall["dst_fallback_split"]) == [False, True, True, False]

    utc_idx = pd.date_range("2012-01-01T00:00:00Z", periods=2, freq="h")
    w_synth = pd.DataFrame(
        {
            "timestamp_utc": [utc_idx[0], utc_idx[1], utc_idx[0], utc_idx[1]],
            "city_name": ["Lisbon", "Lisbon", "Porto", "Porto"],
            "weight": [0.6, 0.6, 0.4, 0.4],
            "temp_c": [10.0, 0.0, 20.0, 15.0],
            "humidity": [50.0, 0.0, 80.0, 60.0],
            "wind_speed": [5.0, 133.0, 10.0, 5.0],
        }
    )
    agg, wdet = build_weighted_weather(w_synth, utc_idx, load_config()["anomaly_bounds"])
    assert np.isclose(agg["temp"].iloc[0], 14.0)
    assert wdet["canonical_anomaly_hours"] == 1
    assert list(agg["weather_physical_anomaly"]) == [False, True]


def test_s2_real_canonical_contract():
    canonical_path = PRACTICE_ROOT / "datasets/processed/canonical_hourly.csv"
    assert canonical_path.exists()
    df = pd.read_csv(canonical_path)
    assert list(df.columns) == CANONICAL_COLUMNS
    ts = pd.to_datetime(df["timestamp_utc"], utc=True)
    assert ts.is_monotonic_increasing and ts.is_unique
    assert ((ts[1:].to_numpy() - ts[:-1].to_numpy()) == np.timedelta64(1, "h")).all()
    assert len(df) == 26304
    assert df["load_observed"].all()
    assert (df["load"] > 0).all()
    assert df[["temp", "humidity", "wind_speed"]].notna().all().all()
    assert (PRACTICE_ROOT / "docs/results/data_contract.md").exists()

    fmap = {r["path"]: r for r in read_file_map()}
    assert fmap["datasets/processed/canonical_hourly.csv"]["existence"] == "EXISTING"
