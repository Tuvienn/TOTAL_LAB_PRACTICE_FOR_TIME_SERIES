"""Temporal split and validation design for Practice 3 v2."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import os
import tempfile
from typing import Any

import pandas as pd

from practice_3_v2.data.data_preparation import (
    calculate_sha256,
    load_and_validate_saved_dataset,
    load_json_contract,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _parse_boundary(value: str) -> pd.Timestamp:
    """Parse an approved timestamp boundary strictly."""

    try:
        parsed = pd.to_datetime(
            value,
            format="%Y-%m-%d %H:%M:%S",
            errors="raise",
        )
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid temporal boundary: {value!r}.") from error
    return pd.Timestamp(parsed)


def load_phase_02_inputs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Load all approved contracts and the Phase 1 audit."""

    project_root = Path(project_root).resolve()
    data_contract = load_json_contract(project_root / "config/data_contract.json")
    preparation_contract = load_json_contract(
        project_root / "config/data_preparation.json"
    )
    forecasting_contract = load_json_contract(
        project_root / "config/forecasting_contract.json"
    )
    split_contract = load_json_contract(
        project_root / "config/temporal_split.json"
    )
    audit_path = project_root / preparation_contract["outputs"]["audit"]
    if not audit_path.is_file():
        raise FileNotFoundError(f"Phase 1 audit not found: {audit_path}")
    with audit_path.open(encoding="utf-8") as file:
        phase_01_audit = json.load(file)
    if phase_01_audit.get("status") != "PASS":
        raise ValueError("Phase 1 audit status must be PASS.")
    return (
        data_contract,
        preparation_contract,
        forecasting_contract,
        split_contract,
    )


