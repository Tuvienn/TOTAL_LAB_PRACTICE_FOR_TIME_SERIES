from pathlib import Path
import json

import numpy as np
import pandas as pd
import pytest

from practice_3_v2.data.data_preparation import (
    PROJECT_ROOT,
    aggregate_duplicate_timestamps,
    build_complete_hourly_timeline,
    calculate_sha256,
    load_and_validate_saved_dataset,
    load_json_contract,
    load_raw_data,
    normalize_raw_data,
    prepare_aep_data,
    run_phase_01,
    save_prepared_artifacts,
)


DATA_CONTRACT = load_json_contract(PROJECT_ROOT / "config/data_contract.json")
PREPARATION_CONTRACT = load_json_contract(
    PROJECT_ROOT / "config/data_preparation.json"
)
RAW_PATH = PROJECT_ROOT / DATA_CONTRACT["raw_path"]


@pytest.fixture(scope="module")
def prepared_bundle() -> tuple[pd.DataFrame, dict]:
    return prepare_aep_data(RAW_PATH, DATA_CONTRACT, PREPARATION_CONTRACT)


def test_raw_file_identity_and_schema() -> None:
    assert RAW_PATH.is_file()
    assert calculate_sha256(RAW_PATH) == DATA_CONTRACT["raw_sha256"]
    raw_data = load_raw_data(RAW_PATH, DATA_CONTRACT)
    assert raw_data.columns.tolist() == ["Datetime", "AEP_MW"]
    assert raw_data.shape == (121_273, 2)


