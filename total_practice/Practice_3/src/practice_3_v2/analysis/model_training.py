"""Phase 6 development-only model selection for Practice 3 v2."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from importlib.metadata import version
from itertools import product
import json
import os
from pathlib import Path
import platform
import random
import tempfile
import time
from typing import Any

import numpy as np

from practice_3_v2.analysis.eda import extract_development_data
from practice_3_v2.analysis.metrics import (
    aggregate_fold_metrics,
    regression_metrics,
)
from practice_3_v2.data.data_preparation import (
    calculate_sha256,
    load_json_contract,
)
from practice_3_v2.data.supervised_dataset import (
    PROJECT_ROOT,
    SupervisedFold,
    apply_expanding_window_folds,
    build_supervised_candidates,
    load_phase_05_inputs,
    validate_supervised_population,
)
from practice_3_v2.data.temporal_split import validate_prepared_input


EXPECTED_ELIGIBLE_SAMPLES = 108_083
EXPECTED_FEATURE_COUNT = 22
EXPECTED_FOLDS = 5
RESULT_FILE_NAMES = {
    "baselines": "baseline_results.json",
    "xgboost_baseline": "xgboost_baseline_results.json",
    "random_forest": "random_forest_results.json",
    "xgboost_tuning": "xgboost_tuning_results.json",
}


def _canonical_json(payload: Any) -> bytes:
    """Serialize a payload deterministically for identity calculations."""

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def atomic_write_json(payload: Any, output_path: Path) -> None:
    """Write JSON atomically after a serialization round trip."""

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
            json.dump(payload, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        with temporary_path.open(encoding="utf-8") as file:
            if json.load(file) != payload:
                raise ValueError("Atomic JSON round-trip validation failed.")
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def read_json_document(path: Path) -> Any:
    """Read a JSON artifact without applying contract-status semantics."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"JSON document not found: {path}")
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def append_run_log(log_path: Path, level: str, message: str) -> None:
    """Append one human-readable execution-status line and flush it."""

    timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {level.upper()} | {message}"
    with Path(log_path).open("a", encoding="utf-8") as file:
        file.write(f"{line}\n")
        file.flush()
        os.fsync(file.fileno())
    print(line, flush=True)


def validate_model_training_contract(contract: dict[str, Any]) -> None:
    """Reject changes to the Human-approved Phase 6 protocol."""

    if contract.get("status") != "APPROVED":
        raise ValueError("Model-training contract must be approved.")
    if contract["upstream"] != {
        "phase_05_audit": "outputs/results/phase_05_supervised_dataset.json",
        "phase_05_audit_sha256": (
            "21d6590a0b4acf5d58d26cb0af36f52b300eacd8a884d7153dad125c3ff81eb5"
        ),
        "eligible_samples": EXPECTED_ELIGIBLE_SAMPLES,
        "feature_count": EXPECTED_FEATURE_COUNT,
        "folds": EXPECTED_FOLDS,
    }:
        raise ValueError("Phase 6 upstream identity contract changed.")
    if contract["comparison"] != {
        "task": "one_step_hourly_forecasting",
        "same_validation_timestamps_for_all_candidates": True,
        "scaling": "none",
        "shuffle": False,
    }:
        raise ValueError("Fair-comparison contract changed.")
    if contract["metrics"] != {
        "primary": "mae",
        "secondary": "rmse",
        "aggregate": ["mean", "standard_deviation"],
        "standard_deviation_ddof": 0,
    }:
        raise ValueError("Metric contract changed.")
    if contract["tuning"]["parameter_candidates"] != 24:
        raise ValueError("Tuning must use exactly 24 parameter candidates.")
    if contract["tuning"]["folds_per_candidate"] != EXPECTED_FOLDS:
        raise ValueError("Every tuning candidate must use all approved folds.")
    if contract["tuning"]["random_state"] != 42:
        raise ValueError("Tuning random state must remain locked at 42.")
    if contract["tuning"]["early_stopping"] is not False:
        raise ValueError("Early stopping is outside the approved Phase 6 design.")
    if contract["execution"]["executor"] != "human_terminal_only":
        raise ValueError("Phase 6 training must remain Human-executed.")
    if contract["execution"]["binary_model_persisted"] is not False:
        raise ValueError("Phase 6 must not persist a binary model.")
    if contract["scope"] != {
        "development_only": True,
        "holdout_access_allowed": False,
        "holdout_evaluated": False,
        "recursive_24h_evaluated": False,
    }:
        raise ValueError("Phase 6 scope exceeds the approved boundary.")


