# EXERCISE 02 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_1
Exercise ID: EXERCISE_02
Topic: White Noise
Plan type: Exercise Before-Process Plan
Reference dataset: AirPassengers
Synthetic sample size: 1000
Random seed: 42
Synthetic distribution: Normal(0, 1)
Maximum ACF lag: 40
Status: COMPLETED
Implementation authorized: YES
```

Tài liệu này là execution plan riêng cho Exercise 2.

Agent chỉ được bắt đầu code Exercise 2 sau khi Human approve file này.

---

## 2. Objective

Mục tiêu của execution cycle này:

- sinh synthetic white noise có thể tái tạo;
- kiểm tra basic statistical behavior của white noise;
- vẽ white-noise series;
- tính ACF với confidence level 95%;
- tái sử dụng validated AirPassengers ACF từ Exercise 1;
- so sánh temporal dependence giữa white noise và AirPassengers;
- viết tối thiểu 5 dòng mô tả sự khác nhau;
- nếu dùng Ljung-Box, chỉ dùng như supplementary diagnostic;
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
docs/exercise_details/exercise_02_white_noise.md
docs/plans/initialize_practice_1.md
docs/plans/exercise_01_before_process.md
docs/status/current_status.md nếu đã tồn tại
```

Ngoài ra phải xác minh Exercise 1 đã có validated ACF output.

Nếu thiếu dependency hoặc có conflict:

```text
STOP
→ report issue
→ chờ Human quyết định
```

---

## 4. Input

Exercise 2 có hai input.

### 4.1 Synthetic White Noise

```text
Number of observations: 1000
Random seed: 42
Distribution: Normal(0, 1)
```

Generator contract:

```text
numpy.random.default_rng(42)
normal(loc=0.0, scale=1.0, size=1000)
```

### 4.2 AirPassengers Reference

```text
Validated AirPassengers ACF from Exercise 1
Frequency: monthly
Seasonal period: 12
```

Không được tự tính lại AirPassengers ACF bằng protocol khác nếu validated output đã tồn tại.

Nếu cần tái chạy, phải dùng đúng logic và parameters của Exercise 1.

---

## 5. Files to Read

Agent cần đọc hoặc inspect:

```text
docs/exercise_details/exercise_02_white_noise.md
config/practice_1.json
docs/plans/exercise_01_before_process.md
validated AirPassengers ACF output
relevant reusable source files
current notebook nếu đã tồn tại
```

Có thể cần đọc:

```text
outputs/results/acf_values.csv
```

nếu file đó đã được tạo ở Exercise 1.

---

## 6. Files Allowed to Create or Modify

Exercise 2 chỉ được phép tạo/sửa trong:

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

Các logic dự kiến:

```text
white-noise generation
white-noise ACF analysis
ACF comparison visualization
optional Ljung-Box diagnostic
```

