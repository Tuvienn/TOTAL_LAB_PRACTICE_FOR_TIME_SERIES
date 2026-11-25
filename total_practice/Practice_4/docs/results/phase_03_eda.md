# Phase 3 — Training-only Exploratory Data Analysis

## Mục tiêu

Kiểm tra chất lượng, phân phối, outlier, trend, seasonality và quan hệ giữa
`load` với các biến thời tiết mà không dùng Validation/Test để ra quyết định.

## Kết quả chính

- EDA được thực hiện trên `train_df`.
- Train có 24.544 quan sát và bước thời gian 1 giờ.
- Train có 32 missing `load` targets và không có duplicate timestamps. Các missing target được ghi nhận, không dùng giá trị tương lai để nội suy.
- Notebook hiển thị thống kê mô tả, kiểm tra outlier, pattern theo giờ/ngày trong
  tuần/tháng và tương quan giữa các biến.

Các biểu đồ hiện được lưu trong output của notebook; chưa có bộ ảnh phase riêng
được export trong lần chạy này.

## Evidence

- <a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">Notebook</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>

## Trạng thái

`Đã chạy`.
