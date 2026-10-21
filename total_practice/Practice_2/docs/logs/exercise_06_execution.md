# EXERCISE 06 — NHẬT KÝ BẰNG CHỨNG EXPLORATORY

## Trạng thái bản ghi

```text
record type: exploratory E06 record with validated residual-diagnostics remediation
execution source: clean-kernel execution of the dedicated advanced notebook
presentation notebook: notebooks/Practice_2_advanced_sarima.ipynb
execution date: 2026-10-20
E06 implementation authorization: residual-fix scope only
E06 residual-fix validation status: validated
E06 formal completion status: not applicable — exploratory only
```

File này ghi lại bằng chứng exploratory của E6 trên AirPassengers và residual-fix
đã được xác nhận. Theo Phương án A do Human lựa chọn, E6 không được formalize và
không chờ chuyển sang trạng thái `COMPLETED`.

## Phạm vi và thiết lập

```text
dataset: airline-passengers.csv (AirPassengers)
observations: 144 monthly values
period: 1949-01 through 1960-12
train: 115 observations, 1949-01 through 1958-07
test: 29 observations, 1958-08 through 1960-12
split: chronological 80/20; no shuffle
analysis scale: natural_log
seasonal period: s = 12
forecast metric scale: passenger counts
```

Chuỗi có level tăng, mùa vụ năm và seasonal amplitude tăng theo level. Phân tích
exploratory sử dụng natural-log scale.

## Bằng chứng ADF và differencing

ADF được chạy trên train ở log scale với `alpha=0.05`:

| Chuỗi train | Input observations | ADF statistic | p-value | Used lag | ADF observations | Quyết định |
|---|---:|---:|---:|---:|---:|---|
| Log series gốc | 115 | -1.574027 | 0.496626 | 13 | 101 | Không bác bỏ H0 |
| Regular difference, d=1 | 114 | -2.635851 | 0.085812 | 12 | 101 | Không bác bỏ H0 |
| Seasonal difference, D=1, s=12 | 103 | -1.991013 | 0.290527 | 12 | 90 | Không bác bỏ H0 |
| Kết hợp d=1 và D=1, s=12 | 102 | -3.946340 | 0.001719 | 11 | 90 | Bác bỏ H0 |

Trong các phép thử đã lưu, chỉ differencing kết hợp regular và seasonal bác bỏ H0
của ADF. Vì vậy lần chạy exploratory dùng `d=1`, `D=1`, `s=12`.

## ACF/PACF và order đã fit

| Diagnostic | Significant lag và correlation |
|---|---|
| ACF | 1: -0.320677; 3: -0.232934; 12: -0.429978 |
| PACF | 1: -0.320677; 3: -0.223399; 12: -0.383332; 23: 0.195020; 36: -0.195495 |

Tại seasonal reference lag, ACF lag 12 có ý nghĩa; lag 24 và 36 không có ý nghĩa.
PACF lag 12 và 36 có ý nghĩa trong bảng đã lưu; lag 24 không có ý nghĩa. Biểu đồ
không xác định một cutoff duy nhất, nên đây là candidate của lần chạy exploratory:

```text
ARIMA baseline: (1,1,1)
SARIMA: (1,1,1)(0,1,1,12)
```

## Kết quả fit và residual

Cả hai model hội tụ và không ghi nhận fitting warning:

| Model | Order | Seasonal order | AIC | BIC |
|---|---|---|---:|---:|
| ARIMA | (1,1,1) | — | -197.221464 | -189.012869 |
| SARIMA | (1,1,1) | (0,1,1,12) | -369.862481 | -359.362590 |

| Model | p-value lag 12 | p-value lag 24 | Diễn giải tại alpha 0.05 |
|---|---:|---:|---|
| ARIMA | 2.944816e-16 | 2.308263e-27 | Bác bỏ H0 không có autocorrelation tại cả hai lag |
| SARIMA | 0.573996 | 0.473545 | Không bác bỏ H0 tại cả hai lag |

Diagnostics sử dụng residual sau model-specific burn-in. ARIMA dùng burn-in `1`
với 114 residual observations; SARIMA dùng burn-in `13` với 102 observations.
Residual mean trên log scale là `0.011221` và `0.001164`. ARIMA còn autocorrelation
tại lag 12/24; SARIMA chưa phát hiện autocorrelation tại hai lag này, nhưng kết quả
không chứng minh white noise ở mọi lag.

## Đánh giá forecast

| Model | MAE | RMSE |
|---|---:|---:|
| ARIMA(1,1,1) | 84.254030 | 96.327159 |
| SARIMA(1,1,1)(0,1,1,12) | 12.164590 | 14.917399 |

| Model | Timestamp | Actual | Forecast | Absolute error |
|---|---|---:|---:|---:|
| ARIMA | 1958-11-01 | 310 | 496.107318 | 186.107318 |
| SARIMA | 1960-03-01 | 419 | 452.013766 | 33.013766 |

Trên holdout này, SARIMA có MAE và RMSE thấp hơn ARIMA. So sánh chỉ áp dụng cho
dataset, split và candidate đã lưu; residual conclusion chỉ áp dụng tại lag 12/24.

## Output và xác nhận

- `outputs/results/06_airpassengers_model_diagnostics.csv`
- `outputs/figures/06_airpassengers_residual_diagnostics.png`

```text
raw data contract/checksum: PASS
forecast/test index equality: PASS
targeted E05/E06 tests: 12 passed
full Practice 2 tests: 30 passed
clean-kernel advanced notebook execution: PASS
notebook error outputs: 0
dependency check: PASS
E06 residual fix: validated
E06 formal completion: not applicable — exploratory only
```

## Kết luận exploratory

Metrics trên holdout ủng hộ SARIMA hơn ARIMA baseline trong lần chạy này. Corrected
post-burn-in diagnostics cho thấy ARIMA còn residual autocorrelation tại lag 12/24,
trong khi SARIMA chưa có bằng chứng đó tại hai lag đã kiểm tra. E6 vẫn là phần mở
rộng exploratory theo quyết định của Human, không phải formal completion.
