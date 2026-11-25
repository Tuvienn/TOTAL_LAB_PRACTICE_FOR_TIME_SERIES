"""Post-hoc Phase 6 supplemental experiments for Practice 3."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import time
from typing import Any

import numpy as np
import pandas as pd

from practice_3.analysis.metrics import (
    aggregate_fold_metrics,
    regression_metrics,
)
from practice_3.analysis.model_training import (
    append_run_log,
    atomic_write_json,
    package_versions,
    read_json_document,
)
from practice_3.data.data_preparation import (
    calculate_sha256,
    load_json_contract,
)
from practice_3.data.supervised_dataset import (
    PROJECT_ROOT,
    SupervisedFold,
    SupervisedPartition,
    apply_expanding_window_folds,
    build_supervised_candidates,
    validate_supervised_population,
)
from practice_3.visualization.supplemental_experiments import (
    save_lag_sensitivity_figure,
    save_model_comparison_figure,
)


EXPECTED_P_VALUES = [1, 6, 12, 24, 48, 168]
EXPECTED_FOLDS = 5
EXPECTED_FEATURE_COUNT = 22
EXPECTED_PROJECT_FITS = 35
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
RUN_LINEAR_FILE = "linear_regression_results.json"
RUN_LAG_FILE = "lag_sensitivity_results.json"


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def validate_supplemental_contract(contract: dict[str, Any]) -> None:
    """Reject drift from the Human-approved supplemental protocol."""

    if contract.get("status") != "APPROVED":
        raise ValueError("Supplemental contract must be approved.")
    if contract.get("evidence_label") != "post_hoc_supplemental_evidence":
        raise ValueError("Supplemental evidence label changed.")
    upstream = contract["upstream"]
    expected_upstream = {
        "development_eligible_samples": 108_083,
        "official_validation_predictions": 42_413,
        "folds": EXPECTED_FOLDS,
        "feature_count": EXPECTED_FEATURE_COUNT,
        "selected_candidate": "xgboost_tuned",
    }
    for key, value in expected_upstream.items():
        if upstream.get(key) != value:
            raise ValueError(f"Supplemental upstream field changed: {key}.")
    linear = contract["linear_regression"]
    if linear != {
        "candidate": "linear_regression_scaled",
        "feature_population": "official_phase_05_22_features",
        "pipeline": ["StandardScaler", "LinearRegression"],
        "scaler_fit_scope": "fold_train_only",
        "regularization": "none",
        "tuning": False,
        "same_validation_timestamps_as_phase_06": True,
        "comparison_candidate": "xgboost_tuned",
        "xgboost_retrained": False,
    }:
        raise ValueError("Linear Regression protocol changed.")
    lag = contract["lag_sensitivity"]
    if lag["p_values"] != EXPECTED_P_VALUES:
        raise ValueError("Approved lag-p registry changed.")
    if (
        lag["common_population_reference_p"] != 168
        or lag["included_feature_groups"] != ["consecutive_lags_only"]
        or lag["rolling_features_included"] is not False
        or lag["calendar_features_included"] is not False
        or lag["imputation"] != "none"
        or lag["tuning"] is not False
    ):
        raise ValueError("Lag-sensitivity protocol changed.")
    execution = contract["execution"]
    if (
        execution["executor"] != "human_terminal_only"
        or execution["project_data_fits"] != EXPECTED_PROJECT_FITS
        or execution["checkpoint_after_each_fit"] is not True
        or execution["resume_supported"] is not True
        or execution["binary_model_persisted"] is not False
    ):
        raise ValueError("Supplemental execution boundary changed.")
    if contract["scope"] != {
        "development_only": True,
        "holdout_access_allowed": False,
        "holdout_evaluated": False,
        "changes_model_lock": False,
        "selection_authority": "none",
        "final_answer_owner": "phase_09",
    }:
        raise ValueError("Supplemental scientific scope changed.")


def _verify_file_identity(path: Path, expected_sha256: str, label: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    actual = calculate_sha256(path)
    if actual != expected_sha256:
        raise ValueError(f"{label} SHA-256 changed. Expected {expected_sha256}; got {actual}.")
    return actual


def _load_development_only(
    project_root: Path,
    data_contract: dict[str, Any],
    preparation_contract: dict[str, Any],
    split_contract: dict[str, Any],
    expected_prepared_sha256: str,
) -> pd.DataFrame:
    """Read only approved development rows after verifying the full file identity."""

    prepared_path = project_root / split_contract["prepared_input"]
    _verify_file_identity(prepared_path, expected_prepared_sha256, "Prepared dataset")
    expected_rows = int(split_contract["development"]["expected_rows"])
    development = pd.read_csv(prepared_path, nrows=expected_rows)
    expected_columns = [
        data_contract["timestamp_column"],
        data_contract["target_column"],
        "source_count",
        "quality_flag",
    ]
    if development.columns.tolist() != expected_columns:
        raise ValueError("Prepared development schema changed.")
    development[data_contract["timestamp_column"]] = pd.to_datetime(
        development[data_contract["timestamp_column"]],
        format=preparation_contract["datetime_format"],
        errors="raise",
    ).astype("datetime64[ns]")
    development[data_contract["target_column"]] = pd.to_numeric(
        development[data_contract["target_column"]], errors="coerce"
    ).astype("float64")
    timestamps = development[data_contract["timestamp_column"]]
    start = pd.Timestamp(split_contract["development"]["start_inclusive"])
    end = pd.Timestamp(split_contract["development"]["end_exclusive"])
    if len(development) != expected_rows or timestamps.iloc[0] != start:
        raise ValueError("Development boundary or row count changed.")
    if timestamps.iloc[-1] >= end:
        raise ValueError("Supplemental loader crossed into holdout timestamps.")
    if not timestamps.is_unique or not timestamps.is_monotonic_increasing:
        raise ValueError("Development timestamps must be unique and chronological.")
    if not timestamps.diff().dropna().eq(pd.Timedelta(hours=1)).all():
        raise ValueError("Development timeline must be complete and hourly.")
    observed = int(development[data_contract["target_column"]].notna().sum())
    if observed != int(split_contract["development"]["expected_observed_targets"]):
        raise ValueError("Development observed-target count changed.")
    return development


def _official_xgboost_record(cv_results: dict[str, Any]) -> dict[str, Any]:
    matches = [
        record
        for record in cv_results["candidate_results"]
        if record["candidate"] == "xgboost_tuned"
    ]
    if len(matches) != 1:
        raise ValueError("Official XGBoost reference is missing or duplicated.")
    return matches[0]


def build_consecutive_lag_frame(
    development: pd.DataFrame,
    data_contract: dict[str, Any],
    max_p: int = 168,
) -> pd.DataFrame:
    """Build target-time-aligned consecutive lags without imputation."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    target = development[target_column].astype("float64")
    columns: dict[str, pd.Series] = {
        "target_timestamp": development[timestamp_column],
        "forecast_origin": development[timestamp_column] - pd.Timedelta(hours=1),
        "target": target,
    }
    columns.update(
        {f"lag_{lag}h": target.shift(lag) for lag in range(1, max_p + 1)}
    )
    frame = pd.DataFrame(columns)
    if not frame["target_timestamp"].is_monotonic_increasing:
        raise ValueError("Lag frame is not chronological.")
    return frame


