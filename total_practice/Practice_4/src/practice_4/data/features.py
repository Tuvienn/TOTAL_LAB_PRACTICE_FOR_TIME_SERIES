from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from practice_4.data.preprocessing import CALENDAR_COLS, SCALED_VARS, WORK_VARS


WINDOW_HOURS = 24
CONTEXT_HOURS = 168
BASE_NAMES = ("load", "temperature", "humidity", "wind_speed")

LAG24_FEATURE_NAMES = tuple(
    f"lag{lag:02d}_{name}"
    for lag in range(WINDOW_HOURS - 1, -1, -1)
    for name in BASE_NAMES
)
EXTENDED_LOAD_LAGS = ("lag47_load", "lag167_load")
ROLLING_LOAD_FEATURES = (
    "mean6h",
    "mean24h",
    "std24h",
    "min24h",
    "max24h",
    "trend24h",
    "diff1h",
    "trend168h",
)
TARGET_CALENDAR_FEATURES = tuple(f"target_{c}" for c in CALENDAR_COLS)
INTERACTION_FEATURES = (
    "load_per_temp_k",
    "hdd_proxy",
    "cdd_proxy",
    "temp_x_humidity",
    "temp_diff_1h",
    "temp_diff_24h",
)

XGB_FULL_FEATURES = (
    *LAG24_FEATURE_NAMES,
    *EXTENDED_LOAD_LAGS,
    *ROLLING_LOAD_FEATURES,
    *TARGET_CALENDAR_FEATURES,
    *INTERACTION_FEATURES,
)


def xgb_ablation_subsets() -> dict[str, list[str]]:
    load_lags_24 = [name for name in LAG24_FEATURE_NAMES if name.endswith("_load")]
    load_only = [*load_lags_24, *EXTENDED_LOAD_LAGS, *ROLLING_LOAD_FEATURES]
    load_weather = [*LAG24_FEATURE_NAMES, *ROLLING_LOAD_FEATURES]
    load_calendar = [*load_only, *TARGET_CALENDAR_FEATURES]
    return {
        "XGB_load_only": load_only,
        "XGB_load_weather": load_weather,
        "XGB_load_calendar": load_calendar,
        "XGB_full": list(XGB_FULL_FEATURES),
    }


def feature_subset_indices(subset_names: list[str]) -> list[int]:
    index_map = {name: i for i, name in enumerate(XGB_FULL_FEATURES)}
    return [index_map[name] for name in subset_names]


@dataclass(frozen=True)
class CandidateOrigin:
    target_row: int
    origin_row: int
    context_start_row: int
    split: str
    load_observed: bool
    context_finite: bool
    exclusion_reason: str | None
    y_true: float | None

    @property
    def eligible(self) -> bool:
        return self.exclusion_reason is None


