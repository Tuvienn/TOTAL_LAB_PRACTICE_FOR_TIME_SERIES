# Practice 4 (v2) — Final Report

## 1. Objective, Official Dataset & GPU Pipeline

- **Dataset:** `UCI ElectricityLoadDiagrams20112014 + Open-Meteo ERA5 Portugal` — 3 full calendar years (`2012-01-01` → `2014-12-31` UTC, `26,304` hourly steps, stable active-client cohort, DST-adjusted, paired with clean population-weighted ERA5 weather for Lisbon/Porto/Coimbra).
- **Hardware Acceleration:** XGBoost 3.4.1 CUDA + PyTorch 2.14.1+cu130 LSTM executed natively on **NVIDIA GeForce RTX 5050**.
- **Leakage Control:** Chronological `70/15/15` split + 3-fold expanding-window CV inside train; train-only EDA and scaler; locked `predict → score → reveal` test walk-forward.

## 2. Official Test Leaderboard

| Model | MAE (kW) | RMSE (kW) | MAPE (%) |
|---|---:|---:|---:|
| `XGB_best` | 3,564.37 | 5,499.38 | 1.7776 |
| `LSTM_core` | 4,156.48 | 5,872.02 | 2.1322 |
| `LSTM_best` | 4,301.28 | 6,191.98 | 2.1765 |
| `VAR` | 4,183.93 | 6,259.22 | 2.0989 |
| `XGB_4var` | 4,129.84 | 6,328.82 | 2.0922 |
| `seasonal24` | 7,716.33 | 13,502.14 | 3.8434 |
| `seasonal168` | 12,247.95 | 19,011.91 | 5.5608 |
| `persistence` | 16,345.12 | 25,507.75 | 8.7756 |

Best model on held-out test: **`XGB_best`** (MAE `3,564.37`, RMSE `5,499.38 kW`, MAPE `1.7776%`).

## 3. Answers to the 6 Assignment Questions (Evidence-Backed)

### Q1. Biến thời tiết nào liên hệ mạnh nhất với điện năng?
- Train Pearson / Spearman correlation với `load`: `temp` (`r=0.6767`, `ρ=0.6018`), `humidity` (`r=-0.6404`, `ρ=-0.6016`), `wind_speed` (`r=0.1113`, `ρ=0.1202`).
- SHAP Group Attribution trên `XGB_full`: `temperature_lags` = `1,702.7`, `humidity_lags` = `739.9`, `wind_speed_lags` = `324.7`, `cross_interactions` = `2,700.7` (kW). Lưu ý đây là liên hệ dự báo, không chứng minh nhân quả.

### Q2. Khi nào VAR thất bại?
- Sau khi áp dụng sai phân `d=1` theo Slide 5 (`chapter4-5.pdf`) và train 100% tập train (`18,411` giờ), `VAR(24)` đạt ổn định (`max |λ|=0.9998 < 1`, Test RMSE `6,259.22 kW`) nhưng vẫn kém `XGB_best` (`5,499.38 kW`, DM `p = 1.837e-10`) vì giả định tuyến tính không nắm được tương tác phi tuyến nhiệt độ–tải, hiệu ứng ngày lễ (`is_holiday`) và biến động mạnh lúc chuyển pha giờ cao điểm.

### Q3. XGBoost học được thông tin gì từ thời tiết và feature engineering?
- Ablation lồng nhau chặt trên Validation (kW): `XGB_24h_4var` (thuần 24h) `5,122.91` → `XGB_load_only` (thêm lag 48h/168h) `4,577.17` → `XGB_load_weather` (+72 lags thời tiết) `4,513.26` → `XGB_load_calendar` (+9 lịch `t+1`) `4,463.62` → **`XGB_full` (+6 tương tác chéo) `4,358.22`**.
- SHAP xác nhận lịch sử phụ tải ngắn/tuần (`lag23_load`, `lag167_load`, `lag47_load`) đóng góp nền tảng, trong khi `load_per_temp_k`, `lag00_temperature`, `temp_diff_24h` và `target_hour_cos` tinh chỉnh phản ứng phi tuyến theo mùa và giờ trong ngày.