def test_invalid_schema_stops_loading(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid.csv"
    pd.DataFrame({"timestamp": ["2004-10-01 01:00:00"]}).to_csv(
        invalid_path,
        index=False,
    )
    with pytest.raises(ValueError, match="Unexpected raw schema"):
        load_raw_data(invalid_path, DATA_CONTRACT)


@pytest.mark.parametrize(
    ("timestamp", "target", "message"),
    [
        ("10/01/2004 01:00", 14_000, "Datetime parsing failed"),
        ("2004-10-01 01:00:00", "invalid", "Target conversion failed"),
        ("2004-10-01 01:00:00", np.nan, "missing values"),
        ("2004-10-01 01:00:00", np.inf, "non-finite values"),
        ("2004-10-01 01:00:00", 0, "non-positive values"),
    ],
)
def test_invalid_raw_values_stop_normalization(
    timestamp: str,
    target: object,
    message: str,
) -> None:
    invalid = pd.DataFrame({"Datetime": [timestamp], "AEP_MW": [target]})
    with pytest.raises((RuntimeError, ValueError), match=message):
        normalize_raw_data(invalid, DATA_CONTRACT, PREPARATION_CONTRACT)


def test_normalization_is_stable_and_chronological() -> None:
    raw_data = pd.DataFrame(
        {
            "Datetime": [
                "2004-10-01 02:00:00",
                "2004-10-01 01:00:00",
                "2004-10-01 01:00:00",
            ],
            "AEP_MW": [3.0, 1.0, 2.0],
        }
    )
    normalized = normalize_raw_data(
        raw_data,
        DATA_CONTRACT,
        PREPARATION_CONTRACT,
    )
    assert normalized["Datetime"].is_monotonic_increasing
    assert normalized.loc[:1, "AEP_MW"].tolist() == [1.0, 2.0]
    assert str(normalized["Datetime"].dtype) == "datetime64[ns]"


def test_prepared_schema_and_timeline(prepared_bundle) -> None:
    prepared_data, _ = prepared_bundle
    assert prepared_data.columns.tolist() == [
        "Datetime",
        "AEP_MW",
        "source_count",
        "quality_flag",
    ]
    assert len(prepared_data) == 121_296
    assert prepared_data["Datetime"].nunique() == 121_296
    assert prepared_data["Datetime"].is_monotonic_increasing
    assert prepared_data["Datetime"].diff().dropna().eq(
        pd.Timedelta(hours=1)
    ).all()


def test_missing_timestamps_are_preserved_without_fabricated_targets(
    prepared_bundle,
) -> None:
    prepared_data, audit = prepared_bundle
    missing_rows = prepared_data.loc[
        prepared_data["quality_flag"] == "missing_timestamp"
    ]
    assert len(missing_rows) == 27
    assert missing_rows["AEP_MW"].isna().all()
    assert missing_rows["source_count"].eq(0).all()
    assert len(audit["missing_hourly_timestamps"]) == 27


def test_duplicate_values_are_aggregated_by_mean(prepared_bundle) -> None:
    raw_data = load_raw_data(RAW_PATH, DATA_CONTRACT)
    raw_data["Datetime"] = pd.to_datetime(
        raw_data["Datetime"],
        format=PREPARATION_CONTRACT["datetime_format"],
        errors="raise",
    )
    duplicate_data = raw_data.loc[
        raw_data["Datetime"].duplicated(keep=False)
    ]
    expected_means = duplicate_data.groupby("Datetime")["AEP_MW"].mean()
    prepared_data, audit = prepared_bundle
    actual_means = (
        prepared_data.loc[
            prepared_data["quality_flag"] == "duplicate_aggregated"
        ]
        .set_index("Datetime")["AEP_MW"]
        .sort_index()
    )
    np.testing.assert_allclose(
        actual_means.to_numpy(),
        expected_means.sort_index().to_numpy(),
    )
    assert len(actual_means) == 4
    assert len(audit["duplicate_timestamps"]) == 4


def test_source_and_quality_metadata_are_conserved(prepared_bundle) -> None:
    prepared_data, audit = prepared_bundle
    assert int(prepared_data["source_count"].sum()) == 121_273
    assert audit["source_count_distribution"] == {
        "0": 27,
        "1": 121_265,
        "2": 4,
    }
    assert audit["quality_flag_distribution"] == {
        "observed": 121_265,
        "missing_timestamp": 27,
        "duplicate_aggregated": 4,
    }
    assert audit["source_conservation"] is True


def test_raw_checksum_is_unchanged(prepared_bundle) -> None:
    _, audit = prepared_bundle
    assert audit["raw_sha256_before"] == DATA_CONTRACT["raw_sha256"]
    assert audit["raw_sha256_after"] == DATA_CONTRACT["raw_sha256"]


def test_serialized_artifact_is_valid_and_deterministic(
    tmp_path: Path,
) -> None:
    first_csv = tmp_path / "first.csv"
    first_audit = tmp_path / "first.json"
    second_csv = tmp_path / "second.csv"
    second_audit = tmp_path / "second.json"
    result_one = run_phase_01(PROJECT_ROOT, first_csv, first_audit)
    result_two = run_phase_01(PROJECT_ROOT, second_csv, second_audit)
    assert result_one["processed_sha256"] == result_two["processed_sha256"]
    assert calculate_sha256(first_csv) == calculate_sha256(second_csv)
    load_and_validate_saved_dataset(
        first_csv,
        DATA_CONTRACT,
        PREPARATION_CONTRACT,
    )
    with first_audit.open(encoding="utf-8") as file:
        saved_audit = json.load(file)
    assert saved_audit["processed_sha256"] == calculate_sha256(first_csv)


def test_invalid_data_is_not_promoted_over_existing_artifacts(
    tmp_path: Path,
) -> None:
    processed_path = tmp_path / "prepared.csv"
    audit_path = tmp_path / "audit.json"
    processed_path.write_text("existing-csv", encoding="utf-8")
    audit_path.write_text("existing-json", encoding="utf-8")
    invalid_data = pd.DataFrame()
    with pytest.raises(ValueError, match="Unexpected prepared-data schema"):
        save_prepared_artifacts(
            invalid_data,
            {"status": "PASS"},
            processed_path,
            audit_path,
            DATA_CONTRACT,
            PREPARATION_CONTRACT,
            PROJECT_ROOT,
        )
    assert processed_path.read_text(encoding="utf-8") == "existing-csv"
    assert audit_path.read_text(encoding="utf-8") == "existing-json"


def test_pipeline_source_does_not_import_legacy_package() -> None:
    source_path = (
        PROJECT_ROOT
        / "src/practice_3_v2/data/data_preparation.py"
    )
    source = source_path.read_text(encoding="utf-8")
    assert "from practice_3 " not in source
    assert "import practice_3" not in source
