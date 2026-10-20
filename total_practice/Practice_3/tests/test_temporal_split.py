from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from practice_3.data.temporal_split import (
    APPROVED_VALIDATION_CONFIG,
    EXPECTED_CONFIGURATION_NAMES,
    EXPECTED_CV_FOLDS,
    EXPECTED_TOP_LEVEL,
    build_temporal_split,
    create_top_level_indices,
    get_common_timestamp_index,
    load_validation_config,
    run_phase_04,
    validate_deterministic_split,
    validate_phase_04_entry,
    validate_shared_indices,
    validate_validation_config,
)


VALIDATION_CONFIG_PATH = Path("config/validation.json")


@pytest.fixture(scope="module")
def validation_config():
    return load_validation_config(VALIDATION_CONFIG_PATH)


@pytest.fixture(scope="module")
def phase_04_result(tmp_path_factory):
    audit_path = tmp_path_factory.mktemp("phase_04") / "audit.json"
    datasets, split, audit = run_phase_04(
        validation_config_path=VALIDATION_CONFIG_PATH,
        audit_path=audit_path,
    )
    return datasets, split, audit, audit_path


def test_validation_config_exists_and_matches_contract(validation_config):
    assert VALIDATION_CONFIG_PATH.exists()
    assert validation_config == APPROVED_VALIDATION_CONFIG
    assert validate_validation_config(validation_config) == {
        "approved_contract": True,
        "status": "PASS",
    }


@pytest.mark.parametrize(
    ("section", "key", "invalid_value"),
    [
        (None, "test_start", "2017-09-01 00:00:00"),
        ("cv", "n_splits", 4),
        ("cv", "test_size", 720),
        ("cv", "gap", 24),
        ("policies", "shuffle", True),
        ("policies", "seal_final_test", False),
    ],
)
def test_validation_config_rejects_unapproved_changes(
    validation_config,
    section,
    key,
    invalid_value,
):
    invalid_config = deepcopy(validation_config)
    if section is None:
        invalid_config[key] = invalid_value
    else:
        invalid_config[section][key] = invalid_value

    with pytest.raises(ValueError, match="approved contract"):
        validate_validation_config(invalid_config)


def test_phase_04_entry_gate():
    datasets, config, audit = validate_phase_04_entry(
        validation_config_path=VALIDATION_CONFIG_PATH
    )

    assert tuple(datasets) == EXPECTED_CONFIGURATION_NAMES
    assert config == APPROVED_VALIDATION_CONFIG
    assert audit == {
        "phase_01": "PASS",
        "phase_02": "PASS",
        "phase_03": "PASS",
        "phase_03_reconstruction": "PASS",
        "validation_config": "PASS",
        "status": "PASS",
    }


def test_phase_04_entry_rejects_failed_phase_03_audit(tmp_path):
    failed_audit_path = tmp_path / "phase_03_failed.json"
    with failed_audit_path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "phase": "phase_03_x_y_preparation",
                "status": "FAIL",
            },
            file,
        )

    with pytest.raises(ValueError, match="has not passed"):
        validate_phase_04_entry(
            validation_config_path=VALIDATION_CONFIG_PATH,
            phase_03_audit_path=failed_audit_path,
        )


def test_common_timestamp_index_contract(phase_04_result):
    datasets, split, _, _ = phase_04_result
    timestamp_index = get_common_timestamp_index(datasets)

    assert timestamp_index.equals(split.timestamp_index)
    assert len(timestamp_index) == EXPECTED_TOP_LEVEL["total_rows"]
    assert timestamp_index.is_unique
    assert timestamp_index.is_monotonic_increasing


def test_common_timestamp_index_rejects_configuration_drift(
    phase_04_result,
):
    datasets, _, _, _ = phase_04_result
    corrupted = dict(datasets)
    original = corrupted["lag_only_p72"]
    corrupted["lag_only_p72"] = replace(
        original,
        timestamp_index=original.timestamp_index[1:],
    )

    with pytest.raises(ValueError, match="common timestamp index"):
        get_common_timestamp_index(corrupted)


def test_top_level_split_contract(phase_04_result):
    _, split, audit, _ = phase_04_result
    top_level = audit["top_level_split"]

    for key, expected_value in EXPECTED_TOP_LEVEL.items():
        assert top_level[key] == expected_value
    assert len(split.train_indices) == 108_083
    assert len(split.test_indices) == 8_592
    assert top_level["train_test_disjoint"] is True
    assert top_level["train_test_complete_union"] is True
    assert top_level["chronological_boundary"] is True
    assert top_level["status"] == "PASS"


def test_top_level_indices_are_complete_disjoint_and_readonly(
    phase_04_result,
):
    _, split, _, _ = phase_04_result
    expected = np.arange(len(split.timestamp_index))
    combined = np.sort(
        np.concatenate((split.train_indices, split.test_indices))
    )

    assert np.intersect1d(split.train_indices, split.test_indices).size == 0
    assert np.array_equal(combined, expected)
    assert split.train_indices.flags.writeable is False
    assert split.test_indices.flags.writeable is False
    with pytest.raises(ValueError):
        split.train_indices[0] = 1


