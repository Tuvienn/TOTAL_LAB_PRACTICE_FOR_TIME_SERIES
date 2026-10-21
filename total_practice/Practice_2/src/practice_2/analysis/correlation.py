from __future__ import annotations

import pandas as pd
from statsmodels.tsa.stattools import acf, pacf


CORRELATION_COLUMNS = ["lag", "correlation", "ci_lower", "ci_upper", "significant"]
CANDIDATE_COLUMNS = [
    "candidate",
    "p",
    "d",
    "q",
    "analysis_scale",
    "acf_evidence",
    "pacf_evidence",
    "status",
]


def _validate_correlation_input(
    series: pd.Series,
    nlags: int,
    alpha: float,
) -> None:
    if not isinstance(series, pd.Series):
        raise TypeError("Correlation input must be a pandas Series")
    if series.empty:
        raise ValueError("Correlation input must be non-empty")
    if series.isna().any():
        raise ValueError("Correlation input must contain no missing values")
    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError("Correlation input must be numeric")
    if not isinstance(nlags, int) or isinstance(nlags, bool) or nlags < 1:
        raise ValueError("nlags must be a positive integer")
    if nlags >= len(series) // 2:
        raise ValueError("nlags must be less than half the number of observations")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")


def _build_correlation_table(values, confidence_intervals) -> pd.DataFrame:
    table = pd.DataFrame(
        {
            "lag": range(len(values)),
            "correlation": values,
            "ci_lower": confidence_intervals[:, 0],
            "ci_upper": confidence_intervals[:, 1],
        }
    )
    table["significant"] = (table["ci_lower"] > 0) | (table["ci_upper"] < 0)
    return table.loc[:, CORRELATION_COLUMNS]


def compute_acf_pacf_tables(
    series: pd.Series,
    nlags: int = 36,
    alpha: float = 0.05,
    pacf_method: str = "ywm",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute ACF/PACF tables with confidence intervals from statsmodels."""
    _validate_correlation_input(series, nlags=nlags, alpha=alpha)
    if pacf_method != "ywm":
        raise ValueError("Practice 2 Exercise 4 requires pacf_method='ywm'")

    acf_values, acf_confidence = acf(
        series,
        nlags=nlags,
        alpha=alpha,
        fft=False,
        result_object=False,
    )
    pacf_values, pacf_confidence = pacf(
        series,
        nlags=nlags,
        alpha=alpha,
        method=pacf_method,
    )
    return (
        _build_correlation_table(acf_values, acf_confidence),
        _build_correlation_table(pacf_values, pacf_confidence),
    )


def validate_arima_candidates(candidate_table: pd.DataFrame) -> pd.DataFrame:
    """Validate the E04 handoff contract for provisional ARIMA candidates."""
    missing_columns = set(CANDIDATE_COLUMNS).difference(candidate_table.columns)
    if missing_columns:
        raise ValueError(f"Candidate table is missing columns: {sorted(missing_columns)}")
    if not 1 <= len(candidate_table) <= 2:
        raise ValueError("Exercise 4 must hand off one or two ARIMA candidates")

    validated = candidate_table.loc[:, CANDIDATE_COLUMNS].copy()
    for order_name in ["p", "d", "q"]:
        if not pd.api.types.is_integer_dtype(validated[order_name]):
            raise TypeError(f"Candidate column '{order_name}' must contain integers")
        if (validated[order_name] < 0).any():
            raise ValueError(f"Candidate column '{order_name}' must be non-negative")

    if not (validated["d"] == 1).all():
        raise ValueError("Exercise 4 candidates must inherit d=1 from Exercise 3")
    if not (validated["analysis_scale"] == "natural_log").all():
        raise ValueError("Exercise 4 candidates must use the natural_log analysis scale")
    if not (validated["status"] == "provisional").all():
        raise ValueError("Exercise 4 candidates must remain provisional")
    return validated
