# E05 — ARIMA, diagnostics và forecast

## Kết quả holdout

Các model được fit trên log training levels với `d=1`, sau đó forecast 41 tháng
và inverse-log về original sales scale.

| Model | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| ARIMA(1,1,1) | 3.833 | 4.866 | 18.494% |
| ARIMA(1,1,0) | 3.567 | 4.214 | 20.066% |
| ARIMA(0,1,1) | 3.466 | 4.177 | 18.170% |
| Seasonal naive (s=12) | 4.256 | 5.186 | 20.097% |

Trong lần chạy này, `ARIMA(0,1,1)` tốt hơn seasonal-naive baseline trên cả MAE,
RMSE và MAPE.

## Điểm cần chú ý

Ljung–Box vẫn bác bỏ white-noise null ở lag 12 và 24 cho các candidates. Vì vậy
không được kết luận residual hoàn toàn là white noise. Kết quả hiện là
reconciliation evidence, chưa phải formal model selection.

## Trạng thái

`Đã phê duyệt và kiểm tra`, với giới hạn residual-autocorrelation được ghi nhận.

## Evidence

- [Execution evidence E05](../logs/exercise_05_execution.md)
- [Forecast comparison](../../outputs/figures/05_forecast_comparison_log_d1.png)
- [Residual diagnostics](../../outputs/figures/05_residual_diagnostics_log_d1.png)
- [Model summary](../../outputs/results/Model_Summary_Prac2_Exercise.txt)
- [Run log](../../runs/2026-11-25_core_arima_two_candidates_v2/Practice_2_Exercise.log)
