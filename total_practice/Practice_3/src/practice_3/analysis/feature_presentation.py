"""Build development-only feature-correlation evidence for presentation."""

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
import pandas as pd

from practice_3.analysis.eda import extract_development_data
from practice_3.analysis.feature_engineering import (
    build_time_safe_features,
    load_phase_04_inputs,
    validate_feature_frame,
)
from practice_3.data.data_preparation import calculate_sha256
from practice_3.data.temporal_split import validate_prepared_input


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = Path("outputs/results/phase_04_feature_presentation.json")
FIGURE_PATH = Path("outputs/figures/phase_04_temporal_feature_correlation.png")


def build_correlation_evidence(
    project_root: Path = PROJECT_ROOT,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Calculate pairwise Pearson correlations on Development only."""

    project_root = Path(project_root).resolve()
    (
        data_contract,
        preparation_contract,
        split_contract,
        feature_contract,
        phase_01_audit,
        _phase_02_audit,
        _phase_03_audit,
    ) = load_phase_04_inputs(project_root)
    phase_04_path = project_root / "outputs/results/phase_04_feature_validation.json"
    phase_04_audit = json.loads(phase_04_path.read_text(encoding="utf-8"))
    if phase_04_audit.get("status") != "PASS":
        raise ValueError("Canonical Phase 4 audit must be PASS.")
    if calculate_sha256(phase_04_path) == "":
        raise ValueError("Canonical Phase 4 audit identity is unavailable.")
    prepared, prepared_sha256 = validate_prepared_input(
        project_root / feature_contract["prepared_input"],
        data_contract,
        preparation_contract,
        split_contract,
        phase_01_audit,
    )
    if prepared_sha256 != phase_04_audit["prepared_sha256"]:
        raise ValueError("Prepared identity conflicts with Phase 4 evidence.")
    development = extract_development_data(prepared, data_contract, split_contract)
    features = build_time_safe_features(
        development, data_contract, feature_contract
    )
    validate_feature_frame(
        features, development, data_contract, feature_contract
    )
    temporal_features = (
        phase_04_audit["feature_groups"]["lags"]
        + phase_04_audit["feature_groups"]["rolling"]
    )
    target_column = data_contract["target_column"]
    analysis_frame = pd.concat(
        [
            development[target_column].rename("AEP_MW (target)"),
            features[temporal_features],
        ],
        axis=1,
    )
    correlation = analysis_frame.corr(method="pearson", min_periods=2)
    valid_pairs = analysis_frame.notna().astype("int64").T.dot(
        analysis_frame.notna().astype("int64")
    )
    if correlation.shape != (13, 13):
        raise ValueError("Expected target plus 12 temporal features.")
    evidence = {
        "phase": "phase_04_feature_presentation",
        "contract_version": "1.0.0",
        "canonical_phase_04_sha256": calculate_sha256(phase_04_path),
        "prepared_sha256": prepared_sha256,
        "scope": {
            "partition": "development_train_validation_only",
            "rows": int(len(development)),
            "holdout_target_values_inspected": False,
        },
        "method": "pairwise_pearson",
        "variables": correlation.columns.tolist(),
        "interpretation": (
            "Descriptive linear association only; not causal evidence or "
            "XGBoost feature importance."
        ),
        "status": "PASS",
    }
    return correlation, valid_pairs, evidence


def save_correlation_heatmap(
    correlation: pd.DataFrame,
    output_path: Path,
) -> None:
    """Render a complete correlation heatmap."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    values = correlation.to_numpy(dtype="float64")
    figure, axis = plt.subplots(figsize=(13.5, 11))
    image = axis.imshow(values, cmap="RdBu_r", vmin=-1, vmax=1)
    labels = correlation.columns.tolist()
    axis.set_xticks(range(len(labels)), labels, rotation=55, ha="right")
    axis.set_yticks(range(len(labels)), labels)
    axis.set_title(
        "Target, Lag and Rolling Feature Correlation — Development Only",
        pad=18,
    )
    for row in range(len(labels)):
        for column in range(len(labels)):
            value = values[row, column]
            text_color = "white" if abs(value) >= 0.55 else "black"
            axis.text(
                column,
                row,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color=text_color,
            )
    colorbar = figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    colorbar.set_label("Pearson correlation")
    figure.text(
        0.5,
        0.01,
        "Pairwise complete observations. Correlation is descriptive and does not equal feature importance.",
        ha="center",
        fontsize=9,
    )
    figure.tight_layout(rect=(0, 0.035, 1, 1))
    figure.savefig(
        output_path,
        dpi=160,
        metadata={"Software": "Practice_3"},
    )
    plt.close(figure)


def atomic_write_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output_path.parent, prefix=f".{output_path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary_name, output_path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def run(
    project_root: Path = PROJECT_ROOT,
    output_path: Path | None = None,
    figure_path: Path | None = None,
) -> dict[str, Any]:
    project_root = Path(project_root).resolve()
    output_path = project_root / OUTPUT_PATH if output_path is None else Path(output_path)
    figure_path = project_root / FIGURE_PATH if figure_path is None else Path(figure_path)
    correlation, valid_pairs, evidence = build_correlation_evidence(project_root)
    save_correlation_heatmap(correlation, figure_path)
    try:
        stored_figure_path = figure_path.relative_to(project_root).as_posix()
    except ValueError:
        stored_figure_path = str(figure_path)
    evidence["correlation_matrix"] = {
        row: {column: float(value) for column, value in values.items()}
        for row, values in correlation.to_dict(orient="index").items()
    }
    evidence["valid_pair_counts"] = {
        row: {column: int(value) for column, value in values.items()}
        for row, values in valid_pairs.to_dict(orient="index").items()
    }
    evidence["figure"] = {
        "name": "temporal_feature_correlation",
        "path": stored_figure_path,
        "sha256": calculate_sha256(figure_path),
        "bytes": figure_path.stat().st_size,
    }
    atomic_write_json(evidence, output_path)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        parser.error("Use --run to generate Phase 4 presentation evidence.")
    result = run()
    print(json.dumps({"output": OUTPUT_PATH.as_posix(), "status": result["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
