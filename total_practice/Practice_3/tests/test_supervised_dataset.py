import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3.analysis.feature_engineering import (
    generate_feature_table,
    validate_phase_02_entry,
)
from practice_3.data.supervised_dataset import (
    EXPECTED_FIRST_TIMESTAMP,
    EXPECTED_LAG_ONLY_COUNTS,
    EXPECTED_LAST_TIMESTAMP,
    EXPECTED_REMOVED_ROWS,
    EXPECTED_USABLE_ROWS,
    FORBIDDEN_FEATURES,
    build_common_validity_mask,
    build_feature_definitions,
    run_phase_03,
    validate_deterministic_construction,
    validate_feature_table,
    validate_phase_03_entry,
    validate_supervised_datasets,
)


CONFIG_PATH = Path("config/feature_engineering.json")


@pytest.fixture(scope="module")
def feature_context():
    source_df, config, _ = validate_phase_02_entry(CONFIG_PATH)
    feature_df = generate_feature_table(source_df, config)
    return config, feature_df


@pytest.fixture(scope="module")
def phase_03_result(tmp_path_factory):
    audit_path = tmp_path_factory.mktemp("phase_03") / "audit.json"
    datasets, audit = run_phase_03(
        config_path=CONFIG_PATH,
        audit_path=audit_path,
    )
    return datasets, audit, audit_path


def test_phase_03_entry_gate():
    source_df, config, feature_df, audit = validate_phase_03_entry(
        config_path=CONFIG_PATH
    )

    assert len(source_df) == 121_296
    assert len(feature_df) == 121_296
    assert config["lag_features"]["max_lag"] == 168
    assert audit == {
        "phase_01": "PASS",
        "phase_02": "PASS",
        "input_contract": "PASS",
        "feature_integrity": "PASS",
        "status": "PASS",
    }


def test_phase_03_entry_rejects_failed_upstream_audit(tmp_path):
    failed_audit_path = tmp_path / "phase_02_failed.json"
    failed_audit = {
        "phase": "phase_02_feature_engineering",
        "status": "FAIL",
    }
    with failed_audit_path.open("w", encoding="utf-8") as file:
        json.dump(failed_audit, file)

    with pytest.raises(ValueError, match="has not passed"):
        validate_phase_03_entry(
            config_path=CONFIG_PATH,
            phase_02_audit_path=failed_audit_path,
        )


def test_feature_definitions_are_complete_and_ordered(feature_context):
    config, _ = feature_context
    definitions = build_feature_definitions(config)

    assert list(definitions) == [
        "lag_only_p24",
        "lag_only_p72",
        "lag_only_p168",
        "lag_rolling_p24",
        "lag_rolling_p72",
        "lag_rolling_p168",
    ]
    assert {name: len(columns) for name, columns in definitions.items()} == {
        "lag_only_p24": 24,
        "lag_only_p72": 72,
        "lag_only_p168": 168,
        "lag_rolling_p24": 28,
        "lag_rolling_p72": 76,
        "lag_rolling_p168": 172,
    }
    assert definitions["lag_only_p168"][0] == "lag_1"
    assert definitions["lag_only_p168"][-1] == "lag_168"
    assert definitions["lag_rolling_p24"][-4:] == (
        "rolling_mean_24",
        "rolling_std_24",
        "rolling_mean_168",
        "rolling_std_168",
    )


def test_feature_table_contract(feature_context):
    config, feature_df = feature_context
    audit = validate_feature_table(feature_df, config)

    assert audit["rows"] == 121_296
    assert audit["columns"] == 176
    assert audit["schema_and_order_valid"] is True
    assert audit["timestamps_unique"] is True
    assert audit["chronologically_sorted"] is True
    assert audit["status"] == "PASS"


