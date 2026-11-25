"""Structural data preparation for Practice 3 v2."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import json
import os
import tempfile
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_CONTRACT_PATH = PROJECT_ROOT / "config/data_contract.json"
PREPARATION_CONTRACT_PATH = PROJECT_ROOT / "config/data_preparation.json"


def calculate_sha256(path: Path) -> str:
    """Return the SHA-256 checksum of a file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_contract(path: Path) -> dict[str, Any]:
    """Load and minimally validate a JSON contract."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Contract not found: {path}")
    with path.open(encoding="utf-8") as file:
        contract = json.load(file)
    if contract.get("status") != "APPROVED":
        raise ValueError(f"Contract is not approved: {path}")
    return contract


def validate_raw_file(path: Path, data_contract: dict[str, Any]) -> str:
    """Validate raw-file existence and checksum."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Raw dataset not found: {path}")
    actual_sha256 = calculate_sha256(path)
    expected_sha256 = data_contract["raw_sha256"]
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "Raw dataset SHA-256 does not match the approved contract. "
            f"Expected {expected_sha256}; got {actual_sha256}."
        )
    return actual_sha256


def load_raw_data(path: Path, data_contract: dict[str, Any]) -> pd.DataFrame:
    """Load the raw CSV and enforce its exact schema."""

    dataframe = pd.read_csv(path)
    expected_columns = data_contract["expected_columns"]
    if dataframe.columns.tolist() != expected_columns:
        raise ValueError(
            "Unexpected raw schema. "
            f"Expected {expected_columns}; got {dataframe.columns.tolist()}."
        )
    return dataframe


def normalize_raw_data(
    raw_data: pd.DataFrame,
    data_contract: dict[str, Any],
    preparation_contract: dict[str, Any],
) -> pd.DataFrame:
    """Strictly normalize timestamp and target values on a working copy."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    datetime_format = preparation_contract["datetime_format"]
    working_data = raw_data.copy(deep=True)

    try:
        parsed_timestamp = pd.to_datetime(
            working_data[timestamp_column],
            format=datetime_format,
            errors="raise",
        ).astype("datetime64[ns]")
    except (TypeError, ValueError, AssertionError) as error:
        raise RuntimeError("Datetime parsing failed.") from error

    if parsed_timestamp.isna().any():
        raise ValueError("Datetime contains missing values after parsing.")
    if parsed_timestamp.dt.tz is not None:
        raise ValueError("Datetime must remain timezone-naive.")
    working_data[timestamp_column] = parsed_timestamp

    try:
        numeric_target = pd.to_numeric(
            working_data[target_column],
            errors="raise",
        )
    except (TypeError, ValueError) as error:
        raise ValueError("Target conversion failed.") from error

    if numeric_target.isna().any():
        raise ValueError("Raw target contains missing values.")
    if not np.isfinite(numeric_target.to_numpy(dtype="float64")).all():
        raise ValueError("Raw target contains non-finite values.")
    if (numeric_target <= 0).any():
        raise ValueError("Raw target contains non-positive values.")
    working_data[target_column] = numeric_target

    working_data = working_data.sort_values(
        timestamp_column,
        ascending=True,
        kind="stable",
    ).reset_index(drop=True)
    if not working_data[timestamp_column].is_monotonic_increasing:
        raise ValueError("Datetime is not chronologically sorted.")
    return working_data


def aggregate_duplicate_timestamps(
    working_data: pd.DataFrame,
    data_contract: dict[str, Any],
    preparation_contract: dict[str, Any],
) -> pd.DataFrame:
    """Aggregate duplicate timestamps by mean and retain source counts."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    expected_duplicates = preparation_contract["expected"][
        "duplicate_timestamps"
    ]
    duplicate_mask = working_data[timestamp_column].duplicated(keep=False)
    duplicate_count = int(
        working_data.loc[duplicate_mask, timestamp_column].nunique()
    )
    if duplicate_count != expected_duplicates:
        raise ValueError(
            "Unexpected duplicate timestamp count. "
            f"Expected {expected_duplicates}; got {duplicate_count}."
        )

    aggregated_data = (
        working_data.groupby(timestamp_column, as_index=False, sort=True)
        .agg(
            **{
                target_column: (target_column, "mean"),
                "source_count": (target_column, "size"),
            }
        )
    )
    aggregated_data["source_count"] = aggregated_data[
        "source_count"
    ].astype("int64")
    aggregated_data["quality_flag"] = "observed"
    aggregated_data.loc[
        aggregated_data["source_count"] > 1,
        "quality_flag",
    ] = "duplicate_aggregated"

    if int(aggregated_data["source_count"].sum()) != len(working_data):
        raise ValueError("Source conservation failed after aggregation.")
    if aggregated_data[timestamp_column].duplicated().any():
        raise ValueError("Duplicate timestamps remain after aggregation.")
    return aggregated_data