def natural_eligibility_counts(
    lag_frame: pd.DataFrame,
    p_values: list[int] | tuple[int, ...] = EXPECTED_P_VALUES,
) -> dict[int, int]:
    """Count naturally eligible development rows for every approved p."""

    counts: dict[int, int] = {}
    target_valid = lag_frame["target"].notna() & np.isfinite(lag_frame["target"])
    for p in p_values:
        columns = [f"lag_{lag}h" for lag in range(1, int(p) + 1)]
        feature_values = lag_frame[columns].to_numpy(dtype="float64")
        valid = target_valid & np.isfinite(feature_values).all(axis=1)
        counts[int(p)] = int(valid.sum())
    values = [counts[int(p)] for p in p_values]
    if any(right > left for left, right in zip(values, values[1:])):
        raise ValueError("Natural lag eligibility increased as p increased.")
    return counts


def _lag_partition(
    lag_frame: pd.DataFrame,
    row_mask: pd.Series,
    p: int,
    common_valid: pd.Series,
) -> SupervisedPartition:
    selected = lag_frame.loc[row_mask & common_valid].copy()
    selected = selected.sort_values("target_timestamp", kind="stable")
    feature_order = [f"lag_{lag}h" for lag in range(1, p + 1)]
    index = pd.DatetimeIndex(selected["target_timestamp"], name="target_timestamp")
    X = selected[feature_order].astype("float64")
    X.index = index
    y = selected["target"].astype("float64")
    y.index = index
    metadata = selected[["target_timestamp", "forecast_origin"]].copy()
    metadata.index = index
    return SupervisedPartition(X=X, y=y, metadata=metadata)


