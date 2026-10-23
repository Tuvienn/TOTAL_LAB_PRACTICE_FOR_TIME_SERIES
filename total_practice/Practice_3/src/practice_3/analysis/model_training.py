from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import logging
from pathlib import Path
import platform
import sys
from time import perf_counter
import warnings
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from practice_3.data.supervised_dataset import (
    SupervisedDataset,
    load_pass_audit,
)
from practice_3.data.temporal_split import (
    CVFoldIndices,
    EXPECTED_CONFIGURATION_NAMES,
    TemporalSplit,
    create_cv_fold_indices,
    create_top_level_indices,
    get_common_timestamp_index,
    validate_phase_04_entry,
    validate_validation_config,
)
from practice_3.visualization.training_progress import (
    render_screening_progress,
)


APPROVED_MODEL_TRAINING_CONFIG = {
    "phase": "phase_05_model_training_selection",
    "forecast_protocol": {
        "mode": "one_step",
        "target": "AEP_MW",
        "frequency": "h",
        "final_test_state": "SEALED",
    },
    "metrics": {
        "primary": "mae",
        "secondary": "rmse",
        "standard_deviation_ddof": 0,
        "cv_summary": ["mean", "standard_deviation"],
    },
    "baselines": {
        "seasonal_naive_24": {"lag": 24},
        "persistence": {"lag": 1},
    },
    "screening": {
        "configuration_order": list(EXPECTED_CONFIGURATION_NAMES),
        "model": "xgboost_baseline",
        "parameters": {
            "objective": "reg:squarederror",
            "n_estimators": 300,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "min_child_weight": 1,
            "reg_alpha": 0.0,
            "reg_lambda": 1.0,
            "tree_method": "hist",
            "random_state": 42,
            "n_jobs": -1,
        },
        "selection": {
            "relative_mae_tolerance": 0.01,
            "decision_order": [
                "mean_mae_relative_tolerance_pool",
                "fewer_features",
                "mean_rmse",
                "mae_standard_deviation",
                "approved_configuration_order",
            ],
        },
    },
    "tuning": {
        "search_method": "RandomizedSearchCV",
        "n_iter": 24,
        "scoring": {
            "mae": "neg_mean_absolute_error",
            "rmse": "neg_root_mean_squared_error",
        },
        "refit": "mae",
        "random_state": 42,
        "early_stopping": False,
        "search_space": {
            "n_estimators": [300, 500, 800],
            "max_depth": [3, 5, 7],
            "learning_rate": [0.03, 0.05, 0.1],
            "subsample": [0.7, 0.85, 1.0],
            "colsample_bytree": [0.7, 0.85, 1.0],
            "min_child_weight": [1, 5, 10],
            "reg_alpha": [0.0, 0.1, 1.0],
            "reg_lambda": [1.0, 5.0, 10.0],
        },
    },
    "random_forest": {
        "parameters": {
            "n_estimators": 300,
            "max_depth": None,
            "min_samples_split": 2,
            "min_samples_leaf": 1,
            "max_features": 1.0,
            "bootstrap": True,
            "random_state": 42,
            "n_jobs": -1,
        },
    },
    "model_lock": {
        "candidate_order": [
            "seasonal_naive_24",
            "persistence",
            "xgboost_baseline",
            "xgboost_tuned",
            "random_forest",
        ],
        "simplicity_order": [
            "seasonal_naive_24",
            "persistence",
            "xgboost_baseline",
            "random_forest",
            "xgboost_tuned",
        ],
        "relative_mae_tolerance": 0.01,
    },
    "policies": {
        "train_cv_only": True,
        "final_test_sealed": True,
        "materialize_final_test_in_training": False,
        "persist_binary_models": False,
    },
}

REQUIRED_RUNTIME_PACKAGES = (
    "matplotlib",
    "numpy",
    "pandas",
    "scikit-learn",
    "xgboost",
    "pytest",
)

DEFAULT_RUNS_DIR = Path("runs")
DEFAULT_SCREENING_OUTPUT = Path(
    "outputs/results/phase_05_screening_results.json"
)
DEFAULT_CV_RESULTS_OUTPUT = Path(
    "outputs/results/phase_05_cv_results.json"
)
DEFAULT_MODEL_LOCK_OUTPUT = Path(
    "outputs/results/phase_05_model_lock.json"
)
RUN_SCHEMA_VERSION = 1
RUN_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")


@dataclass(frozen=True)
class TrainingDataset:
    X: pd.DataFrame
    y: pd.Series
    timestamp_index: pd.DatetimeIndex
    feature_names: tuple[str, ...]


@dataclass(frozen=True)
class Phase05EntryState:
    training_datasets: dict[str, TrainingDataset]
    cv_fold_indices: tuple[CVFoldIndices, ...]
    model_config: dict
    final_test_metadata: dict
    audit: dict


def utc_offset_timestamp(now: datetime | None = None) -> str:
    current = now or datetime.now(RUN_TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=RUN_TIMEZONE)
    return current.astimezone(RUN_TIMEZONE).isoformat(timespec="seconds")