def build_complete_hourly_timeline(
    aggregated_data: pd.DataFrame,
    data_contract: dict[str, Any],
    preparation_contract: dict[str, Any],
) -> pd.DataFrame:
    """Reindex observations to a complete hourly timeline without imputation."""

    timestamp_column = data_contract["timestamp_column"]
    expected_missing = preparation_contract["expected"][
        "missing_hourly_timestamps"
    ]
    complete_index = pd.date_range(
        start=aggregated_data[timestamp_column].min(),
        end=aggregated_data[timestamp_column].max(),
        freq=data_contract["expected_frequency"],
    )
    observed_index = pd.DatetimeIndex(aggregated_data[timestamp_column])
    missing_timestamps = complete_index.difference(observed_index)
    if len(missing_timestamps) != expected_missing:
        raise ValueError(
            "Unexpected missing timestamp count. "
            f"Expected {expected_missing}; got {len(missing_timestamps)}."
        )

    prepared_data = (
        aggregated_data.set_index(timestamp_column)
        .reindex(complete_index)
        .rename_axis(timestamp_column)
        .reset_index()
    )
    inserted_mask = prepared_data["source_count"].isna()
    prepared_data.loc[inserted_mask, "source_count"] = 0
    prepared_data.loc[inserted_mask, "quality_flag"] = "missing_timestamp"
    prepared_data["source_count"] = prepared_data["source_count"].astype(
        "int64"
    )
    return prepared_data