def build_common_lag_folds(
    lag_frame: pd.DataFrame,
    split_contract: dict[str, Any],
    p_values: list[int] | tuple[int, ...] = EXPECTED_P_VALUES,
) -> dict[int, list[SupervisedFold]]:
    """Build every p on the exact timestamps eligible for p=168."""

    max_p = max(int(p) for p in p_values)
    common_columns = [f"lag_{lag}h" for lag in range(1, max_p + 1)]
    common_valid = (
        lag_frame["target"].notna()
        & np.isfinite(lag_frame["target"])
        & np.isfinite(lag_frame[common_columns].to_numpy(dtype="float64")).all(axis=1)
    )
    timestamps = lag_frame["target_timestamp"]
    development_start = pd.Timestamp(split_contract["development"]["start_inclusive"])
    fold_map: dict[int, list[SupervisedFold]] = {}
    for p_value in p_values:
        p = int(p_value)
        folds: list[SupervisedFold] = []
        for fold_contract in split_contract["cross_validation"]["folds"]:
            validation_start = pd.Timestamp(fold_contract["validation_start_inclusive"])
            validation_end = pd.Timestamp(fold_contract["validation_end_exclusive"])
            train_mask = timestamps.ge(development_start) & timestamps.lt(validation_start)
            validation_mask = timestamps.ge(validation_start) & timestamps.lt(validation_end)
            folds.append(
                SupervisedFold(
                    fold=int(fold_contract["fold"]),
                    validation_start=validation_start,
                    validation_end_exclusive=validation_end,
                    train=_lag_partition(lag_frame, train_mask, p, common_valid),
                    validation=_lag_partition(
                        lag_frame, validation_mask, p, common_valid
                    ),
                )
            )
        fold_map[p] = folds
    reference = fold_map[max_p]
    for p, folds in fold_map.items():
        for fold, expected in zip(folds, reference, strict=True):
            if not fold.train.X.index.equals(expected.train.X.index):
                raise ValueError(f"Lag p={p} train timestamps differ from p={max_p}.")
            if not fold.validation.X.index.equals(expected.validation.X.index):
                raise ValueError(
                    f"Lag p={p} validation timestamps differ from p={max_p}."
                )
            if fold.train.X.index.max() >= fold.validation.X.index.min():
                raise ValueError(f"Lag p={p} fold {fold.fold} violates chronology.")
    return fold_map


def load_supplemental_inputs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[
    dict[str, Any],
    list[SupervisedFold],
    dict[int, list[SupervisedFold]],
    dict[str, Any],
    dict[str, Any],
]:
    """Load and validate all development-only supplemental inputs."""

    project_root = Path(project_root).resolve()
    contract = load_json_contract(project_root / "config/supplemental_experiments.json")
    validate_supplemental_contract(contract)
    upstream = contract["upstream"]
    identity_pairs = [
        ("phase_05_audit", "phase_05_audit_sha256", "Phase 5 audit"),
        ("phase_06_cv_results", "phase_06_cv_results_sha256", "Phase 6 CV results"),
        ("phase_06_model_lock", "phase_06_model_lock_sha256", "Phase 6 model lock"),
        ("features_contract", "features_contract_sha256", "Feature contract"),
        ("supervised_contract", "supervised_contract_sha256", "Supervised contract"),
        ("temporal_split_contract", "temporal_split_contract_sha256", "Split contract"),
    ]
    verified_hashes = {
        path_key: _verify_file_identity(
            project_root / upstream[path_key], upstream[hash_key], label
        )
        for path_key, hash_key, label in identity_pairs
    }
    data_contract = load_json_contract(project_root / "config/data_contract.json")
    preparation_contract = load_json_contract(
        project_root / "config/data_preparation.json"
    )
    split_contract = load_json_contract(project_root / upstream["temporal_split_contract"])
    feature_contract = load_json_contract(project_root / upstream["features_contract"])
    supervised_contract = load_json_contract(project_root / upstream["supervised_contract"])
    phase_05_audit = read_json_document(project_root / upstream["phase_05_audit"])
    cv_results = read_json_document(project_root / upstream["phase_06_cv_results"])
    model_lock = read_json_document(project_root / upstream["phase_06_model_lock"])
    if any(item.get("status") != "PASS" for item in [phase_05_audit, cv_results, model_lock]):
        raise ValueError("Locked upstream artifacts must all have PASS status.")
    if cv_results["selected_candidate"] != upstream["selected_candidate"]:
        raise ValueError("Official Phase 6 selected candidate changed.")
    if model_lock["locked_parameters"] != contract["lag_sensitivity"]["parameters"]:
        raise ValueError("Supplemental lag parameters differ from the model lock.")
    if model_lock["feature_order"] != supervised_contract["feature_order"]:
        raise ValueError("Official feature order changed.")
    if len(model_lock["feature_order"]) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Supplemental Linear Regression requires 22 features.")
    if cv_results["package_versions"] != model_lock["package_versions"]:
        raise ValueError("Official Phase 6 package evidence is inconsistent.")
    if package_versions() != model_lock["package_versions"]:
        raise ValueError("Runtime packages differ from the approved Phase 6 environment.")
    official_xgboost = _official_xgboost_record(cv_results)
    if official_xgboost["parameters"] != model_lock["locked_parameters"]:
        raise ValueError("Official tuned XGBoost parameters conflict with model lock.")
    if official_xgboost["aggregate"]["validation_samples"] != upstream[
        "official_validation_predictions"
    ]:
        raise ValueError("Official validation population changed.")

    development = _load_development_only(
        project_root,
        data_contract,
        preparation_contract,
        split_contract,
        upstream["prepared_sha256"],
    )
    candidates = build_supervised_candidates(
        development, data_contract, feature_contract, supervised_contract
    )
    official_folds = apply_expanding_window_folds(
        candidates, data_contract, split_contract, supervised_contract
    )
    validate_supervised_population(
        candidates,
        official_folds,
        development,
        data_contract,
        split_contract,
        supervised_contract,
    )
    eligible = int(candidates["is_eligible"].sum())
    if eligible != upstream["development_eligible_samples"]:
        raise ValueError("Official development eligible population changed.")
    expected_fold_evidence = cv_results["upstream_evidence"]["fold_counts"]
    actual_fold_evidence = [
        {
            "fold": fold.fold,
            "train_samples": len(fold.train.X),
            "validation_samples": len(fold.validation.X),
            "validation_start": fold.validation_start.strftime(DATETIME_FORMAT),
            "validation_end_exclusive": fold.validation_end_exclusive.strftime(
                DATETIME_FORMAT
            ),
        }
        for fold in official_folds
    ]
    if actual_fold_evidence != expected_fold_evidence:
        raise ValueError("Linear Regression folds differ from official Phase 6 folds.")

    lag_frame = build_consecutive_lag_frame(development, data_contract)
    natural_counts = natural_eligibility_counts(lag_frame)
    lag_folds = build_common_lag_folds(lag_frame, split_contract)
    evidence = {
        "evidence_label": contract["evidence_label"],
        "verified_upstream_sha256": verified_hashes,
        "prepared_sha256": upstream["prepared_sha256"],
        "package_versions": package_versions(),
        "official_feature_order": deepcopy(model_lock["feature_order"]),
        "official_fold_counts": actual_fold_evidence,
        "natural_eligibility": {str(p): count for p, count in natural_counts.items()},
        "common_lag_fold_counts": [
            {
                "fold": fold.fold,
                "train_samples": len(fold.train.X),
                "validation_samples": len(fold.validation.X),
                "validation_start": fold.validation_start.strftime(DATETIME_FORMAT),
                "validation_end_exclusive": fold.validation_end_exclusive.strftime(
                    DATETIME_FORMAT
                ),
            }
            for fold in lag_folds[168]
        ],
        "holdout_accessed": False,
        "holdout_features_materialized": False,
        "holdout_evaluated": False,
    }
    return contract, official_folds, lag_folds, official_xgboost, evidence


