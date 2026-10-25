"""One-step supervised-data construction for Practice 3 v2."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import json
import os
import tempfile
from typing import Any

import numpy as np
import pandas as pd

from practice_3_v2.analysis.eda import extract_development_data
from practice_3_v2.analysis.feature_engineering import (
    build_time_safe_features,
    load_phase_04_inputs,
)
from practice_3_v2.data.data_preparation import (
    calculate_sha256,
    load_json_contract,
)
from practice_3_v2.data.temporal_split import validate_prepared_input


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class SupervisedPartition:
    """Aligned, eligible samples for one temporal partition."""

    X: pd.DataFrame
    y: pd.Series
    metadata: pd.DataFrame


@dataclass(frozen=True)
class SupervisedFold:
    """One approved expanding-window fold."""

    fold: int
    validation_start: pd.Timestamp
    validation_end_exclusive: pd.Timestamp
    train: SupervisedPartition
    validation: SupervisedPartition


def validate_supervised_contract(
    supervised_contract: dict[str, Any],
    data_contract: dict[str, Any],
    split_contract: dict[str, Any],
    feature_contract: dict[str, Any],
) -> None:
    """Reject changes that violate the approved X/y protocol."""

    alignment = supervised_contract["alignment"]
    eligibility = supervised_contract["eligibility"]
    cross_validation = supervised_contract["cross_validation"]
    scope = supervised_contract["scope"]
    if supervised_contract["status"] != "APPROVED":
        raise ValueError("Supervised-data contract must be approved.")
    if supervised_contract["feature_order"] != feature_contract["feature_order"]:
        raise ValueError("Supervised X order conflicts with the feature contract.")
    if alignment != {
        "sample_key": "target_timestamp",
        "forecast_origin_offset_hours": 1,
        "target_column": data_contract["target_column"],
        "primary_horizon_hours": 1,
    }:
        raise ValueError("Supervised alignment does not match one-step semantics.")
    if eligibility != {
        "target_must_be_observed_and_finite": True,
        "all_features_must_be_observed_and_finite": True,
        "imputation": "none",
        "shuffle": False,
        "exclusion_priority": [
            "invalid_feature_vector",
            "missing_target_with_valid_features",
        ],
    }:
        raise ValueError("Eligibility policy conflicts with the approved design.")
    expected_cv = split_contract["cross_validation"]
    if (
        cross_validation["method"] != expected_cv["method"]
        or cross_validation["folds"] != expected_cv["splits"]
        or cross_validation["gap_hours"] != expected_cv["gap_hours"]
        or cross_validation["split_key"] != "target_timestamp"
        or cross_validation["validation_history_policy"]
        != "hourly_actual_update_through_target_minus_1_hour"
        or cross_validation["same_eligible_population_for_all_candidates"]
        is not True
    ):
        raise ValueError("Cross-validation application conflicts with Phase 2.")
    if scope != {
        "official_audit_partition": "development_only",
        "holdout_features_materialized": False,
        "holdout_target_statistics_reported": False,
        "recursive_24h_matrix_materialized": False,
        "persist_xy_table": False,
    }:
        raise ValueError("Phase 5 scope exceeds the approved boundary.")


def load_phase_05_inputs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    """Load Phase 5 contracts and verify upstream audit identities."""

    project_root = Path(project_root).resolve()
    (
        data_contract,
        preparation_contract,
        split_contract,
        feature_contract,
        phase_01_audit,
        phase_02_audit,
        phase_03_audit,
    ) = load_phase_04_inputs(project_root)
    supervised_contract = load_json_contract(
        project_root / "config/supervised_dataset.json"
    )
    validate_supervised_contract(
        supervised_contract,
        data_contract,
        split_contract,
        feature_contract,
    )
    if supervised_contract["prepared_sha256"] != feature_contract[
        "prepared_sha256"
    ]:
        raise ValueError("Prepared identity conflicts with Phase 4.")

    split_audit_path = project_root / supervised_contract["split_audit"]
    if calculate_sha256(split_audit_path) != supervised_contract[
        "split_audit_sha256"
    ]:
        raise ValueError("Phase 2 audit SHA-256 does not match Phase 5.")
    feature_audit_path = project_root / supervised_contract["feature_audit"]
    if not feature_audit_path.is_file():
        raise FileNotFoundError(f"Phase 4 audit not found: {feature_audit_path}")
    if calculate_sha256(feature_audit_path) != supervised_contract[
        "feature_audit_sha256"
    ]:
        raise ValueError("Phase 4 audit SHA-256 does not match Phase 5.")
    with feature_audit_path.open(encoding="utf-8") as file:
        phase_04_audit = json.load(file)
    if phase_04_audit.get("status") != "PASS":
        raise ValueError("Phase 4 audit status must be PASS.")
    if phase_04_audit.get("feature_order") != supervised_contract[
        "feature_order"
    ]:
        raise ValueError("Phase 4 feature order conflicts with Phase 5.")
    return (
        data_contract,
        preparation_contract,
        split_contract,
        feature_contract,
        supervised_contract,
        phase_01_audit,
        phase_02_audit,
        phase_03_audit,
        phase_04_audit,
    )


def build_supervised_candidates(
    development_data: pd.DataFrame,
    data_contract: dict[str, Any],
    feature_contract: dict[str, Any],
    supervised_contract: dict[str, Any],
) -> pd.DataFrame:
    """Build an auditable candidate timeline without dropping any row."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    features = build_time_safe_features(
        development_data,
        data_contract,
        feature_contract,
    )
    if features.columns.tolist() != supervised_contract["feature_order"]:
        raise ValueError("Feature builder returned an unexpected X schema.")

    numeric_features = features.to_numpy(dtype="float64")
    feature_valid = pd.Series(
        np.isfinite(numeric_features).all(axis=1),
        index=development_data.index,
    )
    target = development_data[target_column].astype("float64")
    target_valid = target.notna() & np.isfinite(target)
    eligible = feature_valid & target_valid
    exclusion_reason = pd.Series(
        "eligible",
        index=development_data.index,
        dtype="object",
    )
    exclusion_reason.loc[~feature_valid] = "invalid_feature_vector"
    exclusion_reason.loc[feature_valid & ~target_valid] = (
        "missing_target_with_valid_features"
    )

    candidates = pd.DataFrame(index=development_data.index)
    candidates["target_timestamp"] = development_data[timestamp_column]
    candidates["forecast_origin"] = candidates["target_timestamp"] - pd.Timedelta(
        hours=supervised_contract["alignment"]["forecast_origin_offset_hours"]
    )
    for column in supervised_contract["feature_order"]:
        candidates[column] = features[column]
    candidates[target_column] = target
    candidates["is_eligible"] = eligible
    candidates["exclusion_reason"] = exclusion_reason
    return candidates.reset_index(drop=True)


