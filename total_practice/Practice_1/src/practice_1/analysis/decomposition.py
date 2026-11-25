import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.seasonal import STL

from practice_1.analysis.acf_pacf import compute_acf_table


COMPONENT_COLUMNS = [
    "observed_log",
    "trend_log",
    "seasonal_log",
    "residual_log",
]


def _validate_monthly_series(
    series: pd.Series,
    *,
    require_positive: bool,
) -> pd.Series:
    if not isinstance(series, pd.Series):
        raise TypeError("series must be a pandas Series")
    if series.empty:
        raise ValueError("series must not be empty")
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("series index must be a pandas DatetimeIndex")
    if series.index.has_duplicates:
        raise ValueError("series index must not contain duplicate timestamps")
    if not series.index.is_monotonic_increasing:
        raise ValueError("series index must be in chronological order")

    expected_index = pd.date_range(
        start=series.index[0],
        periods=len(series),
        freq="MS",
    )
    if not series.index.equals(expected_index):
        raise ValueError("series must have a complete monthly-start frequency")

    try:
        values = series.to_numpy(dtype=float, copy=True)
    except (TypeError, ValueError) as error:
        raise TypeError("series values must be numeric") from error

    if not np.isfinite(values).all():
        raise ValueError("series must not contain missing or non-finite values")
    if require_positive and np.any(values <= 0.0):
        raise ValueError("series values must be strictly positive for log transform")

    return pd.Series(values, index=series.index.copy(), name=series.name)


def validate_decomposition_series(series: pd.Series) -> pd.Series:
    """Return a validated copy of a positive, complete monthly series."""
    return _validate_monthly_series(series, require_positive=True)


def log_transform_series(series: pd.Series) -> pd.Series:
    """Apply a natural-log transform without modifying the input series."""
    validated = validate_decomposition_series(series)
    transformed = np.log(validated)
    transformed.name = "observed_log"
    return transformed


def compute_stl_decomposition(
    log_series: pd.Series,
    period: int = 12,
    robust: bool = True,
) -> pd.DataFrame:
    """Decompose a validated natural-log monthly series with STL."""
    if isinstance(period, bool) or not isinstance(period, int):
        raise TypeError("period must be an integer")
    if period < 2:
        raise ValueError("period must be at least 2")
    if not isinstance(robust, bool):
        raise TypeError("robust must be a boolean")

    validated_log = _validate_monthly_series(
        log_series,
        require_positive=False,
    )
    fitted = STL(validated_log, period=period, robust=robust).fit()
    components = pd.DataFrame(
        {
            "observed_log": fitted.observed,
            "trend_log": fitted.trend,
            "seasonal_log": fitted.seasonal,
            "residual_log": fitted.resid,
        },
        index=validated_log.index.copy(),
    )
    components.index.name = "timestamp"

    if components[COMPONENT_COLUMNS].isna().any().any():
        raise ValueError("STL decomposition produced missing component values")
    reconstructed = (
        components["trend_log"]
        + components["seasonal_log"]
        + components["residual_log"]
    )
    if not np.allclose(
        components["observed_log"].to_numpy(),
        reconstructed.to_numpy(),
        rtol=1e-10,
        atol=1e-10,
    ):
        raise ValueError("STL components do not reconstruct the observed log series")
    return components


def compute_residual_diagnostics(
    residual: pd.Series,
    max_lag: int = 40,
    alpha: float = 0.05,
    ljung_box_lag: int = 12,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute residual ACF and the approved Ljung-Box diagnostic."""
    validated_residual = _validate_monthly_series(
        residual,
        require_positive=False,
    )
    if isinstance(ljung_box_lag, bool) or not isinstance(ljung_box_lag, int):
        raise TypeError("ljung_box_lag must be an integer")
    if ljung_box_lag < 1 or ljung_box_lag >= len(validated_residual):
        raise ValueError("ljung_box_lag must be between 1 and series length - 1")

    acf_table = compute_acf_table(
        validated_residual,
        max_lag=max_lag,
        alpha=alpha,
    )
    ljung_box = acorr_ljungbox(
        validated_residual,
        lags=[ljung_box_lag],
        return_df=True,
    )
    diagnostics = pd.DataFrame(
        {
            "lag": [ljung_box_lag],
            "ljung_box_statistic": [float(ljung_box.loc[ljung_box_lag, "lb_stat"])],
            "p_value": [float(ljung_box.loc[ljung_box_lag, "lb_pvalue"])],
        }
    )
    return acf_table, diagnostics
