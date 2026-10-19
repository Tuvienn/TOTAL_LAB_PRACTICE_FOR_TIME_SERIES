from pathlib import Path
import json

import numpy as np
import pandas as pd
import pytest

from practice_3.data.data_preparation import (
    DATETIME_FORMAT,
    EXPECTED_RAW_SHA256,
    calculate_sha256,
    normalize_raw_data,
    prepare_aep_data,
    run_phase_01,
    validate_saved_dataset,
)


# ============================================================
# Data path used by the tests
# ============================================================

RAW_DATA_PATH = Path("datasets/raw/AEP_hourly.csv")


# ============================================================
# Simple fixture
# ============================================================

def get_prepared_data():
    """
    Run the Phase 1 pipeline and return:
    - prepared dataframe
    - audit result

    This helper avoids repeating the pipeline call in each test.
    """

    return prepare_aep_data(RAW_DATA_PATH)


# ============================================================
# 1. Validate the raw dataset
# ============================================================

def test_raw_file_exists():
    """Check that the raw dataset exists."""

    assert RAW_DATA_PATH.exists()


def test_raw_sha256():
    """Check that the raw dataset matches the approved baseline."""

    actual_sha256 = calculate_sha256(RAW_DATA_PATH)

    assert actual_sha256 == EXPECTED_RAW_SHA256


# ============================================================
# 2. Validate the prepared dataset schema
# ============================================================

def test_prepared_schema():
    """Check the columns of the prepared dataset."""

    df, _ = get_prepared_data()

    expected_columns = [
        "Datetime",
        "AEP_MW",
        "source_count",
        "quality_flag",
    ]

    assert list(df.columns) == expected_columns

    assert str(df["Datetime"].dtype) == "datetime64[ns]"

    assert pd.api.types.is_numeric_dtype(
        df["AEP_MW"]
    )

    assert pd.api.types.is_integer_dtype(
        df["source_count"]
    )


# ============================================================
# 3. Validate the timeline
# ============================================================

def test_hourly_timeline():
    """
    Validate the timeline:
    - Contains 121,296 timestamps.
    - Timestamps are unique.
    - Contains no duplicates.
    - Is monotonically increasing.
    - Is continuous at hourly intervals.
    """

    df, _ = get_prepared_data()

    assert len(df) == 121_296

    assert df["Datetime"].nunique() == 121_296

    assert df["Datetime"].duplicated().sum() == 0

    assert df["Datetime"].is_monotonic_increasing

    assert (
        df["Datetime"]
        .diff()
        .dropna()
        .eq(pd.Timedelta(hours=1))
        .all()
    )


# ============================================================
# 4. Validate missing timestamps
# ============================================================

def test_missing_timestamps():
    """
    Validate the 27 missing timestamps:
    - AEP_MW must be NaN.
    - source_count must equal 0.
    - quality_flag must be missing_timestamp.
    """

    df, _ = get_prepared_data()

    missing_rows = df.loc[
        df["quality_flag"] == "missing_timestamp"
    ]

    assert len(missing_rows) == 27

    assert missing_rows["AEP_MW"].isna().all()

    assert (
        missing_rows["source_count"] == 0
    ).all()


# ============================================================
# 5. Validate duplicate aggregation
# ============================================================

def test_duplicate_aggregation():
    """
    Validate that the 4 duplicate timestamps are aggregated
    and flagged correctly.
    """

    df, _ = get_prepared_data()

    duplicate_rows = df.loc[
        df["quality_flag"] == "duplicate_aggregated"
    ]

    assert len(duplicate_rows) == 4

    assert (
        duplicate_rows["source_count"] == 2
    ).all()


def test_duplicate_values_are_aggregated_by_mean():
    """Check that duplicate values are averaged according to the contract."""

    df_raw = pd.read_csv(RAW_DATA_PATH)
    df_raw["Datetime"] = pd.to_datetime(
        df_raw["Datetime"],
        format=DATETIME_FORMAT,
        errors="raise",
    )

    duplicate_raw = df_raw.loc[
        df_raw["Datetime"].duplicated(keep=False)
    ]
    expected_means = duplicate_raw.groupby("Datetime")["AEP_MW"].mean()

    df_prepared, _ = get_prepared_data()
    actual_means = (
        df_prepared.loc[
            df_prepared["quality_flag"] == "duplicate_aggregated"
        ]
        .set_index("Datetime")["AEP_MW"]
        .sort_index()
    )

    np.testing.assert_allclose(
        actual_means.to_numpy(),
        expected_means.sort_index().to_numpy(),
    )


