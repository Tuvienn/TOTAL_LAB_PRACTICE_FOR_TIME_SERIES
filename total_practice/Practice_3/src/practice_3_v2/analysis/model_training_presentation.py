"""Build Phase 6 training diagnostics from validated execution evidence."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from practice_3_v2.data.data_preparation import calculate_sha256


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TUNING_RESULT = Path(
    "runs/P6_model_selection_20261025_002459_c83b80bb/"
    "xgboost_tuning_results.json"
)
OUTPUT_PATH = Path("outputs/results/phase_06_training_diagnostics.json")
TUNING_FIGURE_PATH = Path("outputs/figures/phase_06_tuning_candidates.png")
FOLD_FIGURE_PATH = Path("outputs/figures/phase_06_selected_candidate_folds.png")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _atomic_write_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary_name, output_path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def build_training_diagnostics(
    project_root: Path = PROJECT_ROOT,
    tuning_result_path: Path | None = None,
) -> dict[str, Any]:
    """Validate tuning evidence and return presentation-ready diagnostics."""

    project_root = Path(project_root).resolve()
    tuning_result_path = (
        project_root / DEFAULT_TUNING_RESULT
        if tuning_result_path is None
        else Path(tuning_result_path).resolve()
    )
    cv_path = project_root / "outputs/results/phase_06_cv_results.json"
    lock_path = project_root / "outputs/results/phase_06_model_lock.json"
    cv_result = _load_json(cv_path)
    model_lock = _load_json(lock_path)
    tuning_result = _load_json(tuning_result_path)

    _require(cv_result.get("status") == "PASS", "Official Phase 6 CV is not PASS.")
    _require(model_lock.get("status") == "PASS", "Phase 6 model lock is not PASS.")
    _require(tuning_result.get("status") == "PASS", "Tuning result is not PASS.")
    _require(
        calculate_sha256(cv_path)
        == model_lock["upstream_identities"]["cv_results_sha256"],
        "Official CV checksum does not match the model lock.",
    )
    _require(
        cv_result["selected_candidate"] == model_lock["selected_candidate"],
        "Selected candidate conflicts with the model lock.",
    )
    _require(
        cv_result["holdout_evaluated"] is False
        and model_lock["holdout_evaluated"] is False,
        "Phase 6 diagnostics require a sealed holdout.",
    )

    candidates = tuning_result["sampled_candidates"]
    _require(len(candidates) == 24, "Expected exactly 24 tuning candidates.")
    _require(
        [candidate["candidate_index"] for candidate in candidates]
        == list(range(1, 25)),
        "Tuning candidate indices must be sequential from 1 to 24.",
    )
    for candidate in candidates:
        _require(candidate["status"] == "PASS", "A tuning candidate is not PASS.")
        _require(len(candidate["fold_metrics"]) == 5, "Each candidate must have five folds.")

    selected = tuning_result["selected_parameter_candidate"]
    official_selected = next(
        candidate
        for candidate in cv_result["candidate_results"]
        if candidate["candidate"] == cv_result["selected_candidate"]
    )
    _require(
        selected["candidate_index"] == official_selected["tuning_candidate_index"],
        "Selected tuning index conflicts with official CV evidence.",
    )
    _require(
        selected["parameter_identity"] == official_selected["parameter_identity"],
        "Selected parameter identity conflicts with official CV evidence.",
    )
    _require(
        selected["parameters"] == model_lock["locked_parameters"],
        "Selected parameters conflict with the model lock.",
    )
    for metric in ("mean_cv_mae", "mean_cv_rmse", "cv_mae_standard_deviation"):
        _require(
            np.isclose(
                selected["aggregate"][metric],
                model_lock["selection_evidence"][metric],
                rtol=0.0,
                atol=1e-12,
            ),
            f"Selected {metric} conflicts with the model lock.",
        )

    try:
        stored_tuning_path = tuning_result_path.relative_to(project_root).as_posix()
    except ValueError:
        stored_tuning_path = str(tuning_result_path)
    return {
        "phase": "phase_06_training_diagnostics",
        "contract_version": "1.0.0",
        "upstream_evidence": {
            "cv_results_path": cv_path.relative_to(project_root).as_posix(),
            "cv_results_sha256": calculate_sha256(cv_path),
            "model_lock_path": lock_path.relative_to(project_root).as_posix(),
            "model_lock_sha256": calculate_sha256(lock_path),
            "tuning_result_path": stored_tuning_path,
            "tuning_result_sha256": calculate_sha256(tuning_result_path),
        },
        "scope": {
            "partition": "development_train_validation_only",
            "task": "one_step_hourly_forecasting",
            "holdout_evaluated": False,
        },
        "training_summary": {
            "tuning_candidates": len(candidates),
            "folds_per_candidate": 5,
            "completed_tuning_fits": sum(
                len(candidate["fold_metrics"]) for candidate in candidates
            ),
            "early_stopping": False,
            "per_boosting_round_metrics_available": False,
            "folds_are_epochs": False,
        },
        "tuning_candidates": [
            {
                "candidate_index": candidate["candidate_index"],
                "parameter_identity": candidate["parameter_identity"],
                "mean_cv_mae": candidate["aggregate"]["mean_cv_mae"],
                "mean_cv_rmse": candidate["aggregate"]["mean_cv_rmse"],
                "cv_mae_standard_deviation": candidate["aggregate"]
                ["cv_mae_standard_deviation"],
                "selected": candidate["candidate_index"]
                == selected["candidate_index"],
            }
            for candidate in candidates
        ],
        "selected_candidate": {
            "model": model_lock["selected_candidate"],
            "tuning_candidate_index": selected["candidate_index"],
            "parameter_identity": selected["parameter_identity"],
            "parameters": model_lock["locked_parameters"],
            "aggregate": selected["aggregate"],
            "fold_metrics": selected["fold_metrics"],
        },
        "status": "PASS",
    }


def save_tuning_candidates_figure(
    diagnostics: dict[str, Any], output_path: Path
) -> None:
    """Plot mean CV metrics for all 24 tuning candidates."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = diagnostics["tuning_candidates"]
    indices = [row["candidate_index"] for row in rows]
    selected_index = diagnostics["selected_candidate"]["tuning_candidate_index"]
    colors = ["#ef8354" if index == selected_index else "#2b6ca3" for index in indices]
    figure, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    for axis, key, label in (
        (axes[0], "mean_cv_mae", "Mean CV MAE (MW)"),
        (axes[1], "mean_cv_rmse", "Mean CV RMSE (MW)"),
    ):
        values = [row[key] for row in rows]
        axis.bar(indices, values, color=colors, width=0.78)
        axis.axhline(
            values[selected_index - 1],
            color="#ef8354",
            linestyle="--",
            linewidth=1.2,
            label=f"Selected candidate {selected_index}",
        )
        axis.set_ylabel(label)
        axis.grid(axis="y", alpha=0.25)
        axis.legend(loc="upper right")
    axes[0].set_title("XGBoost Tuning Candidates — Development CV Only")
    axes[1].set_xlabel("Tuning candidate index")
    axes[1].set_xticks(indices)
    figure.tight_layout()
    figure.savefig(
        output_path,
        dpi=160,
        metadata={"Software": "Practice_3"},
    )
    plt.close(figure)


