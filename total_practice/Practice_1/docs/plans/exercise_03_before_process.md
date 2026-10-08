# EXERCISE 03 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_1
Exercise ID: EXERCISE_03
Topic: Time Series Decomposition
Plan type: Exercise Before-Process Plan
Dataset: AirPassengers
Decomposition: Log Transform + STL
Status: WAITING_APPROVAL
Implementation authorized: NO
```

Tài liệu này là execution plan riêng cho Exercise 3.

Agent chỉ được bắt đầu code Exercise 3 sau khi Human approve file này.

---

## 2. Objective

Mục tiêu của execution cycle này:

- sử dụng validated AirPassengers series;
- tạo working copy cho decomposition;
- áp dụng natural-log transform;
- chạy STL decomposition với period = 12 và robust = True;
- tạo Observed, Trend, Seasonal và Residual;
- inspect từng component;
- đánh giá residual dựa trên evidence;
- liên hệ residual với khái niệm white noise từ Exercise 2;
- lưu figures và machine-readable results;
- không train model;
- không thay đổi raw dataset.

---

## 3. Required Documents

Trước implementation, agent phải đọc:

```text
working_rule.md
active .agent/ hoặc .agents/ rules
docs/rules/architecture_rule.md
docs/rules/rule_code.md
docs/plans/practice_1_overview.md
docs/exercise_details/exercise_03_decomposition.md
docs/plans/initialize_practice_1.md
docs/plans/exercise_01_before_process.md
docs/plans/exercise_02_before_process.md
docs/status/current_status.md nếu đã tồn tại
```

Ngoài ra phải xác minh Exercise 1 và Exercise 2 đã có validated outputs cần thiết.

Nếu thiếu dependency hoặc có conflict:

```text
STOP
→ report issue
→ chờ Human quyết định
```

---

## 4. Input

Input bắt buộc:

```text
Dataset: AirPassengers
Frequency: monthly
Seasonal period: 12
Observed variable: passenger count in thousands
```

Input phải là validated series từ upstream logic.

Trước decomposition phải xác minh:

```text
all values required for log transform are positive
time index valid
monthly frequency confirmed
chronological order preserved
no unresolved missing values affecting decomposition
```

---

## 5. Files to Read

Agent cần đọc hoặc inspect:

```text
docs/exercise_details/exercise_03_decomposition.md
config/practice_1.json
validated AirPassengers source/output
relevant src/practice_1/data/ files
relevant src/practice_1/analysis/ files
relevant src/practice_1/visualization/ files
current notebook nếu đã tồn tại
Exercise 2 white-noise outputs nếu dùng cho residual comparison
```

Không giả định path nếu chưa xác minh structure thực tế.

---

## 6. Files Allowed to Create or Modify

Exercise 3 chỉ được phép tạo/sửa trong:

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

Có thể mở rộng reusable logic trong `src/practice_1/analysis/` cho:

```text
log transformation
STL decomposition
component extraction
residual diagnostics
```

Có thể mở rộng reusable plotting logic trong `src/practice_1/visualization/` cho:

```text
transformed-series plot
decomposition plot
residual plot
```

Không tạo duplicate owner nếu function tương đương đã tồn tại.

---

## 7. Files Not to Modify

Không được tự ý sửa:

```text
datasets/raw/
working_rule.md
approved scoped rule files
approved overview
approved exercise_01_acf_pacf.md
approved exercise_02_white_noise.md
approved exercise_03_decomposition.md
approved initialize_practice_1.md
validated Exercise 1 outputs
validated Exercise 2 outputs
Exercise 4–5 specifications
Practice/Lab khác
unrelated repository configuration
```

Nếu cần thay đổi upstream logic hoặc output:

```text
STOP
→ explain reason
→ assess impact
→ wait for Human approval
```

---

## 8. Scientific Parameters

Exercise 3 phải dùng:

```text
Dataset: AirPassengers
Frequency: monthly
Seasonal period: 12
Transform: natural logarithm
Decomposition method: STL
STL period: 12
STL robust: True
Residual ACF maximum lag: 40
Residual ACF confidence level: 95%
Residual Ljung-Box lag: 12
Model training: NO
```

Lưu ý:

```text
log transform + STL + robust=True
```

là scientific design decision của project.

Không được tự chuyển sang classical decomposition hoặc bỏ log transform nếu chưa được approve.

---

## 9. Sequential Execution Steps

### Step 1 — Verify Upstream Dependencies

Xác minh:

```text
AirPassengers dataset validated
Exercise 1 completed or required data validation available
Exercise 2 white-noise evidence available for residual comparison
```

Nếu upstream dependency chưa đạt:

```text
STOP
```

---

### Step 2 — Verify Repository Context

Xác minh:

```text
Practice_1 root
required rules
Exercise 3 specification
master initialization plan
current execution state
```

Validation:

```text
no unresolved rule conflict
Exercise 3 before-process plan approved
```

---

### Step 3 — Load Validated Series

Dùng reusable loader/validator từ `src/practice_1/data/`.

Không duplicate loader trong notebook nếu owner đã tồn tại.

Sau load:

```text
inspect shape
inspect time range
verify chronological order
verify monthly frequency
verify missing values
```

---

### Step 4 — Validate Log-Transform Preconditions

Kiểm tra:

```text
all observed values > 0
no invalid/non-numeric values
no unresolved NaN
```

Nếu có giá trị không hợp lệ cho log transform:

```text
STOP
→ do not shift/add constant automatically
→ report exact issue
→ wait for approval
```

---

### Step 5 — Create Working Copy

Tạo working series riêng.

```text
raw data
→ unchanged

