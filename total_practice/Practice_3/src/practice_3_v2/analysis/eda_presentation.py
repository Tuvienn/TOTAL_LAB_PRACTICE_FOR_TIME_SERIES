"""Build extended, development-only EDA evidence for presentation."""

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
import pandas as pd

from practice_3_v2.analysis.eda import extract_development_data
from practice_3_v2.data.data_preparation import calculate_sha256


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = Path("outputs/results/phase_03_eda_presentation.json")
FIGURE_PATH = Path("outputs/figures/phase_03_annual_stability.png")


def build_annual_stability(
    development: pd.DataFrame,
    timestamp_column: str = "Datetime",
    target_column: str = "AEP_MW",
) -> pd.DataFrame:
    """Summarize annual target level and variability with coverage context."""

    observed = development.loc[
        development[target_column].notna(), [timestamp_column, target_column]
    ].copy()
    observed["year"] = observed[timestamp_column].dt.year
    summary = (
        observed.groupby("year", as_index=False, sort=True)[target_column]
        .agg(["mean", "std", "median", "count"])
        .reset_index()
        .rename(
            columns={
                "mean": "mean_target",
                "std": "standard_deviation",
                "median": "median_target",
                "count": "observed_count",
            }
        )
    )
    timeline_counts = (
        development.assign(year=development[timestamp_column].dt.year)
        .groupby("year", sort=True)
        .size()
    )
    summary["timeline_count"] = summary["year"].map(timeline_counts).astype(int)
    summary["coverage_rate"] = (
        summary["observed_count"] / summary["timeline_count"]
    )
    summary["partial_year"] = summary["year"].isin(
        [int(summary["year"].min()), int(summary["year"].max())]
    )
    return summary


