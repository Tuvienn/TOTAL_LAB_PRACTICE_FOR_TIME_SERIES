# Phase 1 — Data Preparation

## Mục tiêu

Đọc canonical processed dataset, kiểm tra schema, timestamp, tần suất và chất
lượng dữ liệu trước khi phân tích.

## Kết quả chính

- 35.064 dòng và 5 cột.
- Khoảng thời gian: 2014-12-31 23:00 UTC → 2018-12-31 22:00 UTC.
- Tần suất hourly.
- Có 36 missing `load` targets; weather inputs không missing. Duplicate timestamps và interval bất thường bằng 0.
- Missing target được giữ nguyên trong canonical dataset; không nội suy hai phía.
- Các cột: `time`, `load`, `temperature`, `humidity`, `wind_speed`.

## Evidence

- <a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">Notebook</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>
- <a href="../status/current_status.md" style="color:#1f6feb;">Dataset provenance</a>

## Trạng thái

`Đã chạy`.
