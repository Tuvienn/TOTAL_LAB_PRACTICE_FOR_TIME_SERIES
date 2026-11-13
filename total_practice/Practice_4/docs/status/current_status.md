# Current Status — Practice 4

Trạng thái dự án: `PLANNING`.

## Đã hoàn thành ở mức lập kế hoạch

- Đã đọc đề bài Practice 4 và các quy tắc repository áp dụng.
- Human đã chọn **Hourly energy demand, generation and weather** làm dataset chính.
- Human đã thống nhất kiến trúc tổng quan gồm Phase 0–10:
  - Phase 0: Problem Definition;
  - Phase 1: Data Preparation;
  - Phase 2: Temporal Split và Validation Design;
  - Phase 3: EDA chỉ trên training set;
  - Phase 4–9: preprocessing, feature engineering, modeling và final evaluation;
  - Phase 10: End-to-End Notebook và Final Report.
- Đã thực hiện preliminary read-only inspection đối với archive công khai:
  - `energy_dataset.csv`: 35.064 dòng, 29 cột, hourly 2015–2018;
  - `weather_features.csv`: 178.396 dòng, 17 cột, weather của năm thành phố;
  - `total load actual` có 36 giá trị thiếu;
  - ba trường `temp`, `humidity`, `wind_speed` không thiếu;
  - có các city-hour bị lặp do nhiều weather descriptions, nhưng ba trường weather
    bắt buộc giống nhau trong các bản lặp đã kiểm tra.
- Hai tài liệu tổng quan đã được cập nhật theo quyết định dataset và đang chờ Human review.

## Chưa thực hiện

- Chưa tải hoặc lưu dataset Spain vào repository.
- Chưa ghi checksum, provenance và bằng chứng kiểm tra có thể tái lập trong execution log.
- Chưa khóa data contract và data-preparation policy thuộc Phase 1.
- Chưa khóa split boundaries và validation protocol thuộc Phase 2.
- Chưa khóa missing-value treatment, scaling hoặc walk-forward protocol.
- Chưa thiết kế chi tiết hay triển khai Phase 0.
- Chưa viết code, notebook, test hoặc huấn luyện mô hình.

Dataset UCI `LD2011_2014.txt` hiện có trong `datasets/raw/` không phải dataset chính
của Practice 4 và được giữ nguyên như source evidence; chưa có quyết định xóa hoặc di chuyển.
