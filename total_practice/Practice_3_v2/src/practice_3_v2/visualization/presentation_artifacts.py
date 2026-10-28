from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import pandas as pd

from practice_3_v2.data.data_preparation import PROJECT_ROOT, calculate_sha256


@dataclass(frozen=True)
class PresentationArtifacts:
    project_root: Path
    prepared_path: Path
    prepared_data: pd.DataFrame
    phase_01_audit: dict[str, Any]
    phase_02_audit: dict[str, Any]
    phase_03_audit: dict[str, Any]
    phase_03_presentation: dict[str, Any]
    phase_04_audit: dict[str, Any]
    phase_04_presentation: dict[str, Any]
    phase_05_audit: dict[str, Any]
    phase_06_cv: dict[str, Any]
    phase_06_lock: dict[str, Any]
    phase_06_training_diagnostics: dict[str, Any]
    phase_06_supplemental_linear: dict[str, Any]
    phase_06_supplemental_lag: dict[str, Any]
    phase_06_supplemental_audit: dict[str, Any]
    phase_06_figure_path: Path
    phase_06_tuning_figure_path: Path
    phase_06_fold_figure_path: Path
    phase_06_supplemental_model_figure_path: Path
    phase_06_supplemental_lag_figure_path: Path


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_presentation_artifacts(artifacts: PresentationArtifacts) -> None:
    phase_01 = artifacts.phase_01_audit
    phase_02 = artifacts.phase_02_audit
    phase_03 = artifacts.phase_03_audit
    phase_03_presentation = artifacts.phase_03_presentation
    phase_04 = artifacts.phase_04_audit
    phase_04_presentation = artifacts.phase_04_presentation
    phase_05 = artifacts.phase_05_audit
    phase_06_cv = artifacts.phase_06_cv
    phase_06_lock = artifacts.phase_06_lock
    training_diagnostics = artifacts.phase_06_training_diagnostics
    supplemental_linear = artifacts.phase_06_supplemental_linear
    supplemental_lag = artifacts.phase_06_supplemental_lag
    supplemental_audit = artifacts.phase_06_supplemental_audit

    _require(phase_01["status"] == "PASS", "Phase 1 audit is not PASS.")
    _require(
        calculate_sha256(artifacts.prepared_path) == phase_01["processed_sha256"],
        "Prepared dataset checksum does not match Phase 1 evidence.",
    )
    for phase_name, audit in (
        ("Phase 2", phase_02),
        ("Phase 3", phase_03),
        ("Phase 4", phase_04),
        ("Phase 5", phase_05),
    ):
        _require(audit["status"] == "PASS", f"{phase_name} audit is not PASS.")
        _require(
            audit["prepared_sha256"] == phase_01["processed_sha256"],
            f"{phase_name} prepared-data identity is inconsistent.",
        )
    for figure_record in phase_03["figures"]:
        figure_path = artifacts.project_root / figure_record["path"]
        _require(figure_path.is_file(), f"Missing Phase 3 figure: {figure_path}")
        _require(
            calculate_sha256(figure_path) == figure_record["sha256"],
            f"Phase 3 figure checksum mismatch: {figure_path}",
        )
    _require(
        phase_03_presentation["status"] == "PASS",
        "Phase 3 presentation evidence is not PASS.",
    )
    _require(
        phase_03_presentation["canonical_eda_sha256"]
        == calculate_sha256(
            artifacts.project_root / "outputs/results/phase_03_eda_summary.json"
        ),
        "Phase 3 presentation evidence references a different EDA audit.",
    )
    _require(
        phase_03_presentation["scope"]["holdout_target_values_inspected"]
        is False,
        "Phase 3 presentation evidence inspected holdout targets.",
    )
    phase_03_presentation_figure = (
        artifacts.project_root / phase_03_presentation["figure"]["path"]
    )
    _require(
        phase_03_presentation_figure.is_file(),
        "Phase 3 annual-stability figure is missing.",
    )
    _require(
        calculate_sha256(phase_03_presentation_figure)
        == phase_03_presentation["figure"]["sha256"],
        "Phase 3 annual-stability figure checksum mismatch.",
    )
    _require(
        phase_04_presentation["status"] == "PASS",
        "Phase 4 presentation evidence is not PASS.",
    )
    _require(
        phase_04_presentation["canonical_phase_04_sha256"]
        == calculate_sha256(
            artifacts.project_root / "outputs/results/phase_04_feature_validation.json"
        ),
        "Phase 4 presentation evidence references a different feature audit.",
    )
    _require(
        phase_04_presentation["scope"]["holdout_target_values_inspected"]
        is False,
        "Phase 4 presentation evidence inspected holdout targets.",
    )
    phase_04_presentation_figure = (
        artifacts.project_root / phase_04_presentation["figure"]["path"]
    )
    _require(
        phase_04_presentation_figure.is_file(),
        "Phase 4 correlation figure is missing.",
    )
    _require(
        calculate_sha256(phase_04_presentation_figure)
        == phase_04_presentation["figure"]["sha256"],
        "Phase 4 correlation figure checksum mismatch.",
    )
    _require(phase_06_cv["status"] == "PASS", "Phase 6 CV result is not PASS.")
    _require(phase_06_lock["status"] == "PASS", "Phase 6 model lock is not PASS.")
    _require(
        calculate_sha256(artifacts.project_root / "outputs/results/phase_06_cv_results.json")
        == phase_06_lock["upstream_identities"]["cv_results_sha256"],
        "Phase 6 CV checksum does not match the model lock.",
    )
    _require(
        phase_06_cv["selected_candidate"] == phase_06_lock["selected_candidate"],
        "Phase 6 selected candidate is inconsistent.",
    )
    _require(phase_06_cv["holdout_evaluated"] is False, "Phase 6 opened the holdout.")
    _require(
        phase_06_lock["binary_model_persisted"] is False,
        "Phase 6 unexpectedly persisted a binary model.",
    )
    _require(
        training_diagnostics["status"] == "PASS",
        "Phase 6 training diagnostics are not PASS.",
    )
    _require(
        training_diagnostics["upstream_evidence"]["cv_results_sha256"]
        == calculate_sha256(
            artifacts.project_root / "outputs/results/phase_06_cv_results.json"
        ),
        "Phase 6 training diagnostics reference different CV evidence.",
    )
    _require(
        training_diagnostics["upstream_evidence"]["model_lock_sha256"]
        == calculate_sha256(
            artifacts.project_root / "outputs/results/phase_06_model_lock.json"
        ),
        "Phase 6 training diagnostics reference a different model lock.",
    )
    _require(
        training_diagnostics["scope"]["holdout_evaluated"] is False,
        "Phase 6 training diagnostics opened the holdout.",
    )
    _require(
        training_diagnostics["training_summary"]["completed_tuning_fits"] == 120,
        "Phase 6 training diagnostics do not contain 24 × 5 tuning fits.",
    )
    for figure_record in training_diagnostics["figures"]:
        figure_path = artifacts.project_root / figure_record["path"]
        _require(figure_path.is_file(), f"Missing Phase 6 diagnostic figure: {figure_path}")
        _require(
            calculate_sha256(figure_path) == figure_record["sha256"],
            f"Phase 6 diagnostic figure checksum mismatch: {figure_path}",
        )
    for name, artifact in (
        ("Linear Regression", supplemental_linear),
        ("Lag sensitivity", supplemental_lag),
        ("Supplemental audit", supplemental_audit),
    ):
        _require(artifact["status"] == "PASS", f"{name} artifact is not PASS.")
    _require(
        supplemental_audit["completed_project_data_fits"] == 35,
        "Supplemental execution did not complete 35 fits.",
    )
    supplemental_components = {
        "linear_regression": artifacts.project_root
        / "outputs/results/phase_06_supplemental_linear_regression.json",
        "lag_sensitivity": artifacts.project_root
        / "outputs/results/phase_06_supplemental_lag_sensitivity.json",
        "model_comparison_figure": artifacts.phase_06_supplemental_model_figure_path,
        "lag_sensitivity_figure": artifacts.phase_06_supplemental_lag_figure_path,
    }
    for component, path in supplemental_components.items():
        _require(
            calculate_sha256(path) == supplemental_audit["component_sha256"][component],
            f"Supplemental component checksum mismatch: {component}",
        )
    _require(
        calculate_sha256(artifacts.project_root / "outputs/results/phase_06_model_lock.json")
        == supplemental_audit["upstream_evidence"]["verified_upstream_sha256"][
            "phase_06_model_lock"
        ],
        "Supplemental evidence references a different Phase 6 model lock.",
    )
    _require(
        supplemental_audit["checks"]["selection_authority"] == "none",
        "Supplemental evidence changed selection authority.",
    )
    _require(
        supplemental_audit["checks"]["holdout_evaluated"] is False,
        "Supplemental execution evaluated the holdout.",
    )


