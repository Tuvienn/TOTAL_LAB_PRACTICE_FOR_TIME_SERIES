# Nhiệm vụ: Đánh giá và phân tích sai số dự báo phân rã chi tiết theo từng bước chân trời dự báo h = 1..H (E6).
from typing import Dict, List
import numpy as np
import pandas as pd


def evaluate_by_horizon(
    y_true_matrix: np.ndarray,
    y_pred_matrix: np.ndarray,
) -> pd.DataFrame:
    """Tính toán MAE, RMSE, MAPE độc lập cho từng bước dự báo h = 1, 2, ..., H.
    
    Args:
        y_true_matrix: Ma trận giá trị thực tế shape (num_folds, H).
        y_pred_matrix: Ma trận giá trị dự báo shape (num_folds, H).
        
    Returns:
        DataFrame chứa các cột 'horizon', 'MAE', 'RMSE', 'MAPE'.
    """
    pass


def summarize_horizon_comparison(
    model_horizon_df: pd.DataFrame,
    baseline_horizon_df: pd.DataFrame,
) -> pd.DataFrame:
    """So sánh sai số của mô hình chính so với baseline tại từng bước chân trời dự báo h.
    
    Args:
        model_horizon_df: Bảng sai số theo horizon của mô hình chính.
        baseline_horizon_df: Bảng sai số theo horizon của baseline.
        
    Returns:
        DataFrame so sánh chênh lệch phần trăm hoặc giá trị tuyệt đối.
    """
    pass
