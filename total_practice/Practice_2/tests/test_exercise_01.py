from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_2.data.time_series_data import chronological_split, load_monthly_retail_sales
from practice_2.analysis import stationarity
from practice_2.analysis.stationarity import first_difference, log_first_difference, run_adf


ROOT = Path(__file__).parents[1]


def test_e01_loader_contract():
    series = load_monthly_retail_sales(ROOT / "datasets" / "raw" / "a10.csv")
    assert isinstance(series.index, pd.DatetimeIndex)
    assert len(series) == 204
    assert series.index.freqstr == "MS"
    assert series.notna().all()


def test_e01_chronological_split():
    series = load_monthly_retail_sales(ROOT / "datasets" / "raw" / "a10.csv")
    train, test = chronological_split(series)
    assert len(train) == 163
    assert len(test) == 41
    assert train.index.max() < test.index.min()


def test_e02_adf_contract_uses_training_series_only():
    series = load_monthly_retail_sales(ROOT / "datasets" / "raw" / "a10.csv")
    train, test = chronological_split(series)
    result, critical = run_adf(train, alpha=0.05)
    assert len(train) == 163
    assert len(test) == 41
    assert {"adf_statistic", "p_value", "alpha", "decision"}.issubset(set(result["metric"]))
    assert set(critical.columns) == {"critical_value", "value"}


def test_e03_first_difference_preserves_alignment():
    series = load_monthly_retail_sales(ROOT / "datasets" / "raw" / "a10.csv")
    train, _ = chronological_split(series)
    differenced = first_difference(train)
    assert len(differenced) == len(train) - 1
    assert differenced.index[0] == train.index[1]
    assert differenced.index[-1] == train.index[-1]


def test_e03_log_first_difference_uses_training_series_only():
    series = load_monthly_retail_sales(ROOT / "datasets" / "raw" / "a10.csv")
    train, test = chronological_split(series)
    original_train = train.copy()
    transformed = log_first_difference(train)

    assert len(train) == 163
    assert len(test) == 41
    assert len(transformed) == 162
    assert transformed.notna().all()
    assert transformed.index[0] == train.index[1]
    assert transformed.index[-1] == train.index[-1]
    assert transformed.iloc[0] == pytest.approx(np.log(train.iloc[1]) - np.log(train.iloc[0]))
    pd.testing.assert_series_equal(train, original_train)
    assert transformed.index.max() < test.index.min()


@pytest.mark.parametrize(
    "values",
    [
        pd.Series(dtype=float),
        pd.Series([1.0, 0.0]),
        pd.Series([1.0, -1.0]),
        pd.Series([1.0, np.nan]),
    ],
)
def test_e03_log_first_difference_rejects_invalid_input(values):
    with pytest.raises(ValueError):
        log_first_difference(values)


def test_e03_adf_configuration_is_explicit(monkeypatch):
    captured = {}

    def fake_adfuller(series, **kwargs):
        captured.update(kwargs)
        return -3.0, 0.01, 1, 10, {"1%": -3.5, "5%": -2.9, "10%": -2.6}, 0.0

    monkeypatch.setattr(stationarity, "adfuller", fake_adfuller)
    result, _ = run_adf(pd.Series([1.0, 0.5, 0.25]), alpha=0.05)

    assert captured == {"regression": "c", "autolag": "AIC"}
    assert result.loc[result["metric"].eq("decision"), "value"].iloc[0] == "reject H0"


def test_e03_log_first_difference_adf_result():
    series = load_monthly_retail_sales(ROOT / "datasets" / "raw" / "a10.csv")
    train, _ = chronological_split(series)
    transformed = log_first_difference(train)
    result, critical = run_adf(transformed, alpha=0.05)
    values = dict(zip(result["metric"], result["value"]))

    assert float(values["adf_statistic"]) == pytest.approx(-3.6594861402, rel=1e-9)
    assert float(values["p_value"]) == pytest.approx(0.0047204835, rel=1e-8)
    assert values["decision"] == "reject H0"
    assert float(values["p_value"]) <= float(values["alpha"])
    assert set(critical["critical_value"]) == {"1%", "5%", "10%"}
