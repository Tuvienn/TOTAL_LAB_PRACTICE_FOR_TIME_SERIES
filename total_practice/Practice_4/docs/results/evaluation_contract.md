# Practice 4 (v2) — Evaluation & Anti-Leakage Contract

- **Cấu hình khóa v2:** `config/practice_4_v2.json`
- **Thực thi kiểm soát:** `src/practice_4/data/splitting.py`, `src/practice_4/analysis/h01_evaluation.py`, `src/practice_4/analysis/error_analysis.py`

## 1. Phân chia thời gian & Chống rò rỉ

- **Chronological split (không shuffle):** `70% Train` (`18,412` giờ) / `15% Validation` (`3,945` giờ) / `15% Test` (`3,947` giờ), kèm `3-fold Expanding-Window CV` nằm hoàn toàn trong Train.
- **Train-only fitting:** EDA, `StandardScaler`, ngưỡng phân vị ngoại lai (`P0.5/P99.5`) và tham số mô hình chỉ được ước lượng trên Train; Validation chỉ dùng cho chọn siêu tham số/biến thể và early stopping; Test bị khóa tuyệt đối cho đến Stage `S8`.
- **Cửa sổ bối cảnh nhân quả chung:** Mọi mô hình đánh giá trên cùng tập origin hợp lệ (`context_hours = 168`, `target_row = origin_row + 1`).

## 2. Giao thức đánh giá Test Walk-Forward (`predict → score → reveal`)

1. Tải toàn bộ trọng số mô hình đã khóa (`VAR`, `XGBoost`, `PyTorch LSTM`) cùng `scaler.json` và ghi nhận checksum `SHA256` trước vòng lặp.
2. Tại từng bước Test theo đúng thứ tự thời gian:
   - **Predict:** Phát dự báo $\hat{y}_{t+1}$ chỉ từ bộ đệm lịch sử $\le t$ và biến lịch tất định của $t+1$.
   - **Score:** Kiểm tra tính hữu hạn và đối chiếu với phụ tải quan sát thực tế $y_{t+1}$.
   - **Reveal:** Biến đổi nhân quả bản ghi thực tế $t+1$ (`transform_causal`) và đẩy vào bộ đệm cho bước tiếp theo. Không bao giờ dùng dự báo thay cho quan sát thực tế.
3. Kiểm tra lại `SHA256` trọng số sau vòng lặp để đảm bảo bất biến tuyệt đối (`0` refit trên Test) và kiểm tra bảo toàn số đếm:
   `n_considered = n_scored + n_missing_excluded + n_input_excluded`.

## 3. Thước đo & Kiểm định thống kê

- Tất cả thước đo tính trên **thang đo gốc (kW)** và trên **cùng tập điểm Test hợp lệ (`3,947` điểm)**:
  - **MAE (kW):** $\frac{1}{N}\sum |y_i - \hat{y}_i|$
  - **RMSE (kW):** $\sqrt{\frac{1}{N}\sum (y_i - \hat{y}_i)^2}$ (thước đo chính để chọn cấu hình trên Validation)
  - **MAPE (%):** $\frac{100}{N}\sum \left|\frac{y_i - \hat{y}_i}{y_i}\right|$ trên các điểm $y_i \neq 0$ (không dùng epsilon giả).
- **Kiểm định ý nghĩa thống kê:** Kiểm định **Diebold–Mariano** hai phía (squared-error loss, $h=1$) so sánh từng cặp mô hình chính trên Test, kèm phân tích tự tương quan phần dư (ACF lag-24, lag-168) và phân rã sai số theo giờ địa phương, thứ, tháng, mùa, ngày lễ và cờ DST.
