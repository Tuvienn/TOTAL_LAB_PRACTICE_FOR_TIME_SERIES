"""Fixed Phase 8 error-analysis and interpretation figures."""

from __future__ import annotations

from pathlib import Path
import os

import numpy as np
import pandas as pd


def _prepare_matplotlib(output_path: Path) -> object:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(output_path.parent / ".matplotlib"))
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _save_figure(figure: object, output_path: Path) -> None:
    output_path = Path(output_path)
    temporary_path = output_path.with_name(f".{output_path.name}.tmp.png")
    figure.savefig(temporary_path, dpi=160, bbox_inches="tight")
    if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
        raise ValueError("Phase 8 figure validation failed.")
    os.replace(temporary_path, output_path)


def save_residual_diagnostics_figure(
    predictions: pd.DataFrame,
    acf: pd.DataFrame,
    candidate: str,
    output_path: Path,
) -> None:
    """Save signed-error distribution and exact-lag residual ACF."""

    selected = predictions.loc[predictions["candidate"].eq(candidate)]
    if selected.empty or acf.empty:
        raise ValueError("Residual diagnostics require non-empty evidence.")
    plt = _prepare_matplotlib(output_path)
    figure, axes = plt.subplots(2, 1, figsize=(13, 9))
    axes[0].hist(selected["error"], bins=60, color="#1f77b4", alpha=0.85)
    axes[0].axvline(0.0, color="#202020", linewidth=1.2)
    axes[0].set_title("Phase 8 — XGBoost One-step Signed-error Distribution")
    axes[0].set_xlabel("Prediction − actual (MW)")
    axes[0].set_ylabel("Observations")
    axes[0].grid(alpha=0.2)
    axes[1].plot(acf["lag_hours"], acf["autocorrelation"], color="#1f77b4")
    axes[1].fill_between(
        acf["lag_hours"],
        -acf["reference_band"],
        acf["reference_band"],
        color="#9ecae1",
        alpha=0.45,
        label="Approximate 95% reference band",
    )
    axes[1].axhline(0.0, color="#202020", linewidth=1.0)
    axes[1].set_title("Exact-timestamp Residual Autocorrelation")
    axes[1].set_xlabel("Lag (hours)")
    axes[1].set_ylabel("Autocorrelation")
    axes[1].set_xlim(1, int(acf["lag_hours"].max()))
    axes[1].grid(alpha=0.2)
    axes[1].legend()
    figure.tight_layout()
    _save_figure(figure, output_path)
    plt.close(figure)


def save_error_by_time_figure(
    regime_metrics: pd.DataFrame,
    candidate: str,
    output_path: Path,
) -> None:
    """Save locked-model MAE across fixed calendar regimes."""

    selected = regime_metrics.loc[regime_metrics["candidate"].eq(candidate)]
    plt = _prepare_matplotlib(output_path)
    figure, axes = plt.subplots(2, 2, figsize=(14, 9))
    definitions = [
        ("hour", axes[0, 0], "Hour of day"),
        ("day_of_week", axes[0, 1], "Day of week"),
        ("day_type", axes[1, 0], "Day type"),
        ("month", axes[1, 1], "Month"),
    ]
    for dimension, axis, title in definitions:
        data = selected.loc[selected["dimension"].eq(dimension)].copy()
        if data.empty:
            raise ValueError(f"Missing time-regime evidence: {dimension}")
        axis.plot(
            data["regime"].astype(str),
            data["mae"],
            marker="o",
            color="#1f77b4",
        )
        axis.set_title(title)
        axis.set_ylabel("MAE (MW)")
        axis.grid(alpha=0.2)
    figure.suptitle("Phase 8 — XGBoost One-step Error by Time Regime")
    figure.tight_layout()
    _save_figure(figure, output_path)
    plt.close(figure)


def save_error_by_load_figure(
    regime_metrics: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save candidate MAE across common actual-load quartiles."""

    selected = regime_metrics.loc[
        regime_metrics["dimension"].eq("actual_load_quartile")
    ].copy()
    if selected.empty:
        raise ValueError("Load-regime evidence is missing.")
    labels = ["low", "medium_low", "medium_high", "high"]
    candidates = ["persistence", "seasonal_naive_24", "xgboost_tuned"]
    positions = np.arange(len(labels))
    width = 0.25
    colors = ["#7f8c8d", "#e67e22", "#1f77b4"]
    plt = _prepare_matplotlib(output_path)
    figure, axis = plt.subplots(figsize=(12, 6))
    for index, (candidate, color) in enumerate(zip(candidates, colors, strict=True)):
        candidate_data = selected.loc[selected["candidate"].eq(candidate)].set_index(
            "regime"
        )
        values = candidate_data.reindex(labels)["mae"].to_numpy(dtype="float64")
        if not np.isfinite(values).all():
            raise ValueError("Load-regime figure contains incomplete candidate data.")
        axis.bar(
            positions + (index - 1) * width,
            values,
            width,
            label=candidate,
            color=color,
        )
    axis.set_title("Phase 8 — One-step MAE by Actual-load Quartile")
    axis.set_xlabel("Post-hoc actual-load quartile")
    axis.set_ylabel("MAE (MW)")
    axis.set_xticks(positions, labels)
    axis.grid(axis="y", alpha=0.2)
    axis.legend()
    figure.tight_layout()
    _save_figure(figure, output_path)
    plt.close(figure)


def save_feature_importance_figure(
    feature_importance: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save normalized XGBoost gain importance for all locked features."""

    required = {"feature", "normalized_gain"}
    if not required.issubset(feature_importance.columns):
        raise ValueError("Feature-importance schema is incomplete.")
    ordered = feature_importance.sort_values("normalized_gain", ascending=True)
    plt = _prepare_matplotlib(output_path)
    figure, axis = plt.subplots(figsize=(11, 9))
    axis.barh(ordered["feature"], ordered["normalized_gain"], color="#1f77b4")
    axis.set_title("Phase 8 — Locked XGBoost Normalized Gain Importance")
    axis.set_xlabel("Normalized gain")
    axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()
    _save_figure(figure, output_path)
    plt.close(figure)
