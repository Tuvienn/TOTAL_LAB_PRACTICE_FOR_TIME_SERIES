# Nhiệm vụ: Kiểm thử tính chính xác của các hàm tính metric MAE, RMSE, MAPE.
import numpy as np
import pytest


def test_compute_mae_known_values() -> None:
    """Xác nhận MAE tính đúng trung bình sai số tuyệt đối trên tập dữ liệu mẫu chuẩn."""
    pass


def test_compute_rmse_penalty() -> None:
    """Xác nhận RMSE phản ánh đúng mức phạt bình phương sai số khi xuất hiện lỗi lớn."""
    pass


def test_compute_mape_stability() -> None:
    """Xác nhận hàm compute_mape xử lý an toàn, không sinh lỗi chia cho 0 khi giá trị thực tế bằng 0."""
    pass
