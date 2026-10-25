import numpy as np

from presentation_24_10_2026.evaluation.metrics import (
    compute_all_metrics,
    compute_mae,
    compute_mape,
    compute_rmse,
)


def test_compute_mae_known_values() -> None:
    """Xác nhận MAE tính đúng trung bình sai số tuyệt đối trên tập dữ liệu mẫu chuẩn."""
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 17.0, 34.0])
    # |10-12|=2, |20-17|=3, |30-34|=4 -> (2+3+4)/3 = 3.0
    mae = compute_mae(y_true, y_pred)
    assert np.isclose(mae, 3.0)


def test_compute_rmse_penalty() -> None:
    """Xác nhận RMSE phản ánh đúng mức phạt bình phương sai số khi xuất hiện lỗi lớn."""
    # Case 1: Lỗi nhỏ đều [2, 3, 4] -> RMSE = sqrt((4+9+16)/3) = sqrt(29/3) ~ 3.109
    y1_true = np.array([10.0, 20.0, 30.0])
    y1_pred = np.array([12.0, 17.0, 34.0])
    rmse_1 = compute_rmse(y1_true, y1_pred)

    # Case 2: 1 lỗi lớn đột biến [1, 1, 10] (cùng MAE = 4)
    y2_true = np.array([10.0, 20.0, 30.0])
    y2_pred = np.array([11.0, 21.0, 40.0])
    rmse_2 = compute_rmse(y2_true, y2_pred)

    assert rmse_2 > rmse_1
    assert np.isclose(compute_mae(y2_true, y2_pred), 4.0)
    assert np.isclose(rmse_2, np.sqrt((1 + 1 + 100) / 3))


def test_compute_mape_stability() -> None:
    """Xác nhận hàm compute_mape xử lý an toàn, không sinh lỗi chia cho 0 khi giá trị thực tế bằng 0."""
    y_true = np.array([0.0, 10.0, 20.0])
    y_pred = np.array([1.0, 11.0, 22.0])
    mape = compute_mape(y_true, y_pred)
    assert not np.isnan(mape)
    assert not np.isinf(mape)
    assert mape > 0
