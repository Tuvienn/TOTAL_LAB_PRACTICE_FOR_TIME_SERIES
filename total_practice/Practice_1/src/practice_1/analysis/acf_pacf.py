import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import acf, pacf


def _build_correlation_table(
    values: np.ndarray,
    confidence_interval: np.ndarray,
    value_column: str,
) -> pd.DataFrame:
    lags = np.arange(len(values))
    return pd.DataFrame(
        {
            "lag": lags,
            value_column: values,
            "lower_ci": confidence_interval[:, 0],
            "upper_ci": confidence_interval[:, 1],
        }
    )


def compute_acf_table(
    series: pd.Series,
    max_lag: int = 40,
    alpha: float = 0.05,
) -> pd.DataFrame:
    values, confidence_interval = acf(
        series.to_numpy(dtype=float),
        nlags=max_lag,
        alpha=alpha,
        fft=True,
    )
    return _build_correlation_table(values, confidence_interval, "acf")


def compute_pacf_table(
    series: pd.Series,
    max_lag: int = 40,
    alpha: float = 0.05,
    method: str = "ywm",
) -> pd.DataFrame:
    values, confidence_interval = pacf(
        series.to_numpy(dtype=float),
        nlags=max_lag,
        alpha=alpha,
        method=method,
    )
    return _build_correlation_table(values, confidence_interval, "pacf")