Không tạo duplicate function nếu reusable owner đã tồn tại.

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
approved initialize_practice_1.md
Exercise 1 validated outputs
Exercise 3–5 specifications
Practice/Lab khác
unrelated repository configuration
```

Nếu thật sự cần thay đổi upstream Exercise 1 output:

```text
STOP
→ giải thích lý do
→ không overwrite silently
→ chờ Human approval
```

---

## 8. Scientific Parameters

Exercise 2 phải dùng:

```text
Synthetic process: White Noise
Number of observations: 1000
Random seed: 42
Distribution: Normal(0, 1)
Maximum ACF lag: 40
Confidence level: 95%
Reference dataset: AirPassengers
Reference frequency: monthly
Reference seasonal period: 12
```

Supplementary diagnostic:

```text
Ljung-Box
```

Ljung-Box:

```text
không bắt buộc theo đề gốc
không thay thế ACF
không được dùng như sole evidence
```

---

## 9. Sequential Execution Steps

### Step 1 — Verify Upstream Dependency

Xác minh Exercise 1 đã có:

```text
validated AirPassengers ACF
validated confidence interval
actual inspected output
```

Nếu chưa:

```text
STOP
```

Không tự bỏ qua Exercise 1 dependency.

---

### Step 2 — Verify Repository Context

Xác minh:

```text
Practice_1 root
required rules
Exercise 2 specification
master initialization plan
current execution state
```

Validation:

```text
no unresolved rule conflict
Exercise 2 before-process plan approved
```

---

### Step 3 — Generate White Noise

Set:

```text
rng = numpy.random.default_rng(42)
```

Sau đó sinh:

```text
rng.normal(loc=0.0, scale=1.0, size=1000)
```

White-noise generation phải reproducible.

Sau execution:

```text
verify length = 1000
inspect mean
inspect standard deviation
```

Không regenerate bằng seed khác trong cùng experiment.

---

### Step 4 — Plot White-Noise Series

Tạo:

```text
outputs/figures/04_white_noise_series.png
```

Figure phải:

```text
readable
correct observation order
clear title
clear axes
```

Sau khi tạo:

```text
inspect actual figure
```

---

### Step 5 — Compute White-Noise ACF

Tính ACF với:

```text
maximum lag = 40
confidence level = 95%
```

Không được tự thay đổi confidence level.

Output:

```text
outputs/figures/05_white_noise_acf.png
```

Nếu lưu numerical result:

```text
outputs/results/white_noise_acf_values.csv
```

Sau execution phải inspect:

```text
majority of spikes
confidence bounds
unexpected patterns
```

Không kết luận chỉ từ expected theory.

---

### Step 6 — Optional Ljung-Box Diagnostic

Nếu implementation sử dụng Ljung-Box:

```text
run actual test
record actual statistic/p-value
mark as supplementary
```

Nếu test không được dùng:

```text
không cần tạo fake placeholder
```

Nếu có output:

```text
outputs/results/white_noise_diagnostics.csv
```

---

### Step 7 — Retrieve AirPassengers ACF

Ưu tiên reuse validated output từ Exercise 1.

Xác minh:

```text
same dataset
same ACF protocol
confidence level compatible
output validated
```

Không dùng một AirPassengers ACF khác nguồn hoặc khác protocol mà không báo.

---

### Step 8 — Create Comparison Figure

So sánh:

```text
White Noise ACF
vs
AirPassengers ACF
```

Output:

```text
outputs/figures/06_white_noise_vs_airpassengers_acf.png
```

Comparison phải cho phép quan sát:

```text
significant spikes
decay behavior
repeated seasonal patterns
relative temporal dependence
```

Sau khi tạo:

```text
inspect actual comparison figure
```

---

### Step 9 — Write Interpretation

Phải trả lời:

```text
1. White noise có pattern rõ theo thời gian không?
2. Phần lớn ACF spikes có nằm trong 95% confidence interval không?
3. Có spike riêng lẻ vượt confidence interval không?
4. Nếu có, điều đó có đủ để phủ nhận white-noise behavior không?
5. AirPassengers ACF khác white noise như thế nào?
6. AirPassengers có temporal dependence mạnh hơn không?
7. Có seasonal pattern lặp lại ở AirPassengers không?
8. Kết quả giúp hiểu gì về white noise?
```

Sau đó viết tối thiểu:

```text
5 dòng so sánh
```

dựa trên actual outputs.

Không được viết trước khi plots được inspect.

---

### Step 10 — Validate Exercise Outputs

Xác minh:

```text
04_white_noise_series.png exists and is readable
05_white_noise_acf.png exists and is readable
06_white_noise_vs_airpassengers_acf.png exists and is readable
numerical result files consistent nếu có
5-line comparison exists
interpretation matches actual evidence
```

---

### Step 11 — Update State

Sau khi Exercise 2 pass validation:

```text
update current status
append concise progress log
```

Không đánh dấu `COMPLETED` nếu còn blocker.

---

## 10. Validation Checklist

```text
[ ] Required documents were read
[ ] Exercise 1 ACF dependency validated
[ ] Random seed fixed at 42
[ ] White noise length = 1000
[ ] White noise distribution = Normal(0, 1)
[ ] White-noise mean inspected
[ ] White-noise standard deviation inspected
[ ] White-noise series figure created and inspected
[ ] White-noise ACF created
[ ] White-noise ACF maximum lag = 40
[ ] Confidence level = 95%
[ ] ACF figure inspected
[ ] AirPassengers ACF reused from validated source
[ ] Comparison figure created and inspected
[ ] Minimum 5-line comparison written
[ ] Interpretation based on actual outputs
[ ] Ljung-Box marked supplementary if used
[ ] No model training performed
[ ] No unrelated file modified
```

---

## 11. Expected Outputs

### Required Figures

```text
outputs/figures/04_white_noise_series.png
outputs/figures/05_white_noise_acf.png
outputs/figures/06_white_noise_vs_airpassengers_acf.png
```

### Optional Results

```text
outputs/results/white_noise_acf_values.csv
outputs/results/white_noise_diagnostics.csv
```

### Narrative Evidence

```text
minimum 5-line comparison
white-noise interpretation
AirPassengers comparison
```

---

## 12. Stop Conditions

Agent phải dừng khi:

```text
Exercise 2 plan chưa được approve
required document missing
rule conflict
Exercise 1 ACF chưa được validate
random seed không được kiểm soát
white noise length khác 1000
ACF computation fail
confidence interval không xác định được
AirPassengers ACF không cùng protocol
comparison figure không hợp lệ
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

Exercise 2 chỉ được xem là complete khi:

```text
white noise generated reproducibly
AND series inspected
AND white-noise ACF validated
AND AirPassengers ACF validated
AND comparison completed
AND minimum 5-line interpretation written
AND outputs inspected
AND no unresolved blocking issue
```

---

## 14. Approval Gate

Trạng thái hiện tại:

```text
EXERCISE_02_BEFORE_PROCESS_CREATED=true
EXERCISE_02_BEFORE_PROCESS_REVIEWED=true
EXERCISE_02_BEFORE_PROCESS_APPROVED=true
EXERCISE_02_IMPLEMENTATION_AUTHORIZED=true
```

Agent không được code Exercise 2 khi:

```text
EXERCISE_02_IMPLEMENTATION_AUTHORIZED=false
```

Sau khi Human approve:

```text
EXERCISE_02_BEFORE_PROCESS_REVIEWED=true
EXERCISE_02_BEFORE_PROCESS_APPROVED=true
EXERCISE_02_IMPLEMENTATION_AUTHORIZED=true
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
tự đổi seed
tự đổi sample size
tự đổi confidence level
tự thay AirPassengers reference
tự thêm model
tự sửa upstream validated output
tự bỏ qua ACF comparison
tự claim completion
```
