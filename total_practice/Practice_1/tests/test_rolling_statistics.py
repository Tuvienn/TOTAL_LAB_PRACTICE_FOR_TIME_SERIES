from pathlib import Path

import pandas as pd
import pytest

from practice_1.analysis import (
    build_month_year_matrix,
    compute_rolling_statistics,
    prepare_monthly_seasonal_data,
    summarize_monthly_pattern,
)
from practice_1.data import load_air_passengers


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "datasets" / "raw" / "air_passengers.csv"


def _series() -> pd.Series:
    return load_air_passengers(RAW_PATH)["passengers_thousands"]


def test_rolling_statistics_match_approved_contract() -> None:
    series = _series()
    before = series.copy(deep=True)
    result = compute_rolling_statistics(
        series,
        window=12,
        min_periods=12,
        center=False,
        std_ddof=1,
    )

    pd.testing.assert_series_equal(series, before)
    assert result.columns.tolist() == [
        "observed_value",
        "rolling_mean_12",
        "rolling_std_12",
    ]
    assert result.index.equals(series.index)
    assert result.index.name == "timestamp"
    assert result["rolling_mean_12"].isna().sum() == 11
    assert result["rolling_std_12"].isna().sum() == 11
    assert result["rolling_mean_12"].first_valid_index() == pd.Timestamp("1949-12-01")
    assert result["rolling_std_12"].first_valid_index() == pd.Timestamp("1949-12-01")
    assert result.loc["1949-12-01", "rolling_mean_12"] == pytest.approx(
        series.iloc[:12].mean()
    )
    assert result.loc["1949-12-01", "rolling_std_12"] == pytest.approx(
        series.iloc[:12].std(ddof=1)
    )
    assert result.loc["1960-12-01", "rolling_mean_12"] == pytest.approx(
        476.1666666666667
    )
    assert result.loc["1960-12-01", "rolling_std_12"] == pytest.approx(
        77.73712501797809
    )


def test_rolling_statistics_reject_invalid_protocol_and_input() -> None:
    series = _series()
    with pytest.raises(ValueError, match="center must be False"):
        compute_rolling_statistics(series, center=True)
    with pytest.raises(ValueError, match="missing or non-finite"):
        compute_rolling_statistics(series.mask(series.index == series.index[20]))

    duplicated = pd.concat([series, series.iloc[[0]]]).sort_index()
    with pytest.raises(ValueError, match="duplicate"):
        compute_rolling_statistics(duplicated)


def test_seasonal_data_and_matrix_match_air_passengers() -> None:
    seasonal_data = prepare_monthly_seasonal_data(_series())
    matrix = build_month_year_matrix(seasonal_data, expected_shape=(12, 12))
    summary = summarize_monthly_pattern(seasonal_data)

    assert seasonal_data.columns.tolist() == [
        "timestamp",
        "year",
        "month",
        "observed_value",
    ]
    assert len(seasonal_data) == 144
    assert matrix.shape == (12, 12)
    assert matrix.index.tolist() == list(range(1, 13))
    assert matrix.columns.tolist() == list(range(1949, 1961))
    assert matrix.loc[1, 1949] == 112.0
    assert matrix.loc[12, 1960] == 432.0
    assert int(summary.loc[summary["mean_value"].idxmax(), "month"]) == 7
    assert int(summary.loc[summary["mean_value"].idxmin(), "month"]) == 11


def test_month_year_matrix_rejects_duplicate_cells() -> None:
    seasonal_data = prepare_monthly_seasonal_data(_series())
    duplicate = pd.concat([seasonal_data, seasonal_data.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate"):
        build_month_year_matrix(duplicate, expected_shape=(12, 12))
