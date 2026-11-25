from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3.analysis.eda import extract_development_data
from practice_3.data.supervised_dataset import (
    PROJECT_ROOT,
    apply_expanding_window_folds,
    build_supervised_candidates,
    extract_eligible_xy,
    load_phase_05_inputs,
    run_phase_05,
    validate_supervised_contract,
    validate_supervised_population,
)
from practice_3.data.temporal_split import validate_prepared_input


(
    DATA_CONTRACT,
    PREPARATION_CONTRACT,
    SPLIT_CONTRACT,
    FEATURE_CONTRACT,
    SUPERVISED_CONTRACT,
    PHASE_01_AUDIT,
    PHASE_02_AUDIT,
    PHASE_03_AUDIT,
    PHASE_04_AUDIT,
) = load_phase_05_inputs()


def load_prepared_and_development() -> tuple[pd.DataFrame, pd.DataFrame]:
    prepared, _ = validate_prepared_input(
        PROJECT_ROOT / SUPERVISED_CONTRACT["prepared_input"],
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


def load_development_candidates() -> tuple[pd.DataFrame, pd.DataFrame]:
    _, development = load_prepared_and_development()
    candidates = build_supervised_candidates(
        development,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    return development, candidates


def synthetic_data(periods: int = 220) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Datetime": pd.date_range("2020-01-01", periods=periods, freq="h"),
            "AEP_MW": np.arange(1, periods + 1, dtype="float64"),
        }
    )


def test_upstream_identities_and_status_are_locked() -> None:
    assert PHASE_02_AUDIT["status"] == "PASS"
    assert PHASE_03_AUDIT["status"] == "PASS"
    assert PHASE_04_AUDIT["status"] == "PASS"
    assert PHASE_04_AUDIT["feature_order"] == SUPERVISED_CONTRACT[
        "feature_order"
    ]


def test_supervised_contract_matches_approved_protocol() -> None:
    validate_supervised_contract(
        SUPERVISED_CONTRACT,
        DATA_CONTRACT,
        SPLIT_CONTRACT,
        FEATURE_CONTRACT,
    )
    assert len(SUPERVISED_CONTRACT["feature_order"]) == 22
    assert SUPERVISED_CONTRACT["scope"]["persist_xy_table"] is False
    assert SUPERVISED_CONTRACT["scope"][
        "holdout_features_materialized"
    ] is False


@pytest.mark.parametrize(
    ("section", "key", "value", "message"),
    [
        ("alignment", "forecast_origin_offset_hours", 0, "alignment"),
        ("eligibility", "imputation", "median", "Eligibility"),
        ("cross_validation", "gap_hours", 24, "Cross-validation"),
        ("scope", "persist_xy_table", True, "scope"),
    ],
)
def test_invalid_supervised_contract_is_rejected(
    section: str,
    key: str,
    value: object,
    message: str,
) -> None:
    contract = deepcopy(SUPERVISED_CONTRACT)
    contract[section][key] = value
    with pytest.raises(ValueError, match=message):
        validate_supervised_contract(
            contract,
            DATA_CONTRACT,
            SPLIT_CONTRACT,
            FEATURE_CONTRACT,
        )