def dependency_smoke_test() -> dict[str, Any]:
    """Fit both estimator types only on tiny synthetic arrays."""

    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from xgboost import XGBRegressor

    X = np.arange(120, dtype="float64").reshape(40, 3)
    y = np.linspace(0.0, 1.0, 40)
    linear = Pipeline(
        [("scaler", StandardScaler()), ("model", LinearRegression())]
    ).fit(X, y)
    xgboost = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=2,
        max_depth=2,
        random_state=42,
        n_jobs=1,
        verbosity=0,
    ).fit(X, y)
    predictions = np.concatenate([linear.predict(X[:2]), xgboost.predict(X[:2])])
    if not np.isfinite(predictions).all():
        raise ValueError("Supplemental dependency smoke predictions are non-finite.")
    return {"versions": package_versions(), "synthetic_fit_predict": "PASS"}


def run_preflight(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Validate scientific inputs without fitting any project-data estimator."""

    contract, folds, lag_folds, _official_xgboost, evidence = load_supplemental_inputs(
        project_root
    )
    dependency = dependency_smoke_test()
    official_outputs_exist = {
        name: (Path(project_root) / path).exists()
        for name, path in contract["outputs"].items()
    }
    return {
        "phase": contract["phase"],
        "dependency_gate": dependency,
        "linear_folds": len(folds),
        "linear_features": len(evidence["official_feature_order"]),
        "lag_p_values": EXPECTED_P_VALUES,
        "lag_common_fold_counts": evidence["common_lag_fold_counts"],
        "natural_eligibility": evidence["natural_eligibility"],
        "planned_project_data_fits": EXPECTED_PROJECT_FITS,
        "training_started": False,
        "holdout_accessed": False,
        "holdout_evaluated": False,
        "official_outputs_exist": official_outputs_exist,
        "status": "PASS",
    }


def _execution_identity(contract: dict[str, Any], evidence: dict[str, Any]) -> str:
    payload = {
        "contract": contract,
        "verified_upstream_sha256": evidence["verified_upstream_sha256"],
        "prepared_sha256": evidence["prepared_sha256"],
        "package_versions": evidence["package_versions"],
        "official_feature_order": evidence["official_feature_order"],
        "official_fold_counts": evidence["official_fold_counts"],
        "natural_eligibility": evidence["natural_eligibility"],
        "common_lag_fold_counts": evidence["common_lag_fold_counts"],
    }
    return sha256(_canonical_json(payload)).hexdigest()[:8]


def initialize_run(
    project_root: Path,
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[Path, Path, dict[str, Any]]:
    """Initialize a resumable Human-owned supplemental run."""

    identity = _execution_identity(contract, evidence)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    run_id = f"P6_supplemental_{timestamp}_{identity}"
    run_dir = Path(project_root) / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    log_path = run_dir / f"{run_id}.log"
    metadata = {
        "run_id": run_id,
        "execution_identity": identity,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "executor": "human_terminal_only",
        "package_versions": package_versions(),
        "upstream_evidence": evidence,
    }
    checkpoint = {
        "run_id": run_id,
        "execution_identity": identity,
        "status": "READY",
        "completed_tasks": [],
        "expected_project_data_fits": EXPECTED_PROJECT_FITS,
        "official_outputs_promoted": False,
        "holdout_accessed": False,
        "holdout_evaluated": False,
    }
    atomic_write_json(contract, run_dir / "config_snapshot.json")
    atomic_write_json(metadata, run_dir / "run_metadata.json")
    atomic_write_json(checkpoint, run_dir / "checkpoint.json")
    atomic_write_json(
        {
            "candidate": contract["linear_regression"]["candidate"],
            "fold_metrics": [],
            "status": "PENDING",
        },
        run_dir / RUN_LINEAR_FILE,
    )
    atomic_write_json(
        {"p_values": EXPECTED_P_VALUES, "p_results": [], "status": "PENDING"},
        run_dir / RUN_LAG_FILE,
    )
    append_run_log(log_path, "INFO", "Phase 6 supplemental run initialized.")
    return run_dir, log_path, checkpoint


def validate_resume_identity(
    run_dir: Path,
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    """Reject a resume if any approved scientific input changed."""

    run_dir = Path(run_dir).resolve()
    checkpoint = read_json_document(run_dir / "checkpoint.json")
    metadata = read_json_document(run_dir / "run_metadata.json")
    snapshot = read_json_document(run_dir / "config_snapshot.json")
    expected_identity = _execution_identity(contract, evidence)
    if snapshot != contract:
        raise ValueError("Supplemental run configuration changed.")
    if checkpoint["execution_identity"] != expected_identity:
        raise ValueError("Supplemental checkpoint identity changed.")
    if metadata["upstream_evidence"] != evidence:
        raise ValueError("Supplemental upstream evidence changed.")
    if checkpoint.get("official_outputs_promoted"):
        raise ValueError("Completed supplemental run must not be resumed.")
    return run_dir / f"{checkpoint['run_id']}.log", checkpoint


def _replace_fold_record(records: list[dict[str, Any]], record: dict[str, Any]) -> None:
    records[:] = [item for item in records if int(item["fold"]) != int(record["fold"])]
    records.append(record)
    records.sort(key=lambda item: int(item["fold"]))


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


def fit_linear_fold(
    fold: SupervisedFold,
) -> tuple[dict[str, Any], dict[str, list[float]]]:
    """Fit the approved fold-local scaled Linear Regression benchmark."""

    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    pipeline = Pipeline(
        [("scaler", StandardScaler()), ("model", LinearRegression())]
    )
    started = time.perf_counter()
    pipeline.fit(fold.train.X, fold.train.y)
    validation_prediction = np.asarray(
        pipeline.predict(fold.validation.X), dtype="float64"
    )
    train_prediction = np.asarray(pipeline.predict(fold.train.X), dtype="float64")
    duration = time.perf_counter() - started
    validation_metrics = regression_metrics(
        fold.validation.y.to_numpy(), validation_prediction
    )
    train_metrics = regression_metrics(fold.train.y.to_numpy(), train_prediction)
    scaler = pipeline.named_steps["scaler"]
    record = {
        "fold": fold.fold,
        **validation_metrics,
        "train_mae": train_metrics["mae"],
        "generalization_gap_mae": validation_metrics["mae"] - train_metrics["mae"],
        "duration_seconds": float(duration),
        "train_samples": len(fold.train.X),
        "validation_start": fold.validation_start.strftime(DATETIME_FORMAT),
        "validation_end_exclusive": fold.validation_end_exclusive.strftime(
            DATETIME_FORMAT
        ),
    }
    scaler_evidence = {
        "mean": np.asarray(scaler.mean_, dtype="float64").tolist(),
        "scale": np.asarray(scaler.scale_, dtype="float64").tolist(),
    }
    return record, scaler_evidence


def evaluate_linear_regression(
    folds: list[SupervisedFold],
    official_xgboost: dict[str, Any],
    run_dir: Path,
    log_path: Path,
    checkpoint: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate five fold-local Linear Regression fits with checkpointing."""

    path = run_dir / RUN_LINEAR_FILE
    result = read_json_document(path)
    result.update(
        {
            "candidate": "linear_regression_scaled",
            "pipeline": ["StandardScaler", "LinearRegression"],
            "scaler_fit_scope": "fold_train_only",
            "feature_count": EXPECTED_FEATURE_COUNT,
            "feature_order": folds[0].train.X.columns.tolist(),
            "status": "RUNNING",
        }
    )
    result.setdefault("scaler_evidence", [])
    for fold in folds:
        task = f"linear_regression:fold:{fold.fold}"
        if task in checkpoint["completed_tasks"]:
            continue
        append_run_log(log_path, "INFO", f"Linear Regression fold {fold.fold}/5 started.")
        record, scaler = fit_linear_fold(fold)
        _replace_fold_record(result["fold_metrics"], record)
        result["scaler_evidence"] = [
            item for item in result["scaler_evidence"] if item["fold"] != fold.fold
        ]
        result["scaler_evidence"].append({"fold": fold.fold, **scaler})
        result["scaler_evidence"].sort(key=lambda item: int(item["fold"]))
        atomic_write_json(result, path)
        _checkpoint_task(run_dir, checkpoint, task)
        append_run_log(
            log_path,
            "INFO",
            f"Linear Regression fold {fold.fold}/5 completed: MAE={record['mae']:.6f} RMSE={record['rmse']:.6f} time={record['duration_seconds']:.3f}s.",
        )
    result["aggregate"] = aggregate_fold_metrics(result["fold_metrics"])
    xgb_reference = {
        "candidate": official_xgboost["candidate"],
        "retrained": False,
        "fold_metrics": deepcopy(official_xgboost["fold_metrics"]),
        "aggregate": deepcopy(official_xgboost["aggregate"]),
    }
    result["official_xgboost_reference"] = xgb_reference
    result["comparison"] = {
        "linear_minus_xgboost_mean_cv_mae": (
            result["aggregate"]["mean_cv_mae"]
            - xgb_reference["aggregate"]["mean_cv_mae"]
        ),
        "linear_minus_xgboost_mean_cv_rmse": (
            result["aggregate"]["mean_cv_rmse"]
            - xgb_reference["aggregate"]["mean_cv_rmse"]
        ),
        "same_validation_samples": (
            result["aggregate"]["validation_samples"]
            == xgb_reference["aggregate"]["validation_samples"]
        ),
    }
    result["total_fit_duration_seconds"] = float(
        sum(record["duration_seconds"] for record in result["fold_metrics"])
    )
    result["holdout_evaluated"] = False
    result["status"] = "PASS"
    atomic_write_json(result, path)
    return result


def fit_lag_fold(
    fold: SupervisedFold,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Fit one fixed-parameter XGBoost lag-sensitivity fold."""

    from xgboost import XGBRegressor

    started = time.perf_counter()
    estimator = XGBRegressor(**parameters, verbosity=0)
    estimator.fit(fold.train.X, fold.train.y)
    validation_prediction = np.asarray(
        estimator.predict(fold.validation.X), dtype="float64"
    )
    train_prediction = np.asarray(estimator.predict(fold.train.X), dtype="float64")
    duration = time.perf_counter() - started
    validation_metrics = regression_metrics(
        fold.validation.y.to_numpy(), validation_prediction
    )
    train_metrics = regression_metrics(fold.train.y.to_numpy(), train_prediction)
    return {
        "fold": fold.fold,
        **validation_metrics,
        "train_mae": train_metrics["mae"],
        "generalization_gap_mae": validation_metrics["mae"] - train_metrics["mae"],
        "duration_seconds": float(duration),
        "train_samples": len(fold.train.X),
        "validation_start": fold.validation_start.strftime(DATETIME_FORMAT),
        "validation_end_exclusive": fold.validation_end_exclusive.strftime(
            DATETIME_FORMAT
        ),
    }


def _p_result(result: dict[str, Any], p: int, natural_count: int) -> dict[str, Any]:
    matches = [item for item in result["p_results"] if int(item["p"]) == p]
    if len(matches) > 1:
        raise ValueError(f"Duplicate lag-p result for p={p}.")
    if matches:
        return matches[0]
    record = {
        "p": p,
        "feature_count": p,
        "feature_order": [f"lag_{lag}h" for lag in range(1, p + 1)],
        "natural_eligible_samples": natural_count,
        "fold_metrics": [],
        "status": "RUNNING",
    }
    result["p_results"].append(record)
    result["p_results"].sort(key=lambda item: EXPECTED_P_VALUES.index(int(item["p"])))
    return record


def evaluate_lag_sensitivity(
    contract: dict[str, Any],
    lag_folds: dict[int, list[SupervisedFold]],
    evidence: dict[str, Any],
    run_dir: Path,
    log_path: Path,
    checkpoint: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate all six fixed lag registries on one common population."""

    path = run_dir / RUN_LAG_FILE
    result = read_json_document(path)
    result.update(
        {
            "model": "xgboost_tuned_locked_parameters",
            "parameters": deepcopy(contract["lag_sensitivity"]["parameters"]),
            "population": "common_p168_eligible_timestamps",
            "imputation": "none",
            "tuning": False,
            "status": "RUNNING",
        }
    )
    for p in EXPECTED_P_VALUES:
        record = _p_result(
            result, p, int(evidence["natural_eligibility"][str(p)])
        )
        for fold in lag_folds[p]:
            task = f"lag_p:{p}:fold:{fold.fold}"
            if task in checkpoint["completed_tasks"]:
                continue
            append_run_log(log_path, "INFO", f"Lag p={p} fold {fold.fold}/5 started.")
            fold_record = fit_lag_fold(
                fold, contract["lag_sensitivity"]["parameters"]
            )
            _replace_fold_record(record["fold_metrics"], fold_record)
            atomic_write_json(result, path)
            _checkpoint_task(run_dir, checkpoint, task)
            append_run_log(
                log_path,
                "INFO",
                f"Lag p={p} fold {fold.fold}/5 completed: MAE={fold_record['mae']:.6f} RMSE={fold_record['rmse']:.6f} time={fold_record['duration_seconds']:.3f}s.",
            )
        record["aggregate"] = aggregate_fold_metrics(record["fold_metrics"])
        record["mean_train_mae"] = float(
            np.mean([item["train_mae"] for item in record["fold_metrics"]])
        )
        record["mean_generalization_gap_mae"] = (
            record["aggregate"]["mean_cv_mae"] - record["mean_train_mae"]
        )
        record["total_fit_duration_seconds"] = float(
            sum(item["duration_seconds"] for item in record["fold_metrics"])
        )
        record["status"] = "PASS"
        atomic_write_json(result, path)
    baseline = result["p_results"][0]
    previous: dict[str, Any] | None = None
    for record in result["p_results"]:
        record["change_from_p1"] = {
            "mean_cv_mae": record["aggregate"]["mean_cv_mae"]
            - baseline["aggregate"]["mean_cv_mae"],
            "mean_cv_rmse": record["aggregate"]["mean_cv_rmse"]
            - baseline["aggregate"]["mean_cv_rmse"],
        }
        record["change_from_previous_p"] = None if previous is None else {
            "previous_p": previous["p"],
            "mean_cv_mae": record["aggregate"]["mean_cv_mae"]
            - previous["aggregate"]["mean_cv_mae"],
            "mean_cv_rmse": record["aggregate"]["mean_cv_rmse"]
            - previous["aggregate"]["mean_cv_rmse"],
        }
        previous = record
    result["common_fold_counts"] = evidence["common_lag_fold_counts"]
    result["total_fit_duration_seconds"] = float(
        sum(item["total_fit_duration_seconds"] for item in result["p_results"])
    )
    result["holdout_evaluated"] = False
    result["status"] = "PASS"
    atomic_write_json(result, path)
    return result


def _validate_complete_results(
    linear_result: dict[str, Any],
    lag_result: dict[str, Any],
    checkpoint: dict[str, Any],
) -> None:
    if linear_result.get("status") != "PASS" or lag_result.get("status") != "PASS":
        raise ValueError("Supplemental results are incomplete.")
    if len(linear_result["fold_metrics"]) != EXPECTED_FOLDS:
        raise ValueError("Linear Regression does not contain five folds.")
    if [item["p"] for item in lag_result["p_results"]] != EXPECTED_P_VALUES:
        raise ValueError("Lag-p results do not contain the approved registry.")
    if any(len(item["fold_metrics"]) != EXPECTED_FOLDS for item in lag_result["p_results"]):
        raise ValueError("A lag-p result does not contain five folds.")
    if len(checkpoint["completed_tasks"]) != EXPECTED_PROJECT_FITS:
        raise ValueError("Checkpoint does not contain all 35 project-data fits.")


def promote_official_bundle(
    project_root: Path,
    contract: dict[str, Any],
    evidence: dict[str, Any],
    metadata: dict[str, Any],
    linear_result: dict[str, Any],
    lag_result: dict[str, Any],
    run_dir: Path,
) -> dict[str, Any]:
    """Promote a validated bundle atomically enough for audit-last semantics."""

    outputs = contract["outputs"]
    official_paths = {name: Path(project_root) / path for name, path in outputs.items()}
    existing = [str(path) for path in official_paths.values() if path.exists()]
    if existing:
        raise FileExistsError(f"Supplemental official output already exists: {existing}")
    staging = run_dir / "official_bundle"
    staging.mkdir(parents=True, exist_ok=True)
    staged_linear = staging / Path(outputs["linear_regression"]).name
    staged_lag = staging / Path(outputs["lag_sensitivity"]).name
    staged_model_figure = staging / Path(outputs["model_comparison_figure"]).name
    staged_lag_figure = staging / Path(outputs["lag_sensitivity_figure"]).name
    atomic_write_json(linear_result, staged_linear)
    atomic_write_json(lag_result, staged_lag)
    save_model_comparison_figure(linear_result, staged_model_figure)
    save_lag_sensitivity_figure(lag_result, staged_lag_figure)
    component_hashes = {
        "linear_regression": calculate_sha256(staged_linear),
        "lag_sensitivity": calculate_sha256(staged_lag),
        "model_comparison_figure": calculate_sha256(staged_model_figure),
        "lag_sensitivity_figure": calculate_sha256(staged_lag_figure),
    }
    audit = {
        "phase": contract["phase"],
        "contract_version": contract["contract_version"],
        "evidence_label": contract["evidence_label"],
        "timing_disclosure": "designed_after_historical_holdout_evaluation",
        "run_id": metadata["run_id"],
        "execution_identity": metadata["execution_identity"],
        "upstream_evidence": evidence,
        "completed_project_data_fits": EXPECTED_PROJECT_FITS,
        "component_sha256": component_hashes,
        "checks": {
            "development_only": True,
            "holdout_accessed": False,
            "holdout_evaluated": False,
            "model_lock_changed": False,
            "selection_authority": "none",
            "xgboost_reference_retrained": False,
            "tuning_performed": False,
            "binary_model_persisted": False,
        },
        "status": "PASS",
    }
    staged_audit = staging / Path(outputs["audit"]).name
    atomic_write_json(audit, staged_audit)
    promoted: list[Path] = []
    try:
        for name in [
            "linear_regression",
            "lag_sensitivity",
            "model_comparison_figure",
            "lag_sensitivity_figure",
        ]:
            destination = official_paths[name]
            destination.parent.mkdir(parents=True, exist_ok=True)
            source = staging / destination.name
            shutil.copy2(source, destination)
            if calculate_sha256(destination) != component_hashes[name]:
                raise ValueError(f"Promoted supplemental output hash mismatch: {name}.")
            promoted.append(destination)
        audit_destination = official_paths["audit"]
        audit_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(staged_audit, audit_destination)
        if read_json_document(audit_destination) != audit:
            raise ValueError("Promoted supplemental audit validation failed.")
        promoted.append(audit_destination)
    except BaseException:
        for path in promoted:
            path.unlink(missing_ok=True)
        raise
    return audit


def run_supplemental(
    project_root: Path = PROJECT_ROOT,
    resume_run_dir: Path | None = None,
) -> dict[str, Any]:
    """Run all Human-authorized supplemental fits and promote official evidence."""

    project_root = Path(project_root).resolve()
    contract, folds, lag_folds, official_xgboost, evidence = load_supplemental_inputs(
        project_root
    )
    dependency_smoke_test()
    existing_official = [
        str(project_root / path)
        for path in contract["outputs"].values()
        if (project_root / path).exists()
    ]
    if existing_official:
        raise FileExistsError(
            "Supplemental official outputs already exist; refusing to retrain or "
            f"overwrite them: {existing_official}"
        )
    if resume_run_dir is None:
        run_dir, log_path, checkpoint = initialize_run(project_root, contract, evidence)
        append_run_log(log_path, "INFO", "Phase 6 supplemental execution started.")
    else:
        run_dir = Path(resume_run_dir).resolve()
        log_path, checkpoint = validate_resume_identity(run_dir, contract, evidence)
        checkpoint["status"] = "RUNNING"
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "INFO", "Phase 6 supplemental run resumed.")
    metadata = read_json_document(run_dir / "run_metadata.json")
    try:
        linear_result = evaluate_linear_regression(
            folds, official_xgboost, run_dir, log_path, checkpoint
        )
        lag_result = evaluate_lag_sensitivity(
            contract, lag_folds, evidence, run_dir, log_path, checkpoint
        )
        _validate_complete_results(linear_result, lag_result, checkpoint)
        audit = promote_official_bundle(
            project_root,
            contract,
            evidence,
            metadata,
            linear_result,
            lag_result,
            run_dir,
        )
        checkpoint["status"] = "COMPLETED"
        checkpoint["official_outputs_promoted"] = True
        checkpoint["holdout_accessed"] = False
        checkpoint["holdout_evaluated"] = False
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "INFO", "Phase 6 supplemental execution completed.")
        return {
            "run_dir": str(run_dir.relative_to(project_root)),
            "completed_project_data_fits": audit["completed_project_data_fits"],
            "linear_regression": contract["outputs"]["linear_regression"],
            "lag_sensitivity": contract["outputs"]["lag_sensitivity"],
            "audit": contract["outputs"]["audit"],
            "selection_authority": "none",
            "model_lock_changed": False,
            "holdout_evaluated": False,
            "status": "PASS",
        }
    except KeyboardInterrupt:
        checkpoint["status"] = "INTERRUPTED"
        checkpoint["official_outputs_promoted"] = False
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "WARNING", "Supplemental execution interrupted by Human.")
        raise
    except Exception as error:
        checkpoint["status"] = "FAILED"
        checkpoint["official_outputs_promoted"] = False
        checkpoint["last_error"] = f"{type(error).__name__}: {error}"
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(
            log_path,
            "ERROR",
            f"Supplemental execution failed: {type(error).__name__}: {error}",
        )
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--preflight",
        action="store_true",
        help="Validate dependencies and inputs without project-data training.",
    )
    actions.add_argument(
        "--run",
        action="store_true",
        help="Start a new Human-authorized 35-fit supplemental run.",
    )
    actions.add_argument(
        "--resume-supplemental",
        type=Path,
        help="Resume an interrupted supplemental run after identity validation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.preflight:
        result = run_preflight()
    elif args.run:
        result = run_supplemental()
    else:
        result = run_supplemental(resume_run_dir=args.resume_supplemental)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
