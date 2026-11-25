# Phase 8 — LSTM

## Mục tiêu

Huấn luyện LSTM trên sequence 24 giờ, theo dõi Validation Loss và dừng sớm khi
mô hình không còn cải thiện.

## Kết quả chính

- Kiến trúc summary: `LSTM(64) → LSTM(32) → Dense(1)`.
- Thiết bị chạy: CPU.
- Validation Loss tốt nhất recursive: `0.561868` trên thang đo chuẩn hóa.
- Early stopping được kích hoạt sau khi Validation Loss không cải thiện.
- Test: RMSE `4855.8257`, MAE `3884.7037`, MAPE `13.3496%`.

## Artifact

- <a href="../../results/model_summaries/LSTM_summary.txt" style="color:#1f6feb;">LSTM summary</a>
- <a href="../../results/model_summaries/LSTM_training_history.csv" style="color:#1f6feb;">Training history</a>
- <a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">Notebook</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>

## Trạng thái

`Đã chạy`.
