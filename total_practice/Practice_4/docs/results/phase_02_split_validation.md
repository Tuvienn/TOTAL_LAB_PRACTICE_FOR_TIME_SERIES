# Phase 2 — Temporal Split và Validation Design

## Mục tiêu

Khóa chronological split và giữ test set tách biệt trước khi lựa chọn mô hình.

## Kết quả chính

| Tập | Số dòng | Tỷ lệ |
|---|---:|---:|
| Train | 24.544 | 70% |
| Validation | 5.260 | 15% |
| Test | 5.260 | 15% |

Dữ liệu được chia theo thứ tự thời gian, không shuffle. Validation dùng cho
model selection và early stopping; Test chỉ dùng ở đánh giá cuối.

## Evidence

- <a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">Notebook</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>
- <a href="../status/current_status.md" style="color:#1f6feb;">Current status</a>

## Trạng thái

`Đã chạy`.
