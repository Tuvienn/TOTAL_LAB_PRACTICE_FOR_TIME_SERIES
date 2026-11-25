"""TRAIN-only exploratory data analysis for Practice 3 v2."""

from __future__ import annotations

from pathlib import Path
import json
import os
import tempfile
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from practice_3_v2.data.data_preparation import (
    calculate_sha256,
    load_json_contract,
)
from practice_3_v2.data.temporal_split import (
    build_development_holdout_masks,
    load_phase_02_inputs,
    validate_contract_alignment,
    validate_prepared_input,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DAY_LABELS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
MONTH_LABELS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def load_phase_03_inputs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    """Load approved contracts and upstream audits for Phase 3."""

    project_root = Path(project_root).resolve()
    (
        data_contract,
        preparation_contract,
        forecasting_contract,
        split_contract,
    ) = load_phase_02_inputs(project_root)
    validate_contract_alignment(forecasting_contract, split_contract)
    eda_contract = load_json_contract(project_root / "config/eda.json")
    phase_01_path = project_root / preparation_contract["outputs"]["audit"]
    split_audit_path = project_root / eda_contract["split_audit"]
    with phase_01_path.open(encoding="utf-8") as file:
        phase_01_audit = json.load(file)
    if not split_audit_path.is_file():
        raise FileNotFoundError(f"Phase 2 audit not found: {split_audit_path}")
    if calculate_sha256(split_audit_path) != eda_contract[
        "split_audit_sha256"
    ]:
        raise ValueError("Phase 2 audit SHA-256 does not match EDA contract.")
    with split_audit_path.open(encoding="utf-8") as file:
        phase_02_audit = json.load(file)
    if phase_02_audit.get("status") != "PASS":
        raise ValueError("Phase 2 audit status must be PASS.")
    if phase_02_audit.get("prepared_sha256") != eda_contract[
        "prepared_sha256"
    ]:
        raise ValueError("Phase 2 prepared identity conflicts with EDA contract.")
    return (
        data_contract,
        preparation_contract,
        split_contract,
        eda_contract,
        phase_01_audit,
        phase_02_audit,
    )


def extract_development_data(
    prepared_data: pd.DataFrame,
    data_contract: dict[str, Any],
    split_contract: dict[str, Any],
) -> pd.DataFrame:
    """Return an isolated copy of the approved development partition."""

    development_mask, _ = build_development_holdout_masks(
        prepared_data,
        data_contract,
        split_contract,
    )
    return prepared_data.loc[development_mask].copy(deep=True).reset_index(
        drop=True
    )


def validate_development_data(
    development_data: pd.DataFrame,
    data_contract: dict[str, Any],
    eda_contract: dict[str, Any],
) -> None:
    """Validate TRAIN-only EDA input without inspecting holdout targets."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    expected = eda_contract["development"]
    start = pd.Timestamp(expected["start_inclusive"])
    end = pd.Timestamp(expected["end_exclusive"])
    if len(development_data) != expected["expected_rows"]:
        raise ValueError("Unexpected development row count.")
    if development_data[timestamp_column].min() != start:
        raise ValueError("Unexpected development start timestamp.")
    if development_data[timestamp_column].max() >= end:
        raise ValueError("Development data contains a holdout timestamp.")
    if not development_data[timestamp_column].is_unique:
        raise ValueError("Development timestamps must be unique.")
    if not development_data[timestamp_column].is_monotonic_increasing:
        raise ValueError("Development timestamps must be increasing.")
    if not development_data[timestamp_column].diff().dropna().eq(
        pd.Timedelta(hours=1)
    ).all():
        raise ValueError("Development timeline must remain continuous hourly.")
    observed = int(development_data[target_column].notna().sum())
    missing = int(development_data[target_column].isna().sum())
    if observed != expected["expected_observed_targets"]:
        raise ValueError("Unexpected development observed-target count.")
    if missing != expected["expected_missing_targets"]:
        raise ValueError("Unexpected development missing-target count.")
    observed_values = development_data[target_column].dropna().to_numpy(
        dtype="float64"
    )
    if not np.isfinite(observed_values).all() or (observed_values <= 0).any():
        raise ValueError("Development observed targets must be finite and positive.")


def summarize_missingness(
    development_data: pd.DataFrame,
    data_contract: dict[str, Any],
) -> dict[str, Any]:
    """Summarize development missing targets without imputation."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    missing = development_data.loc[
        development_data[target_column].isna()
    ].copy()
    missing["year"] = missing[timestamp_column].dt.year
    missing["year_month"] = missing[timestamp_column].dt.strftime("%Y-%m")
    by_year = missing.groupby("year", sort=True).size()
    by_month = missing.groupby("year_month", sort=True).size()
    metadata_valid = bool(
        missing["source_count"].eq(0).all()
        and missing["quality_flag"].eq("missing_timestamp").all()
    )
    return {
        "missing_targets": int(len(missing)),
        "missing_timestamps": [
            timestamp.strftime(DATETIME_FORMAT)
            for timestamp in missing[timestamp_column]
        ],
        "by_year": [
            {"year": int(year), "count": int(count)}
            for year, count in by_year.items()
        ],
        "by_year_month": [
            {"year_month": str(year_month), "count": int(count)}
            for year_month, count in by_month.items()
        ],
        "missing_metadata_valid": metadata_valid,
        "imputation_applied": False,
    }