def validate_prepared_input(
    path: Path,
    data_contract: dict[str, Any],
    preparation_contract: dict[str, Any],
    split_contract: dict[str, Any],
    phase_01_audit: dict[str, Any],
) -> tuple[pd.DataFrame, str]:
    """Load prepared data and validate its identity and structure."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Prepared dataset not found: {path}")
    actual_sha256 = calculate_sha256(path)
    expected_sha256 = split_contract["prepared_sha256"]
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "Prepared dataset SHA-256 does not match the split contract. "
            f"Expected {expected_sha256}; got {actual_sha256}."
        )
    if phase_01_audit.get("processed_sha256") != actual_sha256:
        raise ValueError("Prepared dataset does not match the Phase 1 audit.")

    prepared_data = load_and_validate_saved_dataset(
        path,
        data_contract,
        preparation_contract,
    )
    timestamp_column = data_contract["timestamp_column"]
    development = split_contract["development"]
    holdout = split_contract["holdout"]
    if prepared_data[timestamp_column].min() != _parse_boundary(
        development["start_inclusive"]
    ):
        raise ValueError("Prepared start timestamp does not match the contract.")
    if prepared_data[timestamp_column].max() != _parse_boundary(
        holdout["end_inclusive"]
    ):
        raise ValueError("Prepared end timestamp does not match the contract.")
    return prepared_data, actual_sha256


def validate_contract_alignment(
    forecasting_contract: dict[str, Any],
    split_contract: dict[str, Any],
) -> None:
    """Reject scientific conflicts between forecasting and split contracts."""

    temporal_design = forecasting_contract["temporal_design"]
    development = split_contract["development"]
    holdout = split_contract["holdout"]
    cross_validation = split_contract["cross_validation"]
    expected_pairs = (
        (
            temporal_design["development_start"],
            development["start_inclusive"],
        ),
        (
            temporal_design["development_end_exclusive"],
            development["end_exclusive"],
        ),
        (temporal_design["holdout_start"], holdout["start_inclusive"]),
        (temporal_design["holdout_end"], holdout["end_inclusive"]),
        (temporal_design["holdout_label"], holdout["label"]),
        (
            temporal_design["holdout_is_claimed_unseen"],
            holdout["is_claimed_unseen"],
        ),
        (temporal_design["cv_method"], cross_validation["method"]),
        (temporal_design["cv_splits"], cross_validation["splits"]),
        (temporal_design["shuffle"], cross_validation["shuffle"]),
    )
    if any(forecasting != split for forecasting, split in expected_pairs):
        raise ValueError("Split contract conflicts with forecasting contract.")
    semantics = split_contract["timestamp_semantics"]
    primary_task = forecasting_contract["primary_task"]
    if (
        semantics["forecast_origin"] != forecasting_contract["forecast_origin"]
        or primary_task["horizon"] != 1
        or semantics["primary_target"] != "t_plus_1_hour"
    ):
        raise ValueError("Target timestamp semantics conflict with primary task.")


def build_development_holdout_masks(
    prepared_data: pd.DataFrame,
    data_contract: dict[str, Any],
    split_contract: dict[str, Any],
) -> tuple[pd.Series, pd.Series]:
    """Build mutually exclusive development and holdout masks."""

    timestamp_column = data_contract["timestamp_column"]
    timestamps = prepared_data[timestamp_column]
    development = split_contract["development"]
    holdout = split_contract["holdout"]
    development_start = _parse_boundary(development["start_inclusive"])
    development_end = _parse_boundary(development["end_exclusive"])
    holdout_start = _parse_boundary(holdout["start_inclusive"])
    holdout_end = _parse_boundary(holdout["end_inclusive"])
    if development_end != holdout_start:
        raise ValueError("Development and holdout boundaries are not contiguous.")
    if not development_start < development_end <= holdout_end:
        raise ValueError("Temporal boundaries are not strictly ordered.")

    development_mask = timestamps.ge(development_start) & timestamps.lt(
        development_end
    )
    holdout_mask = timestamps.ge(holdout_start) & timestamps.le(holdout_end)
    if (development_mask & holdout_mask).any():
        raise ValueError("Development and holdout overlap.")
    if not (development_mask | holdout_mask).all():
        raise ValueError("Development and holdout do not cover every timestamp.")
    return development_mask, holdout_mask


def build_expanding_window_folds(
    prepared_data: pd.DataFrame,
    data_contract: dict[str, Any],
    split_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build expanding fold masks from approved target-time boundaries."""

    timestamp_column = data_contract["timestamp_column"]
    timestamps = prepared_data[timestamp_column]
    development_start = _parse_boundary(
        split_contract["development"]["start_inclusive"]
    )
    folds: list[dict[str, Any]] = []
    for fold_contract in split_contract["cross_validation"]["folds"]:
        validation_start = _parse_boundary(
            fold_contract["validation_start_inclusive"]
        )
        validation_end = _parse_boundary(
            fold_contract["validation_end_exclusive"]
        )
        if not development_start < validation_start < validation_end:
            raise ValueError("Invalid expanding-window fold boundaries.")
        train_mask = timestamps.ge(development_start) & timestamps.lt(
            validation_start
        )
        validation_mask = timestamps.ge(validation_start) & timestamps.lt(
            validation_end
        )
        folds.append(
            {
                "fold": int(fold_contract["fold"]),
                "train_mask": train_mask,
                "validation_mask": validation_mask,
                "validation_start": validation_start,
                "validation_end_exclusive": validation_end,
                "contract": fold_contract,
            }
        )
    return folds


