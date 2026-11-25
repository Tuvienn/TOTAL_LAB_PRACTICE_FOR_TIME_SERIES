"""Build Phase 5 supervised-conversion evidence for presentation."""

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
from matplotlib.patches import FancyBboxPatch

from practice_3_v2.analysis.eda import extract_development_data
from practice_3_v2.data.data_preparation import calculate_sha256
from practice_3_v2.data.supervised_dataset import (
    build_supervised_candidates,
    load_phase_05_inputs,
)
from practice_3_v2.data.temporal_split import validate_prepared_input


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = Path("outputs/results/phase_05_supervised_presentation.json")
FIGURE_PATH = Path("outputs/figures/phase_05_time_series_to_supervised.png")


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


def build_supervised_presentation(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    """Reconstruct one Development-only sample and validate Phase 5 counts."""

    project_root = Path(project_root).resolve()
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
    audit_path = project_root / supervised_contract["outputs"]["audit"]
    with audit_path.open(encoding="utf-8") as file:
        phase_05_audit = json.load(file)
    if phase_05_audit.get("status") != "PASS":
        raise ValueError("Canonical Phase 5 audit must be PASS.")

    prepared, prepared_sha256 = validate_prepared_input(
        project_root / supervised_contract["prepared_input"],
        data_contract,
        preparation_contract,
        split_contract,
        phase_01_audit,
    )
    development = extract_development_data(
        prepared,
        data_contract,
        split_contract,
    )
    candidates = build_supervised_candidates(
        development,
        data_contract,
        feature_contract,
        supervised_contract,
    )
    eligible = candidates.loc[candidates["is_eligible"]]
    if len(candidates) != phase_05_audit["development"]["raw_rows"]:
        raise ValueError("Candidate count conflicts with the Phase 5 audit.")
    if len(eligible) != phase_05_audit["development"]["eligible_rows"]:
        raise ValueError("Eligible count conflicts with the Phase 5 audit.")
    if eligible.empty:
        raise ValueError("Phase 5 has no eligible supervised sample.")

    sample = eligible.iloc[0]
    feature_values = {
        feature: float(sample[feature])
        for feature in supervised_contract["feature_order"]
    }
    development_audit = phase_05_audit["development"]
    return {
        "phase": "phase_05_supervised_presentation",
        "contract_version": "1.0.0",
        "upstream_evidence": {
            "phase_05_audit_path": audit_path.relative_to(project_root).as_posix(),
            "phase_05_audit_sha256": calculate_sha256(audit_path),
            "prepared_sha256": prepared_sha256,
        },
        "scope": {
            "partition": "development_train_validation_only",
            "holdout_features_materialized": False,
            "holdout_target_values_inspected": False,
            "training_executed": False,
        },
        "notation": {
            "forecast_origin": "t",
            "target_timestamp": "T = t + 1 hour",
            "feature_semantics": "X(T) uses target history through t",
            "label_semantics": "y(T) is AEP_MW at target timestamp T",
        },
        "feature_groups": {
            "lag": 8,
            "rolling": 4,
            "calendar": 10,
            "total": len(supervised_contract["feature_order"]),
        },
        "example_sample": {
            "target_timestamp": sample["target_timestamp"].strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "forecast_origin": sample["forecast_origin"].strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "feature_values": feature_values,
            "target_name": data_contract["target_column"],
            "target_value": float(sample[data_contract["target_column"]]),
        },
        "matrix_summary": {
            "candidate_rows": development_audit["raw_rows"],
            "eligible_samples": development_audit["eligible_rows"],
            "feature_count": phase_05_audit["feature_count"],
            "x_shape": [
                development_audit["eligible_rows"],
                phase_05_audit["feature_count"],
            ],
            "y_shape": [development_audit["eligible_rows"]],
            "excluded_samples": development_audit["excluded_rows"],
            "invalid_feature_vector": development_audit[
                "invalid_feature_vector"
            ],
            "missing_target_with_valid_features": development_audit[
                "missing_target_with_valid_features"
            ],
            "imputation": supervised_contract["eligibility"]["imputation"],
            "shuffle": supervised_contract["eligibility"]["shuffle"],
        },
        "status": "PASS",
    }


def _add_box(
    axis: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    facecolor: str,
) -> None:
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        linewidth=1.2,
        edgecolor="#334155",
        facecolor=facecolor,
    )
    axis.add_patch(box)
    axis.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=10.5,
        color="#0f172a",
    )