def load_presentation_artifacts(
    project_root: Path = PROJECT_ROOT,
) -> PresentationArtifacts:
    project_root = Path(project_root).resolve()
    paths = {
        "prepared": project_root / "datasets/processed/aep_hourly_prepared.csv",
        "phase_01": project_root / "outputs/results/phase_01_data_quality.json",
        "phase_02": project_root / "outputs/results/phase_02_temporal_split.json",
        "phase_03": project_root / "outputs/results/phase_03_eda_summary.json",
        "phase_03_presentation": project_root
        / "outputs/results/phase_03_eda_presentation.json",
        "phase_04": project_root / "outputs/results/phase_04_feature_validation.json",
        "phase_04_presentation": project_root
        / "outputs/results/phase_04_feature_presentation.json",
        "phase_05": project_root / "outputs/results/phase_05_supervised_dataset.json",
        "phase_06_cv": project_root / "outputs/results/phase_06_cv_results.json",
        "phase_06_lock": project_root / "outputs/results/phase_06_model_lock.json",
        "phase_06_training_diagnostics": project_root
        / "outputs/results/phase_06_training_diagnostics.json",
        "supplemental_linear": project_root
        / "outputs/results/phase_06_supplemental_linear_regression.json",
        "supplemental_lag": project_root
        / "outputs/results/phase_06_supplemental_lag_sensitivity.json",
        "supplemental_audit": project_root
        / "outputs/results/phase_06_supplemental_audit.json",
        "phase_06_figure": project_root / "outputs/figures/phase_06_cv_comparison.png",
        "phase_06_tuning_figure": project_root
        / "outputs/figures/phase_06_tuning_candidates.png",
        "phase_06_fold_figure": project_root
        / "outputs/figures/phase_06_selected_candidate_folds.png",
        "supplemental_model_figure": project_root
        / "outputs/figures/phase_06_supplemental_model_comparison.png",
        "supplemental_lag_figure": project_root
        / "outputs/figures/phase_06_supplemental_lag_sensitivity.png",
        "data_contract": project_root / "config/data_contract.json",
        "forecasting_contract": project_root / "config/forecasting_contract.json",
        "temporal_split_contract": project_root / "config/temporal_split.json",
    }
    missing_paths = [str(path) for path in paths.values() if not path.is_file()]
    if missing_paths:
        raise FileNotFoundError(f"Missing presentation artifacts: {missing_paths}")
    for name in ("data_contract", "forecasting_contract", "temporal_split_contract"):
        _load_json(paths[name])
    artifacts = PresentationArtifacts(
        project_root=project_root,
        prepared_path=paths["prepared"],
        prepared_data=pd.read_csv(paths["prepared"], parse_dates=["Datetime"]),
        phase_01_audit=_load_json(paths["phase_01"]),
        phase_02_audit=_load_json(paths["phase_02"]),
        phase_03_audit=_load_json(paths["phase_03"]),
        phase_03_presentation=_load_json(paths["phase_03_presentation"]),
        phase_04_audit=_load_json(paths["phase_04"]),
        phase_04_presentation=_load_json(paths["phase_04_presentation"]),
        phase_05_audit=_load_json(paths["phase_05"]),
        phase_06_cv=_load_json(paths["phase_06_cv"]),
        phase_06_lock=_load_json(paths["phase_06_lock"]),
        phase_06_training_diagnostics=_load_json(paths["phase_06_training_diagnostics"]),
        phase_06_supplemental_linear=_load_json(paths["supplemental_linear"]),
        phase_06_supplemental_lag=_load_json(paths["supplemental_lag"]),
        phase_06_supplemental_audit=_load_json(paths["supplemental_audit"]),
        phase_06_figure_path=paths["phase_06_figure"],
        phase_06_tuning_figure_path=paths["phase_06_tuning_figure"],
        phase_06_fold_figure_path=paths["phase_06_fold_figure"],
        phase_06_supplemental_model_figure_path=paths["supplemental_model_figure"],
        phase_06_supplemental_lag_figure_path=paths["supplemental_lag_figure"],
    )
    validate_presentation_artifacts(artifacts)
    return artifacts
