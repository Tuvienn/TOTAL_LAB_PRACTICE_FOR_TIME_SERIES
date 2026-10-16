import pandas as pd
from statsmodels.tsa.stattools import adfuller


def run_adf(series: pd.Series, alpha: float = 0.05):
    """Run ADF with AIC autolag and return result and critical-value tables."""
    if series.empty or series.isna().any():
        raise ValueError("ADF input must be non-empty and contain no missing values")
    result = adfuller(series, autolag="AIC")
    decision = "reject H0" if result[1] <= alpha else "fail to reject H0"
    summary = pd.DataFrame({
        "metric": ["adf_statistic", "p_value", "used_lag", "n_observations", "alpha", "decision"],
        "value": [result[0], result[1], result[2], result[3], alpha, decision],
    })
    critical = pd.DataFrame({"critical_value": list(result[4]), "value": list(result[4].values())})
    return summary, critical


def first_difference(series: pd.Series) -> pd.Series:
    """Return first difference without modifying the input series."""
    if series.empty:
        raise ValueError("Cannot difference an empty series")
    return series.diff().dropna()
