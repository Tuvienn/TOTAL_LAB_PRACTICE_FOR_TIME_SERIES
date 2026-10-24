# DATASETS SPECIFICATION — PRESENTATION-24.10.2026

## 1. Nguyên tắc quản lý dữ liệu

- **Raw Data bất biến**: Thư mục `datasets/raw/` chứa các tệp dữ liệu thô ban đầu, tuyệt đối không được ghi đè, sửa đổi, chỉnh sửa giá trị hay điền khuyết trực tiếp.
- **Derived Data**: Thư mục `datasets/processed/` chứa các tập dữ liệu đã qua tiền xử lý hợp lệ (ví dụ: các fold backtest, dữ liệu đã được căn chỉnh timestamp).
- **Yêu cầu Dataset cho Topic 5**:
  - Dữ liệu chuỗi thời gian thực tế (Real-world Time Series).
  - Có cột timestamp rõ ràng, tần suất xác định (ví dụ: ngày, tháng, giờ).
  - Có tính xu hướng (trend) hoặc mùa vụ (seasonality) để phục vụ so sánh trực quan giữa Naive, Seasonal Naive và mô hình có học.
  - Phù hợp để kiểm thử Scaling Leakage và Backtesting nhiều mốc.

## 2. Trạng thái hiện tại

- Giai đoạn: Tiền dự án (Pre-project phase).
- Chưa nạp dữ liệu chính thức, đang chờ Human phê duyệt lựa chọn dataset cụ thể (ví dụ: sử dụng tiếp chuỗi `AirPassengers` hoặc một dataset chuỗi thời gian kinh tế / năng lượng khác).
