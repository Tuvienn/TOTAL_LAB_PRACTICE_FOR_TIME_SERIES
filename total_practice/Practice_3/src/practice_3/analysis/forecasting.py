from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
import shutil
from time import perf_counter
from typing import Callable
import warnings
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


DEFAULT_FORECASTING_CONFIG = Path("config/forecasting.json")
DEFAULT_PHASE_AUDITS = {
    "phase_01": Path("outputs/results/phase_01_data_quality.json"),
    "phase_02": Path("outputs/results/phase_02_feature_quality.json"),
    "phase_03": Path("outputs/results/phase_03_supervised_quality.json"),
    "phase_04": Path("outputs/results/phase_04_split_audit.json"),
}
DEFAULT_PHASE_05_CV_RESULTS = Path(
    "outputs/results/phase_05_cv_results.json"
)
DEFAULT_PHASE_05_MODEL_LOCK = Path(
    "outputs/results/phase_05_model_lock.json"
)
DEFAULT_RUNS_DIR = Path("runs")
RUN_SCHEMA_VERSION = 1
RUN_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")

EXPECTED_UPSTREAM_PHASES = {
    "phase_01": "phase_01_data_preparation",
    "phase_02": "phase_02_feature_engineering",
    "phase_03": "phase_03_x_y_preparation",
    "phase_04": "phase_04_temporal_split_validation",
}


APPROVED_FORECASTING_CONFIG = {
    "phase": "phase_06_forecasting_evaluation",
    "target": "AEP_MW",
    "frequency": "h",
    "selected_feature_configuration": "lag_only_p168",
    "candidate_order": [
        "seasonal_naive_24",
        "persistence",
        "xgboost_baseline",
        "xgboost_tuned",
        "random_forest",
    ],
    "one_step": {
        "strategy": "rolling_observed_history",
        "horizon": 1,
        "expected_test_rows": 8592,
        "test_start": "2017-08-03 00:00:00",
        "test_end": "2018-08-03 00:00:00",
    },
    "multi_step": {
        "strategy": "recursive",
        "horizon": 24,
        "origin_hour": 23,
        "origin_spacing_hours": 24,
        "require_complete_target_block": True,
        "shared_origins": True,
        "allow_actual_future_target_in_history": False,
    },
    "baselines": {
        "seasonal_naive_24": {"lag": 24},
        "persistence": {"lag": 1},
    },
    "metrics": {
        "primary": "mae",
        "secondary": "rmse",
        "multi_step_per_horizon": True,
        "multi_step_pooled": True,
    },
    "visualization": {
        "one_step_full_test": (
            "outputs/figures/phase_06_one_step_full_test.png"
        ),
        "one_step_first_14_days": (
            "outputs/figures/phase_06_one_step_first_14_days.png"
        ),
        "multi_step_error_by_horizon": (
            "outputs/figures/phase_06_multistep_error_by_horizon.png"
        ),
        "diagnostic_start": "2017-08-03 00:00:00",
        "diagnostic_end": "2017-08-16 23:00:00",
    },
    "policies": {
        "open_final_test_after_entry_gate": True,
        "refit_ml_candidates_on_full_train": True,
        "refit_per_test_timestamp": False,
        "allow_post_test_model_change": False,
        "persist_binary_models": False,
        "checkpoint_and_resume": True,
    },
}


@dataclass(frozen=True)
class Phase06EntryState:
    forecasting_config: dict
    phase_04_audit: dict
    cv_results: dict
    model_lock: dict
    audit: dict