def validate_prepared_data(
    prepared_data: pd.DataFrame,
    data_contract: dict[str, Any],
    preparation_contract: dict[str, Any],
) -> None:
    """Validate the complete prepared-data contract."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    expected = preparation_contract["expected"]
    expected_columns = [
        timestamp_column,
        target_column,
        "source_count",
        "quality_flag",
    ]
    if prepared_data.columns.tolist() != expected_columns:
        raise ValueError("Unexpected prepared-data schema.")
    if len(prepared_data) != expected["prepared_rows"]:
        raise ValueError("Unexpected prepared row count.")
    if prepared_data[timestamp_column].nunique() != expected["prepared_rows"]:
        raise ValueError("Prepared timestamps are not unique.")
    if not prepared_data[timestamp_column].is_monotonic_increasing:
        raise ValueError("Prepared timeline is not increasing.")
    hourly_step = pd.Timedelta(hours=1)
    if not prepared_data[timestamp_column].diff().dropna().eq(hourly_step).all():
        raise ValueError("Prepared timeline is not continuous hourly data.")
    if str(prepared_data[timestamp_column].dtype) != "datetime64[ns]":
        raise TypeError("Prepared Datetime dtype must be datetime64[ns].")
    if prepared_data[timestamp_column].dt.tz is not None:
        raise ValueError("Prepared Datetime must remain timezone-naive.")

    missing_target_count = int(prepared_data[target_column].isna().sum())
    if missing_target_count != expected["missing_hourly_timestamps"]:
        raise ValueError("Unexpected prepared missing-target count.")
    finite_targets = prepared_data[target_column].dropna().to_numpy(
        dtype="float64"
    )
    if not np.isfinite(finite_targets).all() or (finite_targets <= 0).any():
        raise ValueError("Prepared observed targets must be finite and positive.")

    actual_source_counts = {
        str(key): int(value)
        for key, value in prepared_data["source_count"].value_counts().items()
    }
    if actual_source_counts != expected["source_count_distribution"]:
        raise ValueError("Unexpected source_count distribution.")
    actual_quality_flags = {
        str(key): int(value)
        for key, value in prepared_data["quality_flag"].value_counts().items()
    }
    if actual_quality_flags != expected["quality_flag_distribution"]:
        raise ValueError("Unexpected quality_flag distribution.")
    if int(prepared_data["source_count"].sum()) != expected["raw_rows"]:
        raise ValueError("Source conservation failed.")

    missing_rows = prepared_data.loc[
        prepared_data["quality_flag"] == "missing_timestamp"
    ]
    if not missing_rows[target_column].isna().all():
        raise ValueError("Missing timestamps contain fabricated targets.")
    if not missing_rows["source_count"].eq(0).all():
        raise ValueError("Missing timestamps must have source_count zero.")


def _format_timestamps(values: pd.Series | pd.DatetimeIndex, fmt: str) -> list[str]:
    index = pd.DatetimeIndex(values).sort_values()
    return [timestamp.strftime(fmt) for timestamp in index]


def prepare_aep_data(
    raw_path: Path,
    data_contract: dict[str, Any],
    preparation_contract: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Prepare raw AEP data and return the dataframe and scientific audit."""

    raw_path = Path(raw_path)
    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    datetime_format = preparation_contract["datetime_format"]
    expected = preparation_contract["expected"]
    raw_sha256_before = validate_raw_file(raw_path, data_contract)
    raw_data = load_raw_data(raw_path, data_contract)

    if raw_data.shape != (expected["raw_rows"], expected["raw_columns"]):
        raise ValueError(
            f"Unexpected raw shape: {raw_data.shape}; expected "
            f"({expected['raw_rows']}, {expected['raw_columns']})."
        )
    fully_duplicated_rows = int(raw_data.duplicated().sum())
    if fully_duplicated_rows != expected["fully_duplicated_rows"]:
        raise ValueError("Unexpected fully duplicated row count.")

    try:
        raw_timestamps = pd.to_datetime(
            raw_data[timestamp_column],
            format=datetime_format,
            errors="raise",
        ).astype("datetime64[ns]")
    except (TypeError, ValueError, AssertionError) as error:
        raise RuntimeError("Datetime parsing failed during raw audit.") from error
    duplicate_mask = raw_timestamps.duplicated(keep=False)
    duplicate_rows = int(duplicate_mask.sum())
    duplicate_timestamps = pd.DatetimeIndex(
        raw_timestamps.loc[duplicate_mask].unique()
    ).sort_values()
    if duplicate_rows != expected["duplicate_rows"]:
        raise ValueError("Unexpected duplicate row count.")

    working_data = normalize_raw_data(
        raw_data,
        data_contract,
        preparation_contract,
    )
    aggregated_data = aggregate_duplicate_timestamps(
        working_data,
        data_contract,
        preparation_contract,
    )
    complete_index = pd.date_range(
        aggregated_data[timestamp_column].min(),
        aggregated_data[timestamp_column].max(),
        freq=data_contract["expected_frequency"],
    )
    missing_timestamps = complete_index.difference(
        pd.DatetimeIndex(aggregated_data[timestamp_column])
    )
    prepared_data = build_complete_hourly_timeline(
        aggregated_data,
        data_contract,
        preparation_contract,
    )
    validate_prepared_data(
        prepared_data,
        data_contract,
        preparation_contract,
    )

    raw_sha256_after = calculate_sha256(raw_path)
    if raw_sha256_after != raw_sha256_before:
        raise ValueError("Raw dataset changed during preparation.")

    audit: dict[str, Any] = {
        "phase": preparation_contract["phase"],
        "contract_version": preparation_contract["contract_version"],
        "raw_path": data_contract["raw_path"],
        "raw_sha256_before": raw_sha256_before,
        "raw_sha256_after": raw_sha256_after,
        "raw_rows": int(len(raw_data)),
        "raw_columns": raw_data.columns.tolist(),
        "raw_time_start": raw_timestamps.min().strftime(datetime_format),
        "raw_time_end": raw_timestamps.max().strftime(datetime_format),
        "raw_chronologically_sorted_before": bool(
            raw_timestamps.is_monotonic_increasing
        ),
        "raw_missing_cells": int(raw_data.isna().sum().sum()),
        "raw_non_finite_target": 0,
        "raw_non_positive_target": 0,
        "fully_duplicated_rows": fully_duplicated_rows,
        "duplicate_rows_before": duplicate_rows,
        "duplicate_timestamps_before": int(len(duplicate_timestamps)),
        "duplicate_timestamps": _format_timestamps(
            duplicate_timestamps,
            datetime_format,
        ),
        "missing_hourly_timestamps_before": int(len(missing_timestamps)),
        "missing_hourly_timestamps": _format_timestamps(
            missing_timestamps,
            datetime_format,
        ),
        "prepared_rows": int(len(prepared_data)),
        "prepared_columns": prepared_data.columns.tolist(),
        "prepared_time_start": prepared_data[timestamp_column]
        .min()
        .strftime(datetime_format),
        "prepared_time_end": prepared_data[timestamp_column]
        .max()
        .strftime(datetime_format),
        "unique_timestamps": int(prepared_data[timestamp_column].nunique()),
        "duplicate_timestamps_after": int(
            prepared_data[timestamp_column].duplicated().sum()
        ),
        "missing_target_after": int(prepared_data[target_column].isna().sum()),
        "source_count_distribution": {
            str(key): int(value)
            for key, value in prepared_data["source_count"].value_counts().items()
        },
        "quality_flag_distribution": {
            str(key): int(value)
            for key, value in prepared_data["quality_flag"].value_counts().items()
        },
        "sum_source_count": int(prepared_data["source_count"].sum()),
        "source_conservation": bool(
            prepared_data["source_count"].sum() == len(raw_data)
        ),
        "timeline_continuous_hourly": bool(
            prepared_data[timestamp_column]
            .diff()
            .dropna()
            .eq(pd.Timedelta(hours=1))
            .all()
        ),
        "policies": deepcopy(preparation_contract["policies"]),
        "processed_path": preparation_contract["outputs"]["prepared_dataset"],
        "processed_sha256": None,
        "status": "PASS",
    }
    return prepared_data, audit


