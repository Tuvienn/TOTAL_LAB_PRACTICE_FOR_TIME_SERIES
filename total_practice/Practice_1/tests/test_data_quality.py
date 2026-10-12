from pathlib import Path

import pandas as pd
import pytest

from practice_1.analysis import (
    apply_missing_value_treatments,
    build_missing_value_comparison,
    detect_residual_iqr_outliers,
    simulate_missing_values,
    summarize_reconstruction_mae,
)
from practice_1.data import load_air_passengers


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "datasets" / "raw" / "air_passengers.csv"
COMPONENTS_PATH = PROJECT_ROOT / "outputs" / "results" / "decomposition_components.csv"
LOCKED_TIMESTAMPS = [
    "1952-03-01",
    "1954-11-01",
    "1959-04-01",
    "1956-06-01",
    "1956-07-01",
    "1956-08-01",
]


def _series() -> pd.Series:
    return load_air_passengers(RAW_PATH)["passengers_thousands"]


def test_missing_experiment_matches_locked_contract() -> None:
    original = _series()
    before = original.copy(deep=True)
    masked, truth = simulate_missing_values(original, LOCKED_TIMESTAMPS)

    pd.testing.assert_series_equal(original, before)
    assert masked.isna().sum() == 6
    assert truth.index.tolist() == sorted(pd.to_datetime(LOCKED_TIMESTAMPS).tolist())
    assert truth.tolist() == [193.0, 203.0, 374.0, 413.0, 405.0, 396.0]

    forward_fill, interpolation = apply_missing_value_treatments(masked)
    assert not forward_fill.isna().any()
    assert not interpolation.isna().any()
    unaffected = ~original.index.isin(truth.index)
    pd.testing.assert_series_equal(
        forward_fill.loc[unaffected].rename(original.name),
        original.loc[unaffected],
    )
    pd.testing.assert_series_equal(
        interpolation.loc[unaffected].rename(original.name),
        original.loc[unaffected],
    )

    comparison = build_missing_value_comparison(truth, forward_fill, interpolation)
    summary = summarize_reconstruction_mae(comparison)
    assert summary.loc[0, "mae_masked_positions"] == pytest.approx(47.833333333333336)
    assert summary.loc[1, "mae_masked_positions"] == pytest.approx(39.71363787818206)


def test_missing_experiment_rejects_invalid_timestamps() -> None:
    original = _series()
    with pytest.raises(ValueError, match="unique"):
        simulate_missing_values(original, ["1952-03-01", "1952-03-01"])
    with pytest.raises(ValueError, match="first or last 12"):
        simulate_missing_values(original, ["1949-01-01"])
    with pytest.raises(ValueError, match="not present"):
        simulate_missing_values(original, ["1970-01-01"])


def test_residual_iqr_outlier_candidates_match_baseline() -> None:
    original = _series()
    components = pd.read_csv(COMPONENTS_PATH, parse_dates=["timestamp"]).set_index(
        "timestamp"
    )
    components.index.freq = original.index.freq
    candidates, thresholds = detect_residual_iqr_outliers(
        original,
        components["residual_log"],
        multiplier=1.5,
    )

    assert len(candidates) == 14
    assert candidates["timestamp"].dt.strftime("%Y-%m").tolist() == [
        "1950-01",
        "1950-05",
        "1950-11",
        "1951-03",
        "1951-05",
        "1953-03",
        "1953-04",
        "1953-05",
        "1954-01",
        "1954-02",
        "1958-04",
        "1958-05",
        "1958-12",
        "1959-03",
    ]
    assert thresholds["lower_fence"] == pytest.approx(-0.03828368232444927)
    assert thresholds["upper_fence"] == pytest.approx(0.03795068457971092)
    assert candidates["flag"].all()
    pd.testing.assert_series_equal(original, _series())