def canonical_sha256(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def save_json_result(result: dict, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f".{output_path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)
        file.write("\n")
    temporary_path.replace(output_path)


def load_json_result(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required run artifact not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_execution_identity(entry_state: Phase05EntryState) -> tuple[str, dict]:
    folds = [
        {
            "fold": fold.fold,
            "train_start_index": int(fold.train_indices[0]),
            "train_end_index": int(fold.train_indices[-1]),
            "validation_start_index": int(fold.validation_indices[0]),
            "validation_end_index": int(fold.validation_indices[-1]),
        }
        for fold in entry_state.cv_fold_indices
    ]
    payload = {
        "model_config": entry_state.model_config,
        "input_sha256": {
            name: identity["sha256"]
            for name, identity in entry_state.audit["input_identities"].items()
        },
        "runtime": entry_state.audit["runtime"],
        "folds": folds,
        "training_population": entry_state.audit["training_population"],
        "source_sha256": file_sha256(Path(__file__)),
        "final_test_state": entry_state.final_test_metadata,
    }
    return canonical_sha256(payload), payload


def create_run_id(
    execution_identity: str,
    now: datetime | None = None,
) -> str:
    current = now or datetime.now(RUN_TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=RUN_TIMEZONE)
    local = current.astimezone(RUN_TIMEZONE)
    timestamp = local.strftime("%Y%m%d_%H%M%S")
    nonce = hashlib.sha256(
        f"{execution_identity}:{local.isoformat()}".encode("utf-8")
    ).hexdigest()[:8]
    return f"P5_xgb_screening_{timestamp}_{nonce}"


def create_tuning_run_id(
    execution_identity: str,
    now: datetime | None = None,
) -> str:
    current = now or datetime.now(RUN_TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=RUN_TIMEZONE)
    local = current.astimezone(RUN_TIMEZONE)
    timestamp = local.strftime("%Y%m%d_%H%M%S")
    nonce = hashlib.sha256(
        f"{execution_identity}:{local.isoformat()}".encode("utf-8")
    ).hexdigest()[:8]
    return f"P5_xgb_tuning_{timestamp}_{nonce}"


def create_random_forest_run_id(
    execution_identity: str,
    now: datetime | None = None,
) -> str:
    current = now or datetime.now(RUN_TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=RUN_TIMEZONE)
    local = current.astimezone(RUN_TIMEZONE)
    timestamp = local.strftime("%Y%m%d_%H%M%S")
    nonce = hashlib.sha256(
        f"{execution_identity}:{local.isoformat()}".encode("utf-8")
    ).hexdigest()[:8]
    return f"P5_random_forest_{timestamp}_{nonce}"


def create_model_lock_run_id(
    execution_identity: str,
    now: datetime | None = None,
) -> str:
    current = now or datetime.now(RUN_TIMEZONE)
    if current.tzinfo is None:
        current = current.replace(tzinfo=RUN_TIMEZONE)
    local = current.astimezone(RUN_TIMEZONE)
    timestamp = local.strftime("%Y%m%d_%H%M%S")
    nonce = hashlib.sha256(
        f"{execution_identity}:{local.isoformat()}".encode("utf-8")
    ).hexdigest()[:8]
    return f"P5_model_lock_{timestamp}_{nonce}"


def create_run_logger(run_dir: Path, run_id: str) -> logging.Logger:
    run_dir = Path(run_dir)
    logger = logging.getLogger(f"practice_3.phase_05.{run_id}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(
        run_dir / f"{run_id}.log",
        mode="a",
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def close_run_logger(logger: logging.Logger) -> None:
    for handler in logger.handlers:
        handler.flush()
        handler.close()
    logger.handlers.clear()


def create_initial_checkpoint(
    entry_state: Phase05EntryState,
    run_id: str,
    execution_identity: str,
    created_at: str,
) -> dict:
    configuration_order = list(
        entry_state.model_config["screening"]["configuration_order"]
    )
    folds = [fold.fold for fold in entry_state.cv_fold_indices]
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "phase_05_feature_configuration_screening",
        "status": "READY",
        "created_at": created_at,
        "updated_at": created_at,
        "execution_identity": execution_identity,
        "configuration_order": configuration_order,
        "folds": folds,
        "total_fold_count": len(configuration_order) * len(folds),
        "completed_fold_count": 0,
        "current": None,
        "fold_status": {
            name: {str(fold): "PENDING" for fold in folds}
            for name in configuration_order
        },
        "fold_results": {name: {} for name in configuration_order},
        "failure": None,
        "final_test_evaluated": False,
    }


def write_run_state(
    run_dir: Path,
    checkpoint: dict,
    metadata: dict,
    plot_callback: Callable[[dict, Path], None] | None,
) -> None:
    timestamp = utc_offset_timestamp()
    checkpoint["updated_at"] = timestamp
    metadata["updated_at"] = timestamp
    metadata["status"] = checkpoint["status"]
    metadata["completed_fold_count"] = checkpoint["completed_fold_count"]
    save_json_result(checkpoint, Path(run_dir) / "checkpoint.json")
    save_json_result(metadata, Path(run_dir) / "run_metadata.json")
    if plot_callback is not None:
        plot_callback(checkpoint, Path(run_dir))


def initialize_screening_run(
    entry_state: Phase05EntryState,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    now: datetime | None = None,
    plot_callback: Callable[[dict, Path], None] | None = (
        render_screening_progress
    ),
) -> tuple[Path, dict, dict]:
    execution_identity, identity_payload = build_execution_identity(
        entry_state
    )
    run_id = create_run_id(execution_identity, now=now)
    run_dir = Path(runs_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    created_at = utc_offset_timestamp(now)
    checkpoint = create_initial_checkpoint(
        entry_state,
        run_id,
        execution_identity,
        created_at,
    )
    metadata = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "phase_05_feature_configuration_screening",
        "status": "READY",
        "created_at": created_at,
        "updated_at": created_at,
        "execution_identity": execution_identity,
        "execution_identity_payload": identity_payload,
        "manifest": create_screening_manifest(entry_state),
        "official_output": str(DEFAULT_SCREENING_OUTPUT),
        "completed_fold_count": 0,
        "artifacts": {
            "log": f"{run_id}.log",
            "metadata": "run_metadata.json",
            "config_snapshot": "config_snapshot.json",
            "checkpoint": "checkpoint.json",
            "progress": "training_progress.png",
            "duration": "fold_duration.png",
            "result": "screening_results.json",
        },
        "final_test_evaluated": False,
    }
    save_json_result(
        entry_state.model_config,
        run_dir / "config_snapshot.json",
    )
    write_run_state(
        run_dir,
        checkpoint,
        metadata,
        plot_callback,
    )
    return run_dir, checkpoint, metadata


def load_resumable_run(
    entry_state: Phase05EntryState,
    run_dir: Path,
) -> tuple[dict, dict]:
    run_dir = Path(run_dir)
    checkpoint = load_json_result(run_dir / "checkpoint.json")
    metadata = load_json_result(run_dir / "run_metadata.json")
    config_snapshot = load_json_result(run_dir / "config_snapshot.json")
    if checkpoint.get("schema_version") != RUN_SCHEMA_VERSION:
        raise ValueError("Screening checkpoint schema version is invalid.")
    if metadata.get("schema_version") != RUN_SCHEMA_VERSION:
        raise ValueError("Screening metadata schema version is invalid.")
    if checkpoint.get("run_id") != run_dir.name:
        raise ValueError("Checkpoint run ID does not match the run directory.")
    if metadata.get("run_id") != run_dir.name:
        raise ValueError("Metadata run ID does not match the run directory.")
    if config_snapshot != entry_state.model_config:
        raise ValueError("Run configuration snapshot does not match current config.")
    execution_identity, identity_payload = build_execution_identity(
        entry_state
    )
    if checkpoint.get("execution_identity") != execution_identity:
        raise ValueError("Checkpoint inputs or source no longer match this run.")
    if metadata.get("execution_identity") != execution_identity:
        raise ValueError("Run metadata inputs or source no longer match this run.")
    if metadata.get("execution_identity_payload") != identity_payload:
        raise ValueError("Run execution identity payload is inconsistent.")
    if checkpoint.get("status") == "COMPLETED":
        raise ValueError("The requested screening run is already completed.")
    if checkpoint.get("status") not in {
        "READY",
        "RUNNING",
        "INTERRUPTED",
        "FAILED",
    }:
        raise ValueError("The requested screening run is not resumable.")
    return checkpoint, metadata


def create_screening_manifest(entry_state: Phase05EntryState) -> dict:
    configuration_order = entry_state.model_config["screening"][
        "configuration_order"
    ]
    if tuple(configuration_order) != EXPECTED_CONFIGURATION_NAMES:
        raise ValueError("Screening configuration order is invalid.")

    fold_count = len(entry_state.cv_fold_indices)
    configurations = []
    for name in configuration_order:
        dataset = entry_state.training_datasets[name]
        configurations.append(
            {
                "name": name,
                "train_rows": len(dataset.X),
                "feature_count": len(dataset.feature_names),
                "cv_folds": fold_count,
                "planned_fits": fold_count,
            }
        )

    return {
        "stage": "phase_05_feature_configuration_screening",
        "configuration_count": len(configurations),
        "cv_fold_count": fold_count,
        "planned_model_fits": len(configurations) * fold_count,
        "configurations": configurations,
        "model": entry_state.model_config["screening"]["model"],
        "parameters": entry_state.model_config["screening"]["parameters"],
        "final_test_included": False,
        "requires_human_execution": True,
        "status": "READY",
    }


def evaluate_xgboost_configuration(
    configuration_name: str,
    dataset: TrainingDataset,
    cv_fold_indices: tuple[CVFoldIndices, ...],
    parameters: dict,
    estimator_factory: Callable | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> dict:
    if estimator_factory is None:
        from xgboost import XGBRegressor

        estimator_factory = XGBRegressor
    return evaluate_cv_estimator_configuration(
        configuration_name=configuration_name,
        dataset=dataset,
        cv_fold_indices=cv_fold_indices,
        parameters=parameters,
        estimator_factory=estimator_factory,
        progress_callback=progress_callback,
    )


def evaluate_cv_estimator_configuration(
    configuration_name: str,
    dataset: TrainingDataset,
    cv_fold_indices: tuple[CVFoldIndices, ...],
    parameters: dict,
    estimator_factory: Callable,
    progress_callback: Callable[[str], None] | None = None,
) -> dict:
    if configuration_name not in EXPECTED_CONFIGURATION_NAMES:
        raise ValueError(
            f"Unapproved screening configuration: {configuration_name}"
        )
    if tuple(dataset.X.columns) != dataset.feature_names:
        raise ValueError(
            f"Feature order is invalid for {configuration_name}."
        )
    fold_metrics = []
    total_start = perf_counter()
    for fold in cv_fold_indices:
        if fold.train_indices[-1] >= fold.validation_indices[0]:
            raise ValueError(
                f"CV fold {fold.fold} violates chronological order."
            )

        X_train = dataset.X.iloc[fold.train_indices]
        y_train = dataset.y.iloc[fold.train_indices]
        X_validation = dataset.X.iloc[fold.validation_indices]
        y_validation = dataset.y.iloc[fold.validation_indices]

        if not X_train.index.equals(y_train.index):
            raise ValueError(
                f"Training alignment failed in fold {fold.fold}."
            )
        if not X_validation.index.equals(y_validation.index):
            raise ValueError(
                f"Validation alignment failed in fold {fold.fold}."
            )
        if X_train.index[-1] >= X_validation.index[0]:
            raise ValueError(
                f"Timestamp chronology failed in fold {fold.fold}."
            )

        if progress_callback is not None:
            progress_callback(
                f"{configuration_name}: fold {fold.fold}/"
                f"{len(cv_fold_indices)}"
            )

        estimator = estimator_factory(**parameters)
        fold_start = perf_counter()
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            estimator.fit(X_train, y_train)
            predictions = np.asarray(
                estimator.predict(X_validation),
                dtype=np.float64,
            )
        training_seconds = perf_counter() - fold_start
        warning_records = [
            {
                "category": warning.category.__name__,
                "message": str(warning.message),
            }
            for warning in caught_warnings
        ]
        if progress_callback is not None and warning_records:
            progress_callback(
                f"{configuration_name}: fold {fold.fold} produced "
                f"{len(warning_records)} warning(s)"
            )

        if predictions.ndim != 1:
            raise ValueError(
                f"Prediction shape is invalid in fold {fold.fold}."
            )
        if len(predictions) != len(y_validation):
            raise ValueError(
                f"Prediction length is invalid in fold {fold.fold}."
            )

        metrics = calculate_regression_metrics(y_validation, predictions)
        fold_metrics.append(
            {
                "fold": fold.fold,
                "train_samples": len(X_train),
                "validation_samples": len(X_validation),
                "train_end": str(X_train.index[-1]),
                "validation_start": str(X_validation.index[0]),
                "validation_end": str(X_validation.index[-1]),
                **metrics,
                "training_seconds": float(training_seconds),
                "warnings": warning_records,
            }
        )

    aggregate = summarize_fold_metrics(fold_metrics, ddof=0)
    aggregate["total_training_seconds"] = float(
        perf_counter() - total_start
    )
    return {
        "configuration": configuration_name,
        "feature_count": len(dataset.feature_names),
        "parameters": dict(parameters),
        "fold_metrics": fold_metrics,
        "aggregate": aggregate,
        "status": "PASS",
    }


def select_feature_configuration(
    screening_results: dict,
    model_config: dict,
) -> tuple[str, dict]:
    validate_model_training_config(model_config)
    approved_order = model_config["screening"]["configuration_order"]
    results = screening_results.get("configurations", {})
    if tuple(results) != tuple(approved_order):
        raise ValueError(
            "Screening results do not contain all configurations in the "
            "approved order."
        )

    records = []
    for order, name in enumerate(approved_order):
        result = results[name]
        if result.get("status") != "PASS":
            raise ValueError(f"Screening result has not passed: {name}")
        aggregate = result["aggregate"]
        record = {
            "name": name,
            "order": order,
            "feature_count": int(result["feature_count"]),
            "mean_mae": float(aggregate["mean_mae"]),
            "mean_rmse": float(aggregate["mean_rmse"]),
            "std_mae": float(aggregate["std_mae"]),
        }
        if not np.isfinite(
            [record["mean_mae"], record["mean_rmse"], record["std_mae"]]
        ).all():
            raise ValueError(f"Non-finite screening metric found: {name}")
        records.append(record)

    best_mean_mae = min(record["mean_mae"] for record in records)
    tolerance = float(
        model_config["screening"]["selection"][
            "relative_mae_tolerance"
        ]
    )
    mae_threshold = best_mean_mae * (1.0 + tolerance)
    tolerance_candidates = [
        record
        for record in records
        if record["mean_mae"] <= mae_threshold
    ]
    fewest_features = min(
        record["feature_count"] for record in tolerance_candidates
    )
    simplicity_candidates = [
        record
        for record in tolerance_candidates
        if record["feature_count"] == fewest_features
    ]
    selected = min(
        simplicity_candidates,
        key=lambda record: (
            record["mean_rmse"],
            record["std_mae"],
            record["order"],
        ),
    )

    evidence = {
        "best_mean_mae": best_mean_mae,
        "relative_mae_tolerance": tolerance,
        "mae_threshold": mae_threshold,
        "tolerance_candidates": [
            record["name"] for record in tolerance_candidates
        ],
        "fewest_feature_count_in_tolerance": fewest_features,
        "simplicity_candidates": [
            record["name"] for record in simplicity_candidates
        ],
        "tie_break_order": [
            "mean_rmse",
            "mae_standard_deviation",
            "approved_configuration_order",
        ],
        "selected_configuration": selected["name"],
        "status": "PASS",
    }
    return selected["name"], evidence


def screen_feature_configurations(
    entry_state: Phase05EntryState,
    estimator_factory: Callable | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> dict:
    manifest = create_screening_manifest(entry_state)
    parameters = entry_state.model_config["screening"]["parameters"]
    results = {}

    for configuration_name in EXPECTED_CONFIGURATION_NAMES:
        results[configuration_name] = evaluate_xgboost_configuration(
            configuration_name=configuration_name,
            dataset=entry_state.training_datasets[configuration_name],
            cv_fold_indices=entry_state.cv_fold_indices,
            parameters=parameters,
            estimator_factory=estimator_factory,
            progress_callback=progress_callback,
        )

    screening_results = {
        "manifest": manifest,
        "configurations": results,
        "final_test_evaluated": False,
        "status": "PASS",
    }
    selected, evidence = select_feature_configuration(
        screening_results,
        entry_state.model_config,
    )
    screening_results["selected_feature_configuration"] = selected
    screening_results["selection_evidence"] = evidence
    return screening_results


def build_completed_screening_results(
    entry_state: Phase05EntryState,
    checkpoint: dict,
) -> dict:
    configuration_results = {}
    parameters = entry_state.model_config["screening"]["parameters"]
    ddof = int(
        entry_state.model_config["metrics"]["standard_deviation_ddof"]
    )
    for configuration_name in checkpoint["configuration_order"]:
        dataset = entry_state.training_datasets[configuration_name]
        fold_metrics = [
            checkpoint["fold_results"][configuration_name][str(fold)]
            for fold in checkpoint["folds"]
        ]
        aggregate = summarize_fold_metrics(fold_metrics, ddof=ddof)
        aggregate["total_training_seconds"] = float(
            sum(fold["training_seconds"] for fold in fold_metrics)
        )
        configuration_results[configuration_name] = {
            "configuration": configuration_name,
            "feature_count": len(dataset.feature_names),
            "parameters": dict(parameters),
            "fold_metrics": fold_metrics,
            "aggregate": aggregate,
            "status": "PASS",
        }

    screening_results = {
        "manifest": create_screening_manifest(entry_state),
        "configurations": configuration_results,
        "final_test_evaluated": False,
        "status": "PASS",
    }
    selected, evidence = select_feature_configuration(
        screening_results,
        entry_state.model_config,
    )
    screening_results["selected_feature_configuration"] = selected
    screening_results["selection_evidence"] = evidence
    return screening_results


def build_screening_result(
    entry_state: Phase05EntryState,
    checkpoint: dict,
) -> dict:
    return {
        "phase": "phase_05_feature_configuration_screening",
        "run_id": checkpoint["run_id"],
        "execution_identity": checkpoint["execution_identity"],
        "entry_gate_status": entry_state.audit["status"],
        "baseline_results": evaluate_forecasting_baselines(entry_state),
        "screening_results": build_completed_screening_results(
            entry_state,
            checkpoint,
        ),
        "final_test": entry_state.final_test_metadata,
        "runtime": entry_state.audit["runtime"],
        "input_identities": entry_state.audit["input_identities"],
        "status": "PASS",
    }


def reset_incomplete_fold(checkpoint: dict) -> None:
    current = checkpoint.get("current")
    if current is not None:
        configuration_name = current["configuration"]
        fold = str(current["fold"])
        if checkpoint["fold_status"][configuration_name][fold] != "PASS":
            checkpoint["fold_status"][configuration_name][fold] = "PENDING"
    for configuration_name in checkpoint["configuration_order"]:
        for fold in checkpoint["folds"]:
            fold_key = str(fold)
            status = checkpoint["fold_status"][configuration_name][fold_key]
            if status in {"RUNNING", "INTERRUPTED", "FAILED"}:
                checkpoint["fold_status"][configuration_name][fold_key] = (
                    "PENDING"
                )
    checkpoint["current"] = None
    checkpoint["failure"] = None


def execute_screening_run(
    entry_state: Phase05EntryState,
    run_dir: Path,
    checkpoint: dict,
    metadata: dict,
    output_path: Path,
    estimator_factory: Callable | None = None,
    plot_callback: Callable[[dict, Path], None] | None = (
        render_screening_progress
    ),
) -> dict:
    run_dir = Path(run_dir)
    output_path = Path(output_path)
    logger = create_run_logger(run_dir, checkpoint["run_id"])
    reset_incomplete_fold(checkpoint)
    checkpoint["status"] = "RUNNING"
    write_run_state(run_dir, checkpoint, metadata, plot_callback)
    logger.info(
        "Screening run %s started or resumed at %s completed folds.",
        checkpoint["run_id"],
        checkpoint["completed_fold_count"],
    )

    parameters = entry_state.model_config["screening"]["parameters"]
    try:
        for configuration_name in checkpoint["configuration_order"]:
            dataset = entry_state.training_datasets[configuration_name]
            for fold in entry_state.cv_fold_indices:
                fold_key = str(fold.fold)
                if (
                    checkpoint["fold_status"][configuration_name][fold_key]
                    == "PASS"
                ):
                    logger.info(
                        "%s fold %s skipped because checkpoint is PASS.",
                        configuration_name,
                        fold.fold,
                    )
                    continue

                checkpoint["current"] = {
                    "configuration": configuration_name,
                    "fold": fold.fold,
                }
                checkpoint["fold_status"][configuration_name][fold_key] = (
                    "RUNNING"
                )
                write_run_state(
                    run_dir,
                    checkpoint,
                    metadata,
                    plot_callback,
                )
                logger.info(
                    "%s fold %s/%s started.",
                    configuration_name,
                    fold.fold,
                    len(entry_state.cv_fold_indices),
                )

                one_fold_result = evaluate_xgboost_configuration(
                    configuration_name=configuration_name,
                    dataset=dataset,
                    cv_fold_indices=(fold,),
                    parameters=parameters,
                    estimator_factory=estimator_factory,
                    progress_callback=None,
                )
                fold_result = one_fold_result["fold_metrics"][0]
                checkpoint["fold_results"][configuration_name][fold_key] = (
                    fold_result
                )
                checkpoint["fold_status"][configuration_name][fold_key] = (
                    "PASS"
                )
                checkpoint["completed_fold_count"] = sum(
                    status == "PASS"
                    for statuses in checkpoint["fold_status"].values()
                    for status in statuses.values()
                )
                checkpoint["current"] = None
                write_run_state(
                    run_dir,
                    checkpoint,
                    metadata,
                    plot_callback,
                )
                logger.info(
                    "%s fold %s completed: MAE=%.6f RMSE=%.6f time=%.3fs.",
                    configuration_name,
                    fold.fold,
                    fold_result["mae"],
                    fold_result["rmse"],
                    fold_result["training_seconds"],
                )

        if checkpoint["completed_fold_count"] != checkpoint[
            "total_fold_count"
        ]:
            raise RuntimeError("Screening ended without completing all folds.")

        result = build_screening_result(entry_state, checkpoint)
        save_json_result(result, run_dir / "screening_results.json")
        save_json_result(result, output_path)
        checkpoint["status"] = "COMPLETED"
        checkpoint["current"] = None
        checkpoint["failure"] = None
        metadata["official_output"] = str(output_path)
        write_run_state(run_dir, checkpoint, metadata, plot_callback)
        logger.info(
            "Screening run completed. Selected configuration: %s.",
            result["screening_results"][
                "selected_feature_configuration"
            ],
        )
        return {
            **result,
            "run_dir": str(run_dir),
        }
    except KeyboardInterrupt:
        current = checkpoint.get("current")
        if current is not None:
            checkpoint["fold_status"][current["configuration"]][
                str(current["fold"])
            ] = "INTERRUPTED"
        checkpoint["status"] = "INTERRUPTED"
        checkpoint["failure"] = {
            "type": "KeyboardInterrupt",
            "message": "Training was interrupted by the Human.",
        }
        write_run_state(run_dir, checkpoint, metadata, plot_callback)
        logger.warning(
            "Screening interrupted after %s/%s completed folds.",
            checkpoint["completed_fold_count"],
            checkpoint["total_fold_count"],
        )
        return {
            "phase": "phase_05_feature_configuration_screening",
            "run_id": checkpoint["run_id"],
            "run_dir": str(run_dir),
            "completed_fold_count": checkpoint["completed_fold_count"],
            "total_fold_count": checkpoint["total_fold_count"],
            "final_test_evaluated": False,
            "status": "INTERRUPTED",
        }
    except Exception as exc:
        current = checkpoint.get("current")
        if current is not None:
            checkpoint["fold_status"][current["configuration"]][
                str(current["fold"])
            ] = "FAILED"
        checkpoint["status"] = "FAILED"
        checkpoint["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        write_run_state(run_dir, checkpoint, metadata, plot_callback)
        logger.exception("Screening run failed.")
        raise
    finally:
        close_run_logger(logger)


def run_phase_05_screening(
    output_path: Path = DEFAULT_SCREENING_OUTPUT,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    resume_run_dir: Path | None = None,
    entry_state: Phase05EntryState | None = None,
    estimator_factory: Callable | None = None,
    plot_callback: Callable[[dict, Path], None] | None = (
        render_screening_progress
    ),
) -> dict:
    current_entry_state = entry_state or validate_phase_05_entry()
    if resume_run_dir is None:
        run_dir, checkpoint, metadata = initialize_screening_run(
            current_entry_state,
            runs_dir=runs_dir,
            plot_callback=plot_callback,
        )
    else:
        run_dir = Path(resume_run_dir)
        checkpoint, metadata = load_resumable_run(
            current_entry_state,
            run_dir,
        )
    return execute_screening_run(
        entry_state=current_entry_state,
        run_dir=run_dir,
        checkpoint=checkpoint,
        metadata=metadata,
        output_path=output_path,
        estimator_factory=estimator_factory,
        plot_callback=plot_callback,
    )


def load_screening_result(
    screening_result_path: Path = DEFAULT_SCREENING_OUTPUT,
) -> dict:
    result = load_json_result(screening_result_path)
    if result.get("phase") != "phase_05_feature_configuration_screening":
        raise ValueError("Phase 5 screening result has an invalid identity.")
    if result.get("status") != "PASS":
        raise ValueError("Phase 5 screening result has not passed.")
    screening = result.get("screening_results", {})
    if screening.get("status") != "PASS":
        raise ValueError("Feature-configuration screening has not passed.")
    if screening.get("final_test_evaluated") is not False:
        raise ValueError("Screening result violated final-test sealing.")
    selected = screening.get("selected_feature_configuration")
    evidence = screening.get("selection_evidence", {})
    if selected != "lag_only_p168":
        raise ValueError(
            "Approved screening result must select lag_only_p168."
        )
    if evidence.get("selected_configuration") != selected:
        raise ValueError("Screening selection evidence is inconsistent.")
    final_test = result.get("final_test", {})
    if final_test.get("sealed") is not True:
        raise ValueError("Final test is not sealed in the screening result.")
    if final_test.get("metrics_computed") is not False:
        raise ValueError("Screening result contains final-test metrics.")
    return result


def validate_screening_inputs_are_current(
    entry_state: Phase05EntryState,
    screening_result: dict,
) -> dict:
    recorded = screening_result.get("input_identities", {})
    current = entry_state.audit["input_identities"]
    if set(recorded) != set(current):
        raise ValueError("Screening input identity registry is incomplete.")
    for name in current:
        if recorded[name].get("sha256") != current[name].get("sha256"):
            raise ValueError(
                f"Current Phase 5 input differs from screening: {name}."
            )
    return {
        "screening_inputs_match_current": True,
        "status": "PASS",
    }


def create_tuning_manifest(
    entry_state: Phase05EntryState,
    screening_result: dict,
) -> dict:
    validate_model_training_config(entry_state.model_config)
    validate_screening_inputs_are_current(entry_state, screening_result)
    selected = screening_result["screening_results"][
        "selected_feature_configuration"
    ]
    if selected not in entry_state.training_datasets:
        raise ValueError("Selected feature configuration is unavailable.")
    tuning_config = entry_state.model_config["tuning"]
    candidate_count = int(tuning_config["n_iter"])
    fold_count = len(entry_state.cv_fold_indices)
    return {
        "stage": "phase_05_xgboost_tuning",
        "selected_feature_configuration": selected,
        "train_rows": len(entry_state.training_datasets[selected].X),
        "feature_count": len(
            entry_state.training_datasets[selected].feature_names
        ),
        "search_method": tuning_config["search_method"],
        "candidate_count": candidate_count,
        "cv_fold_count": fold_count,
        "planned_model_fits": candidate_count * fold_count,
        "scoring": tuning_config["scoring"],
        "refit": tuning_config["refit"],
        "random_state": tuning_config["random_state"],
        "early_stopping": tuning_config["early_stopping"],
        "search_space": tuning_config["search_space"],
        "final_test_included": False,
        "requires_human_execution": True,
        "status": "READY",
    }


def create_xgboost_randomized_search(
    entry_state: Phase05EntryState,
    estimator_factory: Callable | None = None,
    search_factory: Callable | None = None,
):
    if estimator_factory is None:
        from xgboost import XGBRegressor

        estimator_factory = XGBRegressor
    if search_factory is None:
        from sklearn.model_selection import RandomizedSearchCV

        search_factory = RandomizedSearchCV

    tuning_config = entry_state.model_config["tuning"]
    estimator = estimator_factory(
        **entry_state.model_config["screening"]["parameters"]
    )
    cv = [
        (fold.train_indices, fold.validation_indices)
        for fold in entry_state.cv_fold_indices
    ]
    return search_factory(
        estimator=estimator,
        param_distributions=tuning_config["search_space"],
        n_iter=tuning_config["n_iter"],
        scoring=tuning_config["scoring"],
        refit=tuning_config["refit"],
        cv=cv,
        random_state=tuning_config["random_state"],
        error_score="raise",
        return_train_score=False,
    )


def build_tuning_candidates(
    search,
    entry_state: Phase05EntryState,
) -> list[dict]:
    cv_results = search.cv_results_
    candidate_count = len(cv_results["params"])
    expected_count = int(entry_state.model_config["tuning"]["n_iter"])
    if candidate_count != expected_count:
        raise ValueError("Tuning did not evaluate all approved candidates.")

    candidates = []
    ddof = int(
        entry_state.model_config["metrics"]["standard_deviation_ddof"]
    )
    for candidate_index in range(candidate_count):
        fold_metrics = []
        for fold_index, fold in enumerate(entry_state.cv_fold_indices):
            mae = -float(
                cv_results[f"split{fold_index}_test_mae"][candidate_index]
            )
            rmse = -float(
                cv_results[f"split{fold_index}_test_rmse"][candidate_index]
            )
            if not np.isfinite([mae, rmse]).all():
                raise ValueError("Tuning produced a non-finite fold metric.")
            fold_metrics.append(
                {
                    "fold": fold.fold,
                    "train_samples": len(fold.train_indices),
                    "validation_samples": len(fold.validation_indices),
                    "mae": mae,
                    "rmse": rmse,
                }
            )

        aggregate = summarize_fold_metrics(fold_metrics, ddof=ddof)
        reported_mean_mae = -float(
            cv_results["mean_test_mae"][candidate_index]
        )
        reported_mean_rmse = -float(
            cv_results["mean_test_rmse"][candidate_index]
        )
        if not np.isclose(aggregate["mean_mae"], reported_mean_mae):
            raise ValueError("Tuning MAE aggregate is inconsistent.")
        if not np.isclose(aggregate["mean_rmse"], reported_mean_rmse):
            raise ValueError("Tuning RMSE aggregate is inconsistent.")
        candidates.append(
            {
                "candidate_index": candidate_index,
                "parameters": json_safe(cv_results["params"][candidate_index]),
                "fold_metrics": fold_metrics,
                "aggregate": aggregate,
                "rank_mae": int(
                    cv_results["rank_test_mae"][candidate_index]
                ),
                "mean_fit_seconds": float(
                    cv_results["mean_fit_time"][candidate_index]
                ),
                "std_fit_seconds": float(
                    cv_results["std_fit_time"][candidate_index]
                ),
                "status": "PASS",
            }
        )
    return candidates


def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def build_tuning_result(
    search,
    entry_state: Phase05EntryState,
    screening_result: dict,
    run_id: str,
    execution_identity: str,
    screening_result_path: Path,
    training_seconds: float,
    warning_records: list[dict],
) -> dict:
    candidates = build_tuning_candidates(search, entry_state)
    best_index = int(search.best_index_)
    if best_index < 0 or best_index >= len(candidates):
        raise ValueError("Tuning best candidate index is invalid.")
    if candidates[best_index]["rank_mae"] != 1:
        raise ValueError("Tuning best candidate does not have MAE rank 1.")
    best_parameters = json_safe(search.best_params_)
    if best_parameters != candidates[best_index]["parameters"]:
        raise ValueError("Tuning best parameters are inconsistent.")
    base_parameters = dict(
        entry_state.model_config["screening"]["parameters"]
    )
    selected_full_parameters = {
        **base_parameters,
        **best_parameters,
    }

    return {
        "phase": "phase_05_xgboost_tuning",
        "run_id": run_id,
        "execution_identity": execution_identity,
        "selected_feature_configuration": "lag_only_p168",
        "manifest": create_tuning_manifest(
            entry_state,
            screening_result,
        ),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "selected_candidate": candidates[best_index],
        "base_parameters": base_parameters,
        "best_parameters": best_parameters,
        "selected_full_parameters": selected_full_parameters,
        "total_training_seconds": float(training_seconds),
        "warnings": warning_records,
        "screening_result": {
            "path": str(screening_result_path),
            "sha256": file_sha256(screening_result_path),
            "run_id": screening_result["run_id"],
        },
        "runtime": entry_state.audit["runtime"],
        "input_identities": entry_state.audit["input_identities"],
        "final_test": entry_state.final_test_metadata,
        "final_test_evaluated": False,
        "status": "PASS",
    }


def create_tuning_execution_identity(
    entry_state: Phase05EntryState,
    screening_result_path: Path,
) -> tuple[str, dict]:
    payload = {
        "stage": "phase_05_xgboost_tuning",
        "selected_feature_configuration": "lag_only_p168",
        "model_config": entry_state.model_config,
        "screening_result_sha256": file_sha256(screening_result_path),
        "input_sha256": {
            name: identity["sha256"]
            for name, identity in entry_state.audit["input_identities"].items()
        },
        "runtime": entry_state.audit["runtime"],
        "source_sha256": file_sha256(Path(__file__)),
        "final_test_state": entry_state.final_test_metadata,
    }
    return canonical_sha256(payload), payload


def run_phase_05_tuning(
    screening_result_path: Path = DEFAULT_SCREENING_OUTPUT,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    entry_state: Phase05EntryState | None = None,
    estimator_factory: Callable | None = None,
    search_factory: Callable | None = None,
    now: datetime | None = None,
) -> dict:
    current_entry_state = entry_state or validate_phase_05_entry()
    screening_result = load_screening_result(screening_result_path)
    manifest = create_tuning_manifest(
        current_entry_state,
        screening_result,
    )
    execution_identity, identity_payload = create_tuning_execution_identity(
        current_entry_state,
        screening_result_path,
    )
    run_id = create_tuning_run_id(execution_identity, now=now)
    run_dir = Path(runs_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    timestamp = utc_offset_timestamp(now)
    metadata = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "phase_05_xgboost_tuning",
        "status": "RUNNING",
        "created_at": timestamp,
        "updated_at": timestamp,
        "execution_identity": execution_identity,
        "execution_identity_payload": identity_payload,
        "manifest": manifest,
        "result": "tuning_results.json",
        "final_test_evaluated": False,
    }
    save_json_result(
        current_entry_state.model_config,
        run_dir / "config_snapshot.json",
    )
    save_json_result(manifest, run_dir / "tuning_manifest.json")
    save_json_result(metadata, run_dir / "run_metadata.json")
    logger = create_run_logger(run_dir, run_id)
    logger.info(
        "Tuning run started: %s candidates, %s folds, %s planned fits.",
        manifest["candidate_count"],
        manifest["cv_fold_count"],
        manifest["planned_model_fits"],
    )
    dataset = current_entry_state.training_datasets["lag_only_p168"]
    search = create_xgboost_randomized_search(
        current_entry_state,
        estimator_factory=estimator_factory,
        search_factory=search_factory,
    )
    start = perf_counter()
    try:
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            search.fit(dataset.X, dataset.y)
        training_seconds = perf_counter() - start
        warning_records = [
            {
                "category": warning.category.__name__,
                "message": str(warning.message),
            }
            for warning in caught_warnings
        ]
        result = build_tuning_result(
            search=search,
            entry_state=current_entry_state,
            screening_result=screening_result,
            run_id=run_id,
            execution_identity=execution_identity,
            screening_result_path=screening_result_path,
            training_seconds=training_seconds,
            warning_records=warning_records,
        )
        save_json_result(result, run_dir / "tuning_results.json")
        metadata["status"] = "COMPLETED"
        metadata["updated_at"] = utc_offset_timestamp()
        metadata["best_parameters"] = result["best_parameters"]
        metadata["warning_count"] = len(warning_records)
        save_json_result(metadata, run_dir / "run_metadata.json")
        logger.info(
            "Tuning completed in %.3fs with best mean MAE %.6f.",
            training_seconds,
            result["selected_candidate"]["aggregate"]["mean_mae"],
        )
        return {
            **result,
            "run_dir": str(run_dir),
        }
    except KeyboardInterrupt:
        metadata["status"] = "INTERRUPTED"
        metadata["updated_at"] = utc_offset_timestamp()
        metadata["failure"] = {
            "type": "KeyboardInterrupt",
            "message": (
                "Tuning was interrupted and must restart because the "
                "approved RandomizedSearchCV job has no fold-level resume."
            ),
        }
        save_json_result(metadata, run_dir / "run_metadata.json")
        logger.warning("Tuning interrupted; no tuning result was promoted.")
        return {
            "phase": "phase_05_xgboost_tuning",
            "run_id": run_id,
            "run_dir": str(run_dir),
            "final_test_evaluated": False,
            "status": "INTERRUPTED",
        }
    except Exception as exc:
        metadata["status"] = "FAILED"
        metadata["updated_at"] = utc_offset_timestamp()
        metadata["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        save_json_result(metadata, run_dir / "run_metadata.json")
        logger.exception("Tuning run failed.")
        raise
    finally:
        close_run_logger(logger)


def load_tuning_result(tuning_result_path: Path) -> dict:
    result = load_json_result(tuning_result_path)
    if result.get("phase") != "phase_05_xgboost_tuning":
        raise ValueError("Phase 5 tuning result has an invalid identity.")
    if result.get("status") != "PASS":
        raise ValueError("Phase 5 tuning result has not passed.")
    if result.get("selected_feature_configuration") != "lag_only_p168":
        raise ValueError("Tuning result has an invalid feature configuration.")
    if result.get("candidate_count") != 24:
        raise ValueError("Tuning result does not contain 24 candidates.")
    if result.get("final_test_evaluated") is not False:
        raise ValueError("Tuning result violated final-test sealing.")
    final_test = result.get("final_test", {})
    if final_test.get("sealed") is not True:
        raise ValueError("Final test is not sealed in the tuning result.")
    if final_test.get("metrics_computed") is not False:
        raise ValueError("Tuning result contains final-test metrics.")
    selected = result.get("selected_candidate", {})
    if selected.get("rank_mae") != 1:
        raise ValueError("Tuning result does not identify the MAE winner.")
    if not result.get("selected_full_parameters"):
        raise ValueError("Tuning result is missing reconstruction parameters.")
    return result


def validate_tuning_inputs_are_current(
    entry_state: Phase05EntryState,
    tuning_result: dict,
) -> dict:
    recorded = tuning_result.get("input_identities", {})
    current = entry_state.audit["input_identities"]
    if set(recorded) != set(current):
        raise ValueError("Tuning input identity registry is incomplete.")
    for name in current:
        if recorded[name].get("sha256") != current[name].get("sha256"):
            raise ValueError(
                f"Current Phase 5 input differs from tuning: {name}."
            )
    return {"tuning_inputs_match_current": True, "status": "PASS"}


def create_random_forest_manifest(
    entry_state: Phase05EntryState,
    tuning_result: dict,
) -> dict:
    validate_model_training_config(entry_state.model_config)
    validate_tuning_inputs_are_current(entry_state, tuning_result)
    selected = tuning_result["selected_feature_configuration"]
    dataset = entry_state.training_datasets[selected]
    fold_count = len(entry_state.cv_fold_indices)
    return {
        "stage": "phase_05_random_forest_comparison",
        "model": "random_forest",
        "selected_feature_configuration": selected,
        "train_rows": len(dataset.X),
        "feature_count": len(dataset.feature_names),
        "cv_fold_count": fold_count,
        "planned_model_fits": fold_count,
        "parameters": entry_state.model_config["random_forest"][
            "parameters"
        ],
        "metrics": entry_state.model_config["metrics"],
        "checkpoint_unit": "cv_fold",
        "resume_supported": True,
        "final_test_included": False,
        "requires_human_execution": True,
        "status": "READY",
    }


def create_random_forest_execution_identity(
    entry_state: Phase05EntryState,
    tuning_result_path: Path,
) -> tuple[str, dict]:
    payload = {
        "stage": "phase_05_random_forest_comparison",
        "selected_feature_configuration": "lag_only_p168",
        "parameters": entry_state.model_config["random_forest"][
            "parameters"
        ],
        "tuning_result_sha256": file_sha256(tuning_result_path),
        "input_sha256": {
            name: identity["sha256"]
            for name, identity in entry_state.audit[
                "input_identities"
            ].items()
        },
        "runtime": entry_state.audit["runtime"],
        "folds": [
            {
                "fold": fold.fold,
                "train_start_index": int(fold.train_indices[0]),
                "train_end_index": int(fold.train_indices[-1]),
                "validation_start_index": int(
                    fold.validation_indices[0]
                ),
                "validation_end_index": int(
                    fold.validation_indices[-1]
                ),
            }
            for fold in entry_state.cv_fold_indices
        ],
        "source_sha256": file_sha256(Path(__file__)),
        "final_test_state": entry_state.final_test_metadata,
    }
    return canonical_sha256(payload), payload


def create_random_forest_checkpoint(
    entry_state: Phase05EntryState,
    run_id: str,
    execution_identity: str,
    created_at: str,
) -> dict:
    folds = [fold.fold for fold in entry_state.cv_fold_indices]
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "phase_05_random_forest_comparison",
        "status": "READY",
        "created_at": created_at,
        "updated_at": created_at,
        "execution_identity": execution_identity,
        "selected_feature_configuration": "lag_only_p168",
        "folds": folds,
        "total_fold_count": len(folds),
        "completed_fold_count": 0,
        "current": None,
        "fold_status": {str(fold): "PENDING" for fold in folds},
        "fold_results": {},
        "failure": None,
        "final_test_evaluated": False,
    }


def initialize_random_forest_run(
    entry_state: Phase05EntryState,
    tuning_result_path: Path,
    tuning_result: dict,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    now: datetime | None = None,
) -> tuple[Path, dict, dict]:
    execution_identity, identity_payload = (
        create_random_forest_execution_identity(
            entry_state,
            tuning_result_path,
        )
    )
    run_id = create_random_forest_run_id(
        execution_identity,
        now=now,
    )
    run_dir = Path(runs_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    created_at = utc_offset_timestamp(now)
    checkpoint = create_random_forest_checkpoint(
        entry_state,
        run_id,
        execution_identity,
        created_at,
    )
    metadata = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "phase_05_random_forest_comparison",
        "status": "READY",
        "created_at": created_at,
        "updated_at": created_at,
        "execution_identity": execution_identity,
        "execution_identity_payload": identity_payload,
        "manifest": create_random_forest_manifest(
            entry_state,
            tuning_result,
        ),
        "tuning_result": {
            "path": str(tuning_result_path),
            "sha256": file_sha256(tuning_result_path),
            "run_id": tuning_result["run_id"],
        },
        "completed_fold_count": 0,
        "artifacts": {
            "log": f"{run_id}.log",
            "metadata": "run_metadata.json",
            "config_snapshot": "config_snapshot.json",
            "manifest": "random_forest_manifest.json",
            "checkpoint": "checkpoint.json",
            "result": "random_forest_results.json",
        },
        "final_test_evaluated": False,
    }
    save_json_result(
        entry_state.model_config,
        run_dir / "config_snapshot.json",
    )
    save_json_result(
        metadata["manifest"],
        run_dir / "random_forest_manifest.json",
    )
    write_run_state(run_dir, checkpoint, metadata, None)
    return run_dir, checkpoint, metadata


def load_resumable_random_forest_run(
    entry_state: Phase05EntryState,
    tuning_result_path: Path,
    run_dir: Path,
) -> tuple[dict, dict]:
    run_dir = Path(run_dir)
    checkpoint = load_json_result(run_dir / "checkpoint.json")
    metadata = load_json_result(run_dir / "run_metadata.json")
    config_snapshot = load_json_result(run_dir / "config_snapshot.json")
    if checkpoint.get("schema_version") != RUN_SCHEMA_VERSION:
        raise ValueError("Random Forest checkpoint schema is invalid.")
    if metadata.get("schema_version") != RUN_SCHEMA_VERSION:
        raise ValueError("Random Forest metadata schema is invalid.")
    if checkpoint.get("run_id") != run_dir.name:
        raise ValueError("Random Forest checkpoint run ID is invalid.")
    if metadata.get("run_id") != run_dir.name:
        raise ValueError("Random Forest metadata run ID is invalid.")
    if config_snapshot != entry_state.model_config:
        raise ValueError("Random Forest config snapshot has changed.")
    execution_identity, identity_payload = (
        create_random_forest_execution_identity(
            entry_state,
            tuning_result_path,
        )
    )
    if checkpoint.get("execution_identity") != execution_identity:
        raise ValueError("Random Forest inputs or source no longer match.")
    if metadata.get("execution_identity") != execution_identity:
        raise ValueError("Random Forest metadata identity no longer matches.")
    if metadata.get("execution_identity_payload") != identity_payload:
        raise ValueError("Random Forest identity payload is inconsistent.")
    if checkpoint.get("status") == "COMPLETED":
        raise ValueError("The requested Random Forest run is completed.")
    if checkpoint.get("status") not in {
        "READY",
        "RUNNING",
        "INTERRUPTED",
        "FAILED",
    }:
        raise ValueError("The requested Random Forest run is not resumable.")
    return checkpoint, metadata


def reset_incomplete_random_forest_fold(checkpoint: dict) -> None:
    for fold in checkpoint["folds"]:
        key = str(fold)
        if checkpoint["fold_status"][key] != "PASS":
            checkpoint["fold_status"][key] = "PENDING"
    checkpoint["current"] = None
    checkpoint["failure"] = None


def build_random_forest_result(
    entry_state: Phase05EntryState,
    checkpoint: dict,
    tuning_result_path: Path,
    tuning_result: dict,
) -> dict:
    fold_metrics = [
        checkpoint["fold_results"][str(fold)]
        for fold in checkpoint["folds"]
    ]
    ddof = int(
        entry_state.model_config["metrics"]["standard_deviation_ddof"]
    )
    aggregate = summarize_fold_metrics(fold_metrics, ddof=ddof)
    aggregate["total_training_seconds"] = float(
        sum(item["training_seconds"] for item in fold_metrics)
    )
    return {
        "phase": "phase_05_random_forest_comparison",
        "run_id": checkpoint["run_id"],
        "execution_identity": checkpoint["execution_identity"],
        "selected_feature_configuration": "lag_only_p168",
        "parameters": entry_state.model_config["random_forest"][
            "parameters"
        ],
        "fold_metrics": fold_metrics,
        "aggregate": aggregate,
        "tuning_result": {
            "path": str(tuning_result_path),
            "sha256": file_sha256(tuning_result_path),
            "run_id": tuning_result["run_id"],
        },
        "runtime": entry_state.audit["runtime"],
        "input_identities": entry_state.audit["input_identities"],
        "final_test": entry_state.final_test_metadata,
        "final_test_evaluated": False,
        "status": "PASS",
    }


def execute_random_forest_run(
    entry_state: Phase05EntryState,
    tuning_result_path: Path,
    tuning_result: dict,
    run_dir: Path,
    checkpoint: dict,
    metadata: dict,
    estimator_factory: Callable | None = None,
) -> dict:
    if estimator_factory is None:
        from sklearn.ensemble import RandomForestRegressor

        estimator_factory = RandomForestRegressor
    run_dir = Path(run_dir)
    logger = create_run_logger(run_dir, checkpoint["run_id"])
    reset_incomplete_random_forest_fold(checkpoint)
    checkpoint["status"] = "RUNNING"
    write_run_state(run_dir, checkpoint, metadata, None)
    dataset = entry_state.training_datasets["lag_only_p168"]
    parameters = entry_state.model_config["random_forest"]["parameters"]
    try:
        for fold in entry_state.cv_fold_indices:
            fold_key = str(fold.fold)
            if checkpoint["fold_status"][fold_key] == "PASS":
                logger.info(
                    "Random Forest fold %s skipped because checkpoint is PASS.",
                    fold.fold,
                )
                continue
            checkpoint["current"] = {"fold": fold.fold}
            checkpoint["fold_status"][fold_key] = "RUNNING"
            write_run_state(run_dir, checkpoint, metadata, None)
            logger.info(
                "Random Forest fold %s/%s started.",
                fold.fold,
                len(entry_state.cv_fold_indices),
            )
            one_fold_result = evaluate_cv_estimator_configuration(
                configuration_name="lag_only_p168",
                dataset=dataset,
                cv_fold_indices=(fold,),
                parameters=parameters,
                estimator_factory=estimator_factory,
            )
            fold_result = one_fold_result["fold_metrics"][0]
            checkpoint["fold_results"][fold_key] = fold_result
            checkpoint["fold_status"][fold_key] = "PASS"
            checkpoint["completed_fold_count"] = sum(
                status == "PASS"
                for status in checkpoint["fold_status"].values()
            )
            checkpoint["current"] = None
            write_run_state(run_dir, checkpoint, metadata, None)
            logger.info(
                "Random Forest fold %s completed: MAE=%.6f RMSE=%.6f time=%.3fs.",
                fold.fold,
                fold_result["mae"],
                fold_result["rmse"],
                fold_result["training_seconds"],
            )
        if checkpoint["completed_fold_count"] != checkpoint[
            "total_fold_count"
        ]:
            raise RuntimeError(
                "Random Forest ended without completing all folds."
            )
        result = build_random_forest_result(
            entry_state,
            checkpoint,
            tuning_result_path,
            tuning_result,
        )
        save_json_result(
            result,
            run_dir / "random_forest_results.json",
        )
        checkpoint["status"] = "COMPLETED"
        checkpoint["current"] = None
        checkpoint["failure"] = None
        write_run_state(run_dir, checkpoint, metadata, None)
        logger.info("Random Forest comparison completed.")
        return {**result, "run_dir": str(run_dir)}
    except KeyboardInterrupt:
        current = checkpoint.get("current")
        if current is not None:
            checkpoint["fold_status"][str(current["fold"])] = (
                "INTERRUPTED"
            )
        checkpoint["status"] = "INTERRUPTED"
        checkpoint["failure"] = {
            "type": "KeyboardInterrupt",
            "message": "Random Forest training was interrupted by the Human.",
        }
        write_run_state(run_dir, checkpoint, metadata, None)
        logger.warning(
            "Random Forest interrupted after %s/%s folds.",
            checkpoint["completed_fold_count"],
            checkpoint["total_fold_count"],
        )
        return {
            "phase": "phase_05_random_forest_comparison",
            "run_id": checkpoint["run_id"],
            "run_dir": str(run_dir),
            "completed_fold_count": checkpoint["completed_fold_count"],
            "total_fold_count": checkpoint["total_fold_count"],
            "final_test_evaluated": False,
            "status": "INTERRUPTED",
        }
    except Exception as exc:
        current = checkpoint.get("current")
        if current is not None:
            checkpoint["fold_status"][str(current["fold"])] = "FAILED"
        checkpoint["status"] = "FAILED"
        checkpoint["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        write_run_state(run_dir, checkpoint, metadata, None)
        logger.exception("Random Forest comparison failed.")
        raise
    finally:
        close_run_logger(logger)


def run_phase_05_random_forest(
    tuning_result_path: Path,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    resume_run_dir: Path | None = None,
    entry_state: Phase05EntryState | None = None,
    estimator_factory: Callable | None = None,
    now: datetime | None = None,
) -> dict:
    current_entry_state = entry_state or validate_phase_05_entry()
    tuning_result = load_tuning_result(tuning_result_path)
    create_random_forest_manifest(current_entry_state, tuning_result)
    if resume_run_dir is None:
        run_dir, checkpoint, metadata = initialize_random_forest_run(
            current_entry_state,
            tuning_result_path,
            tuning_result,
            runs_dir=runs_dir,
            now=now,
        )
    else:
        run_dir = Path(resume_run_dir)
        checkpoint, metadata = load_resumable_random_forest_run(
            current_entry_state,
            tuning_result_path,
            run_dir,
        )
    return execute_random_forest_run(
        entry_state=current_entry_state,
        tuning_result_path=tuning_result_path,
        tuning_result=tuning_result,
        run_dir=run_dir,
        checkpoint=checkpoint,
        metadata=metadata,
        estimator_factory=estimator_factory,
    )


def load_random_forest_result(random_forest_result_path: Path) -> dict:
    result = load_json_result(random_forest_result_path)
    if result.get("phase") != "phase_05_random_forest_comparison":
        raise ValueError("Random Forest result has an invalid identity.")
    if result.get("status") != "PASS":
        raise ValueError("Random Forest result has not passed.")
    if result.get("selected_feature_configuration") != "lag_only_p168":
        raise ValueError("Random Forest feature configuration is invalid.")
    if len(result.get("fold_metrics", [])) != 5:
        raise ValueError("Random Forest result does not contain five folds.")
    if result.get("final_test_evaluated") is not False:
        raise ValueError("Random Forest result violated final-test sealing.")
    final_test = result.get("final_test", {})
    if final_test.get("sealed") is not True:
        raise ValueError("Final test is not sealed in Random Forest result.")
    if final_test.get("metrics_computed") is not False:
        raise ValueError("Random Forest result contains final-test metrics.")
    return result


def validate_random_forest_result_is_current(
    entry_state: Phase05EntryState,
    tuning_result_path: Path,
    random_forest_result: dict,
) -> dict:
    if random_forest_result.get("parameters") != entry_state.model_config[
        "random_forest"
    ]["parameters"]:
        raise ValueError("Random Forest parameters differ from approved config.")
    recorded = random_forest_result.get("input_identities", {})
    current = entry_state.audit["input_identities"]
    if set(recorded) != set(current):
        raise ValueError("Random Forest input identities are incomplete.")
    for name in current:
        if recorded[name].get("sha256") != current[name].get("sha256"):
            raise ValueError(
                f"Current Phase 5 input differs from Random Forest: {name}."
            )
    tuning_identity = random_forest_result.get("tuning_result", {})
    if tuning_identity.get("sha256") != file_sha256(tuning_result_path):
        raise ValueError("Random Forest tuning-result identity is stale.")
    return {
        "random_forest_inputs_match_current": True,
        "tuning_result_identity_matches": True,
        "status": "PASS",
    }


def build_model_comparison(
    entry_state: Phase05EntryState,
    screening_result: dict,
    tuning_result: dict,
    random_forest_result: dict,
) -> dict:
    selected_feature = screening_result["screening_results"][
        "selected_feature_configuration"
    ]
    if selected_feature != "lag_only_p168":
        raise ValueError("Model comparison feature configuration is invalid.")
    baseline_results = screening_result["baseline_results"]["baselines"]
    screening_configuration = screening_result["screening_results"][
        "configurations"
    ][selected_feature]
    candidates = {
        "seasonal_naive_24": {
            "model": "seasonal_naive_24",
            "feature_configuration": selected_feature,
            "parameters": {
                "lag": baseline_results["seasonal_naive_24"]["lag"]
            },
            "fold_metrics": baseline_results["seasonal_naive_24"][
                "fold_metrics"
            ],
            "aggregate": baseline_results["seasonal_naive_24"][
                "aggregate"
            ],
            "status": "PASS",
        },
        "persistence": {
            "model": "persistence",
            "feature_configuration": selected_feature,
            "parameters": {
                "lag": baseline_results["persistence"]["lag"]
            },
            "fold_metrics": baseline_results["persistence"][
                "fold_metrics"
            ],
            "aggregate": baseline_results["persistence"]["aggregate"],
            "status": "PASS",
        },
        "xgboost_baseline": {
            "model": "xgboost_baseline",
            "feature_configuration": selected_feature,
            "parameters": screening_configuration["parameters"],
            "fold_metrics": screening_configuration["fold_metrics"],
            "aggregate": screening_configuration["aggregate"],
            "status": "PASS",
        },
        "xgboost_tuned": {
            "model": "xgboost_tuned",
            "feature_configuration": selected_feature,
            "parameters": tuning_result["selected_full_parameters"],
            "fold_metrics": tuning_result["selected_candidate"][
                "fold_metrics"
            ],
            "aggregate": tuning_result["selected_candidate"][
                "aggregate"
            ],
            "status": "PASS",
        },
        "random_forest": {
            "model": "random_forest",
            "feature_configuration": selected_feature,
            "parameters": random_forest_result["parameters"],
            "fold_metrics": random_forest_result["fold_metrics"],
            "aggregate": random_forest_result["aggregate"],
            "status": "PASS",
        },
    }
    candidate_order = entry_state.model_config["model_lock"][
        "candidate_order"
    ]
    if tuple(candidates) != tuple(candidate_order):
        raise ValueError("Model comparison candidate order is invalid.")
    for name, candidate in candidates.items():
        aggregate = candidate["aggregate"]
        metrics = [
            aggregate["mean_mae"],
            aggregate["std_mae"],
            aggregate["mean_rmse"],
            aggregate["std_rmse"],
        ]
        if not np.isfinite(metrics).all():
            raise ValueError(f"Non-finite comparison metric found: {name}")
        if len(candidate["fold_metrics"]) != len(
            entry_state.cv_fold_indices
        ):
            raise ValueError(f"Model comparison fold count is invalid: {name}")
        for actual, expected in zip(
            candidate["fold_metrics"],
            entry_state.cv_fold_indices,
        ):
            if actual.get("fold") != expected.fold:
                raise ValueError(
                    f"Model comparison fold identity is invalid: {name}"
                )
            validation_samples = actual.get(
                "validation_samples",
                actual.get("samples"),
            )
            if validation_samples != len(expected.validation_indices):
                raise ValueError(
                    f"Model comparison population is invalid: {name}"
                )
    return {
        "selected_feature_configuration": selected_feature,
        "candidate_order": candidate_order,
        "candidates": candidates,
        "metric_definitions": entry_state.model_config["metrics"],
        "forecast_protocol": entry_state.model_config["forecast_protocol"],
        "final_test_evaluated": False,
        "status": "PASS",
    }


def select_model_candidate(
    model_comparison: dict,
    model_config: dict,
) -> tuple[str, dict]:
    candidates = model_comparison["candidates"]
    candidate_order = model_config["model_lock"]["candidate_order"]
    simplicity_order = model_config["model_lock"]["simplicity_order"]
    if tuple(candidates) != tuple(candidate_order):
        raise ValueError("Model-selection candidate registry is invalid.")
    best_mean_mae = min(
        candidate["aggregate"]["mean_mae"]
        for candidate in candidates.values()
    )
    tolerance = float(
        model_config["model_lock"]["relative_mae_tolerance"]
    )
    mae_threshold = best_mean_mae * (1.0 + tolerance)
    tolerance_candidates = [
        name
        for name in candidate_order
        if candidates[name]["aggregate"]["mean_mae"] <= mae_threshold
    ]
    simplicity_rank = {
        name: rank for rank, name in enumerate(simplicity_order)
    }
    selected = min(
        tolerance_candidates,
        key=lambda name: (
            simplicity_rank[name],
            candidates[name]["aggregate"]["mean_rmse"],
            candidates[name]["aggregate"]["std_mae"],
            candidate_order.index(name),
        ),
    )
    evidence = {
        "best_mean_mae": float(best_mean_mae),
        "relative_mae_tolerance": tolerance,
        "mae_threshold": float(mae_threshold),
        "tolerance_candidates": tolerance_candidates,
        "simplicity_order": simplicity_order,
        "selected_candidate": selected,
        "selected_mean_mae": float(
            candidates[selected]["aggregate"]["mean_mae"]
        ),
        "selected_mean_rmse": float(
            candidates[selected]["aggregate"]["mean_rmse"]
        ),
        "status": "PASS",
    }
    return selected, evidence


def create_model_lock_manifest(
    entry_state: Phase05EntryState,
    model_comparison: dict,
) -> dict:
    selected, evidence = select_model_candidate(
        model_comparison,
        entry_state.model_config,
    )
    return {
        "stage": "phase_05_model_comparison_and_lock",
        "candidate_count": len(model_comparison["candidates"]),
        "candidate_order": model_comparison["candidate_order"],
        "selected_feature_configuration": model_comparison[
            "selected_feature_configuration"
        ],
        "cv_selected_candidate": selected,
        "selection_evidence": evidence,
        "full_train_refit_required": selected in {
            "xgboost_baseline",
            "xgboost_tuned",
            "random_forest",
        },
        "full_train_rows": len(
            entry_state.training_datasets["lag_only_p168"].X
        ),
        "prediction_required": False,
        "persist_binary_model": False,
        "final_test_included": False,
        "requires_human_execution": True,
        "status": "READY",
    }


def create_model_lock_execution_identity(
    entry_state: Phase05EntryState,
    screening_result_path: Path,
    tuning_result_path: Path,
    random_forest_result_path: Path,
) -> tuple[str, dict]:
    payload = {
        "stage": "phase_05_model_comparison_and_lock",
        "artifact_sha256": {
            "screening": file_sha256(screening_result_path),
            "tuning": file_sha256(tuning_result_path),
            "random_forest": file_sha256(random_forest_result_path),
        },
        "model_config": entry_state.model_config,
        "input_sha256": {
            name: identity["sha256"]
            for name, identity in entry_state.audit[
                "input_identities"
            ].items()
        },
        "runtime": entry_state.audit["runtime"],
        "source_sha256": file_sha256(Path(__file__)),
        "final_test_state": entry_state.final_test_metadata,
    }
    return canonical_sha256(payload), payload


def build_phase_05_cv_result(
    entry_state: Phase05EntryState,
    model_comparison: dict,
    artifact_paths: dict[str, Path],
) -> dict:
    return {
        "phase": "phase_05_model_training_selection",
        "selected_feature_configuration": model_comparison[
            "selected_feature_configuration"
        ],
        "candidate_order": model_comparison["candidate_order"],
        "candidates": model_comparison["candidates"],
        "metric_definitions": model_comparison["metric_definitions"],
        "forecast_protocol": model_comparison["forecast_protocol"],
        "source_artifacts": {
            name: {
                "path": str(path),
                "sha256": file_sha256(path),
            }
            for name, path in artifact_paths.items()
        },
        "runtime": entry_state.audit["runtime"],
        "input_identities": entry_state.audit["input_identities"],
        "final_test": entry_state.final_test_metadata,
        "final_test_evaluated": False,
        "status": "PASS",
    }


def build_phase_05_model_lock(
    entry_state: Phase05EntryState,
    model_comparison: dict,
    refit_evidence: dict,
    cv_result_path: Path,
    cv_result_sha256: str,
) -> dict:
    selected, evidence = select_model_candidate(
        model_comparison,
        entry_state.model_config,
    )
    locked_candidates = {
        name: {
            "model": candidate["model"],
            "feature_configuration": candidate["feature_configuration"],
            "parameters": candidate["parameters"],
            "aggregate": candidate["aggregate"],
        }
        for name, candidate in model_comparison["candidates"].items()
    }
    return {
        "phase": "phase_05_model_lock",
        "selected_feature_configuration": model_comparison[
            "selected_feature_configuration"
        ],
        "locked_candidates": locked_candidates,
        "candidate_order": model_comparison["candidate_order"],
        "cv_selected_candidate": selected,
        "selection_evidence": evidence,
        "selected_candidate_refit": refit_evidence,
        "forecast_protocol": model_comparison["forecast_protocol"],
        "metric_definitions": model_comparison["metric_definitions"],
        "cv_results": {
            "path": str(cv_result_path),
            "sha256": cv_result_sha256,
        },
        "runtime": entry_state.audit["runtime"],
        "input_identities": entry_state.audit["input_identities"],
        "final_test": entry_state.final_test_metadata,
        "final_test_evaluated": False,
        "status": "PASS",
    }


def run_phase_05_model_lock(
    screening_result_path: Path,
    tuning_result_path: Path,
    random_forest_result_path: Path,
    cv_result_output_path: Path = DEFAULT_CV_RESULTS_OUTPUT,
    model_lock_output_path: Path = DEFAULT_MODEL_LOCK_OUTPUT,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    entry_state: Phase05EntryState | None = None,
    estimator_factories: dict[str, Callable] | None = None,
    now: datetime | None = None,
) -> dict:
    current_entry_state = entry_state or validate_phase_05_entry()
    screening_result = load_screening_result(screening_result_path)
    validate_screening_inputs_are_current(
        current_entry_state,
        screening_result,
    )
    tuning_result = load_tuning_result(tuning_result_path)
    validate_tuning_inputs_are_current(current_entry_state, tuning_result)
    random_forest_result = load_random_forest_result(
        random_forest_result_path
    )
    validate_random_forest_result_is_current(
        current_entry_state,
        tuning_result_path,
        random_forest_result,
    )
    comparison = build_model_comparison(
        current_entry_state,
        screening_result,
        tuning_result,
        random_forest_result,
    )
    manifest = create_model_lock_manifest(
        current_entry_state,
        comparison,
    )
    execution_identity, identity_payload = (
        create_model_lock_execution_identity(
            current_entry_state,
            screening_result_path,
            tuning_result_path,
            random_forest_result_path,
        )
    )
    run_id = create_model_lock_run_id(execution_identity, now=now)
    run_dir = Path(runs_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    timestamp = utc_offset_timestamp(now)
    metadata = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "phase_05_model_comparison_and_lock",
        "status": "RUNNING",
        "created_at": timestamp,
        "updated_at": timestamp,
        "execution_identity": execution_identity,
        "execution_identity_payload": identity_payload,
        "manifest": manifest,
        "final_test_evaluated": False,
    }
    save_json_result(
        current_entry_state.model_config,
        run_dir / "config_snapshot.json",
    )
    save_json_result(manifest, run_dir / "model_lock_manifest.json")
    save_json_result(metadata, run_dir / "run_metadata.json")
    logger = create_run_logger(run_dir, run_id)
    selected = manifest["cv_selected_candidate"]
    try:
        if manifest["full_train_refit_required"]:
            factories = estimator_factories or {}
            estimator_factory = factories.get(selected)
            if estimator_factory is None:
                if selected in {"xgboost_baseline", "xgboost_tuned"}:
                    from xgboost import XGBRegressor

                    estimator_factory = XGBRegressor
                elif selected == "random_forest":
                    from sklearn.ensemble import RandomForestRegressor

                    estimator_factory = RandomForestRegressor
            dataset = current_entry_state.training_datasets[
                "lag_only_p168"
            ]
            parameters = comparison["candidates"][selected]["parameters"]
            estimator = estimator_factory(**parameters)
            refit_start = perf_counter()
            with warnings.catch_warnings(record=True) as caught_warnings:
                warnings.simplefilter("always")
                estimator.fit(dataset.X, dataset.y)
            refit_seconds = perf_counter() - refit_start
            warning_records = [
                {
                    "category": warning.category.__name__,
                    "message": str(warning.message),
                }
                for warning in caught_warnings
            ]
            refit_evidence = {
                "candidate": selected,
                "train_rows": len(dataset.X),
                "feature_count": len(dataset.feature_names),
                "training_seconds": float(refit_seconds),
                "warnings": warning_records,
                "prediction_executed": False,
                "binary_model_persisted": False,
                "status": "PASS",
            }
        else:
            refit_evidence = {
                "candidate": selected,
                "required": False,
                "prediction_executed": False,
                "binary_model_persisted": False,
                "status": "NOT_REQUIRED",
            }
        artifact_paths = {
            "screening": Path(screening_result_path),
            "tuning": Path(tuning_result_path),
            "random_forest": Path(random_forest_result_path),
        }
        cv_result = build_phase_05_cv_result(
            current_entry_state,
            comparison,
            artifact_paths,
        )
        cv_result["run_id"] = run_id
        cv_result["execution_identity"] = execution_identity
        run_cv_result_path = run_dir / "phase_05_cv_results.json"
        save_json_result(cv_result, run_cv_result_path)
        model_lock = build_phase_05_model_lock(
            current_entry_state,
            comparison,
            refit_evidence,
            cv_result_output_path,
            file_sha256(run_cv_result_path),
        )
        model_lock["run_id"] = run_id
        model_lock["execution_identity"] = execution_identity
        save_json_result(model_lock, run_dir / "phase_05_model_lock.json")
        save_json_result(cv_result, cv_result_output_path)
        save_json_result(model_lock, model_lock_output_path)
        metadata["status"] = "COMPLETED"
        metadata["updated_at"] = utc_offset_timestamp()
        metadata["cv_result_output"] = str(cv_result_output_path)
        metadata["model_lock_output"] = str(model_lock_output_path)
        metadata["refit_evidence"] = refit_evidence
        save_json_result(metadata, run_dir / "run_metadata.json")
        logger.info(
            "Model lock completed. CV-selected candidate: %s.",
            selected,
        )
        return {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "cv_results": cv_result,
            "model_lock": model_lock,
            "final_test_evaluated": False,
            "status": "PASS",
        }
    except KeyboardInterrupt:
        metadata["status"] = "INTERRUPTED"
        metadata["updated_at"] = utc_offset_timestamp()
        metadata["failure"] = {
            "type": "KeyboardInterrupt",
            "message": "Full-TRAIN refit was interrupted by the Human.",
        }
        save_json_result(metadata, run_dir / "run_metadata.json")
        logger.warning("Model-lock refit interrupted; no lock promoted.")
        return {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "final_test_evaluated": False,
            "status": "INTERRUPTED",
        }
    except Exception as exc:
        metadata["status"] = "FAILED"
        metadata["updated_at"] = utc_offset_timestamp()
        metadata["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        save_json_result(metadata, run_dir / "run_metadata.json")
        logger.exception("Model-lock execution failed.")
        raise
    finally:
        close_run_logger(logger)


def calculate_regression_metrics(
    actual: pd.Series | np.ndarray,
    predicted: pd.Series | np.ndarray,
) -> dict:
    actual_values = np.asarray(actual, dtype=np.float64)
    predicted_values = np.asarray(predicted, dtype=np.float64)

    if actual_values.ndim != 1 or predicted_values.ndim != 1:
        raise ValueError("Metric inputs must be one-dimensional.")
    if len(actual_values) != len(predicted_values):
        raise ValueError("Actual and predicted values have different lengths.")
    if len(actual_values) == 0:
        raise ValueError("Metric inputs must not be empty.")
    if not np.isfinite(actual_values).all():
        raise ValueError("Actual values contain non-finite values.")
    if not np.isfinite(predicted_values).all():
        raise ValueError("Predicted values contain non-finite values.")

    errors = actual_values - predicted_values
    return {
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(np.square(errors)))),
    }


def build_baseline_predictions(
    dataset: TrainingDataset,
    validation_indices: np.ndarray,
    lag: int,
) -> pd.Series:
    if lag <= 0:
        raise ValueError("Baseline lag must be a positive integer.")

    feature_name = f"lag_{lag}"
    if feature_name not in dataset.X.columns:
        raise ValueError(
            f"Required baseline feature is missing: {feature_name}"
        )

    indices = np.asarray(validation_indices, dtype=np.int64)
    if indices.ndim != 1 or len(indices) == 0:
        raise ValueError("Validation indices must be a non-empty vector.")
    if indices.min() < 0 or indices.max() >= len(dataset.X):
        raise ValueError("Validation indices are outside TRAIN boundaries.")
    if not np.all(np.diff(indices) > 0):
        raise ValueError("Validation indices are not strictly increasing.")

    predictions = dataset.X.iloc[indices][feature_name].copy()
    expected_index = dataset.timestamp_index[indices]
    if not predictions.index.equals(expected_index):
        raise ValueError("Baseline predictions are timestamp-misaligned.")
    if not np.isfinite(predictions.to_numpy()).all():
        raise ValueError("Baseline predictions contain non-finite values.")

    predictions.name = "prediction"
    return predictions


def summarize_fold_metrics(
    fold_metrics: list[dict],
    ddof: int,
) -> dict:
    if not fold_metrics:
        raise ValueError("At least one fold metric is required.")
    if ddof < 0 or ddof >= len(fold_metrics):
        raise ValueError("Metric standard-deviation ddof is invalid.")

    mae_values = np.asarray(
        [fold["mae"] for fold in fold_metrics],
        dtype=np.float64,
    )
    rmse_values = np.asarray(
        [fold["rmse"] for fold in fold_metrics],
        dtype=np.float64,
    )
    return {
        "fold_count": len(fold_metrics),
        "mean_mae": float(np.mean(mae_values)),
        "std_mae": float(np.std(mae_values, ddof=ddof)),
        "mean_rmse": float(np.mean(rmse_values)),
        "std_rmse": float(np.std(rmse_values, ddof=ddof)),
        "standard_deviation_ddof": ddof,
    }


def evaluate_forecasting_baselines(
    entry_state: Phase05EntryState,
) -> dict:
    config = entry_state.model_config
    validate_model_training_config(config)
    reference_name = EXPECTED_CONFIGURATION_NAMES[0]
    reference = entry_state.training_datasets[reference_name]
    ddof = int(config["metrics"]["standard_deviation_ddof"])
    baseline_results = {}

    for baseline_name, baseline_config in config["baselines"].items():
        lag = int(baseline_config["lag"])
        fold_results = []

        for fold in entry_state.cv_fold_indices:
            if fold.train_indices[-1] >= fold.validation_indices[0]:
                raise ValueError(
                    f"CV fold {fold.fold} violates chronological order."
                )

            predictions = build_baseline_predictions(
                reference,
                fold.validation_indices,
                lag,
            )
            actual = reference.y.iloc[fold.validation_indices]
            if not actual.index.equals(predictions.index):
                raise ValueError(
                    f"Baseline alignment failed in fold {fold.fold}."
                )

            metrics = calculate_regression_metrics(actual, predictions)
            fold_results.append(
                {
                    "fold": fold.fold,
                    "samples": len(actual),
                    "validation_start": str(actual.index[0]),
                    "validation_end": str(actual.index[-1]),
                    **metrics,
                }
            )

        baseline_results[baseline_name] = {
            "lag": lag,
            "prediction_source": f"lag_{lag}",
            "fold_metrics": fold_results,
            "aggregate": summarize_fold_metrics(fold_results, ddof),
            "status": "PASS",
        }

    return {
        "protocol": config["forecast_protocol"]["mode"],
        "evaluation_population": "phase_04_shared_cv_validation_folds",
        "reference_configuration": reference_name,
        "metric_definitions": {
            "primary": config["metrics"]["primary"],
            "secondary": config["metrics"]["secondary"],
            "standard_deviation_ddof": ddof,
        },
        "baselines": baseline_results,
        "final_test_evaluated": False,
        "baseline_evaluation_executed": True,
        "training_executed": False,
        "status": "PASS",
    }


def validate_model_training_config(config: dict) -> dict:
    if config != APPROVED_MODEL_TRAINING_CONFIG:
        raise ValueError(
            "Phase 5 model-training configuration does not match the "
            "approved contract.\n"
            f"Expected: {APPROVED_MODEL_TRAINING_CONFIG}\n"
            f"Actual:   {config}"
        )

    return {
        "approved_contract": True,
        "status": "PASS",
    }


def load_model_training_config(
    config_path: Path = Path("config/model_training.json"),
) -> dict:
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Phase 5 model-training configuration not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    validate_model_training_config(config)
    return config


def file_sha256(path: Path) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_runtime_versions() -> dict:
    package_versions = {}
    for package_name in REQUIRED_RUNTIME_PACKAGES:
        try:
            package_versions[package_name] = version(package_name)
        except PackageNotFoundError as exc:
            raise RuntimeError(
                f"Required Phase 5 dependency is missing: {package_name}"
            ) from exc

    return {
        "python": platform.python_version(),
        "packages": package_versions,
        "status": "PASS",
    }


def reconstruct_phase_04_metadata(
    datasets: dict[str, SupervisedDataset],
    validation_config: dict,
    phase_04_entry_audit: dict,
) -> tuple[TemporalSplit, dict]:
    timestamp_index = get_common_timestamp_index(datasets)
    train_indices, test_indices, top_level_audit = (
        create_top_level_indices(timestamp_index, validation_config)
    )
    cv_fold_indices, cv_audit = create_cv_fold_indices(
        timestamp_index,
        train_indices,
        test_indices,
        validation_config,
    )
    split = TemporalSplit(
        train_indices=train_indices,
        test_indices=test_indices,
        cv_fold_indices=cv_fold_indices,
        split_config=validation_config,
        timestamp_index=timestamp_index,
        configuration_names=EXPECTED_CONFIGURATION_NAMES,
    )
    metadata = {
        "entry_gate": phase_04_entry_audit,
        "configuration": validate_validation_config(validation_config),
        "top_level_split": top_level_audit,
        "cross_validation": cv_audit,
    }
    return split, metadata


def validate_saved_phase_04_contract(
    saved_audit: dict,
    reconstructed_metadata: dict,
) -> dict:
    for section, actual in reconstructed_metadata.items():
        if saved_audit.get(section) != actual:
            raise ValueError(
                f"Saved Phase 4 {section} does not match reconstructed data."
            )

    shared_indices = saved_audit.get("shared_indices", {})
    expected_shared = {
        "configuration_count": 6,
        "configuration_names": list(EXPECTED_CONFIGURATION_NAMES),
        "shared_top_level_indices": True,
        "shared_cv_indices": True,
        "status": "PASS",
    }
    for key, expected_value in expected_shared.items():
        if shared_indices.get(key) != expected_value:
            raise ValueError(
                f"Saved Phase 4 shared-index contract is invalid: {key}."
            )

    expected_final_test = {
        "sealed": True,
        "used_for_feature_selection": False,
        "used_for_tuning": False,
        "used_for_model_selection": False,
        "metrics_computed": False,
        "status": "PASS",
    }
    if saved_audit.get("final_test") != expected_final_test:
        raise ValueError("Phase 4 final-test sealing contract is invalid.")
    if saved_audit.get("determinism") != {
        "deterministic_split": True,
        "status": "PASS",
    }:
        raise ValueError("Phase 4 deterministic split contract is invalid.")
    if saved_audit.get("full_split_datasets_persisted") is not False:
        raise ValueError("Phase 4 unexpectedly persisted full split datasets.")

    return {
        "phase_04_audit": "PASS",
        "reconstruction": "PASS",
        "shared_indices": "PASS",
        "final_test_sealed": True,
        "status": "PASS",
    }


def build_training_datasets(
    datasets: dict[str, SupervisedDataset],
    split: TemporalSplit,
) -> tuple[dict[str, TrainingDataset], dict]:
    expected_train_indices = np.arange(
        len(split.train_indices),
        dtype=np.int64,
    )
    if not np.array_equal(split.train_indices, expected_train_indices):
        raise ValueError(
            "Phase 5 requires the approved contiguous top-level TRAIN block."
        )

    training_datasets = {}
    configuration_audit = {}
    train_rows = len(split.train_indices)

    for name in EXPECTED_CONFIGURATION_NAMES:
        dataset = datasets[name]
        X_train = dataset.X.iloc[:train_rows]
        y_train = dataset.y.iloc[:train_rows]
        train_timestamps = dataset.timestamp_index[:train_rows]

        if tuple(X_train.columns) != dataset.feature_names:
            raise ValueError(f"TRAIN feature order is invalid for {name}.")
        if not X_train.index.equals(y_train.index):
            raise ValueError(f"TRAIN X/y alignment failed for {name}.")
        if not X_train.index.equals(train_timestamps):
            raise ValueError(f"TRAIN timestamp alignment failed for {name}.")
        if not train_timestamps.is_monotonic_increasing:
            raise ValueError(f"TRAIN chronology failed for {name}.")
        if not np.isfinite(X_train.to_numpy()).all():
            raise ValueError(f"TRAIN features are non-finite for {name}.")
        if not np.isfinite(y_train.to_numpy()).all():
            raise ValueError(f"TRAIN target is non-finite for {name}.")
        if "AEP_MW" in X_train.columns:
            raise ValueError(f"Target leakage detected for {name}.")

        training_datasets[name] = TrainingDataset(
            X=X_train,
            y=y_train,
            timestamp_index=train_timestamps,
            feature_names=dataset.feature_names,
        )
        configuration_audit[name] = {
            "train_rows": len(X_train),
            "feature_count": len(X_train.columns),
            "train_start": str(train_timestamps[0]),
            "train_end": str(train_timestamps[-1]),
            "alignment": "PASS",
            "finite_X_y": True,
            "target_leakage": False,
        }

    reference_index = training_datasets[
        EXPECTED_CONFIGURATION_NAMES[0]
    ].timestamp_index
    for name in EXPECTED_CONFIGURATION_NAMES[1:]:
        if not training_datasets[name].timestamp_index.equals(reference_index):
            raise ValueError(
                f"TRAIN timestamp population differs for {name}."
            )

    return training_datasets, {
        "configuration_count": len(training_datasets),
        "configuration_names": list(training_datasets),
        "shared_train_population": True,
        "train_rows": train_rows,
        "configurations": configuration_audit,
        "status": "PASS",
    }


def validate_cv_and_test_boundaries(split: TemporalSplit) -> tuple[dict, dict]:
    fold_audit = []
    for fold in split.cv_fold_indices:
        if np.intersect1d(
            fold.train_indices,
            split.test_indices,
        ).size:
            raise ValueError(f"Final test appears in CV train fold {fold.fold}.")
        if np.intersect1d(
            fold.validation_indices,
            split.test_indices,
        ).size:
            raise ValueError(
                f"Final test appears in CV validation fold {fold.fold}."
            )
        fold_audit.append(
            {
                "fold": fold.fold,
                "train_samples": len(fold.train_indices),
                "validation_samples": len(fold.validation_indices),
                "train_end": str(
                    split.timestamp_index[fold.train_indices[-1]]
                ),
                "validation_start": str(
                    split.timestamp_index[fold.validation_indices[0]]
                ),
                "validation_end": str(
                    split.timestamp_index[fold.validation_indices[-1]]
                ),
            }
        )

    cv_audit = {
        "fold_count": len(split.cv_fold_indices),
        "folds": fold_audit,
        "final_test_excluded": True,
        "status": "PASS",
    }
    test_metadata = {
        "sealed": True,
        "rows": len(split.test_indices),
        "start": str(split.timestamp_index[split.test_indices[0]]),
        "end": str(split.timestamp_index[split.test_indices[-1]]),
        "feature_matrices_materialized": False,
        "target_values_accessed": False,
        "metrics_computed": False,
        "status": "PASS",
    }
    return cv_audit, test_metadata


def validate_phase_05_entry(
    feature_config_path: Path = Path("config/feature_engineering.json"),
    validation_config_path: Path = Path("config/validation.json"),
    model_config_path: Path = Path("config/model_training.json"),
    phase_03_audit_path: Path = Path(
        "outputs/results/phase_03_supervised_quality.json"
    ),
    phase_04_audit_path: Path = Path(
        "outputs/results/phase_04_split_audit.json"
    ),
) -> Phase05EntryState:
    model_config = load_model_training_config(model_config_path)
    saved_phase_04_audit = load_pass_audit(
        phase_04_audit_path,
        "phase_04_temporal_split_validation",
    )
    datasets, validation_config, phase_04_entry_audit = (
        validate_phase_04_entry(
            feature_config_path=feature_config_path,
            validation_config_path=validation_config_path,
            phase_03_audit_path=phase_03_audit_path,
        )
    )
    split, reconstructed_metadata = reconstruct_phase_04_metadata(
        datasets,
        validation_config,
        phase_04_entry_audit,
    )
    upstream_audit = validate_saved_phase_04_contract(
        saved_phase_04_audit,
        reconstructed_metadata,
    )
    training_datasets, training_audit = build_training_datasets(
        datasets,
        split,
    )
    cv_audit, final_test_metadata = validate_cv_and_test_boundaries(split)
    runtime_audit = collect_runtime_versions()

    input_paths = {
        "feature_config": Path(feature_config_path),
        "validation_config": Path(validation_config_path),
        "model_training_config": Path(model_config_path),
        "phase_03_audit": Path(phase_03_audit_path),
        "phase_04_audit": Path(phase_04_audit_path),
    }
    identities = {
        name: {
            "path": str(path),
            "sha256": file_sha256(path),
        }
        for name, path in input_paths.items()
    }

    audit = {
        "phase": "phase_05_entry_gate",
        "upstream": upstream_audit,
        "model_training_config": validate_model_training_config(
            model_config
        ),
        "training_population": training_audit,
        "cross_validation": cv_audit,
        "final_test": final_test_metadata,
        "runtime": runtime_audit,
        "input_identities": identities,
        "training_executed": False,
        "baseline_evaluation_executed": False,
        "status": "PASS",
    }
    return Phase05EntryState(
        training_datasets=training_datasets,
        cv_fold_indices=split.cv_fold_indices,
        model_config=model_config,
        final_test_metadata=final_test_metadata,
        audit=audit,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run Phase 5 screening, tuning, or Random Forest comparison."
        )
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--dry-run-screening",
        action="store_true",
    )
    action.add_argument(
        "--run-screening",
        action="store_true",
    )
    action.add_argument(
        "--resume-screening",
        type=Path,
        metavar="RUN_DIR",
    )
    action.add_argument(
        "--dry-run-tuning",
        action="store_true",
    )
    action.add_argument(
        "--run-tuning",
        action="store_true",
    )
    action.add_argument(
        "--dry-run-random-forest",
        action="store_true",
    )
    action.add_argument(
        "--run-random-forest",
        action="store_true",
    )
    action.add_argument(
        "--resume-random-forest",
        type=Path,
        metavar="RUN_DIR",
    )
    action.add_argument(
        "--dry-run-model-lock",
        action="store_true",
    )
    action.add_argument(
        "--run-model-lock",
        action="store_true",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_SCREENING_OUTPUT,
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIR,
    )
    parser.add_argument(
        "--screening-result",
        type=Path,
        default=DEFAULT_SCREENING_OUTPUT,
    )
    parser.add_argument(
        "--tuning-result",
        type=Path,
    )
    parser.add_argument(
        "--random-forest-result",
        type=Path,
    )
    parser.add_argument(
        "--cv-results-output",
        type=Path,
        default=DEFAULT_CV_RESULTS_OUTPUT,
    )
    parser.add_argument(
        "--model-lock-output",
        type=Path,
        default=DEFAULT_MODEL_LOCK_OUTPUT,
    )
    args = parser.parse_args(argv)

    entry_state = validate_phase_05_entry()
    if args.dry_run_tuning:
        screening_result = load_screening_result(args.screening_result)
        manifest = create_tuning_manifest(entry_state, screening_result)
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0
    if args.run_tuning:
        result = run_phase_05_tuning(
            screening_result_path=args.screening_result,
            runs_dir=args.runs_dir,
            entry_state=entry_state,
        )
        if result["status"] == "INTERRUPTED":
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 130
        summary = {
            "run_dir": result["run_dir"],
            "candidate_count": result["candidate_count"],
            "selected_feature_configuration": result[
                "selected_feature_configuration"
            ],
            "best_parameters": result["best_parameters"],
            "best_mean_mae": result["selected_candidate"]["aggregate"][
                "mean_mae"
            ],
            "best_mean_rmse": result["selected_candidate"]["aggregate"][
                "mean_rmse"
            ],
            "final_test_evaluated": result["final_test_evaluated"],
            "status": result["status"],
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    random_forest_requested = (
        args.dry_run_random_forest
        or args.run_random_forest
        or args.resume_random_forest is not None
    )
    if random_forest_requested:
        if args.tuning_result is None:
            parser.error(
                "--tuning-result is required for Random Forest actions."
            )
        tuning_result = load_tuning_result(args.tuning_result)
        if args.dry_run_random_forest:
            manifest = create_random_forest_manifest(
                entry_state,
                tuning_result,
            )
            print(json.dumps(manifest, indent=2, ensure_ascii=False))
            return 0
        result = run_phase_05_random_forest(
            tuning_result_path=args.tuning_result,
            runs_dir=args.runs_dir,
            resume_run_dir=args.resume_random_forest,
            entry_state=entry_state,
        )
        if result["status"] == "INTERRUPTED":
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 130
        summary = {
            "run_dir": result["run_dir"],
            "selected_feature_configuration": result[
                "selected_feature_configuration"
            ],
            "mean_mae": result["aggregate"]["mean_mae"],
            "mean_rmse": result["aggregate"]["mean_rmse"],
            "final_test_evaluated": result["final_test_evaluated"],
            "status": result["status"],
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    model_lock_requested = args.dry_run_model_lock or args.run_model_lock
    if model_lock_requested:
        if args.tuning_result is None:
            parser.error("--tuning-result is required for model lock.")
        if args.random_forest_result is None:
            parser.error(
                "--random-forest-result is required for model lock."
            )
        screening_result = load_screening_result(args.screening_result)
        validate_screening_inputs_are_current(entry_state, screening_result)
        tuning_result = load_tuning_result(args.tuning_result)
        validate_tuning_inputs_are_current(entry_state, tuning_result)
        random_forest_result = load_random_forest_result(
            args.random_forest_result
        )
        validate_random_forest_result_is_current(
            entry_state,
            args.tuning_result,
            random_forest_result,
        )
        comparison = build_model_comparison(
            entry_state,
            screening_result,
            tuning_result,
            random_forest_result,
        )
        if args.dry_run_model_lock:
            manifest = create_model_lock_manifest(
                entry_state,
                comparison,
            )
            print(json.dumps(manifest, indent=2, ensure_ascii=False))
            return 0
        result = run_phase_05_model_lock(
            screening_result_path=args.screening_result,
            tuning_result_path=args.tuning_result,
            random_forest_result_path=args.random_forest_result,
            cv_result_output_path=args.cv_results_output,
            model_lock_output_path=args.model_lock_output,
            runs_dir=args.runs_dir,
            entry_state=entry_state,
        )
        if result["status"] == "INTERRUPTED":
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 130
        summary = {
            "run_dir": result["run_dir"],
            "cv_selected_candidate": result["model_lock"][
                "cv_selected_candidate"
            ],
            "cv_results_output": str(args.cv_results_output),
            "model_lock_output": str(args.model_lock_output),
            "final_test_evaluated": result["final_test_evaluated"],
            "status": result["status"],
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    manifest = create_screening_manifest(entry_state)
    if args.dry_run_screening:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0

    result = run_phase_05_screening(
        output_path=args.output,
        runs_dir=args.runs_dir,
        resume_run_dir=args.resume_screening,
        entry_state=entry_state,
    )
    if result["status"] == "INTERRUPTED":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 130
    summary = {
        "selected_feature_configuration": result["screening_results"][
            "selected_feature_configuration"
        ],
        "run_dir": result["run_dir"],
        "output": str(args.output),
        "final_test_evaluated": result["screening_results"][
            "final_test_evaluated"
        ],
        "status": result["status"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
