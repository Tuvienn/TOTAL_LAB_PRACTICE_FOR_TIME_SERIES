from collections.abc import Sequence

import numpy as np
import pandas as pd

from practice_1.analysis.decomposition import validate_decomposition_series


MISSING_COMPARISON_COLUMNS = [
    "timestamp",
    "true_value",
    "forward_fill_value",
    "interpolation_value",
    "forward_fill_absolute_error",
    "interpolation_absolute_error",
]


def _validated_timestamps(
    series: pd.Series,
    timestamps: Sequence[str | pd.Timestamp],
) -> pd.DatetimeIndex:
    parsed = pd.DatetimeIndex(pd.to_datetime(list(timestamps)))
    if parsed.empty:
        raise ValueError("at least one timestamp must be provided")
    if parsed.has_duplicates:
        raise ValueError("masked timestamps must be unique")
    if not parsed.isin(series.index).all():
        missing = parsed[~parsed.isin(series.index)]
        raise ValueError(f"timestamps are not present in the series: {missing.tolist()}")
    protected = series.index[:12].append(series.index[-12:])
    if parsed.isin(protected).any():
        raise ValueError("masked timestamps must not occur in the first or last 12 observations")
    return parsed.sort_values()


def simulate_missing_values(
    series: pd.Series,
    timestamps: Sequence[str | pd.Timestamp],
) -> tuple[pd.Series, pd.Series]:
    validated = validate_decomposition_series(series)
    masked_timestamps = _validated_timestamps(validated, timestamps)
    ground_truth = validated.loc[masked_timestamps].copy()
    ground_truth.name = "true_value"
    masked = validated.copy()
    masked.loc[masked_timestamps] = np.nan
    masked.name = "value_with_missing"
    return masked, ground_truth


def apply_missing_value_treatments(
    masked_series: pd.Series,
) -> tuple[pd.Series, pd.Series]:
    if not isinstance(masked_series, pd.Series):
        raise TypeError("masked_series must be a pandas Series")
    if not isinstance(masked_series.index, pd.DatetimeIndex):
        raise TypeError("masked_series index must be a pandas DatetimeIndex")
    if masked_series.isna().sum() == 0:
        raise ValueError("masked_series must contain missing values")

    forward_fill = masked_series.ffill()
    interpolation = masked_series.interpolate(method="time", limit_area="inside")
    if forward_fill.isna().any() or interpolation.isna().any():
        raise ValueError("treatments did not reconstruct every masked observation")
    forward_fill.name = "forward_fill_value"
    interpolation.name = "interpolation_value"
    return forward_fill, interpolation


def build_missing_value_comparison(
    ground_truth: pd.Series,
    forward_fill: pd.Series,
    interpolation: pd.Series,
) -> pd.DataFrame:
    timestamps = ground_truth.index
    if not timestamps.isin(forward_fill.index).all() or not timestamps.isin(
        interpolation.index
    ).all():
        raise ValueError("treatment series do not contain every ground-truth timestamp")

    comparison = pd.DataFrame(
        {
            "timestamp": timestamps,
            "true_value": ground_truth.to_numpy(dtype=float),
            "forward_fill_value": forward_fill.loc[timestamps].to_numpy(dtype=float),
            "interpolation_value": interpolation.loc[timestamps].to_numpy(dtype=float),
        }
    )
    comparison["forward_fill_absolute_error"] = (
        comparison["forward_fill_value"] - comparison["true_value"]
    ).abs()
    comparison["interpolation_absolute_error"] = (
        comparison["interpolation_value"] - comparison["true_value"]
    ).abs()
    return comparison[MISSING_COMPARISON_COLUMNS]


def summarize_reconstruction_mae(comparison: pd.DataFrame) -> pd.DataFrame:
    required = {
        "forward_fill_absolute_error",
        "interpolation_absolute_error",
    }
    if required.difference(comparison.columns):
        raise ValueError("comparison is missing absolute-error columns")
    return pd.DataFrame(
        {
            "method": ["forward_fill", "time_interpolation"],
            "mae_masked_positions": [
                comparison["forward_fill_absolute_error"].mean(),
                comparison["interpolation_absolute_error"].mean(),
            ],
        }
    )


def detect_residual_iqr_outliers(
    observed: pd.Series,
    residual_log: pd.Series,
    multiplier: float = 1.5,
) -> tuple[pd.DataFrame, dict[str, float]]:
    validated_observed = validate_decomposition_series(observed)
    if not isinstance(residual_log, pd.Series):
        raise TypeError("residual_log must be a pandas Series")
    if not residual_log.index.equals(validated_observed.index):
        raise ValueError("observed and residual indexes must match")
    residual_values = residual_log.to_numpy(dtype=float)
    if not np.isfinite(residual_values).all():
        raise ValueError("residual_log must contain only finite values")
    if not np.isfinite(multiplier) or multiplier <= 0:
        raise ValueError("multiplier must be positive and finite")

    q1 = float(residual_log.quantile(0.25))
    q3 = float(residual_log.quantile(0.75))
    iqr = q3 - q1
    lower_fence = q1 - multiplier * iqr
    upper_fence = q3 + multiplier * iqr
    flag = residual_log.lt(lower_fence) | residual_log.gt(upper_fence)
    candidates = pd.DataFrame(
        {
            "timestamp": residual_log.index[flag],
            "observed_value": validated_observed.loc[flag].to_numpy(dtype=float),
            "residual_log": residual_log.loc[flag].to_numpy(dtype=float),
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_fence": lower_fence,
            "upper_fence": upper_fence,
            "flag": True,
        }
    )
    thresholds = {
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_fence": lower_fence,
        "upper_fence": upper_fence,
    }
    return candidates, thresholds
