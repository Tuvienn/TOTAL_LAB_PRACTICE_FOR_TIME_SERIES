# EXERCISE 03 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_03
Topic: Differencing and ADF Retest
Plan type: Exercise Before-Process Plan
Dataset: Monthly Retail Sales
Status: CONFIRMED
Implementation authorized: YES
Execution result: EXECUTED_AND_VALIDATED
Scientific result: STATIONARITY_SUPPORTED_ON_LOG_FIRST_DIFFERENCE
Downstream gate: OPEN_FOR_E04_REVIEW
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_03_execution.md
```

Plan và implementation scope của Exercise 3 đã được xác nhận. Mọi lần chạy lại
phải tiếp tục tuân thủ đúng scope, validation và stop conditions trong file này.

## 2. Objective

- xác minh E02 ADF result và original training series;
- giữ raw first-difference failure làm evidence;
- áp dụng natural log và regular first difference trên training working copy;
- vẽ transformed differenced series;
- chạy ADF remediation với `α = 0.05`;
- kết luận stationarity trên transformed scale;
- xác định transformation và `d` từ actual evidence;
- không sửa raw data, không dùng test set và không fit model.

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
total_practice/Practice_2/docs/plans/plan_overview.md
total_practice/Practice_2/docs/exercise_details/exercise_03_differencing_adf_retest.md
total_practice/Practice_2/docs/plans/exercise_02_before_process.md
total_practice/Practice_2/docs/status/current_status.md nếu đã tồn tại
```

Nếu thiếu E02 evidence hoặc có conflict: `STOP → report issue → chờ xử lý xung đột`.

## 4. Input

```text
Original training series from Exercise 1
ADF result from Exercise 2
Test set: sealed and excluded
Confirmed remediation transformation: natural logarithm
Regular differencing order: 1
Significance level α: 0.05
```

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

Không tạo duplicate differencing hoặc ADF function nếu owner tương đương đã tồn tại.

## 6. Files Not to Modify

```text
datasets/raw/a10.csv
working_rule.md
.agents/ rules
confirmed scoped rule files
Exercise 1 và Exercise 2 validated outputs
Exercise 4–6 specifications nếu có
Practice/Lab khác
unrelated configuration
```

Nếu cần sửa ngoài scope: `STOP → explain reason → propose change → chờ xác nhận`.

## 7. Scientific Parameters

```text
Transformation: natural logarithm
Regular differencing order tested: 1
Seasonal differencing: not introduced
ADF significance level α: 0.05
Regression: constant (`regression="c"`)
Lag selection: AIC (`autolag="AIC"`)
Input: original training series
Test set usage: NO
Model training: NO
Forecast generation: NO
```

## 8. Sequential Execution Steps

### Step 1 — Verify Upstream Dependency

Xác minh E02 đã có original-series ADF result, training boundary và sealed test set.
Nếu chưa đủ evidence thì STOP.

### Step 2 — Preserve Raw First-Difference Evidence

Xác minh raw first-difference attempt và ADF blocker hiện tại; không trình bày attempt
này như stationary evidence.

### Step 3 — Create Log First-Differenced Working Series

Xác minh training values đều dương, áp dụng natural log rồi regular first difference.
Không ghi transformation hoặc xử lý `NaN` ngược vào raw file.

### Step 4 — Plot Transformed Differenced Series

Tạo và inspect:

```text
outputs/figures/02_first_differenced_series.png
outputs/figures/02_log_first_differenced_series.png
```

### Step 5 — Run ADF Remediation

Chạy ADF trên log first-differenced training series với `α = 0.05`, `regression="c"`
và `autolag="AIC"`; ghi statistic, p-value, critical values, used lag và observations
khi output cung cấp.

### Step 6 — Decide Stationarity, Transformation and d

```text
p-value ≤ 0.05 → evidence supports stationarity → transformation=natural_log, d=1
p-value > 0.05 → transformation and selected_d = REVIEW_REQUIRED → handoff đóng
```

Nếu scientific handoff đóng, phải STOP trước E04 và report issue. Không tự tăng
differencing hoặc đổi protocol nếu chưa được approve.

### Step 7 — Save and Inspect Outputs

