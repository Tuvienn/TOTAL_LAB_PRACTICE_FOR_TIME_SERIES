# EXERCISE 03 — NHẬT KÝ THỰC THI

## Phạm vi

Giữ lại first-order differencing trên thang gốc làm bằng chứng chưa đạt. Biện pháp
đã được phê duyệt là áp dụng natural log rồi regular first differencing trên chuỗi
train gốc và chạy lại ADF. Không thực hiện ACF/PACF, fit model hoặc forecast.

## Bằng chứng

```text
original training observations: 163
test observations: 41, sealed and excluded
all training values positive: true
raw first-differenced observations: 162
raw first-difference ADF statistic: -1.706074
raw first-difference p-value: 0.427986
raw first-difference decision: fail to reject H0
remediation transformation: natural logarithm
regular differencing order: 1
log first-differenced observations: 162
remaining missing values: 0
ADF regression: c
ADF autolag: AIC
ADF statistic: -3.659486
p-value: 0.004720
used lag: 13
n observations: 148
alpha: 0.05
decision: reject H0
selected d: 1
E04 handoff: OPEN_FOR_REVIEW
```

## Output

- `outputs/figures/02_first_differenced_series.png`
- `outputs/figures/02_log_first_differenced_series.png`
- `outputs/results/adf_differenced_series.csv`
- `outputs/results/adf_differenced_critical_values.csv`
- `outputs/results/adf_log_first_differenced_series.csv`
- `outputs/results/adf_log_first_differenced_critical_values.csv`
- `outputs/results/e03_transformation_comparison.csv`
- `outputs/results/differencing_decision.csv`

## Quyết định

First difference trên thang gốc không bác bỏ H0 của ADF. Chuỗi sau natural-log
transformation và first difference bác bỏ H0 tại `alpha=0.05`. Vì vậy E3 chọn
natural log và regular `d=1` cho chuỗi train. Không sử dụng quan sát test.

## Giới hạn

Biểu đồ transformed series vẫn có các spike lặp lại theo năm. ADF hỗ trợ
stationarity đối với unit root phi mùa vụ đã kiểm tra nhưng không chứng minh seasonal
dependence đã biến mất. E4 phải phân tích cấu trúc seasonal lag trên đúng scale của E3.

## Xác nhận

```text
python -m pytest -q: 11 passed
notebook code cells executed: 10/10
notebook execution errors: 0
raw SHA-256: 4baa700091ba43f59d762ed7112e203134467ecde3f7bc88da3b153040d384cb
legacy notebook modified: false
E04/E05 modified: false
```
