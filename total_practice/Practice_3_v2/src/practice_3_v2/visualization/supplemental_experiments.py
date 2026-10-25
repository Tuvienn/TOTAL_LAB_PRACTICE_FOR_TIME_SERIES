"""Figures for approved Phase 6 supplemental assignment experiments."""

from __future__ import annotations

from pathlib import Path
import os

import numpy as np


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
        raise ValueError("Supplemental figure validation failed.")
    os.replace(temporary_path, output_path)


def save_model_comparison_figure(
    linear_result: dict,
    output_path: Path,
) -> None:
    """Compare post-hoc Linear Regression with official tuned XGBoost CV."""

    linear = linear_result["aggregate"]
    xgboost = linear_result["official_xgboost_reference"]["aggregate"]
    labels = ["Linear Regression", "XGBoost tuned"]
    maes = [linear["mean_cv_mae"], xgboost["mean_cv_mae"]]
    rmses = [linear["mean_cv_rmse"], xgboost["mean_cv_rmse"]]
    mae_std = [
        linear["cv_mae_standard_deviation"],
        xgboost["cv_mae_standard_deviation"],
    ]
    if not np.isfinite([*maes, *rmses, *mae_std]).all():
        raise ValueError("Model-comparison figure received non-finite evidence.")
    positions = np.arange(len(labels))
    width = 0.34
    plt = _prepare_matplotlib(output_path)
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.bar(
        positions - width / 2,
        maes,
        width,
        yerr=mae_std,
        capsize=5,
        label="Mean CV MAE",
        color="#2f6b9a",
    )
    axis.bar(
        positions + width / 2,
        rmses,
        width,
        label="Mean CV RMSE",
        color="#e67e22",
    )
    axis.set_title("Phase 6 Supplemental — Development CV Model Comparison")
    axis.set_ylabel("Error (MW)")
    axis.set_xticks(positions, labels)
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    figure.tight_layout()
    _save_figure(figure, output_path)
    plt.close(figure)


def save_lag_sensitivity_figure(
    lag_result: dict,
    output_path: Path,
) -> None:
    """Show validation error and natural eligibility as lag p increases."""

    records = lag_result["p_results"]
    p_values = np.asarray([record["p"] for record in records], dtype="int64")
    maes = np.asarray(
        [record["aggregate"]["mean_cv_mae"] for record in records],
        dtype="float64",
    )
    rmses = np.asarray(
        [record["aggregate"]["mean_cv_rmse"] for record in records],
        dtype="float64",
    )
    eligible = np.asarray(
        [record["natural_eligible_samples"] for record in records],
        dtype="int64",
    )
    if (
        len(records) == 0
        or not np.isfinite(maes).all()
        or not np.isfinite(rmses).all()
    ):
        raise ValueError("Lag-sensitivity figure received invalid evidence.")
    plt = _prepare_matplotlib(output_path)
    figure, axes = plt.subplots(2, 1, figsize=(11, 9), sharex=True)
    axes[0].plot(p_values, maes, marker="o", label="Mean CV MAE", color="#2f6b9a")
    axes[0].plot(p_values, rmses, marker="o", label="Mean CV RMSE", color="#e67e22")
    axes[0].set_ylabel("Error (MW)")
    axes[0].set_title("Fixed XGBoost — Error versus Consecutive Lag Count")
    axes[0].grid(alpha=0.25)
    axes[0].legend()
    axes[1].plot(p_values, eligible, marker="o", color="#5b8c5a")
    axes[1].set_xlabel("Consecutive lag count p")
    axes[1].set_ylabel("Natural eligible samples")
    axes[1].set_title("Natural Development Eligibility versus Lag Count")
    axes[1].set_xticks(p_values)
    axes[1].grid(alpha=0.25)
    figure.suptitle("Phase 6 Supplemental — Lag-p Sensitivity")
    figure.tight_layout()
    _save_figure(figure, output_path)
    plt.close(figure)