def file_sha256(path: Path) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required Phase 6 artifact not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(payload: dict, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")
    temporary_path.replace(path)


def canonical_sha256(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def phase_06_timestamp(now: datetime | None = None) -> str:
    current = now or datetime.now(RUN_TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=RUN_TIMEZONE)
    return current.astimezone(RUN_TIMEZONE).isoformat(timespec="seconds")


def validate_phase_06_entry(
    forecasting_config_path: Path = DEFAULT_FORECASTING_CONFIG,
    phase_audit_paths: dict[str, Path] | None = None,
    cv_results_path: Path = DEFAULT_PHASE_05_CV_RESULTS,
    model_lock_path: Path = DEFAULT_PHASE_05_MODEL_LOCK,
) -> Phase06EntryState:
    """Validate Phase 1-5 evidence without reading final-test targets."""
    audit_paths = phase_audit_paths or DEFAULT_PHASE_AUDITS
    if set(audit_paths) != set(EXPECTED_UPSTREAM_PHASES):
        raise ValueError("Phase 6 requires exactly the Phase 1-4 audits.")

    config = load_forecasting_config(forecasting_config_path)
    upstream = {}
    for phase_name, expected_phase in EXPECTED_UPSTREAM_PHASES.items():
        path = Path(audit_paths[phase_name])
        artifact = load_json(path)
        if artifact.get("phase") != expected_phase:
            raise ValueError(f"{phase_name} audit identity is invalid.")
        if artifact.get("status") != "PASS":
            raise ValueError(f"{phase_name} has not passed.")
        upstream[phase_name] = {
            "path": str(path),
            "sha256": file_sha256(path),
            "status": "PASS",
        }

    phase_04_audit = load_json(audit_paths["phase_04"])
    top_level = phase_04_audit.get("top_level_split", {})
    final_test_phase_04 = phase_04_audit.get("final_test", {})
    expected_one_step = config["one_step"]
    expected_split = {
        "test_rows": expected_one_step["expected_test_rows"],
        "test_start": expected_one_step["test_start"],
        "test_end": expected_one_step["test_end"],
    }
    for key, expected_value in expected_split.items():
        if top_level.get(key) != expected_value:
            raise ValueError(f"Phase 4 split mismatch for {key}.")
    if final_test_phase_04 != {
        "sealed": True,
        "used_for_feature_selection": False,
        "used_for_tuning": False,
        "used_for_model_selection": False,
        "metrics_computed": False,
        "status": "PASS",
    }:
        raise ValueError("Phase 4 final-test sealing evidence is invalid.")

    cv_results_path = Path(cv_results_path)
    model_lock_path = Path(model_lock_path)
    cv_results = load_json(cv_results_path)
    model_lock = load_json(model_lock_path)
    if cv_results.get("phase") != "phase_05_model_training_selection":
        raise ValueError("Phase 5 CV result identity is invalid.")
    if model_lock.get("phase") != "phase_05_model_lock":
        raise ValueError("Phase 5 model-lock identity is invalid.")
    if cv_results.get("status") != "PASS" or model_lock.get("status") != "PASS":
        raise ValueError("Phase 5 evidence has not passed.")
    if model_lock.get("cv_results", {}).get("sha256") != file_sha256(
        cv_results_path
    ):
        raise ValueError("Phase 5 CV result hash does not match model lock.")

    candidate_order = config["candidate_order"]
    if cv_results.get("candidate_order") != candidate_order:
        raise ValueError("Phase 5 CV candidate order is invalid.")
    if model_lock.get("candidate_order") != candidate_order:
        raise ValueError("Phase 5 model-lock candidate order is invalid.")
    if list(model_lock.get("locked_candidates", {})) != candidate_order:
        raise ValueError("Locked candidate registry is incomplete or reordered.")
    selected_feature = config["selected_feature_configuration"]
    if cv_results.get("selected_feature_configuration") != selected_feature:
        raise ValueError("Phase 5 CV selected feature is invalid.")
    if model_lock.get("selected_feature_configuration") != selected_feature:
        raise ValueError("Phase 5 model-lock selected feature is invalid.")
    selected_candidate = model_lock.get("cv_selected_candidate")
    if selected_candidate not in candidate_order:
        raise ValueError("CV-selected candidate is not in the locked registry.")

    for candidate_id in candidate_order:
        candidate = model_lock["locked_candidates"][candidate_id]
        if candidate.get("model") != candidate_id:
            raise ValueError(f"Locked model identity is invalid: {candidate_id}.")
        if candidate.get("feature_configuration") != selected_feature:
            raise ValueError(
                f"Locked feature configuration is invalid: {candidate_id}."
            )
        if not isinstance(candidate.get("parameters"), dict):
            raise ValueError(f"Locked parameters are missing: {candidate_id}.")

    expected_phase_05_final = {
        "sealed": True,
        "rows": expected_one_step["expected_test_rows"],
        "start": expected_one_step["test_start"],
        "end": expected_one_step["test_end"],
        "feature_matrices_materialized": False,
        "target_values_accessed": False,
        "metrics_computed": False,
        "status": "PASS",
    }
    if model_lock.get("final_test") != expected_phase_05_final:
        raise ValueError("Phase 5 final-test state is not SEALED.")
    if model_lock.get("final_test_evaluated") is not False:
        raise ValueError("Phase 5 reports that final test was evaluated.")

    current_inputs = model_lock.get("input_identities", {})
    for identity_name, identity in current_inputs.items():
        path = Path(identity.get("path", ""))
        if not path.exists() or file_sha256(path) != identity.get("sha256"):
            raise ValueError(
                f"Phase 5 upstream identity changed: {identity_name}."
            )

    input_identities = {
        "forecasting_config": {
            "path": str(forecasting_config_path),
            "sha256": file_sha256(forecasting_config_path),
        },
        "phase_05_cv_results": {
            "path": str(cv_results_path),
            "sha256": file_sha256(cv_results_path),
        },
        "phase_05_model_lock": {
            "path": str(model_lock_path),
            "sha256": file_sha256(model_lock_path),
        },
        **upstream,
    }
    entry_audit = {
        "phase": "phase_06_entry_gate",
        "upstream_phases": upstream,
        "forecasting_config": validate_forecasting_config(config),
        "split_identity": expected_split,
        "candidate_order": candidate_order,
        "selected_feature_configuration": selected_feature,
        "cv_selected_candidate": selected_candidate,
        "final_test_state": "SEALED",
        "target_values_accessed": False,
        "metrics_computed": False,
        "input_identities": input_identities,
        "status": "PASS",
    }
    return Phase06EntryState(
        forecasting_config=config,
        phase_04_audit=phase_04_audit,
        cv_results=cv_results,
        model_lock=model_lock,
        audit=entry_audit,
    )


def build_phase_06_execution_identity(
    entry_state: Phase06EntryState,
) -> tuple[str, dict]:
    source_paths = {
        "forecasting": Path(__file__),
        "evaluation": Path(__file__).with_name("evaluation.py"),
        "visualization": (
            Path(__file__).parents[1]
            / "visualization"
            / "forecast_evaluation.py"
        ),
    }
    payload = {
        "stage": "phase_06_final_evaluation",
        "forecasting_config": entry_state.forecasting_config,
        "input_sha256": {
            name: identity["sha256"]
            for name, identity in entry_state.audit[
                "input_identities"
            ].items()
        },
        "source_sha256": {
            name: file_sha256(path) for name, path in source_paths.items()
        },
        "candidate_order": entry_state.audit["candidate_order"],
        "selected_feature_configuration": entry_state.audit[
            "selected_feature_configuration"
        ],
        "cv_selected_candidate": entry_state.audit[
            "cv_selected_candidate"
        ],
        "split_identity": entry_state.audit["split_identity"],
        "state_before": "SEALED",
    }
    return canonical_sha256(payload), payload


def create_phase_06_manifest(entry_state: Phase06EntryState) -> dict:
    execution_identity, _ = build_phase_06_execution_identity(entry_state)
    candidates = entry_state.forecasting_config["candidate_order"]
    units = [
        {
            "unit_id": f"{protocol}:{candidate_id}",
            "protocol": protocol,
            "candidate_id": candidate_id,
        }
        for protocol in ("one_step", "multi_step")
        for candidate_id in candidates
    ]
    return {
        "phase": "phase_06_forecasting_evaluation",
        "execution_identity": execution_identity,
        "candidate_order": candidates,
        "selected_feature_configuration": entry_state.audit[
            "selected_feature_configuration"
        ],
        "cv_selected_candidate": entry_state.audit[
            "cv_selected_candidate"
        ],
        "one_step_expected_rows_per_candidate": (
            entry_state.forecasting_config["one_step"][
                "expected_test_rows"
            ]
        ),
        "multi_step_horizon": entry_state.forecasting_config[
            "multi_step"
        ]["horizon"],
        "units": units,
        "unit_count": len(units),
        "checkpoint_unit": "candidate_protocol",
        "resume_supported": True,
        "final_test_state": "SEALED",
        "final_test_opened": False,
        "requires_human_execution": True,
        "status": "READY",
    }


def create_phase_06_run_id(
    execution_identity: str,
    now: datetime | None = None,
) -> str:
    current = now or datetime.now(RUN_TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=RUN_TIMEZONE)
    timestamp = current.astimezone(RUN_TIMEZONE).strftime("%Y%m%d_%H%M%S")
    return f"P6_final_evaluation_{timestamp}_{execution_identity[:8]}"


def initialize_phase_06_run(
    entry_state: Phase06EntryState,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    now: datetime | None = None,
) -> tuple[Path, dict, dict]:
    execution_identity, identity_payload = (
        build_phase_06_execution_identity(entry_state)
    )
    manifest = create_phase_06_manifest(entry_state)
    run_id = create_phase_06_run_id(execution_identity, now=now)
    run_dir = Path(runs_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    timestamp = phase_06_timestamp(now)
    units = {
        unit["unit_id"]: {
            **unit,
            "status": "PENDING",
            "result_path": None,
        }
        for unit in manifest["units"]
    }
    checkpoint = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "execution_identity": execution_identity,
        "status": "READY",
        "opening_event_count": 0,
        "final_test_opening_event": None,
        "units": units,
        "completed_unit_count": 0,
        "total_unit_count": len(units),
        "updated_at": timestamp,
    }
    metadata = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "phase_06_final_evaluation",
        "status": "READY",
        "created_at": timestamp,
        "updated_at": timestamp,
        "execution_identity": execution_identity,
        "execution_identity_payload": identity_payload,
        "final_test_state": "SEALED",
        "final_test_opened": False,
        "official_outputs_promoted": False,
    }
    save_json(entry_state.forecasting_config, run_dir / "config_snapshot.json")
    save_json(manifest, run_dir / "evaluation_manifest.json")
    save_json(checkpoint, run_dir / "checkpoint.json")
    save_json(metadata, run_dir / "run_metadata.json")
    (run_dir / f"{run_id}.log").touch(exist_ok=False)
    return run_dir, checkpoint, metadata


def load_resumable_phase_06_run(
    entry_state: Phase06EntryState,
    run_dir: Path,
) -> tuple[dict, dict]:
    run_dir = Path(run_dir)
    checkpoint = load_json(run_dir / "checkpoint.json")
    metadata = load_json(run_dir / "run_metadata.json")
    expected_identity, _ = build_phase_06_execution_identity(entry_state)
    for artifact_name, artifact in (
        ("checkpoint", checkpoint),
        ("metadata", metadata),
    ):
        if artifact.get("execution_identity") != expected_identity:
            raise ValueError(
                f"Phase 6 {artifact_name} execution identity changed."
            )
    if checkpoint.get("status") not in {
        "READY",
        "RUNNING",
        "INTERRUPTED",
    }:
        raise ValueError("Phase 6 run is not resumable.")
    opening_count = checkpoint.get("opening_event_count")
    opening_event = checkpoint.get("final_test_opening_event")
    if opening_count not in {0, 1}:
        raise ValueError("Final-test opening event count is invalid.")
    if (opening_count == 0) != (opening_event is None):
        raise ValueError("Final-test opening event state is inconsistent.")
    if checkpoint.get("total_unit_count") != len(
        checkpoint.get("units", {})
    ):
        raise ValueError("Phase 6 checkpoint unit count is invalid.")
    return checkpoint, metadata


def migrate_failed_run_after_approved_fix(
    entry_state: Phase06EntryState,
    run_dir: Path,
    fix_id: str,
    now: datetime | None = None,
) -> dict:
    """Preserve one opening event while adopting an approved source fix."""
    run_dir = Path(run_dir)
    checkpoint_path = run_dir / "checkpoint.json"
    metadata_path = run_dir / "run_metadata.json"
    manifest_path = run_dir / "evaluation_manifest.json"
    checkpoint = load_json(checkpoint_path)
    metadata = load_json(metadata_path)
    manifest = load_json(manifest_path)
    if checkpoint.get("status") != "FAILED" or metadata.get("status") != "FAILED":
        raise ValueError("Approved-fix migration requires a FAILED run.")
    if checkpoint.get("opening_event_count") != 1:
        raise ValueError("Approved-fix migration requires one opening event.")
    if metadata.get("official_outputs_promoted") is not False:
        raise ValueError("Cannot migrate a run with promoted official outputs.")
    old_identity = checkpoint.get("execution_identity")
    if (
        not old_identity
        or metadata.get("execution_identity") != old_identity
        or manifest.get("execution_identity") != old_identity
    ):
        raise ValueError("Failed-run execution identities are inconsistent.")
    passed_units = []
    for unit_id, unit in checkpoint.get("units", {}).items():
        if unit.get("status") != "PASS":
            continue
        load_completed_unit_frame(unit)
        passed_units.append(unit_id)
    if checkpoint.get("completed_unit_count") != len(passed_units):
        raise ValueError("Failed-run completed-unit count is inconsistent.")

    new_identity, new_payload = build_phase_06_execution_identity(entry_state)
    old_payload = metadata.get("execution_identity_payload", {})
    old_contract = {
        key: value
        for key, value in old_payload.items()
        if key != "source_sha256"
    }
    new_contract = {
        key: value
        for key, value in new_payload.items()
        if key != "source_sha256"
    }
    if old_contract != new_contract:
        raise ValueError(
            "Approved fix changed configuration, inputs, candidates, or split."
        )
    if old_identity == new_identity:
        raise ValueError("Approved-fix migration did not change source identity.")

    timestamp = phase_06_timestamp(now)
    migration = {
        "fix_id": fix_id,
        "approved_by": "Human",
        "migrated_at": timestamp,
        "old_execution_identity": old_identity,
        "new_execution_identity": new_identity,
        "preserved_opening_event_count": 1,
        "preserved_passed_units": passed_units,
        "official_outputs_promoted": False,
        "status": "PASS",
    }
    checkpoint["execution_identity"] = new_identity
    checkpoint["status"] = "INTERRUPTED"
    checkpoint["updated_at"] = timestamp
    checkpoint.setdefault("approved_fix_migrations", []).append(migration)
    metadata["execution_identity"] = new_identity
    metadata["execution_identity_payload"] = new_payload
    metadata["status"] = "INTERRUPTED"
    metadata["updated_at"] = timestamp
    metadata.setdefault("approved_fix_migrations", []).append(migration)
    manifest["execution_identity"] = new_identity
    manifest["final_test_state"] = "OPENED_FOR_FINAL_EVALUATION"
    manifest["final_test_opened"] = True
    manifest.setdefault("approved_fix_migrations", []).append(migration)
    save_json(migration, run_dir / "approved_fix_migration.json")
    save_json(manifest, manifest_path)
    save_json(metadata, metadata_path)
    save_json(checkpoint, checkpoint_path)
    return migration


def record_final_test_opening(
    run_dir: Path,
    entry_state: Phase06EntryState,
    now: datetime | None = None,
) -> dict:
    """Record the one allowed opening event after a passing entry gate."""
    if entry_state.audit.get("status") != "PASS":
        raise ValueError("Final test cannot open before entry-gate PASS.")
    checkpoint, metadata = load_resumable_phase_06_run(
        entry_state,
        run_dir,
    )
    if checkpoint["opening_event_count"] != 0:
        raise ValueError("Final-test opening event already exists.")
    timestamp = phase_06_timestamp(now)
    event = {
        "state_before": "SEALED",
        "purpose": "FINAL_EVALUATION_ONLY",
        "opened_after_phase_05_lock": True,
        "opened_at": timestamp,
        "locked_candidate_registry_identity": (
            entry_state.audit["input_identities"][
                "phase_05_model_lock"
            ]["sha256"]
        ),
        "split_identity": entry_state.audit["split_identity"],
        "state_after": "OPENED_FOR_FINAL_EVALUATION",
    }
    checkpoint["opening_event_count"] = 1
    checkpoint["final_test_opening_event"] = event
    checkpoint["status"] = "RUNNING"
    checkpoint["updated_at"] = timestamp
    metadata["status"] = "RUNNING"
    metadata["final_test_state"] = "OPENED_FOR_FINAL_EVALUATION"
    metadata["final_test_opened"] = True
    metadata["updated_at"] = timestamp
    save_json(checkpoint, Path(run_dir) / "checkpoint.json")
    save_json(metadata, Path(run_dir) / "run_metadata.json")
    return event


def create_phase_06_logger(run_dir: Path, run_id: str) -> logging.Logger:
    logger = logging.getLogger(f"practice_3.phase_06.{run_id}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    handler = logging.FileHandler(
        Path(run_dir) / f"{run_id}.log",
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)
    return logger


def update_phase_06_unit(
    run_dir: Path,
    entry_state: Phase06EntryState,
    unit_id: str,
    result_path: Path,
    now: datetime | None = None,
) -> dict:
    checkpoint, _ = load_resumable_phase_06_run(entry_state, run_dir)
    if checkpoint["opening_event_count"] != 1:
        raise ValueError(
            "Phase 6 unit cannot complete before final-test opening."
        )
    if unit_id not in checkpoint["units"]:
        raise ValueError(f"Unknown Phase 6 checkpoint unit: {unit_id}")
    unit = checkpoint["units"][unit_id]
    if unit["status"] == "PASS":
        raise ValueError(f"Phase 6 unit is already complete: {unit_id}")
    result_path = Path(result_path)
    if not result_path.exists():
        raise FileNotFoundError(f"Unit result does not exist: {result_path}")
    unit["status"] = "PASS"
    unit["result_path"] = str(result_path)
    unit["result_sha256"] = file_sha256(result_path)
    checkpoint["completed_unit_count"] = sum(
        item["status"] == "PASS" for item in checkpoint["units"].values()
    )
    checkpoint["status"] = "RUNNING"
    checkpoint["updated_at"] = phase_06_timestamp(now)
    save_json(checkpoint, Path(run_dir) / "checkpoint.json")
    return checkpoint


def load_completed_unit_frame(unit: dict) -> pd.DataFrame:
    if unit.get("status") != "PASS":
        raise ValueError("Cannot load an incomplete Phase 6 unit.")
    path = Path(unit.get("result_path", ""))
    if not path.exists() or file_sha256(path) != unit.get("result_sha256"):
        raise ValueError("Completed Phase 6 unit artifact changed.")
    frame = pd.read_csv(path)
    for column in ("timestamp", "forecast_origin", "target_timestamp"):
        if column in frame:
            frame[column] = pd.to_datetime(frame[column])
    return frame


def create_locked_estimator(candidate_id: str, parameters: dict):
    if candidate_id in {"xgboost_baseline", "xgboost_tuned"}:
        from xgboost import XGBRegressor

        return XGBRegressor(**parameters)
    if candidate_id == "random_forest":
        from sklearn.ensemble import RandomForestRegressor

        return RandomForestRegressor(**parameters)
    if candidate_id in {"seasonal_naive_24", "persistence"}:
        return None
    raise ValueError(f"Unknown locked candidate: {candidate_id}")


def reconstruct_phase_06_dataset(entry_state: Phase06EntryState):
    """Materialize final-test values only after the opening event exists."""
    from practice_3.data.temporal_split import (
        create_top_level_indices,
        get_common_timestamp_index,
        validate_phase_04_entry,
    )

    datasets, validation_config, _ = validate_phase_04_entry()
    selected_name = entry_state.audit["selected_feature_configuration"]
    dataset = datasets[selected_name]
    timestamp_index = get_common_timestamp_index(datasets)
    train_indices, test_indices, split_audit = create_top_level_indices(
        timestamp_index,
        validation_config,
    )
    if split_audit != entry_state.phase_04_audit["top_level_split"]:
        raise ValueError("Reconstructed Phase 6 split identity changed.")
    return dataset, train_indices, test_indices


def fit_locked_estimators(
    entry_state: Phase06EntryState,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> tuple[dict, dict]:
    estimators = {}
    evidence = {}
    for candidate_id in entry_state.audit["candidate_order"]:
        spec = entry_state.model_lock["locked_candidates"][candidate_id]
        estimator = create_locked_estimator(
            candidate_id,
            spec["parameters"],
        )
        if estimator is None:
            evidence[candidate_id] = {
                "model_fit_required": False,
                "status": "PASS",
            }
            continue
        start = perf_counter()
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            estimator.fit(X_train, y_train)
        evidence[candidate_id] = {
            "model_fit_required": True,
            "train_rows": len(X_train),
            "feature_count": X_train.shape[1],
            "training_seconds": float(perf_counter() - start),
            "warnings": [
                {
                    "category": item.category.__name__,
                    "message": str(item.message),
                }
                for item in caught_warnings
            ],
            "binary_model_persisted": False,
            "status": "PASS",
        }
        estimators[candidate_id] = estimator
    return estimators, evidence


def atomic_save_frame(frame: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    frame.to_csv(temporary_path, index=False)
    temporary_path.replace(path)


def promote_phase_06_artifacts(
    run_dir: Path,
    predictions: dict[str, pd.DataFrame],
    metrics: dict[str, dict],
    audit: dict,
    figures: dict[str, Path],
    output_root: Path = Path("."),
    promote_replace: Callable[[Path, Path], None] | None = None,
) -> dict:
    run_dir = Path(run_dir)
    output_root = Path(output_root)
    replace_file = promote_replace or (
        lambda source, target: source.replace(target)
    )
    relative_result_paths = {
        "one_step_predictions": Path(
            "outputs/results/phase_06_one_step_predictions.csv"
        ),
        "one_step_metrics": Path(
            "outputs/results/phase_06_one_step_metrics.json"
        ),
        "multi_step_predictions": Path(
            "outputs/results/phase_06_multistep_predictions.csv"
        ),
        "multi_step_metrics": Path(
            "outputs/results/phase_06_multistep_metrics.json"
        ),
        "evaluation_audit": Path(
            "outputs/results/phase_06_evaluation_audit.json"
        ),
    }
    result_paths = {
        name: output_root / path
        for name, path in relative_result_paths.items()
    }
    official_figures = {
        output_root / Path(path): Path(run_figure)
        for path, run_figure in figures.items()
    }
    staging_dir = run_dir / "promotion_staging"
    backup_dir = run_dir / "promotion_backup"
    checkpoint_path = run_dir / "checkpoint.json"
    metadata_path = run_dir / "run_metadata.json"
    original_checkpoint = load_json(checkpoint_path)
    original_metadata = load_json(metadata_path)
    if original_checkpoint.get("opening_event_count") != 1:
        raise ValueError("Phase 6 promotion requires one opening event.")
    if original_checkpoint.get("completed_unit_count") != (
        original_checkpoint.get("total_unit_count")
    ):
        raise ValueError("Phase 6 promotion requires all units to pass.")
    staging_dir.mkdir(parents=True, exist_ok=False)
    backup_dir.mkdir(parents=True, exist_ok=False)
    staged = {
        result_paths["one_step_predictions"]: (
            staging_dir / "phase_06_one_step_predictions.csv"
        ),
        result_paths["one_step_metrics"]: (
            staging_dir / "phase_06_one_step_metrics.json"
        ),
        result_paths["multi_step_predictions"]: (
            staging_dir / "phase_06_multistep_predictions.csv"
        ),
        result_paths["multi_step_metrics"]: (
            staging_dir / "phase_06_multistep_metrics.json"
        ),
        result_paths["evaluation_audit"]: (
            staging_dir / "phase_06_evaluation_audit.json"
        ),
    }
    atomic_save_frame(
        predictions["one_step"],
        staged[result_paths["one_step_predictions"]],
    )
    atomic_save_frame(
        predictions["multi_step"],
        staged[result_paths["multi_step_predictions"]],
    )
    save_json(
        metrics["one_step"],
        staged[result_paths["one_step_metrics"]],
    )
    save_json(
        metrics["multi_step"],
        staged[result_paths["multi_step_metrics"]],
    )
    save_json(audit, staged[result_paths["evaluation_audit"]])
    for index, (official_path, run_figure) in enumerate(
        official_figures.items(),
        start=1,
    ):
        staged[official_path] = (
            staging_dir / f"figure_{index}_{official_path.name}"
        )
        shutil.copy2(run_figure, staged[official_path])

    if len(staged) != 8 or not all(path.exists() for path in staged.values()):
        raise ValueError("Phase 6 promotion staging is incomplete.")
    staged_hashes = {
        official_path: file_sha256(staged_path)
        for official_path, staged_path in staged.items()
    }
    backups = {}
    for index, official_path in enumerate(staged, start=1):
        if official_path.exists():
            backup_path = backup_dir / f"{index}_{official_path.name}"
            shutil.copy2(official_path, backup_path)
            backups[official_path] = backup_path

    promoted = {
        name: {
            "path": str(result_paths[name]),
            "sha256": staged_hashes[result_paths[name]],
        }
        for name in result_paths
    }
    promoted["figures"] = {
        str(path): staged_hashes[path] for path in official_figures
    }
    committed = []
    try:
        for official_path, staged_path in staged.items():
            official_path.parent.mkdir(parents=True, exist_ok=True)
            replace_file(staged_path, official_path)
            committed.append(official_path)
        for official_path, expected_hash in staged_hashes.items():
            if (
                not official_path.exists()
                or file_sha256(official_path) != expected_hash
            ):
                raise RuntimeError(
                    f"Promoted artifact verification failed: {official_path}"
                )

        completed_at = phase_06_timestamp()
        completed_checkpoint = dict(original_checkpoint)
        completed_checkpoint["status"] = "COMPLETED"
        completed_checkpoint["updated_at"] = completed_at
        completed_metadata = dict(original_metadata)
        completed_metadata["status"] = "COMPLETED"
        completed_metadata["updated_at"] = completed_at
        completed_metadata["official_outputs_promoted"] = True
        completed_metadata["promoted_artifacts"] = promoted
        save_json(promoted, run_dir / "promoted_artifacts.json")
        save_json(completed_checkpoint, checkpoint_path)
        save_json(completed_metadata, metadata_path)
    except Exception:
        for official_path in reversed(committed):
            backup_path = backups.get(official_path)
            if backup_path is None:
                official_path.unlink(missing_ok=True)
            else:
                rollback_path = official_path.with_name(
                    f".{official_path.name}.rollback"
                )
                shutil.copy2(backup_path, rollback_path)
                rollback_path.replace(official_path)
        save_json(original_checkpoint, checkpoint_path)
        save_json(original_metadata, metadata_path)
        raise
    return promoted


def run_phase_06_final_evaluation(
    entry_state: Phase06EntryState | None = None,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    resume_run_dir: Path | None = None,
    now: datetime | None = None,
) -> dict:
    from practice_3.analysis.evaluation import (
        build_multistep_prediction_frame,
        build_one_step_prediction_frame,
        calculate_multistep_metrics,
        calculate_one_step_metrics,
    )
    from practice_3.visualization.forecast_evaluation import (
        plot_multistep_error_by_horizon,
        plot_one_step_diagnostic_window,
        plot_one_step_full_test,
    )

    current_entry = entry_state or validate_phase_06_entry()
    if resume_run_dir is None:
        run_dir, _, metadata = initialize_phase_06_run(
            current_entry,
            runs_dir=runs_dir,
            now=now,
        )
        opening_event = record_final_test_opening(
            run_dir,
            current_entry,
            now=now,
        )
    else:
        run_dir = Path(resume_run_dir)
        checkpoint, metadata = load_resumable_phase_06_run(
            current_entry,
            run_dir,
        )
        if checkpoint["opening_event_count"] == 0:
            opening_event = record_final_test_opening(
                run_dir,
                current_entry,
                now=now,
            )
        else:
            opening_event = checkpoint["final_test_opening_event"]

    run_id = metadata["run_id"]
    logger = create_phase_06_logger(run_dir, run_id)
    logger.info("Phase 6 final evaluation started or resumed.")
    try:
        dataset, train_indices, test_indices = reconstruct_phase_06_dataset(
            current_entry
        )
        X_train = dataset.X.iloc[train_indices]
        y_train = dataset.y.iloc[train_indices]
        X_test = dataset.X.iloc[test_indices]
        y_test = dataset.y.iloc[test_indices]
        test_timestamps = dataset.timestamp_index[test_indices]
        expected_rows = current_entry.forecasting_config["one_step"][
            "expected_test_rows"
        ]
        if len(test_indices) != expected_rows:
            raise ValueError("Final-test row count changed before evaluation.")

        logger.info("Refitting three locked ML candidates on full TRAIN.")
        estimators, fit_evidence = fit_locked_estimators(
            current_entry,
            X_train,
            y_train,
        )
        candidates = current_entry.audit["candidate_order"]
        selected_feature = current_entry.audit[
            "selected_feature_configuration"
        ]
        checkpoint = load_json(run_dir / "checkpoint.json")
        one_step_frames = []
        for candidate_id in candidates:
            unit_id = f"one_step:{candidate_id}"
            unit = checkpoint["units"][unit_id]
            if unit["status"] == "PASS":
                frame = load_completed_unit_frame(unit)
                logger.info("Reused completed unit %s.", unit_id)
            else:
                if candidate_id == "seasonal_naive_24":
                    prediction = predict_one_step_baseline(X_test, 24)
                elif candidate_id == "persistence":
                    prediction = predict_one_step_baseline(X_test, 1)
                else:
                    prediction = predict_one_step_model(
                        estimators[candidate_id],
                        X_test,
                    )
                frame = build_one_step_prediction_frame(
                    test_timestamps,
                    candidate_id,
                    y_test.to_numpy(dtype=np.float64),
                    prediction,
                    selected_feature,
                )
                path = run_dir / "predictions" / f"{unit_id}.csv"
                atomic_save_frame(frame, path)
                checkpoint = update_phase_06_unit(
                    run_dir,
                    current_entry,
                    unit_id,
                    path,
                )
                logger.info("Completed unit %s.", unit_id)
            one_step_frames.append(frame)

        sparse_target = pd.Series(
            dataset.y.to_numpy(dtype=np.float64),
            index=dataset.timestamp_index,
            name="AEP_MW",
        )
        target = build_complete_hourly_target_grid(sparse_target)
        multi_config = current_entry.forecasting_config["multi_step"]
        origins, origin_audit = build_eligible_origins(
            target=target,
            test_start=pd.Timestamp(
                current_entry.forecasting_config["one_step"]["test_start"]
            ),
            test_end=pd.Timestamp(
                current_entry.forecasting_config["one_step"]["test_end"]
            ),
            horizon=multi_config["horizon"],
            max_lag=len(dataset.feature_names),
            origin_hour=multi_config["origin_hour"],
            spacing_hours=multi_config["origin_spacing_hours"],
        )
        if len(origins) == 0:
            raise ValueError("No eligible multi-step origin was produced.")

        checkpoint = load_json(run_dir / "checkpoint.json")
        multi_step_frames = []
        for candidate_id in candidates:
            unit_id = f"multi_step:{candidate_id}"
            unit = checkpoint["units"][unit_id]
            if unit["status"] == "PASS":
                candidate_frame = load_completed_unit_frame(unit)
                logger.info("Reused completed unit %s.", unit_id)
            else:
                predictor = candidate_prediction_function(
                    candidate_id,
                    estimators.get(candidate_id),
                    dataset.feature_names,
                )
                blocks = []
                for origin in origins:
                    prediction = predictor(
                        target,
                        origin,
                        multi_config["horizon"],
                    )
                    actual = target.reindex(prediction.index)
                    blocks.append(
                        build_multistep_prediction_frame(
                            origin,
                            candidate_id,
                            actual,
                            prediction,
                            selected_feature,
                        )
                    )
                candidate_frame = pd.concat(blocks, ignore_index=True)
                path = run_dir / "predictions" / f"{unit_id}.csv"
                atomic_save_frame(candidate_frame, path)
                checkpoint = update_phase_06_unit(
                    run_dir,
                    current_entry,
                    unit_id,
                    path,
                )
                logger.info("Completed unit %s.", unit_id)
            multi_step_frames.append(candidate_frame)

        one_step = pd.concat(one_step_frames, ignore_index=True)
        multi_step = pd.concat(multi_step_frames, ignore_index=True)
        one_step_metrics = calculate_one_step_metrics(one_step, candidates)
        if (
            one_step_metrics["population"]["rows_per_candidate"]
            != expected_rows
        ):
            raise ValueError("One-step population differs from contract.")
        multi_step_metrics = calculate_multistep_metrics(
            multi_step,
            candidates,
            multi_config["horizon"],
        )

        run_figure_dir = run_dir / "figures"
        visualization = current_entry.forecasting_config["visualization"]
        run_figures = {
            visualization["one_step_full_test"]: (
                run_figure_dir / "phase_06_one_step_full_test.png"
            ),
            visualization["one_step_first_14_days"]: (
                run_figure_dir / "phase_06_one_step_first_14_days.png"
            ),
            visualization["multi_step_error_by_horizon"]: (
                run_figure_dir / "phase_06_multistep_error_by_horizon.png"
            ),
        }
        plot_one_step_full_test(
            one_step,
            current_entry.audit["cv_selected_candidate"],
            run_figures[visualization["one_step_full_test"]],
        )
        plot_one_step_diagnostic_window(
            one_step,
            candidates,
            pd.Timestamp(visualization["diagnostic_start"]),
            pd.Timestamp(visualization["diagnostic_end"]),
            run_figures[visualization["one_step_first_14_days"]],
        )
        plot_multistep_error_by_horizon(
            multi_step_metrics,
            candidates,
            run_figures[visualization["multi_step_error_by_horizon"]],
        )
        evaluation_audit = {
            "phase": "phase_06_forecasting_evaluation",
            "run_id": run_id,
            "execution_identity": checkpoint["execution_identity"],
            "entry_gate": current_entry.audit,
            "final_test_opening_event": opening_event,
            "candidate_reconstruction": fit_evidence,
            "one_step_population": one_step_metrics["population"],
            "multi_step_population": multi_step_metrics["population"],
            "multi_step_origin_audit": origin_audit,
            "cv_selected_candidate": current_entry.audit[
                "cv_selected_candidate"
            ],
            "post_test_model_change": False,
            "binary_models_persisted": False,
            "status": "PASS",
        }
        local_results = {
            "one_step_metrics": one_step_metrics,
            "multi_step_metrics": multi_step_metrics,
            "evaluation_audit": evaluation_audit,
        }
        for name, payload in local_results.items():
            save_json(payload, run_dir / f"{name}.json")
        checkpoint = load_json(run_dir / "checkpoint.json")
        if checkpoint["completed_unit_count"] != checkpoint["total_unit_count"]:
            raise ValueError("Phase 6 cannot complete with pending units.")
        promoted = promote_phase_06_artifacts(
            run_dir,
            {"one_step": one_step, "multi_step": multi_step},
            {
                "one_step": one_step_metrics,
                "multi_step": multi_step_metrics,
            },
            evaluation_audit,
            run_figures,
        )
        checkpoint = load_json(run_dir / "checkpoint.json")
        logger.info("Phase 6 final evaluation completed and promoted.")
        return {
            "run_dir": str(run_dir),
            "opening_event_count": checkpoint["opening_event_count"],
            "eligible_origin_count": len(origins),
            "one_step_rows_per_candidate": expected_rows,
            "official_outputs_promoted": True,
            "status": "PASS",
        }
    except KeyboardInterrupt:
        checkpoint = load_json(run_dir / "checkpoint.json")
        checkpoint["status"] = "INTERRUPTED"
        checkpoint["updated_at"] = phase_06_timestamp()
        metadata = load_json(run_dir / "run_metadata.json")
        metadata["status"] = "INTERRUPTED"
        metadata["updated_at"] = checkpoint["updated_at"]
        save_json(checkpoint, run_dir / "checkpoint.json")
        save_json(metadata, run_dir / "run_metadata.json")
        logger.warning("Phase 6 final evaluation interrupted by Human.")
        return {"run_dir": str(run_dir), "status": "INTERRUPTED"}
    except Exception:
        checkpoint = load_json(run_dir / "checkpoint.json")
        checkpoint["status"] = "FAILED"
        checkpoint["updated_at"] = phase_06_timestamp()
        metadata = load_json(run_dir / "run_metadata.json")
        metadata["status"] = "FAILED"
        metadata["updated_at"] = checkpoint["updated_at"]
        save_json(checkpoint, run_dir / "checkpoint.json")
        save_json(metadata, run_dir / "run_metadata.json")
        logger.exception("Phase 6 final evaluation failed.")
        raise
    finally:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


def validate_forecasting_config(config: dict) -> dict:
    if config != APPROVED_FORECASTING_CONFIG:
        raise ValueError(
            "Phase 6 forecasting configuration does not match the approved "
            "contract."
        )
    return {"approved_contract": True, "status": "PASS"}


def load_forecasting_config(
    config_path: Path = Path("config/forecasting.json"),
) -> dict:
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Phase 6 forecasting configuration not found: {config_path}"
        )
    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)
    validate_forecasting_config(config)
    return config


def validate_hourly_target_series(target: pd.Series) -> pd.Series:
    if not isinstance(target.index, pd.DatetimeIndex):
        raise TypeError("Target series must use a DatetimeIndex.")
    if not target.index.is_unique:
        raise ValueError("Target series timestamps must be unique.")
    if not target.index.is_monotonic_increasing:
        raise ValueError("Target series must be chronologically ordered.")
    expected = pd.date_range(
        target.index[0],
        target.index[-1],
        freq="h",
    )
    if not target.index.equals(expected):
        raise ValueError("Target series must use a complete hourly timeline.")
    return target.astype(np.float64).copy()


def build_complete_hourly_target_grid(target: pd.Series) -> pd.Series:
    """Represent supervised-timeline gaps as NaN without imputation."""
    if not isinstance(target.index, pd.DatetimeIndex):
        raise TypeError("Target series must use a DatetimeIndex.")
    if target.empty:
        raise ValueError("Target series must not be empty.")
    if not target.index.is_unique:
        raise ValueError("Target series timestamps must be unique.")
    if not target.index.is_monotonic_increasing:
        raise ValueError("Target series must be chronologically ordered.")
    if not target.index.floor("h").equals(target.index):
        raise ValueError("Target timestamps must align to hourly boundaries.")
    values = target.to_numpy(dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("Observed sparse target values must be finite.")
    complete_index = pd.date_range(
        target.index[0],
        target.index[-1],
        freq="h",
    )
    return target.astype(np.float64).reindex(complete_index)


def build_lag_feature_frame(
    history: pd.Series,
    target_timestamp: pd.Timestamp,
    feature_names: tuple[str, ...],
) -> pd.DataFrame:
    values = []
    for feature_name in feature_names:
        if not feature_name.startswith("lag_"):
            raise ValueError(
                f"Recursive forecasting received a non-lag feature: {feature_name}"
            )
        lag = int(feature_name.removeprefix("lag_"))
        if lag <= 0:
            raise ValueError("Lag values must be positive.")
        source_timestamp = target_timestamp - pd.Timedelta(hours=lag)
        if source_timestamp not in history.index:
            raise ValueError(
                f"Required history is unavailable at {source_timestamp}."
            )
        value = float(history.loc[source_timestamp])
        if not np.isfinite(value):
            raise ValueError(
                f"Required history is non-finite at {source_timestamp}."
            )
        values.append(value)
    return pd.DataFrame(
        [values],
        index=pd.DatetimeIndex([target_timestamp]),
        columns=list(feature_names),
        dtype=np.float64,
    )


def predict_one_step_model(estimator, X_test: pd.DataFrame) -> np.ndarray:
    predictions = np.asarray(estimator.predict(X_test), dtype=np.float64)
    if predictions.ndim != 1 or len(predictions) != len(X_test):
        raise ValueError("One-step model prediction shape is invalid.")
    if not np.isfinite(predictions).all():
        raise ValueError("One-step model predictions are non-finite.")
    return predictions


def predict_one_step_baseline(
    X_test: pd.DataFrame,
    lag: int,
) -> np.ndarray:
    feature_name = f"lag_{lag}"
    if feature_name not in X_test.columns:
        raise ValueError(f"Required baseline feature is missing: {feature_name}")
    predictions = X_test[feature_name].to_numpy(dtype=np.float64)
    if not np.isfinite(predictions).all():
        raise ValueError("One-step baseline predictions are non-finite.")
    return predictions


def build_eligible_origins(
    target: pd.Series,
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
    horizon: int,
    max_lag: int,
    origin_hour: int,
    spacing_hours: int,
) -> tuple[pd.DatetimeIndex, dict]:
    target = validate_hourly_target_series(target)
    if horizon <= 0 or max_lag <= 0 or spacing_hours <= 0:
        raise ValueError("Horizon, max lag, and spacing must be positive.")
    first_origin = test_start - pd.Timedelta(hours=1)
    if first_origin.hour != origin_hour:
        raise ValueError("The first scheduled origin does not match origin_hour.")
    last_origin = test_end - pd.Timedelta(hours=horizon)
    scheduled = pd.date_range(
        first_origin,
        last_origin,
        freq=f"{spacing_hours}h",
    )
    eligible = []
    exclusions = {
        "scheduled_origins": len(scheduled),
        "incomplete_target_block": 0,
        "non_finite_target_block": 0,
        "insufficient_or_non_finite_history": 0,
    }
    for origin in scheduled:
        future_index = pd.date_range(
            origin + pd.Timedelta(hours=1),
            periods=horizon,
            freq="h",
        )
        if (
            future_index[0] < test_start
            or future_index[-1] > test_end
            or not future_index.isin(target.index).all()
        ):
            exclusions["incomplete_target_block"] += 1
            continue
        future_values = target.reindex(future_index).to_numpy(
            dtype=np.float64
        )
        if not np.isfinite(future_values).all():
            exclusions["non_finite_target_block"] += 1
            continue
        history_index = pd.date_range(
            origin - pd.Timedelta(hours=max_lag - 1),
            origin,
            freq="h",
        )
        if not history_index.isin(target.index).all():
            exclusions["insufficient_or_non_finite_history"] += 1
            continue
        history_values = target.reindex(history_index).to_numpy(
            dtype=np.float64
        )
        if not np.isfinite(history_values).all():
            exclusions["insufficient_or_non_finite_history"] += 1
            continue
        eligible.append(origin)
    exclusions["eligible_origins"] = len(eligible)
    exclusions["excluded_origins"] = len(scheduled) - len(eligible)
    return pd.DatetimeIndex(eligible), exclusions


def predict_recursive_model(
    estimator,
    actual_history: pd.Series,
    origin: pd.Timestamp,
    horizon: int,
    feature_names: tuple[str, ...],
) -> pd.Series:
    history = actual_history.loc[:origin].astype(np.float64).copy()
    if history.empty or history.index[-1] != origin:
        raise ValueError("Actual history does not end at the forecast origin.")
    predictions = []
    prediction_index = []
    for step in range(1, horizon + 1):
        target_timestamp = origin + pd.Timedelta(hours=step)
        feature_frame = build_lag_feature_frame(
            history,
            target_timestamp,
            feature_names,
        )
        prediction = np.asarray(
            estimator.predict(feature_frame),
            dtype=np.float64,
        )
        if prediction.shape != (1,) or not np.isfinite(prediction[0]):
            raise ValueError("Recursive model prediction is invalid.")
        value = float(prediction[0])
        history.loc[target_timestamp] = value
        prediction_index.append(target_timestamp)
        predictions.append(value)
    return pd.Series(
        predictions,
        index=pd.DatetimeIndex(prediction_index),
        name="prediction",
        dtype=np.float64,
    )


def predict_recursive_persistence(
    actual_history: pd.Series,
    origin: pd.Timestamp,
    horizon: int,
) -> pd.Series:
    if origin not in actual_history.index:
        raise ValueError("Persistence origin is unavailable in history.")
    value = float(actual_history.loc[origin])
    if not np.isfinite(value):
        raise ValueError("Persistence origin value is non-finite.")
    index = pd.date_range(
        origin + pd.Timedelta(hours=1),
        periods=horizon,
        freq="h",
    )
    return pd.Series(value, index=index, name="prediction", dtype=np.float64)


def predict_recursive_seasonal_naive(
    actual_history: pd.Series,
    origin: pd.Timestamp,
    horizon: int,
    seasonal_lag: int = 24,
) -> pd.Series:
    index = pd.date_range(
        origin + pd.Timedelta(hours=1),
        periods=horizon,
        freq="h",
    )
    source_index = index - pd.Timedelta(hours=seasonal_lag)
    if not source_index.isin(actual_history.index).all():
        raise ValueError("Seasonal-naive history is incomplete.")
    values = actual_history.reindex(source_index).to_numpy(dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("Seasonal-naive history is non-finite.")
    return pd.Series(values, index=index, name="prediction")


def candidate_prediction_function(
    candidate_id: str,
    estimator,
    feature_names: tuple[str, ...],
) -> Callable[[pd.Series, pd.Timestamp, int], pd.Series]:
    if candidate_id == "persistence":
        return predict_recursive_persistence
    if candidate_id == "seasonal_naive_24":
        return predict_recursive_seasonal_naive
    if candidate_id in {
        "xgboost_baseline",
        "xgboost_tuned",
        "random_forest",
    }:
        return lambda history, origin, horizon: predict_recursive_model(
            estimator,
            history,
            origin,
            horizon,
            feature_names,
        )
    raise ValueError(f"Unknown locked candidate: {candidate_id}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the approved Phase 6 final evaluation protocol."
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--run-final-evaluation", action="store_true")
    action.add_argument(
        "--resume-final-evaluation",
        type=Path,
        metavar="RUN_DIR",
    )
    action.add_argument(
        "--prepare-approved-fix-resume",
        type=Path,
        metavar="FAILED_RUN_DIR",
    )
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    args = parser.parse_args(argv)

    entry_state = validate_phase_06_entry()
    if args.dry_run:
        print(
            json.dumps(
                create_phase_06_manifest(entry_state),
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    if args.prepare_approved_fix_resume is not None:
        migration = migrate_failed_run_after_approved_fix(
            entry_state,
            args.prepare_approved_fix_resume,
            fix_id="PHASE_06_MULTISTEP_TIMELINE_FIX",
        )
        print(json.dumps(migration, indent=2, ensure_ascii=False))
        return 0
    result = run_phase_06_final_evaluation(
        entry_state=entry_state,
        runs_dir=args.runs_dir,
        resume_run_dir=args.resume_final_evaluation,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 130 if result["status"] == "INTERRUPTED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
