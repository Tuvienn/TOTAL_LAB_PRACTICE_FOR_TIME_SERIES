# Nhiệm vụ: Cung cấp mô hình dự báo chính (ví dụ: Linear/Ridge hoặc ML model với lag features) để so sánh với baseline trong E4..E6.
from typing import Any, List, Optional
import numpy as np
import pandas as pd


def create_lag_features(
    series: pd.Series,
    lags: List[int],
    prefix: str = "lag_",
) -> pd.DataFrame:
    """Tạo các đặc trưng độ trễ (Lag Features) hoàn toàn hướng về quá khứ, không gây rò rỉ tương lai.
    
    Args:
        series: Chuỗi thời gian mục tiêu.
        lags: Danh sách các bước trễ (ví dụ: [1, 2, 3, 12]).
        prefix: Tiền tố tên cột đặc trưng.
        
    Returns:
        DataFrame chứa các cột lag đã dịch chuyển.
    """
    pass


class TimeSeriesForecaster:
    """Mô hình dự báo máy học (ví dụ: Ridge Regression) sử dụng các đặc trưng lag an toàn theo thời gian."""

    def __init__(self, model_type: str = "ridge", **model_params: Any) -> None:
        self.model_type = model_type
        self.model_params = model_params
        self.model: Optional[Any] = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "TimeSeriesForecaster":
        """Huấn luyện mô hình dự báo trên ma trận đặc trưng và nhãn của tập train."""
        pass

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Thực hiện dự báo trên ma trận đặc trưng mới."""
        pass
