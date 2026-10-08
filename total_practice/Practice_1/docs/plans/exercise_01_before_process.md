# EXERCISE 01 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_1
Exercise ID: EXERCISE_01
Topic: ACF/PACF
Plan type: Exercise Before-Process Plan
Dataset: AirPassengers
Status: COMPLETED
Implementation authorized: YES
```

Tài liệu này là execution plan riêng cho Exercise 1.

Agent chỉ được bắt đầu code Exercise 1 sau khi Human approve file này.

---

## 2. Objective

Mục tiêu của execution cycle này:

- xác minh input AirPassengers;
- kiểm tra time index và basic data quality;
- tạo reusable logic cần thiết cho Exercise 1;
- vẽ original time series;
- tính ACF đến 40 lags;
- tính PACF đến 40 lags;
- inspect actual outputs;
- trả lời các interpretation questions dựa trên evidence;
- lưu figures và result files đúng vị trí;
- không train model;
- không thay đổi raw dataset.

---

## 3. Required Documents

Trước khi implementation, agent phải đọc:

```text
working_rule.md
active .agent/ hoặc .agents/ rules
docs/rules/architecture_rule.md
docs/rules/rule_code.md
docs/plans/practice_1_overview.md
docs/exercise_details/exercise_01_acf_pacf.md
docs/plans/initialize_practice_1.md
docs/status/current_status.md nếu đã tồn tại
```

Nếu thiếu tài liệu bắt buộc hoặc có conflict:

```text
STOP
→ report missing/conflict
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

Approved source contract:

```text
CSV URL: https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv
Raw file: datasets/raw/air_passengers.csv
Expected observations: 144
Expected range: 1949-01 through 1960-12
Expected frequency: monthly
Unit: thousands of passengers
Canonical analysis field: passengers_thousands
```

Canonical monthly index phải bắt đầu tại `1949-01-01`, có 144 month-start timestamps
và kết thúc tại `1960-12-01`, sau khi raw time semantics được validate.

Input phải được validate trước khi analysis.

Các check tối thiểu:

```text
dataset readable
schema correct
timestamp parseable
chronological order valid
monthly frequency confirmed
missing values checked
duplicate timestamps checked
observation count sufficient
```

---

## 5. Files to Read

Agent cần đọc hoặc inspect:

```text
datasets/raw/air_passengers.csv
datasets/README.md
config/practice_1.json
docs/exercise_details/exercise_01_acf_pacf.md
relevant reusable source files nếu đã tồn tại
current notebook nếu đã tồn tại
```

Không được giả định file path nếu chưa xác minh folder thực tế.

---

## 6. Files Allowed to Create or Modify