def _partition_summary(
    prepared_data: pd.DataFrame,
    mask: pd.Series,
    data_contract: dict[str, Any],
) -> dict[str, Any]:
    """Summarize structural membership without target-value statistics."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    partition = prepared_data.loc[mask]
    datetime_format = "%Y-%m-%d %H:%M:%S"
    return {
        "rows": int(len(partition)),
        "observed_targets": int(partition[target_column].notna().sum()),
        "missing_targets": int(partition[target_column].isna().sum()),
        "time_start": partition[timestamp_column].min().strftime(
            datetime_format
        ),
        "time_end": partition[timestamp_column].max().strftime(datetime_format),
    }


def validate_temporal_split(
    prepared_data: pd.DataFrame,
    data_contract: dict[str, Any],
    split_contract: dict[str, Any],
    development_mask: pd.Series,
    holdout_mask: pd.Series,
    folds: list[dict[str, Any]],
) -> None:
    """Validate coverage, counts, chronology, and fold expansion."""

    timestamp_column = data_contract["timestamp_column"]
    if split_contract["timestamp_semantics"]["split_key"] != "target_timestamp":
        raise ValueError("Split key must be target_timestamp.")
    cross_validation = split_contract["cross_validation"]
    if cross_validation["method"] != "expanding_window":
        raise ValueError("Cross-validation method must be expanding_window.")
    if cross_validation["shuffle"] is not False:
        raise ValueError("Temporal split cannot shuffle observations.")
    if cross_validation["gap_hours"] != 0:
        raise ValueError("Approved one-step CV gap must be zero hours.")
    if len(folds) != cross_validation["splits"]:
        raise ValueError("Unexpected cross-validation fold count.")

    for name, mask, expected in (
        ("development", development_mask, split_contract["development"]),
        ("holdout", holdout_mask, split_contract["holdout"]),
    ):
        summary = _partition_summary(prepared_data, mask, data_contract)
        for field in ("rows", "observed_targets", "missing_targets"):
            if summary[field] != expected[f"expected_{field}"]:
                raise ValueError(f"Unexpected {name} {field} count.")

    prior_train_rows = 0
    prior_validation_end: pd.Timestamp | None = None
    development_end = _parse_boundary(
        split_contract["development"]["end_exclusive"]
    )
    for fold in folds:
        train_mask = fold["train_mask"]
        validation_mask = fold["validation_mask"]
        fold_contract = fold["contract"]
        if (train_mask & validation_mask).any():
            raise ValueError("Fold train and validation overlap.")
        if (validation_mask & ~development_mask).any():
            raise ValueError("Fold validation lies outside development.")
        train_times = prepared_data.loc[train_mask, timestamp_column]
        validation_times = prepared_data.loc[validation_mask, timestamp_column]
        if train_times.max() >= validation_times.min():
            raise ValueError("Fold chronology is invalid.")
        if len(train_times) <= prior_train_rows:
            raise ValueError("Fold train windows do not expand monotonically.")
        if (
            prior_validation_end is not None
            and validation_times.min() != prior_validation_end
        ):
            raise ValueError("Validation folds are not contiguous.")
        prior_train_rows = len(train_times)
        prior_validation_end = fold["validation_end_exclusive"]

        train_summary = _partition_summary(
            prepared_data,
            train_mask,
            data_contract,
        )
        validation_summary = _partition_summary(
            prepared_data,
            validation_mask,
            data_contract,
        )
        expected_values = {
            "train_rows": train_summary["rows"],
            "train_observed_targets": train_summary["observed_targets"],
            "validation_rows": validation_summary["rows"],
            "validation_observed_targets": validation_summary[
                "observed_targets"
            ],
            "validation_missing_targets": validation_summary[
                "missing_targets"
            ],
        }
        for field, actual in expected_values.items():
            if actual != fold_contract[f"expected_{field}"]:
                raise ValueError(
                    f"Unexpected fold {fold['fold']} {field} count."
                )
    if prior_validation_end != development_end:
        raise ValueError("Final validation fold does not end at development end.")


def build_phase_02_audit(
    prepared_data: pd.DataFrame,
    prepared_sha256: str,
    data_contract: dict[str, Any],
    split_contract: dict[str, Any],
    development_mask: pd.Series,
    holdout_mask: pd.Series,
    folds: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build deterministic structural evidence for the approved split."""

    fold_audits: list[dict[str, Any]] = []
    for fold in folds:
        fold_audits.append(
            {
                "fold": fold["fold"],
                "train": _partition_summary(
                    prepared_data,
                    fold["train_mask"],
                    data_contract,
                ),
                "validation": _partition_summary(
                    prepared_data,
                    fold["validation_mask"],
                    data_contract,
                ),
                "validation_start_inclusive": fold["contract"][
                    "validation_start_inclusive"
                ],
                "validation_end_exclusive": fold["contract"][
                    "validation_end_exclusive"
                ],
            }
        )

    return {
        "phase": split_contract["phase"],
        "contract_version": split_contract["contract_version"],
        "prepared_input": split_contract["prepared_input"],
        "prepared_sha256": prepared_sha256,
        "timestamp_semantics": deepcopy(split_contract["timestamp_semantics"]),
        "development": {
            **_partition_summary(
                prepared_data,
                development_mask,
                data_contract,
            ),
            "start_inclusive": split_contract["development"][
                "start_inclusive"
            ],
            "end_exclusive": split_contract["development"]["end_exclusive"],
        },
        "holdout": {
            **_partition_summary(
                prepared_data,
                holdout_mask,
                data_contract,
            ),
            "start_inclusive": split_contract["holdout"]["start_inclusive"],
            "end_inclusive": split_contract["holdout"]["end_inclusive"],
            "label": split_contract["holdout"]["label"],
            "is_claimed_unseen": split_contract["holdout"][
                "is_claimed_unseen"
            ],
        },
        "cross_validation": {
            "method": split_contract["cross_validation"]["method"],
            "splits": split_contract["cross_validation"]["splits"],
            "shuffle": split_contract["cross_validation"]["shuffle"],
            "gap_hours": split_contract["cross_validation"]["gap_hours"],
            "validation_duration": split_contract["cross_validation"][
                "validation_duration"
            ],
            "folds": fold_audits,
        },
        "missing_target_policy": deepcopy(
            split_contract["missing_target_policy"]
        ),
        "checks": {
            "timeline_coverage_complete": bool(
                (development_mask | holdout_mask).all()
            ),
            "development_holdout_overlap": int(
                (development_mask & holdout_mask).sum()
            ),
            "fold_train_expands": True,
            "fold_validation_non_overlapping": True,
            "holdout_target_values_inspected": False,
        },
        "status": "PASS",
    }


