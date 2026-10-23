from __future__ import annotations

import os
from pathlib import Path
import tempfile

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "practice_3_matplotlib"),
)

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np


STATUS_ORDER = (
    "PENDING",
    "RUNNING",
    "PASS",
    "INTERRUPTED",
    "FAILED",
)

STATUS_COLORS = (
    "#3B3F46",
    "#2F80ED",
    "#27AE60",
    "#F2994A",
    "#EB5757",
)


def _save_figure_atomically(figure, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f".{output_path.name}.tmp")
    figure.savefig(
        temporary_path,
        format="png",
        dpi=160,
        bbox_inches="tight",
        facecolor=figure.get_facecolor(),
    )
    temporary_path.replace(output_path)


def _apply_dark_axes_style(figure, axis) -> None:
    figure.patch.set_facecolor("#202124")
    axis.set_facecolor("#202124")
    axis.tick_params(colors="#E8EAED")
    axis.xaxis.label.set_color("#E8EAED")
    axis.yaxis.label.set_color("#E8EAED")
    axis.title.set_color("#F1F3F4")
    for spine in axis.spines.values():
        spine.set_color("#5F6368")


def render_screening_progress(checkpoint: dict, run_dir: Path) -> None:
    run_dir = Path(run_dir)
    configurations = checkpoint["configuration_order"]
    folds = checkpoint["folds"]
    fold_status = checkpoint["fold_status"]
    fold_results = checkpoint["fold_results"]
    status_codes = {status: index for index, status in enumerate(STATUS_ORDER)}

    matrix = np.asarray(
        [
            [status_codes[fold_status[name][str(fold)]] for fold in folds]
            for name in configurations
        ],
        dtype=np.int64,
    )

    progress_figure, progress_axis = plt.subplots(
        figsize=(10.5, 5.4),
        constrained_layout=True,
    )
    _apply_dark_axes_style(progress_figure, progress_axis)
    progress_axis.imshow(
        matrix,
        cmap=ListedColormap(STATUS_COLORS),
        vmin=0,
        vmax=len(STATUS_ORDER) - 1,
        aspect="auto",
    )
    progress_axis.set_title("Phase 5 XGBoost Screening Progress", weight="bold")
    progress_axis.set_xlabel("CV fold")
    progress_axis.set_ylabel("Feature configuration")
    progress_axis.set_xticks(range(len(folds)), labels=[str(fold) for fold in folds])
    progress_axis.set_yticks(range(len(configurations)), labels=configurations)

    for row, name in enumerate(configurations):
        for column, fold in enumerate(folds):
            status = fold_status[name][str(fold)]
            duration = fold_results[name].get(str(fold), {}).get(
                "training_seconds"
            )
            label = status if duration is None else f"{status}\n{duration:.1f}s"
            progress_axis.text(
                column,
                row,
                label,
                ha="center",
                va="center",
                color="#FFFFFF",
                fontsize=7.5,
                weight="bold",
            )

    _save_figure_atomically(
        progress_figure,
        run_dir / "training_progress.png",
    )
    plt.close(progress_figure)

    duration_figure, duration_axis = plt.subplots(
        figsize=(11.5, 5.8),
        constrained_layout=True,
    )
    _apply_dark_axes_style(duration_figure, duration_axis)
    x_positions = np.arange(len(configurations), dtype=np.float64)
    width = 0.14

    for fold_index, fold in enumerate(folds):
        durations = [
            fold_results[name].get(str(fold), {}).get(
                "training_seconds",
                np.nan,
            )
            for name in configurations
        ]
        duration_axis.bar(
            x_positions + (fold_index - (len(folds) - 1) / 2) * width,
            durations,
            width,
            label=f"Fold {fold}",
        )

    duration_axis.set_title("Phase 5 Fold Training Duration", weight="bold")
    duration_axis.set_xlabel("Feature configuration")
    duration_axis.set_ylabel("Seconds")
    duration_axis.set_xticks(x_positions, labels=configurations, rotation=20)
    duration_axis.grid(axis="y", color="#5F6368", alpha=0.35)
    legend = duration_axis.legend(
        facecolor="#2B2D31",
        edgecolor="#5F6368",
    )
    for text in legend.get_texts():
        text.set_color("#E8EAED")

    _save_figure_atomically(
        duration_figure,
        run_dir / "fold_duration.png",
    )
    plt.close(duration_figure)
