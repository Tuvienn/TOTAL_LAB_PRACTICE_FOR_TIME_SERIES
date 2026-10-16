from pathlib import Path

import pandas as pd

from practice_2.data.time_series_data import chronological_split, load_monthly_retail_sales
from practice_2.analysis.stationarity import first_difference, run_adf


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
