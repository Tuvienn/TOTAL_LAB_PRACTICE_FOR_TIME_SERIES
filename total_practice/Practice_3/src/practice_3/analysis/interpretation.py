"""Human-gated Phase 8 error and model-interpretation analysis."""

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
    atomic_write_csv,
    validate_one_step_predictions,
    validate_recursive_predictions,
)
from practice_3.analysis.metrics import regression_metrics
from practice_3.analysis.model_training import (
    append_run_log,
    atomic_write_json,
    dependency_smoke_test,
    package_versions,
    read_json_document,
)
from practice_3.analysis.forecasting import build_full_development_partition
from practice_3.data.data_preparation import calculate_sha256, load_json_contract
from practice_3.data.supervised_dataset import PROJECT_ROOT, load_phase_05_inputs
from practice_3.data.temporal_split import (
    build_development_holdout_masks,
    validate_prepared_input,
)
from practice_3.visualization.error_analysis import (
    save_error_by_load_figure,
    save_error_by_time_figure,
    save_feature_importance_figure,
    save_residual_diagnostics_figure,
)


EXPECTED_CANDIDATES = ["persistence", "seasonal_naive_24", "xgboost_tuned"]
EXPECTED_ONE_STEP_ROWS = 8_592
EXPECTED_RECURSIVE_ORIGINS = 357
EXPECTED_RECURSIVE_ROWS = 8_568
EXPECTED_DEVELOPMENT_SAMPLES = 108_083
EXPECTED_FEATURE_COUNT = 22
EXPECTED_SUMMARY_STATISTICS = [
    "mean_error",
    "median_error",
    "error_standard_deviation",
    "mae",
    "rmse",
    "absolute_error_p90",
    "absolute_error_p95",
    "over_forecast_rate",
    "under_forecast_rate",
]
EXPECTED_RECURSIVE_ANALYSES = [
    "per_horizon_mae_rmse",
    "mae_growth_from_horizon_1",
    "rmse_growth_from_horizon_1",
    "baseline_gap_by_horizon",
    "hardest_horizon_by_mae",
]
EXPECTED_FEATURE_GROUPS = {
    "lag": "prefix_lag_",
    "rolling": "prefix_rolling_",
    "calendar": "remaining_features",
}


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def validate_error_analysis_contract(contract: dict[str, Any]) -> None:
    """Reject changes to the approved Phase 8 analysis boundary."""

    if contract.get("status") != "APPROVED":
        raise ValueError("Error-analysis contract must be approved.")
    upstream = contract["upstream"]
    if upstream["locked_candidate"] != "xgboost_tuned":
        raise ValueError("Phase 8 locked candidate changed.")
    if upstream["candidate_registry"] != EXPECTED_CANDIDATES:
        raise ValueError("Phase 8 candidate registry changed.")
    one_step = contract["one_step"]
    if (
        one_step["detailed_candidate"] != "xgboost_tuned"
        or one_step["expected_rows_per_candidate"] != EXPECTED_ONE_STEP_ROWS
        or one_step["residual_sign"] != "prediction_minus_actual"
        or one_step["summary_statistics"] != EXPECTED_SUMMARY_STATISTICS
        or one_step["residual_acf"]
        != {
            "minimum_lag_hours": 1,
            "maximum_lag_hours": 168,
            "exact_timestamp_pairs": True,
            "confidence_level": 0.95,
            "confidence_formula": "plus_minus_1.96_over_sqrt_n_pairs",
        }
        or one_step["largest_errors"]
        != {
            "sort_key": "absolute_error_descending_then_timestamp_ascending",
            "top_n": 10,
        }
    ):
        raise ValueError("Phase 8 one-step protocol changed.")
    regimes = contract["regimes"]
    if regimes != {
        "dimensions": [
            "hour",
            "day_of_week",
            "day_type",
            "month",
            "actual_load_quartile",
        ],
        "day_type_labels": ["weekday", "weekend"],
        "load_quantiles": [0.0, 0.25, 0.5, 0.75, 1.0],
        "load_labels": ["low", "medium_low", "medium_high", "high"],
        "same_rows_for_all_candidates": True,
        "post_hoc_only": True,
    }:
        raise ValueError("Phase 8 regime protocol changed.")
    recursive = contract["recursive"]
    if (
        recursive["horizon_hours"] != 24
        or recursive["expected_common_origins"] != EXPECTED_RECURSIVE_ORIGINS
        or recursive["expected_predictions_per_candidate"]
        != EXPECTED_RECURSIVE_ROWS
        or recursive["analysis"] != EXPECTED_RECURSIVE_ANALYSES
    ):
        raise ValueError("Phase 8 recursive protocol changed.")
    importance = contract["feature_importance"]
    if (
        importance["candidate"] != "xgboost_tuned"
        or importance["method"] != "xgboost_gain_normalized"
        or importance["refit_partition"] != "full_development_only"
        or importance["expected_refit_samples"] != EXPECTED_DEVELOPMENT_SAMPLES
        or importance["expected_feature_count"] != EXPECTED_FEATURE_COUNT
        or importance["feature_groups"] != EXPECTED_FEATURE_GROUPS
        or importance["causal_claim_allowed"] is not False
        or importance["holdout_used_for_importance"] is not False
        or importance["binary_model_persisted"] is not False
    ):
        raise ValueError("Phase 8 feature-importance protocol changed.")
    execution = contract["execution"]
    if execution != {
        "executor": "human_terminal_only",
        "reason": "locked_model_refit_required_for_gain_importance",
        "atomic_promotion": True,
        "binary_model_persisted": False,
        "run_directory_pattern": (
            "runs/P8_error_interpretation_<timestamp>_<execution_identity>"
        ),
    }:
        raise ValueError("Phase 8 execution boundary changed.")
    scope = contract["scope"]
    if scope != {
        "post_hoc_analysis_only": True,
        "model_change_allowed": False,
        "feature_change_allowed": False,
        "parameter_change_allowed": False,
        "new_model_selection_allowed": False,
        "final_conclusion_owner": "phase_09",
    }:
        raise ValueError("Phase 8 post-hoc scope changed.")
    if contract["outputs"] != {
        "error_analysis": "outputs/results/phase_08_error_analysis.json",
        "feature_importance": "outputs/results/phase_08_feature_importance.csv",
        "residual_diagnostics_figure": (
            "outputs/figures/phase_08_residual_diagnostics.png"
        ),
        "error_by_time_figure": "outputs/figures/phase_08_error_by_time.png",
        "error_by_load_figure": (
            "outputs/figures/phase_08_error_by_load_regime.png"
        ),
        "feature_importance_figure": (
            "outputs/figures/phase_08_feature_importance.png"
        ),
    }:
        raise ValueError("Phase 8 output ownership changed.")


