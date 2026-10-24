# Nhiệm vụ: Triển khai quy trình kiểm chứng lịch sử đa mốc: Expanding Window Backtesting và Rolling Window Backtesting (E5).
from typing import Any, Callable, Dict, List
import pandas as pd


def expanding_window_backtest(
    df: pd.DataFrame,
    initial_train_size: int,
    horizon: int,
    step_size: int,
    model_trainer_fn: Callable[[pd.DataFrame, int], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Thực hiện Expanding Window Backtesting: Kích thước train mở rộng dần theo thời gian.
    
    Quy tắc an toàn: Mỗi fold fit riêng scaler/model trên tập train của fold đó, không dùng dữ liệu tương lai.
    
    Args:
        df: DataFrame chuỗi thời gian đã sắp xếp.
        initial_train_size: Số lượng quan sát tối thiểu của fold đầu tiên.
        horizon: Số bước dự báo về phía trước (forecast horizon H).
        step_size: Bước dịch chuyển của forecast origin giữa các fold.
        model_trainer_fn: Hàm callback nhận (train_fold, horizon) và trả về kết quả dự báo/metrics.
        
    Returns:
        Danh sách kết quả chi tiết từng fold.
    """
    pass


def rolling_window_backtest(
    df: pd.DataFrame,
    window_size: int,
    horizon: int,
    step_size: int,
    model_trainer_fn: Callable[[pd.DataFrame, int], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Thực hiện Rolling Window Backtesting: Kích thước tập train cố định, loại bỏ dữ liệu cũ nhất khi dịch về phía trước.
    
    Args:
        df: DataFrame chuỗi thời gian đã sắp xếp.
        window_size: Độ dài cố định của cửa sổ huấn luyện.
        horizon: Số bước dự báo về phía trước.
        step_size: Bước dịch chuyển của forecast origin.
        model_trainer_fn: Hàm callback huấn luyện và đánh giá.
        
    Returns:
        Danh sách kết quả chi tiết từng fold.
    """
    pass


def summarize_backtest_results(fold_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Tổng hợp mean, standard deviation, min, max của các metric qua tất cả các fold backtest.
    
    Args:
        fold_results: Kết quả đầu ra từ expanding hoặc rolling backtest.
        
    Returns:
        DataFrame tóm tắt hiệu năng và độ ổn định của mô hình.
    """
    pass
