"""Deterministic Phase 9 evidence synthesis for Practice 3."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from practice_3.data.data_preparation import (
    calculate_sha256,
    load_json_contract,
)
from practice_3.data.supervised_dataset import PROJECT_ROOT


EXPECTED_UPSTREAM_KEYS = [
    "phase_01_data_quality",
    "phase_02_temporal_split",
    "phase_03_eda",
    "phase_04_features",
    "phase_05_supervised",
    "phase_06_cv",
    "phase_06_model_lock",
    "supplemental_linear",
    "supplemental_lag",
    "supplemental_audit",
    "phase_07_audit",
    "phase_07_one_step",
    "phase_07_recursive",
    "phase_08_error_analysis",
    "phase_08_feature_importance",
]


def read_json(path: Path) -> dict[str, Any]:
    """Read one JSON document with an object root."""

    with Path(path).open(encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def atomic_write_json(payload: dict[str, Any], output_path: Path) -> None:
    """Write a deterministic JSON object atomically."""

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
        if read_json(temporary_path) != payload:
            raise ValueError("Final conclusion JSON round-trip validation failed.")
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def validate_final_conclusion_contract(contract: dict[str, Any]) -> None:
    """Reject drift from the Human-approved Phase 9 design."""

    if contract.get("status") != "APPROVED":
        raise ValueError("Final-conclusion contract must be approved.")
    if list(contract.get("upstream", {})) != EXPECTED_UPSTREAM_KEYS:
        raise ValueError("Final-conclusion upstream registry changed.")
    expected = contract["expected"]
    if expected != {
        "selected_candidate": "xgboost_tuned",
        "feature_count": 22,
        "development_timestamps": 112535,
        "eligible_supervised_samples": 108083,
        "cv_folds": 5,
        "one_step_observations": 8592,
        "recursive_origins": 357,
        "recursive_predictions": 8568,
        "holdout_label": "historical_re_evaluation_holdout",
        "supplemental_fits": 35,
        "lag_p_values": [1, 6, 12, 24, 48, 168],
    }:
        raise ValueError("Final-conclusion expected evidence changed.")
    if contract["scope"] != {
        "evidence_synthesis_only": True,
        "training_allowed": False,
        "prediction_allowed": False,
        "tuning_allowed": False,
        "model_selection_allowed": False,
        "holdout_re_evaluation_allowed": False,
        "model_lock_change_allowed": False,
        "arima_empirically_benchmarked": False,
    }:
        raise ValueError("Final-conclusion scope changed.")
    if contract["outputs"] != {
        "final_conclusion": "outputs/results/phase_09_final_conclusion.json"
    }:
        raise ValueError("Final-conclusion output path changed.")


def load_phase_09_inputs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, str]]:
    """Load all locked Phase 9 evidence after exact identity validation."""

    project_root = Path(project_root).resolve()
    contract = load_json_contract(project_root / "config/final_conclusion.json")
    validate_final_conclusion_contract(contract)
    documents: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for name, record in contract["upstream"].items():
        path = project_root / record["path"]
        if not path.is_file():
            raise FileNotFoundError(f"Phase 9 upstream artifact not found: {path}")
        actual_sha256 = calculate_sha256(path)
        if actual_sha256 != record["sha256"]:
            raise ValueError(
                f"Phase 9 upstream SHA-256 changed for {name}. "
                f"Expected {record['sha256']}; got {actual_sha256}."
            )
        hashes[name] = actual_sha256
        if path.suffix == ".json":
            documents[name] = read_json(path)
    required_pass = [name for name in EXPECTED_UPSTREAM_KEYS if name != "phase_08_feature_importance"]
    for name in required_pass:
        if documents[name].get("status") != "PASS":
            raise ValueError(f"Phase 9 upstream status is not PASS: {name}.")
    return contract, documents, hashes


def _candidate(records: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [record for record in records if record["candidate"] == name]
    if len(matches) != 1:
        raise ValueError(f"Candidate must occur exactly once: {name}.")
    return matches[0]


def validate_evidence_consistency(
    contract: dict[str, Any],
    documents: dict[str, dict[str, Any]],
) -> None:
    """Validate cross-phase populations, identities, and scientific boundaries."""

    expected = contract["expected"]
    phase_01 = documents["phase_01_data_quality"]
    phase_02 = documents["phase_02_temporal_split"]
    phase_04 = documents["phase_04_features"]
    phase_05 = documents["phase_05_supervised"]
    phase_06_cv = documents["phase_06_cv"]
    model_lock = documents["phase_06_model_lock"]
    supplemental_linear = documents["supplemental_linear"]
    supplemental_lag = documents["supplemental_lag"]
    supplemental_audit = documents["supplemental_audit"]
    phase_07_audit = documents["phase_07_audit"]
    one_step = documents["phase_07_one_step"]
    recursive = documents["phase_07_recursive"]
    phase_08 = documents["phase_08_error_analysis"]

    if phase_01["prepared_rows"] != 121296 or phase_01["missing_target_after"] != 27:
        raise ValueError("Phase 1 final timeline evidence changed.")
    if phase_02["development"]["rows"] != expected["development_timestamps"]:
        raise ValueError("Development timestamp population changed.")
    if phase_02["cross_validation"]["splits"] != expected["cv_folds"]:
        raise ValueError("Cross-validation fold count changed.")
    if phase_02["cross_validation"]["shuffle"] is not False:
        raise ValueError("Temporal validation must not shuffle.")
    if phase_04["feature_count"] != expected["feature_count"]:
        raise ValueError("Official feature count changed.")
    if phase_05["development"]["eligible_rows"] != expected["eligible_supervised_samples"]:
        raise ValueError("Eligible supervised population changed.")
    if model_lock["selected_candidate"] != expected["selected_candidate"]:
        raise ValueError("Selected candidate changed.")
    if phase_06_cv["selected_candidate"] != model_lock["selected_candidate"]:
        raise ValueError("Phase 6 selection and model lock disagree.")
    if model_lock["feature_order"] != phase_05["feature_order"]:
        raise ValueError("Phase 5 and model-lock feature order disagree.")
    if supplemental_audit["completed_project_data_fits"] != expected["supplemental_fits"]:
        raise ValueError("Supplemental fit count changed.")
    if any(
        supplemental_audit["checks"][key] is not False
        for key in [
            "holdout_accessed",
            "holdout_evaluated",
            "model_lock_changed",
            "xgboost_reference_retrained",
            "tuning_performed",
            "binary_model_persisted",
        ]
    ):
        raise ValueError("Supplemental evidence exceeded its scientific scope.")
    if supplemental_audit["checks"]["selection_authority"] != "none":
        raise ValueError("Supplemental evidence cannot have selection authority.")
    if supplemental_linear["aggregate"]["validation_samples"] != _candidate(
        phase_06_cv["candidate_results"], "xgboost_tuned"
    )["aggregate"]["validation_samples"]:
        raise ValueError("Linear and XGBoost comparison populations differ.")
    p_values = [record["p"] for record in supplemental_lag["p_results"]]
    if p_values != expected["lag_p_values"]:
        raise ValueError("Lag-p registry changed.")
    if phase_07_audit["locked_candidate"] != model_lock["selected_candidate"]:
        raise ValueError("Phase 7 evaluated a different candidate.")
    if phase_07_audit["development_refit_samples"] != expected["eligible_supervised_samples"]:
        raise ValueError("Phase 7 development refit population changed.")
    if one_step["holdout_label"] != expected["holdout_label"]:
        raise ValueError("One-step holdout label changed.")
    if recursive["holdout_label"] != expected["holdout_label"]:
        raise ValueError("Recursive holdout label changed.")
    one_step_xgb = _candidate(one_step["candidate_metrics"], "xgboost_tuned")
    recursive_xgb = _candidate(recursive["candidate_metrics"], "xgboost_tuned")
    if one_step_xgb["n_observations"] != expected["one_step_observations"]:
        raise ValueError("One-step evaluation population changed.")
    if recursive_xgb["pooled"]["n_origins"] != expected["recursive_origins"]:
        raise ValueError("Recursive origin population changed.")
    if recursive_xgb["pooled"]["n_predictions"] != expected["recursive_predictions"]:
        raise ValueError("Recursive prediction population changed.")
    if phase_08["scope"]["final_conclusion_owner"] != "phase_09":
        raise ValueError("Phase 8 did not transfer final-conclusion ownership.")
    if phase_08["checks"]["model_changed"] is not False:
        raise ValueError("Phase 8 model-change boundary failed.")


def _one_step_summary(one_step: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "candidate": record["candidate"],
            "mae": record["mae"],
            "rmse": record["rmse"],
            "n_observations": record["n_observations"],
        }
        for record in one_step["candidate_metrics"]
    ]


def _recursive_summary(recursive: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "candidate": record["candidate"],
            "pooled_mae": record["pooled"]["pooled_mae"],
            "pooled_rmse": record["pooled"]["pooled_rmse"],
            "n_predictions": record["pooled"]["n_predictions"],
            "n_origins": record["pooled"]["n_origins"],
        }
        for record in recursive["candidate_metrics"]
    ]


def build_final_conclusion(
    contract: dict[str, Any],
    documents: dict[str, dict[str, Any]],
    hashes: dict[str, str],
) -> dict[str, Any]:
    """Build the final deterministic conclusion from official evidence."""

    validate_evidence_consistency(contract, documents)
    phase_01 = documents["phase_01_data_quality"]
    phase_02 = documents["phase_02_temporal_split"]
    phase_04 = documents["phase_04_features"]
    phase_05 = documents["phase_05_supervised"]
    phase_06_cv = documents["phase_06_cv"]
    model_lock = documents["phase_06_model_lock"]
    linear = documents["supplemental_linear"]
    lag = documents["supplemental_lag"]
    one_step = documents["phase_07_one_step"]
    recursive = documents["phase_07_recursive"]
    error_analysis = documents["phase_08_error_analysis"]

    official_xgb_cv = _candidate(phase_06_cv["candidate_results"], "xgboost_tuned")
    linear_mae = float(linear["aggregate"]["mean_cv_mae"])
    xgb_cv_mae = float(official_xgb_cv["aggregate"]["mean_cv_mae"])
    xgb_improvement = (linear_mae - xgb_cv_mae) / linear_mae * 100.0
    lag_records = deepcopy(lag["p_results"])
    best_lag_record = min(
        lag_records,
        key=lambda record: (float(record["aggregate"]["mean_cv_mae"]), int(record["p"])),
    )
    one_step_xgb = _candidate(one_step["candidate_metrics"], "xgboost_tuned")
    recursive_xgb = _candidate(recursive["candidate_metrics"], "xgboost_tuned")
    xgb_error = _candidate(
        error_analysis["one_step"]["candidate_summaries"], "xgboost_tuned"
    )
    xgb_recursive_interpretation = _candidate(
        error_analysis["recursive"]["candidate_horizon_analysis"],
        "xgboost_tuned",
    )
    lag_one = next(
        record
        for record in error_analysis["one_step"]["xgboost_residual_acf"]
        if record["lag_hours"] == 1
    )

    lag_answer = [
        {
            "p": record["p"],
            "natural_eligible_samples": record["natural_eligible_samples"],
            "mean_cv_mae": record["aggregate"]["mean_cv_mae"],
            "mean_cv_rmse": record["aggregate"]["mean_cv_rmse"],
            "mean_train_mae": record["mean_train_mae"],
            "mean_generalization_gap_mae": record["mean_generalization_gap_mae"],
            "total_fit_duration_seconds": record["total_fit_duration_seconds"],
        }
        for record in lag_records
    ]
    limitations = [
        "The holdout is a historical re-evaluation holdout, not a claimed unseen test set.",
        "No prediction interval or uncertainty calibration was implemented.",
        "Recursive 24-hour error grows materially across the forecast horizon.",
        "Residual autocorrelation remains, including short-lag and daily structure.",
        "XGBoost gain importance is model-specific and is not causal importance.",
        "Linear Regression and lag-p experiments are post-hoc development-only evidence.",
        "ARIMA was not empirically benchmarked in Practice 3.",
        "Findings are limited to this AEP dataset, period, and temporal protocol.",
        "No external validation or production drift monitoring was performed.",
    ]
    return {
        "phase": contract["phase"],
        "contract_version": contract["contract_version"],
        "upstream_sha256": deepcopy(hashes),
        "workflow": [
            "problem_definition",
            "structural_data_preparation",
            "temporal_split_validation",
            "train_only_eda",
            "feature_engineering",
            "xy_construction",
            "development_only_model_selection",
            "historical_holdout_evaluation",
            "error_interpretation_analysis",
            "final_conclusion_handoff",
        ],
        "dataset_summary": {
            "prepared_rows": phase_01["prepared_rows"],
            "missing_targets_preserved": phase_01["missing_target_after"],
            "timeline_continuous_hourly": phase_01["timeline_continuous_hourly"],
            "development_timestamps": phase_02["development"]["rows"],
            "development_observed_targets": phase_02["development"]["observed_targets"],
            "eligible_supervised_samples": phase_05["development"]["eligible_rows"],
        },
        "validation_summary": {
            "method": phase_02["cross_validation"]["method"],
            "folds": phase_02["cross_validation"]["splits"],
            "shuffle": phase_02["cross_validation"]["shuffle"],
            "holdout_label": one_step["holdout_label"],
            "holdout_claimed_unseen": phase_02["holdout"]["is_claimed_unseen"],
        },
        "official_model": {
            "selected_candidate": model_lock["selected_candidate"],
            "feature_count": phase_04["feature_count"],
            "feature_order": deepcopy(model_lock["feature_order"]),
            "locked_parameters": deepcopy(model_lock["locked_parameters"]),
            "development_cv": deepcopy(official_xgb_cv["aggregate"]),
            "model_lock_changed_after_selection": False,
        },
        "final_evaluation": {
            "one_step": {
                "protocol": one_step["protocol"],
                "candidate_metrics": _one_step_summary(one_step),
                "xgboost_conclusion": {
                    "mae": one_step_xgb["mae"],
                    "rmse": one_step_xgb["rmse"],
                    "n_observations": one_step_xgb["n_observations"],
                    "assessment": "best_of_evaluated_candidates_for_one_step_historical_re_evaluation",
                },
            },
            "recursive_24h": {
                "protocol": recursive["protocol"],
                "candidate_metrics": _recursive_summary(recursive),
                "xgboost_conclusion": {
                    "pooled_mae": recursive_xgb["pooled"]["pooled_mae"],
                    "pooled_rmse": recursive_xgb["pooled"]["pooled_rmse"],
                    "n_predictions": recursive_xgb["pooled"]["n_predictions"],
                    "n_origins": recursive_xgb["pooled"]["n_origins"],
                    "hardest_horizon_by_mae": xgb_recursive_interpretation[
                        "hardest_horizon_by_mae"
                    ],
                    "hardest_horizon_mae": xgb_recursive_interpretation[
                        "hardest_horizon_mae"
                    ],
                    "assessment": "better_than_both_evaluated_baselines_at_all_24_horizons_but_error_accumulates",
                },
            },
        },
        "error_interpretation": {
            "residual_sign": error_analysis["one_step"]["residual_sign"],
            "xgboost_mean_error": xgb_error["mean_error"],
            "xgboost_under_forecast_rate": xgb_error["under_forecast_rate"],
            "xgboost_absolute_error_p95": xgb_error["absolute_error_p95"],
            "residual_acf_lag_1": lag_one["autocorrelation"],
            "residual_acf_lag_1_reference_band": lag_one["reference_band"],
            "residual_white_noise_claim_allowed": False,
            "feature_importance_method": error_analysis["feature_importance"]["method"],
            "feature_group_normalized_gain": deepcopy(
                error_analysis["feature_importance"]["group_normalized_gain"]
            ),
            "causal_claim_allowed": False,
        },
        "assignment_answers": {
            "xgboost_vs_linear_regression": {
                "evidence_type": "post_hoc_development_cv",
                "same_validation_population": linear["comparison"][
                    "same_validation_samples"
                ],
                "validation_samples": linear["aggregate"]["validation_samples"],
                "linear_regression": deepcopy(linear["aggregate"]),
                "xgboost_tuned": deepcopy(official_xgb_cv["aggregate"]),
                "xgboost_mae_improvement_percent": xgb_improvement,
                "conclusion": "XGBoost had lower development CV error on the same validation population, consistent with useful nonlinearities or interactions.",
                "universal_superiority_claim_allowed": False,
            },
            "lag_p_sensitivity": {
                "evidence_type": "post_hoc_development_cv_fixed_xgboost_parameters",
                "results": lag_answer,
                "best_observed_p_by_mean_cv_mae": best_lag_record["p"],
                "conclusion": "Error improved strongly through p=24, improved slightly at p=48, and degraded at p=168; more lags were not always better.",
                "global_optimum_claim_allowed": False,
                "official_feature_schema_changed": False,
            },
            "xgboost_vs_arima": {
                "evidence_type": "conceptual_only",
                "arima_empirically_benchmarked": False,
                "xgboost_may_be_advantageous_when": [
                    "many lag, rolling, and calendar predictors are available",
                    "feature-target relations or interactions are nonlinear",
                    "multiple seasonal signals must be combined",
                    "sufficient data and time-safe validation control model complexity",
                ],
                "arima_may_be_advantageous_when": [
                    "the series is short and approximately linear after stationarity treatment",
                    "a compact AR/MA statistical structure is preferred",
                    "model-based probabilistic intervals are required under validated assumptions",
                ],
                "conclusion": "Practice 3 has no empirical evidence that XGBoost outperforms ARIMA; a fair comparison requires a separate ARIMA benchmark on identical folds, timestamps, and metrics.",
                "head_to_head_superiority_claim_allowed": False,
            },
        },
        "scientific_limitations": limitations,
        "claim_boundary": {
            "primary_supported_use": "one_step_hourly_historical_re_evaluation_with_observed_history",
            "secondary_supported_use": "recursive_24_hour_historical_re_evaluation_with_material_error_accumulation",
            "production_readiness_claimed": False,
            "external_generalization_claimed": False,
            "arima_superiority_claimed": False,
            "causal_interpretation_claimed": False,
        },
        "handoff_readiness": {
            "phase_01_through_phase_08_official_evidence_verified": True,
            "supplemental_evidence_verified": True,
            "model_lock_unchanged": True,
            "training_performed_in_phase_09": False,
            "prediction_performed_in_phase_09": False,
            "holdout_re_evaluated_in_phase_09": False,
            "notebook_and_readme_pending_at_artifact_creation": True,
            "human_final_review_required": True,
        },
        "status": "PASS",
    }


def run_preflight(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Validate all upstream evidence without writing the final artifact."""

    contract, documents, hashes = load_phase_09_inputs(project_root)
    validate_evidence_consistency(contract, documents)
    return {
        "phase": contract["phase"],
        "verified_upstream_artifacts": len(hashes),
        "selected_candidate": documents["phase_06_model_lock"]["selected_candidate"],
        "training_started": False,
        "prediction_started": False,
        "holdout_re_evaluated": False,
        "status": "PASS",
    }


def run_final_conclusion(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Create the official deterministic Phase 9 conclusion artifact."""

    project_root = Path(project_root).resolve()
    contract, documents, hashes = load_phase_09_inputs(project_root)
    conclusion = build_final_conclusion(contract, documents, hashes)
    output_path = project_root / contract["outputs"]["final_conclusion"]
    atomic_write_json(conclusion, output_path)
    if read_json(output_path) != conclusion:
        raise ValueError("Official Phase 9 artifact validation failed.")
    return {
        "final_conclusion": contract["outputs"]["final_conclusion"],
        "final_conclusion_sha256": calculate_sha256(output_path),
        "selected_candidate": conclusion["official_model"]["selected_candidate"],
        "training_performed": False,
        "prediction_performed": False,
        "holdout_re_evaluated": False,
        "status": "PASS",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--preflight", action="store_true")
    actions.add_argument("--run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_preflight() if args.preflight else run_final_conclusion()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