def load_phase_08_inputs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    pd.DataFrame,
    dict[str, Any],
    pd.DataFrame,
    dict[str, Any],
    dict[str, Any],
]:
    """Load and validate all official Phase 8 input evidence."""

    project_root = Path(project_root).resolve()
    contract = load_json_contract(project_root / "config/error_analysis.json")
    validate_error_analysis_contract(contract)
    upstream = contract["upstream"]
    for path_key, hash_key in (
        ("phase_07_audit", "phase_07_audit_sha256"),
        ("one_step_predictions", "one_step_predictions_sha256"),
        ("one_step_metrics", "one_step_metrics_sha256"),
        ("recursive_predictions", "recursive_predictions_sha256"),
        ("recursive_metrics", "recursive_metrics_sha256"),
        ("phase_06_model_lock", "phase_06_model_lock_sha256"),
    ):
        path = project_root / upstream[path_key]
        if calculate_sha256(path) != upstream[hash_key]:
            raise ValueError(f"Phase 8 upstream identity changed: {path_key}.")
    phase_07_audit = read_json_document(project_root / upstream["phase_07_audit"])
    one_step_metrics = read_json_document(project_root / upstream["one_step_metrics"])
    recursive_metrics = read_json_document(project_root / upstream["recursive_metrics"])
    model_lock = read_json_document(project_root / upstream["phase_06_model_lock"])
    one_step = pd.read_csv(
        project_root / upstream["one_step_predictions"],
        parse_dates=["timestamp"],
    )
    recursive = pd.read_csv(
        project_root / upstream["recursive_predictions"],
        parse_dates=["forecast_origin", "target_timestamp"],
    )
    if phase_07_audit.get("status") != "PASS":
        raise ValueError("Phase 7 audit must have PASS status.")
    if one_step_metrics.get("status") != "PASS" or recursive_metrics.get(
        "status"
    ) != "PASS":
        raise ValueError("Phase 7 metric artifacts must have PASS status.")
    if model_lock.get("status") != "PASS":
        raise ValueError("Phase 6 model lock must have PASS status.")
    if model_lock["selected_candidate"] != "xgboost_tuned":
        raise ValueError("Model lock candidate changed before Phase 8.")
    if model_lock["package_versions"] != package_versions():
        raise ValueError("Current package versions do not match the model lock.")
    timestamps = pd.DatetimeIndex(
        one_step.loc[one_step["candidate"].eq(EXPECTED_CANDIDATES[0]), "timestamp"]
    )
    validate_one_step_predictions(one_step, EXPECTED_CANDIDATES, timestamps)
    if len(timestamps) != EXPECTED_ONE_STEP_ROWS:
        raise ValueError("Phase 8 one-step population changed.")
    origins = pd.DatetimeIndex(
        recursive.loc[
            recursive["candidate"].eq(EXPECTED_CANDIDATES[0]), "forecast_origin"
        ].unique()
    )
    validate_recursive_predictions(recursive, EXPECTED_CANDIDATES, origins)
    if len(origins) != EXPECTED_RECURSIVE_ORIGINS:
        raise ValueError("Phase 8 recursive-origin population changed.")
    if any(
        len(recursive.loc[recursive["candidate"].eq(candidate)])
        != EXPECTED_RECURSIVE_ROWS
        for candidate in EXPECTED_CANDIDATES
    ):
        raise ValueError("Phase 8 recursive prediction population changed.")
    evidence = {
        key: upstream[key]
        for key in upstream
        if key.endswith("sha256")
    }
    evidence.update(
        {
            "candidate_registry": deepcopy(EXPECTED_CANDIDATES),
            "one_step_rows_per_candidate": EXPECTED_ONE_STEP_ROWS,
            "recursive_common_origins": EXPECTED_RECURSIVE_ORIGINS,
            "recursive_rows_per_candidate": EXPECTED_RECURSIVE_ROWS,
            "locked_parameters": deepcopy(model_lock["locked_parameters"]),
            "feature_order": deepcopy(model_lock["feature_order"]),
            "package_versions": deepcopy(model_lock["package_versions"]),
        }
    )
    return (
        contract,
        model_lock,
        one_step,
        one_step_metrics,
        recursive,
        recursive_metrics,
        evidence,
    )


