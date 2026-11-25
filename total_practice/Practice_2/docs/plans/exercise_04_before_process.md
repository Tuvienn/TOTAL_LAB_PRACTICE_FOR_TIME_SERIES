# EXERCISE 04 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_04
Topic: ACF/PACF and ARIMA Candidate Identification
Plan type: Exercise Before-Process Plan
Dataset: Monthly Retail Sales
Status: APPROVED_AND_COMPLETED
Implementation authorized: YES
Upstream handoff: EXERCISE_03_COMPLETED_WITH_LOG_TRANSFORMATION
Downstream gate: CLOSED_PENDING_E04_VALIDATION
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_04_execution.md
```

File này chỉ mô tả kế hoạch chi tiết cho E04. Việc tạo plan không cho phép triển khai
code, chỉnh notebook, tạo output hoặc mở handoff sang E05 khi chưa có Human approval.

## 2. Objective

- phân tích ACF và PACF của stationary training series do E03 bàn giao;
- xác định các lag ngắn và lag mùa vụ đáng chú ý;
- đề xuất candidate `p` và `q` từ actual evidence;
- kế thừa natural-log transformation và regular `d = 1` từ E03;
- xác định từ một đến hai ARIMA candidates để bàn giao cho E05;
- không fit model, forecast, mở test set hoặc triển khai SARIMA trong E04.

## 3. Required Documents

```text
working_rule.md
AGENTS.md
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
total_practice/Practice_2/docs/exercise_details/exercise_03_differencing_adf_retest.md
total_practice/Practice_2/docs/plans/exercise_03_before_process.md
total_practice/Practice_2/docs/logs/exercise_03_execution.md
total_practice/Practice_2/docs/status/current_status.md
```

Nếu thiếu tài liệu, upstream evidence hoặc có conflict:
`STOP → report issue → chờ Human quyết định`.

## 4. Upstream Input Contract

```text
Source series: original training series from E01
Original training observations: 163
Test observations: 41, sealed and excluded
Transformation: natural logarithm
Regular differencing order: 1
E04 analysis series: log_first_differenced_training
Expected transformed observations: 162
Remaining missing values: 0
E03 ADF statistic: approximately -3.659486
E03 p-value: approximately 0.004720
E03 decision: reject H0
Stationarity supported: true on transformed training scale
```

E04 không được sử dụng `df_diff1` từ `Practice2_latest.ipynb`, full series, raw
first-differenced series hoặc bất kỳ test observation nào.

## 5. Scientific Parameters

```text
ACF maximum lag: 36
PACF maximum lag: 36
Confidence level: 95%
Alpha: 0.05
PACF method: ywm
Lag 0: retained technically when required, excluded from p/q interpretation
Seasonal reference lags: 12, 24, 36
Inherited transformation: natural_log
Inherited regular differencing order: d = 1
Candidate count: 1–2
Model fitting: NO
Forecast generation: NO
Test set usage: NO
SARIMA identification: NOT IN E04
```

Ba mươi sáu lag bao phủ ba chu kỳ năm của dữ liệu monthly và vẫn phù hợp với 162
quan sát transformed training. ACF/PACF chỉ cung cấp evidence để đề xuất candidates,
không tự động xác nhận final model.

## 6. Files Allowed to Create or Modify

Sau khi plan được Human phê duyệt, E04 chỉ được phép tạo hoặc cập nhật:

```text
docs/exercise_details/exercise_04_acf_pacf_arima_candidates.md
docs/plans/exercise_04_before_process.md
src/practice_2/analysis/correlation.py
src/practice_2/analysis/__init__.py
src/practice_2/visualization/plots.py
tests/test_exercise_04.py
notebooks/Practice_2_Exercise.ipynb
outputs/figures/03_acf_pacf_log_first_differenced.png
outputs/results/acf_log_first_differenced.csv
outputs/results/pacf_log_first_differenced.csv
outputs/results/arima_candidates.csv
docs/logs/exercise_04_execution.md
docs/status/current_status.md
```

Không tạo duplicate module nếu reusable owner tương đương đã tồn tại.

## 7. Files Not to Modify

```text
datasets/raw/a10.csv
datasets/raw/airline-passengers.csv
working_rule.md
AGENTS.md
.agents/ rules and workflows
approved Practice_2 rule files
E01–E03 validated source logic and result files
historical Practice2_latest.ipynb reference (not present in the current repository)
E05/E06 implementation or documents
README.md
unrelated Practice/Lab files
```

Nếu cần sửa ngoài scope:
`STOP → explain reason and impact → propose scope update → wait for approval`.

## 8. Planned Reusable Logic

### 8.1. Correlation Analysis Owner

Tạo `src/practice_2/analysis/correlation.py` với trách nhiệm:

1. validate series không rỗng và không có missing values;
2. validate `nlags`, `alpha` và PACF method;
3. tính ACF đến lag 36 với confidence interval 95%;
4. tính PACF đến lag 36 bằng `method="ywm"` với confidence interval 95%;
5. tạo machine-readable ACF/PACF tables;
6. đánh dấu lag có confidence interval không chứa 0;
7. không tự động chọn final `p`, `q` hoặc model.

Schema dự kiến:

```text
lag
correlation
ci_lower
ci_upper
significant
```

### 8.2. Visualization Owner

Mở rộng approved visualization owner để tạo một figure gồm:

```text
left panel: ACF
right panel: PACF
```

Figure phải:

- ghi rõ input là log first-differenced training series;
- hiển thị 36 lag và confidence interval 95%;
- ghi rõ PACF method trong metadata hoặc narrative;
- hỗ trợ nhận diện các lag 12, 24 và 36;
- được inspect trước khi viết interpretation.

## 9. Sequential Execution Steps

### Step 1 — Verify Repository and Approval State

Xác minh required documents, E03 completion, E04 plan approval và current status.
Nếu plan chưa được Human phê duyệt thì không triển khai bước tiếp theo.

### Step 2 — Verify E03 Handoff

Tái tạo approved E03 input bằng reusable source logic và xác minh:

```text
train observations = 163
transformed observations = 162
missing values = 0
first transformed timestamp = second training timestamp
last transformed timestamp = last training timestamp
last transformed timestamp < first test timestamp
ADF decision = reject H0 at alpha 0.05
```

Nếu bất kỳ điều kiện nào không đạt thì STOP.

### Step 3 — Compute ACF/PACF Evidence

Tính ACF/PACF trên đúng `log_first_differenced_training` với configuration đã chốt.
Không truy cập test values để tính correlation hoặc chọn candidate.

### Step 4 — Save Machine-Readable Results

Lưu:

```text
outputs/results/acf_log_first_differenced.csv
outputs/results/pacf_log_first_differenced.csv
```

Mỗi output phải chứa lag, correlation, confidence interval và significant flag.

### Step 5 — Create and Inspect Figure

Tạo:

```text
outputs/figures/03_acf_pacf_log_first_differenced.png
```

Inspect actual plot; không viết kết luận từ expected pattern hoặc notebook legacy.

### Step 6 — Interpret Actual Lag Structure

Trả lời từ actual tables và figure:

1. ACF có cutoff, decay hoặc pattern khác không?
2. PACF có cutoff, decay hoặc pattern khác không?
3. Những lag ngắn nào nổi bật?
4. Các lag 12, 24 và 36 có evidence seasonality còn lại không?
5. Evidence hỗ trợ candidate `p/q` nào?

Không dùng một spike đơn lẻ để tuyên bố model chắc chắn đúng.

### Step 7 — Propose ARIMA Candidates

Chọn từ một đến hai candidates sau khi actual evidence được inspect. Candidate phải:

```text
use natural-log analysis scale
inherit d = 1
identify p/q from ACF/PACF evidence
include concise rationale
remain provisional until E05 fitting and diagnostics
```

Lưu bảng:

```text
outputs/results/arima_candidates.csv
```

Schema dự kiến:

```text
candidate
p
d
q
analysis_scale
acf_evidence
pacf_evidence
status
```

### Step 8 — Update Canonical Notebook

Thêm E04 vào `Practice_2_Exercise.ipynb` theo cấu trúc ngắn:

```text
# Exercise 4 — Phân tích ACF/PACF
### 1. Input từ E3
### 2. Biểu đồ ACF/PACF
### 3. Các lag nổi bật
### 4. ARIMA candidates
### 5. Kết luận E04
```

Notebook chỉ trình bày input metadata ngắn, figure, bảng lag cần thiết, candidate
table và kết luận ngắn. Không chép theory, rules hoặc plan vào notebook.

### Step 9 — Run Validation

Chạy targeted tests, full relevant tests và notebook từ clean kernel. Inspect figure,
CSV, notebook output, execution order và absence of errors.

### Step 10 — Update Execution Evidence

Chỉ sau khi validation đạt mới tạo execution log và cập nhật current status bằng
actual result. Không ghi candidate, significant lag hoặc completion state trước execution.

## 10. Test Plan

Tests tối thiểu:

```text
[ ] E04 uses exactly 162 log-first-differenced training observations
[ ] No test timestamp appears in E04 input
[ ] Empty input is rejected
[ ] Input containing NaN is rejected
[ ] Output covers the approved lag range
[ ] PACF method is ywm
[ ] Confidence level is 95%
[ ] Significant flag agrees with the confidence interval
[ ] Lag 0 is excluded from p/q interpretation
[ ] Candidate inherits natural_log and d = 1
[ ] Candidate count is between 1 and 2
[ ] Raw dataset checksum is unchanged
[ ] E05/E06 remain unmodified
```

## 11. Required Outputs

```text
outputs/figures/03_acf_pacf_log_first_differenced.png
outputs/results/acf_log_first_differenced.csv
outputs/results/pacf_log_first_differenced.csv
outputs/results/arima_candidates.csv
```

Required notebook evidence:

```text
input series identity and observation count
ACF/PACF figure
concise significant-lag evidence
one or two provisional ARIMA candidates
concise limitation about remaining seasonal dependence when present
```

## 12. Acceptance Criteria

```text
[ ] E03 handoff is reproduced and validated
[ ] Only transformed training series is analyzed
[ ] Test set remains sealed
[ ] ACF/PACF configuration is explicit
[ ] ACF/PACF tables are created and inspected
[ ] Combined figure is created and inspected
[ ] Lag interpretation is based on actual evidence
[ ] One or two ARIMA candidates have traceable rationale
[ ] d = 1 and natural_log are inherited correctly
[ ] No model is fitted or forecast is generated
[ ] Tests pass
[ ] Notebook runs from a clean kernel without errors
[ ] Outputs match notebook values
[ ] Raw data remains unchanged
[ ] E05/E06 are not modified
```

## 13. Stop Conditions

Phải dừng E04 nếu:

- E03 handoff không tái tạo được;
- input không phải log-first-differenced training series;
- test leakage xuất hiện;
- transformed series có missing values hoặc sai alignment;
- stationarity evidence không còn đạt;
- ACF/PACF computation fail hoặc parameter phải đổi;
- candidate không có traceable evidence;
- cần thay đổi E03 transformation hoặc `d`;
- cần sửa E05/E06 để hoàn thành E04;
- dependency hoặc scope mới cần được thêm.

Khi dừng:

```text
1. Không tiếp tục step sau.
2. Ghi observed và expected behavior.
3. Ghi evidence và impact.
4. Đề xuất next action.
5. Chờ Human approval.
```

## 14. Risks and Limitations

| Risk | Control |
|---|---|
| Dùng nhầm full series hoặc raw difference | Validate identity, length, timestamps và E03 ADF handoff |
| Diễn giải ACF/PACF quá chắc chắn | Ghi candidates là provisional và yêu cầu E05 diagnostics |
| Lag mùa vụ còn đáng kể | Ghi limitation; không tự mở SARIMA trong E04 |
| Chọn quá nhiều candidates | Giới hạn một đến hai candidates có rationale |
| Notebook trở lại quá nhiều chữ | Chỉ giữ figure, bảng cần thiết và kết luận ngắn |
| Output và notebook lệch nhau | Clean-kernel execution và CSV/notebook comparison |

## 15. Downstream Handoff to E05

E04 chỉ được mở handoff sang E05 khi:

```text
E03 input identity validated
AND no test leakage
AND ACF/PACF evidence generated and inspected
AND one or two candidates recorded with rationale
AND natural_log and d = 1 inherited correctly
AND tests and clean notebook execution pass
AND no unresolved blocker remains
```

E04 bàn giao:

```text
stationary transformed training series identity
natural_log transformation
d = 1
ACF/PACF configuration and evidence
one or two provisional ARIMA candidates
remaining seasonal-lag limitation when applicable
```

## 16. Approval Gate

```text
EXERCISE_04_BEFORE_PROCESS_CREATED=true
EXERCISE_04_BEFORE_PROCESS_REVIEWED=true
EXERCISE_04_BEFORE_PROCESS_APPROVED=true
EXERCISE_04_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_04_IMPLEMENTED=true
EXERCISE_04_VALIDATED=true
EXERCISE_04_COMPLETED=true
EXERCISE_05_HANDOFF_OPEN=false
```

Human approval is required before any E04 implementation begins.