### Q4. LSTM thể hiện chu kỳ ngày/tuần như thế nào?
- Khi cấp ngân sách tuning công bằng (4 cấu hình cho mỗi biến thể) và nối đặc trưng lịch tất định tại `t+1` vào tầng cuối (`future_cal_dim=9`), kết quả Validation (kW) là: `LSTM_24h_load_only` `5,986.57` | `LSTM_24h_core` `5,928.51` | `LSTM_24h_cal` `6,054.99` | `LSTM_168h_diag` `5,891.69` (biến thể thắng Validation: **`LSTM_168h_diag`**).
- Residual ACF trên Test: `LSTM_best` (`LSTM_168h_diag`) có ACF lag-24 = `0.4589` và lag-168 = `0.3832` (so với `LSTM_core`: `0.3703` / `0.3753`), trong khi `XGB_best` khử gần như triệt để (`-0.0357` và `0.0708`).

### Q5. LSTM có bị overfitting không?
- Trên Validation, `LSTM_168h_diag` chọn cấu hình `lr1e3_d00` (`dropout=0.0`, `weight_decay=0.0`) với `ReduceLROnPlateau` và `EarlyStopping` (`patience=10`, dừng ở epoch `37`, khôi phục best epoch `27`, Train MSE scaled = `0.004058` vs Val MSE scaled = `0.005405`).
- Tuy nhiên khi đánh giá trên Test, `LSTM_168h_diag` (`6,191.98 kW`) tổng quát hóa kém hơn `LSTM_core` (`5,872.02 kW`), cho thấy việc mở rộng lên 13 kênh chuỗi + 9 kênh lịch đích với `dropout=0.0` đã dẫn tới quá khớp nhẹ vào giai đoạn validation (kèm biến động giữa các seed: `6,027.62 ± 144.62 kW`).

### Q6. Machine Learning (XGBoost) và Deep Learning (LSTM) khác nhau thế nào?
- Khi giới hạn công bằng trong đúng cửa sổ 24h thuần 4 biến (`XGB_24h_4var` vs `LSTM_core`, không dùng lag tuần hay lịch), `LSTM_core` nhỉnh hơn có ý nghĩa thống kê (`6,328.82` vs `5,872.02 kW`, DM `p = 0.001167`).
- Khi mở khóa đầy đủ đặc trưng bảng (lags tuần `lag47`/`lag167`, lịch/DST/ngày lễ `t+1`, tương tác phi tuyến `load_per_temp_k`, `hdd_proxy`/`cdd_proxy`), `XGB_best` (`5,499.38 kW`) vượt trội `LSTM_best` (`6,191.98 kW`, DM stat = `-4.9617`, `p = 6.988e-07`), giải thích minh bạch bằng SHAP và chỉ tốn `3.38s` huấn luyện trên RTX 5050.

## 4. Giới hạn và Rủi ro còn lại

- **Proxy thời tiết tái phân tích:** ERA5 đại diện cho 3 đô thị lớn của Bồ Đào Nha (Lisbon/Porto/Coimbra) theo trọng số `0.50/0.35/0.15`, không phải cảm biến đặt tại từng khách hàng trong 321 hộ/cơ sở của UCI.
- **Lệch mùa giữa các phân vùng đơn lẻ:** Test (`2014-07` → `2014-12`) phủ Hè–Thu–đầu Đông, trong khi Validation (`2014-02` → `2014-07`) phủ cuối Đông–Xuân–đầu Hè; vì vậy không dùng Test để tuning lại sau khi khóa cấu hình.
- **Giả định vận hành 1-step:** Giao thức `predict → score → reveal` giả định giá trị phụ tải thực tế của giờ vừa kết thúc sẵn sàng ngay để dự báo giờ tiếp theo.