def _add_arrow(
    axis: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
) -> None:
    axis.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={"arrowstyle": "->", "color": "#475569", "lw": 1.7},
    )


def save_conversion_figure(
    evidence: dict[str, Any],
    output_path: Path,
) -> None:
    """Visualize how one time-series timestamp becomes one X/y sample."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = evidence["matrix_summary"]
    figure, axis = plt.subplots(figsize=(14, 6.6))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")
    figure.patch.set_facecolor("white")
    axis.set_facecolor("white")
    axis.set_title(
        "Time Series to Supervised Learning — One-step Forecasting",
        fontsize=16,
        pad=18,
        color="#0f172a",
    )

    _add_box(
        axis,
        0.03,
        0.38,
        0.18,
        0.24,
        "AEP_MW time series\nHistory through origin t\n(t−168h … t)",
        "#dbeafe",
    )
    _add_arrow(axis, (0.21, 0.50), (0.28, 0.50))
    _add_box(
        axis,
        0.28,
        0.30,
        0.20,
        0.40,
        "Feature construction\nfor target T = t + 1h\n\n8 lag features\n4 rolling features\n10 calendar features",
        "#dcfce7",
    )
    _add_arrow(axis, (0.48, 0.50), (0.55, 0.50))
    _add_box(
        axis,
        0.55,
        0.58,
        0.17,
        0.18,
        "X(T)\n22 time-safe features",
        "#fef3c7",
    )
    _add_box(
        axis,
        0.55,
        0.24,
        0.17,
        0.18,
        "y(T)\nAEP_MW at target T",
        "#fee2e2",
    )
    axis.plot(
        [0.735, 0.76, 0.76, 0.735],
        [0.76, 0.76, 0.24, 0.24],
        color="#475569",
        linewidth=1.7,
    )
    axis.text(
        0.75,
        0.82,
        "One supervised sample\n(X(T), y(T))",
        ha="center",
        va="bottom",
        fontsize=10.5,
        color="#334155",
    )
    _add_arrow(axis, (0.77, 0.50), (0.90, 0.50))
    _add_box(
        axis,
        0.90,
        0.35,
        0.085,
        0.30,
        (
            f"Repeat\n\nX: {summary['eligible_samples']:,} × "
            f"{summary['feature_count']}\n"
            f"y: {summary['eligible_samples']:,}"
        ),
        "#ede9fe",
    )
    axis.text(
        0.50,
        0.08,
        (
            "Leakage control: y(T) is never included in X(T); rolling features "
            "are shifted by one hour before aggregation."
        ),
        ha="center",
        fontsize=10,
        color="#475569",
    )
    figure.tight_layout()
    figure.savefig(
        output_path,
        dpi=160,
        facecolor="white",
        metadata={"Software": "Practice_3"},
    )
    plt.close(figure)


def run(
    project_root: Path = PROJECT_ROOT,
    output_path: Path | None = None,
    figure_path: Path | None = None,
) -> dict[str, Any]:
    """Generate the official Phase 5 presentation bundle."""

    project_root = Path(project_root).resolve()
    output_path = project_root / OUTPUT_PATH if output_path is None else Path(output_path)
    figure_path = project_root / FIGURE_PATH if figure_path is None else Path(figure_path)
    evidence = build_supervised_presentation(project_root)
    save_conversion_figure(evidence, figure_path)
    try:
        stored_path = figure_path.relative_to(project_root).as_posix()
    except ValueError:
        stored_path = str(figure_path)
    evidence["figure"] = {
        "name": "time_series_to_supervised",
        "path": stored_path,
        "sha256": calculate_sha256(figure_path),
        "bytes": figure_path.stat().st_size,
    }
    _atomic_write_json(evidence, output_path)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        parser.error("Use --run to generate Phase 5 presentation evidence.")
    result = run()
    print(
        json.dumps(
            {
                "output": OUTPUT_PATH.as_posix(),
                "eligible_samples": result["matrix_summary"]["eligible_samples"],
                "status": result["status"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
