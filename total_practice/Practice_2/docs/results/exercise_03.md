# E03 — Sai phân và kiểm định lại

## Kết luận chính thức

Raw first difference chưa đủ bằng chứng stationarity. Sau remediation bằng
natural logarithm và first difference, ADF cho `p-value = 0.004720`.

```text
Transformation: natural log
Regular differencing: first difference
Selected d: 1
```

## Kết quả ADF trên chuỗi log-first-difference

| Chỉ số | Giá trị |
|---|---:|
| ADF statistic | -3.659486 |
| p-value | 0.004720 |
| Lag sử dụng | 13 |
| Số observations dùng trong ADF | 148 |
| Quyết định | Bác bỏ H0 |

## Điểm cần chú ý

Second difference chỉ được giữ làm historical comparison, không phải lựa chọn
chính thức. E04 phải dùng đúng chuỗi log-first-difference training series.

## Evidence

- <a href="../logs/exercise_03_execution.md" style="color:#1f6feb;">Execution evidence E03</a>
- <a href="../../outputs/figures/02_first_differenced_series.png" style="color:#1f6feb;">Chuỗi first difference</a>
- <a href="../../outputs/figures/02_log_first_differenced_series.png" style="color:#1f6feb;">Chuỗi log-first-difference</a>
- <a href="../../notebooks/Practice_2_Exercise.ipynb" style="color:#1f6feb;">Notebook core</a>
