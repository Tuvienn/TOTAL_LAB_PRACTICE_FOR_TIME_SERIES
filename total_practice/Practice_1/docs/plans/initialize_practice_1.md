# PRACTICE 1 — MASTER INITIALIZATION PLAN

## 1. Plan Identity

```text
Practice: Practice_1
Plan ID: INITIALIZE_PRACTICE_1
Plan type: Master Before-Process Plan
Dataset: AirPassengers
Status: INITIALIZATION_COMPLETED
Implementation authorized: YES_FOR_INITIALIZATION_AND_EXERCISE_1
```

Tài liệu này chỉ quản lý kế hoạch khởi tạo chung của Practice 1.

Chi tiết thực thi từng bài được tách riêng tại:

```text
docs/plans/exercise_01_before_process.md
docs/plans/exercise_02_before_process.md
docs/plans/exercise_03_before_process.md
docs/plans/exercise_04_before_process.md
docs/plans/exercise_05_before_process.md
```

---

## 2. Objective

Mục tiêu của bước khởi tạo:

- xác minh rule và structure của Practice 1;
- xác minh dataset AirPassengers;
- chuẩn bị shared reusable structure;
- khóa các scientific parameters dùng chung;
- xác định thứ tự thực thi Exercise 1–5;
- đảm bảo agent không tự mở rộng scope;
- chuẩn bị điều kiện để từng exercise có thể được thực thi độc lập theo before-process plan riêng.

---

## 3. Required Documents

Agent phải đọc trước khi bắt đầu:

```text
working_rule.md
các rule trong .agent/ hoặc .agents/ đang active
docs/rules/architecture_rule.md
docs/rules/rule_code.md
docs/plans/practice_1_overview.md
docs/exercise_details/exercise_01_acf_pacf.md
docs/exercise_details/exercise_02_white_noise.md
docs/exercise_details/exercise_03_decomposition.md
docs/exercise_details/exercise_04_data_quality.md
docs/exercise_details/exercise_05_visualization.md
```

Nếu file hoặc path thực tế khác:

```text
STOP
→ xác minh structure
→ không tự suy đoán path mới
```

---

## 4. Shared Scientific Configuration

```text
Dataset: AirPassengers
Frequency: monthly
Seasonal period: 12
Maximum ACF/PACF lag: 40
Confidence level: 95%
White-noise observations: 1000
White-noise distribution: Normal(0, 1)
Random seed: 42
Rolling window: 12
Rolling min_periods: 12
Rolling center: False
Rolling std ddof: 1
Decomposition: log transform + STL
STL period: 12
STL robust: True
Residual ACF maximum lag: 40
Residual Ljung-Box lag: 12
Missing positions: 1952-03, 1954-11, 1956-06 through 1956-08, 1959-04
Outlier method: IQR 1.5 on natural-log STL residual
Model training: NO
```

Các config này chỉ được thay đổi khi Human approve.

---

## 5. Dataset Acquisition Protocol

Dataset chính:

```text
AirPassengers
```

Canonical source contract:

```text
CSV URL: https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv
Documentation URL: https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html
Expected observations: 144
Expected time range: 1949-01 through 1960-12
Expected frequency: monthly
Expected unit: thousands of passengers
Canonical analysis field: passengers_thousands
Raw filename: air_passengers.csv
```

Sau khi xác minh 144 rows, documented start/frequency và raw `time` progression,
canonical monthly index được tạo deterministically bằng:

```text
start = 1949-01-01
periods = 144
frequency = month-start
end = 1960-12-01
```

Không parse trực tiếp fractional-year floats thành datetimes bằng heuristic. Nếu raw
schema hoặc progression không khớp contract, dừng dataset acquisition.

Trước khi sử dụng phải xác minh:

```text
source
schema
number of observations
time range
timestamp semantics
monthly frequency
missing values
duplicate timestamps
chronological order
retrieval date
SHA-256 checksum
license/provenance limitation
```

Dataset raw phải lưu tại:

```text
datasets/raw/air_passengers.csv
```

Dataset provenance được ghi tại `datasets/README.md` sau actual download, bao gồm canonical
URL, documentation URL, retrieval date, actual schema, units, frequency, SHA-256 và
license limitation.

Raw data là immutable.

Không được:

```text
overwrite raw data
fill missing trên raw
remove outlier trên raw
sort rồi ghi đè raw
transform rồi ghi đè raw
```

---

## 6. Shared Folder Ownership

```text
src/practice_1/data/
→ reusable data loading và validation logic

src/practice_1/analysis/
→ reusable analytical logic

src/practice_1/visualization/
→ reusable plotting logic

notebooks/
→ exercise execution, explanation và interpretation

outputs/figures/
→ exported figures

outputs/results/
→ machine-readable analytical results

```

Không duplicate reusable logic trong nhiều notebook cells nếu đã có owner trong
`src/practice_1/`.

### 6.1 Runtime and Dependency Contract

```text
Python: 3.12
Local environment: .venv
Package owner: pyproject.toml
Package name: practice_1
Package layout: src/practice_1/
Notebook kernel: time-series-practice-1
```

Planned dependencies:

```text
runtime: numpy, pandas, matplotlib, statsmodels
notebook: jupyterlab, ipykernel, nbconvert
test: pytest
```

Exact resolved versions phải được ghi từ environment thực tế trong Nhóm 4. Không dùng
Python 3.14 mặc định hiện tại vì environment đó chưa có scientific/Jupyter packages và
compatibility chưa được xác minh. `.venv/` phải được ignore và không commit.

Environment snapshot sau cài đặt được lưu tại:

```text
docs/logs/environment_snapshot.txt
```

Snapshot phải ghi Python executable/version, kernel name và resolved package versions.

Import contract:

```text
editable install từ pyproject.toml
from practice_1... imports
no sys.path mutation
no notebook-relative import hacks
```

### 6.2 Canonical Implementation Map

Các owner dự kiến cho implementation:

```text
config/practice_1.json
datasets/README.md
datasets/raw/air_passengers.csv
.gitignore
pyproject.toml
src/practice_1/__init__.py
src/practice_1/data/__init__.py
src/practice_1/data/air_passengers.py
src/practice_1/analysis/__init__.py
src/practice_1/analysis/acf_pacf.py
src/practice_1/analysis/white_noise.py
src/practice_1/analysis/decomposition.py
src/practice_1/analysis/data_quality.py
src/practice_1/analysis/rolling_statistics.py
src/practice_1/visualization/__init__.py
src/practice_1/visualization/diagnostic_plots.py
src/practice_1/visualization/data_quality_plots.py
src/practice_1/visualization/seasonal_plots.py
notebooks/practice_1.ipynb
docs/logs/environment_snapshot.txt
tests/test_air_passengers.py
tests/test_acf_pacf.py
tests/test_white_noise.py
tests/test_decomposition.py
tests/test_data_quality.py
tests/test_rolling_statistics.py
tests/test_seasonal_matrix.py
```

Notebook section order:

```text
0. Reproducibility and configuration
1. Dataset provenance, loading and validation
2. Exercise 1 — ACF/PACF
3. Exercise 2 — White Noise
4. Exercise 3 — Decomposition
5. Exercise 4 — Data Quality
6. Exercise 5 — Visualization
7. Evidence summary for TuVien's Word report
```

Notebook chỉ orchestration, display và interpretation; reusable logic thuộc các
source owners ở trên. Test filenames sẽ được tạo theo source owner thực tế và không
được gom thành placeholder test vô nghĩa.

`config/practice_1.json` là owner duy nhất của các giá trị execution đã khóa. Schema
dự kiến:

```json
{
  "dataset": {
    "url": "https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv",
    "raw_filename": "air_passengers.csv",
    "expected_rows": 144,
    "start": "1949-01-01",
    "end": "1960-12-01",
    "frequency": "MS"
  },
  "correlation": {"max_lag": 40, "confidence_level": 0.95, "alpha": 0.05, "pacf_method": "ywm"},
  "white_noise": {"size": 1000, "seed": 42, "mean": 0.0, "standard_deviation": 1.0},
  "decomposition": {"transform": "log", "method": "STL", "period": 12, "robust": true},
  "residual_diagnostics": {"acf_max_lag": 40, "ljung_box_lag": 12},
  "missing_experiment": {
    "isolated": ["1952-03-01", "1954-11-01", "1959-04-01"],
    "consecutive": ["1956-06-01", "1956-07-01", "1956-08-01"],
    "metric": "MAE",
    "interpolation_method": "time",
    "interpolation_limit_area": "inside"
  },
  "outliers": {"method": "IQR", "multiplier": 1.5, "action": "flag_only"},
  "rolling": {"window": 12, "min_periods": 12, "center": false, "std_ddof": 1},
  "heatmap": {"rows": "month", "columns": "year", "expected_shape": [12, 12]}
}
```

### 6.3 Minimum Test Matrix

```text
dataset has exactly 144 observations
monthly index runs from 1949-01-01 through 1960-12-01 with frequency MS
no duplicate timestamps and no unexpected raw missing values
raw-file SHA-256 is unchanged before and after analysis
ACF and PACF cover lags 0 through 40
white noise is deterministic for default_rng(42)
exactly six locked timestamps are masked
masking and treatments do not mutate the validated source series
MAE is calculated only on the six masked positions
rolling mean/std have exactly 11 initial NaN values
month-year heatmap has shape 12 × 12
notebook executes end-to-end after kernel restart
```

Test ownership:

```text
tests/test_air_passengers.py
→ row count, monthly index, date range, duplicate/missing checks, source immutability

tests/test_acf_pacf.py
→ lag coverage 0–40, alpha 0.05, PACF method ywm contract

tests/test_white_noise.py
→ length 1000 and deterministic default_rng(42) output

tests/test_decomposition.py
→ log-scale component alignment, period 12, residual diagnostic shape

tests/test_data_quality.py
→ exact six masks, no source mutation, inside-only interpolation, masked-only MAE

tests/test_rolling_statistics.py
→ window 12, min_periods 12, center False, ddof 1, eleven initial NaN values

tests/test_seasonal_matrix.py
→ month rows, year columns, chronological labels, shape 12 × 12
```

Raw-file checksum stability được kiểm tra trong dataset validation workflow trước và
sau end-to-end execution; test không được hardcode checksum trước actual acquisition.

### 6.4 Canonical Validation Commands