Exercise 1 chỉ được phép tạo/sửa trong các khu vực cần thiết:

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
docs/analysis_error/
```

Các file dự kiến có thể cần tạo:

```text
src/practice_1/data/air_passengers.py
src/practice_1/analysis/acf_pacf.py
src/practice_1/visualization/diagnostic_plots.py
notebooks/practice_1_analysis.ipynb
```

Tên file cuối cùng phải tuân thủ structure hiện có và naming rule của project.

Không tạo duplicate module nếu owner tương đương đã tồn tại.

---

## 7. Files Not to Modify

Không được tự ý sửa:

```text
datasets/raw/air_passengers.csv
working_rule.md
approved scoped rule files
approved practice_1_overview.md
approved exercise_01_acf_pacf.md
approved initialize_practice_1.md
Exercise 2–5 specifications
Practice/Lab khác
unrelated repository configuration
```

Nếu implementation thật sự yêu cầu sửa ngoài scope:

```text
STOP
→ explain reason
→ propose change
→ wait for Human approval
```

---

## 8. Scientific Parameters

Exercise 1 phải dùng:

```text
Dataset: AirPassengers
Frequency: monthly
Seasonal period: 12
Maximum ACF lag: 40
Maximum PACF lag: 40
Confidence level: 95%
Statsmodels alpha: 0.05
PACF method: ywm
Model training: NO
```

Seasonal lags cần inspect:

```text
12
24
36
```

Lưu ý:

```text
12/24/36 chỉ là lags cần kiểm tra
không được mặc định là significant
```

Nếu PACF 40 lags không hợp lệ theo sample size hoặc implementation method:

```text
STOP
```

Không tự giảm lag.

---

## 9. Sequential Execution Steps

### Step 1 — Verify Repository Context

Xác minh:

```text
current Practice_1 root
folder structure
required docs
active rules
current execution state
```

Validation:

```text
no unresolved rule conflict
correct Practice_1 root
Exercise 1 plan is approved
```

---

### Step 2 — Verify Dataset Availability

Xác minh AirPassengers đã tồn tại trong approved raw-data location.

Nếu chưa có:

```text
thực hiện dataset acquisition theo initialize_practice_1.md
```

Sau khi có dataset, xác minh:

```text
source
schema
observation count
time range
timestamp meaning
monthly frequency
retrieval date
SHA-256 checksum
license/provenance limitation
```

Không thay đổi raw file.

---

### Step 3 — Load Dataset

Dùng reusable loader nếu đã tồn tại.

Nếu chưa có, tạo logic tối thiểu trong:

```text
src/practice_1/data/
```

Loader phải:

```text
read raw data
preserve raw values
parse timestamp trên working object
return validated structure
```

Sau implementation:

```text
run
→ inspect head
→ inspect shape
→ verify
```

---

### Step 4 — Validate Time Index and Data Quality

Kiểm tra:

```text
timestamp dtype
chronological order
monthly frequency
missing values
duplicate timestamps
time range
```

Nếu chronology sai trên raw file:

```text
không ghi đè raw
```

Nếu analysis cần sorted working copy:

```text
chỉ được tạo working representation
và phải ghi rõ lý do
```

Nếu có unresolved missing hoặc duplicate timestamp:

```text
STOP
```

---

### Step 5 — Create Original-Series Plot

Tạo visualization cho full AirPassengers series.

Output:

```text
outputs/figures/01_time_series_overview.png
```

Plot phải có:

```text
clear title
time axis
observed-value axis
readable labels
```

Sau khi tạo:

```text
inspect figure
```

Không chỉ kiểm tra file existence.

---

### Step 6 — Compute ACF

Tính ACF:

```text
max lag = 40
confidence level = 95%
alpha = 0.05
```

Nếu reusable analysis function chưa có, tạo trong:

```text
src/practice_1/analysis/
```

Output figure:

```text
outputs/figures/02_acf_40_lags.png
```

Nếu lưu numerical result:

```text
outputs/results/acf_values.csv
```

Sau execution phải inspect:

```text
lag range
confidence interval
unexpected NaN/shape issue
actual spike pattern
```

---

### Step 7 — Compute PACF

Trước calculation:

```text
verify requested 40 lags is scientifically and technically valid
```

Nếu không hợp lệ:

```text
STOP
→ report exact reason
→ do not silently reduce lag
```

Nếu hợp lệ:

```text
max lag = 40
confidence level = 95%
alpha = 0.05
method = ywm
```

Output figure:

```text
outputs/figures/03_pacf_40_lags.png
```

Nếu lưu numerical result:

```text
outputs/results/pacf_values.csv
```

Sau execution phải inspect:

```text
lag range
confidence interval
actual significant spikes
unexpected numerical behavior
```

---

### Step 8 — Answer Interpretation Questions

Chỉ sau khi actual outputs đã được tạo và inspect.

Phải trả lời:

```text
1. Chuỗi có tự tương quan mạnh không?
2. ACF giảm nhanh hay giảm chậm?
3. Có spike lặp lại theo chu kỳ không?
4. Có evidence seasonality ở lag 12, 24, 36 không?
5. PACF cho thấy lag nào nổi bật?
6. Lag nào quan trọng nhất dựa trên actual evidence?
7. Chuỗi có giống white noise không?
8. Có dấu hiệu trend/non-stationary behavior cần kiểm tra thêm không?
```

Không fabricate answer.

---

### Step 9 — Validate Exercise Outputs

Xác minh:

```text
01_time_series_overview.png exists and is readable
02_acf_40_lags.png exists and is readable
03_pacf_40_lags.png exists and is readable
numerical result files consistent nếu được tạo
interpretation matches actual plots
```

---

### Step 10 — Update State

Sau khi Exercise 1 pass validation:

```text
update current status
append concise progress log
```

Không được đánh dấu `COMPLETED` nếu còn blocker.

---

## 10. Validation Checklist

```text
[ ] Required documents were read
[ ] Dataset source/path verified
[ ] Raw data unchanged
[ ] Dataset loaded successfully
[ ] Timestamp parsed correctly
[ ] Chronological order verified
[ ] Monthly frequency verified
[ ] Missing values checked
[ ] Duplicate timestamps checked
[ ] Observation count supports requested analysis
[ ] Original-series plot created and inspected
[ ] ACF computed to 40 lags
[ ] ACF confidence level = 95%
[ ] ACF alpha = 0.05
[ ] ACF figure inspected
[ ] PACF 40-lag validity checked
[ ] PACF computed to 40 lags
[ ] PACF confidence level = 95%
[ ] PACF alpha = 0.05
[ ] PACF method = ywm
[ ] PACF figure inspected
[ ] Lag 12/24/36 interpreted from actual evidence only
[ ] Interpretation questions answered
[ ] No model training performed
[ ] No unrelated file modified
```

---

## 11. Expected Outputs

### Required Figures

```text
outputs/figures/01_time_series_overview.png
outputs/figures/02_acf_40_lags.png
outputs/figures/03_pacf_40_lags.png
```

### Optional Machine-Readable Results

```text
outputs/results/acf_values.csv
outputs/results/pacf_values.csv
```

Chỉ tạo optional result files nếu chúng có giá trị cho traceability hoặc downstream reuse.

### Narrative Evidence

Exercise 1 phải có interpretation dựa trên actual execution.

---

## 12. Stop Conditions

Agent phải dừng khi:

```text
Exercise 1 plan chưa được approve
required document missing
rule conflict
AirPassengers source/path chưa xác minh
dataset schema unexpected
timestamp parse fail
monthly frequency không xác nhận được
missing values gây analysis invalid
duplicate timestamp chưa giải quyết
observation count không đủ
PACF 40 lags không hợp lệ
ACF/PACF computation fail
output figure sai hoặc không đọc được
scientific parameter cần thay đổi
dependency mới cần thêm
unrelated file cần sửa
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
7. Chờ Human approval.
```

---

## 13. Completion Gate

Exercise 1 chỉ được xem là complete khi:

```text
input validated
AND original series inspected
AND ACF 40 lags validated
AND PACF 40 lags validated
AND figures inspected
AND interpretation questions answered
AND raw data unchanged
AND no unresolved blocking issue
```

---

## 14. Approval Gate

Trạng thái hiện tại:

```text
EXERCISE_01_BEFORE_PROCESS_CREATED=true
EXERCISE_01_BEFORE_PROCESS_REVIEWED=true
EXERCISE_01_BEFORE_PROCESS_APPROVED=true
EXERCISE_01_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_01_IMPLEMENTED=true
EXERCISE_01_VALIDATED=true
```

Agent không được code Exercise 1 khi:

```text
EXERCISE_01_IMPLEMENTATION_AUTHORIZED=false
```

Sau khi Human approve:

```text
EXERCISE_01_BEFORE_PROCESS_REVIEWED=true
EXERCISE_01_BEFORE_PROCESS_APPROVED=true
EXERCISE_01_IMPLEMENTATION_AUTHORIZED=true
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
tự đổi dataset
tự giảm lag
tự đổi confidence level
tự thêm forecasting model
tự sửa raw data
tự sửa approved specification
tự bỏ qua validation
tự claim completion
```
