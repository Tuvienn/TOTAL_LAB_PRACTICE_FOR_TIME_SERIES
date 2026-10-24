# E4 PLAN — BASELINE VS FORECASTING MODEL

## 1. Mục tiêu
Xây dựng ít nhất một mốc tham chiếu (Baseline) hợp lý và so sánh với mô hình dự báo chính nhằm xác thực mô hình máy học có thực sự học được quy luật có ích hay không.

## 2. Thiết lập thực nghiệm
- **Baseline Models**:
  - `Naive Forecast`: Lấy giá trị quan sát cuối cùng của tập train ($\hat{y}_{t+h} = y_t$).
  - `Seasonal Naive Forecast`: Lấy giá trị tương ứng của chu kỳ mùa vụ trước ($\hat{y}_{t+h} = y_{t+h-m}$, ví dụ $m=12$ cho dữ liệu tháng).
- **Forecasting Model**: Chọn 1 mô hình dự báo chính (ví dụ: Linear Regression / Ridge hoặc RandomForest với các đặc trưng trễ lag-safe).
- Cả Baseline và Mô hình chính phải được đánh giá trên cùng tập test và tính toán cùng tập chỉ số (MAE, RMSE, MAPE).

## 3. Output mong đợi
- Bảng tổng hợp kết quả Baseline: `baseline_results.csv`.
- Bảng tổng hợp kết quả Mô hình chính: `model_results.csv`.
- `04_baseline_vs_model.png`: Biểu đồ đường so sánh Actual vs Baseline vs Model Forecast.
- `baseline_vs_model_metrics.csv`: Bảng đối chiếu các chỉ số giữa Baseline và Model.
- Nhận xét và kết luận: Mô hình chính có vượt qua baseline hay không? Nếu không, lý giải nguyên nhân.
