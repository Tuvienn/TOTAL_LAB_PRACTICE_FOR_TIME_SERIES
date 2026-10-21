# PRACTICE 2 — TRẠNG THÁI HIỆN TẠI

## 1. Trạng thái tổng thể

```text
EXERCISE_01_COMPLETED
EXERCISE_02_COMPLETED
EXERCISE_03_COMPLETED_WITH_LOG_TRANSFORMATION
EXERCISE_04_COMPLETED_AND_VALIDATED
EXERCISE_05_COMPLETED_AND_VALIDATED
EXERCISE_06_EXPLORATORY_ONLY
EXERCISE_06_RESIDUAL_DIAGNOSTICS_FIXED_AND_VALIDATED
PRACTICE_2_HANDOFF_APPROVED
```

E1–E5 là phạm vi chính thức đã triển khai và kiểm tra. Theo quyết định của
Human, E6 được giữ ở mức **exploratory**: notebook và kết quả hiện có được dùng
để trình bày phần mở rộng, nhưng E6 không được đánh dấu `COMPLETED` và không
phải formal workflow của Practice 2.

## 2. Exercise 1 — EDA và temporal split

```text
implementation authorized: true
implementation completed: true
validation passed: true
formal completion: true
dataset: a10.csv
rows: 204
monthly index: valid
missing values: 0
duplicate timestamps: 0
missing monthly intervals: 0
train/test observations: 163/41
split: chronological 80/20, shuffle=false
test set sealed during analysis: true
```

E1 ghi nhận xu hướng tăng, mùa vụ năm và độ biến động tăng theo level. Đây là
nhận xét EDA, không thay thế kiểm định stationarity ở E2.

## 3. Exercise 2 — ADF trên chuỗi gốc

```text
implementation authorized: true
implementation completed: true
validation passed: true
formal completion: true
series tested: raw training series
ADF statistic: 2.230893
p-value: 0.998907
alpha: 0.05
decision: fail to reject H0
```

Kết luận đúng phạm vi: chưa đủ bằng chứng để xem chuỗi train gốc là stationary;
không diễn giải việc không bác bỏ H0 thành bằng chứng tuyệt đối rằng H0 đúng.

## 4. Exercise 3 — Transformation và differencing

```text
implementation authorized: true
implementation completed: true
validation passed: true
formal completion: true
raw first-difference ADF statistic/p-value: -1.706074 / 0.427986
remediation transformation: natural logarithm
log first-difference ADF statistic/p-value: -3.659486 / 0.004720
regular differencing order: d=1
analysis observations: 162
remaining missing values: 0
test set used: false
```

Chuỗi được chuyển tiếp sang E4 là `log(train).diff().dropna()`. ADF hỗ trợ
stationarity trên scale này nhưng không khẳng định seasonal dependence đã biến mất.

## 5. Exercise 4 — ACF/PACF và candidate

```text
implementation authorized: true
implementation completed: true
validation passed: true
formal completion: true
analysis input: 162-value log first-differenced training series
test set used: false
maximum lag: 36
confidence level: 95%
PACF method: ywm
provisional candidates: ARIMA(1,1,1), ARIMA(2,1,1)
remaining seasonal dependence: present
```

E4 chỉ đề xuất candidate để E5 fit và đánh giá; không tuyên bố đã chọn final model.
Evidence chi tiết nằm trong `docs/logs/exercise_04_execution.md`.

## 6. Exercise 5 — ARIMA và đánh giá forecast

```text
implementation authorized: true
implementation completed: true
validation passed: true
formal completion: true
train/test observations: 163/41
candidates: ARIMA(1,1,1), ARIMA(2,1,1)
baseline: seasonal naive, period=12
forecast horizon: 41
analysis scale: natural_log
inverse policy: exp(log forecast mean), no bias correction
trend policy: no drift, trend='n'
best holdout metrics among candidates: ARIMA(2,1,1)
best training AIC/BIC among candidates: ARIMA(1,1,1)
residual white-noise support: false for both candidates
final adequate ARIMA selected: false
```

