import numpy as np
import pandas as pd

from practice_1.analysis.decomposition import validate_decomposition_series


ROLLING_COLUMNS = [
    "observed_value",
    "rolling_mean_12",
    "rolling_std_12",
]
SEASONAL_COLUMNS = [
    "timestamp",
    "year",
    "month",
    "observed_value",
]


def compute_rolling_statistics(
    series: pd.Series,
    window: int = 12,
    min_periods: int = 12,
    center: bool = False,
    std_ddof: int = 1,
) -> pd.DataFrame:
    if isinstance(window, bool) or not isinstance(window, int):
        raise TypeError("window must be an integer")
    if isinstance(min_periods, bool) or not isinstance(min_periods, int):
        raise TypeError("min_periods must be an integer")
    if window < 1:
        raise ValueError("window must be positive")
    if min_periods < 1 or min_periods > window:
        raise ValueError("min_periods must be between 1 and window")
    if center is not False:
        raise ValueError("center must be False for the approved trailing protocol")
    if isinstance(std_ddof, bool) or not isinstance(std_ddof, int):
        raise TypeError("std_ddof must be an integer")
    if std_ddof < 0 or std_ddof >= min_periods:
        raise ValueError("std_ddof must be between 0 and min_periods - 1")

    validated = validate_decomposition_series(series)
    rolling = validated.rolling(
        window=window,
        min_periods=min_periods,
        center=center,
    )
    result = pd.DataFrame(
        {
            "observed_value": validated,
            "rolling_mean_12": rolling.mean(),
            "rolling_std_12": rolling.std(ddof=std_ddof),
        },
        index=validated.index.copy(),
    )
    result.index.name = "timestamp"
    return result[ROLLING_COLUMNS]


def prepare_monthly_seasonal_data(series: pd.Series) -> pd.DataFrame:
    validated = validate_decomposition_series(series)
    return pd.DataFrame(
        {
            "timestamp": validated.index,
            "year": validated.index.year.astype(int),
            "month": validated.index.month.astype(int),
            "observed_value": validated.to_numpy(dtype=float),
        }
    )[SEASONAL_COLUMNS]


def _validate_seasonal_data(seasonal_data: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(seasonal_data, pd.DataFrame):
        raise TypeError("seasonal_data must be a pandas DataFrame")
    missing_columns = set(SEASONAL_COLUMNS).difference(seasonal_data.columns)
    if missing_columns:
        raise ValueError(
            f"seasonal_data is missing columns: {sorted(missing_columns)}"
        )
    if seasonal_data.empty:
        raise ValueError("seasonal_data must not be empty")

    validated = seasonal_data[SEASONAL_COLUMNS].copy()
    validated["timestamp"] = pd.to_datetime(validated["timestamp"], errors="raise")
    if validated[SEASONAL_COLUMNS].isna().any().any():
        raise ValueError("seasonal_data must not contain missing values")
    if validated["timestamp"].duplicated().any():
        raise ValueError("seasonal_data contains duplicate timestamps")
    if validated.duplicated(subset=["year", "month"]).any():
        raise ValueError("seasonal_data contains duplicate month-year observations")
    if not validated["month"].between(1, 12).all():
        raise ValueError("month values must be between 1 and 12")
    if not (
        validated["timestamp"].dt.year.to_numpy()
        == validated["year"].to_numpy()
    ).all():
        raise ValueError("timestamp years do not match the year column")
    if not (
        validated["timestamp"].dt.month.to_numpy()
        == validated["month"].to_numpy()
    ).all():
        raise ValueError("timestamp months do not match the month column")
    try:
        observed = validated["observed_value"].to_numpy(dtype=float, copy=True)
    except (TypeError, ValueError) as error:
        raise TypeError("observed_value must be numeric") from error
    if not np.isfinite(observed).all():
        raise ValueError("observed_value must contain only finite values")
    validated["observed_value"] = observed
    return validated.sort_values("timestamp").reset_index(drop=True)


def build_month_year_matrix(
    seasonal_data: pd.DataFrame,
    expected_shape: tuple[int, int] = (12, 12),
) -> pd.DataFrame:
    if (
        not isinstance(expected_shape, tuple)
        or len(expected_shape) != 2
        or any(isinstance(value, bool) or not isinstance(value, int) for value in expected_shape)
        or any(value < 1 for value in expected_shape)
    ):
        raise ValueError("expected_shape must contain two positive integers")

    validated = _validate_seasonal_data(seasonal_data)
    matrix = validated.pivot(
        index="month",
        columns="year",
        values="observed_value",
    ).sort_index(axis=0).sort_index(axis=1)
    if matrix.shape != expected_shape:
        raise ValueError(
            f"month-year matrix must have shape {expected_shape}, found {matrix.shape}"
        )
    if matrix.isna().any().any():
        raise ValueError("month-year matrix contains missing cells")
    return matrix


def summarize_monthly_pattern(seasonal_data: pd.DataFrame) -> pd.DataFrame:
    validated = _validate_seasonal_data(seasonal_data)
    summary = (
        validated.groupby("month", sort=True)["observed_value"]
        .agg(mean_value="mean", min_value="min", max_value="max")
        .reset_index()
    )
    if summary["month"].tolist() != list(range(1, 13)):
        raise ValueError("monthly summary must contain every month from 1 through 12")
    return summary