def test_top_level_split_rejects_unapproved_config(
    phase_04_result,
    validation_config,
):
    _, split, _, _ = phase_04_result
    invalid_config = deepcopy(validation_config)
    invalid_config["test_start"] = "2017-09-01 00:00:00"

    with pytest.raises(ValueError, match="approved contract"):
        create_top_level_indices(split.timestamp_index, invalid_config)


def test_cv_fold_counts_and_boundaries(phase_04_result):
    _, split, audit, _ = phase_04_result
    cv_audit = audit["cross_validation"]

    assert len(split.cv_fold_indices) == 5
    assert cv_audit["n_splits"] == 5
    assert cv_audit["test_size"] == 2160
    assert cv_audit["gap"] == 0

    for actual, expected in zip(cv_audit["folds"], EXPECTED_CV_FOLDS):
        for key, expected_value in expected.items():
            assert actual[key] == expected_value


def test_cv_folds_are_expanding_and_disjoint(phase_04_result):
    _, split, audit, _ = phase_04_result
    validation_indices = []

    for previous, current in zip(
        split.cv_fold_indices,
        split.cv_fold_indices[1:],
    ):
        assert len(current.train_indices) > len(previous.train_indices)
        assert np.array_equal(
            current.train_indices[: len(previous.train_indices)],
            previous.train_indices,
        )

    for fold in split.cv_fold_indices:
        assert fold.train_indices[-1] < fold.validation_indices[0]
        assert np.intersect1d(
            fold.train_indices,
            fold.validation_indices,
        ).size == 0
        validation_indices.append(fold.validation_indices)

    combined = np.concatenate(validation_indices)
    assert len(np.unique(combined)) == len(combined)
    assert audit["cross_validation"]["training_windows_expand"] is True
    assert audit["cross_validation"]["validation_folds_disjoint"] is True


def test_final_test_is_excluded_from_cross_validation(phase_04_result):
    _, split, audit, _ = phase_04_result

    for fold in split.cv_fold_indices:
        assert np.intersect1d(
            fold.train_indices,
            split.test_indices,
        ).size == 0
        assert np.intersect1d(
            fold.validation_indices,
            split.test_indices,
        ).size == 0

    assert audit["cross_validation"]["final_test_excluded"] is True
    assert audit["final_test"] == {
        "sealed": True,
        "used_for_feature_selection": False,
        "used_for_tuning": False,
        "used_for_model_selection": False,
        "metrics_computed": False,
        "status": "PASS",
    }


def test_all_configurations_share_split_indices(phase_04_result):
    datasets, split, audit, _ = phase_04_result
    validation = validate_shared_indices(datasets, split)

    assert validation["configuration_count"] == 6
    assert validation["configuration_names"] == list(
        EXPECTED_CONFIGURATION_NAMES
    )
    assert validation["shared_top_level_indices"] is True
    assert validation["shared_cv_indices"] is True
    assert validation["status"] == "PASS"
    assert audit["shared_indices"] == validation


def test_split_application_preserves_alignment(phase_04_result):
    datasets, split, _, _ = phase_04_result

    for dataset in datasets.values():
        for indices in (split.train_indices, split.test_indices):
            X = dataset.X.iloc[indices]
            y = dataset.y.iloc[indices]
            metadata = dataset.aligned_metadata.iloc[indices]

            assert X.index.equals(y.index)
            assert X.index.equals(metadata.index)
            assert X.index.is_monotonic_increasing


def test_temporal_split_is_deterministic(
    phase_04_result,
    validation_config,
):
    datasets, split, audit, _ = phase_04_result
    validation = validate_deterministic_split(
        datasets,
        validation_config,
        split,
    )

    assert validation == {
        "deterministic_split": True,
        "status": "PASS",
    }
    assert audit["determinism"] == validation


def test_build_temporal_split_matches_official_result(
    phase_04_result,
    validation_config,
):
    datasets, official_split, _, _ = phase_04_result
    rebuilt_split, _, _ = build_temporal_split(
        datasets,
        validation_config,
    )

    assert np.array_equal(
        rebuilt_split.train_indices,
        official_split.train_indices,
    )
    assert np.array_equal(
        rebuilt_split.test_indices,
        official_split.test_indices,
    )


def test_phase_04_audit_round_trip(phase_04_result):
    _, _, audit, audit_path = phase_04_result

    with audit_path.open("r", encoding="utf-8") as file:
        saved_audit = json.load(file)

    assert saved_audit == audit
    assert audit["phase"] == "phase_04_temporal_split_validation"
    assert audit["full_split_datasets_persisted"] is False
    assert audit["status"] == "PASS"
