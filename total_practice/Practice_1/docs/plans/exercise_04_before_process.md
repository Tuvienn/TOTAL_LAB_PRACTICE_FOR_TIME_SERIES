# EXERCISE 04 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_1
Exercise ID: EXERCISE_04
Topic: Time Series Data Quality
Plan type: Exercise Before-Process Plan
Dataset: AirPassengers
Status: WAITING_APPROVAL
Implementation authorized: NO
```

Tài liệu này là execution plan riêng cho Exercise 4.

Agent chỉ được bắt đầu code Exercise 4 sau khi Human approve file này.

---

## 2. Objective

Mục tiêu của execution cycle này:

- sử dụng validated AirPassengers series;
- kiểm tra existing missing values;
- tạo missing values giả lập trên working copy;
- lưu true values trước khi masking;
- so sánh forward-fill và time interpolation trên cùng missing positions;
- đánh giá reconstruction error tại đúng các vị trí bị mask;
- phát hiện potential outliers bằng approved protocol;
- đối chiếu outlier candidates với decomposition residual;
- vẽ before/after treatment;
- không sửa raw dataset;
- không tự động xóa outlier;
- không train model.

---

## 3. Required Documents

Trước implementation, agent phải đọc:

```text
working_rule.md
active .agent/ hoặc .agents/ rules
docs/rules/architecture_rule.md
docs/rules/rule_code.md
docs/plans/practice_1_overview.md
docs/exercise_details/exercise_04_data_quality.md
docs/plans/initialize_practice_1.md
docs/plans/exercise_03_before_process.md
docs/status/current_status.md nếu đã tồn tại
```

Phải xác minh Exercise 3 đã có validated decomposition residual nếu residual được dùng trong outlier analysis.

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
Validated original series
```

Input bổ sung cho outlier analysis:

```text
validated decomposition residual from Exercise 3
```

Trước thí nghiệm phải xác minh:

```text
raw series available
raw series unchanged
time index valid
chronological order valid
missing count known
```

---

## 5. Locked Scientific Decisions

```text
Total masked observations: 6
Isolated timestamps: 1952-03, 1954-11, 1959-04
Consecutive block: 1956-06 through 1956-08
Boundary rule: no masked point in the first or last 12 observations
Reconstruction summary metric: MAE on masked positions only
Outlier input: natural-log STL residual from Exercise 3
Outlier method: IQR
Lower fence: Q1 - 1.5 × IQR
Upper fence: Q3 + 1.5 × IQR
Outlier action: flag and inspect only
```

Các timestamp phải được đối chiếu với validated monthly index trước masking. Nếu một
timestamp không tồn tại hoặc source index khác contract, phải dừng thay vì tự chọn vị
trí thay thế.

---

## 6. Files to Read

Agent cần đọc hoặc inspect:

```text
docs/exercise_details/exercise_04_data_quality.md
config/practice_1.json
validated AirPassengers input
Exercise 3 decomposition outputs
relevant src/practice_1/data/ files
relevant src/practice_1/analysis/ files
relevant src/practice_1/visualization/ files
current notebook nếu đã tồn tại
```

Không giả định file path nếu chưa xác minh repository structure.

---

## 7. Files Allowed to Create or Modify

Exercise 4 chỉ được phép tạo/sửa trong:

```text
src/practice_1/data/
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
missing-value masking
forward-fill treatment
time interpolation treatment
reconstruction comparison
outlier scoring
outlier candidate extraction
before/after visualization
```

Không tạo duplicate owner nếu reusable logic tương đương đã tồn tại.

---

## 8. Files Not to Modify

Không được tự ý sửa:

```text
datasets/raw/
working_rule.md
approved scoped rule files
approved overview
approved exercise_04_data_quality.md
approved initialize_practice_1.md
validated Exercise 1–3 outputs
Practice/Lab khác
unrelated repository configuration
```

Nếu cần thay đổi upstream artifact:

```text
STOP
→ explain reason
→ assess impact
→ wait for Human approval
```

---

## 9. Approved Scientific Parameters

Exercise 4 phải dùng:

```text
Dataset: AirPassengers
Frequency: monthly
Missing detection: isna().sum()
Treatment method 1: forward-fill
Treatment method 2: time interpolation
Interpolation method: time
Interpolation limit_area: inside
Missing positions: identical across methods
Ground truth: preserved before masking
Primary outlier evidence: decomposition residual
Total masked observations: 6
Isolated timestamps: 1952-03, 1954-11, 1959-04
Consecutive block: 1956-06 through 1956-08
Reconstruction summary metric: MAE on masked positions only
Outlier scoring formula: IQR fences on log-STL residual
Outlier multiplier: 1.5
Automatic outlier removal: NO
Model training: NO
```

Time interpolation trong Exercise 4 là:

```text
data-quality reconstruction experiment
```

không được mặc định coi là forecasting-safe preprocessing.

---

## 10. Sequential Execution Steps

### Step 1 — Verify Upstream Dependencies

Xác minh:

```text
validated AirPassengers input exists
Exercise 3 residual exists nếu được dùng
locked parameters match this plan
```

Nếu chưa đủ:

```text
STOP
```

---

### Step 2 — Verify Repository Context

Xác minh:

```text
Practice_1 root
required rules
Exercise 4 specification
master initialization plan
current execution state
```

Validation:

```text
no unresolved rule conflict
Exercise 4 before-process plan approved
```

---

### Step 3 — Load Validated Original Series

Dùng reusable data loader/validator.

Sau load:

```text
inspect shape
inspect time range
verify chronology
verify monthly frequency
```

Không sửa raw data.

---

### Step 4 — Check Existing Missing Values

Dùng:

```text
isna().sum()
```

Ghi nhận missing count ban đầu.

Không tạo giả lập missing trước bước này.

---

### Step 5 — Create Working Copy

Tạo working copy riêng cho experiment.

```text
raw/original series
→ unchanged

working series
→ masking and treatment only
```

---

### Step 6 — Preserve Ground Truth

Trước masking:

```text
record locked missing positions
save true values at those positions
save timestamps
```

Phải verify ground truth record trước khi tiếp tục.

Nếu true values chưa được lưu:

```text
STOP
```

---

### Step 7 — Create Simulated Missing Values

Mask đúng locked positions:

```text
observed value → NaN
```

Không xóa row hoặc timestamp.

Sau masking:

```text
verify missing count
verify positions
verify timestamps unchanged
```

Output figure:

```text
outputs/figures/10_missing_values_simulation.png
```

---

### Step 8 — Apply Forward-Fill

Tạo copy riêng:

```text
forward_fill_series
```

Áp dụng forward-fill.

Không overwrite masked working series.

Sau execution:

```text
verify masked positions reconstructed
verify unrelated positions unchanged
```

---

### Step 9 — Apply Time Interpolation

Tạo copy riêng:

```text
interpolation_series
```

Áp dụng:

```text
Series.interpolate(method="time", limit_area="inside")
```

Không extrapolate ở boundary.

Sau execution:

```text
verify masked positions reconstructed
verify timestamps preserved
verify unrelated positions unchanged
```

---

### Step 10 — Compare Reconstruction Methods

Tại đúng masked positions, tạo comparison:

```text
timestamp
true_value
forward_fill_value
interpolation_value
forward_fill_absolute_error
interpolation_absolute_error
```

Tính MAE riêng cho forward-fill và interpolation:

```text
MAE = mean absolute error on the six masked positions only
```

Không tính metric toàn bộ series để đánh giá reconstruction.

Output:

```text
outputs/results/missing_value_comparison.csv
```

---

### Step 11 — Plot Missing-Treatment Comparison

Tạo:

```text
outputs/figures/11_missing_treatment_comparison.png
```

Figure phải cho phép quan sát:

```text
original values
masked locations
forward-fill reconstruction
interpolation reconstruction
```

Sau khi tạo:

```text
inspect actual figure
```

---

### Step 12 — Run Outlier Detection

Sử dụng locked outlier protocol.

Project ưu tiên evidence từ:

```text
STL decomposition residual
```

Phải dùng:

```text
IQR multiplier = 1.5
Q1/Q3 fences on the log-STL residual
```

Không tự đổi threshold trong lúc chạy.

Nếu Exercise 3 residual chưa validate:

```text
STOP
```

---

### Step 13 — Create Outlier Candidate Table

Dự kiến lưu:

```text
outputs/results/outlier_candidates.csv
```

Cột có thể gồm:

```text
timestamp
observed_value
residual_log
q1
q3
iqr
lower_fence
upper_fence
flag
```

Phải verify:

```text
timestamp alignment
score calculation
flag count
```

---

### Step 14 — Inspect Outlier Candidates

Mỗi candidate phải được đối chiếu với:

```text
original series
timestamp context
seasonal pattern
decomposition residual
```

Không tự động kết luận:

```text
flagged point = true anomaly
```

Không tự động xóa hoặc replace outlier.

---

### Step 15 — Plot Outlier Analysis

Tạo:

```text
outputs/figures/12_outlier_analysis.png
```

Figure phải hiển thị rõ potential outliers trong context của series hoặc residual.

Sau khi tạo:

```text
inspect actual figure
```

---

### Step 16 — Answer Interpretation Questions

Phải trả lời:

