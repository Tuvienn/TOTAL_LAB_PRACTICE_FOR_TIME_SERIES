from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import holidays as pyholidays
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


BASE_VARS = ["load", "temp", "humidity", "wind_speed"]
WORK_VARS = ["load_input", "temp_input", "humidity_input", "wind_speed_input"]
SCALED_VARS = ["load_scaled", "temp_scaled", "humidity_scaled", "wind_speed_scaled"]
CALENDAR_COLS = [
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "doy_sin",
    "doy_cos",
    "is_weekend",
    "is_dst",
    "is_holiday",
]


@dataclass
class CausalStreamState:
    last_values: dict[str, float]
    missing_runs: dict[str, int]
    last_timestamp: str | None = None

    @classmethod
    def empty(cls) -> "CausalStreamState":
        return cls(
            last_values={v: float("nan") for v in BASE_VARS},
            missing_runs={v: 0 for v in BASE_VARS},
            last_timestamp=None,
        )


def compute_calendar_features(
    timestamps_utc: pd.DatetimeIndex,
    tz_local: str = "Europe/Lisbon",
    country_code: str = "PT",
) -> pd.DataFrame:
    local = timestamps_utc.tz_convert(tz_local)
    hour = local.hour.to_numpy(dtype=np.float64)
    dow = local.dayofweek.to_numpy(dtype=np.float64)
    doy = local.dayofyear.to_numpy(dtype=np.float64)
    is_weekend = (dow >= 5).astype(np.float64)
    is_dst = np.array(
        [1.0 if (t.dst() is not None and t.dst().total_seconds() > 0) else 0.0 for t in local],
        dtype=np.float64,
    )
    years = sorted(set(local.year.tolist()))
    cal = pyholidays.country_holidays(country_code, years=years)
    is_holiday = np.array([1.0 if t.date() in cal else 0.0 for t in local], dtype=np.float64)

    return pd.DataFrame(
        {
            "hour_sin": np.sin(2.0 * np.pi * hour / 24.0),
            "hour_cos": np.cos(2.0 * np.pi * hour / 24.0),
            "dow_sin": np.sin(2.0 * np.pi * dow / 7.0),
            "dow_cos": np.cos(2.0 * np.pi * dow / 7.0),
            "doy_sin": np.sin(2.0 * np.pi * (doy - 1.0) / 365.25),
            "doy_cos": np.cos(2.0 * np.pi * (doy - 1.0) / 365.25),
            "is_weekend": is_weekend,
            "is_dst": is_dst,
            "is_holiday": is_holiday,
        }
    )


def causal_locf_series(
    values: np.ndarray,
    invalid_mask: np.ndarray,
    var_name: str,
    max_gap: int,
    state: CausalStreamState,
) -> tuple[np.ndarray, int]:
    out = np.empty(len(values), dtype=np.float64)
    filled = 0
    for i, (val, is_bad) in enumerate(zip(values, invalid_mask)):
        if is_bad or not np.isfinite(val):
            state.missing_runs[var_name] += 1
            if state.missing_runs[var_name] <= max_gap and np.isfinite(state.last_values[var_name]):
                out[i] = state.last_values[var_name]
                filled += 1
            else:
                out[i] = np.nan
        else:
            fval = float(val)
            state.last_values[var_name] = fval
            state.missing_runs[var_name] = 0
            out[i] = fval
    return out, filled


def physical_invalid_masks(frame: pd.DataFrame, bounds: dict[str, Any]) -> dict[str, np.ndarray]:
    temp_bad = (frame["temp"].to_numpy(dtype=np.float64) < bounds["temp_min_c"]) | (
        frame["temp"].to_numpy(dtype=np.float64) > bounds["temp_max_c"]
    )
    hum_bad = (
        (frame["humidity"].to_numpy(dtype=np.float64) < bounds["humidity_min"])
        | (frame["humidity"].to_numpy(dtype=np.float64) > bounds["humidity_max"])
        | ((frame["humidity"].to_numpy(dtype=np.float64) == 0.0) & np.isclose(frame["temp"].to_numpy(dtype=np.float64), 0.0, atol=1e-6))
    )
    wind_bad = (frame["wind_speed"].to_numpy(dtype=np.float64) < bounds["wind_speed_min"]) | (
        frame["wind_speed"].to_numpy(dtype=np.float64) > bounds["wind_speed_max"]
    )
    load_bad = frame["load"].isna().to_numpy() | (frame["load"].to_numpy(dtype=np.float64) < bounds["load_min"])
    return {
        "load": load_bad,
        "temp": temp_bad,
        "humidity": hum_bad,
        "wind_speed": wind_bad,
    }