```text
outputs/results/adf_differenced_series.csv
outputs/results/adf_differenced_critical_values.csv
outputs/results/adf_log_first_differenced_series.csv
outputs/results/adf_log_first_differenced_critical_values.csv
outputs/results/e03_transformation_comparison.csv
outputs/results/differencing_decision.csv
```

Inspect plots, tables và narrative answer cho hai câu hỏi chính của bài.

### Step 8 — Update State

Sau khi technical execution validation hoàn thành, cập nhật current status và execution
log bằng actual outcome. Scientific handoff chỉ được mở khi stationarity và `d` có evidence.

## 9. Validation Checklist

```text
[x] Required documents were read
[x] E02 ADF result validated
[x] Original training series used
[x] Raw first-difference failure preserved as evidence
[x] Training values are positive before natural log
[x] Log transformation and first differencing performed on training working copy
[x] Raw data unchanged
[x] Transformed differenced plot created and inspected
[x] ADF remediation executed on log first-differenced train
[x] α = 0.05
[x] Regression option `c` recorded
[x] Autolag setting `AIC` recorded
[x] ADF statistic, p-value and critical values recorded
[x] Test set excluded
[x] Analysis scale recorded
[x] Stationarity conclusion based on actual remediation result
[x] Transformation and `d` selected from actual evidence
[x] No model fitting or forecast
[x] No unrelated file modified
```

## 10. Expected Outputs

```text
outputs/figures/02_first_differenced_series.png
outputs/figures/02_log_first_differenced_series.png
outputs/results/adf_differenced_series.csv
outputs/results/adf_differenced_critical_values.csv
outputs/results/adf_log_first_differenced_series.csv
outputs/results/adf_log_first_differenced_critical_values.csv
outputs/results/e03_transformation_comparison.csv
outputs/results/differencing_decision.csv
```

Required narrative evidence: stationarity after differencing và `d` decision. Nếu
evidence chưa đủ để chọn một giá trị số, `REVIEW_REQUIRED` là kết quả hợp lệ.

## 11. Stop Conditions

Quy trình phải dừng khi E02 evidence thiếu, input sai, test leakage xảy ra, giá trị train
không dương, log/differencing hoặc ADF fail, remediation chưa stationary,
parameter/scope cần đổi, dependency mới cần thêm hoặc raw/unrelated file cần sửa.

Khi dừng:

```text
1. Không tiếp tục step sau.
2. Ghi observed và expected behavior.
3. Ghi evidence và impact.
4. Đề xuất next action.
5. Chờ xác nhận.
```

## 12. Execution Completion và Scientific Handoff

### 12.1. Technical Execution Gate

```text
raw failed evidence preserved
AND log first-differenced series created
AND plot inspected
AND ADF remediation executed
AND stationarity conclusion documented
AND d decision recorded from actual evidence
```

Technical execution có thể hoàn thành dù kết quả khoa học tạo blocker.

### 12.2. Scientific Handoff Gate

Chỉ mở handoff sang Exercise 4 khi:

```text
stationary log first-differenced training series supported by evidence
AND transformation and d selected with evidence
AND no unresolved scientific blocker
```

Nếu gate chưa đạt, `selected_d = REVIEW_REQUIRED`, Exercise 3 chưa complete và
Exercise 4 không được bắt đầu.

## 13. confirmation gate

```text
EXERCISE_03_BEFORE_PROCESS_CREATED=true
EXERCISE_03_BEFORE_PROCESS_REVIEWED=true
EXERCISE_03_BEFORE_PROCESS_CONFIRMED=true
EXERCISE_03_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_03_IMPLEMENTED=true
EXERCISE_03_VALIDATED=true
EXERCISE_03_COMPLETED=true
EXERCISE_03_BLOCKED_BY_SCIENTIFIC_RESULT=false
EXERCISE_04_HANDOFF_OPEN=false
```

Actual result và runtime state phải được đọc từ execution log và current status;
before-process plan không thay thế hai evidence owner này.

## 14. workflow Execution Rule

Sau confirmation:

```text
one step → execute → run → verify → report → next step
```

Không được tự đổi differencing order, alpha, dùng test set, tăng `d`, sửa raw data,
bỏ qua validation hoặc claim completion.