def build_residual_summary(
    predictions: pd.DataFrame,
    candidates: list[str],
) -> list[dict[str, Any]]:
    """Build deterministic one-step residual statistics for every candidate."""

    records: list[dict[str, Any]] = []
    for candidate in candidates:
        selected = predictions.loc[predictions["candidate"].eq(candidate)]
        errors = selected["error"].to_numpy(dtype="float64")
        absolute_errors = selected["absolute_error"].to_numpy(dtype="float64")
        if len(selected) == 0 or not np.isfinite(errors).all():
            raise ValueError("Residual summary contains invalid candidate evidence.")
        metrics = regression_metrics(selected["actual"], selected["prediction"])
        records.append(
            {
                "candidate": candidate,
                "n_observations": int(len(selected)),
                "mean_error": float(np.mean(errors)),
                "median_error": float(np.median(errors)),
                "error_standard_deviation": float(np.std(errors, ddof=0)),
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "absolute_error_p90": float(np.quantile(absolute_errors, 0.90)),
                "absolute_error_p95": float(np.quantile(absolute_errors, 0.95)),
                "over_forecast_rate": float(np.mean(errors > 0.0)),
                "under_forecast_rate": float(np.mean(errors < 0.0)),
                "exact_forecast_rate": float(np.mean(errors == 0.0)),
            }
        )
    return records