```text
1. Dataset gốc có missing values không?
2. Có bao nhiêu missing values được tạo giả lập?
3. Forward-fill reconstruction như thế nào?
4. Time interpolation reconstruction như thế nào?
5. Method nào có reconstruction error thấp hơn trong experiment?
6. Có case nào forward-fill tốt hơn không?
7. Có case nào interpolation tốt hơn không?
8. Method nào thay đổi hình dạng chuỗi rõ hơn?
9. Điểm nào được flag là potential outlier?
10. Flagged point có thể chỉ là seasonal peak không?
11. Residual giúp phân biệt outlier với seasonality như thế nào?
12. Có nên tự động xóa outlier không? Vì sao?
```

Không viết kết luận trước actual execution.

---

### Step 17 — Validate Exercise Outputs

Xác minh:

```text
10_missing_values_simulation.png exists and is readable
11_missing_treatment_comparison.png exists and is readable
12_outlier_analysis.png exists and is readable
missing_value_comparison.csv consistent
outlier_candidates.csv consistent
interpretation matches actual evidence
raw data unchanged
```

---

### Step 18 — Update State

Sau khi Exercise 4 pass validation:

```text
update current status
append concise progress log
```

Không đánh dấu `COMPLETED` nếu còn blocker.

---

## 11. Validation Checklist

```text
[ ] Required documents were read
[ ] Upstream validated AirPassengers input confirmed
[ ] Exercise 3 log-STL residual confirmed
[ ] Locked masking and outlier parameters verified
[ ] Raw data unchanged
[ ] Existing missing count recorded
[ ] Working copy created
[ ] True values preserved before masking
[ ] Missing positions recorded
[ ] Same positions used for both methods
[ ] Missing count after masking verified
[ ] Forward-fill completed
[ ] Time interpolation completed
[ ] Interpolation method = time and limit_area = inside
[ ] Reconstruction compared only at masked positions
[ ] MAE computed separately for both methods on the six masked positions only
[ ] Comparison file created and inspected
[ ] Approved outlier protocol used
[ ] Outlier candidates inspected
[ ] No automatic outlier deletion performed
[ ] Before/after figures created and inspected
[ ] Interpretation based on actual evidence
[ ] No model training performed
[ ] No unrelated file modified
```

---

## 12. Expected Outputs

### Required Figures

```text
outputs/figures/10_missing_values_simulation.png
outputs/figures/11_missing_treatment_comparison.png
outputs/figures/12_outlier_analysis.png
```

### Required / Recommended Results

```text
outputs/results/missing_value_comparison.csv
outputs/results/outlier_candidates.csv
```

### Narrative Evidence

Interpretation phải bao gồm:

```text
existing missing status
reconstruction comparison
method-specific strengths/weaknesses
outlier candidate discussion
seasonal-peak vs anomaly distinction
```

---

## 13. Stop Conditions

Agent phải dừng khi:

```text
Exercise 4 plan chưa được approve
required document missing
rule conflict
validated AirPassengers input chưa sẵn sàng
locked timestamp không tồn tại trong validated monthly index
true values chưa được lưu trước masking
missing positions khác nhau giữa methods
timestamp bị thay đổi
forward-fill fail
time interpolation fail
Exercise 3 residual chưa validate nhưng đang được dùng
outlier protocol không khớp IQR multiplier 1.5 trên log-STL residual
output file inconsistent
raw data bị thay đổi
scientific parameter cần thay đổi
dependency mới cần thêm
unrelated file cần sửa
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

## 14. Completion Gate

Exercise 4 chỉ được xem là complete khi:

```text
validated input used
AND missing experiment reproducible
AND true values preserved
AND both treatment methods validated
AND reconstruction comparison validated
AND outlier analysis validated
AND figures inspected
AND interpretation questions answered
AND raw data unchanged
AND no unresolved blocking issue
```

---

## 15. Approval Gate

Trạng thái hiện tại:

```text
EXERCISE_04_BEFORE_PROCESS_CREATED=true
EXERCISE_04_BEFORE_PROCESS_REVIEWED=false
EXERCISE_04_BEFORE_PROCESS_APPROVED=false
EXERCISE_04_IMPLEMENTATION_AUTHORIZED=false
```

Agent không được code Exercise 4 khi:

```text
EXERCISE_04_IMPLEMENTATION_AUTHORIZED=false
```

Sau khi Human approve:

```text
EXERCISE_04_BEFORE_PROCESS_REVIEWED=true
EXERCISE_04_BEFORE_PROCESS_APPROVED=true
EXERCISE_04_IMPLEMENTATION_AUTHORIZED=true
```

---

## 16. Agent Execution Rule

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
tự đổi locked missing positions
tự đổi masked-observation count
tự đổi outlier threshold
tự đổi scoring formula
tự sửa raw data
tự xóa outlier
tự dùng interpolation như forecasting-safe preprocessing
tự sửa upstream validated output
tự thêm model
tự bỏ qua validation
tự claim completion
```
