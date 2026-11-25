# Phase 6 — VAR

## Mục tiêu

Kiểm tra tính dừng, chọn lag theo BIC, huấn luyện VAR và thực hiện walk-forward
forecasting trên Validation/Test.

## Kết quả chính

- ADF không đánh dấu biến nào cần sai phân trong lần chạy hiện tại.
- VAR lag order được chọn theo BIC: `26`.
- VAR tạo 5.260 dự báo Validation và 5.260 dự báo Test.

## Artifact

- <a href="../../results/model_summaries/VAR_summary.txt" style="color:#1f6feb;">VAR model summary</a>
- <a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">Notebook</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>

## Trạng thái

`Đã chạy`.