def save_selected_folds_figure(
    diagnostics: dict[str, Any], output_path: Path
) -> None:
    """Plot the selected candidate's final metric on each temporal fold."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics = diagnostics["selected_candidate"]["fold_metrics"]
    folds = [row["fold"] for row in metrics]
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for axis, key, label, color in (
        (axes[0], "mae", "MAE (MW)", "#2b6ca3"),
        (axes[1], "rmse", "RMSE (MW)", "#2a9d8f"),
    ):
        values = [row[key] for row in metrics]
        mean_value = float(np.mean(values))
        axis.bar(folds, values, color=color, width=0.65)
        axis.axhline(
            mean_value,
            color="#ef8354",
            linestyle="--",
            linewidth=1.5,
            label=f"Mean = {mean_value:.3f}",
        )
        axis.set_xlabel("Expanding-window fold")
        axis.set_ylabel(label)
        axis.set_xticks(folds)
        axis.grid(axis="y", alpha=0.25)
        axis.legend(loc="upper right")
    figure.suptitle("Selected XGBoost Candidate Across Five Temporal Folds")
    figure.tight_layout()
    figure.savefig(
        output_path,
        dpi=160,
        metadata={"Software": "Practice_3"},
    )
    plt.close(figure)


def run(
    project_root: Path = PROJECT_ROOT,
    tuning_result_path: Path | None = None,
    output_path: Path | None = None,
    tuning_figure_path: Path | None = None,
    fold_figure_path: Path | None = None,
) -> dict[str, Any]:
    """Generate the official Phase 6 presentation bundle."""

    project_root = Path(project_root).resolve()
    output_path = project_root / OUTPUT_PATH if output_path is None else Path(output_path)
    tuning_figure_path = (
        project_root / TUNING_FIGURE_PATH
        if tuning_figure_path is None
        else Path(tuning_figure_path)
    )
    fold_figure_path = (
        project_root / FOLD_FIGURE_PATH
        if fold_figure_path is None
        else Path(fold_figure_path)
    )
    diagnostics = build_training_diagnostics(project_root, tuning_result_path)
    save_tuning_candidates_figure(diagnostics, tuning_figure_path)
    save_selected_folds_figure(diagnostics, fold_figure_path)

    figures = []
    for name, path in (
        ("tuning_candidates", tuning_figure_path),
        ("selected_candidate_folds", fold_figure_path),
    ):
        try:
            stored_path = path.relative_to(project_root).as_posix()
        except ValueError:
            stored_path = str(path)
        figures.append(
            {
                "name": name,
                "path": stored_path,
                "sha256": calculate_sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    diagnostics["figures"] = figures
    _atomic_write_json(diagnostics, output_path)
    return diagnostics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--tuning-result", type=Path, default=None)
    args = parser.parse_args()
    if not args.run:
        parser.error("Use --run to generate Phase 6 training diagnostics.")
    result = run(tuning_result_path=args.tuning_result)
    print(
        json.dumps(
            {
                "output": OUTPUT_PATH.as_posix(),
                "selected_candidate": result["selected_candidate"]["model"],
                "tuning_fits": result["training_summary"]["completed_tuning_fits"],
                "status": result["status"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
