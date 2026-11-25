# EXERCISE 01 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_01
Topic: EDA and Time-Series Preparation
Plan type: Exercise Before-Process Plan
Dataset: Monthly Retail Sales
Status: APPROVED
Implementation authorized: YES
Execution result: COMPLETED
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_01_execution.md
```

Plan và implementation scope của Exercise 1 đã được Human phê duyệt. Mọi lần chạy lại
phải tiếp tục tuân thủ đúng scope, validation và stop conditions trong file này.

## 2. Objective

- xác minh input `datasets/raw/a10.csv`;
- chuyển cột `date` thành time index;
- kiểm tra schema, time index, monthly frequency và data quality;
- tạo original-series plot và EDA observations;
- xác định chronological train/test boundary khoảng 80/20;
- seal test set cho đến Exercise 5;
- không chạy ADF, differencing, model training hoặc forecast;
- không thay đổi raw dataset.

## 3. Required Documents

```text
working_rule.md
.agents/RULES_INDEX.md
.agents/rules/GENERAL_RULES.md
.agents/rules/CODE_RULES.md
.agents/rules/TIME_SERIES_RULES.md
.agents/workflows/WORKFLOW.md
total_practice/Practice_2/README.md
total_practice/Practice_2/docs/rules/architecture_rule.md
total_practice/Practice_2/docs/rules/rule_code.md
total_practice/Practice_2/docs/plans/project_overview.md
total_practice/Practice_2/docs/plans/plan_overview.md
total_practice/Practice_2/docs/exercise_details/exercise_01_eda_time_series_preparation.md
total_practice/Practice_2/docs/status/current_status.md nếu đã tồn tại
```

Nếu thiếu tài liệu hoặc có conflict: `STOP → report missing/conflict → chờ Human quyết định`.

## 4. Input

```text
Raw file: datasets/raw/a10.csv
Time column: date
Target column: value
Frequency: monthly
```

Các check tối thiểu: readable file, schema, date parsing, chronological order,
monthly frequency, missing values, duplicate timestamps, missing monthly intervals,
observation count và date range.

## 5. Files Allowed to Create or Modify

```text
src/practice_2/data/
src/practice_2/analysis/
src/practice_2/visualization/
notebooks/
outputs/figures/
outputs/results/
tests/
docs/status/
docs/logs/
docs/error_analysis/
docs/fix_plans/
```

Không tạo duplicate module nếu owner tương đương đã tồn tại.

## 6. Files Not to Modify

```text
datasets/raw/a10.csv
working_rule.md
.agents/ rules
approved scoped rule files
approved project_overview.md
approved plan_overview.md
Exercise 2–6 specifications nếu có
Practice/Lab khác
unrelated repository configuration
```

Nếu cần sửa ngoài scope: `STOP → explain reason → propose change → wait for approval`.

## 7. Scientific Parameters

```text
Dataset: Monthly Retail Sales
Time column: date
Target column: value
Frequency: monthly
Chronological train proportion: approximately 80%
Chronological test proportion: approximately 20%
Shuffle: NO
Model training: NO
Forecast generation: NO
ADF and differencing: NOT IN THIS EXERCISE
```

Boundary thực tế phải được ghi bằng timestamp và observation count sau validation.

## 8. Sequential Execution Steps

### Step 1 — Verify Repository Context

Xác minh Practice_2 root, folder structure, required docs, active rules và current execution state.

### Step 2 — Verify Dataset Availability

Xác minh `datasets/raw/a10.csv` tồn tại và ghi nhận source/path, schema, data types,
observation count, date range, timestamp meaning và monthly frequency. Không thay raw file.

### Step 3 — Load Dataset

Dùng reusable loader nếu đã tồn tại; nếu chưa, tạo logic tối thiểu trong
`src/practice_2/data/`. Loader phải preserve raw values, parse date trên working object
và return validated structure.

### Step 4 — Convert Date to Time Index and Validate Data Quality

Parse `date`, set `date` làm `DatetimeIndex`, sau đó kiểm tra chronological order, monthly frequency, missing values, duplicate
timestamps, missing monthly intervals và date range. Nếu có unresolved issue thì STOP.

### Step 5 — Create Original-Series Plot

Tạo và inspect:

```text
outputs/figures/01_original_time_series.png
```

Plot phải có title, time axis, observed-value axis và readable labels.

### Step 6 — Record EDA Questions and Observations

Sau actual checks và figure inspection, trả lời: chuỗi có xu hướng không, có dấu hiệu
mùa vụ không, và chuỗi có khả năng dừng không dựa trên EDA. Ghi variance và visual
limitations. Không kết luận ADF, `d`, `p`, `q` hoặc model.

### Step 7 — Establish Chronological Holdout Boundary

Tạo approximately 80/20 split theo thời gian, không shuffle. Ghi train/test start,
end, counts và downstream forecast horizon. Đánh dấu test set sealed; E02–E04 chỉ dùng train.

### Step 8 — Validate and Update State

Inspect required outputs, xác nhận boundary và sealed test set, cập nhật current status
và append concise progress log. Không đánh dấu complete nếu còn blocker.

## 9. Validation Checklist

```text
[ ] Required documents were read
[ ] Dataset source/path verified
[ ] Raw data unchanged
[ ] Dataset loaded successfully
[ ] date parsed correctly
[ ] date được chuyển thành DatetimeIndex
[ ] Chronological order verified
[ ] Monthly frequency verified
[ ] Missing values checked
[ ] Duplicate timestamps checked
[ ] Missing monthly intervals checked
[ ] Observation count and date range recorded
[ ] Original-series plot created and inspected
[ ] Trend observation documented
[ ] Seasonality observation documented
[ ] Initial stationarity assessment documented
[ ] Train/test boundary created chronologically
[ ] No shuffle performed
[ ] Test set sealed for E02–E04
[ ] No model training or forecast performed
[ ] No unrelated file modified
```

## 10. Expected Outputs

```text
outputs/figures/01_original_time_series.png
outputs/results/dataset_validation.csv
outputs/results/train_test_boundary.csv
```

Required narrative evidence: validated schema/time index, EDA observations và sealed boundary.

## 11. Stop Conditions

Agent phải dừng khi plan chưa được approve, required document missing, rule conflict,
schema/date/frequency unexpected, duplicate hoặc missing interval chưa giải quyết,
boundary không hợp lệ, plot không inspect được, dependency mới cần thêm, unrelated file
cần sửa hoặc raw data bị thay đổi.

Khi dừng:

```text
1. Không tiếp tục step sau.
2. Ghi observed và expected behavior.
3. Ghi evidence và impact.
4. Đề xuất next action.
5. Chờ Human approval.
```

## 12. Completion Gate

```text
input validated
AND original series inspected
AND EDA observations documented
AND chronological train/test boundary validated
AND test set sealed
AND required output inspected
AND raw data unchanged
AND no unresolved blocking issue
```

## 13. Approval Gate

```text
EXERCISE_01_BEFORE_PROCESS_CREATED=true
EXERCISE_01_BEFORE_PROCESS_REVIEWED=true
EXERCISE_01_BEFORE_PROCESS_APPROVED=true
EXERCISE_01_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_01_IMPLEMENTED=true
EXERCISE_01_VALIDATED=true
EXERCISE_01_COMPLETED=true
```

Actual result và runtime state phải được đọc từ execution log và current status;
before-process plan không thay thế hai evidence owner này.

## 14. Agent Execution Rule

Sau approval:

```text
one step → execute → run → verify → report → next step
```

Không được tự đổi dataset, shuffle dữ liệu, chạy ADF trong E01, thêm forecasting model,
sửa raw data, sửa approved specification, bỏ qua validation hoặc claim completion.
