from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_2.analysis.correlation import (
    CANDIDATE_COLUMNS,
    CORRELATION_COLUMNS,
    compute_acf_pacf_tables,
    validate_arima_candidates,
)
from practice_2.analysis.stationarity import log_first_difference
from practice_2.data.time_series_data import chronological_split, load_monthly_retail_sales


ROOT = Path(__file__).parents[1]


def _e04_input():
    series = load_monthly_retail_sales(ROOT / "datasets" / "raw" / "a10.csv")
    train, test = chronological_split(series)
    return train, test, log_first_difference(train)


def test_e04_input_contract_and_test_boundary():
    train, test, transformed = _e04_input()

    assert len(train) == 163
    assert len(test) == 41
    assert len(transformed) == 162
    assert transformed.notna().all()
    assert transformed.index[0] == train.index[1]
    assert transformed.index[-1] == train.index[-1]
    assert transformed.index.max() < test.index.min()


def test_e04_correlation_tables_follow_approved_configuration():
    _, _, transformed = _e04_input()
    acf_table, pacf_table = compute_acf_pacf_tables(
        transformed,
        nlags=36,
        alpha=0.05,
        pacf_method="ywm",
    )

    assert list(acf_table.columns) == CORRELATION_COLUMNS
    assert list(pacf_table.columns) == CORRELATION_COLUMNS
    assert acf_table["lag"].tolist() == list(range(37))
    assert pacf_table["lag"].tolist() == list(range(37))
    for table in [acf_table, pacf_table]:
        expected = (table["ci_lower"] > 0) | (table["ci_upper"] < 0)
        pd.testing.assert_series_equal(table["significant"], expected, check_names=False)


@pytest.mark.parametrize(
    "series",
    [
        pd.Series(dtype=float),
        pd.Series([1.0, np.nan, 2.0]),
    ],
)
def test_e04_rejects_invalid_series(series):
    with pytest.raises(ValueError):
        compute_acf_pacf_tables(series, nlags=1)


def test_e04_rejects_unapproved_pacf_method():
    _, _, transformed = _e04_input()
    with pytest.raises(ValueError, match="ywm"):
        compute_acf_pacf_tables(transformed, nlags=36, pacf_method="ols")


def test_e04_candidate_handoff_contract():
    candidates = pd.DataFrame(
        {
            "candidate": ["ARIMA(1,1,1)", "ARIMA(2,1,1)"],
            "p": pd.Series([1, 2], dtype=int),
            "d": pd.Series([1, 1], dtype=int),
            "q": pd.Series([1, 1], dtype=int),
            "analysis_scale": ["natural_log", "natural_log"],
            "acf_evidence": ["lag 1", "lag 1"],
            "pacf_evidence": ["lag 1", "lags 1-2"],
            "status": ["provisional", "provisional"],
        }
    )

    validated = validate_arima_candidates(candidates)
    assert list(validated.columns) == CANDIDATE_COLUMNS
    assert 1 <= len(validated) <= 2
    assert (validated["d"] == 1).all()
    assert (validated["analysis_scale"] == "natural_log").all()
    assert (validated["status"] == "provisional").all()


def test_e04_rejects_more_than_two_candidates():
    candidates = pd.DataFrame(
        {
            "candidate": ["a", "b", "c"],
            "p": pd.Series([1, 2, 3], dtype=int),
            "d": pd.Series([1, 1, 1], dtype=int),
            "q": pd.Series([1, 1, 1], dtype=int),
            "analysis_scale": ["natural_log"] * 3,
            "acf_evidence": ["evidence"] * 3,
            "pacf_evidence": ["evidence"] * 3,
            "status": ["provisional"] * 3,
        }
    )
    with pytest.raises(ValueError, match="one or two"):
        validate_arima_candidates(candidates)
