import numpy as np
import pandas as pd

from presentation_24_10_2026.preprocessing.scaling import (
    scale_with_leakage,
    scale_without_leakage,
)


def test_correct_scaling_isolation() -> None:
    """Xác nhận rằng mean/std của scaler ở Pipeline B chỉ được tính từ tập train, không phụ thuộc tập test."""
    train_df = pd.DataFrame({"val": [10.0, 20.0, 30.0]})
    # Test set với giá trị cực kỳ khác biệt
    test_df_1 = pd.DataFrame({"val": [100.0, 200.0]})
    test_df_2 = pd.DataFrame({"val": [1000.0, 2000.0]})

    _, _, scaler_1 = scale_without_leakage(train_df, test_df_1, ["val"])
    _, _, scaler_2 = scale_without_leakage(train_df, test_df_2, ["val"])

    # Ở Pipeline B, scaler không bị ảnh hưởng bởi test_df
    assert np.isclose(scaler_1.mean_[0], 20.0)
    assert np.isclose(scaler_2.mean_[0], 20.0)
    assert np.isclose(scaler_1.mean_[0], scaler_2.mean_[0])


def test_leakage_scaling_contamination() -> None:
    """Xác nhận rằng ở Pipeline A, các giá trị ngoại lệ hoặc phân phối tương lai của test đã làm méo mó scaler train."""
    train_df = pd.DataFrame({"val": [10.0, 20.0, 30.0]})
    test_df_1 = pd.DataFrame({"val": [100.0, 200.0]})
    test_df_2 = pd.DataFrame({"val": [1000.0, 2000.0]})

    _, _, scaler_leak_1 = scale_with_leakage(train_df, test_df_1, ["val"])
    _, _, scaler_leak_2 = scale_with_leakage(train_df, test_df_2, ["val"])

    # Ở Pipeline A, mean bị kéo lệch dữ dội do test set
    assert not np.isclose(scaler_leak_1.mean_[0], 20.0)
    assert not np.isclose(scaler_leak_1.mean_[0], scaler_leak_2.mean_[0])
