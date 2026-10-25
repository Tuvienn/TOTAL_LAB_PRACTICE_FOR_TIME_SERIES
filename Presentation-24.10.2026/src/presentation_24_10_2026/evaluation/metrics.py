# Nhiệm vụ: Tính toán các chỉ số đánh giá sai số mô hình dự báo gồm MAE, RMSE, MAPE và phân tích giới hạn của từng chỉ số.
from typing import Dict
import numpy as np


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Tính sai số tuyệt đối trung bình: MAE = (1/n) * sum(|y - y_hat|)."""
    y_t = np.asarray(y_true, dtype=float).ravel()
    y_p = np.asarray(y_pred, dtype=float).ravel()
    if len(y_t) == 0:
        raise ValueError("Inputs must not be empty.")
    return float(np.mean(np.abs(y_t - y_p)))


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Tính căn bậc hai sai số bình phương trung bình: RMSE = sqrt((1/n) * sum((y - y_hat)^2))."""
    y_t = np.asarray(y_true, dtype=float).ravel()
    y_p = np.asarray(y_pred, dtype=float).ravel()
    if len(y_t) == 0:
        raise ValueError("Inputs must not be empty.")
    return float(np.sqrt(np.mean((y_t - y_p) ** 2)))


def compute_mape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-8) -> float:
    """Tính sai số phần trăm tuyệt đối trung bình: MAPE = (100%/n) * sum(|(y - y_hat) / y|)."""
    y_t = np.asarray(y_true, dtype=float).ravel()
    y_p = np.asarray(y_pred, dtype=float).ravel()
    if len(y_t) == 0:
        raise ValueError("Inputs must not be empty.")
    denom = np.where(np.abs(y_t) < eps, eps, np.abs(y_t))
    return float(np.mean(np.abs((y_t - y_p) / denom)) * 100.0)


def compute_all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Tổng hợp tính toán đồng thời MAE, RMSE và MAPE cho một lần đánh giá."""
    return {
        "MAE": compute_mae(y_true, y_pred),
        "RMSE": compute_rmse(y_true, y_pred),
        "MAPE": compute_mape(y_true, y_pred),
    }
