# EXERCISE 05 — TIME SERIES VISUALIZATION

## 1. Exercise Identity

```text
Practice: Practice_1
Exercise ID: EXERCISE_05
Topic: Time Series Visualization
Dataset: AirPassengers
Frequency: Monthly
Rolling window: 12
Rolling direction: trailing
Rolling min_periods: 12
Rolling center: False
Rolling std ddof: 1
Model training required: NO
Status: READY_FOR_HUMAN_APPROVAL
```

---

## 2. Objective

Mục tiêu của bài tập:

- trực quan hóa toàn bộ chuỗi thời gian;
- quan sát trend dài hạn;
- quan sát biến động cục bộ;
- phân tích rolling mean;
- phân tích rolling standard deviation;
- trực quan hóa seasonality theo tháng;
- trực quan hóa seasonality theo month-year heatmap;
- tổng hợp các pattern đã thấy ở các exercise trước;
- tạo evidence trực quan cho báo cáo cuối.

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
Rolling window: 12
```

Exercise 5 sử dụng validated AirPassengers series từ các exercise trước.

Có thể tái sử dụng các findings đã được verify từ:

```text
Exercise 1 — ACF/PACF
Exercise 3 — Decomposition
Exercise 4 — Data Quality
```

Nhưng visualization phải được tạo từ actual validated data, không từ suy luận hoặc dữ liệu đã bị thay đổi không rõ nguồn.

---

## 4. Required Steps

### Step 1 — Load Validated Series

Sử dụng cùng AirPassengers dataset đã được xác minh trước đó.

Kiểm tra tối thiểu:

```text
shape
time range
chronological order
missing values
```

### Step 2 — Plot Full Time Series

Vẽ toàn bộ chuỗi.

Biểu đồ phải hỗ trợ quan sát:

```text
overall trend
seasonal repetition
variance behavior
possible unusual observations
```

### Step 3 — Compute Rolling Mean

Sử dụng:

```text
window = 12
min_periods = 12
center = False
```

Rolling mean dùng để quan sát level/trend cục bộ của chuỗi theo một chu kỳ năm.

Không dùng centered rolling window nếu điều đó làm đưa future observations vào calculation.

### Step 4 — Compute Rolling Standard Deviation

Sử dụng:

```text
window = 12
min_periods = 12
center = False
ddof = 1
```

Rolling standard deviation dùng để quan sát mức độ biến động của chuỗi theo thời gian.

Phải đối chiếu với original series.

### Step 5 — Plot Original Series with Rolling Statistics

Vẽ:

```text
original series
rolling mean
rolling standard deviation
```

Có thể dùng cùng figure hoặc tách figure nếu cần để dễ đọc.

### Step 6 — Create Monthly Seasonal Plot

Do AirPassengers là dữ liệu monthly:

```text
x-axis: month
grouping: year
```

Seasonal plot dùng để quan sát:

```text
monthly pattern
peak months
low months
change in seasonal amplitude across years
```

### Step 7 — Create Month-Year Heatmap

Tạo ma trận:

```text
rows: month, January through December
columns: year, 1949 through 1960
cell value: passengers_thousands
expected shape: 12 × 12
```

Mục tiêu:

```text
observe seasonal concentration
compare years
identify unusually high/low months
```

### Step 8 — Inspect Possible Anomalies

Đối chiếu visualization với evidence từ:

```text
Exercise 3 — residual behavior
Exercise 4 — outlier candidates
```

Không được gọi một điểm là anomaly chỉ vì visually high hoặc low.

### Step 9 — Write Interpretation

Trả lời các câu hỏi ở Section 8.

---

## 5. Scientific Method

### 5.1 Full-Series Visualization

Line chart là visualization nền tảng để quan sát:

```text
trend
seasonality
level changes
variance changes
possible anomalies
```

Nhưng line chart không thay thế statistical analysis.

### 5.2 Rolling Mean

Rolling mean với:

```text
window = 12
```

được dùng để làm mượt biến động ngắn hạn và quan sát level/trend theo chu kỳ năm.

Với monthly data:

```text
12 observations ≈ 1 year
```

### 5.3 Rolling Standard Deviation

Rolling std dùng để kiểm tra variance behavior theo thời gian.

Nếu rolling std tăng cùng level của chuỗi, đây là evidence cần đối chiếu với nhận xét ở Exercise 3 về seasonal amplitude và log transform.

### 5.4 Seasonal Plot

Seasonal plot theo tháng giúp trả lời:

```text
tháng nào thường cao?
tháng nào thường thấp?
pattern theo tháng có lặp lại giữa các năm không?
seasonal amplitude có tăng theo thời gian không?
```

### 5.5 Heatmap

Month-year heatmap giúp nhận diện nhanh:

```text
seasonal blocks
year-to-year growth
high-value periods
low-value periods
visual anomalies
```

Heatmap chỉ là evidence trực quan, không tự xác nhận statistical significance.

---

## 6. Scientific Parameters

```text
Dataset: AirPassengers
Frequency: monthly
Seasonal period: 12
Rolling mean window: 12
Rolling std window: 12
Rolling min_periods: 12
Rolling center: False
Rolling std ddof: 1
Seasonal grouping: month within year
Heatmap rows: month, January through December
Heatmap columns: year, 1949 through 1960
Heatmap expected shape: 12 × 12
```

### Rolling Rule

Mặc định:

```text
trailing rolling window
```

Không dùng:

```text
center=True
```

nếu điều đó khiến rolling value tại thời điểm `t` sử dụng future observations.

---

## 7. Expected Outputs

### Figures

Tối thiểu:

```text
13_full_time_series.png
14_rolling_mean_std.png
15_monthly_seasonal_plot.png
16_month_year_heatmap.png
```

Lưu tại:

```text
outputs/figures/
```

Nếu cần tách rolling mean và rolling std thành hai figure để dễ đọc thì được phép, miễn naming rõ ràng.

### Machine-readable Results

Không bắt buộc tạo result table mới nếu visualization có thể được tái tạo trực tiếp từ validated dataset.

Nếu cần lưu rolling statistics:

```text
rolling_statistics.csv
```

có thể gồm:

```text
timestamp
observed_value
rolling_mean_12
rolling_std_12
```

Lưu tại:

```text
outputs/results/
```

### Narrative Output

Phải có interpretation cho:

```text
overall trend
rolling behavior
seasonality
variance behavior
possible unusual observations
```

---

## 8. Interpretation Questions

Exercise 5 phải trả lời:

1. Xu hướng chung của AirPassengers là gì?
2. Rolling mean thay đổi như thế nào theo thời gian?
3. Rolling standard deviation có ổn định không?
4. Variance có xu hướng tăng theo level của chuỗi không?
5. Tháng nào thường có lượng hành khách cao?
6. Tháng nào thường thấp?
7. Seasonal pattern có lặp lại giữa các năm không?
8. Seasonal amplitude có thay đổi theo thời gian không?
9. Heatmap cho thấy pattern nổi bật nào?
10. Có observation nào trông bất thường không?
11. Các observation đó có trùng với outlier candidates của Exercise 4 không?
12. Visualization có hỗ trợ các kết luận từ ACF/PACF và decomposition không?

Không được viết kết luận trước khi actual figures được tạo.

---

## 9. Validation Criteria

Exercise 5 đạt khi:

```text
[ ] Validated AirPassengers series được sử dụng
[ ] Raw dataset không bị sửa
[ ] Full-series line chart được tạo
[ ] Rolling mean dùng window = 12
[ ] Rolling std dùng window = 12
[ ] Rolling mean/std dùng min_periods = 12 và center = False
[ ] Rolling std dùng ddof = 1
[ ] Rolling calculation không dùng future information ngoài protocol
[ ] Monthly seasonal plot được tạo
[ ] Month-year heatmap được tạo
[ ] Heatmap rows = month, columns = year, shape = 12 × 12
[ ] Figure labels và axes rõ ràng
[ ] Figures đã được inspect
[ ] Interpretation dựa trên actual outputs
[ ] Potential anomalies được đối chiếu với previous evidence
[ ] Không fabricate conclusion
```

---

## 10. Stop Conditions

Phải dừng Exercise 5 nếu:

```text
dataset không phải validated AirPassengers
time index bị sai
frequency không còn là monthly
rolling window khác 12 mà chưa được approve
rolling calculation dùng future observations ngoài protocol
seasonal plot mapping month/year bị sai
heatmap pivot tạo duplicate cell không được giải thích
visualization output không khớp dữ liệu
scientific parameter cần đổi ngoài specification
```

Khi gặp stop condition:

```text
STOP
→ document issue
→ explain impact
→ propose next action
→ wait for approval
```

---

## 11. Completion Condition

Exercise 5 chỉ được xem là `COMPLETED` khi:

```text
full-series visualization completed
AND rolling statistics completed
AND seasonal plot completed
AND heatmap completed
AND figures inspected
AND interpretation questions answered
AND outputs saved
AND no unresolved blocking issue
```

---

## 12. Downstream Role

Kết quả Exercise 5 sẽ được dùng trực tiếp cho:

```text
User-owned Word report — outside the AI implementation plan
```

Exercise 5 là bước tổng hợp visualization cuối trước khi viết báo cáo.

Nó không train model và không tự đưa ra model-performance claim.