def package_versions() -> dict[str, str]:
    """Return exact modeling-package versions for provenance."""

    return {
        "python": platform.python_version(),
        "numpy": version("numpy"),
        "pandas": version("pandas"),
        "scikit-learn": version("scikit-learn"),
        "xgboost": version("xgboost"),
    }


def dependency_smoke_test() -> dict[str, Any]:
    """Verify imports plus tiny fit/predict operations without project data."""

    from sklearn.ensemble import RandomForestRegressor
    from xgboost import XGBRegressor

    X = np.arange(80, dtype="float64").reshape(40, 2)
    y = np.arange(40, dtype="float64")
    random_forest = RandomForestRegressor(
        n_estimators=2,
        random_state=42,
        n_jobs=1,
    ).fit(X, y)
    xgboost = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=2,
        max_depth=2,
        random_state=42,
        n_jobs=1,
        verbosity=0,
    ).fit(X, y)
    predictions = np.concatenate(
        [random_forest.predict(X[:2]), xgboost.predict(X[:2])]
    )
    if not np.isfinite(predictions).all():
        raise ValueError("Dependency smoke-test predictions are non-finite.")
    return {
        "versions": package_versions(),
        "synthetic_fit_predict": "PASS",
    }


def sample_tuning_parameters(contract: dict[str, Any]) -> list[dict[str, Any]]:
    """Sample the approved parameter space deterministically."""

    tuning = contract["tuning"]
    parameter_space = tuning["parameter_space"]
    names = list(parameter_space)
    combinations = [
        dict(zip(names, values, strict=True))
        for values in product(*(parameter_space[name] for name in names))
    ]
    random_generator = random.Random(tuning["random_state"])
    selected_indices = random_generator.sample(
        range(len(combinations)),
        tuning["parameter_candidates"],
    )
    fixed = contract["candidates"]["xgboost_tuned"]["fixed_parameters"]
    sampled: list[dict[str, Any]] = []
    for candidate_index, source_index in enumerate(selected_indices, start=1):
        parameters = {**fixed, **combinations[source_index]}
        identity = sha256(_canonical_json(parameters)).hexdigest()[:12]
        sampled.append(
            {
                "candidate_index": candidate_index,
                "source_index": source_index,
                "parameter_identity": identity,
                "parameters": parameters,
            }
        )
    return sampled


