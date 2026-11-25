"""Fixed Phase 7 forecast-evaluation visualizations."""

from __future__ import annotations

from pathlib import Path
import os

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
        raise ValueError("Forecast-evaluation figure validation failed.")
    os.replace(temporary_path, output_path)


def _prepare_one_step_plot_data(
    predictions: pd.DataFrame,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> tuple[pd.Series, pd.DataFrame]:
    selected = predictions.copy()
    if start is not None:
        selected = selected.loc[selected["timestamp"].ge(pd.Timestamp(start))]
    if end is not None:
        selected = selected.loc[selected["timestamp"].le(pd.Timestamp(end))]
    if selected.empty:
        raise ValueError("One-step figure window contains no predictions.")
    pivot = selected.pivot(index="timestamp", columns="candidate", values="prediction")
    actual = (
        selected.loc[
            selected["candidate"].eq("xgboost_tuned"),
            ["timestamp", "actual"],
        ]
        .set_index("timestamp")["actual"]
        .sort_index()
    )
    required = {"xgboost_tuned", "seasonal_naive_24"}
    if not required.issubset(pivot.columns):
        raise ValueError("One-step figure candidates are incomplete.")
    complete_timeline = pd.date_range(
        selected["timestamp"].min(),
        selected["timestamp"].max(),
        freq="h",
    )
    return actual.reindex(complete_timeline), pivot.reindex(complete_timeline)


def save_one_step_figure(
    predictions: pd.DataFrame,
    output_path: Path,
    title: str,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> None:
    """Save actual, locked-model, and seasonal one-step lines."""

    actual, pivot = _prepare_one_step_plot_data(predictions, start, end)
    plt = _prepare_matplotlib(output_path)
    figure, axis = plt.subplots(figsize=(14, 6))
    axis.plot(actual.index, actual, color="#202020", linewidth=1.3, label="Actual")
    axis.plot(
        pivot.index,
        pivot["xgboost_tuned"],
        color="#1f77b4",
        linewidth=1.0,
        label="XGBoost tuned",
    )
    axis.plot(
        pivot.index,
        pivot["seasonal_naive_24"],
        color="#e67e22",
        linewidth=0.9,
        alpha=0.85,
        label="Seasonal naive 24h",
    )
    axis.set_title(title)
    axis.set_xlabel("Target timestamp")
    axis.set_ylabel("AEP demand (MW)")
    axis.grid(alpha=0.22)
    axis.legend()
    figure.tight_layout()
    _save_figure(figure, output_path)
    plt.close(figure)


def save_recursive_horizon_figure(
    recursive_metrics: dict[str, object],
    output_path: Path,
) -> None:
    """Save per-horizon recursive MAE and RMSE for every candidate."""

    records = recursive_metrics.get("candidate_metrics", [])
    if not records:
        raise ValueError("Recursive metrics do not contain candidate records.")
    plt = _prepare_matplotlib(output_path)
    figure, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    colors = {
        "persistence": "#7f8c8d",
        "seasonal_naive_24": "#e67e22",
        "xgboost_tuned": "#1f77b4",
    }
    for record in records:
        candidate = str(record["candidate"])
        per_horizon = pd.DataFrame(record["per_horizon"])
        if per_horizon["horizon"].tolist() != list(range(1, 25)):
            raise ValueError("Recursive figure requires horizons 1..24.")
        axes[0].plot(
            per_horizon["horizon"],
            per_horizon["mae"],
            marker="o",
            markersize=3,
            color=colors[candidate],
            label=candidate,
        )
        axes[1].plot(
            per_horizon["horizon"],
            per_horizon["rmse"],
            marker="o",
            markersize=3,
            color=colors[candidate],
            label=candidate,
        )
    axes[0].set_title("Phase 7 — Recursive 24-hour Error by Horizon")
    axes[0].set_ylabel("MAE (MW)")
    axes[1].set_ylabel("RMSE (MW)")
    axes[1].set_xlabel("Forecast horizon (hours)")
    axes[1].set_xticks(range(1, 25))
    for axis in axes:
        axis.grid(alpha=0.22)
        axis.legend()
    figure.tight_layout()
    _save_figure(figure, output_path)
    plt.close(figure)
