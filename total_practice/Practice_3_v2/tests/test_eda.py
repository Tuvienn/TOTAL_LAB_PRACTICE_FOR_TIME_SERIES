from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd

from practice_3_v2.analysis.eda import (
    PROJECT_ROOT,
    build_daily_trend,
    build_seasonality_profiles,
    calculate_lag_correlations,
    extract_development_data,
    load_phase_03_inputs,
    run_phase_03,
    screen_robust_anomalies,
    summarize_distribution,
    summarize_missingness,
    validate_development_data,
)
from practice_3_v2.data.temporal_split import validate_prepared_input


(
    DATA_CONTRACT,
    PREPARATION_CONTRACT,
    SPLIT_CONTRACT,
    EDA_CONTRACT,
    PHASE_01_AUDIT,
    PHASE_02_AUDIT,
) = load_phase_03_inputs()


def load_prepared_and_development() -> tuple[pd.DataFrame, pd.DataFrame]:
    prepared, _ = validate_prepared_input(
        PROJECT_ROOT / EDA_CONTRACT["prepared_input"],
        DATA_CONTRACT,
        PREPARATION_CONTRACT,
        SPLIT_CONTRACT,
        PHASE_01_AUDIT,
    )
    development = extract_development_data(
        prepared,
        DATA_CONTRACT,
        SPLIT_CONTRACT,
    )
    return prepared, development


def test_upstream_identities_are_locked() -> None:
    assert PHASE_02_AUDIT["status"] == "PASS"
    assert PHASE_02_AUDIT["prepared_sha256"] == EDA_CONTRACT[
        "prepared_sha256"
    ]
    assert EDA_CONTRACT["holdout_policy"] == {
        "excluded_from_eda": True,
        "target_values_inspected": False,
    }


def test_development_boundary_and_counts() -> None:
    _, development = load_prepared_and_development()
    validate_development_data(development, DATA_CONTRACT, EDA_CONTRACT)
    assert len(development) == 112_535
    assert development["AEP_MW"].notna().sum() == 112_509
    assert development["AEP_MW"].isna().sum() == 26
    assert development["Datetime"].max() < pd.Timestamp(
        "2017-08-03 00:00:00"
    )


def test_development_timeline_remains_hourly_and_unique() -> None:
    _, development = load_prepared_and_development()
    assert development["Datetime"].is_unique
    assert development["Datetime"].is_monotonic_increasing
    assert development["Datetime"].diff().dropna().eq(
        pd.Timedelta(hours=1)
    ).all()


def test_holdout_target_mutation_cannot_change_eda_input() -> None:
    prepared, expected = load_prepared_and_development()
    mutated = prepared.copy(deep=True)
    holdout_mask = mutated["Datetime"].ge("2017-08-03 00:00:00")
    mutated.loc[holdout_mask, "AEP_MW"] = 9_999_999.0
    actual = extract_development_data(mutated, DATA_CONTRACT, SPLIT_CONTRACT)
    pd.testing.assert_frame_equal(actual, expected)


def test_missingness_is_reported_without_imputation() -> None:
    _, development = load_prepared_and_development()
    before = development["AEP_MW"].copy(deep=True)
    summary = summarize_missingness(development, DATA_CONTRACT)
    assert summary["missing_targets"] == 26
    assert len(summary["missing_timestamps"]) == 26
    assert sum(item["count"] for item in summary["by_year"]) == 26
    assert summary["missing_metadata_valid"] is True
    assert summary["imputation_applied"] is False
    pd.testing.assert_series_equal(development["AEP_MW"], before)


def test_distribution_uses_only_observed_development_targets() -> None:
    _, development = load_prepared_and_development()
    summary = summarize_distribution(
        development,
        DATA_CONTRACT,
        EDA_CONTRACT,
    )
    assert summary["count"] == 112_509
    assert summary["minimum"] > 0
    assert summary["minimum"] <= summary["median"] <= summary["maximum"]
    assert np.isclose(summary["iqr"], summary["q75"] - summary["q25"])


def test_daily_trend_uses_approved_trailing_window() -> None:
    _, development = load_prepared_and_development()
    trend = build_daily_trend(development, DATA_CONTRACT, EDA_CONTRACT)
    assert trend["date"].is_monotonic_increasing
    assert trend["rolling_mean_30d"].iloc[:29].isna().all()
    assert trend["rolling_mean_30d"].iloc[29:].notna().all()
    assert trend["observed_hours"].sum() == 112_509


