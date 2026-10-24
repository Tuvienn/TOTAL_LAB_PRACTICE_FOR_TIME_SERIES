# Nhiệm vụ: Cung cấp các mô hình mốc tham chiếu chuẩn: Naive Forecast và Seasonal Naive Forecast cho thực nghiệm E4.
from typing import Optional
import numpy as np
import pandas as pd


class NaiveForecaster:
    """Mô hình Naive Forecast (Persistence): Giá trị dự báo cho tương lai bằng giá trị quan sát gần nhất ở thời điểm t."""

    def __init__(self) -> None:
        self.last_value: Optional[float] = None

    def fit(self, y: pd.Series) -> "NaiveForecaster":
        """Lưu lại giá trị quan sát cuối cùng của tập huấn luyện."""
        pass

    def predict(self, horizon: int) -> np.ndarray:
        """Dự báo horizon bước tiếp theo bằng cách lặp lại giá trị quan sát cuối cùng."""
        pass


class SeasonalNaiveForecaster:
    """Mô hình Seasonal Naive: Giá trị dự báo tại thời điểm t+h bằng giá trị quan sát ở cùng vị trí của chu kỳ trước (t+h-m)."""

    def __init__(self, season_length: int = 12) -> None:
        self.season_length = season_length
        self.history: Optional[np.ndarray] = None

    def fit(self, y: pd.Series) -> "SeasonalNaiveForecaster":
        """Lưu lại chu kỳ quan sát gần nhất của tập huấn luyện."""
        pass

    def predict(self, horizon: int) -> np.ndarray:
        """Dự báo horizon bước tiếp theo dựa trên chu kỳ quá khứ tương ứng."""
        pass
