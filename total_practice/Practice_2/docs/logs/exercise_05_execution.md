# EXERCISE 05 — NHẬT KÝ THỰC THI

## Trạng thái

```text
execution date: 2026-10-20
implementation: completed
validation: passed
formal completion: confirmed by Human
```

## Input và evaluation contract

```text
dataset: datasets/raw/a10.csv
full observations: 204
training observations: 163
test observations: 41
train period: 1991-07 through 2005-01
test period: 2005-02 through 2008-06
split: chronological 80/20
shuffle: false
candidate source: outputs/results/arima_candidates.csv
candidates: ARIMA(1,1,1), ARIMA(2,1,1)
fit input: natural log of 163 training levels
regular differencing order: d=1 inside ARIMA
trend policy: no drift (`trend='n'`)
seasonal-naive period: 12
forecast horizon: 41
metric scale: original sales scale
inverse policy: exp(predicted log mean), no bias correction
test used for candidate selection or fitting: false
```

Inverse policy gần tương ứng với conditional-median forecast trên thang gốc và có
thể thấp hơn conditional mean vì không áp dụng log-normal bias correction. Policy
này đã được khóa trước formal evaluation run.

## Kết quả fit

| Model | Trend | Drift | Hội tụ | AIC | BIC | Warning |
|---|---|---:|---:|---:|---:|---|
| `ARIMA(1,1,1)` | `n` | Không | Có | -131.048881 | -121.786092 | none |
| `ARIMA(2,1,1)` | `n` | Không | Có | -129.532608 | -117.182223 | none |

`ARIMA(1,1,1)` có AIC và BIC thấp hơn. Fit criteria không đủ để khẳng định chất
lượng forecast hoặc residual adequacy.

## Residual diagnostics

Quan sát khởi tạo đầu tiên (`loglikelihood_burn=1`) được loại trước khi tính
residual mean, ACF và Ljung–Box. Mỗi model còn 162 residual observations.

| Model | Residual mean | Lag | model_df | Ljung–Box statistic | p-value | Hỗ trợ white noise |
|---|---:|---:|---:|---:|---:|---:|
| `ARIMA(1,1,1)` | 0.036686 | 12 | 2 | 141.289874 | 2.292669e-25 | Không |
| `ARIMA(1,1,1)` | 0.036686 | 24 | 2 | 253.225577 | 3.259832e-41 | Không |
| `ARIMA(2,1,1)` | 0.037050 | 12 | 3 | 140.169457 | 9.517944e-26 | Không |
| `ARIMA(2,1,1)` | 0.037050 | 24 | 3 | 251.126441 | 2.439552e-41 | Không |

Tại `alpha=0.05`, tất cả kiểm định Ljung–Box đều bác bỏ H0 không có
autocorrelation. Residual ACF cũng có seasonal spike mạnh; chưa candidate nào có
residual được hỗ trợ là white noise.

## Đánh giá forecast

Tất cả forecast có 41 giá trị và index trùng khớp hoàn toàn với test index.

| Model | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| `ARIMA(1,1,1)` | 3.833269 | 4.865791 | 18.493908% |
| `ARIMA(2,1,1)` | 3.806140 | 4.834521 | 18.357642% |
| Seasonal naive (12) | 4.256436 | 5.186466 | 20.097262% |

Hai ARIMA candidate có MAE, RMSE và MAPE thấp hơn seasonal-naive baseline trên
holdout này. `ARIMA(2,1,1)` nhỉnh hơn trên ba forecast metrics, còn
`ARIMA(1,1,1)` tốt hơn theo AIC/BIC.

## Sai lệch tuyệt đối lớn nhất

| Model | Timestamp | Actual | Forecast | Absolute error |
|---|---|---:|---:|---:|
| `ARIMA(1,1,1)` | 2008-01-01 | 29.665356 | 17.032717 | 12.632639 |
| `ARIMA(2,1,1)` | 2008-01-01 | 29.665356 | 17.073746 | 12.591610 |
| Seasonal naive (12) | 2008-04-01 | 23.107677 | 12.882645 | 10.225032 |

## Diễn giải

- Giữ nguyên thứ tự thời gian để tránh future leakage; test chỉ là final holdout.
- Residual mean nhỏ trên log scale nhưng autocorrelation mạnh nên không thể kết luận
  white noise.
- Hai ARIMA forecast gần như phẳng và bỏ lỡ level tăng cùng seasonal peak của holdout.
- RMSE nhạy với lỗi lớn hơn vì sai số được bình phương.
- RMSE tốt nhất khoảng 4.83 đơn vị sales, tương đương khoảng 24.8% test mean 19.51;
  sai số vẫn đáng kể dù tốt hơn baseline.
- Seasonal structure hoặc order mới chỉ nên được nghiên cứu trong phạm vi phê duyệt riêng.
- Không candidate nào được công bố là final adequate ARIMA model.

## Output

- `outputs/figures/05_arima_residual_diagnostics.png`
- `outputs/figures/05_arima_forecast_comparison.png`
- `outputs/results/05_arima_fit_summary.csv`
- `outputs/results/05_arima_residual_diagnostics.csv`
- `outputs/results/05_arima_forecasts.csv`
- `outputs/results/05_arima_metrics.csv`

## Xác nhận

```text
targeted and full tests at formal E05 review: 26 passed
dependency check: passed
notebook path: notebooks/Practice_2_present.ipynb
E05 notebook errors: 0
CSV parity with reusable source: passed
figures inspected: passed
raw SHA-256: 4baa700091ba43f59d762ed7112e203134467ecde3f7bc88da3b153040d384cb
E01-E04 artifacts modified by formal E05 execution: false
E06 executed or modified: false
```

Hai `adfuller` FutureWarning trong test E2/E3 không ảnh hưởng kết quả E5. Lần kiểm
tra toàn bộ gần nhất của Practice 2 đạt 30/30 test.
