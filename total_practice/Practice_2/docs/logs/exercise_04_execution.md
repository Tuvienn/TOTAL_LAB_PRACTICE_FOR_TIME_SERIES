# EXERCISE 04 — NHẬT KÝ THỰC THI

## Trạng thái

```text
execution date: 2026-10-20
implementation: completed
validation: passed
E04-to-E05 handoff: completed
```

## Input contract

```text
dataset: datasets/raw/a10.csv
full observations: 204
training observations: 163
sealed test observations: 41
analysis series: log_first_differenced_training
analysis observations: 162
missing values: 0
analysis start: 1991-08-01
analysis end: 2005-01-01
test start: 2005-02-01
analysis scale: natural_log
regular differencing order: d=1
E03 ADF statistic: -3.659486
E03 ADF p-value: 0.004720
test values used for E04 selection: false
```

## Cấu hình ACF/PACF

```text
maximum lag: 36
confidence level: 95%
alpha: 0.05
ACF FFT: false
PACF method: ywm
lag 0 used for p/q interpretation: false
seasonal reference lags: 12, 24, 36
```

Significance được xác định từ confidence interval của `statsmodels` cho từng lag.
Phép xấp xỉ cố định `1.96 / sqrt(n)` không còn được sử dụng.

## Bằng chứng thực tế

```text
significant ACF lags above 0: 1, 11, 12, 24, 36
significant PACF lags above 0: 1, 2, 4, 5, 9, 10, 11, 12, 13, 14
ACF lag 12: 0.844390, significant
ACF lag 24: 0.704369, significant
ACF lag 36: 0.605161, significant
PACF lag 12: 0.512103, significant
PACF lag 24: -0.057087, not significant
PACF lag 36: -0.027328, not significant
```

ACF không cắt cụt đơn giản sau lag 1. ACF mạnh tại lag 12, 24 và 36 cho thấy
seasonal dependence vẫn tồn tại sau natural-log first differencing.

## Candidate tạm thời

| Candidate | Bằng chứng | Trạng thái |
|---|---|---|
| `ARIMA(1,1,1)` | ACF lag 1 và PACF lag 1 có ý nghĩa | provisional |
| `ARIMA(2,1,1)` | PACF lag 1 và 2 có ý nghĩa; cần so sánh với candidate gọn hơn | provisional |

Cả hai candidate kế thừa `natural_log` và `d=1`. Chúng là input cho bước fit và
diagnostics ở E5, không phải final-model conclusion. Seasonal dependence còn lại
được ghi nhận là giới hạn; E4 không tự mở rộng sang SARIMA.

## Output

- `outputs/figures/03_acf_pacf_log_first_differenced.png`
- `outputs/results/acf_log_first_differenced.csv`
- `outputs/results/pacf_log_first_differenced.csv`
- `outputs/results/arima_candidates.csv`

## Xác nhận

```text
targeted and full tests: 18 passed
notebook path: notebooks/Practice_2_present.ipynb
E04 notebook errors: 0
figure inspected: true
CSV outputs matched reusable computation: true
raw SHA-256: 4baa700091ba43f59d762ed7112e203134467ecde3f7bc88da3b153040d384cb
E05/E06 executed or modified by E04 validation: false
```

Tại thời điểm xác nhận E4, chỉ các cell thuộc phạm vi E4 được chạy. E5 sau đó đã
được phê duyệt, triển khai và kiểm tra độc lập.
