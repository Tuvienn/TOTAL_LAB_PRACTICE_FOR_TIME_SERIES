# Phase 4 — Preprocessing và Scaling

## Mục tiêu

Chuẩn hóa dữ liệu theo nguyên tắc không leakage và áp dụng cùng transformation
cho Validation/Test sau khi fit trên Train.

## Kết quả chính

- `StandardScaler` được fit trên Train.
- Validation sau preprocessing có 5.260 dòng và 4 biến số.
- Test sau preprocessing có 5.260 dòng và 4 biến số.
- Thứ tự thời gian được giữ nguyên giữa các tập.
- `load` input được forward-fill past-only; các target gốc bị thiếu không được dùng làm ground truth khi tính metrics.

## Evidence

- <a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">Notebook</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>

## Trạng thái

`Đã chạy`.