def load_and_validate_saved_dataset(
    path: Path,
    data_contract: dict[str, Any],
    preparation_contract: dict[str, Any],
) -> pd.DataFrame:
    """Read a serialized prepared CSV and revalidate its contract."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    saved_data = pd.read_csv(path)
    saved_data[timestamp_column] = pd.to_datetime(
        saved_data[timestamp_column],
        format=preparation_contract["datetime_format"],
        errors="raise",
    ).astype("datetime64[ns]")
    saved_data[target_column] = pd.to_numeric(
        saved_data[target_column],
        errors="raise",
    )
    saved_data["source_count"] = pd.to_numeric(
        saved_data["source_count"],
        errors="raise",
    ).astype("int64")
    validate_prepared_data(saved_data, data_contract, preparation_contract)
    return saved_data


def save_prepared_artifacts(
    prepared_data: pd.DataFrame,
    audit: dict[str, Any],
    processed_path: Path,
    audit_path: Path,
    data_contract: dict[str, Any],
    preparation_contract: dict[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    """Validate temporary artifacts before atomically promoting each file."""

    validate_prepared_data(prepared_data, data_contract, preparation_contract)
    processed_path = Path(processed_path)
    audit_path = Path(audit_path)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_paths: list[Path] = []

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".csv.tmp",
            prefix="phase_01_",
            dir=processed_path.parent,
            delete=False,
            encoding="utf-8",
            newline="",
        ) as temporary_csv:
            temporary_csv_path = Path(temporary_csv.name)
            temporary_paths.append(temporary_csv_path)
            prepared_data.to_csv(
                temporary_csv,
                index=False,
                date_format=preparation_contract["datetime_format"],
                float_format="%.15g",
                lineterminator="\n",
            )

        load_and_validate_saved_dataset(
            temporary_csv_path,
            data_contract,
            preparation_contract,
        )
        processed_sha256 = calculate_sha256(temporary_csv_path)
        final_audit = deepcopy(audit)
        resolved_processed_path = processed_path.resolve()
        resolved_project_root = Path(project_root).resolve()
        try:
            processed_identity = resolved_processed_path.relative_to(
                resolved_project_root
            )
        except ValueError:
            processed_identity = resolved_processed_path
        final_audit["processed_path"] = str(processed_identity)
        final_audit["processed_sha256"] = processed_sha256

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json.tmp",
            prefix="phase_01_",
            dir=audit_path.parent,
            delete=False,
            encoding="utf-8",
        ) as temporary_json:
            temporary_json_path = Path(temporary_json.name)
            temporary_paths.append(temporary_json_path)
            json.dump(final_audit, temporary_json, indent=2, ensure_ascii=False)
            temporary_json.write("\n")

        with temporary_json_path.open(encoding="utf-8") as file:
            validated_audit = json.load(file)
        if validated_audit != final_audit or final_audit["status"] != "PASS":
            raise ValueError("Serialized audit validation failed.")

        os.replace(temporary_csv_path, processed_path)
        temporary_paths.remove(temporary_csv_path)
        os.replace(temporary_json_path, audit_path)
        temporary_paths.remove(temporary_json_path)
        return final_audit
    finally:
        for temporary_path in temporary_paths:
            temporary_path.unlink(missing_ok=True)


def run_phase_01(
    project_root: Path = PROJECT_ROOT,
    processed_path: Path | None = None,
    audit_path: Path | None = None,
) -> dict[str, Any]:
    """Run Phase 1 from approved contracts to validated official artifacts."""

    project_root = Path(project_root).resolve()
    data_contract = load_json_contract(project_root / "config/data_contract.json")
    preparation_contract = load_json_contract(
        project_root / "config/data_preparation.json"
    )
    raw_path = project_root / data_contract["raw_path"]
    prepared_data, audit = prepare_aep_data(
        raw_path,
        data_contract,
        preparation_contract,
    )
    resolved_processed_path = processed_path or (
        project_root / preparation_contract["outputs"]["prepared_dataset"]
    )
    resolved_audit_path = audit_path or (
        project_root / preparation_contract["outputs"]["audit"]
    )
    return save_prepared_artifacts(
        prepared_data,
        audit,
        Path(resolved_processed_path),
        Path(resolved_audit_path),
        data_contract,
        preparation_contract,
        project_root,
    )


def main() -> int:
    """Execute Phase 1 and print its validated audit."""

    audit = run_phase_01()
    print(json.dumps(audit, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
