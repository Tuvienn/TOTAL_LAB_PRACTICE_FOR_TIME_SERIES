# Nhiệm vụ: Đánh giá và phân tích sai số dự báo phân rã chi tiết theo từng bước chân trời dự báo h = 1..H (E6).
from typing import Dict, List
import numpy as np
import pandas as pd

from presentation_24_10_2026.evaluation.metrics import (
    compute_mae,
    compute_mape,
    compute_rmse,
)


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
    y_t = np.asarray(y_true_matrix, dtype=float)
    y_p = np.asarray(y_pred_matrix, dtype=float)

    if y_t.shape != y_p.shape:
        raise ValueError(f"Shape mismatch: y_true_matrix {y_t.shape} vs y_pred_matrix {y_p.shape}")
    if y_t.ndim != 2:
        raise ValueError(f"Expected 2D matrix (num_folds, horizon), got shape {y_t.shape}")

    num_folds, horizon = y_t.shape
    records = []

    for h_idx in range(horizon):
        h_step = h_idx + 1
        true_h = y_t[:, h_idx]
        pred_h = y_p[:, h_idx]

        mae_h = compute_mae(true_h, pred_h)
        rmse_h = compute_rmse(true_h, pred_h)
        mape_h = compute_mape(true_h, pred_h)

        records.append(
            {
                "horizon": h_step,
                "MAE": mae_h,
                "RMSE": rmse_h,
                "MAPE": mape_h,
            }
        )

    return pd.DataFrame(records)


def summarize_horizon_comparison(
    model_horizon_df: pd.DataFrame,
    baseline_horizon_df: pd.DataFrame,
) -> pd.DataFrame:
    """So sánh sai số của mô hình chính so với baseline tại từng bước chân trời dự báo h."""
    merged = pd.merge(
        model_horizon_df,
        baseline_horizon_df,
        on="horizon",
        suffixes=("_model", "_baseline"),
    )

    merged["MAE_improvement_pct"] = (
        (merged["MAE_baseline"] - merged["MAE_model"]) / merged["MAE_baseline"] * 100.0
    )
    merged["RMSE_improvement_pct"] = (
        (merged["RMSE_baseline"] - merged["RMSE_model"]) / merged["RMSE_baseline"] * 100.0
    )
    return merged
