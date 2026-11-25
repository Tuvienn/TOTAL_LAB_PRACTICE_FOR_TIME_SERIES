import pandas as pd
from statsmodels.tsa.stattools import acf, pacf


def acf_pacf_tables(
    series: pd.Series,
    nlags: int = 36,
    alpha: float = 0.05,
    pacf_method: str = "ywm",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ACF and PACF tables with confidence intervals."""
    if series.empty or series.isna().any():
        raise ValueError("Correlation input must be non-empty and contain no missing values")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not isinstance(nlags, int) or nlags < 1:
        raise ValueError("nlags must be a positive integer")
    if nlags >= len(series) // 2:
        raise ValueError("nlags must be less than half the number of observations")

    acf_values, acf_intervals = acf(series, nlags=nlags, alpha=alpha, fft=True)
    pacf_values, pacf_intervals = pacf(series, nlags=nlags, alpha=alpha, method=pacf_method)
    return (
        _correlation_table(acf_values, acf_intervals),
        _correlation_table(pacf_values, pacf_intervals),
    )


def _correlation_table(values, intervals) -> pd.DataFrame:
    table = pd.DataFrame(
        {
            "lag": range(len(values)),
            "correlation": values,
            "ci_lower": intervals[:, 0],
            "ci_upper": intervals[:, 1],
        }
    )
    table["significant"] = (table["ci_lower"] > 0) | (table["ci_upper"] < 0)
    return table