Sau khi Nhóm 4 tạo environment và package:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m jupyter nbconvert --execute --to notebook --inplace --ExecutePreprocessor.kernel_name=time-series-practice-1 notebooks/practice_1.ipynb
```

Notebook execution phải dùng registered kernel `time-series-practice-1`. Nếu command,
kernel hoặc import fail, không được thay bằng `sys.path` workaround.

---

## 7. Execution Order

Practice 1 phải thực hiện tuần tự:

```text
Initialization
→ Exercise 1 — ACF/PACF
→ Exercise 2 — White Noise
→ Exercise 3 — Decomposition
→ Exercise 4 — Data Quality
→ Exercise 5 — Visualization
```

Exercise 6 là Word report do TuVien tự thực hiện và không thuộc AI implementation
plan. Agent chỉ cung cấp validated evidence từ Exercise 1–5.

Mỗi exercise chỉ được bắt đầu khi:

```text
exercise specification đã đọc
AND exercise before-process plan đã được approve
AND upstream dependency cần thiết đã được validate
```

---

## 8. Exercise Before-Process Files

Mỗi exercise phải có execution plan riêng:

```text
exercise_01_before_process.md
exercise_02_before_process.md
exercise_03_before_process.md
exercise_04_before_process.md
exercise_05_before_process.md
```

Mỗi file phải chỉ rõ:

```text
Objective
Required documents
Input
Files to read
Files to create/modify
Files not to modify
Scientific parameters
Sequential execution steps
Validation steps
Expected outputs
Stop conditions
Approval gate
```

---

## 9. Shared Files Allowed to Create or Modify

Agent chỉ được làm việc trong các khu vực đã duyệt:

```text
config/practice_1.json
pyproject.toml
.gitignore
datasets/raw/
datasets/processed/
datasets/README.md
src/practice_1/
notebooks/
outputs/figures/
outputs/results/
tests/
docs/status/
docs/logs/
docs/error_analysis/
docs/fix_plans/
```

Không được tự tạo top-level folder mới.

---

## 10. Files Not to Modify

Không tự ý sửa:

```text
working_rule.md
approved scoped rule files
approved overview
approved exercise specification files
raw dataset sau khi đã xác minh
các Practice/Lab khác
unrelated repository configuration
```

Nếu cần sửa:

```text
STOP
→ giải thích lý do
→ xin Human approval
```

---

## 11. Shared Validation Requirements

Mọi exercise phải bảo đảm:

```text
raw data immutable
chronological order preserved
timestamp semantics preserved
no random shuffle
no future leakage
no silent data repair
no fabricated results
actual outputs inspected
```

Agent không được claim:

```text
PASS
COMPLETED
FIXED
```

nếu chưa có execution evidence.

---

## 12. Shared Stop Conditions

Phải dừng nếu:

```text
rule conflict
required document missing
dataset source chưa xác minh
schema unexpected
timestamp invalid
frequency không phải monthly
raw data bị thay đổi
scientific parameter cần đổi
dependency mới cần thêm
scope cần mở rộng
unrelated file cần sửa
validation fail chưa rõ nguyên nhân
```

Khi dừng:

```text
1. Không tiếp tục bước sau.
2. Ghi observed behavior.
3. Ghi expected behavior.
4. Nêu impact.
5. Đề xuất next action.
6. Chờ Human approval.
```

---

## 13. Current State

```text
Master initialization plan: COMPLETED
Exercise 1 specification: CREATED
Exercise 2 specification: CREATED
Exercise 3 specification: CREATED
Exercise 4 specification: CREATED
Exercise 5 specification: CREATED

Exercise 1 before-process plan: COMPLETED
Exercise 2 before-process plan: CREATED / WAITING_APPROVAL
Exercise 3 before-process plan: CREATED / WAITING_APPROVAL
Exercise 4 before-process plan: CREATED / WAITING_APPROVAL
Exercise 5 before-process plan: CREATED / WAITING_APPROVAL

Initialization: COMPLETED
Exercise 1 implementation: COMPLETED / VALIDATED
Next implementation: NOT_AUTHORIZED
Exercise 6 Word report: USER_OWNED / OUTSIDE_AI_IMPLEMENTATION_PLAN
```

---

## 14. Next Step

```text
1. Human reviews the validated Exercise 1 evidence.
2. Human reviews Exercise 2 specification and before-process plan.
3. Human explicitly authorizes Exercise 2 implementation.
4. Only then may Exercise 2 execution begin.
```

---

## 15. Approval Gate

```text
MASTER_PLAN_CREATED=true
MASTER_PLAN_UPDATED_FOR_GROUP_1_3=true
MASTER_PLAN_REVIEWED=true
MASTER_PLAN_APPROVED=true
IMPLEMENTATION_AUTHORIZED=true_FOR_INITIALIZATION_AND_EXERCISE_1
INITIALIZATION_COMPLETED=true
EXERCISE_01_COMPLETED=true
NEXT_IMPLEMENTATION_AUTHORIZED=false
```

Sau khi Human approve:

```text
MASTER_PLAN_REVIEWED=true
MASTER_PLAN_APPROVED=true
```

Lưu ý:

```text
MASTER_PLAN_APPROVED=true
```

không tự động cho phép chạy tất cả exercise.

Mỗi exercise vẫn phải có:

```text
exercise-specific before-process approval
```

trước khi implementation.