Hai candidate tốt hơn seasonal-naive baseline trên holdout hiện tại nhưng đều còn
residual autocorrelation mạnh. Vì vậy E5 hoàn thành phần so sánh được yêu cầu mà
không tuyên bố có một final adequate model. Evidence chi tiết nằm trong
`docs/logs/exercise_05_execution.md`.

## 7. Exercise 6 — AirPassengers exploratory

```text
formal implementation authorization: false
formal completion: false
scope: exploratory extension
presentation notebook: notebooks/Practice_2_advanced_sarima.ipynb
dataset: airline-passengers.csv
rows: 144
train/test observations: 115/29
split: chronological 80/20, shuffle=false
analysis scale: natural_log
selected exploratory differencing: d=1, D=1, s=12
candidate models: ARIMA(1,1,1), SARIMA(1,1,1)(0,1,1,12)
residual diagnostics fix approved: true
residual diagnostics fix validated: true
```

Kết quả exploratory đã kiểm tra:

| Mô hình | Burn-in | Residual observations | Ljung–Box p-value lag 12 | Ljung–Box p-value lag 24 | MAE | RMSE |
|---|---:|---:|---:|---:|---:|---:|
| ARIMA | 1 | 114 | 2.944816e-16 | 2.308263e-27 | 84.254030 | 96.327159 |
| SARIMA | 13 | 102 | 0.573996 | 0.473545 | 12.164590 | 14.917399 |

Trong holdout này, SARIMA có MAE/RMSE thấp hơn ARIMA. Sau khi loại đúng burn-in,
Ljung–Box còn phát hiện residual autocorrelation của ARIMA tại lag 12 và 24; chưa
phát hiện autocorrelation của SARIMA tại hai lag được kiểm tra. Điều này không chứng
minh residual SARIMA là white noise ở mọi lag.

Theo Phương án A đã được Human chọn, không mở rộng E6 thành reusable pipeline đầy
đủ, không yêu cầu full artifact set và không đánh dấu E6 hoàn thành chính thức.

## 8. Ranh giới khoa học và bàn giao

- E1–E5 giữ nguyên temporal split, scale phân tích, candidate và verified metrics.
- E6 chỉ là bằng chứng exploratory, tách khỏi formal completion của E1–E5.
- Hai notebook đã hoàn tất presentation state, 5W1H, dataset provenance và table
  styling light/dark theo phạm vi Human phê duyệt.
- Trạng thái bàn giao hiện tại: `HANDOFF_APPROVED`.
- Không push lên GitHub nếu Human chưa yêu cầu riêng.

## 9. Kết quả final review ngày 2026-10-21

```text
full test suite: 30 passed
main notebook: 27/27 code cells, sequential, 0 errors
advanced notebook: 10/10 code cells, sequential, 0 errors
notebook kernelspec: practice2-timeseries, valid Python 3.12 environment
dataset links: verified against the assignment PDF
E1-E5 artifact/report consistency: passed after numeric synchronization
handoff state: HANDOFF_APPROVED
```

Final review đã sửa ba sai lệch tài liệu mà không thay đổi modeling logic:

1. Đồng bộ mô tả E4 để xác nhận ACF/PACF dùng đúng
   `log(train).diff().dropna()` thay vì ghi nhầm là sai phân thô.
2. Đồng bộ forecast và absolute error lớn nhất của E5 theo artifact sau clean-run.
3. Đồng bộ AIC/BIC của SARIMA theo clean-run hiện hành.

Các giới hạn còn lại là kết quả khoa học, không phải lỗi triển khai:

- residual của hai ARIMA E5 vẫn còn autocorrelation tại lag 12 và 24;
- chưa chọn được một final adequate ARIMA cho Dataset 1;
- E6 vẫn là exploratory theo Phương án A và không được đánh dấu hoàn thành chính thức.
