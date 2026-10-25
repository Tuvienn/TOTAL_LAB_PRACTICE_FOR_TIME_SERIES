# E1 PLAN — DATA UNDERSTANDING

## 1. Trạng thái thực hiện
- **Trạng thái**: `[COMPLETED]`
- **Thời điểm hoàn thành**: 2026-10-25
- **Dataset thực tế**: `AirPassengers` (`datasets/raw/air_passengers.csv`)

## 2. Mục tiêu
Khảo sát toàn diện dataset trước khi thực hiện tiền xử lý hay mô hình hóa.

## 3. Các thông số đã xác định qua thực nghiệm
- **Dataset size**: 144 dòng, 2 cột chính (`date`, `value` kèm alias `passengers_thousands`).
- **Timestamp & DatetimeIndex**: Kiểu ngày tháng năm chuẩn `pd.DatetimeIndex`, tần suất tháng đầu kỳ (`freq="MS"`).
- **Target variable**: `value` / `passengers_thousands` (đơn vị: nghìn hành khách quốc tế).
- **Date range**: Từ `1949-01-01` đến `1960-12-01` (tròn 12 năm lịch sử liên tục).
- **Missing values**: 0 giá trị bị khuyết, không có khoảng trống thời gian (missing timestamps = 0).
- **Duplicate timestamps**: False (không có bản ghi nào bị trùng lặp thời gian).
- **Chronological order**: `is_monotonic_increasing = True` (bảo toàn trật tự thời gian tuyệt đối).
- **Thống kê mô tả sơ bộ**:
  - Min: 104.0 nghìn hành khách (tháng 11/1949).
  - Max: 622.0 nghìn hành khách (tháng 07/1960).
  - Mean: 280.30, Median: 265.50, Std: 119.97, IQR: 180.0.
  - Outliers: 0 quan sát bất thường ngoài dải $1.5 \times \text{IQR}$.

## 4. Output bàn giao thực tế
- [x] `dataset_summary.csv`: Bảng tổng hợp các thông số định lượng cốt lõi của chuỗi thời gian.
- [x] `data_quality_report.csv`: Báo cáo chi tiết về chất lượng dữ liệu, kiểm tra tính liên tục và phân phối.
- [x] `01_time_series_overview.png` (Visual 1): Biểu đồ trực quan hóa chuỗi thời gian hàng tháng kèm đường Max (622), Min (104) và đường trung bình năm Annual Average (`figsize=(12, 5)`).
- [x] **Kết luận E1**: Dữ liệu đáp ứng hoàn hảo tính đơn điệu, liên tục và mùa vụ 12 tháng, đủ điều kiện để triển khai chia tách và mô hình hóa.