working series
→ transformed for analysis
```

Không ghi transformed values trở lại raw file.

---

### Step 6 — Apply Natural-Log Transform

Tính:

```text
log(y_t)
```

Sau execution:

```text
inspect transformed values
verify no NaN/inf
verify index preserved
```

Output figure:

```text
outputs/figures/07_log_transformed_series.png
```

Figure phải được inspect thực tế.

---

### Step 7 — Apply STL Decomposition

Dùng:

```text
period = 12
robust = True
```

Extract:

```text
Observed
Trend
Seasonal
Residual
```

Sau execution phải xác minh:

```text
all components exist
index alignment preserved
component lengths consistent
no unexpected NaN beyond method boundary behavior
```

Nếu STL fail:

```text
STOP
```

Không tự chuyển method.

---

### Step 8 — Create Decomposition Figure

Tạo:

```text
outputs/figures/08_stl_decomposition.png
```

Figure phải hiển thị rõ:

```text
Observed
Trend
Seasonal
Residual
```

Sau khi tạo:

```text
inspect actual figure
```

---

### Step 9 — Export Components

Nếu cần cho traceability/downstream reuse, lưu:

```text
outputs/results/decomposition_components.csv
```

Cột dự kiến:

```text
timestamp
observed_log
trend_log
seasonal_log
residual_log
```

Phải verify:

```text
row count
timestamp alignment
no accidental index shift
component scale labeled as natural log
```

---

### Step 10 — Inspect Residual

Phân tích residual theo các tiêu chí:

```text
mean behavior
variance behavior
remaining trend
remaining seasonality
remaining pattern
possible extreme points
```

Tạo residual figure:

```text
outputs/figures/09_decomposition_residual.png
```

Figure này gồm residual time plot và residual ACF đến 40 lags. Lưu actual Ljung-Box
lag-12 result tại:

```text
outputs/results/residual_diagnostics.csv
```

---

### Step 11 — Compare Residual with White-Noise Concept

Dùng Exercise 2 làm conceptual reference.

Không được kết luận:

```text
residual = white noise
```

chỉ vì residual nhìn ngẫu nhiên.

Phải dựa trên actual evidence như:

```text
visible pattern
residual ACF to 40 lags with 95% confidence interval
Ljung-Box diagnostic at lag 12
stability around zero
seasonal traces
```

Ljung-Box phải được ghi rõ là supplementary và không được dùng như sole evidence.

---

### Step 12 — Answer Interpretation Questions

Phải trả lời:

```text
1. Trend tăng hay giảm?
2. Trend có giai đoạn tăng nhanh hơn không?
3. Seasonality mạnh hay yếu?
4. Pattern có lặp theo chu kỳ 12 tháng không?
5. Seasonal amplitude original series có thay đổi theo level không?
6. Log transform có làm seasonal amplitude ổn định hơn không?
7. Residual còn pattern rõ không?
8. Residual còn dấu hiệu seasonality không?
9. Residual có gần white noise không?
10. Có residual bất thường nổi bật không?
```

Không viết kết luận trước khi outputs được inspect.

---

### Step 13 — Validate Exercise Outputs

Xác minh:

```text
07_log_transformed_series.png exists and is readable
08_stl_decomposition.png exists and is readable
09_decomposition_residual.png exists and is readable
decomposition_components.csv consistent nếu được tạo
residual_diagnostics.csv contains actual lag-12 statistic and p-value
interpretation matches actual outputs
```

---

### Step 14 — Update State

Sau khi Exercise 3 pass validation:

```text
update current status
append concise progress log
```

Không đánh dấu `COMPLETED` nếu còn blocker.

---

## 10. Validation Checklist

```text
[ ] Required documents were read
[ ] Upstream validated AirPassengers input confirmed
[ ] Log-transform preconditions checked
[ ] Raw data unchanged
[ ] Working copy created
[ ] Natural-log transform applied
[ ] Index preserved after transform
[ ] No unexpected NaN/inf after transform
[ ] STL period = 12
[ ] STL robust = True
[ ] Observed component created
[ ] Trend component created
[ ] Seasonal component created
[ ] Residual component created
[ ] Component alignment verified
[ ] Decomposition figure created and inspected
[ ] Residual figure created and inspected
[ ] Residual ACF to 40 lags created and inspected
[ ] Residual Ljung-Box lag 12 executed and interpreted as supplementary evidence
[ ] Residual interpretation based on actual evidence
[ ] No model training performed
[ ] No unrelated file modified
```

---

## 11. Expected Outputs

### Required Figures

```text
outputs/figures/07_log_transformed_series.png
outputs/figures/08_stl_decomposition.png
outputs/figures/09_decomposition_residual.png
```

### Optional / Recommended Result

```text
outputs/results/decomposition_components.csv
```

### Required Diagnostic Result

```text
outputs/results/residual_diagnostics.csv
```

### Narrative Evidence

Interpretation phải bao gồm:

```text
trend
seasonality
effect of log transform
residual behavior
white-noise similarity assessment
```

---

## 12. Stop Conditions

Agent phải dừng khi:

```text
Exercise 3 plan chưa được approve
required document missing
rule conflict
validated AirPassengers input chưa sẵn sàng
series chứa giá trị <= 0
unresolved NaN
frequency không phải monthly
STL period không còn phù hợp
STL computation fail
component alignment sai
unexpected missing output
scientific parameter cần thay đổi
dependency mới cần thêm
unrelated file cần sửa
upstream validated output cần overwrite
```

Khi dừng:

```text
1. Không tiếp tục step sau.
2. Ghi observed behavior.
3. Ghi expected behavior.
4. Ghi relevant evidence.
5. Nêu impact.
6. Đề xuất next action.
7. Chờ Human approval.
```

---

## 13. Completion Gate

Exercise 3 chỉ được xem là complete khi:

```text
validated input used
AND log transform validated
AND STL decomposition validated
AND all four components inspected
AND residual assessed
AND interpretation questions answered
AND outputs inspected
AND raw data unchanged
AND no unresolved blocking issue
```

---

## 14. Approval Gate

Trạng thái hiện tại:

```text
EXERCISE_03_BEFORE_PROCESS_CREATED=true
EXERCISE_03_BEFORE_PROCESS_REVIEWED=false
EXERCISE_03_BEFORE_PROCESS_APPROVED=false
EXERCISE_03_IMPLEMENTATION_AUTHORIZED=false
```

Agent không được code Exercise 3 khi:

```text
EXERCISE_03_IMPLEMENTATION_AUTHORIZED=false
```

Sau khi Human approve:

```text
EXERCISE_03_BEFORE_PROCESS_REVIEWED=true
EXERCISE_03_BEFORE_PROCESS_APPROVED=true
EXERCISE_03_IMPLEMENTATION_AUTHORIZED=true
```

---

## 15. Agent Execution Rule

Sau approval:

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
tự bỏ log transform
tự đổi STL period
tự đổi robust setting
tự chuyển decomposition method
tự sửa raw data
tự sửa upstream validated output
tự thêm forecasting model
tự bỏ qua validation
tự claim completion
```
