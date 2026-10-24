# E1 PLAN — DATA UNDERSTANDING

## 1. Mục tiêu
Khảo sát toàn diện dataset trước khi thực hiện tiền xử lý hay mô hình hóa.

## 2. Các thông số cần xác định
- Dataset size (số dòng, số cột).
- Cột Timestamp và kiểu dữ liệu thời gian.
- Cột Target (biến cần dự báo).
- Tần suất quan sát (Frequency, ví dụ: hàng tháng, hàng ngày, hàng giờ).
- Khoảng thời gian (Date range: ngày bắt đầu, ngày kết thúc).
- Dữ liệu bị khuyết (Missing values) và khoảng trống thời gian (Missing timestamps).
- Dữ liệu trùng lặp thời gian (Duplicate timestamps).
- Tính tuần tự tăng dần (Chronological order).
- Đặc tính xu hướng (Trend) và mùa vụ (Seasonality) sơ bộ.

## 3. Output mong đợi
- `dataset_summary.csv` hoặc bảng Markdown mô tả dataset.
- `data_quality_report.csv`: Báo cáo chi tiết về missing values, tính liên tục.
- `01_time_series_overview.png`: Biểu đồ trực quan hóa chuỗi thời gian.
- Nhận xét và đánh giá sơ bộ về tính phù hợp của dữ liệu cho bài toán đánh giá mô hình.
