from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def save_figure(figure, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f".{output_path.name}.tmp.png")
    figure.savefig(temporary_path, dpi=160, bbox_inches="tight")
    temporary_path.replace(output_path)
    plt.close(figure)


def plot_one_step_full_test(
    predictions: pd.DataFrame,
    selected_candidate: str,
    output_path: Path,
) -> None:
    actual = predictions.loc[
        predictions["candidate_id"] == selected_candidate
    ]
    selected = actual
    seasonal = predictions.loc[
        predictions["candidate_id"] == "seasonal_naive_24"
    ]
    figure, axis = plt.subplots(figsize=(16, 6))
    axis.plot(actual["timestamp"], actual["actual"], label="Actual", lw=1.0)
    axis.plot(
        selected["timestamp"],
        selected["prediction"],
        label=selected_candidate,
        lw=0.9,
    )
    axis.plot(
        seasonal["timestamp"],
        seasonal["prediction"],
        label="Seasonal Naive 24",
        lw=0.8,
        alpha=0.8,
    )
    axis.set_title("One-step Forecast — Full Final-test Window")
    axis.set_xlabel("Timestamp")
    axis.set_ylabel("AEP_MW")
    axis.legend()
    axis.grid(alpha=0.2)
    save_figure(figure, output_path)


def plot_one_step_diagnostic_window(
    predictions: pd.DataFrame,
    candidate_order: list[str],
    start: pd.Timestamp,
    end: pd.Timestamp,
    output_path: Path,
) -> None:
    window = predictions.loc[
        predictions["timestamp"].between(start, end)
    ]
    reference = window.loc[
        window["candidate_id"] == candidate_order[0]
    ]
    figure, axis = plt.subplots(figsize=(16, 7))
    axis.plot(
        reference["timestamp"],
        reference["actual"],
        label="Actual",
        color="black",
        lw=2.0,
    )
    for candidate_id in candidate_order:
        candidate = window.loc[window["candidate_id"] == candidate_id]
        axis.plot(
            candidate["timestamp"],
            candidate["prediction"],
            label=candidate_id,
            lw=1.0,
            alpha=0.85,
        )
    axis.set_title("One-step Forecast — Fixed First 14 Days")
    axis.set_xlabel("Timestamp")
    axis.set_ylabel("AEP_MW")
    axis.legend(ncol=2)
    axis.grid(alpha=0.2)
    save_figure(figure, output_path)


def plot_multistep_error_by_horizon(
    metrics: dict,
    candidate_order: list[str],
    output_path: Path,
) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(13, 10), sharex=True)
    for candidate_id in candidate_order:
        per_horizon = metrics["candidates"][candidate_id]["per_horizon"]
        horizons = [item["horizon"] for item in per_horizon]
        axes[0].plot(
            horizons,
            [item["mae"] for item in per_horizon],
            label=candidate_id,
        )
        axes[1].plot(
            horizons,
            [item["rmse"] for item in per_horizon],
            label=candidate_id,
        )
    axes[0].set_title("Recursive 24-hour Forecast Error by Horizon")
    axes[0].set_ylabel("MAE")
    axes[1].set_ylabel("RMSE")
    axes[1].set_xlabel("Horizon (hours)")
    for axis in axes:
        axis.grid(alpha=0.2)
        axis.legend(ncol=2)
    save_figure(figure, output_path)
