# Nhiệm vụ: Triển khai 2 pipeline scaling: Pipeline A (Data Leakage) và Pipeline B (Correct) để so sánh trong thực nghiệm E3.
from typing import Any, List, Tuple
import pandas as pd


def scale_with_leakage(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str],
    scaler_type: str = "standard",
) -> Tuple[pd.DataFrame, pd.DataFrame, Any]:
    """Pipeline A (SAI PHẠM - LEAKAGE): Fit scaler trên toàn bộ dữ liệu trước khi chia hoặc dùng thông tin test.
    
    Quy trình sai: Toàn bộ dữ liệu -> Fit Scaler -> Transform -> Đưa vào đánh giá.
    
    Args:
        train_df: DataFrame tập train.
        test_df: DataFrame tập test.
        feature_cols: Danh sách các cột cần scale.
        scaler_type: Loại scaler ('standard' hoặc 'minmax').
        
    Returns:
        Tuple gồm (train_scaled, test_scaled, scaler_object).
    """
    pass


def scale_without_leakage(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str],
    scaler_type: str = "standard",
) -> Tuple[pd.DataFrame, pd.DataFrame, Any]:
    """Pipeline B (CHUẨN - CORRECT): Fit scaler CHỈ trên tập train, sau đó dùng tham số đã học để transform test.
    
    Quy trình chuẩn: Chia dữ liệu theo thời gian -> Fit Scaler trên Train -> Transform Train & Test.
    
    Args:
        train_df: DataFrame tập train.
        test_df: DataFrame tập test.
        feature_cols: Danh sách các cột cần scale.
        scaler_type: Loại scaler ('standard' hoặc 'minmax').
        
    Returns:
        Tuple gồm (train_scaled, test_scaled, scaler_object).
    """
    pass