def fit_scaler_on_train(
    train_frame: pd.DataFrame,
    config: dict[str, Any],
    provenance: dict[str, str],
) -> dict[str, Any]:
    bounds = config["anomaly_bounds"]
    prep_cfg = config["preprocessing"]
    state = CausalStreamState.empty()
    masks = physical_invalid_masks(train_frame, bounds)

    work = {}
    for var in BASE_VARS:
        max_gap = prep_cfg["locf_max_gap_load"] if var == "load" else prep_cfg["locf_max_gap_weather"]
        work[f"{var}_input"], _ = causal_locf_series(
            train_frame[var].to_numpy(dtype=np.float64),
            masks[var],
            var,
            max_gap,
            state,
        )
    matrix = np.column_stack([work[col] for col in WORK_VARS])
    valid = np.isfinite(matrix).all(axis=1)
    if not valid.any():
        raise ValueError("No finite training rows for scaler fit")

    scaler = StandardScaler().fit(matrix[valid])
    pct_bounds = {}
    for var in BASE_VARS:
        sample = train_frame[var].dropna().to_numpy(dtype=np.float64)
        lo, hi = np.percentile(sample, bounds["percentiles"], method="linear")
        pct_bounds[var] = {"lower": float(lo), "upper": float(hi), "count": int(len(sample))}

    return {
        "schema_version": "2",
        "feature_order": WORK_VARS,
        "mean": scaler.mean_.tolist(),
        "std": np.sqrt(scaler.var_).tolist(),
        "scale": scaler.scale_.tolist(),
        "variance": scaler.var_.tolist(),
        "fit_count": int(valid.sum()),
        "train_rows": int(len(train_frame)),
        "percentile_bounds": pct_bounds,
        "anomaly_bounds": bounds,
        "locf_max_gap_load": int(prep_cfg["locf_max_gap_load"]),
        "locf_max_gap_weather": int(prep_cfg["locf_max_gap_weather"]),
        "provenance": provenance,
    }


def transform_causal(
    frame: pd.DataFrame,
    scaler_state: dict[str, Any],
    stream_state: CausalStreamState,
    tz_local: str = "Europe/Lisbon",
    country_code: str = "PT",
) -> tuple[pd.DataFrame, dict[str, int]]:
    ts = pd.DatetimeIndex(pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise"))
    if len(ts) > 1 and not ((ts[1:] - ts[:-1]) == pd.Timedelta(hours=1)).all():
        raise ValueError("Non-contiguous hourly timestamps in transform_causal")
    if stream_state.last_timestamp is not None:
        expected_next = pd.Timestamp(stream_state.last_timestamp) + pd.Timedelta(hours=1)
        if ts[0] != expected_next:
            raise ValueError(f"Stream state discontinuity: expected {expected_next}, got {ts[0]}")

    result = frame.copy(deep=True)
    result["timestamp_utc"] = ts
    masks = physical_invalid_masks(result, scaler_state["anomaly_bounds"])

    filled_counts: dict[str, int] = {}
    for var in BASE_VARS:
        max_gap = (
            scaler_state["locf_max_gap_load"]
            if var == "load"
            else scaler_state["locf_max_gap_weather"]
        )
        arr, n_filled = causal_locf_series(
            result[var].to_numpy(dtype=np.float64),
            masks[var],
            var,
            max_gap,
            stream_state,
        )
        result[f"{var}_input"] = arr
        result[f"{var}_physical_invalid"] = masks[var]
        filled_counts[var] = int(n_filled)

    work_mat = result[WORK_VARS].to_numpy(dtype=np.float64)
    means = np.asarray(scaler_state["mean"], dtype=np.float64)
    scales = np.asarray(scaler_state["scale"], dtype=np.float64)
    scaled = (work_mat - means) / scales
    for idx, col in enumerate(SCALED_VARS):
        result[col] = scaled[:, idx]

    cal_df = compute_calendar_features(ts, tz_local=tz_local, country_code=country_code)
    for col in CALENDAR_COLS:
        result[col] = cal_df[col].to_numpy()

    if len(ts):
        stream_state.last_timestamp = ts[-1].isoformat()
    return result, filled_counts


def inverse_scale_load(scaled_values: np.ndarray, scaler_state: dict[str, Any]) -> np.ndarray:
    return np.asarray(scaled_values, dtype=np.float64) * float(scaler_state["scale"][0]) + float(
        scaler_state["mean"][0]
    )


def load_canonical_prefix(canonical_path: Path, n_rows: int) -> pd.DataFrame:
    frame = pd.read_csv(canonical_path, nrows=n_rows)
    if len(frame) != n_rows:
        raise ValueError(f"Expected {n_rows} rows, got {len(frame)}")
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    return frame
