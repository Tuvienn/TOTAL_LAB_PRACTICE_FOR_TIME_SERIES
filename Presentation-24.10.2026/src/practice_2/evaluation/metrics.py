# Nhiệm vụ: Tính toán các chỉ số đánh giá sai số mô hình dự báo gồm MAE, RMSE, MAPE và phân tích giới hạn của từng chỉ số.
from typing import Dict
import numpy as np


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Tính sai số tuyệt đối trung bình: MAE = (1/n) * sum(|y - y_hat|).
    
    Đơn vị cùng đơn vị với biến mục tiêu, ít nhạy với ngoại lệ hơn RMSE.
    """
    pass


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Tính căn bậc hai sai số bình phương trung bình: RMSE = sqrt((1/n) * sum((y - y_hat)^2)).
    
    Phạt nặng các sai số lớn, nhạy cảm với ngoại lệ.
    """
    pass


def compute_mape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-8) -> float:
    """Tính sai số phần trăm tuyệt đối trung bình: MAPE = (100%/n) * sum(|(y - y_hat) / y|).
    
    Cảnh báo: Không xác định hoặc bùng nổ khi y_true tiến sát hoặc bằng 0.
    """
    pass


def compute_all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Tổng hợp tính toán đồng thời MAE, RMSE và MAPE cho một lần đánh giá.
    
    Returns:
        Dict gồm các khóa 'MAE', 'RMSE', 'MAPE'.
    """
    pass