def build_feature_row_from_arrays(
    scaled_levels: np.ndarray,
    raw_work: np.ndarray,
    cal_matrix: np.ndarray,
    target_row: int,
    hdd_base_c: float = 18.0,
    cdd_base_c: float = 22.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if target_row < CONTEXT_HOURS:
        raise ValueError(f"target_row {target_row} < CONTEXT_HOURS ({CONTEXT_HOURS})")
    ctx_scaled = scaled_levels[target_row - CONTEXT_HOURS : target_row]
    ctx_work = raw_work[target_row - CONTEXT_HOURS : target_row]
    ctx_cal = cal_matrix[target_row - CONTEXT_HOURS : target_row]
    target_cal = cal_matrix[target_row]

    if not (np.isfinite(ctx_scaled).all() and np.isfinite(ctx_work).all() and np.isfinite(ctx_cal).all()):
        raise ValueError("Non-finite value in causal context")

    seq24_base = ctx_scaled[-WINDOW_HOURS:, :]
    seq24_cal = np.concatenate([seq24_base, ctx_cal[-WINDOW_HOURS:, :]], axis=1).astype(np.float32)
    flat96 = seq24_base.reshape(-1)

    load_s = ctx_scaled[:, 0]
    lag47_load = load_s[-48]
    lag167_load = load_s[0]

    mean6h = float(load_s[-6:].mean())
    mean24h = float(load_s[-24:].mean())
    std24h = float(load_s[-24:].std(ddof=0))
    min24h = float(load_s[-24:].min())
    max24h = float(load_s[-24:].max())
    trend24h = float(load_s[-1] - load_s[-25])
    diff1h = float(load_s[-1] - load_s[-2])
    trend168h = float(load_s[-1] - load_s[0])

    load_t = float(ctx_work[-1, 0])
    temp_t = float(ctx_work[-1, 1])
    hum_t = float(ctx_work[-1, 2])
    temp_t_m1 = float(ctx_work[-2, 1])
    temp_t_m24 = float(ctx_work[-25, 1])

    load_per_temp_k = load_t / (temp_t + 273.15)
    hdd_proxy = max(0.0, hdd_base_c - temp_t)
    cdd_proxy = max(0.0, temp_t - cdd_base_c)
    temp_x_humidity = temp_t * hum_t
    temp_diff_1h = temp_t - temp_t_m1
    temp_diff_24h = temp_t - temp_t_m24

    xgb_vec = np.concatenate(
        [
            flat96,
            np.array(
                [
                    lag47_load,
                    lag167_load,
                    mean6h,
                    mean24h,
                    std24h,
                    min24h,
                    max24h,
                    trend24h,
                    diff1h,
                    trend168h,
                ],
                dtype=np.float64,
            ),
            target_cal.astype(np.float64),
            np.array(
                [
                    load_per_temp_k,
                    hdd_proxy,
                    cdd_proxy,
                    temp_x_humidity,
                    temp_diff_1h,
                    temp_diff_24h,
                ],
                dtype=np.float64,
            ),
        ]
    )
    return seq24_base.astype(np.float32), seq24_cal, xgb_vec.astype(np.float32)


def materialize_supervised_dataset(
    prepared_df: pd.DataFrame,
    train_end_row: int,
    hdd_base_c: float = 18.0,
    cdd_base_c: float = 22.0,
) -> dict[str, Any]:
    n = len(prepared_df)
    scaled_levels = prepared_df[SCALED_VARS].to_numpy(dtype=np.float64)
    raw_work = prepared_df[WORK_VARS].to_numpy(dtype=np.float64)
    cal_matrix = prepared_df[CALENDAR_COLS].to_numpy(dtype=np.float64)
    raw_load = prepared_df["load"].to_numpy(dtype=np.float64)
    observed = prepared_df["load_observed"].to_numpy(dtype=bool)
    timestamps = pd.DatetimeIndex(prepared_df["timestamp_utc"])

    origins: list[CandidateOrigin] = []
    eligible_targets: list[int] = []

    for target_row in range(CONTEXT_HOURS, n):
        split = "train" if target_row <= train_end_row else "validation"
        obs = bool(observed[target_row])
        ctx_ok = bool(
            np.isfinite(scaled_levels[target_row - CONTEXT_HOURS : target_row]).all()
            and np.isfinite(raw_work[target_row - CONTEXT_HOURS : target_row]).all()
        )
        if not obs:
            reason = "missing_truth"
        elif not ctx_ok:
            reason = "invalid_context"
        else:
            reason = None
            eligible_targets.append(target_row)

        origins.append(
            CandidateOrigin(
                target_row=target_row,
                origin_row=target_row - 1,
                context_start_row=target_row - CONTEXT_HOURS,
                split=split,
                load_observed=obs,
                context_finite=ctx_ok,
                exclusion_reason=reason,
                y_true=float(raw_load[target_row]) if obs else None,
            )
        )

    m = len(eligible_targets)
    x_lstm_core = np.empty((m, WINDOW_HOURS, 4), dtype=np.float32)
    x_lstm_cal = np.empty((m, WINDOW_HOURS, 4 + len(CALENDAR_COLS)), dtype=np.float32)
    x_xgb = np.empty((m, len(XGB_FULL_FEATURES)), dtype=np.float32)
    y_true = np.empty(m, dtype=np.float64)
    target_rows_arr = np.asarray(eligible_targets, dtype=np.int64)

    for idx, trow in enumerate(eligible_targets):
        seq_core, seq_cal, xgb_vec = build_feature_row_from_arrays(
            scaled_levels, raw_work, cal_matrix, trow, hdd_base_c, cdd_base_c
        )
        x_lstm_core[idx] = seq_core
        x_lstm_cal[idx] = seq_cal
        x_xgb[idx] = xgb_vec
        y_true[idx] = raw_load[trow]

    origin_records = []
    sample_idx = 0
    for o in origins:
        origin_records.append(
            {
                "origin_row": o.origin_row,
                "target_row": o.target_row,
                "context_start_row": o.context_start_row,
                "origin_timestamp_utc": timestamps[o.origin_row].isoformat(),
                "target_timestamp_utc": timestamps[o.target_row].isoformat(),
                "split": o.split,
                "load_observed": o.load_observed,
                "context_finite": o.context_finite,
                "eligible": o.eligible,
                "exclusion_reason": o.exclusion_reason or "",
                "y_true": o.y_true if o.y_true is not None else np.nan,
                "sample_index": sample_idx if o.eligible else -1,
            }
        )
        if o.eligible:
            sample_idx += 1

    counts = {}
    for split_name in ("train", "validation"):
        part = [o for o in origins if o.split == split_name]
        counts[split_name] = {
            "n_considered": len(part),
            "n_missing_excluded": sum(o.exclusion_reason == "missing_truth" for o in part),
            "n_input_excluded": sum(o.exclusion_reason == "invalid_context" for o in part),
            "n_eligible": sum(o.eligible for o in part),
        }

    var_train_levels = scaled_levels[: train_end_row + 1].copy()
    if not np.isfinite(var_train_levels).all():
        var_df = pd.DataFrame(var_train_levels).ffill().bfill()
        var_train_levels = var_df.to_numpy(dtype=np.float64)

    return {
        "origin_df": pd.DataFrame(origin_records),
        "counts": counts,
        "arrays": {
            "schema_version": np.asarray(2, dtype=np.uint8),
            "target_row": target_rows_arr,
            "x_lstm_core": x_lstm_core,
            "x_lstm_cal": x_lstm_cal,
            "x_xgb": x_xgb,
            "y_true": y_true,
            "var_train_levels": var_train_levels,
            "full_scaled_seq": np.concatenate([scaled_levels, cal_matrix], axis=1).astype(np.float32),
        },
    }


def format_feature_dictionary_markdown(counts: dict[str, Any]) -> str:
    subsets = xgb_ablation_subsets()
    lines = [
        "# Stage S4 — Causal Feature Dictionary (v2)",
        "",
        f"- **Common Causal Context:** `{CONTEXT_HOURS}` hours (`t-167 .. t`) to predict observed raw `load(t+1)`.",
        f"- **Train Eligible:** `{counts['train']['n_eligible']:,}` / `{counts['train']['n_considered']:,}`",
        f"- **Validation Eligible:** `{counts['validation']['n_eligible']:,}` / `{counts['validation']['n_considered']:,}`",
        f"- **Total `XGB_full` Features:** `{len(XGB_FULL_FEATURES)}`",
        f"- **LSTM Core Shape:** `(N, {WINDOW_HOURS}, 4)` | **LSTM Calendar Shape:** `(N, {WINDOW_HOURS}, {4 + len(CALENDAR_COLS)})`",
        "",
        "## Ablation Feature Subsets",
        "",
        "| Subset | Count | Description |",
        "|---|---:|---|",
        f"| `XGB_load_only` | {len(subsets['XGB_load_only'])} | 24h load lags + lag47/lag167 + 8 rolling load stats |",
        f"| `XGB_load_weather` | {len(subsets['XGB_load_weather'])} | 96 base 24h multivariate lags + 8 rolling load stats |",
        f"| `XGB_load_calendar` | {len(subsets['XGB_load_calendar'])} | `XGB_load_only` + 9 local calendar/DST/holiday target features |",
        f"| `XGB_full` | {len(subsets['XGB_full'])} | All load, weather, calendar/DST/holiday, and 6 cross-variable interactions |",
        "",
        "## Cross-Variable Interaction Features (Slide 7, `chapter4-5.pdf`)",
        "",
        "- `load_per_temp_k`: `load_input(t) / (temp_input(t) + 273.15)`",
        "- `hdd_proxy`: `max(0, 18.0 - temp_input(t))` (heating load nonlinearity)",
        "- `cdd_proxy`: `max(0, temp_input(t) - 22.0)` (cooling load nonlinearity)",
        "- `temp_x_humidity`: `temp_input(t) * humidity_input(t)`",
        "- `temp_diff_1h`, `temp_diff_24h`: 1-hour and 24-hour temperature change at origin `t`",
        "",
    ]
    return "\n".join(lines)