def extract_eligible_xy(
    candidates: pd.DataFrame,
    row_mask: pd.Series,
    data_contract: dict[str, Any],
    supervised_contract: dict[str, Any],
) -> SupervisedPartition:
    """Return aligned X, y, and metadata for eligible rows in one partition."""

    target_column = data_contract["target_column"]
    selected = candidates.loc[row_mask & candidates["is_eligible"]].copy()
    selected = selected.sort_values("target_timestamp", kind="stable")
    sample_index = pd.DatetimeIndex(
        selected["target_timestamp"],
        name="target_timestamp",
    )
    X = selected[supervised_contract["feature_order"]].copy()
    X.index = sample_index
    y = selected[target_column].astype("float64").copy()
    y.index = sample_index
    metadata = selected[["target_timestamp", "forecast_origin"]].copy()
    metadata.index = sample_index
    return SupervisedPartition(X=X, y=y, metadata=metadata)


def apply_expanding_window_folds(
    candidates: pd.DataFrame,
    data_contract: dict[str, Any],
    split_contract: dict[str, Any],
    supervised_contract: dict[str, Any],
) -> list[SupervisedFold]:
    """Apply approved target-time boundaries to eligible candidates."""

    timestamps = candidates["target_timestamp"]
    development_start = pd.Timestamp(
        split_contract["development"]["start_inclusive"]
    )
    folds: list[SupervisedFold] = []
    for fold_contract in split_contract["cross_validation"]["folds"]:
        validation_start = pd.Timestamp(
            fold_contract["validation_start_inclusive"]
        )
        validation_end = pd.Timestamp(
            fold_contract["validation_end_exclusive"]
        )
        train_mask = timestamps.ge(development_start) & timestamps.lt(
            validation_start
        )
        validation_mask = timestamps.ge(validation_start) & timestamps.lt(
            validation_end
        )
        folds.append(
            SupervisedFold(
                fold=int(fold_contract["fold"]),
                validation_start=validation_start,
                validation_end_exclusive=validation_end,
                train=extract_eligible_xy(
                    candidates,
                    train_mask,
                    data_contract,
                    supervised_contract,
                ),
                validation=extract_eligible_xy(
                    candidates,
                    validation_mask,
                    data_contract,
                    supervised_contract,
                ),
            )
        )
    return folds


