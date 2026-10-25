# Nhiệm vụ: Trực quan hóa 7 biểu đồ chuẩn mực cho Topic 5 theo triết lý tinh gọn, thẩm mỹ và độ tin cậy cao.
from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Cấu hình font tương thích cao với tiếng Việt, loại bỏ bold mặc định và thiết lập nét vẽ chuẩn mực
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [
    "DejaVu Sans",
    "Segoe UI",
    "Arial",
    "Helvetica",
    "sans-serif",
]
plt.rcParams["font.weight"] = "normal"
plt.rcParams["axes.titleweight"] = "normal"
plt.rcParams["axes.labelweight"] = "normal"


def _save_figure(figure: plt.Figure, output_path: Optional[Any] = None) -> None:
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(out_file, dpi=150, bbox_inches="tight")
    plt.close(figure)


_save_and_close = _save_figure


def plot_time_series(
    frame: pd.DataFrame,
    output_path: Optional[Any] = None,
    timestamp_col: str = "date",
    target_col: str = "passengers_thousands",
    title: str = "Monthly International Airline Passengers (1949–1960)",
    save_path: Optional[Any] = None,
) -> None:
    """Visual 1: Trực quan hóa toàn bộ chuỗi thời gian kèm đường Max, Min và Annual Average."""
    target_out = output_path if output_path is not None else save_path

    plot_df = frame.copy()
    if not isinstance(plot_df.index, pd.DatetimeIndex) and timestamp_col in plot_df.columns:
        plot_df = plot_df.set_index(pd.to_datetime(plot_df[timestamp_col]))

    if "passengers_thousands" in plot_df.columns:
        target_series = plot_df["passengers_thousands"]
    elif target_col in plot_df.columns:
        target_series = plot_df[target_col]
    elif "value" in plot_df.columns:
        target_series = plot_df["value"]
    else:
        target_series = plot_df.select_dtypes(include=[np.number]).iloc[:, 0]

    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(plot_df.index, target_series, color="#1769aa", linewidth=1.8, label="Monthly Observed")
    min_val = float(target_series.min())
    max_val = float(target_series.max())
    axis.axhline(
        max_val,
        color="#85db87",
        linestyle="--",
        linewidth=1.125,
        label=f"Max ({int(max_val)})",
    )

    try:
        yearly_avg = target_series.resample("YE").mean()
    except ValueError:
        yearly_avg = target_series.resample("Y").mean()

    axis.plot(
        yearly_avg.index,
        yearly_avg.values,
        color="#f59e0b",
        linestyle="--",
        linewidth=1.3,
        marker="o",
        markersize=5,
        label="Annual Average",
    )
    axis.axhline(
        min_val,
        color="#d32f2f",
        linestyle="--",
        linewidth=1.125,
        label=f"Min ({int(min_val)})",
    )

    axis.set_title(title)
    axis.set_xlabel("Date")
    axis.set_ylabel("Passengers (thousands)")
    axis.grid(alpha=0.25)
    axis.legend(loc="upper left")
    plt.tight_layout()
    _save_figure(figure, target_out)


def plot_split_comparison(
    df: pd.DataFrame,
    random_train_idx: Any,
    random_test_idx: Any,
    temporal_train_idx: Any,
    temporal_test_idx: Any,
    title: str = "Visual 2: Random Split vs Temporal Split Timeline",
    save_path: Optional[str] = None,
) -> None:
    """Visual 2: So sánh phân bổ các quan sát giữa Random Split và Temporal Split trên dòng thời gian."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 4.5), sharex=True)

    ax1.scatter(random_train_idx, np.ones(len(random_train_idx)), color="tab:green", s=20, label="Train (80%)")
    ax1.scatter(random_test_idx, np.ones(len(random_test_idx)), color="tab:red", s=20, marker="x", label="Test (20%)")
    ax1.set_yticks([1])
    ax1.set_yticklabels(["Random Split"])
    ax1.set_title(title, pad=10)
    ax1.legend(loc="upper right")
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2.scatter(temporal_train_idx, np.ones(len(temporal_train_idx)), color="tab:green", s=20, label="Train")
    ax2.scatter(temporal_test_idx, np.ones(len(temporal_test_idx)), color="tab:blue", s=20, marker="s", label="Test")
    ax2.set_yticks([1])
    ax2.set_yticklabels(["Temporal Split"])
    ax2.set_xlabel("Time Index (t)")
    ax2.legend(loc="upper right")
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    _save_and_close(fig, save_path)


def plot_leakage_distribution_comparison(
    train_correct: pd.Series,
    test_correct: pd.Series,
    train_leakage: pd.Series,
    test_leakage: pd.Series,
    title: str = "Visual 3: Scaling Leakage - Distribution Distortion",
    save_path: Optional[str] = None,
) -> None:
    """Visual 3: Minh họa sự sai lệch phân phối khi scale toàn bộ chuỗi so với scale chuẩn cách ly."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)

    ax1.hist(train_correct, bins=15, alpha=0.6, color="tab:green", label="Train")
    ax1.hist(test_correct, bins=15, alpha=0.6, color="tab:blue", label="Test")
    ax1.set_title("Pipeline B: Correct Isolation\n(Scaler fit on Train only)")
    ax1.set_xlabel("Standardized Value (z-score)")
    ax1.set_ylabel("Frequency")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right")

    ax2.hist(train_leakage, bins=15, alpha=0.6, color="tab:red", label="Train")
    ax2.hist(test_leakage, bins=15, alpha=0.6, color="tab:orange", label="Test")
    ax2.set_title("Pipeline A: Data Leakage\n(Scaler fit on entire series)")
    ax2.set_xlabel("Standardized Value (z-score)")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right")

    plt.suptitle(title, y=1.02)
    plt.tight_layout()
    _save_and_close(fig, save_path)