# ============================================================
# 6. Validate source conservation
# ============================================================

def test_source_conservation():
    """
    The total source_count after processing must equal
    the original number of raw observations.
    """

    df, _ = get_prepared_data()

    assert df["source_count"].sum() == 121_273


# ============================================================
# 7. Validate the metadata distribution
# ============================================================

def test_metadata_distribution():
    """Check source_count and quality_flag."""

    df, _ = get_prepared_data()

    source_counts = (
        df["source_count"]
        .value_counts()
        .to_dict()
    )

    assert source_counts == {
        0: 27,
        1: 121_265,
        2: 4,
    }

    quality_flags = (
        df["quality_flag"]
        .value_counts()
        .to_dict()
    )

    assert quality_flags == {
        "observed": 121_265,
        "missing_timestamp": 27,
        "duplicate_aggregated": 4,
    }


# ============================================================
# 8. Validate the audit
# ============================================================

def test_phase_01_audit():
    """Check the key values in the Phase 1 audit."""

    _, audit = get_prepared_data()

    assert audit["raw_rows"] == 121_273
    assert audit["raw_missing_AEP_MW"] == 0
    assert audit["raw_non_positive_AEP_MW"] == 0
    assert audit["duplicate_rows_before"] == 8
    assert audit["duplicate_timestamps_before"] == 4
    assert audit["missing_hourly_timestamps_before"] == 27
    assert audit["prepared_rows"] == 121_296
    assert audit["unique_timestamps"] == 121_296
    assert audit["prepared_time_start"] == "2004-10-01 01:00:00"
    assert audit["prepared_time_end"] == "2018-08-03 00:00:00"

    assert audit["duplicate_timestamps_after"] == 0

    assert audit["missing_AEP_MW"] == 27

    assert audit["source_count_0"] == 27
    assert audit["source_count_1"] == 121_265
    assert audit["source_count_2"] == 4

    assert audit["sum_source_count"] == 121_273

    assert audit["timeline_continuous_hourly"] is True

    assert audit["timezone_policy"] == "timezone-naive"

    assert audit["raw_sha256_before"] == EXPECTED_RAW_SHA256
    assert audit["raw_sha256_after"] == EXPECTED_RAW_SHA256

    assert audit["status"] == "PASS"


# ============================================================
# 9. Validate stop conditions
# ============================================================

def test_invalid_datetime_stops_pipeline():
    """Datetime values outside the approved format must stop the pipeline."""

    invalid = pd.DataFrame(
        {
            "Datetime": ["10/01/2004 01:00"],
            "AEP_MW": [14_000],
        }
    )

    with pytest.raises(RuntimeError, match="Datetime parsing failed"):
        normalize_raw_data(invalid)


def test_invalid_target_stops_pipeline():
    """Non-numeric target values must stop the pipeline."""

    invalid = pd.DataFrame(
        {
            "Datetime": ["2004-10-01 01:00:00"],
            "AEP_MW": ["not-a-number"],
        }
    )

    with pytest.raises(ValueError):
        normalize_raw_data(invalid)


def test_non_positive_target_stops_pipeline():
    """Non-positive target values must stop the pipeline."""

    invalid = pd.DataFrame(
        {
            "Datetime": ["2004-10-01 01:00:00"],
            "AEP_MW": [0],
        }
    )

    with pytest.raises(ValueError, match="non-positive"):
        normalize_raw_data(invalid)


# ============================================================
# 10. Validate integration and artifacts
# ============================================================

def test_phase_01_runner_creates_valid_artifacts(tmp_path):
    """The runner must create readable and verifiable CSV and JSON artifacts."""

    processed_path = tmp_path / "aep_hourly_prepared.csv"
    audit_path = tmp_path / "phase_01_data_quality.json"

    audit = run_phase_01(
        raw_path=RAW_DATA_PATH,
        processed_path=processed_path,
        audit_path=audit_path,
    )

    assert processed_path.exists()
    assert audit_path.exists()

    validate_saved_dataset(processed_path)

    with audit_path.open(encoding="utf-8") as file:
        saved_audit = json.load(file)

    assert saved_audit == audit
    assert saved_audit["status"] == "PASS"