def test_common_validity_mask_and_row_loss(feature_context):
    config, feature_df = feature_context
    common_valid, audit = build_common_validity_mask(feature_df, config)

    assert common_valid.dtype == bool
    assert int(common_valid.sum()) == EXPECTED_USABLE_ROWS
    assert audit["lag_only_usable_rows"] == EXPECTED_LAG_ONLY_COUNTS
    assert audit["removed_unique_rows"] == EXPECTED_REMOVED_ROWS
    assert audit["usable_rows"] == EXPECTED_USABLE_ROWS
    assert audit["first_usable_timestamp"] == str(EXPECTED_FIRST_TIMESTAMP)
    assert audit["last_usable_timestamp"] == str(EXPECTED_LAST_TIMESTAMP)
    assert sum(audit["reason_counts"].values()) > EXPECTED_REMOVED_ROWS
    assert audit["status"] == "PASS"


def test_common_validity_mask_rejects_unexpected_input(feature_context):
    config, feature_df = feature_context
    truncated_feature_df = feature_df.iloc[:-1]

    with pytest.raises(ValueError, match="acceptance values changed"):
        build_common_validity_mask(truncated_feature_df, config)


def test_six_supervised_dataset_contracts(phase_03_result, feature_context):
    datasets, _, _ = phase_03_result
    config, _ = feature_context
    audit = validate_supervised_datasets(datasets, config)

    assert audit["configuration_count"] == 6
    assert audit["shared_timestamp_index"] is True
    assert all(
        result["samples"] == EXPECTED_USABLE_ROWS
        for result in audit["datasets"].values()
    )
    assert audit["status"] == "PASS"


def test_supervised_alignment_and_values(phase_03_result, feature_context):
    datasets, _, _ = phase_03_result
    _, feature_df = feature_context
    indexed_features = feature_df.set_index("Datetime")

    for dataset in datasets.values():
        expected_target = indexed_features.loc[
            dataset.timestamp_index,
            "AEP_MW",
        ]
        expected_metadata = indexed_features.loc[
            dataset.timestamp_index,
            ["source_count", "quality_flag"],
        ]

        pd.testing.assert_series_equal(dataset.y, expected_target)
        pd.testing.assert_frame_equal(
            dataset.aligned_metadata,
            expected_metadata,
        )
        assert dataset.X.index.equals(dataset.y.index)
        assert dataset.X.index.equals(dataset.aligned_metadata.index)
        assert dataset.X.index.equals(dataset.timestamp_index)


def test_supervised_outputs_have_no_leakage_or_invalid_values(
    phase_03_result,
):
    datasets, _, _ = phase_03_result

    for dataset in datasets.values():
        assert not FORBIDDEN_FEATURES.intersection(dataset.X.columns)
        assert np.isfinite(dataset.X.to_numpy()).all()
        assert np.isfinite(dataset.y.to_numpy()).all()
        assert dataset.timestamp_index[0] == EXPECTED_FIRST_TIMESTAMP
        assert dataset.timestamp_index[-1] == EXPECTED_LAST_TIMESTAMP
        assert dataset.timestamp_index.is_monotonic_increasing
        assert dataset.timestamp_index.is_unique


def test_all_configurations_use_identical_timestamp_population(
    phase_03_result,
):
    datasets, _, _ = phase_03_result
    reference_index = datasets["lag_only_p24"].timestamp_index

    for dataset in datasets.values():
        assert dataset.timestamp_index.equals(reference_index)


def test_phase_03_does_not_mutate_feature_table(
    phase_03_result,
):
    _, audit, _ = phase_03_result

    assert audit["input_mutation"] == {
        "feature_table_mutated": False,
        "status": "PASS",
    }


def test_supervised_construction_is_deterministic(
    phase_03_result,
    feature_context,
):
    datasets, audit, _ = phase_03_result
    config, feature_df = feature_context
    validation = validate_deterministic_construction(
        feature_df,
        config,
        datasets,
    )

    assert validation == {
        "deterministic_construction": True,
        "status": "PASS",
    }
    assert audit["determinism"] == validation


def test_phase_03_audit_round_trip(phase_03_result):
    _, audit, audit_path = phase_03_result

    with audit_path.open("r", encoding="utf-8") as file:
        saved_audit = json.load(file)

    assert saved_audit == audit
    assert audit["phase"] == "phase_03_x_y_preparation"
    assert audit["full_supervised_datasets_persisted"] is False
    assert audit["status"] == "PASS"
