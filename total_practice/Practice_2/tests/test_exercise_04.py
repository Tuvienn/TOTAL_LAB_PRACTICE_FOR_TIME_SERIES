import numpy as np
import pandas as pd
import pytest

from practice_2.analysis import acf_pacf_tables


def test_e04_acf_pacf_tables_include_expected_schema():
    series = pd.Series(np.sin(np.arange(120) / 3))

    acf_table, pacf_table = acf_pacf_tables(series, nlags=24)

    expected_columns = {"lag", "correlation", "ci_lower", "ci_upper", "significant"}
    assert len(acf_table) == 25
    assert len(pacf_table) == 25
    assert set(acf_table.columns) == expected_columns
    assert set(pacf_table.columns) == expected_columns
    assert acf_table.loc[0, "correlation"] == pytest.approx(1.0)


@pytest.mark.parametrize("nlags", [0, 60])
def test_e04_acf_pacf_tables_reject_invalid_lags(nlags):
    series = pd.Series(np.arange(120, dtype=float))

    with pytest.raises(ValueError):
        acf_pacf_tables(series, nlags=nlags)


def test_e04_acf_pacf_tables_reject_missing_values():
    series = pd.Series([1.0, np.nan, 3.0])

    with pytest.raises(ValueError):
        acf_pacf_tables(series, nlags=1)
