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
| `XGB_4var` | 3,756.09 | 5,889.87 | 1.8802 |
| `VAR` | 4,183.93 | 6,259.22 | 2.0989 |
| `LSTM_best` | 4,557.90 | 6,433.83 | 2.4024 |
| `seasonal24` | 7,716.33 | 13,502.14 | 3.8434 |
| `seasonal168` | 12,247.95 | 19,011.91 | 5.5608 |
| `persistence` | 16,345.12 | 25,507.75 | 8.7756 |

Best model on held-out test: **`XGB_best`** (MAE `3,564.37`, RMSE `5,499.38 kW`, MAPE `1.7776%`).

## 3. Answers to the 6 Assignment Questions (Evidence-Backed)

### Q1. Biến thời tiết nào liên hệ mạnh nhất với điện năng?
- Train Pearson / Spearman correlation với `load`: `temp` (`r=0.6767`, `ρ=0.6018`), `humidity` (`r=-0.6404`, `ρ=-0.6016`), `wind_speed` (`r=0.1113`, `ρ=0.1202`).
- SHAP Group Attribution trên `XGB_full`: `temperature_lags` = `1,702.7`, `humidity_lags` = `739.9`, `wind_speed_lags` = `324.7`, `cross_interactions` = `2,700.7` (kW). Lưu ý đây là liên hệ dự báo, không chứng minh nhân quả.

### Q2. Khi nào VAR thất bại?
- Sau khi sửa flaw v1 (sai phân `d=1` theo Slide 5 và train 100% tập train `18,411` giờ), `VAR(24)` đạt ổn định (`max |λ|=0.9998 < 1`) nhưng vẫn kém ML/DL vì giả định tuyến tính không nắm được tương tác phi tuyến nhiệt độ–tải, hiệu ứng ngày lễ (`is_holiday`) và biến động mạnh lúc chuyển pha giờ cao điểm.

### Q3. XGBoost học được thông tin gì từ thời tiết và feature engineering?
- Ablation trên Validation: `XGB_load_only` RMSE `4,577.17` → `XGB_load_calendar` `4,463.62` → `XGB_full` `4,358.22` (kW); `XGB_load_weather` (4 biến thuần) đạt `4,514.44`.
- SHAP xác nhận lịch sử phụ tải ngắn/tuần và đặc trưng lịch (`calendar_dst_holiday`) đóng góp lớn nhất, trong khi `hdd_proxy`/`cdd_proxy` và nhiệt độ tinh chỉnh phản ứng phi tuyến theo mùa.

### Q4. LSTM thể hiện chu kỳ ngày/tuần như thế nào?
- Thực nghiệm đối chứng trực tiếp trên RTX 5050 giải quyết dứt điểm hạn chế v1: `LSTM_24h_core` (24h thuần 4 biến) đạt Val RMSE `5,928.51 kW` vs `LSTM_24h_cal` (thêm kênh lịch) `5,903.38 kW` vs `LSTM_168h_diag` (cửa sổ 168h = 1 tuần) `6,444.57 kW`. Điều này chứng minh nhận định ở Slide 10 (`chapter4-5.pdf`): LSTM xử lý tốt chu kỳ ngắn/ngày 24h nhưng suy giảm trên chuỗi rất dài 168 bước.
- Residual ACF trên Test: `LSTM_best` vẫn còn tự tương quan ở lag-24 (`0.4965`) và lag-168 (`0.4505`), trong khi `XGB_best` khử gần như triệt để (`-0.0357` và `0.0708`).

### Q5. LSTM có bị overfitting không?
- Trên validation, `LSTM_24h_cal` chọn thử nghiệm `lr1e3_d00` (`dropout=0.0`, `weight_decay=0.0`) với `ReduceLROnPlateau` và `EarlyStopping` (`patience=10`, dừng ở epoch `29`, khôi phục best epoch `19`, Train MSE scaled = `0.005131` vs Val MSE scaled = `0.005427`).
- Tuy nhiên khi đánh giá trên Test, `LSTM_24h_cal` (`6,433.83 kW`) tổng quát hóa kém hơn `LSTM_core` (`5,872.02 kW`), cho thấy việc mở rộng từ 4 lên 13 kênh mà không có `dropout` đã dẫn tới hiện tượng quá khớp nhẹ vào giai đoạn validation (và biến động giữa các seed: `6,025.87 ± 174.77 kW`).

### Q6. Machine Learning (XGBoost) và Deep Learning (LSTM) khác nhau thế nào?
- Khi dùng đúng 4 biến thô (`XGB_4var` vs `LSTM_core`), hai mô hình cho kết quả tương đương về mặt thống kê (`5,889.87` vs `5,872.02 kW`, DM `p = 0.8986`). Tuy nhiên khi bổ sung đầy đủ đặc trưng bảng (lags tuần `lag47`/`lag167`, calendar/DST/holiday, và tương tác phi tuyến `load_per_temp_k`, `hdd_proxy`/`cdd_proxy`), `XGB_full` vươn lên dẫn đầu vượt trội (`5,499.38 kW`, DM `p = 1.79e-10`), giải thích minh bạch qua SHAP và train chỉ mất `3.41s` trên RTX 5050.

## 4. Giới hạn và Rủi ro còn lại

- **Proxy thời tiết tái phân tích:** ERA5 đại diện cho 3 đô thị lớn của Bồ Đào Nha (Lisbon/Porto/Coimbra) theo trọng số `0.50/0.35/0.15`, không phải cảm biến đặt tại từng khách hàng trong 321 hộ/cơ sở của UCI.
- **Lệch mùa giữa các phân vùng đơn lẻ:** Test (`2014-07` → `2014-12`) phủ Hè–Thu–đầu Đông, trong khi Validation (`2014-02` → `2014-07`) phủ cuối Đông–Xuân–đầu Hè; vì vậy không dùng Test để tuning lại sau khi khóa cấu hình.
- **Giả định vận hành 1-step:** Giao thức `predict → score → reveal` giả định giá trị phụ tải thực tế của giờ vừa kết thúc sẵn sàng ngay để dự báo giờ tiếp theo.