def validate_supervised_population(
    candidates: pd.DataFrame,
    folds: list[SupervisedFold],
    development_data: pd.DataFrame,
    data_contract: dict[str, Any],
    split_contract: dict[str, Any],
    supervised_contract: dict[str, Any],
) -> None:
    """Validate sample alignment, eligibility, chronology, and fold application."""

    target_column = data_contract["target_column"]
    feature_order = supervised_contract["feature_order"]
    expected_columns = (
        ["target_timestamp", "forecast_origin"]
        + feature_order
        + [target_column, "is_eligible", "exclusion_reason"]
    )
    if candidates.columns.tolist() != expected_columns:
        raise ValueError("Candidate frame does not use the approved schema.")
    if len(candidates) != len(development_data):
        raise ValueError("Candidate timeline changed the development row count.")
    if not candidates["target_timestamp"].equals(
        development_data[data_contract["timestamp_column"]]
    ):
        raise ValueError("Candidate target timestamps are not source-aligned.")
    expected_origins = candidates["target_timestamp"] - pd.Timedelta(hours=1)
    if not candidates["forecast_origin"].equals(expected_origins):
        raise ValueError("Forecast origins are not one hour before targets.")
    if not candidates["target_timestamp"].is_unique:
        raise ValueError("Candidate target timestamps must be unique.")
    if not candidates["target_timestamp"].is_monotonic_increasing:
        raise ValueError("Candidate target timestamps must remain chronological.")
    if set(candidates["exclusion_reason"].unique()) != {
        "eligible",
        "invalid_feature_vector",
        "missing_target_with_valid_features",
    }:
        raise ValueError("Candidate exclusion reasons are incomplete.")
    if not candidates.loc[
        candidates["exclusion_reason"].eq("eligible"), "is_eligible"
    ].all():
        raise ValueError("Eligible reason conflicts with eligibility mask.")
    if candidates.loc[
        ~candidates["exclusion_reason"].eq("eligible"), "is_eligible"
    ].any():
        raise ValueError("Excluded rows cannot be eligible.")

    full_mask = pd.Series(True, index=candidates.index)
    full = extract_eligible_xy(
        candidates,
        full_mask,
        data_contract,
        supervised_contract,
    )
    if full.X.columns.tolist() != feature_order:
        raise ValueError("Eligible X does not use the approved feature order.")
    if full.X.isna().any().any() or not np.isfinite(
        full.X.to_numpy(dtype="float64")
    ).all():
        raise ValueError("Eligible X contains missing or non-finite values.")
    if full.y.isna().any() or not np.isfinite(full.y.to_numpy()).all():
        raise ValueError("Eligible y contains missing or non-finite values.")
    if not full.X.index.equals(full.y.index):
        raise ValueError("Eligible X and y indices are not aligned.")

    if len(folds) != split_contract["cross_validation"]["splits"]:
        raise ValueError("Unexpected supervised fold count.")
    previous_train_rows = -1
    timestamps = candidates["target_timestamp"]
    for fold, fold_contract in zip(
        folds,
        split_contract["cross_validation"]["folds"],
        strict=True,
    ):
        train_raw = timestamps.lt(fold.validation_start)
        validation_raw = timestamps.ge(fold.validation_start) & timestamps.lt(
            fold.validation_end_exclusive
        )
        if int(train_raw.sum()) != fold_contract["expected_train_rows"]:
            raise ValueError(f"Fold {fold.fold} raw train count changed.")
        if int(validation_raw.sum()) != fold_contract[
            "expected_validation_rows"
        ]:
            raise ValueError(f"Fold {fold.fold} raw validation count changed.")
        if len(fold.train.X) <= previous_train_rows:
            raise ValueError("Eligible fold-train population must expand.")
        previous_train_rows = len(fold.train.X)
        if not fold.train.X.index.equals(fold.train.y.index):
            raise ValueError(f"Fold {fold.fold} train X/y are misaligned.")
        if not fold.validation.X.index.equals(fold.validation.y.index):
            raise ValueError(f"Fold {fold.fold} validation X/y are misaligned.")
        if fold.train.X.index.max() >= fold.validation.X.index.min():
            raise ValueError(f"Fold {fold.fold} violates chronology.")
        if fold.train.X.index.intersection(fold.validation.X.index).size:
            raise ValueError(f"Fold {fold.fold} train and validation overlap.")