def summarize_distribution(
    development_data: pd.DataFrame,
    data_contract: dict[str, Any],
    eda_contract: dict[str, Any],
) -> dict[str, float | int]:
    """Calculate approved descriptive statistics on observed targets."""

    target = development_data[data_contract["target_column"]].dropna().astype(
        "float64"
    )
    quantiles = target.quantile(eda_contract["distribution"]["quantiles"])
    return {
        "count": int(target.count()),
        "mean": float(target.mean()),
        "standard_deviation": float(target.std(ddof=1)),
        "minimum": float(target.min()),
        "q01": float(quantiles.loc[0.01]),
        "q05": float(quantiles.loc[0.05]),
        "q25": float(quantiles.loc[0.25]),
        "median": float(quantiles.loc[0.50]),
        "q75": float(quantiles.loc[0.75]),
        "q95": float(quantiles.loc[0.95]),
        "q99": float(quantiles.loc[0.99]),
        "maximum": float(target.max()),
        "iqr": float(quantiles.loc[0.75] - quantiles.loc[0.25]),
    }


def build_daily_trend(
    development_data: pd.DataFrame,
    data_contract: dict[str, Any],
    eda_contract: dict[str, Any],
) -> pd.DataFrame:
    """Build daily means and a trailing rolling mean for presentation."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    trend = development_data[[timestamp_column, target_column]].copy()
    trend["date"] = trend[timestamp_column].dt.floor("D")
    daily = (
        trend.groupby("date", as_index=False, sort=True)[target_column]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "daily_mean", "count": "observed_hours"})
    )
    trend_contract = eda_contract["trend"]
    daily["rolling_mean_30d"] = daily["daily_mean"].rolling(
        window=trend_contract["rolling_window_days"],
        min_periods=trend_contract["rolling_min_periods"],
        center=trend_contract["centered"],
    ).mean()
    return daily


def build_seasonality_profiles(
    development_data: pd.DataFrame,
    data_contract: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    """Build TRAIN-only calendar seasonality profiles and support counts."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    observed = development_data.loc[
        development_data[target_column].notna(),
        [timestamp_column, target_column],
    ].copy()
    observed["hour"] = observed[timestamp_column].dt.hour
    observed["day_of_week"] = observed[timestamp_column].dt.day_of_week
    observed["month"] = observed[timestamp_column].dt.month

    def profile(column: str) -> pd.DataFrame:
        return (
            observed.groupby(column, as_index=False, sort=True)[target_column]
            .agg(["mean", "count"])
            .reset_index()
            .rename(
                columns={
                    "mean": "mean_target",
                    "count": "observed_count",
                }
            )
        )

    hour = profile("hour")
    day = profile("day_of_week")
    day["day_name"] = day["day_of_week"].map(dict(enumerate(DAY_LABELS)))
    month = profile("month")
    month["month_name"] = month["month"].map(
        {index + 1: value for index, value in enumerate(MONTH_LABELS)}
    )
    heatmap = observed.pivot_table(
        index="day_of_week",
        columns="hour",
        values=target_column,
        aggfunc="mean",
        observed=False,
    ).reindex(index=range(7), columns=range(24))
    heatmap.index.name = "day_of_week"
    heatmap.columns.name = "hour"
    return {
        "hour_of_day": hour,
        "day_of_week": day,
        "month": month,
        "hour_day_heatmap": heatmap,
    }


