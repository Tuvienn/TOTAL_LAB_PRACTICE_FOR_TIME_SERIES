# E6 PLAN — FORECAST HORIZON EVALUATION

## 1. Mục tiêu
Đo lường và đánh giá chi tiết sự thay đổi của chất lượng dự báo khi khoảng cách dự báo thay đổi theo từng bước chân trời dự báo:
$$h = 1, 2, \dots, H$$
Kiểm chứng thực nghiệm xem sai số có tăng dần theo horizon hay không mà không được giả định trước.

## 2. Thiết lập thực nghiệm
- Trích xuất ma trận dự báo thực tế và ma trận dự báo của mô hình qua các fold backtest:
  - Shape: $(N_{\text{folds}}, H)$
- Tính toán MAE, RMSE, MAPE độc lập cho từng bước $h \in \{1, 2, \dots, H\}$.
- So sánh sai số theo horizon của mô hình chính với baseline tương ứng tại từng bước $h$.

## 3. Output mong đợi
- `error_by_horizon_table.csv`: Bảng tổng hợp chi tiết sai số theo từng bước $h=1..H$.
- `07_error_by_forecast_horizon.png`: Biểu đồ biểu thị quan hệ giữa độ lớn sai số và khoảng cách dự báo $h$.
- Nhận xét và phân tích: Khoảng dự báo nào là đáng tin cậy nhất? Tại bước nào mô hình bắt đầu suy giảm hiệu năng rõ rệt?