def save_phase_02_artifact(
    audit: dict[str, Any],
    audit_path: Path,
) -> dict[str, Any]:
    """Validate and atomically promote the Phase 2 JSON audit."""

    if audit.get("status") != "PASS":
        raise ValueError("Phase 2 audit status must be PASS.")
    audit_path = Path(audit_path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json.tmp",
            prefix="phase_02_",
            dir=audit_path.parent,
            delete=False,
            encoding="utf-8",
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(audit, temporary_file, indent=2, ensure_ascii=False)
            temporary_file.write("\n")
        with temporary_path.open(encoding="utf-8") as file:
            serialized_audit = json.load(file)
        if serialized_audit != audit:
            raise ValueError("Serialized Phase 2 audit validation failed.")
        os.replace(temporary_path, audit_path)
        temporary_path = None
        return audit
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def run_phase_02(
    project_root: Path = PROJECT_ROOT,
    audit_path: Path | None = None,
) -> dict[str, Any]:
    """Run Phase 2 from approved inputs to a validated split audit."""

    project_root = Path(project_root).resolve()
    (
        data_contract,
        preparation_contract,
        forecasting_contract,
        split_contract,
    ) = load_phase_02_inputs(project_root)
    phase_01_audit_path = (
        project_root / preparation_contract["outputs"]["audit"]
    )
    with phase_01_audit_path.open(encoding="utf-8") as file:
        phase_01_audit = json.load(file)
    validate_contract_alignment(forecasting_contract, split_contract)
    prepared_path = project_root / split_contract["prepared_input"]
    prepared_data, prepared_sha256 = validate_prepared_input(
        prepared_path,
        data_contract,
        preparation_contract,
        split_contract,
        phase_01_audit,
    )
    development_mask, holdout_mask = build_development_holdout_masks(
        prepared_data,
        data_contract,
        split_contract,
    )
    folds = build_expanding_window_folds(
        prepared_data,
        data_contract,
        split_contract,
    )
    validate_temporal_split(
        prepared_data,
        data_contract,
        split_contract,
        development_mask,
        holdout_mask,
        folds,
    )
    audit = build_phase_02_audit(
        prepared_data,
        prepared_sha256,
        data_contract,
        split_contract,
        development_mask,
        holdout_mask,
        folds,
    )
    resolved_audit_path = audit_path or (
        project_root / split_contract["outputs"]["audit"]
    )
    return save_phase_02_artifact(audit, Path(resolved_audit_path))


def main() -> int:
    """Execute Phase 2 and print its validated audit."""

    audit = run_phase_02()
    print(json.dumps(audit, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
