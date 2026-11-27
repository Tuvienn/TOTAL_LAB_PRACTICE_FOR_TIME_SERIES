# E06 — SARIMA trên AirPassengers

## Trạng thái

`Đã xác nhận bằng clean-kernel execution — run 2026-11-27_e06_113951`.

Notebook E06 giữ bố cục cũ và được điều chỉnh trực tiếp để có input validation,
training-only differencing, ACF/PACF, ARIMA baseline, SARIMA, residual diagnostics
và 29-month holdout evaluation. E06 là advanced extension độc lập, không thay đổi
trạng thái completed của core E01–E05.

## Nội dung hiện có

- Dataset: `datasets/raw/airline-passengers.csv`.
- Chronological split: 115 train và 29 test observations.
- Seasonal period: `s=12`.
- Notebook: <a href="../../notebooks/Practice_2_Advanced.ipynb" style="color:#1f6feb;">Practice_2_Advanced.ipynb</a>.
- Runtime log chính thức: `runs/2026-11-27_e06_113951/Practice_2_Advanced.log`.
- Machine-readable outputs của run chính thức:
  - `outputs/results/06_airpassengers_validation.csv`
  - `outputs/results/06_airpassengers_split.csv`
  - `outputs/results/06_airpassengers_adf_results.csv`
  - `outputs/results/06_airpassengers_model_candidates.csv`
  - `outputs/results/06_airpassengers_model_diagnostics.csv`
  - `outputs/results/06_airpassengers_forecasts.csv`
  - `outputs/results/06_airpassengers_metrics.csv`
- Figures của run chính thức:
  - `outputs/figures/06_airpassengers_original_series.png`
  - `outputs/figures/06_airpassengers_differencing.png`
  - `outputs/figures/06_airpassengers_acf_pacf.png`
  - `outputs/figures/06_airpassengers_residual_diagnostics.png`
  - `outputs/figures/06_airpassengers_forecast_arima.png`
  - `outputs/figures/06_airpassengers_forecast_sarima.png`
  - `outputs/figures/06_airpassengers_forecast_comparison.png`

## Kết quả và điểm cần chú ý

- Forecast được đánh giá trên đúng 29 tháng test, không dùng test set để fit.
- ARIMA(0,1,1): MAE `88.420620`, RMSE `101.104982`.
- SARIMA(0,1,1)(0,1,1,12): MAE `24.059215`, RMSE `30.580049`.
- Ljung–Box của SARIMA tại lag 12 và 24 lần lượt có p-value `0.1205` và
  `0.3304`, nên không bác bỏ giả thuyết không có tự tương quan ở các lag đã chọn.
- Chi tiết execution và artifact được ghi trong
  [`docs/logs/exercise_06_execution.md`](../logs/exercise_06_execution.md).

Không dùng các output exploratory cũ làm evidence cho workflow đã điều chỉnh.