def save_annual_stability_figure(
    annual: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save annual mean and variability without implying holdout access."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    axes[0].plot(
        annual["year"], annual["mean_target"], marker="o", color="#245782"
    )
    axes[0].set(title="Annual Mean — Development Only", ylabel="Mean AEP_MW (MW)")
    axes[1].plot(
        annual["year"],
        annual["standard_deviation"],
        marker="o",
        color="#d1495b",
    )
    axes[1].set(
        title="Annual Variability — Development Only",
        xlabel="Year",
        ylabel="Standard deviation (MW)",
    )
    axes[1].set_xticks(annual["year"])
    for axis in axes:
        axis.grid(alpha=0.2)
    figure.text(
        0.5,
        0.01,
        "2004 and 2017 are partial years; interpret their annual summaries with caution.",
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


def _native_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(frame.to_json(orient="records"))


def build_presentation_evidence(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Build explanatory EDA tables from validated canonical evidence."""

    project_root = Path(project_root).resolve()

    def load_json(relative_path: str) -> dict[str, Any]:
        return json.loads((project_root / relative_path).read_text(encoding="utf-8"))

    phase_01 = load_json("outputs/results/phase_01_data_quality.json")
    phase_02 = load_json("outputs/results/phase_02_temporal_split.json")
    phase_03 = load_json("outputs/results/phase_03_eda_summary.json")
    phase_04 = load_json("outputs/results/phase_04_feature_validation.json")
    if any(
        artifact.get("status") != "PASS"
        for artifact in (phase_01, phase_02, phase_03, phase_04)
    ):
        raise ValueError("Phase 1–4 canonical evidence must be PASS.")
    prepared_path = project_root / "datasets/processed/aep_hourly_prepared.csv"
    if calculate_sha256(prepared_path) != phase_01["processed_sha256"]:
        raise ValueError("Prepared dataset checksum does not match Phase 1 evidence.")
    if any(
        artifact["prepared_sha256"] != phase_01["processed_sha256"]
        for artifact in (phase_02, phase_03, phase_04)
    ):
        raise ValueError("Phase 1–4 prepared-data identities are inconsistent.")
    split_contract = json.loads(
        (project_root / "config/temporal_split.json").read_text(
            encoding="utf-8"
        )
    )
    data_contract = json.loads(
        (project_root / "config/data_contract.json").read_text(
            encoding="utf-8"
        )
    )
    development = extract_development_data(
        pd.read_csv(prepared_path, parse_dates=[data_contract["timestamp_column"]]),
        data_contract,
        split_contract,
    )
    annual = build_annual_stability(development)
    lag_values = pd.DataFrame(phase_03["lag_correlation"]["values"])
    top_lags = lag_values.sort_values(
        ["correlation", "lag_hours"], ascending=[False, True], kind="stable"
    ).head(10)
    top_anomalies = phase_03["anomaly_screening"]["top_candidates"][:10]
    quality_recap = {
        "raw_duplicate_timestamps": phase_01["duplicate_timestamps_before"],
        "raw_missing_hourly_timestamps": phase_01[
            "missing_hourly_timestamps_before"
        ],
        "development_missing_targets": phase_03["missingness"]["missing_targets"],
        "duplicate_policy": phase_01["policies"]["duplicate_treatment"],
        "missing_policy": "Giữ timeline theo giờ; không impute trong EDA",
        "anomaly_policy": "Chỉ screening; không xóa, clip hoặc thay target",
    }
    decisions = [
        {
            "eda_finding": "Phụ thuộc rất mạnh ở lag 1 giờ",
            "evidence": f"r={lag_values.loc[lag_values['lag_hours'].eq(1), 'correlation'].iloc[0]:.4f}",
            "phase_04_decision": "lag_1h, lag_2h, lag_3h",
        },
        {
            "eda_finding": "Chu kỳ ngày nổi bật",
            "evidence": f"lag 24h: r={lag_values.loc[lag_values['lag_hours'].eq(24), 'correlation'].iloc[0]:.4f}",
            "phase_04_decision": "lag_23h/24h/25h, rolling 24h, hour",
        },
        {
            "eda_finding": "Chu kỳ tuần còn rõ",
            "evidence": f"lag 168h: r={lag_values.loc[lag_values['lag_hours'].eq(168), 'correlation'].iloc[0]:.4f}",
            "phase_04_decision": "lag_168h, rolling 168h, day_of_week, is_weekend",
        },
        {
            "eda_finding": "Profile thay đổi theo tháng",
            "evidence": "Mean target theo 12 tháng khác nhau",
            "phase_04_decision": "month và cyclic month features",
        },
        {
            "eda_finding": "Có robust anomaly candidates",
            "evidence": f"{phase_03['anomaly_screening']['candidate_count']:,} candidates",
            "phase_04_decision": "Không dùng anomaly flag; giữ nguyên target",
        },
    ]
    expected_features = set(phase_04["feature_order"])
    referenced_features = {
        "lag_1h", "lag_2h", "lag_3h", "lag_23h", "lag_24h", "lag_25h",
        "lag_168h", "rolling_mean_24h", "rolling_std_24h",
        "rolling_mean_168h", "rolling_std_168h", "hour", "day_of_week",
        "is_weekend", "month", "month_sin", "month_cos",
    }
    if not referenced_features.issubset(expected_features):
        raise ValueError("EDA-to-feature decisions conflict with Phase 4 evidence.")
    return {
        "phase": "phase_03_eda_presentation",
        "contract_version": "1.0.0",
        "canonical_eda_sha256": calculate_sha256(
            project_root / "outputs/results/phase_03_eda_summary.json"
        ),
        "prepared_sha256": phase_03["prepared_sha256"],
        "scope": {
            "partition": "development_train_validation_only",
            "start": phase_02["development"]["time_start"],
            "end": phase_02["development"]["time_end"],
            "holdout_target_values_inspected": False,
        },
        "data_profile": {
            "dataset": "PJM Hourly Energy Consumption — AEP",
            "target": "AEP_MW",
            "unit": "MW",
            "frequency": "hourly",
            "rows": phase_03["development"]["rows"],
            "observed_targets": phase_03["development"]["observed_targets"],
            "missing_targets": phase_03["development"]["missing_targets"],
        },
        "quality_recap": quality_recap,
        "annual_stability": _native_records(annual),
        "top_lag_correlations": _native_records(top_lags),
        "top_anomaly_candidates": top_anomalies,
        "eda_to_feature_decisions": decisions,
        "figure": {
            "name": "annual_stability",
            "path": FIGURE_PATH.as_posix(),
        },
        "status": "PASS",
    }


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
    output_path = (
        project_root / OUTPUT_PATH if output_path is None else Path(output_path)
    )
    figure_path = (
        project_root / FIGURE_PATH if figure_path is None else Path(figure_path)
    )
    evidence = build_presentation_evidence(project_root)
    prepared_path = project_root / "datasets/processed/aep_hourly_prepared.csv"
    split_contract = json.loads(
        (project_root / "config/temporal_split.json").read_text(encoding="utf-8")
    )
    data_contract = json.loads(
        (project_root / "config/data_contract.json").read_text(encoding="utf-8")
    )
    development = extract_development_data(
        pd.read_csv(prepared_path, parse_dates=[data_contract["timestamp_column"]]),
        data_contract,
        split_contract,
    )
    annual = build_annual_stability(development)
    save_annual_stability_figure(annual, figure_path)
    try:
        evidence["figure"]["path"] = figure_path.relative_to(project_root).as_posix()
    except ValueError:
        evidence["figure"]["path"] = str(figure_path)
    evidence["figure"]["sha256"] = calculate_sha256(figure_path)
    evidence["figure"]["bytes"] = figure_path.stat().st_size
    atomic_write_json(evidence, output_path)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        parser.error("Use --run to generate Phase 3 presentation evidence.")
    result = run()
    print(json.dumps({"output": OUTPUT_PATH.as_posix(), "status": result["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