def build_exact_lag_residual_acf(
    predictions: pd.DataFrame,
    candidate: str,
    minimum_lag: int = 1,
    maximum_lag: int = 168,
) -> pd.DataFrame:
    """Compute residual correlations using exact hourly timestamp pairs."""

    selected = predictions.loc[
        predictions["candidate"].eq(candidate), ["timestamp", "error"]
    ].sort_values("timestamp")
    records: list[dict[str, Any]] = []
    for lag in range(minimum_lag, maximum_lag + 1):
        previous = selected.copy()
        previous["timestamp"] = previous["timestamp"] + pd.Timedelta(hours=lag)
        previous = previous.rename(columns={"error": "previous_error"})
        pairs = selected.merge(previous, on="timestamp", how="inner")
        if len(pairs) < 2:
            raise ValueError("Residual ACF has insufficient exact timestamp pairs.")
        correlation = pairs["error"].corr(pairs["previous_error"])
        if not np.isfinite(correlation):
            raise ValueError("Residual ACF contains a non-finite correlation.")
        records.append(
            {
                "lag_hours": lag,
                "n_pairs": int(len(pairs)),
                "autocorrelation": float(correlation),
                "reference_band": float(1.96 / np.sqrt(len(pairs))),
            }
        )
    return pd.DataFrame(records)


