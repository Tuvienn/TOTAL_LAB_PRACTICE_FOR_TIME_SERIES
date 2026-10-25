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
        if len(y) == 0:
            raise ValueError("Training series y must not be empty.")
        self.last_value = float(y.iloc[-1])
        return self

    def predict(self, horizon: int) -> np.ndarray:
        """Dự báo horizon bước tiếp theo bằng cách lặp lại giá trị quan sát cuối cùng."""
        if self.last_value is None:
            raise RuntimeError("NaiveForecaster must be fitted before predict.")
        if horizon <= 0:
            raise ValueError(f"horizon must be positive, got {horizon}")
        return np.full(horizon, self.last_value, dtype=float)


class SeasonalNaiveForecaster:
    """Mô hình Seasonal Naive: Giá trị dự báo tại thời điểm t+h bằng giá trị quan sát ở cùng vị trí của chu kỳ trước (t+h-m)."""

    def __init__(self, season_length: int = 12) -> None:
        if season_length <= 0:
            raise ValueError(f"season_length must be positive, got {season_length}")
        self.season_length = season_length
        self.history: Optional[np.ndarray] = None

    def fit(self, y: pd.Series) -> "SeasonalNaiveForecaster":
        """Lưu lại chu kỳ quan sát gần nhất của tập huấn luyện."""
        if len(y) < self.season_length:
            raise ValueError(
                f"Training series length ({len(y)}) is smaller than season_length ({self.season_length})."
            )
        vals = y.to_numpy(dtype=float)
        self.history = vals[-self.season_length:].copy()
        return self

    def predict(self, horizon: int) -> np.ndarray:
        """Dự báo horizon bước tiếp theo dựa trên chu kỳ quá khứ tương ứng."""
        if self.history is None:
            raise RuntimeError("SeasonalNaiveForecaster must be fitted before predict.")
        if horizon <= 0:
            raise ValueError(f"horizon must be positive, got {horizon}")
        reps = int(np.ceil(horizon / self.season_length))
        tiled = np.tile(self.history, reps)
        return tiled[:horizon].astype(float)
