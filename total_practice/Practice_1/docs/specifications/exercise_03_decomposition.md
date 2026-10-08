# EXERCISE 03 — TIME SERIES DECOMPOSITION

## 1. Exercise Identity

```text
Practice: Practice_1
Exercise ID: EXERCISE_03
Topic: Time Series Decomposition
Dataset: AirPassengers
Frequency: Monthly
Seasonal period: 12
Decomposition method: STL
Log transform: YES
STL robust: TRUE
Model training required: NO
Status: READY_FOR_HUMAN_APPROVAL
```

---

## 2. Objective

Mục tiêu của bài tập:

- phân rã chuỗi thành các thành phần chính;
- quan sát trend;
- quan sát seasonality;
- phân tích residual;
- đánh giá residual có giống white noise hay không;
- hiểu seasonal amplitude thay đổi như thế nào theo level của chuỗi;
- tạo evidence phục vụ kết luận tổng hợp ở các exercise sau.

---

## 3. Input

Dataset chính:

```text
AirPassengers
```

Thông tin liên quan:

```text
Frequency: monthly
Seasonal period: 12
Observed variable: passenger count in thousands
```

Dataset phải là cùng dữ liệu đã được xác minh ở Exercise 1.

Không được thay raw dataset.

---

## 4. Required Steps

### Step 1 — Load validated AirPassengers series

Sử dụng cùng nguồn và schema đã được xác minh trước đó.

### Step 2 — Inspect original series

Quan sát lại:

```text
trend
seasonality
variance behavior
seasonal amplitude
```

### Step 3 — Apply Log Transform

Áp dụng log transform trên working series:

```text
log(y_t)
```

Mục tiêu:

```text
giảm level-dependent variance
làm seasonal amplitude ổn định hơn
hỗ trợ additive STL decomposition
```

Raw data không bị sửa.

### Step 4 — Apply STL Decomposition

Sử dụng:

```text
period = 12
robust = True
```

Decompose thành:

```text
Observed
Trend
Seasonal
Residual
```

### Step 5 — Plot Components

Phải vẽ đầy đủ:

```text
Observed
Trend
Seasonal
Residual
```

### Step 6 — Inspect Residual

Quan sát:

```text
mean behavior
variance behavior
remaining pattern
remaining seasonality
possible outliers
```

### Step 7 — Compare Residual with White Noise Concept

Dùng kiến thức và evidence từ Exercise 2 để đánh giá:

```text
Residual có gần white noise không?
```

Không được kết luận chỉ dựa trên việc residual "trông ngẫu nhiên".

Residual assessment tối thiểu gồm:

```text
residual plot
residual ACF to 40 lags with 95% confidence interval
Ljung-Box diagnostic at lag 12
```

Ljung-Box là supplementary statistical evidence; conclusion phải kết hợp plot, ACF
và test result thay vì phụ thuộc vào một p-value duy nhất.

### Step 8 — Write Interpretation

Phải trả lời các câu hỏi ở Section 8.

---

## 5. Scientific Method

### 5.1 Decomposition

Decomposition được dùng để biểu diễn chuỗi thành:

```text
Observed
→ Trend
→ Seasonal
→ Residual
```

Trong Exercise 3, decomposition dùng để khám phá cấu trúc chuỗi chứ không phục vụ model fitting.

### 5.2 Why Log Transform

AirPassengers có thể có seasonal amplitude thay đổi theo level.

Log transform được sử dụng như một scientific design decision nhằm:

```text
stabilize variance
reduce multiplicative behavior
make additive decomposition more interpretable
```

Không được hiểu rằng đề bài bắt buộc log transform.

### 5.3 STL

Sử dụng STL vì:

```text
hỗ trợ seasonal period rõ ràng
linh hoạt với trend
phù hợp cho monthly data
robust option giúp giảm ảnh hưởng của extreme observations
```

### 5.4 Residual Interpretation

Residual lý tưởng nên:

```text
không còn trend rõ
không còn seasonal pattern rõ
không còn strong autocorrelation
gần white-noise behavior
```

Đây là điều cần kiểm tra bằng evidence, không phải giả định trước.

---

## 6. Scientific Parameters

