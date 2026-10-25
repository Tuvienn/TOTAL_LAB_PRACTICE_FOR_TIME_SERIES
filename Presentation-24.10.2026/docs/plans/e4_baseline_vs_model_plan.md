# E4 PLAN — BASELINE VS FORECASTING MODEL

## 1. Trạng thái thực hiện
- **Trạng thái**: `[COMPLETED]`
- **Thời điểm hoàn thành**: 2026-10-25
- **Mô hình đối sánh**:
  - Baseline 1: `Naive Forecaster` ($\hat{y}_{t+h} = y_t$).
  - Baseline 2: `Seasonal Naive Forecaster` ($m=12, \hat{y}_{t+h} = y_{t+h-12}$).
  - Model chính: `Ridge Regression` (Recursive Multi-step Forecasting với 12 lags).

## 2. Mục tiêu
Xây dựng ít nhất một mốc tham chiếu (Baseline) hợp lý và so sánh với mô hình dự báo chính nhằm xác thực mô hình máy học có thực sự học được quy luật có ích hay không.

## 3. Thiết lập thực nghiệm
- Đánh giá trên cùng tập Test (24 tháng cuối của chuỗi dữ liệu AirPassengers).
- Bắt buộc tính toán 3 chỉ số chuẩn: MAE, RMSE, MAPE và tỷ lệ cải thiện tương đối (Relative Improvement).

## 4. Kết quả thực nghiệm đối chứng
Bảng trích xuất thực tế từ `baseline_vs_model_metrics.csv`:

| Mô hình | MAE | RMSE | MAPE (%) | Độ cải thiện so với Naive | Đánh giá |
|---|:---:|:---:|:---:|:---:|---|
| **1. Naive Forecast** (Mốc cơ bản) | 76.00 | 102.98 | 14.25% | 0.0% | Bị trễ pha nặng nề, hoàn toàn bỏ lỡ tính mùa vụ |
| **2. Seasonal Naive** ($m=12$) | 47.83 | 50.71 | 9.99% | +37.1% | Tốt hơn Naive rõ rệt nhờ nắm bắt chu kỳ 1 năm |
| **3. Ridge Regression** (Recursive) | **14.72** | **17.49** | **3.13%** | **+80.6%** | Vượt bậc (+69.2% so với Seasonal Naive), học được cả trend và seasonality |

## 5. Output bàn giao thực tế
- [x] `baseline_vs_model_metrics.csv`: Bảng số liệu chi tiết đối chiếu các chỉ số giữa 2 baseline và mô hình chính.
- [x] `04_baseline_vs_model.png` (Visual 4): Đồ thị đường đối sánh Actual Test Ground Truth vs Naive vs Seasonal Naive vs Forecaster.
- [x] **Kết luận E4**: Mô hình máy học chính vượt qua cả 2 baseline với mức cải thiện ấn tượng (+80.6% so với Naive, +69.2% so với Seasonal Naive), chứng minh giá trị thực tế của thuật toán có học.