def test_seasonality_profiles_have_complete_categories_and_support() -> None:
    _, development = load_prepared_and_development()
    profiles = build_seasonality_profiles(development, DATA_CONTRACT)
    assert profiles["hour_of_day"]["hour"].tolist() == list(range(24))
    assert profiles["day_of_week"]["day_of_week"].tolist() == list(range(7))
    assert profiles["month"]["month"].tolist() == list(range(1, 13))
    assert profiles["hour_day_heatmap"].shape == (7, 24)
    assert profiles["hour_of_day"]["observed_count"].sum() == 112_509


def test_lag_correlations_cover_approved_range() -> None:
    _, development = load_prepared_and_development()
    correlations = calculate_lag_correlations(
        development,
        DATA_CONTRACT,
        EDA_CONTRACT,
    )
    assert correlations["lag_hours"].tolist() == list(range(1, 169))
    assert correlations["correlation"].notna().all()
    assert {1, 24, 168}.issubset(set(correlations["lag_hours"]))
    assert (correlations["valid_pairs"] > 0).all()


def test_lag_correlation_does_not_compress_a_missing_gap() -> None:
    synthetic = pd.DataFrame(
        {
            "Datetime": pd.date_range("2020-01-01", periods=5, freq="h"),
            "AEP_MW": [1.0, 2.0, np.nan, 4.0, 5.0],
        }
    )
    contract = deepcopy(EDA_CONTRACT)
    contract["lag_correlation"]["maximum_lag_hours"] = 1
    correlation = calculate_lag_correlations(
        synthetic,
        DATA_CONTRACT,
        contract,
    )
    assert correlation.loc[0, "valid_pairs"] == 2


def test_anomaly_screening_does_not_change_target() -> None:
    _, development = load_prepared_and_development()
    before = development["AEP_MW"].copy(deep=True)
    candidates, summary = screen_robust_anomalies(
        development,
        DATA_CONTRACT,
        EDA_CONTRACT,
    )
    assert summary["observed_targets"] == 112_509
    assert summary["candidate_count"] == len(candidates)
    assert summary["target_treatment"] == "none"
    pd.testing.assert_series_equal(development["AEP_MW"], before)


def test_zero_mad_and_low_support_are_not_evaluable() -> None:
    synthetic = pd.DataFrame(
        {
            "Datetime": pd.date_range("2020-01-06", periods=10, freq="7D"),
            "AEP_MW": [100.0] * 10,
        }
    )
    contract = deepcopy(EDA_CONTRACT)
    contract["anomaly_screening"]["minimum_group_support"] = 20
    candidates, summary = screen_robust_anomalies(
        synthetic,
        DATA_CONTRACT,
        contract,
    )
    assert candidates.empty
    assert summary["evaluable_targets"] == 0
    assert summary["not_evaluable_targets"] == 10


def test_phase_03_bundle_is_deterministic_and_complete(tmp_path: Path) -> None:
    first_summary = tmp_path / "first.json"
    second_summary = tmp_path / "second.json"
    first_figures = tmp_path / "first_figures"
    second_figures = tmp_path / "second_figures"
    first = run_phase_03(PROJECT_ROOT, first_summary, first_figures)
    second = run_phase_03(PROJECT_ROOT, second_summary, second_figures)
    assert first == second
    assert first_summary.read_bytes() == second_summary.read_bytes()
    assert len(first["figures"]) == 6
    for record in first["figures"]:
        first_path = first_figures / Path(record["path"]).name
        second_path = second_figures / Path(record["path"]).name
        assert first_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        assert first_path.read_bytes() == second_path.read_bytes()
        assert first_path.stat().st_size > 0


def test_phase_03_audit_contains_no_holdout_target_statistics(
    tmp_path: Path,
) -> None:
    audit = run_phase_03(
        PROJECT_ROOT,
        tmp_path / "summary.json",
        tmp_path / "figures",
    )
    assert audit["holdout"] == {
        "excluded_from_eda": True,
        "target_values_inspected": False,
        "rows_excluded": 8761,
        "label": "historical_re_evaluation_holdout",
    }
    assert audit["checks"]["holdout_target_values_inspected"] is False
    assert audit["checks"]["missing_target_imputed"] is False


def test_pipeline_source_does_not_import_legacy_package() -> None:
    source = (
        PROJECT_ROOT / "src/practice_3_v2/analysis/eda.py"
    ).read_text(encoding="utf-8")
    assert "from practice_3 " not in source
    assert "import practice_3" not in source