def build_largest_error_records(
    predictions: pd.DataFrame,
    candidate: str,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Return deterministically ordered largest absolute one-step errors."""

    selected = predictions.loc[predictions["candidate"].eq(candidate)].copy()
    selected = selected.sort_values(
        ["absolute_error", "timestamp"],
        ascending=[False, True],
        kind="stable",
    ).head(top_n)
    return [
        {
            "rank": rank,
            "timestamp": row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "actual": float(row.actual),
            "prediction": float(row.prediction),
            "error": float(row.error),
            "absolute_error": float(row.absolute_error),
        }
        for rank, row in enumerate(selected.itertuples(index=False), start=1)
    ]


def attach_error_regimes(
    predictions: pd.DataFrame,
    quantiles: list[float],
    labels: list[str],
) -> tuple[pd.DataFrame, list[float]]:
    """Attach common calendar and post-hoc load regimes to prediction rows."""

    actual_counts = predictions.groupby("timestamp", sort=True)["actual"].nunique()
    if not actual_counts.eq(1).all():
        raise ValueError("One-step candidates disagree on actual values.")
    actual_by_timestamp = (
        predictions.groupby("timestamp", sort=True, as_index=False)["actual"]
        .first()
        .sort_values("timestamp")
    )
    boundaries = np.quantile(
        actual_by_timestamp["actual"].to_numpy(dtype="float64"),
        quantiles,
    )
    if len(np.unique(boundaries)) != len(boundaries):
        raise ValueError("Actual-load quantile boundaries are not unique.")
    result = predictions.copy()
    result["hour"] = result["timestamp"].dt.hour
    result["day_of_week"] = result["timestamp"].dt.day_of_week
    result["day_type"] = pd.Categorical(
        np.where(result["day_of_week"].ge(5), "weekend", "weekday"),
        categories=["weekday", "weekend"],
        ordered=True,
    )
    result["month"] = result["timestamp"].dt.month
    result["actual_load_quartile"] = pd.cut(
        result["actual"],
        bins=boundaries,
        labels=labels,
        include_lowest=True,
        ordered=True,
    )
    if result["actual_load_quartile"].isna().any():
        raise ValueError("Actual-load regime assignment is incomplete.")
    return result, [float(value) for value in boundaries]


def _native_value(value: Any) -> Any:
    return value.item() if hasattr(value, "item") else value


def build_regime_metrics(
    predictions_with_regimes: pd.DataFrame,
    candidates: list[str],
    dimensions: list[str],
) -> pd.DataFrame:
    """Build candidate metrics for every approved regime dimension."""

    records: list[dict[str, Any]] = []
    for dimension in dimensions:
        for candidate in candidates:
            selected = predictions_with_regimes.loc[
                predictions_with_regimes["candidate"].eq(candidate)
            ]
            total = 0
            for regime, group in selected.groupby(dimension, sort=True, observed=True):
                metrics = regression_metrics(group["actual"], group["prediction"])
                records.append(
                    {
                        "dimension": dimension,
                        "candidate": candidate,
                        "regime": _native_value(regime),
                        "n_observations": metrics["samples"],
                        "mae": metrics["mae"],
                        "rmse": metrics["rmse"],
                        "mean_error": float(group["error"].mean()),
                    }
                )
                total += len(group)
            if total != len(selected):
                raise ValueError("Regime groups do not conserve candidate rows.")
    result = pd.DataFrame(records)
    numeric = result[["mae", "rmse", "mean_error"]].to_numpy(dtype="float64")
    if not np.isfinite(numeric).all():
        raise ValueError("Regime metrics contain non-finite values.")
    return result


def build_recursive_interpretation(
    recursive_metrics: dict[str, Any],
) -> dict[str, Any]:
    """Build fixed horizon-growth and baseline-gap records."""

    candidates = {
        record["candidate"]: record
        for record in recursive_metrics["candidate_metrics"]
    }
    if list(candidates) != EXPECTED_CANDIDATES:
        raise ValueError("Recursive metric candidate order changed.")
    expected_horizons = list(range(1, 25))
    for candidate in EXPECTED_CANDIDATES:
        horizons = [
            int(record["horizon"])
            for record in candidates[candidate]["per_horizon"]
        ]
        if horizons != expected_horizons:
            raise ValueError("Recursive metrics must contain ordered horizons 1..24.")
    candidate_records: list[dict[str, Any]] = []
    for candidate in EXPECTED_CANDIDATES:
        record = candidates[candidate]
        horizon_one = record["per_horizon"][0]
        horizon_records = []
        for horizon_record in record["per_horizon"]:
            horizon_records.append(
                {
                    "horizon": int(horizon_record["horizon"]),
                    "mae": float(horizon_record["mae"]),
                    "rmse": float(horizon_record["rmse"]),
                    "mae_growth_from_horizon_1": float(
                        horizon_record["mae"] - horizon_one["mae"]
                    ),
                    "rmse_growth_from_horizon_1": float(
                        horizon_record["rmse"] - horizon_one["rmse"]
                    ),
                }
            )
        hardest = max(horizon_records, key=lambda item: item["mae"])
        candidate_records.append(
            {
                "candidate": candidate,
                "hardest_horizon_by_mae": hardest["horizon"],
                "hardest_horizon_mae": hardest["mae"],
                "horizons": horizon_records,
            }
        )
    xgboost = candidates["xgboost_tuned"]["per_horizon"]
    comparisons = []
    for baseline in ("persistence", "seasonal_naive_24"):
        for baseline_record, xgboost_record in zip(
            candidates[baseline]["per_horizon"], xgboost, strict=True
        ):
            comparisons.append(
                {
                    "baseline": baseline,
                    "horizon": int(xgboost_record["horizon"]),
                    "baseline_mae_minus_xgboost_mae": float(
                        baseline_record["mae"] - xgboost_record["mae"]
                    ),
                    "baseline_rmse_minus_xgboost_rmse": float(
                        baseline_record["rmse"] - xgboost_record["rmse"]
                    ),
                }
            )
    return {
        "candidate_horizon_analysis": candidate_records,
        "xgboost_baseline_gaps": comparisons,
    }


def normalize_gain_importance(
    raw_gain: dict[str, float],
    feature_order: list[str],
) -> pd.DataFrame:
    """Retain all locked features and normalize finite positive gain."""

    rows = []
    for feature in feature_order:
        gain = float(raw_gain.get(feature, 0.0))
        if not np.isfinite(gain) or gain < 0.0:
            raise ValueError("XGBoost gain importance must be finite and non-negative.")
        if feature.startswith("lag_"):
            group = "lag"
        elif feature.startswith("rolling_"):
            group = "rolling"
        else:
            group = "calendar"
        rows.append({"feature": feature, "feature_group": group, "gain": gain})
    result = pd.DataFrame(rows)
    total = float(result["gain"].sum())
    if total <= 0.0:
        raise ValueError("XGBoost total gain must be positive.")
    result["normalized_gain"] = result["gain"] / total
    result["rank"] = (
        result["normalized_gain"].rank(method="first", ascending=False).astype("int64")
    )
    return result.sort_values(["rank", "feature"], kind="stable").reset_index(drop=True)


def run_preflight(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Validate Phase 8 evidence and dependencies without project-data refit."""

    contract, model_lock, one_step, _osm, recursive, _rm, evidence = (
        load_phase_08_inputs(project_root)
    )
    dependency = dependency_smoke_test()
    official_outputs_created = any(
        (Path(project_root) / path).exists()
        for path in contract["outputs"].values()
    )
    return {
        "phase": contract["phase"],
        "locked_candidate": model_lock["selected_candidate"],
        "one_step_rows_per_candidate": int(
            len(one_step) / len(EXPECTED_CANDIDATES)
        ),
        "recursive_rows_per_candidate": int(
            len(recursive) / len(EXPECTED_CANDIDATES)
        ),
        "recursive_common_origins": evidence["recursive_common_origins"],
        "feature_count": len(model_lock["feature_order"]),
        "dependency_gate": dependency,
        "project_model_refit_started": False,
        "official_outputs_created": official_outputs_created,
        "status": "PASS",
    }


def _execution_identity(contract: dict[str, Any], evidence: dict[str, Any]) -> str:
    return sha256(_canonical_json({"contract": contract, "evidence": evidence})).hexdigest()[:8]


def initialize_run(
    project_root: Path,
    contract: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[Path, Path, dict[str, Any]]:
    """Create a Human-owned Phase 8 run directory and checkpoint."""

    identity = _execution_identity(contract, evidence)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    run_id = f"P8_error_interpretation_{timestamp}_{identity}"
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
        "binary_model_persisted": False,
    }
    atomic_write_json(contract, run_dir / "config_snapshot.json")
    atomic_write_json(metadata, run_dir / "run_metadata.json")
    atomic_write_json(checkpoint, run_dir / "checkpoint.json")
    append_run_log(log_path, "INFO", "Phase 8 error and interpretation run initialized.")
    return run_dir, log_path, checkpoint


def _load_development_partition(
    project_root: Path,
) -> tuple[pd.DataFrame, pd.Series]:
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
    development_mask, _holdout_mask = build_development_holdout_masks(
        prepared, data_contract, split_contract
    )
    return build_full_development_partition(
        prepared,
        development_mask,
        data_contract,
        {"feature": feature_contract, "supervised": supervised_contract},
    )


def _promote_phase_08_outputs(
    local_to_official: list[tuple[Path, Path]],
) -> None:
    """Promote a complete Phase 8 bundle or remove every partial destination."""

    temporary_paths: list[Path] = []
    official_paths = [Path(destination) for _, destination in local_to_official]
    if any(path.exists() for path in official_paths):
        raise ValueError("Phase 8 official output already exists or is partial.")
    try:
        for source, destination in local_to_official:
            source = Path(source)
            destination = Path(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(f".{destination.name}.phase08.tmp")
            shutil.copyfile(source, temporary)
            if calculate_sha256(temporary) != calculate_sha256(source):
                raise ValueError("Phase 8 staged output checksum validation failed.")
            temporary_paths.append(temporary)
        for temporary, destination in zip(
            temporary_paths, official_paths, strict=True
        ):
            os.replace(temporary, destination)
    except BaseException:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)
        for destination in official_paths:
            destination.unlink(missing_ok=True)
        raise


def run_analysis(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Run the Human-authorized Phase 8 analysis and gain-importance refit."""

    project_root = Path(project_root).resolve()
    (
        contract,
        model_lock,
        one_step,
        _one_step_metrics,
        _recursive,
        recursive_metrics,
        evidence,
    ) = load_phase_08_inputs(project_root)
    dependency_smoke_test()
    official_paths = [project_root / path for path in contract["outputs"].values()]
    if any(path.exists() for path in official_paths):
        raise ValueError("Phase 8 official output already exists or is partial.")
    run_dir, log_path, checkpoint = initialize_run(project_root, contract, evidence)
    checkpoint["status"] = "RUNNING"
    atomic_write_json(checkpoint, run_dir / "checkpoint.json")
    try:
        residual_summary = build_residual_summary(one_step, EXPECTED_CANDIDATES)
        acf = build_exact_lag_residual_acf(one_step, "xgboost_tuned")
        largest_errors = build_largest_error_records(one_step, "xgboost_tuned")
        regime_data, load_boundaries = attach_error_regimes(
            one_step,
            contract["regimes"]["load_quantiles"],
            contract["regimes"]["load_labels"],
        )
        regime_metrics = build_regime_metrics(
            regime_data,
            EXPECTED_CANDIDATES,
            contract["regimes"]["dimensions"],
        )
        recursive_analysis = build_recursive_interpretation(recursive_metrics)
        checkpoint["completed_tasks"].append("error_analysis")
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "INFO", "Prediction error analysis completed.")

        X_development, y_development = _load_development_partition(project_root)
        if len(X_development) != EXPECTED_DEVELOPMENT_SAMPLES:
            raise ValueError("Phase 8 development refit population changed.")
        if X_development.columns.tolist() != model_lock["feature_order"]:
            raise ValueError("Phase 8 development feature order changed.")
        from xgboost import XGBRegressor

        estimator = XGBRegressor(**model_lock["locked_parameters"])
        append_run_log(
            log_path,
            "INFO",
            f"Locked XGBoost refit started on {len(X_development)} development samples.",
        )
        estimator.fit(X_development, y_development)
        raw_gain = estimator.get_booster().get_score(importance_type="gain")
        feature_importance = normalize_gain_importance(
            raw_gain, model_lock["feature_order"]
        )
        local_importance = run_dir / "feature_importance.csv"
        atomic_write_csv(feature_importance, local_importance)
        checkpoint["completed_tasks"].append("feature_importance")
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "INFO", "Locked XGBoost gain importance completed.")

        residual_figure = run_dir / "phase_08_residual_diagnostics.png"
        time_figure = run_dir / "phase_08_error_by_time.png"
        load_figure = run_dir / "phase_08_error_by_load_regime.png"
        importance_figure = run_dir / "phase_08_feature_importance.png"
        save_residual_diagnostics_figure(
            one_step, acf, "xgboost_tuned", residual_figure
        )
        save_error_by_time_figure(
            regime_metrics, "xgboost_tuned", time_figure
        )
        save_error_by_load_figure(regime_metrics, load_figure)
        save_feature_importance_figure(feature_importance, importance_figure)
        group_importance = (
            feature_importance.groupby("feature_group", sort=True)["normalized_gain"]
            .sum()
            .to_dict()
        )
        result = {
            "phase": contract["phase"],
            "contract_version": contract["contract_version"],
            "run_id": checkpoint["run_id"],
            "upstream_evidence": evidence,
            "scope": deepcopy(contract["scope"]),
            "one_step": {
                "residual_sign": contract["one_step"]["residual_sign"],
                "candidate_summaries": residual_summary,
                "xgboost_residual_acf": acf.to_dict(orient="records"),
                "xgboost_largest_errors": largest_errors,
                "load_quartile_boundaries": load_boundaries,
                "regime_metrics": regime_metrics.to_dict(orient="records"),
            },
            "recursive": recursive_analysis,
            "feature_importance": {
                "method": contract["feature_importance"]["method"],
                "development_refit_samples": len(X_development),
                "feature_count": len(feature_importance),
                "group_normalized_gain": {
                    key: float(value) for key, value in group_importance.items()
                },
                "csv_path": contract["outputs"]["feature_importance"],
                "csv_sha256": calculate_sha256(local_importance),
                "causal_claim_allowed": False,
            },
            "figures": {
                "residual_diagnostics": {
                    "path": contract["outputs"]["residual_diagnostics_figure"],
                    "sha256": calculate_sha256(residual_figure),
                },
                "error_by_time": {
                    "path": contract["outputs"]["error_by_time_figure"],
                    "sha256": calculate_sha256(time_figure),
                },
                "error_by_load": {
                    "path": contract["outputs"]["error_by_load_figure"],
                    "sha256": calculate_sha256(load_figure),
                },
                "feature_importance": {
                    "path": contract["outputs"]["feature_importance_figure"],
                    "sha256": calculate_sha256(importance_figure),
                },
            },
            "checks": {
                "post_hoc_only": True,
                "model_changed": False,
                "features_changed": False,
                "parameters_changed": False,
                "new_model_selection_performed": False,
                "holdout_used_for_importance": False,
                "binary_model_persisted": False,
                "regime_population_conserved": True,
                "exact_timestamp_acf": True,
            },
            "status": "PASS",
        }
        local_result = run_dir / "error_analysis.json"
        atomic_write_json(result, local_result)

        outputs = contract["outputs"]
        _promote_phase_08_outputs(
            [
                (
                    local_importance,
                    project_root / outputs["feature_importance"],
                ),
                (
                    residual_figure,
                    project_root / outputs["residual_diagnostics_figure"],
                ),
                (time_figure, project_root / outputs["error_by_time_figure"]),
                (load_figure, project_root / outputs["error_by_load_figure"]),
                (
                    importance_figure,
                    project_root / outputs["feature_importance_figure"],
                ),
                (local_result, project_root / outputs["error_analysis"]),
            ]
        )
        checkpoint["completed_tasks"].extend(["figures", "official_promotion"])
        checkpoint["completed_tasks"] = sorted(set(checkpoint["completed_tasks"]))
        checkpoint["status"] = "COMPLETED"
        checkpoint["official_outputs_promoted"] = True
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "INFO", "Phase 8 error and interpretation analysis completed.")
        return {
            "run_dir": str(run_dir.relative_to(project_root)),
            "locked_candidate": model_lock["selected_candidate"],
            "one_step_rows_per_candidate": EXPECTED_ONE_STEP_ROWS,
            "recursive_common_origins": EXPECTED_RECURSIVE_ORIGINS,
            "development_refit_samples": len(X_development),
            "error_analysis": outputs["error_analysis"],
            "status": "PASS",
        }
    except KeyboardInterrupt:
        for path in official_paths:
            path.unlink(missing_ok=True)
        checkpoint["status"] = "INTERRUPTED"
        checkpoint["official_outputs_promoted"] = False
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(log_path, "WARNING", "Phase 8 execution interrupted by Human.")
        raise
    except Exception as error:
        for path in official_paths:
            path.unlink(missing_ok=True)
        checkpoint["status"] = "FAILED"
        checkpoint["official_outputs_promoted"] = False
        checkpoint["last_error"] = f"{type(error).__name__}: {error}"
        atomic_write_json(checkpoint, run_dir / "checkpoint.json")
        append_run_log(
            log_path,
            "ERROR",
            f"Phase 8 execution failed: {type(error).__name__}: {error}",
        )
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument(
        "--preflight",
        action="store_true",
        help="Validate Phase 8 gates without project-data refit.",
    )
    actions.add_argument(
        "--run",
        action="store_true",
        help="Start the Human-authorized Phase 8 analysis run.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_preflight() if args.preflight else run_analysis()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