def _partition_audit(
    candidates: pd.DataFrame,
    raw_mask: pd.Series,
) -> dict[str, Any]:
    """Summarize raw and eligible rows without target statistics."""

    raw = candidates.loc[raw_mask]
    eligible = raw.loc[raw["is_eligible"]]
    return {
        "raw_rows": int(len(raw)),
        "eligible_rows": int(len(eligible)),
        "excluded_rows": int((~raw["is_eligible"]).sum()),
        "eligible_start": eligible["target_timestamp"].min().strftime(
            DATETIME_FORMAT
        ),
        "eligible_end": eligible["target_timestamp"].max().strftime(
            DATETIME_FORMAT
        ),
    }


def build_phase_05_audit(
    candidates: pd.DataFrame,
    folds: list[SupervisedFold],
    prepared_sha256: str,
    split_audit_sha256: str,
    feature_audit_sha256: str,
    split_contract: dict[str, Any],
    supervised_contract: dict[str, Any],
) -> dict[str, Any]:
    """Build the deterministic development-only supervised-data audit."""

    timestamps = candidates["target_timestamp"]
    reason_counts = candidates["exclusion_reason"].value_counts()
    fold_records: list[dict[str, Any]] = []
    for fold, fold_contract in zip(
        folds,
        split_contract["cross_validation"]["folds"],
        strict=True,
    ):
        train_mask = timestamps.lt(fold.validation_start)
        validation_mask = timestamps.ge(fold.validation_start) & timestamps.lt(
            fold.validation_end_exclusive
        )
        fold_records.append(
            {
                "fold": fold.fold,
                "validation_start_inclusive": fold.validation_start.strftime(
                    DATETIME_FORMAT
                ),
                "validation_end_exclusive": (
                    fold.validation_end_exclusive.strftime(DATETIME_FORMAT)
                ),
                "train": _partition_audit(candidates, train_mask),
                "validation": _partition_audit(candidates, validation_mask),
                "gap_hours": int(
                    split_contract["cross_validation"]["gap_hours"]
                ),
                "shuffle": bool(split_contract["cross_validation"]["shuffle"]),
                "raw_counts_match_phase_02": (
                    int(train_mask.sum())
                    == fold_contract["expected_train_rows"]
                    and int(validation_mask.sum())
                    == fold_contract["expected_validation_rows"]
                ),
            }
        )
    eligible = candidates.loc[candidates["is_eligible"]]
    return {
        "phase": supervised_contract["phase"],
        "contract_version": supervised_contract["contract_version"],
        "prepared_input": supervised_contract["prepared_input"],
        "prepared_sha256": prepared_sha256,
        "split_audit": supervised_contract["split_audit"],
        "split_audit_sha256": split_audit_sha256,
        "feature_audit": supervised_contract["feature_audit"],
        "feature_audit_sha256": feature_audit_sha256,
        "alignment": deepcopy(supervised_contract["alignment"]),
        "feature_count": len(supervised_contract["feature_order"]),
        "feature_order": deepcopy(supervised_contract["feature_order"]),
        "development": {
            "raw_rows": int(len(candidates)),
            "eligible_rows": int(candidates["is_eligible"].sum()),
            "excluded_rows": int((~candidates["is_eligible"]).sum()),
            "invalid_feature_vector": int(
                reason_counts.get("invalid_feature_vector", 0)
            ),
            "missing_target_with_valid_features": int(
                reason_counts.get("missing_target_with_valid_features", 0)
            ),
            "eligible_start": eligible["target_timestamp"].min().strftime(
                DATETIME_FORMAT
            ),
            "eligible_end": eligible["target_timestamp"].max().strftime(
                DATETIME_FORMAT
            ),
        },
        "eligibility": deepcopy(supervised_contract["eligibility"]),
        "cross_validation": {
            "method": supervised_contract["cross_validation"]["method"],
            "folds": fold_records,
            "validation_history_policy": supervised_contract[
                "cross_validation"
            ]["validation_history_policy"],
            "same_eligible_population_for_all_candidates": True,
        },
        "holdout": {
            "reserved": True,
            "features_materialized": False,
            "target_statistics_reported": False,
            "evaluation_owner": "phase_07",
        },
        "recursive_24h": {
            "matrix_materialized": False,
            "evaluation_owner": "phase_07",
        },
        "persistence": {
            "xy_table_written": False,
            "reconstruction_owner": (
                "practice_3_v2.data.supervised_dataset"
            ),
        },
        "checks": {
            "development_only": True,
            "exact_feature_order": True,
            "target_in_X": False,
            "metadata_in_X": False,
            "feature_imputation_applied": False,
            "shuffle_applied": False,
            "eligible_X_finite": True,
            "eligible_y_finite": True,
            "xy_timestamp_aligned": True,
            "forecast_origin_offset_valid": True,
            "folds_chronological": True,
            "folds_non_overlapping": True,
            "holdout_used_for_construction": False,
        },
        "status": "PASS",
    }


