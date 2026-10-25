import numpy as np
import pandas as pd

from presentation_24_10_2026.data.split import (
    random_train_test_split,
    temporal_train_test_split,
)


def test_temporal_train_test_split_order() -> None:
    """Xác nhận rằng tập train kết thúc trước khi tập test bắt đầu, bảo toàn 100% trật tự thời gian."""
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    df = pd.DataFrame({"date": dates, "value": np.arange(100)})
    
    train_df, test_df = temporal_train_test_split(df, test_ratio=0.2, timestamp_col="date")
    assert len(train_df) == 80
    assert len(test_df) == 20
    assert train_df["date"].max() < test_df["date"].min()
    assert train_df["value"].max() < test_df["value"].min()


def test_random_train_test_split_disruption() -> None:
    """Xác nhận rằng random split phá vỡ tính tuần tự thời gian và trộn lẫn quan sát tương lai vào train."""
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    df = pd.DataFrame({"date": dates, "value": np.arange(100)})
    
    train_df, test_df = random_train_test_split(df, test_ratio=0.2, random_state=42)
    assert len(train_df) == 80
    assert len(test_df) == 20
    # Trong random split, train max sẽ lớn hơn test min vì bị trộn lẫn tương lai
    assert train_df["date"].max() >= test_df["date"].min()
