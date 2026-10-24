# Nhiệm vụ: Tải dữ liệu chuỗi thời gian, kiểm tra timestamp, tần suất và đánh giá chất lượng dữ liệu ban đầu (E1).
from typing import Any, Optional
import pandas as pd


def load_time_series_data(
    file_path: str,
    timestamp_col: str,
    target_col: str,
    date_format: Optional[str] = None,
) -> pd.DataFrame:
    """Tải dữ liệu từ tệp tin, phân tích định dạng timestamp và sắp xếp thứ tự thời gian.
    
    Args:
        file_path: Đường dẫn tệp CSV dữ liệu.
        timestamp_col: Tên cột thời gian.
        target_col: Tên cột giá trị chuỗi thời gian cần dự báo.
        date_format: Định dạng ngày giờ nếu cần thiết.
        
    Returns:
        DataFrame đã được sắp xếp tăng dần theo thời gian.
    """
    pass


def validate_time_index(
    df: pd.DataFrame,
    timestamp_col: str,
    expected_freq: Optional[str] = None,
) -> dict[str, Any]:
    """Kiểm tra tính hợp lệ của trục thời gian: kiểm tra trùng lặp, tính liên tục và khoảng cách thời gian.
    
    Args:
        df: DataFrame chứa dữ liệu chuỗi thời gian.
        timestamp_col: Tên cột thời gian.
        expected_freq: Tần suất kỳ vọng (ví dụ: 'MS', 'D', 'h').
        
    Returns:
        Từ điển chứa thông tin kiểm tra tính hợp lệ của time index.
    """
    pass


def check_data_quality(
    df: pd.DataFrame,
    target_col: str,
) -> dict[str, Any]:
    """Đánh giá chất lượng dữ liệu: số lượng missing values, outliers sơ bộ, min, max, mean, std.
    
    Args:
        df: DataFrame cần kiểm tra.
        target_col: Tên cột giá trị mục tiêu.
        
    Returns:
        Từ điển tổng kết các chỉ số chất lượng dữ liệu.
    """
    pass