def test_one_step_target_origin_and_feature_alignment() -> None:
    data = synthetic_data()
    candidates = build_supervised_candidates(
        data,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    row = candidates.iloc[168]
    assert row["target_timestamp"] == data.loc[168, "Datetime"]
    assert row["forecast_origin"] == data.loc[167, "Datetime"]
    assert row["lag_1h"] == data.loc[167, "AEP_MW"]
    assert row["AEP_MW"] == data.loc[168, "AEP_MW"]
    assert row["is_eligible"]


def test_X_schema_excludes_target_metadata_and_control_fields() -> None:
    data = synthetic_data()
    candidates = build_supervised_candidates(
        data,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    mask = pd.Series(True, index=candidates.index)
    partition = extract_eligible_xy(
        candidates,
        mask,
        DATA_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    assert partition.X.columns.tolist() == SUPERVISED_CONTRACT["feature_order"]
    forbidden = {
        "AEP_MW",
        "Datetime",
        "target_timestamp",
        "forecast_origin",
        "quality_flag",
        "source_count",
        "is_eligible",
        "exclusion_reason",
    }
    assert forbidden.isdisjoint(partition.X.columns)


def test_development_eligibility_and_exclusion_counts() -> None:
    _, candidates = load_development_candidates()
    counts = candidates["exclusion_reason"].value_counts().to_dict()
    assert len(candidates) == 112_535
    assert counts == {
        "eligible": 108_083,
        "invalid_feature_vector": 4_427,
        "missing_target_with_valid_features": 25,
    }
    assert sum(counts.values()) == len(candidates)


def test_eligible_X_y_are_finite_aligned_and_chronological() -> None:
    _, candidates = load_development_candidates()
    partition = extract_eligible_xy(
        candidates,
        pd.Series(True, index=candidates.index),
        DATA_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    assert len(partition.X) == 108_083
    assert np.isfinite(partition.X.to_numpy(dtype="float64")).all()
    assert np.isfinite(partition.y.to_numpy(dtype="float64")).all()
    assert partition.X.index.equals(partition.y.index)
    assert partition.X.index.is_unique
    assert partition.X.index.is_monotonic_increasing
    assert partition.X.index.min() == pd.Timestamp("2004-10-08 01:00:00")
    assert partition.X.index.max() == pd.Timestamp("2017-08-02 23:00:00")


def test_five_fold_eligible_counts_and_chronology() -> None:
    development, candidates = load_development_candidates()
    folds = apply_expanding_window_folds(
        candidates,
        DATA_CONTRACT,
        SPLIT_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    validate_supervised_population(
        candidates,
        folds,
        development,
        DATA_CONTRACT,
        SPLIT_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    assert [(len(fold.train.X), len(fold.validation.X)) for fold in folds] == [
        (65_670, 8_253),
        (73_923, 8_363),
        (82_286, 8_591),
        (90_877, 8_615),
        (99_492, 8_591),
    ]
    for fold in folds:
        assert fold.train.X.index.max() < fold.validation.X.index.min()
        assert fold.train.X.index.intersection(fold.validation.X.index).empty


def test_one_step_validation_uses_actual_previous_hour() -> None:
    _, candidates = load_development_candidates()
    folds = apply_expanding_window_folds(
        candidates,
        DATA_CONTRACT,
        SPLIT_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    for fold in folds:
        second_timestamp = fold.validation.X.index[1]
        previous_timestamp = second_timestamp - pd.Timedelta(hours=1)
        previous_actual = candidates.loc[
            candidates["target_timestamp"].eq(previous_timestamp), "AEP_MW"
        ].iloc[0]
        assert fold.validation.X.loc[second_timestamp, "lag_1h"] == previous_actual


def test_current_and_future_target_mutation_does_not_change_current_X() -> None:
    data = synthetic_data()
    target_row = 190
    expected = build_supervised_candidates(
        data,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    mutated = data.copy(deep=True)
    mutated.loc[target_row:, "AEP_MW"] = 9_999_999.0
    actual = build_supervised_candidates(
        mutated,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    feature_order = SUPERVISED_CONTRACT["feature_order"]
    pd.testing.assert_series_equal(
        actual.loc[target_row, feature_order],
        expected.loc[target_row, feature_order],
    )
    assert actual.loc[target_row, "AEP_MW"] != expected.loc[target_row, "AEP_MW"]


def test_holdout_mutation_cannot_change_development_candidates() -> None:
    prepared, development = load_prepared_and_development()
    expected = build_supervised_candidates(
        development,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    mutated = prepared.copy(deep=True)
    holdout_mask = mutated["Datetime"].ge(
        SPLIT_CONTRACT["holdout"]["start_inclusive"]
    )
    mutated.loc[holdout_mask, "AEP_MW"] = 9_999_999.0
    mutated_development = extract_development_data(
        mutated,
        DATA_CONTRACT,
        SPLIT_CONTRACT,
    )
    actual = build_supervised_candidates(
        mutated_development,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    pd.testing.assert_frame_equal(actual, expected)


def test_supervised_builder_does_not_modify_input() -> None:
    data = synthetic_data()
    before = data.copy(deep=True)
    build_supervised_candidates(
        data,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
        SUPERVISED_CONTRACT,
    )
    pd.testing.assert_frame_equal(data, before)


def test_phase_05_audit_is_deterministic_and_development_only(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first = run_phase_05(PROJECT_ROOT, first_path)
    second = run_phase_05(PROJECT_ROOT, second_path)
    assert first == second
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["development"]["eligible_rows"] == 108_083
    assert first["holdout"] == {
        "reserved": True,
        "features_materialized": False,
        "target_statistics_reported": False,
        "evaluation_owner": "phase_07",
    }
    assert first["recursive_24h"]["matrix_materialized"] is False
    assert first["persistence"]["xy_table_written"] is False
    assert first["status"] == "PASS"
    with first_path.open(encoding="utf-8") as file:
        assert json.load(file) == first


def test_pipeline_source_does_not_import_legacy_package() -> None:
    source = (
        PROJECT_ROOT / "src/practice_3/data/supervised_dataset.py"
    ).read_text(encoding="utf-8")
    assert "from practice_3 " not in source
    assert "import practice_3" not in source