def calculate_lag_correlations(
    development_data: pd.DataFrame,
    data_contract: dict[str, Any],
    eda_contract: dict[str, Any],
) -> pd.DataFrame:
    """Calculate pairwise hourly-aligned correlations without timeline compression."""

    target = development_data[data_contract["target_column"]].astype("float64")
    lag_contract = eda_contract["lag_correlation"]
    rows: list[dict[str, float | int]] = []
    for lag in range(
        lag_contract["minimum_lag_hours"],
        lag_contract["maximum_lag_hours"] + 1,
    ):
        lagged = target.shift(lag)
        valid = target.notna() & lagged.notna()
        rows.append(
            {
                "lag_hours": lag,
                "correlation": float(target.loc[valid].corr(lagged.loc[valid])),
                "valid_pairs": int(valid.sum()),
            }
        )
    return pd.DataFrame(rows)


def screen_robust_anomalies(
    development_data: pd.DataFrame,
    data_contract: dict[str, Any],
    eda_contract: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Screen anomaly candidates by calendar-year and hour-of-week MAD."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    contract = eda_contract["anomaly_screening"]
    observed = development_data.loc[
        development_data[target_column].notna(),
        [timestamp_column, target_column],
    ].copy()
    original_values = observed[target_column].copy(deep=True)
    observed["year"] = observed[timestamp_column].dt.year
    observed["hour_of_week"] = (
        observed[timestamp_column].dt.day_of_week * 24
        + observed[timestamp_column].dt.hour
    )
    group_columns = ["year", "hour_of_week"]
    grouped_target = observed.groupby(group_columns, sort=True)[target_column]
    observed["group_support"] = grouped_target.transform("count")
    observed["group_median"] = grouped_target.transform("median")
    observed["absolute_deviation"] = (
        observed[target_column] - observed["group_median"]
    ).abs()
    observed["group_mad"] = observed.groupby(
        group_columns,
        sort=True,
    )["absolute_deviation"].transform("median")
    evaluable = (
        observed["group_support"].ge(contract["minimum_group_support"])
        & observed["group_mad"].gt(0)
    )
    observed["robust_score"] = np.nan
    observed.loc[evaluable, "robust_score"] = (
        0.6745
        * (
            observed.loc[evaluable, target_column]
            - observed.loc[evaluable, "group_median"]
        )
        / observed.loc[evaluable, "group_mad"]
    )
    observed["is_candidate"] = (
        evaluable
        & observed["robust_score"].abs().gt(contract["threshold"])
    )
    if not observed[target_column].equals(original_values):
        raise ValueError("Anomaly screening changed target values.")

    candidates = observed.loc[observed["is_candidate"]].copy()
    candidates["absolute_score"] = candidates["robust_score"].abs()
    candidates = candidates.sort_values(
        ["absolute_score", timestamp_column],
        ascending=[False, True],
        kind="stable",
    )
    top = candidates.head(contract["top_candidates"])
    summary = {
        "method": contract["method"],
        "grouping": contract["grouping"],
        "threshold": float(contract["threshold"]),
        "minimum_group_support": int(contract["minimum_group_support"]),
        "observed_targets": int(len(observed)),
        "evaluable_targets": int(evaluable.sum()),
        "not_evaluable_targets": int((~evaluable).sum()),
        "candidate_count": int(observed["is_candidate"].sum()),
        "candidate_rate_among_evaluable": float(
            observed.loc[evaluable, "is_candidate"].mean()
        ),
        "target_treatment": contract["treatment"],
        "top_candidates": [
            {
                "timestamp": row[timestamp_column].strftime(DATETIME_FORMAT),
                "target": float(row[target_column]),
                "robust_score": float(row["robust_score"]),
                "year": int(row["year"]),
                "hour_of_week": int(row["hour_of_week"]),
            }
            for _, row in top.iterrows()
        ],
    }
    return candidates, summary


def _records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a numeric summary dataframe into JSON-native records."""

    records: list[dict[str, Any]] = []
    for record in dataframe.to_dict(orient="records"):
        converted: dict[str, Any] = {}
        for key, value in record.items():
            if isinstance(value, (np.integer,)):
                converted[key] = int(value)
            elif isinstance(value, (np.floating,)):
                converted[key] = float(value)
            else:
                converted[key] = value
        records.append(converted)
    return records


def render_phase_03_figures(
    development_data: pd.DataFrame,
    daily_trend: pd.DataFrame,
    profiles: dict[str, pd.DataFrame],
    lag_correlations: pd.DataFrame,
    anomaly_candidates: pd.DataFrame,
    data_contract: dict[str, Any],
    eda_contract: dict[str, Any],
    output_paths: dict[str, Path],
) -> None:
    """Render deterministic TRAIN-only EDA figures to staged paths."""

    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    dpi = eda_contract["figures"]["dpi"]
    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    plt.style.use("default")

    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(
        daily_trend["date"],
        daily_trend["daily_mean"],
        color="#7aa6c2",
        linewidth=0.65,
        alpha=0.65,
        label="Daily mean",
    )
    axis.plot(
        daily_trend["date"],
        daily_trend["rolling_mean_30d"],
        color="#d1495b",
        linewidth=1.5,
        label="Trailing 30-day mean",
    )
    axis.set(title="Development Trend", xlabel="Date", ylabel="AEP_MW (MW)")
    axis.legend()
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(
        output_paths["trend"],
        dpi=dpi,
        metadata={"Software": "Practice_3"},
    )
    plt.close(figure)

    observed_target = development_data[target_column].dropna()
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].hist(
        observed_target,
        bins=eda_contract["distribution"]["histogram_bins"],
        color="#2a6f97",
        edgecolor="white",
    )
    axes[0].set(title="Target Distribution", xlabel="AEP_MW (MW)", ylabel="Count")
    axes[1].boxplot(observed_target, orientation="vertical")
    axes[1].set(title="Target Boxplot", ylabel="AEP_MW (MW)", xticks=[])
    figure.tight_layout()
    figure.savefig(
        output_paths["distribution"],
        dpi=dpi,
        metadata={"Software": "Practice_3"},
    )
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    hour = profiles["hour_of_day"]
    axes[0].plot(hour["hour"], hour["mean_target"], marker="o", markersize=3)
    axes[0].set(title="Hour-of-day", xlabel="Hour", ylabel="Mean AEP_MW (MW)")
    day = profiles["day_of_week"]
    axes[1].plot(day["day_of_week"], day["mean_target"], marker="o")
    axes[1].set_xticks(range(7), [label[:3] for label in DAY_LABELS])
    axes[1].set(title="Day-of-week", xlabel="Day", ylabel="Mean AEP_MW (MW)")
    month = profiles["month"]
    axes[2].plot(month["month"], month["mean_target"], marker="o")
    axes[2].set_xticks(range(1, 13), [label[:3] for label in MONTH_LABELS], rotation=45)
    axes[2].set(title="Month", xlabel="Month", ylabel="Mean AEP_MW (MW)")
    for axis in axes:
        axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(
        output_paths["seasonality_profiles"],
        dpi=dpi,
        metadata={"Software": "Practice_3"},
    )
    plt.close(figure)

    heatmap = profiles["hour_day_heatmap"]
    figure, axis = plt.subplots(figsize=(12, 4.8))
    image = axis.imshow(heatmap.to_numpy(), aspect="auto", cmap="viridis")
    axis.set(
        title="Mean AEP_MW by Day and Hour — Development Only",
        xlabel="Hour of day",
        ylabel="Day of week",
    )
    axis.set_xticks(range(24))
    axis.set_yticks(range(7), DAY_LABELS)
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("Mean AEP_MW (MW)")
    figure.tight_layout()
    figure.savefig(
        output_paths["hour_day_heatmap"],
        dpi=dpi,
        metadata={"Software": "Practice_3"},
    )
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(12, 4.5))
    axis.plot(
        lag_correlations["lag_hours"],
        lag_correlations["correlation"],
        color="#2a6f97",
    )
    highlighted = lag_correlations.loc[
        lag_correlations["lag_hours"].isin(
            eda_contract["lag_correlation"]["highlighted_lags"]
        )
    ]
    axis.scatter(
        highlighted["lag_hours"],
        highlighted["correlation"],
        color="#d1495b",
        zorder=3,
    )
    for row in highlighted.itertuples(index=False):
        axis.annotate(
            f"{row.lag_hours}h",
            (row.lag_hours, row.correlation),
            xytext=(4, 6),
            textcoords="offset points",
        )
    axis.set(
        title="Hourly-aligned Lag Correlation — Development Only",
        xlabel="Lag (hours)",
        ylabel="Pearson correlation",
    )
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(
        output_paths["lag_correlation"],
        dpi=dpi,
        metadata={"Software": "Practice_3"},
    )
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(
        daily_trend["date"],
        daily_trend["daily_mean"],
        color="#8d99ae",
        linewidth=0.7,
        label="Daily mean",
    )
    axis.scatter(
        anomaly_candidates[timestamp_column],
        anomaly_candidates[target_column],
        s=8,
        color="#d90429",
        alpha=0.7,
        label="Robust anomaly candidates",
    )
    axis.set(
        title="Robust Anomaly Screening — No Target Treatment",
        xlabel="Date",
        ylabel="AEP_MW (MW)",
    )
    axis.legend()
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(
        output_paths["anomaly_screening"],
        dpi=dpi,
        metadata={"Software": "Practice_3"},
    )
    plt.close(figure)


def build_phase_03_audit(
    development_data: pd.DataFrame,
    prepared_sha256: str,
    phase_02_audit_sha256: str,
    missingness: dict[str, Any],
    distribution: dict[str, float | int],
    daily_trend: pd.DataFrame,
    profiles: dict[str, pd.DataFrame],
    lag_correlations: pd.DataFrame,
    anomaly_summary: dict[str, Any],
    figure_records: list[dict[str, Any]],
    data_contract: dict[str, Any],
    eda_contract: dict[str, Any],
) -> dict[str, Any]:
    """Build the deterministic Phase 3 scientific audit."""

    timestamp_column = data_contract["timestamp_column"]
    highlighted = lag_correlations.loc[
        lag_correlations["lag_hours"].isin(
            eda_contract["lag_correlation"]["highlighted_lags"]
        )
    ]
    heatmap = profiles["hour_day_heatmap"]
    heatmap_records = [
        {
            "day_of_week": day,
            "day_name": DAY_LABELS[day],
            "hourly_mean_target": [float(value) for value in heatmap.loc[day]],
        }
        for day in range(7)
    ]
    return {
        "phase": eda_contract["phase"],
        "contract_version": eda_contract["contract_version"],
        "prepared_input": eda_contract["prepared_input"],
        "prepared_sha256": prepared_sha256,
        "split_audit": eda_contract["split_audit"],
        "split_audit_sha256": phase_02_audit_sha256,
        "development": {
            "start_inclusive": development_data[timestamp_column]
            .min()
            .strftime(DATETIME_FORMAT),
            "end_inclusive": development_data[timestamp_column]
            .max()
            .strftime(DATETIME_FORMAT),
            "end_exclusive": eda_contract["development"]["end_exclusive"],
            "rows": int(len(development_data)),
            "observed_targets": int(distribution["count"]),
            "missing_targets": int(missingness["missing_targets"]),
        },
        "holdout": {
            "excluded_from_eda": True,
            "target_values_inspected": False,
            "rows_excluded": 8761,
            "label": "historical_re_evaluation_holdout",
        },
        "missingness": missingness,
        "distribution": distribution,
        "trend": {
            "aggregation": eda_contract["trend"]["aggregation"],
            "daily_rows": int(len(daily_trend)),
            "daily_start": daily_trend["date"].min().strftime("%Y-%m-%d"),
            "daily_end": daily_trend["date"].max().strftime("%Y-%m-%d"),
            "rolling_window_days": eda_contract["trend"][
                "rolling_window_days"
            ],
            "rolling_available_days": int(
                daily_trend["rolling_mean_30d"].notna().sum()
            ),
            "centered": eda_contract["trend"]["centered"],
        },
        "seasonality": {
            "hour_of_day": _records(profiles["hour_of_day"]),
            "day_of_week": _records(profiles["day_of_week"]),
            "month": _records(profiles["month"]),
            "hour_day_heatmap": heatmap_records,
        },
        "lag_correlation": {
            "method": eda_contract["lag_correlation"]["method"],
            "minimum_lag_hours": eda_contract["lag_correlation"][
                "minimum_lag_hours"
            ],
            "maximum_lag_hours": eda_contract["lag_correlation"][
                "maximum_lag_hours"
            ],
            "values": _records(lag_correlations),
            "highlighted": _records(highlighted),
        },
        "anomaly_screening": anomaly_summary,
        "feature_hypotheses": [
            {
                "candidate": "short_term_lag",
                "evidence": f"lag_1_correlation={highlighted.iloc[0]['correlation']:.6f}",
                "status": "candidate_for_phase_04_review",
            },
            {
                "candidate": "daily_lag",
                "evidence": f"lag_24_correlation={highlighted.iloc[1]['correlation']:.6f}",
                "status": "candidate_for_phase_04_review",
            },
            {
                "candidate": "weekly_lag",
                "evidence": f"lag_168_correlation={highlighted.iloc[2]['correlation']:.6f}",
                "status": "candidate_for_phase_04_review",
            },
            {
                "candidate": "calendar_features",
                "evidence": "TRAIN-only hour/day/month profiles were calculated",
                "status": "candidate_for_phase_04_review",
            },
        ],
        "figures": figure_records,
        "checks": {
            "development_only": True,
            "timeline_compressed": False,
            "missing_target_imputed": False,
            "anomaly_target_treatment_applied": False,
            "holdout_target_values_inspected": False,
        },
        "status": "PASS",
    }


def _validate_staged_bundle(
    audit: dict[str, Any],
    staged_json: Path,
    staged_figures: dict[str, Path],
) -> None:
    """Validate staged JSON and PNG files before official promotion."""

    with staged_json.open(encoding="utf-8") as file:
        serialized = json.load(file)
    if serialized != audit or serialized.get("status") != "PASS":
        raise ValueError("Serialized Phase 3 audit validation failed.")
    expected_hashes = {
        record["name"]: record["sha256"] for record in audit["figures"]
    }
    for name, path in staged_figures.items():
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Staged figure is missing or empty: {name}")
        if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Staged figure is not a PNG: {name}")
        if calculate_sha256(path) != expected_hashes[name]:
            raise ValueError(f"Staged figure checksum mismatch: {name}")


def run_phase_03(
    project_root: Path = PROJECT_ROOT,
    summary_path: Path | None = None,
    figures_dir: Path | None = None,
) -> dict[str, Any]:
    """Run Phase 3 and promote validated TRAIN-only EDA artifacts."""

    project_root = Path(project_root).resolve()
    (
        data_contract,
        preparation_contract,
        split_contract,
        eda_contract,
        phase_01_audit,
        phase_02_audit,
    ) = load_phase_03_inputs(project_root)
    prepared_path = project_root / eda_contract["prepared_input"]
    prepared_data, prepared_sha256 = validate_prepared_input(
        prepared_path,
        data_contract,
        preparation_contract,
        split_contract,
        phase_01_audit,
    )
    development_data = extract_development_data(
        prepared_data,
        data_contract,
        split_contract,
    )
    validate_development_data(development_data, data_contract, eda_contract)
    missingness = summarize_missingness(development_data, data_contract)
    distribution = summarize_distribution(
        development_data,
        data_contract,
        eda_contract,
    )
    daily_trend = build_daily_trend(
        development_data,
        data_contract,
        eda_contract,
    )
    profiles = build_seasonality_profiles(development_data, data_contract)
    lag_correlations = calculate_lag_correlations(
        development_data,
        data_contract,
        eda_contract,
    )
    anomaly_candidates, anomaly_summary = screen_robust_anomalies(
        development_data,
        data_contract,
        eda_contract,
    )

    final_summary_path = Path(summary_path) if summary_path else (
        project_root / eda_contract["outputs"]["summary"]
    )
    configured_figure_paths = {
        name: project_root / relative_path
        for name, relative_path in eda_contract["figures"].items()
        if name != "dpi"
    }
    if figures_dir is not None:
        final_figure_paths = {
            name: Path(figures_dir) / path.name
            for name, path in configured_figure_paths.items()
        }
    else:
        final_figure_paths = configured_figure_paths
    staging_parent = project_root / "outputs"
    staging_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="phase_03_staging_",
        dir=staging_parent,
    ) as temporary_directory:
        staging_root = Path(temporary_directory)
        staged_figures = {
            name: staging_root / path.name
            for name, path in configured_figure_paths.items()
        }
        render_phase_03_figures(
            development_data,
            daily_trend,
            profiles,
            lag_correlations,
            anomaly_candidates,
            data_contract,
            eda_contract,
            staged_figures,
        )
        figure_records = [
            {
                "name": name,
                "path": eda_contract["figures"][name],
                "sha256": calculate_sha256(staged_figures[name]),
                "bytes": int(staged_figures[name].stat().st_size),
            }
            for name in configured_figure_paths
        ]
        audit = build_phase_03_audit(
            development_data,
            prepared_sha256,
            calculate_sha256(project_root / eda_contract["split_audit"]),
            missingness,
            distribution,
            daily_trend,
            profiles,
            lag_correlations,
            anomaly_summary,
            figure_records,
            data_contract,
            eda_contract,
        )
        staged_json = staging_root / "phase_03_eda_summary.json"
        with staged_json.open("w", encoding="utf-8") as file:
            json.dump(audit, file, indent=2, ensure_ascii=False)
            file.write("\n")
        _validate_staged_bundle(audit, staged_json, staged_figures)

        for name, destination in final_figure_paths.items():
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged_figures[name], destination)
        final_summary_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged_json, final_summary_path)
    return audit


def main() -> int:
    """Execute Phase 3 and print a concise validated result."""

    audit = run_phase_03()
    print(
        json.dumps(
            {
                "phase": audit["phase"],
                "development_rows": audit["development"]["rows"],
                "observed_targets": audit["development"]["observed_targets"],
                "missing_targets": audit["development"]["missing_targets"],
                "anomaly_candidates": audit["anomaly_screening"][
                    "candidate_count"
                ],
                "figures": len(audit["figures"]),
                "status": audit["status"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
