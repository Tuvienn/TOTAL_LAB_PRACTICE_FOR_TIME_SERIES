# EXERCISE 03 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_03
Topic: Differencing and ADF Retest
Plan type: Exercise Before-Process Plan
Dataset: Monthly Retail Sales
Status: DRAFT_FOR_HUMAN_REVIEW
Implementation authorized: NO
```

Agent chỉ được bắt đầu code Exercise 3 sau khi Human approve file này và implementation scope tương ứng.

## 2. Objective

- xác minh E02 ADF result và original training series;
- thực hiện sai phân bậc 1 trên working copy;
- vẽ chuỗi sau sai phân;
- chạy ADF lần 2 với `α = 0.05`;
- kết luận stationarity sau sai phân;
- xác định `d` từ actual evidence;
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

Nếu thiếu E02 evidence hoặc có conflict: `STOP → report issue → chờ Human quyết định`.

## 4. Input

```text
Original training series from Exercise 1
ADF result from Exercise 2
Test set: sealed and excluded
First differencing order: 1
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
approved scoped rule files
Exercise 1 và Exercise 2 validated outputs
Exercise 4–6 specifications nếu có
Practice/Lab khác
unrelated configuration
```

Nếu cần sửa ngoài scope: `STOP → explain reason → propose change → wait for approval`.

## 7. Scientific Parameters

```text
Differencing order tested: 1
ADF significance level α: 0.05
Input: original training series
Test set usage: NO
Model training: NO
Forecast generation: NO
```

## 8. Sequential Execution Steps

### Step 1 — Verify Upstream Dependency

Xác minh E02 đã có original-series ADF result, training boundary và sealed test set.
Nếu chưa đủ evidence thì STOP.

### Step 2 — Create First-Differenced Working Series

Áp dụng first difference trên original training series working copy. Không ghi kết quả
hoặc xử lý `NaN` ngược vào raw file.

### Step 3 — Plot Differenced Series

Tạo và inspect:

```text
outputs/figures/02_first_differenced_series.png
```

### Step 4 — Run ADF Retest

Chạy ADF lần 2 trên differenced training series với `α = 0.05`; ghi statistic, p-value,
critical values, used lag và observations khi output cung cấp.

### Step 5 — Decide Stationarity and d

```text
p-value ≤ 0.05 → evidence supports stationarity → d = 1
p-value > 0.05 → first difference chưa đủ evidence → STOP và report issue
```

Không tự tăng differencing hoặc đổi protocol nếu chưa được approve.

### Step 6 — Save and Inspect Outputs

```text
outputs/results/adf_differenced_series.csv
outputs/results/differencing_decision.csv
```

Inspect plots, tables và narrative answer cho hai câu hỏi chính của bài.

### Step 7 — Update State

Chỉ sau khi validation pass mới cập nhật current status và execution log.

## 9. Validation Checklist

```text
[ ] Required documents were read
[ ] E02 ADF result validated
[ ] Original training series used
[ ] First differencing performed on working copy
[ ] Raw data unchanged
[ ] Differenced plot created and inspected
[ ] ADF retest executed
[ ] α = 0.05
[ ] ADF statistic, p-value and critical values recorded
[ ] Test set excluded
[ ] Stationarity conclusion based on actual result
[ ] d justified from evidence
[ ] No model fitting or forecast
[ ] No unrelated file modified
```

## 10. Expected Outputs

```text
outputs/figures/02_first_differenced_series.png
outputs/results/adf_differenced_series.csv
outputs/results/differencing_decision.csv
```

Required narrative evidence: stationarity after differencing và selected `d`.

## 11. Stop Conditions

Agent phải dừng khi E02 evidence thiếu, input sai, test leakage xảy ra, differencing
hoặc ADF fail, first difference chưa stationary, parameter/scope cần đổi, dependency
mới cần thêm hoặc raw/unrelated file cần sửa.

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
first differenced series created
AND plot inspected
AND ADF retest executed
AND stationarity conclusion documented
AND d justified by actual evidence
AND no unresolved blocking issue
```

## 13. Approval Gate

```text
EXERCISE_03_BEFORE_PROCESS_CREATED=true
EXERCISE_03_BEFORE_PROCESS_REVIEWED=false
EXERCISE_03_BEFORE_PROCESS_APPROVED=false
EXERCISE_03_IMPLEMENTATION_AUTHORIZED=false
EXERCISE_03_IMPLEMENTED=false
EXERCISE_03_VALIDATED=false
```

Agent không được code khi `EXERCISE_03_IMPLEMENTATION_AUTHORIZED=false`.

## 14. Agent Execution Rule

Sau approval:

```text
one step → execute → run → verify → report → next step
```

Không được tự đổi differencing order, alpha, dùng test set, tăng `d`, sửa raw data,
bỏ qua validation hoặc claim completion.
