# EXERCISE 05 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_1
Exercise ID: EXERCISE_05
Topic: Time Series Visualization
Plan type: Exercise Before-Process Plan
Dataset: AirPassengers
Status: COMPLETED_AND_VALIDATED
Implementation authorized: YES
```

Tài liệu này là execution plan riêng cho Exercise 5.

Đã xác nhận và Exercise 5 đã được triển khai, chạy và xác minh.

---

## 2. Objective

Mục tiêu của execution cycle này:

- sử dụng validated AirPassengers series;
- tạo full-series visualization;
- tính rolling mean với window = 12;
- tính rolling standard deviation với window = 12;
- bảo đảm rolling window không dùng future information ngoài protocol;
- tạo monthly seasonal plot;
- tạo month-year heatmap;
- đối chiếu possible anomalies với evidence từ Exercise 3 và Exercise 4;
- tổng hợp visual evidence để báo cáo sử dụng trong Word report outside the repository;
- không train model;
- không thay đổi raw dataset.

---

## 3. Required Documents

Trước implementation, Quy trình thực thi phải đọc:

```text
working_rule.md
active .agent/ hoặc .agents/ rules
docs/rules/architecture_rule.md
docs/rules/rule_code.md
docs/plans/practice_1_overview.md
docs/exercise_details/exercise_05_visualization.md
docs/plans/initialize_practice_1.md
docs/plans/exercise_03_before_process.md
docs/plans/exercise_04_before_process.md
docs/status/current_status.md nếu đã tồn tại
```

Phải xác minh upstream outputs cần dùng đã được validate.

Nếu thiếu dependency hoặc có conflict:

```text
STOP
→ report issue
→ chờ xử lý quyết định
```

---

## 4. Input

Input bắt buộc:

```text
Dataset: AirPassengers
Frequency: monthly
Seasonal period: 12
Rolling window: 12
Validated original series
```

Upstream evidence có thể tái sử dụng:

```text
Exercise 1 — ACF/PACF findings
Exercise 3 — decomposition findings
Exercise 4 — outlier candidates
```

Visualization phải dựa trên actual validated data.

---

## 5. Files to Read

Quy trình cần đọc hoặc inspect:

```text
docs/exercise_details/exercise_05_visualization.md
config/practice_1.json
validated AirPassengers input
Exercise 3 decomposition outputs
Exercise 4 outlier outputs
relevant src/practice_1/data/ files
relevant src/practice_1/analysis/ files
relevant src/practice_1/visualization/ files
current notebook nếu đã tồn tại
```

Không giả định file path nếu chưa xác minh structure thực tế.

---

## 6. Files Allowed to Create or Modify

Exercise 5 chỉ được phép tạo/sửa trong:

```text
src/practice_1/analysis/
src/practice_1/visualization/
notebooks/
outputs/figures/
outputs/results/
tests/
docs/status/
docs/logs/
docs/error_analysis/
docs/fix_plans/
```

Reusable logic có thể gồm:

```text
rolling-statistics calculation
full-series plotting
rolling-statistics plotting
seasonal plotting
month-year heatmap generation
anomaly-overlay visualization
```

Không tạo duplicate owner nếu reusable logic tương đương đã tồn tại.

---

## 7. Files Not to Modify

Không được tự ý sửa:

```text
datasets/raw/
working_rule.md
confirmed scoped rule files
confirmed overview
confirmed exercise_05_visualization.md
confirmed initialize_practice_1.md
validated Exercise 1–4 outputs
Practice/Lab khác
unrelated repository configuration
```

Nếu cần thay đổi upstream logic hoặc artifact:

```text
STOP
→ explain reason
→ assess impact
→ chờ xác nhận
```

---

## 8. Scientific Parameters

Exercise 5 phải dùng:

```text
Dataset: AirPassengers
Frequency: monthly
Seasonal period: 12
Rolling mean window: 12
Rolling std window: 12
Rolling direction: trailing
center=True: NOT ALLOWED
Rolling min_periods: 12
Rolling std ddof: 1
Seasonal grouping: month within year
Heatmap rows: month, January through December
Heatmap columns: year, 1949 through 1960
Heatmap expected shape: 12 × 12
Model training: NO
```

Không được tự đổi rolling window.

---

## 9. Sequential Execution Steps

### Step 1 — Verify Upstream Dependencies

Xác minh:

```text
validated AirPassengers input exists
Exercise 3 findings available nếu được tham chiếu
Exercise 4 outlier evidence available nếu được tham chiếu
```

Nếu required upstream dependency chưa đủ:

```text
STOP
```

---

### Step 2 — Verify Repository Context

Xác minh:

```text
Practice_1 root
required rules
Exercise 5 specification
master initialization plan
current execution state
```

Validation:

```text
no unresolved rule conflict
Exercise 5 before-process plan confirmed
```

---

### Step 3 — Load Validated Original Series

Dùng reusable loader/validator.

Sau load:

```text
inspect shape
inspect time range
verify chronology
verify monthly frequency
verify missing values
```

Không sửa raw data.

---

### Step 4 — Create Full-Series Visualization

Tạo:

```text
outputs/figures/13_full_time_series.png
```

Figure phải hỗ trợ quan sát:

```text
overall trend
seasonality
variance behavior
possible unusual observations
```

Sau khi tạo:

```text
inspect actual figure
```

---

### Step 5 — Compute Rolling Mean

Dùng:

```text
window = 12
direction = trailing
min_periods = 12
center = False
```

Không dùng:

```text
center=True
```

Phải verify:

```text
index preserved
expected initial NaN behavior understood
no future observations used
```

---

### Step 6 — Compute Rolling Standard Deviation

Dùng:

```text
window = 12
direction = trailing
min_periods = 12
center = False
ddof = 1
```

Phải verify:

```text
index preserved
initial boundary behavior understood
no future observations used
```

---

### Step 7 — Plot Rolling Statistics

Tạo:

```text
outputs/figures/14_rolling_mean_std.png
```

Figure phải hiển thị rõ:

```text
original series
rolling mean
rolling standard deviation
```

Nếu một figure trở nên khó đọc:

```text
có thể tách figure
```

nhưng naming phải rõ ràng.

Sau khi tạo:

```text
inspect actual figure
```

---

### Step 8 — Create Monthly Seasonal Plot

Chuẩn bị grouping:

```text
x-axis: month
grouping: year
value: passenger count
```

Tạo:

```text
outputs/figures/15_monthly_seasonal_plot.png
```

Phải verify:

```text
month order correct
year grouping correct
no timestamp misalignment
```

Figure phải cho phép quan sát:

```text
peak months
low months
repeated monthly pattern
change in seasonal amplitude across years
```

---

### Step 9 — Create Month-Year Heatmap

Tạo month-year matrix:

```text
rows = month, January through December
columns = year, 1949 through 1960
expected shape = 12 × 12
```

Cell value:

```text
passenger count
```

Output:

```text
outputs/figures/16_month_year_heatmap.png
```

Trước khi pivot:

```text
verify one observation per month-year cell
```

Nếu duplicate cell xuất hiện:

```text
STOP
→ do not aggregate silently
```

Phải inspect:

```text
month labels
year labels
value mapping
visual pattern
```

---

### Step 10 — Optional Rolling Statistics Export

Nếu cần cho traceability/downstream reuse, lưu:

```text
outputs/results/rolling_statistics.csv
```

Cột dự kiến:

```text
timestamp
observed_value
rolling_mean_12
rolling_std_12
```

Không bắt buộc nếu không có giá trị reuse rõ ràng.

---

### Step 11 — Inspect Possible Anomalies

Đối chiếu visual observations với:

```text
Exercise 3 residual behavior
Exercise 4 outlier candidates
```

Không được kết luận:

```text
high/low visual point = anomaly
```

nếu chưa có supporting evidence.

---

### Step 12 — Answer Interpretation Questions

Phải trả lời:

```text
1. Xu hướng chung của AirPassengers là gì?
2. Rolling mean thay đổi như thế nào?
3. Rolling std có ổn định không?
4. Variance có tăng theo level không?
5. Tháng nào thường cao?
6. Tháng nào thường thấp?
7. Seasonal pattern có lặp giữa các năm không?
8. Seasonal amplitude có thay đổi theo thời gian không?
9. Heatmap cho thấy pattern nổi bật nào?
10. Có observation nào trông bất thường không?
11. Observation đó có trùng với outlier candidates của Exercise 4 không?
12. Visualization có hỗ trợ kết luận từ ACF/PACF và decomposition không?
```

Không viết kết luận trước actual output inspection.

---

### Step 13 — Validate Exercise Outputs

Xác minh:

```text
13_full_time_series.png exists and is readable
14_rolling_mean_std.png exists and is readable
15_monthly_seasonal_plot.png exists and is readable
16_month_year_heatmap.png exists and is readable
rolling_statistics.csv consistent nếu được tạo
interpretation matches actual figures
```

---

### Step 14 — Update State

Sau khi Exercise 5 pass validation:

```text
update current status
append concise progress log
```

Không đánh dấu `COMPLETED` nếu còn blocker.

---

## 10. Validation Checklist

```text
[x] Required documents were read
[x] Validated AirPassengers input confirmed
[x] Raw data unchanged
[x] Full-series plot created and inspected
[x] Rolling mean window = 12
[x] Rolling std window = 12
[x] Rolling calculations are trailing
[x] center=True not used
[x] Rolling min_periods = 12
[x] Rolling std ddof = 1
[x] Future information not used in rolling statistics
[x] Rolling figure created and inspected
[x] Monthly seasonal plot created
[x] Month order verified
[x] Year grouping verified
[x] Month-year heatmap created
[x] Heatmap rows = month, columns = year, shape = 12 × 12
[x] No duplicate month-year cells silently aggregated
[x] Heatmap labels and mapping verified
[x] Possible anomalies compared with upstream evidence
[x] Interpretation based on actual outputs
[x] No model training performed
[x] No unrelated file modified
```

---

## 11. Expected Outputs

### Required Figures

```text
outputs/figures/13_full_time_series.png
outputs/figures/14_rolling_mean_std.png
outputs/figures/15_monthly_seasonal_plot.png
outputs/figures/16_month_year_heatmap.png
```

### Optional Result

```text
outputs/results/rolling_statistics.csv
```

### Narrative Evidence

Interpretation phải bao gồm:

```text
overall trend
rolling behavior
variance behavior
monthly seasonality
heatmap pattern
possible unusual observations
cross-check with prior exercises
```

---

## 12. Stop Conditions

Quy trình phải dừng khi:

```text
Exercise 5 plan chưa được approve
required document missing
rule conflict
validated AirPassengers input chưa sẵn sàng
frequency không phải monthly
rolling window khác 12
centered rolling được yêu cầu ngoài protocol
rolling calculation dùng future observations
seasonal month mapping sai
year grouping sai
heatmap có duplicate month-year cells chưa giải thích
visual output không khớp dữ liệu
scientific parameter cần thay đổi
dependency mới cần thêm
unrelated file cần sửa
upstream validated output cần overwrite
raw data bị thay đổi
```

Khi dừng:

```text
1. Không tiếp tục step sau.
2. Ghi observed behavior.
3. Ghi expected behavior.
4. Ghi relevant evidence.
5. Nêu impact.
6. Đề xuất next action.
7. Chờ xác nhận.
```

---

## 13. Completion Gate

Exercise 5 chỉ được xem là complete khi:

```text
validated input used
AND full-series visualization validated
AND rolling statistics validated
AND monthly seasonal plot validated
AND month-year heatmap validated
AND possible anomalies cross-checked
AND interpretation questions answered
AND outputs inspected
AND raw data unchanged
AND no unresolved blocking issue
```

---

## 14. confirmation gate

Trạng thái hiện tại:

```text
EXERCISE_05_BEFORE_PROCESS_CREATED=true
EXERCISE_05_BEFORE_PROCESS_REVIEWED=true
EXERCISE_05_BEFORE_PROCESS_CONFIRMED=true
EXERCISE_05_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_05_COMPLETED=true
EXERCISE_05_VALIDATED=true
```

Quy trình không được code Exercise 5 khi:

```text
EXERCISE_05_IMPLEMENTATION_AUTHORIZED=false
```

Sau khi confirmation:

```text
EXERCISE_05_BEFORE_PROCESS_REVIEWED=true
EXERCISE_05_BEFORE_PROCESS_CONFIRMED=true
EXERCISE_05_IMPLEMENTATION_AUTHORIZED=true
```

---

## 15. workflow Execution Rule

Sau confirmation:

```text
one step
→ execute
→ run
→ verify
→ report
→ next step
```

Không được:

```text
tự đổi rolling window
tự dùng centered rolling
tự sửa raw data
tự aggregate duplicate heatmap cells
tự gọi visual peak là anomaly
tự sửa upstream validated output
tự thêm model
tự bỏ qua validation
tự claim completion
```
