# Nhiệm vụ: Tạo 7 biểu đồ trực quan hóa phục vụ phân tích chi tiết và chuẩn bị tài liệu thuyết trình theo yêu cầu của Topic 5.
from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _save_fig_if_needed(fig: plt.Figure, save_path: Optional[str] = None) -> None:
    if save_path:
        out_file = Path(save_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_file, dpi=150, bbox_inches="tight")


def plot_time_series(
    df: pd.DataFrame,
    timestamp_col: str,
    target_col: str,
    title: str = "Visual 1: Time Series Overview (AirPassengers)",
    save_path: Optional[str] = None,
) -> None:
    """Visual 1: Trực quan hóa toàn bộ chuỗi thời gian, làm nổi bật trend và seasonality."""
    fig, ax = plt.subplots(figsize=(10, 5))
    x_vals = df[timestamp_col] if timestamp_col in df.columns else df.index
    y_vals = df[target_col]

    ax.plot(x_vals, y_vals, color="#1f77b4", linewidth=1.8, marker="o", markersize=3, label="Actual Observed")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Time (Month / Year)", fontsize=11)
    ax.set_ylabel("Passengers (Thousands)", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper left")
    plt.tight_layout()
    _save_fig_if_needed(fig, save_path)
    plt.close(fig)


def plot_split_comparison(
    df: pd.DataFrame,
    random_train_idx: List[int],
    random_test_idx: List[int],
    temporal_train_idx: List[int],
    temporal_test_idx: List[int],
    title: str = "Visual 2: Random Split vs Temporal Split Observation Timeline",
    save_path: Optional[str] = None,
) -> None:
    """Visual 2: So sánh trực quan cách phân bổ các quan sát giữa Random Split và Temporal Split trên dòng thời gian."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 4.5), sharex=True)
    n = len(df)
    indices = np.arange(n)

    # Random split: 1 for train, 0 for test
    rand_status = np.zeros(n)
    rand_status[random_train_idx] = 1

    temp_status = np.zeros(n)
    temp_status[temporal_train_idx] = 1

    # Plot Random Split
    ax1.scatter(indices[rand_status == 1], np.ones(np.sum(rand_status == 1)), color="#2ca02c", s=25, label="Train (80%)")
    ax1.scatter(indices[rand_status == 0], np.ones(np.sum(rand_status == 0)), color="#d62728", s=25, marker="x", label="Test (20%) - Shuffled!")
    ax1.set_yticks([1])
    ax1.set_yticklabels(["Random Split"], fontsize=11, fontweight="bold")
    ax1.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax1.legend(loc="upper right", framealpha=0.9)
    ax1.grid(True, axis="x", linestyle="--", alpha=0.5)

    # Plot Temporal Split
    ax2.scatter(indices[temp_status == 1], np.ones(np.sum(temp_status == 1)), color="#2ca02c", s=25, label="Train (Quá khứ)")
    ax2.scatter(indices[temp_status == 0], np.ones(np.sum(temp_status == 0)), color="#1f77b4", s=25, marker="s", label="Test (Tương lai)")
    ax2.set_yticks([1])
    ax2.set_yticklabels(["Temporal Split"], fontsize=11, fontweight="bold")
    ax2.set_xlabel("Time Index (t = 0 ... N-1)", fontsize=11)
    ax2.axvline(x=len(temporal_train_idx) - 0.5, color="black", linestyle="--", linewidth=1.5, label="Cutoff Origin")
    ax2.legend(loc="upper right", framealpha=0.9)
    ax2.grid(True, axis="x", linestyle="--", alpha=0.5)

    plt.tight_layout()
    _save_fig_if_needed(fig, save_path)
    plt.close(fig)


def plot_leakage_distribution_comparison(
    train_correct: pd.Series,
    test_correct: pd.Series,
    train_leakage: pd.Series,
    test_leakage: pd.Series,
    title: str = "Visual 3: Scaling Leakage - Parameter & Distribution Distortion",
    save_path: Optional[str] = None,
) -> None:
    """Visual 3: Minh họa sự sai lệch phân phối khi scale toàn bộ chuỗi so với scale chuẩn cách ly train/test."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)

    # Pipeline B: Correct
    ax1.hist(train_correct, bins=15, alpha=0.6, color="#2ca02c", label="Train (Fit Scaler)")
    ax1.hist(test_correct, bins=15, alpha=0.6, color="#1f77b4", label="Test (Transform Only)")
    ax1.set_title("Pipeline B: Correct Isolation\n(Scaler fit CHỈ trên Train)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Standardized Value (z-score)", fontsize=10)
    ax1.set_ylabel("Frequency", fontsize=10)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right")

    # Pipeline A: Leakage
    ax2.hist(train_leakage, bins=15, alpha=0.6, color="#d62728", label="Train (Biased)")
    ax2.hist(test_leakage, bins=15, alpha=0.6, color="#ff7f0e", label="Test (Contaminated)")
    ax2.set_title("Pipeline A: Data Leakage\n(Scaler fit trên TOÀN BỘ)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Standardized Value (z-score)", fontsize=10)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right")

    plt.suptitle(title, fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    _save_fig_if_needed(fig, save_path)
    plt.close(fig)


def plot_actual_vs_predicted(
    y_true: pd.Series,
    y_pred_model: pd.Series,
    y_pred_baseline: Optional[pd.Series] = None,
    baseline_label: str = "Seasonal Naive",
    title: str = "Visual 4: Actual vs Baseline vs Model Forecast",
    save_path: Optional[str] = None,
) -> None:
    """Visual 4: Đồ thị đường so sánh giá trị thực tế, dự báo của Baseline và dự báo của mô hình chính."""
    fig, ax = plt.subplots(figsize=(10, 5))
    x_axis = np.arange(len(y_true))
    if isinstance(y_true.index, pd.DatetimeIndex):
        x_axis = y_true.index

    ax.plot(x_axis, y_true, color="black", linewidth=2.0, marker="o", label="Actual Test Ground Truth")
    if y_pred_baseline is not None:
        ax.plot(x_axis, y_pred_baseline, color="#ff7f0e", linestyle="--", linewidth=1.8, label=f"Baseline ({baseline_label})")
    ax.plot(x_axis, y_pred_model, color="#1f77b4", linestyle="-.", linewidth=2.0, marker="s", markersize=4, label="Forecaster (Ridge + Lags)")

    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Test Horizon Timeline", fontsize=11)
    ax.set_ylabel("Value", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper left")
    plt.tight_layout()
    _save_fig_if_needed(fig, save_path)
    plt.close(fig)


def plot_backtest_folds(
    total_length: int,
    folds_info: List[Dict[str, Any]],
    title: str = "Visual 5: Backtesting Folds Diagram (Expanding Window)",
    save_path: Optional[str] = None,
) -> None:
    """Visual 5: Sơ đồ minh họa các fold huấn luyện và kiểm chứng qua thời gian (Expanding hoặc Rolling Window)."""
    fig, ax = plt.subplots(figsize=(10, max(4, len(folds_info) * 0.7)))
    num_folds = len(folds_info)

    for i, fold in enumerate(reversed(folds_info)):
        fold_num = fold.get("fold", i + 1)
        y_pos = i
        train_size = fold["train_size"]
        val_size = fold["val_size"]

        if fold.get("strategy") == "rolling":
            train_start = total_length - (num_folds - fold_num + 1) * fold["step_size"] - train_size
            train_start = max(0, train_size * (fold_num - 1)) # approx for visualization
        else:
            train_start = 0

        # Draw Train Bar
        ax.barh(y_pos, train_size, left=train_start, color="#2ca02c", alpha=0.85, height=0.5, label="Train Window" if i == 0 else "")
        # Draw Validation Bar
        ax.barh(y_pos, val_size, left=train_start + train_size, color="#1f77b4", alpha=0.85, height=0.5, label="Validation Horizon" if i == 0 else "")

    ax.set_yticks(range(num_folds))
    ax.set_yticklabels([f"Fold {f.get('fold', len(folds_info)-idx)}" for idx, f in enumerate(reversed(folds_info))], fontsize=10)
    ax.set_xlabel("Timeline Steps (t)", fontsize=11)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right")
    plt.tight_layout()
    _save_fig_if_needed(fig, save_path)
    plt.close(fig)


def plot_performance_across_folds(
    fold_metrics_df: pd.DataFrame,
    metric_name: str = "MAE",
    title: str = "Visual 6: Performance Stability Across Backtesting Folds",
    save_path: Optional[str] = None,
) -> None:
    """Visual 6: Biểu đồ cột/đường biểu thị sai số của mô hình và baseline qua từng fold."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    folds = fold_metrics_df["fold"].astype(str)
    x = np.arange(len(folds))

    model_metric = fold_metrics_df[f"{metric_name}_model"] if f"{metric_name}_model" in fold_metrics_df.columns else fold_metrics_df[metric_name]
    ax.plot(x, model_metric, marker="o", linewidth=2, color="#1f77b4", label=f"Model {metric_name}")

    if f"{metric_name}_baseline" in fold_metrics_df.columns:
        ax.plot(x, fold_metrics_df[f"{metric_name}_baseline"], marker="s", linestyle="--", linewidth=1.8, color="#ff7f0e", label=f"Baseline {metric_name}")

    ax.set_xticks(x)
    ax.set_xticklabels([f"Fold {f}" for f in folds], fontsize=10)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Backtesting Folds", fontsize=11)
    ax.set_ylabel(metric_name, fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="best")
    plt.tight_layout()
    _save_fig_if_needed(fig, save_path)
    plt.close(fig)


def plot_error_by_horizon(
    horizon_metrics_df: pd.DataFrame,
    metrics: List[str] = ["MAE", "RMSE"],
    title: str = "Visual 7: Error by Forecast Horizon (h = 1..H)",
    save_path: Optional[str] = None,
) -> None:
    """Visual 7: Biểu đồ quan hệ giữa độ lớn sai số và khoảng cách dự báo h."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    h_steps = horizon_metrics_df["horizon"]

    colors = ["#1f77b4", "#d62728", "#2ca02c"]
    for i, m in enumerate(metrics):
        if m in horizon_metrics_df.columns:
            ax.plot(h_steps, horizon_metrics_df[m], marker="o", linewidth=2.0, color=colors[i % len(colors)], label=f"Model {m}")
        if f"{m}_baseline" in horizon_metrics_df.columns:
            ax.plot(h_steps, horizon_metrics_df[f"{m}_baseline"], marker="^", linestyle="--", linewidth=1.5, color=colors[i % len(colors)], alpha=0.7, label=f"Baseline {m}")

    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Forecast Horizon Step (h)", fontsize=11)
    ax.set_ylabel("Error Value", fontsize=11)
    ax.set_xticks(h_steps)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="best")
    plt.tight_layout()
    _save_fig_if_needed(fig, save_path)
    plt.close(fig)
