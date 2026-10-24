# Nhiệm vụ: Tạo 7 biểu đồ trực quan hóa phục vụ phân tích chi tiết và chuẩn bị tài liệu thuyết trình theo yêu cầu của Topic 5.
from typing import Any, Dict, List, Optional
import matplotlib.pyplot as plt
import pandas as pd


def plot_time_series(
    df: pd.DataFrame,
    timestamp_col: str,
    target_col: str,
    title: str = "1. Time Series Overview",
    save_path: Optional[str] = None,
) -> None:
    """Visual 1: Trực quan hóa toàn bộ chuỗi thời gian, làm nổi bật trend và seasonality."""
    pass


def plot_split_comparison(
    df: pd.DataFrame,
    random_train_idx: List[int],
    random_test_idx: List[int],
    temporal_train_idx: List[int],
    temporal_test_idx: List[int],
    title: str = "2. Random Split vs Temporal Split",
    save_path: Optional[str] = None,
) -> None:
    """Visual 2: So sánh trực quan cách phân bổ các quan sát giữa Random Split và Temporal Split trên dòng thời gian."""
    pass


def plot_leakage_distribution_comparison(
    train_correct: pd.Series,
    test_correct: pd.Series,
    train_leakage: pd.Series,
    test_leakage: pd.Series,
    title: str = "3. Scaling Leakage: Wrong vs Correct Distribution",
    save_path: Optional[str] = None,
) -> None:
    """Visual 3: Minh họa sự sai lệch phân phối khi scale toàn bộ chuỗi so với scale chuẩn cách ly train/test."""
    pass


def plot_actual_vs_predicted(
    y_true: pd.Series,
    y_pred_model: pd.Series,
    y_pred_baseline: Optional[pd.Series] = None,
    title: str = "4. Baseline vs Model Forecast",
    save_path: Optional[str] = None,
) -> None:
    """Visual 4: Đồ thị đường so sánh giá trị thực tế, dự báo của Baseline và dự báo của mô hình chính."""
    pass


def plot_backtest_folds(
    total_length: int,
    folds_info: List[Dict[str, Any]],
    title: str = "5. Backtesting Folds Diagram",
    save_path: Optional[str] = None,
) -> None:
    """Visual 5: Sơ đồ minh họa các fold huấn luyện và kiểm chứng qua thời gian (Expanding hoặc Rolling Window)."""
    pass


def plot_performance_across_folds(
    fold_metrics_df: pd.DataFrame,
    metric_name: str = "MAE",
    title: str = "6. Model Performance Across Backtesting Folds",
    save_path: Optional[str] = None,
) -> None:
    """Visual 6: Biểu đồ đường hoặc cột biểu thị sai số của mô hình và baseline qua từng fold."""
    pass


def plot_error_by_horizon(
    horizon_metrics_df: pd.DataFrame,
    metrics: List[str] = ["MAE", "RMSE"],
    title: str = "7. Error by Forecast Horizon (h = 1..H)",
    save_path: Optional[str] = None,
) -> None:
    """Visual 7: Biểu đồ quan hệ giữa độ lớn sai số và khoảng cách dự báo h."""
    pass
