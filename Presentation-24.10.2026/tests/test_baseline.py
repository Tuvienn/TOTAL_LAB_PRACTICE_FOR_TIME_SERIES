import numpy as np
import pandas as pd

from presentation_24_10_2026.models.baseline import (
    NaiveForecaster,
    SeasonalNaiveForecaster,
)


def test_naive_forecaster_persistence() -> None:
    """Xác nhận Naive Forecaster dự báo đúng giá trị cuối cùng của tập train cho toàn bộ horizon."""
    y_train = pd.Series([10.0, 20.0, 35.0])
    model = NaiveForecaster()
    model.fit(y_train)
    preds = model.predict(horizon=5)
    
    assert len(preds) == 5
    assert np.allclose(preds, 35.0)


def test_seasonal_naive_forecaster_lag() -> None:
    """Xác nhận Seasonal Naive Forecaster dự báo lặp lại chính xác giá trị ở chu kỳ trước tương ứng."""
    # Chu kỳ 4 quý
    y_train = pd.Series([1.0, 2.0, 3.0, 4.0, 10.0, 20.0, 30.0, 40.0])
    model = SeasonalNaiveForecaster(season_length=4)
    model.fit(y_train)
    preds = model.predict(horizon=6)
    
    assert len(preds) == 6
    expected = np.array([10.0, 20.0, 30.0, 40.0, 10.0, 20.0])
    assert np.allclose(preds, expected)