def load_phase_06_inputs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[dict[str, Any], list[SupervisedFold], dict[str, Any]]:
    """Load and validate the complete development-only Phase 6 input state."""

    project_root = Path(project_root).resolve()
    training_contract = load_json_contract(project_root / "config/model_training.json")
    validate_model_training_contract(training_contract)
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
    phase_05_path = project_root / training_contract["upstream"]["phase_05_audit"]
    phase_05_sha256 = calculate_sha256(phase_05_path)
    if phase_05_sha256 != training_contract["upstream"]["phase_05_audit_sha256"]:
        raise ValueError("Phase 5 audit SHA-256 does not match Phase 6.")
    phase_05_audit = read_json_document(phase_05_path)
    if phase_05_audit.get("status") != "PASS":
        raise ValueError("Phase 5 audit must have PASS status.")
    if phase_05_audit["development"]["eligible_rows"] != EXPECTED_ELIGIBLE_SAMPLES:
        raise ValueError("Phase 5 eligible-sample count changed.")
    if phase_05_audit["feature_order"] != supervised_contract["feature_order"]:
        raise ValueError("Phase 5 feature order changed.")
    if len(phase_05_audit["feature_order"]) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Phase 6 requires exactly 22 features.")
    if phase_05_audit["holdout"] != {
        "reserved": True,
        "features_materialized": False,
        "target_statistics_reported": False,
        "evaluation_owner": "phase_07",
    }:
        raise ValueError("Holdout-sealed state changed before Phase 6.")

    prepared, prepared_sha256 = validate_prepared_input(
        project_root / supervised_contract["prepared_input"],
        data_contract,
        preparation_contract,
        split_contract,
        phase_01_audit,
    )
    development = extract_development_data(prepared, data_contract, split_contract)
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
    if int(candidates["is_eligible"].sum()) != EXPECTED_ELIGIBLE_SAMPLES:
        raise ValueError("Reconstructed Phase 6 eligible population changed.")
    expected_counts = [(record["train"]["eligible_rows"], record["validation"]["eligible_rows"]) for record in phase_05_audit["cross_validation"]["folds"]]
    actual_counts = [(len(fold.train.X), len(fold.validation.X)) for fold in folds]
    if actual_counts != expected_counts:
        raise ValueError("Reconstructed Phase 6 fold populations changed.")
    evidence = {
        "phase_05_audit_sha256": phase_05_sha256,
        "prepared_sha256": prepared_sha256,
        "eligible_samples": EXPECTED_ELIGIBLE_SAMPLES,
        "feature_order": deepcopy(supervised_contract["feature_order"]),
        "fold_counts": [
            {
                "fold": fold.fold,
                "train_samples": len(fold.train.X),
                "validation_samples": len(fold.validation.X),
                "validation_start": fold.validation_start.strftime("%Y-%m-%d %H:%M:%S"),
                "validation_end_exclusive": fold.validation_end_exclusive.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for fold in folds
        ],
        "holdout_evaluated": False,
        "holdout_features_materialized": False,
    }
    return training_contract, folds, evidence


def run_preflight(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Run dependency and upstream gates without project-data training."""

    contract, folds, evidence = load_phase_06_inputs(project_root)
    sampled = sample_tuning_parameters(contract)
    dependency = dependency_smoke_test()
    return {
        "phase": contract["phase"],
        "dependency_gate": dependency,
        "eligible_samples": evidence["eligible_samples"],
        "feature_count": len(evidence["feature_order"]),
        "folds": len(folds),
        "tuning_parameter_candidates": len(sampled),
        "sampled_parameter_set_sha256": sha256(_canonical_json(sampled)).hexdigest(),
        "holdout_evaluated": False,
        "training_started": False,
        "status": "PASS",
    }


def _execution_identity(contract: dict[str, Any], evidence: dict[str, Any]) -> str:
    payload = {
        "contract": contract,
        "phase_05_audit_sha256": evidence["phase_05_audit_sha256"],
        "prepared_sha256": evidence["prepared_sha256"],
        "feature_order": evidence["feature_order"],
        "fold_counts": evidence["fold_counts"],
    }
    return sha256(_canonical_json(payload)).hexdigest()[:8]


def initialize_run(
    project_root: Path,
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[Path, Path, dict[str, Any]]:
    """Create a new Human-owned run with all tuning parameters pre-recorded."""

    identity = _execution_identity(contract, evidence)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    run_id = f"P6_model_selection_{timestamp}_{identity}"
    run_dir = project_root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    log_path = run_dir / f"{run_id}.log"
    sampled = sample_tuning_parameters(contract)
    metadata = {
        "run_id": run_id,
        "execution_identity": identity,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "executor": "human_terminal_only",
        "package_versions": package_versions(),
        "upstream_evidence": evidence,
        "sampled_parameter_set_sha256": sha256(_canonical_json(sampled)).hexdigest(),
    }
    checkpoint = {
        "run_id": run_id,
        "execution_identity": identity,
        "status": "READY",
        "completed_tasks": [],
        "official_outputs_promoted": False,
        "holdout_evaluated": False,
    }
    atomic_write_json(contract, run_dir / "config_snapshot.json")
    atomic_write_json(metadata, run_dir / "run_metadata.json")
    atomic_write_json(checkpoint, run_dir / "checkpoint.json")
    atomic_write_json(
        {"status": "PENDING", "sampled_candidates": sampled},
        run_dir / RESULT_FILE_NAMES["xgboost_tuning"],
    )
    append_run_log(log_path, "INFO", "Phase 6 model selection initialized.")
    return run_dir, log_path, checkpoint


def validate_resume_identity(
    run_dir: Path,
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    """Reject resume when any approved scientific input changed."""

    run_dir = Path(run_dir).resolve()
    checkpoint = read_json_document(run_dir / "checkpoint.json")
    metadata = read_json_document(run_dir / "run_metadata.json")
    snapshot = read_json_document(run_dir / "config_snapshot.json")
    expected_identity = _execution_identity(contract, evidence)
    if snapshot != contract:
        raise ValueError("Run configuration no longer matches Phase 6 contract.")
    if checkpoint["execution_identity"] != expected_identity:
        raise ValueError("Checkpoint execution identity does not match current inputs.")
    if metadata["upstream_evidence"] != evidence:
        raise ValueError("Run upstream evidence no longer matches current inputs.")
    if checkpoint.get("official_outputs_promoted"):
        raise ValueError("Completed official run must not be resumed.")
    log_path = run_dir / f"{checkpoint['run_id']}.log"
    return log_path, checkpoint


def _checkpoint_task(
    run_dir: Path,
    checkpoint: dict[str, Any],
    task: str,
) -> None:
    completed = set(checkpoint["completed_tasks"])
    completed.add(task)
    checkpoint["completed_tasks"] = sorted(completed)
    checkpoint["status"] = "RUNNING"
    atomic_write_json(checkpoint, run_dir / "checkpoint.json")


def _load_or_initialize_result(path: Path, candidate: str) -> dict[str, Any]:
    if path.is_file():
        return read_json_document(path)
    return {"candidate": candidate, "fold_metrics": [], "status": "RUNNING"}


def _replace_fold_record(records: list[dict[str, Any]], record: dict[str, Any]) -> None:
    records[:] = [item for item in records if int(item["fold"]) != int(record["fold"])]
    records.append(record)
    records.sort(key=lambda item: int(item["fold"]))


def evaluate_baseline_candidate(
    candidate: str,
    prediction_feature: str,
    folds: list[SupervisedFold],
    run_dir: Path,
    log_path: Path,
    checkpoint: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate one no-fit baseline on approved validation timestamps."""

    output_path = run_dir / RESULT_FILE_NAMES["baselines"]
    result = read_json_document(output_path) if output_path.is_file() else {"candidates": {}}
    candidate_result = result["candidates"].setdefault(
        candidate,
        {"candidate": candidate, "prediction_feature": prediction_feature, "fold_metrics": []},
    )
    for fold in folds:
        task = f"{candidate}:fold:{fold.fold}"
        if task in checkpoint["completed_tasks"]:
            continue
        append_run_log(log_path, "INFO", f"{candidate} fold {fold.fold}/5 started.")
        prediction = fold.validation.X[prediction_feature].to_numpy(dtype="float64")
        metrics = regression_metrics(fold.validation.y.to_numpy(), prediction)
        record = {"fold": fold.fold, **metrics, "duration_seconds": 0.0}
        _replace_fold_record(candidate_result["fold_metrics"], record)
        atomic_write_json(result, output_path)
        _checkpoint_task(run_dir, checkpoint, task)
        append_run_log(
            log_path,
            "INFO",
            f"{candidate} fold {fold.fold} completed: MAE={metrics['mae']:.6f} RMSE={metrics['rmse']:.6f} time=0.000s.",
        )
    candidate_result["aggregate"] = aggregate_fold_metrics(candidate_result["fold_metrics"])
    candidate_result["status"] = "PASS"
    atomic_write_json(result, output_path)
    return candidate_result


def _build_estimator(kind: str, parameters: dict[str, Any]) -> Any:
    if kind == "xgboost":
        from xgboost import XGBRegressor

        return XGBRegressor(**parameters, verbosity=0)
    if kind == "random_forest":
        from sklearn.ensemble import RandomForestRegressor

        return RandomForestRegressor(**parameters)
    raise ValueError(f"Unsupported estimator kind: {kind}")


def evaluate_model_candidate(
    candidate: str,
    kind: str,
    parameters: dict[str, Any],
    folds: list[SupervisedFold],
    run_dir: Path,
    log_path: Path,
    checkpoint: dict[str, Any],
) -> dict[str, Any]:
    """Fit one fixed ML candidate across all approved folds."""

    output_path = run_dir / RESULT_FILE_NAMES[candidate]
    result = _load_or_initialize_result(output_path, candidate)
    result["kind"] = kind
    result["parameters"] = deepcopy(parameters)
    for fold in folds:
        task = f"{candidate}:fold:{fold.fold}"
        if task in checkpoint["completed_tasks"]:
            continue
        append_run_log(log_path, "INFO", f"{candidate} fold {fold.fold}/5 started.")
        started = time.perf_counter()
        estimator = _build_estimator(kind, parameters)
        estimator.fit(fold.train.X, fold.train.y)
        prediction = np.asarray(estimator.predict(fold.validation.X), dtype="float64")
        duration = time.perf_counter() - started
        metrics = regression_metrics(fold.validation.y.to_numpy(), prediction)
        record = {"fold": fold.fold, **metrics, "duration_seconds": float(duration)}
        _replace_fold_record(result["fold_metrics"], record)
        atomic_write_json(result, output_path)
        _checkpoint_task(run_dir, checkpoint, task)
        append_run_log(
            log_path,
            "INFO",
            f"{candidate} fold {fold.fold} completed: MAE={metrics['mae']:.6f} RMSE={metrics['rmse']:.6f} time={duration:.3f}s.",
        )
    result["aggregate"] = aggregate_fold_metrics(result["fold_metrics"])
    result["status"] = "PASS"
    atomic_write_json(result, output_path)
    return result


def _metric_sort_key(record: dict[str, Any]) -> tuple[float, int]:
    aggregate = record["aggregate"]
    return (
        float(aggregate["mean_cv_mae"]),
        int(record.get("candidate_index", 0)),
    )


def evaluate_xgboost_tuning(
    contract: dict[str, Any],
    folds: list[SupervisedFold],
    run_dir: Path,
    log_path: Path,
    checkpoint: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate all pre-recorded XGBoost configurations with checkpointing."""

    output_path = run_dir / RESULT_FILE_NAMES["xgboost_tuning"]
    result = read_json_document(output_path)
    sampled = result["sampled_candidates"]
    for candidate in sampled:
        candidate.setdefault("fold_metrics", [])
        candidate["status"] = "RUNNING"
        index = int(candidate["candidate_index"])
        for fold in folds:
            task = f"xgboost_tuning:{index}:fold:{fold.fold}"
            if task in checkpoint["completed_tasks"]:
                continue
            append_run_log(
                log_path,
                "INFO",
                f"XGBoost tuning candidate {index}/24 fold {fold.fold}/5 started.",
            )
            started = time.perf_counter()
            estimator = _build_estimator("xgboost", candidate["parameters"])
            estimator.fit(fold.train.X, fold.train.y)
            prediction = np.asarray(estimator.predict(fold.validation.X), dtype="float64")
            duration = time.perf_counter() - started
            metrics = regression_metrics(fold.validation.y.to_numpy(), prediction)
            record = {"fold": fold.fold, **metrics, "duration_seconds": float(duration)}
            _replace_fold_record(candidate["fold_metrics"], record)
            atomic_write_json(result, output_path)
            _checkpoint_task(run_dir, checkpoint, task)
            append_run_log(
                log_path,
                "INFO",
                f"XGBoost tuning candidate {index}/24 fold {fold.fold} completed: MAE={metrics['mae']:.6f} RMSE={metrics['rmse']:.6f} time={duration:.3f}s.",
            )
        candidate["aggregate"] = aggregate_fold_metrics(candidate["fold_metrics"])
        candidate["status"] = "PASS"
        atomic_write_json(result, output_path)
    best = min(sampled, key=_metric_sort_key)
    result["selected_parameter_candidate"] = {
        "candidate_index": best["candidate_index"],
        "parameter_identity": best["parameter_identity"],
        "parameters": deepcopy(best["parameters"]),
        "fold_metrics": deepcopy(best["fold_metrics"]),
        "aggregate": deepcopy(best["aggregate"]),
    }
    result["status"] = "PASS"
    atomic_write_json(result, output_path)
    return result


def select_candidate(
    candidate_records: list[dict[str, Any]],
    selection_contract: dict[str, Any],
) -> dict[str, Any]:
    """Apply the approved sequential metric and simplicity tie-break."""

    names = [record["candidate"] for record in candidate_records]
    if set(names) != set(selection_contract["simplicity_order"]):
        raise ValueError("Candidate set does not match the approved registry.")
    tolerance = float(selection_contract["floating_point_tie_tolerance"])
    simplicity = {
        name: index for index, name in enumerate(selection_contract["simplicity_order"])
    }

    def better(left: dict[str, Any], right: dict[str, Any]) -> bool:
        metric_keys = [
            "mean_cv_mae",
            "mean_cv_rmse",
            "cv_mae_standard_deviation",
        ]
        for key in metric_keys:
            left_value = float(left["aggregate"][key])
            right_value = float(right["aggregate"][key])
            if left_value < right_value - tolerance:
                return True
            if left_value > right_value + tolerance:
                return False
        return simplicity[left["candidate"]] < simplicity[right["candidate"]]

    selected = candidate_records[0]
    for record in candidate_records[1:]:
        if better(record, selected):
            selected = record
    return selected


def _candidate_summary(
    baseline_results: list[dict[str, Any]],
    xgboost_baseline: dict[str, Any],
    random_forest: dict[str, Any],
    tuning: dict[str, Any],
) -> list[dict[str, Any]]:
    tuned = tuning["selected_parameter_candidate"]
    return [
        *[
            {
                "candidate": result["candidate"],
                "kind": "baseline",
                "parameters": {"prediction_feature": result["prediction_feature"]},
                "fold_metrics": result["fold_metrics"],
                "aggregate": result["aggregate"],
            }
            for result in baseline_results
        ],
        {
            "candidate": "xgboost_baseline",
            "kind": "xgboost",
            "parameters": xgboost_baseline["parameters"],
            "fold_metrics": xgboost_baseline["fold_metrics"],
            "aggregate": xgboost_baseline["aggregate"],
        },
        {
            "candidate": "random_forest",
            "kind": "random_forest",
            "parameters": random_forest["parameters"],
            "fold_metrics": random_forest["fold_metrics"],
            "aggregate": random_forest["aggregate"],
        },
        {
            "candidate": "xgboost_tuned",
            "kind": "xgboost",
            "parameters": tuned["parameters"],
            "tuning_candidate_index": tuned["candidate_index"],
            "parameter_identity": tuned["parameter_identity"],
            "fold_metrics": tuned["fold_metrics"],
            "aggregate": tuned["aggregate"],
        },
    ]


def save_comparison_figure(candidate_records: list[dict[str, Any]], output_path: Path) -> None:
    """Atomically save the official CV comparison figure."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(output_path.parent / ".matplotlib"))
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [record["candidate"] for record in candidate_records]
    maes = [record["aggregate"]["mean_cv_mae"] for record in candidate_records]
    rmses = [record["aggregate"]["mean_cv_rmse"] for record in candidate_records]
    mae_std = [record["aggregate"]["cv_mae_standard_deviation"] for record in candidate_records]
    positions = np.arange(len(labels))
    width = 0.36
    figure, axis = plt.subplots(figsize=(12, 6))
    axis.bar(positions - width / 2, maes, width, yerr=mae_std, capsize=4, label="Mean CV MAE")
    axis.bar(positions + width / 2, rmses, width, label="Mean CV RMSE")
    axis.set_title("Phase 6 — Development CV Model Comparison")
    axis.set_ylabel("MW")
    axis.set_xticks(positions, labels, rotation=18, ha="right")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    temporary_path = output_path.with_name(f".{output_path.name}.tmp.png")
    figure.savefig(temporary_path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
        raise ValueError("Comparison figure validation failed.")
    os.replace(temporary_path, output_path)


def promote_official_outputs(
    project_root: Path,
    contract: dict[str, Any],
    evidence: dict[str, Any],
    metadata: dict[str, Any],
    candidate_records: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Promote complete CV evidence and a non-binary model lock."""

    selected = select_candidate(candidate_records, contract["selection"])
    cv_results = {
        "phase": contract["phase"],
        "contract_version": contract["contract_version"],
        "upstream_evidence": evidence,
        "comparison_contract": deepcopy(contract["comparison"]),
        "metric_contract": deepcopy(contract["metrics"]),
        "candidate_results": candidate_records,
        "selection_policy": deepcopy(contract["selection"]),
        "selected_candidate": selected["candidate"],
        "package_versions": metadata["package_versions"],
        "holdout_evaluated": False,
        "binary_model_persisted": False,
        "status": "PASS",
    }
    cv_path = project_root / contract["outputs"]["cv_results"]
    atomic_write_json(cv_results, cv_path)
    cv_sha256 = calculate_sha256(cv_path)
    model_lock = {
        "phase": contract["phase"],
        "contract_version": contract["contract_version"],
        "candidate_registry": list(contract["candidates"]),
        "selected_candidate": selected["candidate"],
        "selected_kind": selected["kind"],
        "locked_parameters": deepcopy(selected["parameters"]),
        "random_state": selected["parameters"].get("random_state"),
        "selection_evidence": deepcopy(selected["aggregate"]),
        "feature_order": deepcopy(evidence["feature_order"]),
        "upstream_identities": {
            "phase_05_audit_sha256": evidence["phase_05_audit_sha256"],
            "prepared_sha256": evidence["prepared_sha256"],
            "cv_results_sha256": cv_sha256,
        },
        "package_versions": metadata["package_versions"],
        "holdout_evaluated": False,
        "binary_model_persisted": False,
        "status": "PASS",
    }
    lock_path = project_root / contract["outputs"]["model_lock"]
    atomic_write_json(model_lock, lock_path)
    save_comparison_figure(
        candidate_records,
        project_root / contract["outputs"]["comparison_figure"],
    )
    return cv_results, model_lock


def run_training(
    project_root: Path = PROJECT_ROOT,
    resume_run_dir: Path | None = None,
) -> dict[str, Any]:
    """Run Human-authorized Phase 6 training with fold-level checkpoints."""

    project_root = Path(project_root).resolve()
    contract, folds, evidence = load_phase_06_inputs(project_root)
    dependency_smoke_test()
    if resume_run_dir is None:
        run_dir, log_path, checkpoint = initialize_run(project_root, contract, evidence)
        append_run_log(log_path, "INFO", "Phase 6 model selection started.")
    else:
        run_dir = Path(resume_run_dir).resolve()
        log_path, checkpoint = validate_resume_identity(run_dir, contract, evidence)
        checkpoint["status"] = "RUNNING"
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "INFO", "Phase 6 run resumed after identity validation.")
    metadata = read_json_document(run_dir / "run_metadata.json")
    try:
        persistence = evaluate_baseline_candidate(
            "persistence",
            contract["candidates"]["persistence"]["prediction_feature"],
            folds,
            run_dir,
            log_path,
            checkpoint,
        )
        seasonal = evaluate_baseline_candidate(
            "seasonal_naive_24",
            contract["candidates"]["seasonal_naive_24"]["prediction_feature"],
            folds,
            run_dir,
            log_path,
            checkpoint,
        )
        xgb_contract = contract["candidates"]["xgboost_baseline"]
        xgboost_baseline = evaluate_model_candidate(
            "xgboost_baseline",
            "xgboost",
            xgb_contract["parameters"],
            folds,
            run_dir,
            log_path,
            checkpoint,
        )
        rf_contract = contract["candidates"]["random_forest"]
        random_forest = evaluate_model_candidate(
            "random_forest",
            "random_forest",
            rf_contract["parameters"],
            folds,
            run_dir,
            log_path,
            checkpoint,
        )
        tuning = evaluate_xgboost_tuning(
            contract,
            folds,
            run_dir,
            log_path,
            checkpoint,
        )
        candidate_records = _candidate_summary(
            [persistence, seasonal],
            xgboost_baseline,
            random_forest,
            tuning,
        )
        cv_results, model_lock = promote_official_outputs(
            project_root,
            contract,
            evidence,
            metadata,
            candidate_records,
        )
        checkpoint["status"] = "COMPLETED"
        checkpoint["official_outputs_promoted"] = True
        checkpoint["holdout_evaluated"] = False
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "INFO", "Phase 6 model selection completed.")
        return {
            "run_dir": str(run_dir.relative_to(project_root)),
            "selected_candidate": model_lock["selected_candidate"],
            "cv_results": contract["outputs"]["cv_results"],
            "model_lock": contract["outputs"]["model_lock"],
            "holdout_evaluated": cv_results["holdout_evaluated"],
            "status": "PASS",
        }
    except KeyboardInterrupt:
        checkpoint["status"] = "INTERRUPTED"
        checkpoint["official_outputs_promoted"] = False
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "WARNING", "Phase 6 training interrupted by Human.")
        raise
    except Exception as error:
        checkpoint["status"] = "FAILED"
        checkpoint["official_outputs_promoted"] = False
        checkpoint["last_error"] = f"{type(error).__name__}: {error}"
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "ERROR", f"Phase 6 training failed: {type(error).__name__}: {error}")
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--preflight",
        action="store_true",
        help="Validate dependencies and scientific inputs without project-data training.",
    )
    actions.add_argument(
        "--run-training",
        action="store_true",
        help="Start a new Human-authorized Phase 6 training run.",
    )
    actions.add_argument(
        "--resume-run-dir",
        type=Path,
        help="Resume a Human-authorized interrupted run after identity validation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.preflight:
        result = run_preflight()
    elif args.run_training:
        result = run_training()
    else:
        result = run_training(resume_run_dir=args.resume_run_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