def plot_actual_vs_predicted(
    y_true: pd.Series,
    y_pred_model: pd.Series,
    y_pred_baseline: Optional[pd.Series] = None,
    baseline_label: str = "Seasonal Naive",
    title: str = "Visual 4: Actual vs Baseline vs Model Forecast",
    save_path: Optional[str] = None,
) -> None:
    """Visual 4: Đồ thị đường so sánh giá trị thực tế, dự báo của Baseline và mô hình máy học."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = y_true.index if isinstance(y_true.index, pd.DatetimeIndex) else np.arange(len(y_true))

    ax.plot(x, y_true, color="black", linewidth=2.0, marker="o", label="Actual Test Ground Truth")
    if y_pred_baseline is not None:
        ax.plot(x, y_pred_baseline, color="tab:orange", linestyle="--", linewidth=1.8, label=f"Baseline ({baseline_label})")
    ax.plot(x, y_pred_model, color="tab:blue", linestyle="-.", linewidth=2.0, marker="s", markersize=4, label="Forecaster (Ridge + Lags)")

    ax.set_title(title, pad=10)
    ax.set_xlabel("Timeline")
    ax.set_ylabel("Passengers (thousands)")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")
    plt.tight_layout()
    _save_and_close(fig, save_path)


def plot_backtest_folds(
    *args: Any,
    title: str = "Visual 5: Backtesting Folds Diagram (Expanding Window)",
    save_path: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Visual 5: Sơ đồ minh họa các fold huấn luyện và kiểm chứng qua dòng thời gian."""
    folds_info = args[0] if len(args) == 1 else (args[1] if len(args) >= 2 else kwargs.get("folds_info", []))
    num_folds = len(folds_info)
    fig, ax = plt.subplots(figsize=(10, max(3.5, num_folds * 0.6)))

    for i, fold in enumerate(reversed(folds_info)):
        train_size = fold["train_size"]
        val_size = fold["val_size"]
        train_start = fold.get("train_start_idx", 0)
        val_start = fold.get("val_start_idx", train_start + train_size)

        ax.barh(i, train_size, left=train_start, color="tab:green", alpha=0.85, height=0.5, label="Train" if i == 0 else "")
        ax.barh(i, val_size, left=val_start, color="tab:blue", alpha=0.85, height=0.5, label="Validation" if i == 0 else "")

    ax.set_yticks(range(num_folds))
    ax.set_yticklabels([f"Fold {f.get('fold', num_folds - idx)}" for idx, f in enumerate(reversed(folds_info))])
    ax.set_xlabel("Timeline Steps (t)")
    ax.set_title(title, pad=10)
    ax.grid(True, axis="x", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right")
    plt.tight_layout()
    _save_and_close(fig, save_path)


def plot_performance_across_folds(
    fold_metrics_df: pd.DataFrame,
    metric_name: str = "MAE",
    title: str = "Visual 6: Performance Stability Across Folds",
    save_path: Optional[str] = None,
) -> None:
    """Visual 6: Biểu đồ đường biểu thị sai số của mô hình và baseline qua từng fold."""
    fig, ax = plt.subplots(figsize=(9, 4.2))
    folds = fold_metrics_df["fold"]
    x = np.arange(len(folds))

    model_col = f"{metric_name}_model" if f"{metric_name}_model" in fold_metrics_df.columns else metric_name
    ax.plot(x, fold_metrics_df[model_col], marker="o", linewidth=2, color="tab:blue", label=f"Model {metric_name}")

    base_col = f"{metric_name}_baseline"
    if base_col in fold_metrics_df.columns:
        ax.plot(x, fold_metrics_df[base_col], marker="s", linestyle="--", linewidth=1.8, color="tab:orange", label=f"Baseline {metric_name}")

    ax.set_xticks(x)
    ax.set_xticklabels([f"Fold {f}" for f in folds])
    ax.set_title(title, pad=10)
    ax.set_xlabel("Backtesting Folds")
    ax.set_ylabel(metric_name)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="best")
    plt.tight_layout()
    _save_and_close(fig, save_path)


def plot_error_by_horizon(
    horizon_metrics_df: pd.DataFrame,
    metrics: List[str] = ["MAE", "RMSE"],
    title: str = "Visual 7: Error by Forecast Horizon (h = 1..H)",
    save_path: Optional[str] = None,
) -> None:
    """Visual 7: Biểu đồ quan hệ giữa độ lớn sai số và khoảng cách dự báo h."""
    fig, ax = plt.subplots(figsize=(9, 4.2))
    h = horizon_metrics_df["horizon"]

    colors = ["tab:blue", "tab:red", "tab:green"]
    for i, m in enumerate(metrics):
        if m in horizon_metrics_df.columns:
            ax.plot(h, horizon_metrics_df[m], marker="o", linewidth=2.0, color=colors[i % len(colors)], label=f"Model {m}")
        if f"{m}_baseline" in horizon_metrics_df.columns:
            ax.plot(h, horizon_metrics_df[f"{m}_baseline"], marker="^", linestyle="--", linewidth=1.5, color=colors[i % len(colors)], alpha=0.7, label=f"Baseline {m}")

    ax.set_title(title, pad=10)
    ax.set_xlabel("Forecast Horizon Step (h)")
    ax.set_ylabel("Error Value")
    ax.set_xticks(h)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="best")
    plt.tight_layout()
    _save_and_close(fig, save_path)