```text
Dataset: AirPassengers
Frequency: monthly
Seasonal period: 12
Transform: natural logarithm
Decomposition: STL
STL period: 12
STL robust: True
Residual ACF maximum lag: 40
Residual ACF confidence level: 95%
Residual Ljung-Box lag: 12
```

### Design Decision Note

Các parameter sau là scientific design decision của Practice 1:

```text
log transform
STL
robust=True
```

Không phải requirement bắt buộc của đề gốc.

Đề gốc chỉ yêu cầu:

```text
STL hoặc classical decomposition
```

---

## 7. Expected Outputs

### Figures

Tối thiểu:

```text
07_log_transformed_series.png
08_stl_decomposition.png
09_decomposition_residual.png
```

`09_decomposition_residual.png` phải gồm residual time plot và residual ACF đến 40
lags; có thể dùng hai panels trong cùng figure.

Lưu tại:

```text
outputs/figures/
```

### Machine-readable Results

Recommended reusable component output:

```text
decomposition_components.csv
```

Component columns:

```text
timestamp
observed_log
trend_log
seasonal_log
residual_log
```

Các component là kết quả STL trên natural-log scale; tên cột và axis label không được
làm người đọc hiểu nhầm đây là passenger counts trên original scale.

Lưu tại:

```text
outputs/results/
```

Required diagnostic output:

```text
residual_diagnostics.csv
```

File này lưu actual Ljung-Box lag, statistic và p-value tại lag 12.

### Narrative Output

Phải có interpretation cho:

```text
trend
seasonality
residual
white-noise similarity
```

---

## 8. Interpretation Questions

Exercise 3 phải trả lời:

1. Trend của AirPassengers tăng hay giảm?
2. Trend có thay đổi đều hay có giai đoạn tăng nhanh hơn?
3. Seasonality có mạnh không?
4. Seasonal pattern có lặp lại theo chu kỳ 12 tháng không?
5. Seasonal amplitude của original series có thay đổi theo level không?
6. Log transform có làm seasonal amplitude ổn định hơn không?
7. Residual còn pattern rõ ràng không?
8. Residual có dấu hiệu seasonality còn sót lại không?
9. Residual có gần white noise không?
10. Có điểm residual bất thường nổi bật nào không?

Không được trả lời trước khi actual decomposition output được tạo.

---

## 9. Validation Criteria

Exercise 3 đạt khi:

```text
[ ] Validated AirPassengers series được sử dụng
[ ] Raw data không bị sửa
[ ] Log transform được áp dụng trên working copy
[ ] STL sử dụng period = 12
[ ] STL robust = True
[ ] Observed component được tạo
[ ] Trend component được tạo
[ ] Seasonal component được tạo
[ ] Residual component được tạo
[ ] Decomposition plot đã được inspect
[ ] Residual đã được inspect
[ ] Residual ACF đến 40 lags đã được inspect
[ ] Residual Ljung-Box lag 12 đã được chạy và diễn giải như supplementary evidence
[ ] Interpretation dựa trên actual outputs
[ ] Không fabricate conclusion
```

---

## 10. Stop Conditions

Phải dừng Exercise 3 nếu:

```text
dataset không phải validated AirPassengers
series chứa giá trị không hợp lệ cho log transform
frequency không được xác nhận là monthly
STL period không phù hợp với actual frequency
decomposition computation fail
component output có missing hoặc shape mismatch bất thường
scientific parameter cần đổi ngoài specification
```

Nếu log transform không thể áp dụng:

```text
STOP
→ document cause
→ explain scientific impact
→ propose alternative
→ wait for approval
```

Không tự chuyển sang decomposition khác.

---

## 11. Completion Condition

Exercise 3 chỉ được xem là `COMPLETED` khi:

```text
validated input used
AND log transformation completed
AND STL decomposition completed
AND all four components inspected
AND residual assessed
AND interpretation questions answered
AND outputs saved
AND no unresolved blocking issue
```

---

## 12. Downstream Role

Kết quả Exercise 3 sẽ được dùng làm evidence cho:

```text
Exercise 4 — Outlier analysis
Exercise 5 — Visualization synthesis
User-owned Word report — outside the AI implementation plan
```

Đặc biệt:

```text
decomposition residual
```

có thể được sử dụng làm cơ sở để phát hiện outlier ở Exercise 4.

Exercise 3 không train hoặc chọn forecasting model.