def save_phase_05_artifact(audit: dict[str, Any], output_path: Path) -> None:
    """Validate staged JSON before atomic promotion."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            dir=output_path.parent,
            delete=False,
        ) as temporary:
            json.dump(audit, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        with temporary_path.open(encoding="utf-8") as file:
            reloaded = json.load(file)
        if reloaded != audit or reloaded.get("status") != "PASS":
            raise ValueError("Serialized Phase 5 audit validation failed.")
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def run_phase_05(
    project_root: Path = PROJECT_ROOT,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Run official development-only X/y construction validation."""

    project_root = Path(project_root).resolve()
    (
        data_contract,
        preparation_contract,
        split_contract,
        feature_contract,
        supervised_contract,
        phase_01_audit,
        _phase_02_audit,
        _phase_03_audit,
        _phase_04_audit,
    ) = load_phase_05_inputs(project_root)
    prepared, prepared_sha256 = validate_prepared_input(
        project_root / supervised_contract["prepared_input"],
        data_contract,
        preparation_contract,
        split_contract,
        phase_01_audit,
    )
    development = extract_development_data(
        prepared,
        data_contract,
        split_contract,
    )
    source_before = development.copy(deep=True)
    candidates = build_supervised_candidates(
        development,
        data_contract,
        feature_contract,
        supervised_contract,
    )
    folds = apply_expanding_window_folds(
        candidates,
        data_contract,
        split_contract,
        supervised_contract,
    )
    validate_supervised_population(
        candidates,
        folds,
        development,
        data_contract,
        split_contract,
        supervised_contract,
    )
    pd.testing.assert_frame_equal(development, source_before)
    audit = build_phase_05_audit(
        candidates,
        folds,
        prepared_sha256,
        calculate_sha256(project_root / supervised_contract["split_audit"]),
        calculate_sha256(project_root / supervised_contract["feature_audit"]),
        split_contract,
        supervised_contract,
    )
    destination = output_path or (
        project_root / supervised_contract["outputs"]["audit"]
    )
    save_phase_05_artifact(audit, destination)
    return audit


def main() -> int:
    """Run Phase 5 from the command line."""

    audit = run_phase_05()
    print(
        json.dumps(
            {
                "phase": audit["phase"],
                "development_rows": audit["development"]["raw_rows"],
                "eligible_samples": audit["development"]["eligible_rows"],
                "folds": len(audit["cross_validation"]["folds"]),
                "status": audit["status"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
