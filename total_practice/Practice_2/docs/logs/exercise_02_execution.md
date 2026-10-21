# EXERCISE 02 — NHẬT KÝ THỰC THI

## Phạm vi

Chạy kiểm định ADF trên chuỗi train gốc từ E1. Không thực hiện differencing,
ACF/PACF, fit model hoặc forecast.

## Bằng chứng

```text
input: original training series only
train observations: 163
test observations: 41, excluded
alpha: 0.05
ADF statistic: 2.230893
p-value: 0.998907
used lag: 14
n observations: 148
decision: fail to reject H0
```

H0 phát biểu rằng chuỗi có unit root. Vì p-value lớn hơn `0.05`, chưa đủ bằng
chứng để bác bỏ H0; kiểm định này chưa hỗ trợ kết luận chuỗi train gốc là stationary.

## Output

- `outputs/results/adf_original_series.csv`
- `outputs/results/adf_original_critical_values.csv`

## Xác nhận

- `python -m pytest -q`: 3 test đạt.
- Notebook thực thi thành công.
