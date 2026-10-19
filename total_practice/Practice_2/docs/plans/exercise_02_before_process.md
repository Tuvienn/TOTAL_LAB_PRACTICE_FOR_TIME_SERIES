# EXERCISE 02 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_02
Topic: ADF on Original Series
Plan type: Exercise Before-Process Plan
Dataset: Monthly Retail Sales
Status: APPROVED
Implementation authorized: YES
Execution result: COMPLETED
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_02_execution.md
```

Plan và implementation scope của Exercise 2 đã được Human phê duyệt. Mọi lần chạy lại
phải tiếp tục tuân thủ đúng scope, validation và stop conditions trong file này.

## 2. Objective

- xác minh E01 handoff và sealed test boundary;
- chạy ADF trên original training series;
- ghi statistic, p-value, critical values và metadata khi có;
- giải thích `H₀`, p-value và stationarity decision;
- lưu actual result;
- không differencing, không ACF/PACF và không fit model.

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
total_practice/Practice_2/docs/exercise_details/exercise_02_adf_original_series.md
total_practice/Practice_2/docs/plans/exercise_01_before_process.md
total_practice/Practice_2/docs/status/current_status.md nếu đã tồn tại
```

Nếu thiếu tài liệu, E01 evidence hoặc có conflict: `STOP → report issue → chờ Human quyết định`.

## 4. Input

```text
Original untransformed training series from Exercise 1
Dataset: datasets/raw/a10.csv
Time column: date
Target column: value
Significance level α: 0.05
Test set: sealed and excluded
```

## 5. Files Allowed to Create or Modify

```text
src/practice_2/analysis/
notebooks/
outputs/results/
tests/
docs/status/
docs/logs/
docs/error_analysis/
docs/fix_plans/
```

Không tạo duplicate ADF logic nếu reusable owner tương đương đã tồn tại.

## 6. Files Not to Modify

```text
datasets/raw/a10.csv
working_rule.md
.agents/ rules
approved scoped rule files
Exercise 1 validated outputs
approved Exercise 1 documents
Exercise 3–6 specifications nếu có
Practice/Lab khác
unrelated configuration
```

Nếu cần sửa ngoài scope: `STOP → explain reason → propose change → wait for approval`.

## 7. Scientific Parameters

```text
Test: Augmented Dickey-Fuller
Input: original training series
Significance level α: 0.05
Regression: constant (`regression="c"`)
Lag selection: AIC (`autolag="AIC"`)
Test set usage: NO
Differencing: NO
Model training: NO
Forecast generation: NO
```

## 8. Sequential Execution Steps

### Step 1 — Verify Upstream Dependency

Xác minh E01 đã cung cấp validated original training series, time index và sealed test boundary.
Nếu chưa đủ evidence thì STOP.

### Step 2 — Verify Repository Context

Xác minh Practice_2 root, active rules, Exercise 2 specification, approved plan state và current status.

### Step 3 — Prepare ADF Input

Load original untransformed training series từ validated working representation. Kiểm tra test
observations không xuất hiện trong input và không thực hiện differencing.

### Step 4 — Execute ADF

Chạy ADF với `α = 0.05`, `regression="c"` và `autolag="AIC"`. Ghi statistic,
p-value, critical values, used lag và used observations khi output cung cấp.

### Step 5 — Apply Decision Rule

```text
p-value ≤ 0.05 → reject H₀ → evidence supports stationarity
p-value > 0.05 → fail to reject H₀ → insufficient evidence of stationarity
```

Giải thích H₀ là unit-root hypothesis và không biến “fail to reject” thành proof tuyệt đối.

### Step 6 — Save and Inspect Output

Lưu actual result tại:

```text
outputs/results/adf_original_series.csv
outputs/results/adf_original_critical_values.csv
```

Inspect result table và narrative answer cho ba câu hỏi: H₀, p-value và chuỗi có dừng không.

### Step 7 — Update State

Chỉ sau khi output pass validation mới cập nhật current status và execution log. Không đánh dấu complete nếu còn blocker.

## 9. Validation Checklist

```text
[ ] Required documents were read
[ ] Exercise 1 handoff validated
[ ] Original training series used
[ ] Test set excluded
[ ] ADF executed successfully
[ ] Significance level α = 0.05
[ ] Regression option `c` recorded
[ ] Autolag setting `AIC` recorded
[ ] ADF statistic recorded
[ ] p-value recorded
[ ] Critical values recorded
[ ] Used lag/observations recorded when available
[ ] H₀ explained correctly
[ ] p-value interpreted correctly
[ ] Stationarity conclusion based on actual output
[ ] No differencing or model fitting performed
[ ] No unrelated file modified
```

## 10. Expected Outputs

```text
outputs/results/adf_original_series.csv
outputs/results/adf_original_critical_values.csv
```

Required narrative evidence:

```text
H₀ explanation
p-value explanation
stationary/non-stationary conclusion
```

## 11. Stop Conditions

Agent phải dừng khi E01 handoff thiếu, test leakage xảy ra, input không phải original
training series, ADF fail, output thiếu statistic/p-value/critical values, parameter cần
đổi, dependency mới cần thêm hoặc unrelated file cần sửa.

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
original training series validated
AND ADF executed
AND statistic/p-value/critical values recorded
AND H₀ and p-value explained
AND stationarity conclusion documented
AND output inspected
AND no unresolved blocking issue
```

## 13. Approval Gate

```text
EXERCISE_02_BEFORE_PROCESS_CREATED=true
EXERCISE_02_BEFORE_PROCESS_REVIEWED=true
EXERCISE_02_BEFORE_PROCESS_APPROVED=true
EXERCISE_02_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_02_IMPLEMENTED=true
EXERCISE_02_VALIDATED=true
EXERCISE_02_COMPLETED=true
```

Actual result và runtime state phải được đọc từ execution log và current status;
before-process plan không thay thế hai evidence owner này.

## 14. Agent Execution Rule

Sau approval:

```text
one step → execute → run → verify → report → next step
```

Không được tự đổi alpha, dùng test set, differencing trước ADF, fabricate result, bỏ qua
validation hoặc claim completion.
