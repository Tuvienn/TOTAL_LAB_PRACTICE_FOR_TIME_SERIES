# Phase 5 — Feature Engineering

## Mục tiêu

Tạo đầu vào time-safe cho ba nhóm mô hình từ cửa sổ lịch sử 24 giờ.

## Kết quả chính

- LSTM dùng tensor cửa sổ `(samples, 24, 4)`; sau khi loại target thiếu: Train 24.488, Validation 5.258, Test 5.258 mẫu.
- XGBoost dùng 96 lag features (4 biến × 24 giờ) và 3 rolling features; sau khi loại target thiếu: Train 24.487, Validation 5.258, Test 5.258 mẫu.
- Target là `load` ở bước thời gian kế tiếp.
- Feature engineering giữ thứ tự thời gian và loại bỏ các hàng đầu tiên không đủ
  lịch sử.

## Evidence

- <a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">Notebook</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>
- <a href="../../results/model_summaries/XGBoost_tuning_results.csv" style="color:#1f6feb;">XGBoost tuning results</a>

## Trạng thái

`Đã chạy`.
