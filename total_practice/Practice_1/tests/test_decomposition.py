from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_1.analysis import (
    compute_residual_diagnostics,
    compute_stl_decomposition,
    log_transform_series,
)
from practice_1.data import load_air_passengers


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "datasets" / "raw" / "air_passengers.csv"


def _load_series() -> pd.Series:
    return load_air_passengers(RAW_PATH)["passengers_thousands"]


def test_log_transform_preserves_input_and_index() -> None:
    series = _load_series()
    original = series.copy(deep=True)

    transformed = log_transform_series(series)

    pd.testing.assert_series_equal(series, original)
    assert transformed.name == "observed_log"
    assert transformed.index.equals(series.index)
    assert np.isfinite(transformed.to_numpy()).all()
    assert np.allclose(transformed.to_numpy(), np.log(series.to_numpy()))


@pytest.mark.parametrize("invalid_value", [0.0, -1.0, np.nan, np.inf])
def test_log_transform_rejects_invalid_values(invalid_value: float) -> None:
    series = _load_series()
    series.iloc[0] = invalid_value

    with pytest.raises(ValueError):
        log_transform_series(series)


def test_log_transform_rejects_incomplete_monthly_index() -> None:
    series = _load_series().drop(pd.Timestamp("1950-01-01"))

    with pytest.raises(ValueError, match="monthly-start"):
        log_transform_series(series)


def test_stl_components_match_approved_contract() -> None:
    log_series = log_transform_series(_load_series())
    components = compute_stl_decomposition(log_series, period=12, robust=True)

    assert components.columns.tolist() == [
        "observed_log",
        "trend_log",
        "seasonal_log",
        "residual_log",
    ]
    assert components.index.name == "timestamp"
    assert len(components) == 144
    assert components.index.equals(log_series.index)
    assert components.notna().all().all()

    reconstructed = (
        components["trend_log"]
        + components["seasonal_log"]
        + components["residual_log"]
    )
    assert np.allclose(components["observed_log"], reconstructed)
    assert components["residual_log"].mean() == pytest.approx(
        0.0002903949454523917
    )
    assert components["residual_log"].std(ddof=1) == pytest.approx(
        0.02652660295381051
    )


def test_residual_diagnostics_match_approved_contract() -> None:
    components = compute_stl_decomposition(
        log_transform_series(_load_series()),
        period=12,
        robust=True,
    )
    acf_table, diagnostics = compute_residual_diagnostics(
        components["residual_log"],
        max_lag=40,
        alpha=0.05,
        ljung_box_lag=12,
    )

    assert acf_table["lag"].tolist() == list(range(41))
    assert acf_table.loc[1, "acf"] == pytest.approx(0.3747280690749967)
    assert acf_table.loc[12, "acf"] == pytest.approx(-0.1335531725024365)
    assert acf_table[["acf", "lower_ci", "upper_ci"]].notna().all().all()
    assert diagnostics.columns.tolist() == [
        "lag",
        "ljung_box_statistic",
        "p_value",
    ]
    assert diagnostics.loc[0, "lag"] == 12
    assert diagnostics.loc[0, "ljung_box_statistic"] == pytest.approx(
        41.709381406087424
    )
    assert diagnostics.loc[0, "p_value"] == pytest.approx(
        3.7270534544884546e-05
    )
