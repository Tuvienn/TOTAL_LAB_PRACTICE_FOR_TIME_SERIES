# E6 PLAN — FORECAST HORIZON EVALUATION

## 1. Trạng thái thực hiện
- **Trạng thái**: `[COMPLETED]`
- **Thời điểm hoàn thành**: 2026-10-25
- **Phạm vi chân trời**: $h = 1, 2, \dots, 12$ tháng cuốn chiếu (Recursive Multi-step).

## 2. Mục tiêu
Đo lường và đánh giá chi tiết sự thay đổi của chất lượng dự báo khi khoảng cách dự báo thay đổi theo từng bước chân trời dự báo:
$$h = 1, 2, \dots, H$$
Kiểm chứng thực nghiệm xem sai số có tăng dần tuyến tính theo horizon hay không dựa trên số liệu thực tế qua các fold.

## 3. Thiết lập thực nghiệm
- Trích xuất ma trận giá trị thực tế và ma trận dự báo của mô hình qua 6 folds: shape $(6, 12)$.
- Tính toán MAE, RMSE, MAPE độc lập cho từng bước $h \in \{1, 2, \dots, 12\}$.
- So sánh sai số theo horizon của mô hình chính với Seasonal Naive baseline tại từng bước $h$.

## 4. Kết quả thực nghiệm đối chứng
Bảng trích xuất thực tế từ `error_by_horizon_table.csv`:

| Horizon ($h$) | MAE Model | RMSE Model | MAPE Model (%) | MAE Baseline | Độ cải thiện MAE | Đánh giá hành vi sai số |
|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **$h=1$** | **13.80** | 15.61 | 4.36% | 35.50 | **+61.1%** | Bước ngắn, mô hình nắm bắt rất tốt |
| **$h=2$** | 17.14 | 18.84 | 5.86% | 33.83 | +49.3% | Sai số bắt đầu tích lũy nhẹ |
| **$h=3$** | 21.23 | 23.88 | 6.45% | 30.67 | +30.8% | Tích tụ sai số cuốn chiếu |
| **$h=4$** | 25.98 | 28.50 | 7.35% | 39.00 | +33.4% | Đạt đỉnh sai số ngắn hạn |
| **$h=5$** | 18.58 | 22.79 | 5.22% | 39.67 | +53.2% | Sai số giảm do nhịp mùa vụ hồi quy |
| **$h=6$** | 19.49 | 23.29 | 4.83% | 45.17 | +56.9% | Duy trì độ chính xác cao |
| **$h=7$** | 20.69 | 24.84 | 4.52% | 53.33 | +61.2% | Vượt trội so với baseline |
| **$h=8$** | **12.83** | 15.92 | 3.01% | 52.17 | **+75.4%** | Điểm hội tụ chu kỳ tốt nhất |
| **$h=9$** | 21.77 | 30.07 | 5.46% | 41.50 | +47.5% | Biến động do tính mùa thu |
| **$h=10$** | 15.73 | 19.66 | 4.62% | 38.67 | +59.3% | Ổn định trở lại |
| **$h=11$** | 18.28 | 21.62 | 5.75% | 31.17 | +41.3% | Chuẩn bị chu kỳ mới |
| **$h=12$** | 22.56 | 26.57 | 6.64% | 33.83 | +33.3% | Kết thúc chu kỳ 1 năm |

## 5. Output bàn giao thực tế
- [x] `error_by_horizon_table.csv`: Bảng tổng hợp chi tiết sai số và độ cải thiện của từng bước $h=1..12$.
- [x] `07_error_by_forecast_horizon.png` (Visual 7): Biểu đồ biểu thị quan hệ giữa MAE/RMSE của mô hình và baseline theo bước $h$.
- [x] **Kết luận E6**: Sai số không tăng đơn điệu tuyến tính mà biến thiên theo chu kỳ sóng mùa vụ. Mô hình máy học duy trì ưu thế vượt trội (+33% đến +75% độ chính xác) so với baseline ở tất cả 12 bước chân trời dự báo.

