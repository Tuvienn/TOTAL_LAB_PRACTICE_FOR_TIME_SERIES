"""Human-gated Phase 7 final forecasting and evaluation pipeline."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
from typing import Any

import numpy as np
import pandas as pd

from practice_3.analysis.evaluation import (
    ONE_STEP_COLUMNS,
    RECURSIVE_COLUMNS,
    atomic_write_csv,
    attach_error_columns,
    build_one_step_metrics,
    build_recursive_metrics,
    validate_one_step_predictions,
    validate_recursive_predictions,
)
from practice_3.analysis.feature_engineering import (
    build_feature_row_from_history,
    build_time_safe_features,
)
from practice_3.analysis.model_training import (
    append_run_log,
    atomic_write_json,
    dependency_smoke_test,
    package_versions,
    read_json_document,
)
from practice_3.data.data_preparation import calculate_sha256, load_json_contract
from practice_3.data.supervised_dataset import (
    PROJECT_ROOT,
    build_supervised_candidates,
    extract_eligible_xy,
    load_phase_05_inputs,
)
from practice_3.data.temporal_split import (
    build_development_holdout_masks,
    validate_prepared_input,
)
from practice_3.visualization.forecast_evaluation import (
    save_one_step_figure,
    save_recursive_horizon_figure,
)


EXPECTED_CANDIDATES = ["persistence", "seasonal_naive_24", "xgboost_tuned"]
EXPECTED_DEVELOPMENT_SAMPLES = 108_083
EXPECTED_FEATURE_COUNT = 22
EXPECTED_HOLDOUT_ROWS = 8_761
EXPECTED_ONE_STEP_ROWS = 8_592
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def seasonal_naive_24_values(
    target: pd.Series,
    target_timestamps: pd.DatetimeIndex,
    *,
    forecast_origin: pd.Timestamp | None = None,
) -> pd.Series:
    """Return the 24-hour seasonal-naive source value for each target timestamp.

    The lookup is timestamp-based (``y[t - 24h]``), never positional.  For a
    recursive forecast, ``forecast_origin`` additionally guards against using
    a source timestamp that occurs after the forecast origin.
    """

    timestamps = pd.DatetimeIndex(target_timestamps)
    source_timestamps = timestamps - pd.Timedelta(hours=24)
    if forecast_origin is not None and len(source_timestamps):
        if source_timestamps.max() > pd.Timestamp(forecast_origin):
            raise ValueError(
                "Seasonal-naive 24h lookup would use a value after the forecast origin."
            )
    return target.reindex(source_timestamps)


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def validate_final_evaluation_contract(contract: dict[str, Any]) -> None:
    """Reject changes to the Human-approved Phase 7 protocol."""

    if contract.get("status") != "APPROVED":
        raise ValueError("Final-evaluation contract must be approved.")
    upstream = contract["upstream"]
    if (
        upstream["selected_candidate"] != "xgboost_tuned"
        or upstream["development_eligible_samples"] != EXPECTED_DEVELOPMENT_SAMPLES
        or upstream["feature_count"] != EXPECTED_FEATURE_COUNT
    ):
        raise ValueError("Phase 7 upstream identity contract changed.")
    if contract["candidate_registry"] != EXPECTED_CANDIDATES:
        raise ValueError("Phase 7 candidate registry changed.")
    one_step = contract["one_step"]
    if one_step != {
        "strategy": "rolling_observed_history",
        "horizon_hours": 1,
        "expected_holdout_rows": EXPECTED_HOLDOUT_ROWS,
        "expected_common_eligible_rows": EXPECTED_ONE_STEP_ROWS,
        "start_inclusive": "2017-08-03 00:00:00",
        "end_inclusive": "2018-08-03 00:00:00",
        "imputation": "none",
        "same_timestamps_for_all_candidates": True,
    }:
        raise ValueError("One-step evaluation protocol changed.")
    recursive = contract["recursive"]
    if recursive != {
        "strategy": "recursive",
        "horizon_hours": 24,
        "origin_hour": 23,
        "origin_spacing_hours": 24,
        "require_complete_target_block": True,
        "target_windows_overlap": False,
        "same_origins_for_all_candidates": True,
        "allow_actual_future_target_in_history": False,
    }:
        raise ValueError("Recursive evaluation protocol changed.")
    if contract["metrics"] != {
        "primary": "mae",
        "secondary": "rmse",
        "recursive_per_horizon": True,
        "recursive_pooled": True,
    }:
        raise ValueError("Phase 7 metric contract changed.")
    if contract["visualization"] != {
        "diagnostic_start": "2017-08-03 00:00:00",
        "diagnostic_end": "2017-08-16 23:00:00",
    }:
        raise ValueError("Phase 7 fixed visualization window changed.")
    execution = contract["execution"]
    if (
        execution["executor"] != "human_terminal_only"
        or execution["checkpoint"] is not True
        or execution["atomic_promotion"] is not True
        or execution["binary_model_persisted"] is not False
        or execution["run_directory_pattern"]
        != "runs/P7_final_evaluation_<timestamp>_<execution_identity>"
    ):
        raise ValueError("Phase 7 execution boundary changed.")
    scope = contract["scope"]
    if scope != {
        "holdout_label": "historical_re_evaluation_holdout",
        "holdout_is_claimed_unseen": False,
        "post_holdout_model_change_allowed": False,
        "error_interpretation_owner": "phase_08",
    }:
        raise ValueError("Phase 7 claim boundary changed.")
    if contract["outputs"] != {
        "one_step_predictions": "outputs/results/phase_07_one_step_predictions.csv",
        "one_step_metrics": "outputs/results/phase_07_one_step_metrics.json",
        "recursive_predictions": "outputs/results/phase_07_recursive_predictions.csv",
        "recursive_metrics": "outputs/results/phase_07_recursive_metrics.json",
        "evaluation_audit": "outputs/results/phase_07_evaluation_audit.json",
        "one_step_full_figure": "outputs/figures/phase_07_one_step_full_holdout.png",
        "one_step_diagnostic_figure": "outputs/figures/phase_07_one_step_first_14_days.png",
        "recursive_horizon_figure": "outputs/figures/phase_07_recursive_error_by_horizon.png",
    }:
        raise ValueError("Phase 7 output ownership changed.")


def load_phase_07_preflight_inputs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Validate Phase 7 identities without materializing holdout targets."""

    project_root = Path(project_root).resolve()
    contract = load_json_contract(project_root / "config/final_evaluation.json")
    validate_final_evaluation_contract(contract)
    upstream = contract["upstream"]
    cv_path = project_root / upstream["phase_06_cv_results"]
    lock_path = project_root / upstream["phase_06_model_lock"]
    if calculate_sha256(cv_path) != upstream["phase_06_cv_results_sha256"]:
        raise ValueError("Phase 6 CV-results SHA-256 changed.")
    if calculate_sha256(lock_path) != upstream["phase_06_model_lock_sha256"]:
        raise ValueError("Phase 6 model-lock SHA-256 changed.")
    cv_results = read_json_document(cv_path)
    model_lock = read_json_document(lock_path)
    if cv_results.get("status") != "PASS" or model_lock.get("status") != "PASS":
        raise ValueError("Phase 6 official artifacts must have PASS status.")
    if (
        cv_results["selected_candidate"] != "xgboost_tuned"
        or model_lock["selected_candidate"] != "xgboost_tuned"
        or model_lock["selected_kind"] != "xgboost"
    ):
        raise ValueError("Phase 6 selected candidate no longer matches Phase 7.")
    if model_lock["upstream_identities"]["cv_results_sha256"] != calculate_sha256(
        cv_path
    ):
        raise ValueError("Model lock does not link to the current CV results.")
    if len(model_lock["feature_order"]) != EXPECTED_FEATURE_COUNT:
        raise ValueError("Model lock must contain exactly 22 ordered features.")
    if model_lock["holdout_evaluated"] is not False:
        raise ValueError("Holdout was evaluated before Phase 7.")
    if model_lock["binary_model_persisted"] is not False:
        raise ValueError("Phase 6 unexpectedly persisted a binary model.")
    if model_lock["package_versions"] != package_versions():
        raise ValueError("Current package versions do not match the model lock.")
    phase_05_path = project_root / "outputs/results/phase_05_supervised_dataset.json"
    if calculate_sha256(phase_05_path) != model_lock["upstream_identities"][
        "phase_05_audit_sha256"
    ]:
        raise ValueError("Phase 5 audit identity changed after model lock.")
    phase_05_audit = read_json_document(phase_05_path)
    if (
        phase_05_audit.get("status") != "PASS"
        or phase_05_audit["development"]["eligible_rows"]
        != EXPECTED_DEVELOPMENT_SAMPLES
        or phase_05_audit["feature_order"] != model_lock["feature_order"]
    ):
        raise ValueError("Phase 5 development evidence changed.")
    prepared_path = project_root / phase_05_audit["prepared_input"]
    if calculate_sha256(prepared_path) != model_lock["upstream_identities"][
        "prepared_sha256"
    ]:
        raise ValueError("Prepared-data identity changed after model lock.")
    evidence = {
        "phase_05_audit_sha256": calculate_sha256(phase_05_path),
        "phase_06_cv_results_sha256": calculate_sha256(cv_path),
        "phase_06_model_lock_sha256": calculate_sha256(lock_path),
        "prepared_sha256": calculate_sha256(prepared_path),
        "development_eligible_samples": EXPECTED_DEVELOPMENT_SAMPLES,
        "feature_order": deepcopy(model_lock["feature_order"]),
        "locked_parameters": deepcopy(model_lock["locked_parameters"]),
        "package_versions": deepcopy(model_lock["package_versions"]),
        "holdout_opened": False,
    }
    return contract, cv_results, model_lock, evidence


