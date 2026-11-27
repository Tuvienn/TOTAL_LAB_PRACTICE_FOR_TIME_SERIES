# Phase 10 — Results và Final Report

## Kết luận mô hình

Trong lần chạy hiện tại, XGBoost đứng đầu trên Test với RMSE `3664.4820`, MAE
`2935.2076` và MAPE `9.9482%`. VAR và LSTM lần lượt có Test RMSE `4614.2743`
và `4855.8257`. Các metrics được tính trên thang đo `load` ban đầu bằng protocol
recursive walk-forward one-step-ahead.

## Trả lời sáu câu hỏi phân tích

### 1. Biến thời tiết nào ảnh hưởng mạnh nhất đến điện năng?

Nhiệt độ có liên hệ mạnh nhất với `load`: Pearson correlation `0.214`, so với
độ ẩm `-0.195` và tốc độ gió `0.094`. Tổng feature importance của các lag nhiệt
độ trong XGBoost cũng cao nhất trong ba nhóm thời tiết. Đây là bằng chứng về liên
hệ thống kê, không phải kết luận nhân quả; `load_lag_1` vẫn là tín hiệu chính.

### 2. Khi nào VAR thất bại?

VAR kém hiệu quả khi dự báo recursive trên quan hệ phi tuyến và sai số tích lũy.
Trên Test, VAR có RMSE `4614.27`, MAE `3952.87`, MAPE `13.94%`, kém XGBoost với
RMSE `3664.48` và MAPE `9.95%`. Mô hình tuyến tính khó mô tả đủ tương tác giữa
điện năng và thời tiết.

### 3. XGBoost học được thông tin gì từ thời tiết?

XGBoost dùng các lag nhiệt độ, độ ẩm và tốc độ gió để điều chỉnh dự báo load ở
giờ kế tiếp. Tuy nhiên, các lag của `load` chiếm phần lớn feature importance, nên
weather là thông tin bối cảnh còn temporal continuity của load là tín hiệu chính.

### 4. LSTM học được chu kỳ ngày hay tuần?

LSTM dùng cửa sổ `24 giờ`, nên có cơ sở để học intraday cycle. Notebook không
dùng cửa sổ `168 giờ` và không đưa trực tiếp biến thứ trong tuần vào đầu vào; do
đó chưa đủ bằng chứng để kết luận mô hình đã học weekly cycle.

### 5. LSTM có bị overfitting không?

Có dấu hiệu overfitting: training loss giảm từ `0.4195` xuống `0.0163`, trong
khi validation loss tốt nhất ở epoch `7` với `0.5619` rồi tăng trở lại. Early
stopping dừng ở epoch `13`; Test RMSE `4855.83` cũng cao hơn Validation RMSE
`3400.40`.

### 6. Khác biệt giữa Machine Learning và Deep Learning trong bài này?

XGBoost dùng lag và rolling features được tạo trước, học quan hệ phi tuyến bằng
cây quyết định và có thể diễn giải qua feature importance. LSTM nhận sequence
`24 × 4`, tự học temporal representation, nhiều tham số hơn và cần early
stopping. Trong lần chạy hiện tại, XGBoost tổng quát hóa tốt hơn trên Test; LSTM
có thể học pattern tuần tự nhưng nhạy hơn với overfitting và thiết kế cửa sổ.

## Evidence

- <a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">Notebook chính</a>
- <a href="phase_09_evaluation.md" style="color:#1f6feb;">Phase 9 — Walk-forward Evaluation</a>
- <a href="../../results/model_evaluation.csv" style="color:#1f6feb;">Model evaluation CSV</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>