def run_preflight(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Run Phase 7 gates without opening or evaluating holdout targets."""

    contract, _cv_results, model_lock, evidence = load_phase_07_preflight_inputs(
        project_root
    )
    dependency = dependency_smoke_test()
    return {
        "phase": contract["phase"],
        "selected_candidate": model_lock["selected_candidate"],
        "candidate_registry": deepcopy(contract["candidate_registry"]),
        "development_eligible_samples": evidence["development_eligible_samples"],
        "feature_count": len(evidence["feature_order"]),
        "dependency_gate": dependency,
        "holdout_opened": False,
        "evaluation_started": False,
        "status": "PASS",
    }


def _execution_identity(contract: dict[str, Any], evidence: dict[str, Any]) -> str:
    payload = {
        "contract": contract,
        "phase_05_audit_sha256": evidence["phase_05_audit_sha256"],
        "phase_06_cv_results_sha256": evidence["phase_06_cv_results_sha256"],
        "phase_06_model_lock_sha256": evidence["phase_06_model_lock_sha256"],
        "prepared_sha256": evidence["prepared_sha256"],
        "feature_order": evidence["feature_order"],
        "package_versions": evidence["package_versions"],
    }
    return sha256(_canonical_json(payload)).hexdigest()[:8]


def initialize_run(
    project_root: Path,
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[Path, Path, dict[str, Any]]:
    """Create a new Human-owned final-evaluation run."""

    identity = _execution_identity(contract, evidence)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    run_id = f"P7_final_evaluation_{timestamp}_{identity}"
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
        "official_outputs_promoted": False,
        "holdout_opened": False,
    }
    atomic_write_json(contract, run_dir / "config_snapshot.json")
    atomic_write_json(metadata, run_dir / "run_metadata.json")
    atomic_write_json(checkpoint, run_dir / "checkpoint.json")
    append_run_log(log_path, "INFO", "Phase 7 final evaluation initialized.")
    return run_dir, log_path, checkpoint


def validate_resume_identity(
    run_dir: Path,
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    """Reject a resume when any locked scientific identity changed."""

    run_dir = Path(run_dir).resolve()
    checkpoint = read_json_document(run_dir / "checkpoint.json")
    metadata = read_json_document(run_dir / "run_metadata.json")
    snapshot = read_json_document(run_dir / "config_snapshot.json")
    expected_identity = _execution_identity(contract, evidence)
    if snapshot != contract:
        raise ValueError("Run configuration no longer matches Phase 7 contract.")
    if checkpoint["execution_identity"] != expected_identity:
        raise ValueError("Checkpoint identity does not match current Phase 7 inputs.")
    if metadata["upstream_evidence"] != evidence:
        raise ValueError("Run upstream evidence no longer matches current inputs.")
    if checkpoint.get("official_outputs_promoted"):
        raise ValueError("Completed official Phase 7 run must not be resumed.")
    return run_dir / f"{checkpoint['run_id']}.log", checkpoint


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


def _load_evaluation_data(
    project_root: Path,
) -> tuple[
    pd.DataFrame,
    pd.Series,
    pd.Series,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
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
    prepared, _prepared_sha256 = validate_prepared_input(
        project_root / supervised_contract["prepared_input"],
        data_contract,
        preparation_contract,
        split_contract,
        phase_01_audit,
    )
    development_mask, holdout_mask = build_development_holdout_masks(
        prepared,
        data_contract,
        split_contract,
    )
    if int(development_mask.sum()) != 112_535:
        raise ValueError("Development structural population changed.")
    if int(holdout_mask.sum()) != EXPECTED_HOLDOUT_ROWS:
        raise ValueError("Holdout structural population changed.")
    return (
        prepared,
        development_mask,
        holdout_mask,
        data_contract,
        split_contract,
        {"feature": feature_contract, "supervised": supervised_contract},
    )


def build_full_development_partition(
    prepared: pd.DataFrame,
    development_mask: pd.Series,
    data_contract: dict[str, Any],
    contracts: dict[str, Any],
) -> tuple[pd.DataFrame, pd.Series]:
    """Reconstruct the exact full-development X/y population for refit."""

    development = prepared.loc[development_mask].reset_index(drop=True)
    candidates = build_supervised_candidates(
        development,
        data_contract,
        contracts["feature"],
        contracts["supervised"],
    )
    partition = extract_eligible_xy(
        candidates,
        pd.Series(True, index=candidates.index),
        data_contract,
        contracts["supervised"],
    )
    if len(partition.X) != EXPECTED_DEVELOPMENT_SAMPLES:
        raise ValueError("Full-development eligible population changed.")
    if partition.X.columns.tolist() != contracts["supervised"]["feature_order"]:
        raise ValueError("Full-development feature order changed.")
    return partition.X, partition.y


def build_one_step_predictions(
    estimator: Any,
    prepared: pd.DataFrame,
    holdout_mask: pd.Series,
    data_contract: dict[str, Any],
    feature_contract: dict[str, Any],
    candidate_registry: list[str],
) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    """Build common-population rolling one-step predictions."""

    features = build_time_safe_features(prepared, data_contract, feature_contract)
    target = prepared[data_contract["target_column"]].astype("float64")
    feature_values = features.to_numpy(dtype="float64")
    eligible = (
        holdout_mask
        & target.notna()
        & np.isfinite(target)
        & pd.Series(np.isfinite(feature_values).all(axis=1), index=prepared.index)
    )
    selected_features = features.loc[eligible, feature_contract["feature_order"]]
    actual = target.loc[eligible].to_numpy(dtype="float64")
    timestamps = pd.DatetimeIndex(prepared.loc[eligible, data_contract["timestamp_column"]])
    if len(timestamps) != EXPECTED_ONE_STEP_ROWS:
        raise ValueError(
            f"One-step common population must contain {EXPECTED_ONE_STEP_ROWS} rows; "
            f"got {len(timestamps)}."
        )
    target_by_timestamp = pd.Series(
        target.to_numpy(dtype="float64"),
        index=pd.DatetimeIndex(prepared[data_contract["timestamp_column"]]),
    )
    seasonal_values = seasonal_naive_24_values(target_by_timestamp, timestamps)
    lag_24_values = selected_features["lag_24h"].to_numpy(dtype="float64")
    if not np.array_equal(
        seasonal_values.to_numpy(dtype="float64"), lag_24_values, equal_nan=True
    ):
        raise ValueError("Seasonal-naive 24h lookup is misaligned with lag_24h.")
    prediction_by_candidate = {
        "persistence": selected_features["lag_1h"].to_numpy(dtype="float64"),
        "seasonal_naive_24": seasonal_values.to_numpy(dtype="float64"),
        "xgboost_tuned": np.asarray(estimator.predict(selected_features), dtype="float64"),
    }
    records: list[pd.DataFrame] = []
    for candidate in candidate_registry:
        records.append(
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "candidate": candidate,
                    "actual": actual,
                    "prediction": prediction_by_candidate[candidate],
                    "forecast_protocol": "one_step_rolling_observed_history",
                }
            )
        )
    frame = attach_error_columns(pd.concat(records, ignore_index=True))
    frame = frame.loc[:, ONE_STEP_COLUMNS]
    validate_one_step_predictions(frame, candidate_registry, timestamps)
    return frame, timestamps


def scheduled_recursive_origins(
    split_contract: dict[str, Any],
    horizon: int = 24,
) -> pd.DatetimeIndex:
    """Build fixed 23:00 daily origins whose full targets lie in holdout."""

    holdout_start = pd.Timestamp(split_contract["holdout"]["start_inclusive"])
    holdout_end = pd.Timestamp(split_contract["holdout"]["end_inclusive"])
    first_origin = holdout_start - pd.Timedelta(hours=1)
    last_origin = holdout_end - pd.Timedelta(hours=horizon)
    origins = pd.date_range(first_origin, last_origin, freq="24h")
    if not (origins.hour == 23).all():
        raise ValueError("Recursive scheduled origins must occur at 23:00.")
    return origins


def eligible_recursive_origins(
    target: pd.Series,
    scheduled_origins: pd.DatetimeIndex,
    feature_contract: dict[str, Any],
    horizon: int = 24,
) -> pd.DatetimeIndex:
    """Keep only origins with complete common candidate information."""

    eligible: list[pd.Timestamp] = []
    for origin in scheduled_origins:
        targets = pd.date_range(origin + pd.Timedelta(hours=1), periods=horizon, freq="h")
        actual = target.reindex(targets)
        seasonal = seasonal_naive_24_values(
            target, targets, forecast_origin=origin
        )
        if not np.isfinite(actual.to_numpy(dtype="float64")).all():
            continue
        if not np.isfinite(seasonal.to_numpy(dtype="float64")).all():
            continue
        if origin not in target.index or not np.isfinite(float(target.loc[origin])):
            continue
        history = target.loc[:origin].copy()
        structurally_complete = True
        for target_timestamp in targets:
            row = build_feature_row_from_history(
                history,
                target_timestamp,
                feature_contract,
            )
            if not np.isfinite(row.to_numpy(dtype="float64")).all():
                structurally_complete = False
                break
            history.loc[target_timestamp] = 0.0
        if structurally_complete:
            eligible.append(pd.Timestamp(origin))
    if not eligible:
        raise ValueError("No complete common recursive origins are eligible.")
    return pd.DatetimeIndex(eligible)


def build_recursive_predictions(
    estimator: Any,
    prepared: pd.DataFrame,
    eligible_origins: pd.DatetimeIndex,
    data_contract: dict[str, Any],
    feature_contract: dict[str, Any],
    candidate_registry: list[str],
    horizon: int = 24,
) -> pd.DataFrame:
    """Build common-origin recursive predictions without future actual updates."""

    target = prepared.set_index(data_contract["timestamp_column"])[
        data_contract["target_column"]
    ].astype("float64")
    target.index = pd.DatetimeIndex(target.index)
    records: list[dict[str, Any]] = []
    for origin in eligible_origins:
        target_timestamps = pd.date_range(
            origin + pd.Timedelta(hours=1), periods=horizon, freq="h"
        )
        actual_values = target.reindex(target_timestamps).to_numpy(dtype="float64")
        predictions: dict[str, list[float]] = {
            "persistence": [float(target.loc[origin])] * horizon,
            "seasonal_naive_24": seasonal_naive_24_values(
                target, target_timestamps, forecast_origin=origin
            ).to_numpy(dtype="float64").tolist(),
            "xgboost_tuned": [],
        }
        synthetic_history = target.loc[:origin].copy()
        for target_timestamp in target_timestamps:
            row = build_feature_row_from_history(
                synthetic_history,
                target_timestamp,
                feature_contract,
            )
            if not np.isfinite(row.to_numpy(dtype="float64")).all():
                raise ValueError("Recursive feature row contains non-finite values.")
            prediction = float(estimator.predict(row.to_frame().T)[0])
            if not np.isfinite(prediction):
                raise ValueError("Recursive model prediction is non-finite.")
            predictions["xgboost_tuned"].append(prediction)
            synthetic_history.loc[target_timestamp] = prediction
        for candidate in candidate_registry:
            for horizon_index, (target_timestamp, actual, prediction) in enumerate(
                zip(
                    target_timestamps,
                    actual_values,
                    predictions[candidate],
                    strict=True,
                ),
                start=1,
            ):
                records.append(
                    {
                        "forecast_origin": origin,
                        "horizon": horizon_index,
                        "target_timestamp": target_timestamp,
                        "candidate": candidate,
                        "actual": actual,
                        "prediction": prediction,
                        "forecast_protocol": "recursive_24_hour",
                    }
                )
    frame = attach_error_columns(pd.DataFrame.from_records(records))
    frame = frame.loc[:, RECURSIVE_COLUMNS]
    validate_recursive_predictions(
        frame,
        candidate_registry,
        eligible_origins,
        horizon=horizon,
    )
    return frame


def _build_estimator(model_lock: dict[str, Any]) -> Any:
    from xgboost import XGBRegressor

    return XGBRegressor(**model_lock["locked_parameters"])


def _load_prediction_csv(path: Path, date_columns: list[str]) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=date_columns)
    for column in date_columns:
        frame[column] = frame[column].astype("datetime64[ns]")
    return frame


def _atomic_copy(source: Path, destination: Path) -> None:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    shutil.copyfile(source, temporary)
    if calculate_sha256(temporary) != calculate_sha256(source):
        temporary.unlink(missing_ok=True)
        raise ValueError("Atomic-copy checksum validation failed.")
    os.replace(temporary, destination)


def run_final_evaluation(
    project_root: Path = PROJECT_ROOT,
    resume_run_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the Human-authorized Phase 7 historical holdout evaluation."""

    project_root = Path(project_root).resolve()
    contract, _cv_results, model_lock, evidence = load_phase_07_preflight_inputs(
        project_root
    )
    official_paths = [project_root / path for path in contract["outputs"].values()]
    official_audit = project_root / contract["outputs"]["evaluation_audit"]
    if resume_run_dir is None and official_audit.exists():
        raise ValueError("Official Phase 7 evaluation already exists; start is forbidden.")
    if resume_run_dir is None and any(path.exists() for path in official_paths):
        raise ValueError(
            "Partial Phase 7 official outputs exist without a promotion audit."
        )
    dependency_smoke_test()
    if resume_run_dir is None:
        run_dir, log_path, checkpoint = initialize_run(
            project_root, contract, evidence
        )
    else:
        run_dir = Path(resume_run_dir).resolve()
        log_path, checkpoint = validate_resume_identity(
            run_dir, contract, evidence
        )
    checkpoint["status"] = "RUNNING"
    checkpoint["holdout_opened"] = True
    opening_time = datetime.now().astimezone().isoformat(timespec="seconds")
    checkpoint["holdout_opened_at"] = opening_time
    atomic_write_json(checkpoint, run_dir / "checkpoint.json")
    append_run_log(
        log_path,
        "INFO",
        "Historical re-evaluation holdout opened after Phase 7 preflight PASS.",
    )
    try:
        (
            prepared,
            development_mask,
            holdout_mask,
            data_contract,
            split_contract,
            contracts,
        ) = _load_evaluation_data(project_root)
        X_development, y_development = build_full_development_partition(
            prepared,
            development_mask,
            data_contract,
            contracts,
        )
        estimator = _build_estimator(model_lock)
        append_run_log(
            log_path,
            "INFO",
            f"Locked XGBoost refit started on {len(X_development)} development samples.",
        )
        estimator.fit(X_development, y_development)
        _checkpoint_task(run_dir, checkpoint, "locked_model_refit")
        append_run_log(log_path, "INFO", "Locked XGBoost refit completed.")

        one_step_path = run_dir / "one_step_predictions.csv"
        if "one_step_predictions" in checkpoint["completed_tasks"]:
            one_step = _load_prediction_csv(one_step_path, ["timestamp"])
            one_step_timestamps = pd.DatetimeIndex(
                one_step.loc[one_step["candidate"].eq(EXPECTED_CANDIDATES[0]), "timestamp"]
            )
            validate_one_step_predictions(
                one_step, EXPECTED_CANDIDATES, one_step_timestamps
            )
        else:
            one_step, one_step_timestamps = build_one_step_predictions(
                estimator,
                prepared,
                holdout_mask,
                data_contract,
                contracts["feature"],
                EXPECTED_CANDIDATES,
            )
            atomic_write_csv(one_step, one_step_path)
            _checkpoint_task(run_dir, checkpoint, "one_step_predictions")
            append_run_log(
                log_path,
                "INFO",
                f"One-step evaluation completed on {len(one_step_timestamps)} common timestamps.",
            )

        target = prepared.set_index(data_contract["timestamp_column"])[
            data_contract["target_column"]
        ].astype("float64")
        scheduled_origins = scheduled_recursive_origins(split_contract)
        origins = eligible_recursive_origins(
            target,
            scheduled_origins,
            contracts["feature"],
        )
        recursive_path = run_dir / "recursive_predictions.csv"
        if "recursive_predictions" in checkpoint["completed_tasks"]:
            recursive = _load_prediction_csv(
                recursive_path, ["forecast_origin", "target_timestamp"]
            )
            validate_recursive_predictions(
                recursive, EXPECTED_CANDIDATES, origins
            )
        else:
            recursive = build_recursive_predictions(
                estimator,
                prepared,
                origins,
                data_contract,
                contracts["feature"],
                EXPECTED_CANDIDATES,
            )
            atomic_write_csv(recursive, recursive_path)
            _checkpoint_task(run_dir, checkpoint, "recursive_predictions")
            append_run_log(
                log_path,
                "INFO",
                f"Recursive evaluation completed on {len(origins)} common origins.",
            )

        one_step_metrics = build_one_step_metrics(one_step, EXPECTED_CANDIDATES)
        one_step_metrics.update(
            {
                "prediction_file": contract["outputs"]["one_step_predictions"],
                "prediction_sha256": calculate_sha256(one_step_path),
                "holdout_label": contract["scope"]["holdout_label"],
            }
        )
        recursive_metrics = build_recursive_metrics(recursive, EXPECTED_CANDIDATES)
        recursive_metrics.update(
            {
                "prediction_file": contract["outputs"]["recursive_predictions"],
                "prediction_sha256": calculate_sha256(recursive_path),
                "holdout_label": contract["scope"]["holdout_label"],
            }
        )
        local_one_step_metrics = run_dir / "one_step_metrics.json"
        local_recursive_metrics = run_dir / "recursive_metrics.json"
        atomic_write_json(one_step_metrics, local_one_step_metrics)
        atomic_write_json(recursive_metrics, local_recursive_metrics)

        full_figure = run_dir / "phase_07_one_step_full_holdout.png"
        diagnostic_figure = run_dir / "phase_07_one_step_first_14_days.png"
        recursive_figure = run_dir / "phase_07_recursive_error_by_horizon.png"
        save_one_step_figure(
            one_step,
            full_figure,
            "Phase 7 — Full Historical Holdout One-step Forecast",
        )
        save_one_step_figure(
            one_step,
            diagnostic_figure,
            "Phase 7 — Fixed First 14 Days One-step Forecast",
            pd.Timestamp(contract["visualization"]["diagnostic_start"]),
            pd.Timestamp(contract["visualization"]["diagnostic_end"]),
        )
        save_recursive_horizon_figure(recursive_metrics, recursive_figure)
        audit = {
            "phase": contract["phase"],
            "contract_version": contract["contract_version"],
            "run_id": checkpoint["run_id"],
            "opening_event": {
                "holdout_label": contract["scope"]["holdout_label"],
                "opened_at": opening_time,
                "after_preflight": True,
            },
            "upstream_evidence": evidence,
            "candidate_registry": deepcopy(EXPECTED_CANDIDATES),
            "locked_candidate": model_lock["selected_candidate"],
            "locked_parameters": deepcopy(model_lock["locked_parameters"]),
            "development_refit_samples": len(X_development),
            "one_step": {
                "structural_holdout_rows": int(holdout_mask.sum()),
                "common_eligible_rows": len(one_step_timestamps),
                "prediction_sha256": calculate_sha256(one_step_path),
                "metrics_sha256": calculate_sha256(local_one_step_metrics),
            },
            "recursive": {
                "scheduled_origins": len(scheduled_origins),
                "eligible_common_origins": len(origins),
                "excluded_origins": len(scheduled_origins) - len(origins),
                "horizon_hours": 24,
                "prediction_sha256": calculate_sha256(recursive_path),
                "metrics_sha256": calculate_sha256(local_recursive_metrics),
            },
            "figures": {
                "one_step_full_sha256": calculate_sha256(full_figure),
                "one_step_diagnostic_sha256": calculate_sha256(diagnostic_figure),
                "recursive_horizon_sha256": calculate_sha256(recursive_figure),
            },
            "checks": {
                "common_one_step_timestamps": True,
                "common_recursive_origins": True,
                "future_actual_used_in_recursive_history": False,
                "holdout_used_for_model_selection": False,
                "post_holdout_model_change": False,
                "binary_model_persisted": False,
                "official_audit_is_promotion_marker": True,
            },
            "status": "PASS",
        }
        local_audit = run_dir / "evaluation_audit.json"
        atomic_write_json(audit, local_audit)

        outputs = contract["outputs"]
        atomic_write_csv(one_step, project_root / outputs["one_step_predictions"])
        one_step_metrics["prediction_sha256"] = calculate_sha256(
            project_root / outputs["one_step_predictions"]
        )
        atomic_write_json(one_step_metrics, project_root / outputs["one_step_metrics"])
        atomic_write_csv(recursive, project_root / outputs["recursive_predictions"])
        recursive_metrics["prediction_sha256"] = calculate_sha256(
            project_root / outputs["recursive_predictions"]
        )
        atomic_write_json(recursive_metrics, project_root / outputs["recursive_metrics"])
        _atomic_copy(full_figure, project_root / outputs["one_step_full_figure"])
        _atomic_copy(
            diagnostic_figure,
            project_root / outputs["one_step_diagnostic_figure"],
        )
        _atomic_copy(recursive_figure, project_root / outputs["recursive_horizon_figure"])
        audit["one_step"]["prediction_sha256"] = calculate_sha256(
            project_root / outputs["one_step_predictions"]
        )
        audit["one_step"]["metrics_sha256"] = calculate_sha256(
            project_root / outputs["one_step_metrics"]
        )
        audit["recursive"]["prediction_sha256"] = calculate_sha256(
            project_root / outputs["recursive_predictions"]
        )
        audit["recursive"]["metrics_sha256"] = calculate_sha256(
            project_root / outputs["recursive_metrics"]
        )
        atomic_write_json(audit, project_root / outputs["evaluation_audit"])
        checkpoint["status"] = "COMPLETED"
        checkpoint["official_outputs_promoted"] = True
        checkpoint["completed_tasks"] = sorted(
            set(checkpoint["completed_tasks"])
            | {"metrics", "figures", "official_promotion"}
        )
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "INFO", "Phase 7 final evaluation completed.")
        return {
            "run_dir": str(run_dir.relative_to(project_root)),
            "selected_candidate": model_lock["selected_candidate"],
            "one_step_rows_per_candidate": len(one_step_timestamps),
            "recursive_origins": len(origins),
            "holdout_label": contract["scope"]["holdout_label"],
            "evaluation_audit": outputs["evaluation_audit"],
            "status": "PASS",
        }
    except KeyboardInterrupt:
        checkpoint["status"] = "INTERRUPTED"
        checkpoint["official_outputs_promoted"] = False
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "WARNING", "Phase 7 evaluation interrupted by Human.")
        raise
    except Exception as error:
        checkpoint["status"] = "FAILED"
        checkpoint["official_outputs_promoted"] = False
        checkpoint["last_error"] = f"{type(error).__name__}: {error}"
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(
            log_path,
            "ERROR",
            f"Phase 7 evaluation failed: {type(error).__name__}: {error}",
        )
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--preflight",
        action="store_true",
        help="Validate Phase 7 gates without opening the holdout target.",
    )
    actions.add_argument(
        "--run-final-evaluation",
        action="store_true",
        help="Start a new Human-authorized Phase 7 final evaluation.",
    )
    actions.add_argument(
        "--resume-run-dir",
        type=Path,
        help="Resume an interrupted Human-authorized Phase 7 run.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.preflight:
        result = run_preflight()
    elif args.run_final_evaluation:
        result = run_final_evaluation()
    else:
        result = run_final_evaluation(resume_run_dir=args.resume_run_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
