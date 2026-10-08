# TIME SERIES PRACTICE 01 — QUY TẮC KIẾN TRÚC

## 1. Danh tính tài liệu

```text
Document ID: TS-PRACTICE-01-ARCHITECTURE-v1.1
Phạm vi repository: total_practice/Practice_1
Phong cách kiến trúc: Source-owned processing kết hợp notebook cho exploration và presentation
Phạm vi khoa học: Khám phá, chẩn đoán và đánh giá forecastability của chuỗi thời gian
Trạng thái: APPROVED_AND_ACTIVE
Runtime/package amendment approved: 2026-10-08
```

Tài liệu này quy định kiến trúc, trách nhiệm thư mục, hướng dependency, vòng đời dữ liệu, ranh giới notebook, quyền sở hữu output và các quy tắc validation cho `Practice_1`.

Tài liệu này không thay thế:

```text
.agents/RULES_INDEX.md và các canonical source được router này nạp
total_practice/Practice_1/docs/RULE_BASE/rule_code.md
các tài liệu chi tiết của từng exercise khi tồn tại
các before-process plan đã được duyệt khi implementation được yêu cầu
```

Nếu các rule xung đột nhau, phải dừng thực thi và chờ Human quyết định.

---

## 2. Mục tiêu kiến trúc

Kiến trúc phải bảo đảm:

```text
Mỗi loại logic có một owner rõ ràng.
Raw data được giữ bất biến.
Thứ tự thời gian được bảo toàn.
Không dùng thông tin tương lai để tác động dữ liệu quá khứ.
Notebook không phải nơi duy nhất chứa reusable processing logic.
Data, source code, outputs, tests và documentation được tách biệt trách nhiệm.
Mỗi exercise có input, processing, output và validation truy vết được.
Kết quả có thể tái tạo từ source, data và configuration hiện có.
```

Phạm vi Practice 1 bao gồm:

```text
kiểm tra time index và chất lượng dữ liệu
trực quan hóa chuỗi thời gian
phân tích ACF/PACF
thí nghiệm white noise
decomposition
missing-value experiment
outlier analysis
đánh giá forecastability
```

Ngoài phạm vi Practice 1:

```text
forecasting model fitting
ARIMA/SARIMA fitting
Machine Learning hoặc Deep Learning
train/validation/test modeling protocol
hyperparameter tuning
model backtesting
```

---

## 3. Canonical Lab Root

Root chuẩn của Practice 1:

```text
total_practice/Practice_1/
```

Cấu trúc chuẩn:

```text
Practice_1/
├── .gitignore
├── README.md
├── pyproject.toml
├── config/
├── data/
│   ├── README.md
│   ├── raw/
│   └── processed/
├── docs/
│   ├── RULE_BASE/
│   ├── plan/
│   │   ├── overview/
│   │   ├── exercise_details/
│   │   └── before_process/
│   ├── current_flow/
│   ├── analysis_error/
│   ├── logs/
│   └── learning_notes/
├── notebooks/
├── src/
│   └── practice_1/
│       ├── __init__.py
│       ├── data/
│       ├── analysis/
│       └── visualization/
├── outputs/
│   ├── figures/
│   └── results/
└── tests/
```

Không tạo thêm folder song song có cùng trách nhiệm nếu chưa được duyệt.

Folder trong cây kiến trúc chỉ được tạo khi có artifact thực tế thuộc trách nhiệm của folder đó.

---

## 4. Trách nhiệm các thư mục cấp cao

### 4.1 `data/`

Lưu dữ liệu nguồn và dữ liệu dẫn xuất.

```text
data/raw/
```

lưu dữ liệu gốc.

Quy tắc:

```text
Không ghi đè raw data.
Không âm thầm sort file raw trên disk.
Không âm thầm fill missing values.
Không âm thầm remove outliers.
Không âm thầm rename columns.
Không thay raw file bằng processed version.
```

```text
data/processed/
```

lưu dữ liệu dẫn xuất đã được duyệt.

Processed data phải có thể tái tạo từ:

```text
raw data
+
source code
+
approved processing steps
```

`data/README.md` sở hữu provenance của dataset, bao gồm source, retrieval date, license, checksum, schema, units, frequency và known limitations.

---

### 4.2 `config/`

Lưu các tham số khoa học và tham số reproducibility đã được duyệt.

Ví dụ:

```text
random seed
seasonal period
maximum lag
rolling window
confidence level
decomposition settings
missing-value experiment settings
```

Configuration không được chứa secret hoặc machine-specific absolute path.

---

### 4.3 `docs/`

Lưu governance, planning, current state, analysis notes, issue records, progress logs và learning notes.

`docs/` không phải nơi lưu scientific result tables vốn thuộc `outputs/`.

---

### 4.4 `notebooks/`

Lưu exploration, explanation, exercise execution và presentation.

Notebook có thể:

```text
gọi approved public functions
chạy exploratory analysis
hiển thị bảng
hiển thị figure
giải thích finding
ghi interpretation
```

Khi logic trở nên reusable hoặc được dùng nhiều hơn một lần, logic đó nên được chuyển vào package `src/practice_1/`.

Notebook không được phụ thuộc hidden execution state.

---

### 4.5 `src/practice_1/`

Lưu reusable logic dưới một installable Python package có tên `practice_1`.

```text
src/practice_1/data/
```

sở hữu:

```text
data loading
timestamp parsing
basic validation
approved preprocessing
raw-data integrity checks
```

```text
src/practice_1/analysis/
```

sở hữu:

```text
time-series analysis
statistics
ACF/PACF calculations
decomposition helpers
stationarity checks
white-noise analysis
missing-value experiment helpers
outlier analysis trên decomposition residual khi phù hợp
các reusable analytical logic khác
```

```text
src/practice_1/visualization/
```

sở hữu reusable plotting functions.

Mỗi package/subpackage phải có `__init__.py` phù hợp. Notebook và tests import qua
public package path, ví dụ `from practice_1.analysis.acf_pacf import ...`.

Không thêm `sys.path`, absolute path hoặc notebook-relative path hack để import source.

---

### 4.6 `pyproject.toml` và local environment

`pyproject.toml` sở hữu package metadata, Python compatibility, runtime dependencies,
test dependencies và editable-install configuration.

Runtime đã chốt cho Practice 1:

```text
Python: 3.12
Local environment: .venv
Notebook kernel: time-series-practice-1
Package layout: src/practice_1/
```

`.venv/` là generated local environment, không phải repository artifact và phải được
ignore. Không commit interpreter binaries hoặc installed packages.

Nếu repository chưa có ignore rule phù hợp, Practice 1 sở hữu local `.gitignore` với
tối thiểu `.venv/`, Python cache, notebook checkpoints và generated local metadata.

---

### 4.7 `outputs/`

Lưu kết quả tạo ra từ execution.

```text
outputs/figures/
```

lưu exported plots.

```text
outputs/results/
```

lưu result tables và machine-readable summaries như CSV hoặc JSON.

Output là bằng chứng thực thi, không phải source code.

---

### 4.7 `tests/`

Lưu validation tests cho reusable logic khi cần.

Phải có validation tự động cho time-index integrity, raw-data immutability và các analytical logic có nguy cơ alignment sai.

Ngoài nhóm tối thiểu trên, chỉ tạo test khi logic đủ reusable, non-trivial hoặc có nguy cơ dễ hỏng.

Không tạo test vô nghĩa chỉ để lấp đầy folder.

---

## 5. Vòng đời dữ liệu

Luồng chuẩn:

```text
data/raw
→ provenance and integrity validation
→ in-memory working copy
→ approved exploratory processing
→ analysis
→ outputs
→ final report
```

Raw data là source of truth.

Processed data không được thay thế raw dataset ban đầu.

Missing values và outliers giả lập chỉ được tạo trên working copy. Không ghi ngược exploratory mutation vào raw data.

---

## 6. Quy tắc toàn vẹn Time Series

Mọi xử lý Time Series phải bảo toàn:

```text
chronological order
ý nghĩa timestamp
sampling frequency awareness
duplicate timestamp awareness
missing timestamp awareness
future-information boundaries
data-availability boundaries khi diễn giải khả năng forecasting
```

Bị cấm nếu chưa có protocol approval rõ ràng:

```text
future leakage
centered rolling features dùng future values
silent interpolation
silent resampling
silent outlier removal
silent timestamp repair
```

Practice 1 không thực hiện model training. Các future-information rule được giữ để bảo đảm kết luận forecastability không dựa trên quy trình không thể sử dụng trong thực tế.

---

## 7. Ranh giới Notebook

Notebook được phép chứa:

```text
Markdown explanation
small exploratory calculations
calls tới reusable source functions
tables
plots
interpretation
exercise-specific demonstrations
```

Notebook không nên trở thành nơi canonical cho:

```text
large reusable functions
duplicate processing logic
shared validation logic
data pipeline implementation
hidden path hacks
silent repair logic
```

Khi logic trong notebook trở nên reusable hoặc ảnh hưởng correctness khoa học, phải chuyển sang package `src/practice_1/`.

---

## 8. Hướng dependency

Được phép:

```text
notebooks → installed practice_1 package
tests → installed practice_1 package
practice_1.analysis → practice_1.data khi cần
practice_1.analysis → approved config khi cần
practice_1.visualization → validated analysis/data objects
outputs ← notebooks/practice_1 package execution
docs ← verified project state
```

Không được phép:

```text
practice_1 package → notebooks
data → source code
outputs → canonical source logic
tests → notebook state
```

Không cho phép circular dependency.

---

## 9. Exercise Ownership

Mỗi exercise phải có:

```text
objective
input
required tasks
expected outputs
validation criteria
completion condition
```

Các nội dung này nằm trong:

```text
docs/plan/exercise_details/
```

Exercise execution phải tuân thủ exercise detail đã duyệt và before-process plan hiện tại.

---

## 10. Planning Boundary

Trước meaningful implementation, active task phải được mô tả trong:

```text
docs/plan/before_process/
```

Plan phải chỉ rõ:

```text
task objective
relevant files
files to modify
files not to modify
steps
validation
expected outputs
stop conditions
```

Human phải approve plan trước khi có major execution.

---

## 11. Current Flow

Trạng thái hiện tại của Lab phải được tổng hợp trong:

```text
docs/current_flow/
```

Tài liệu phải trả lời được:

```text
Đã hoàn thành gì?
Đang làm gì?
Tiếp theo là gì?
Output nào đang còn hiệu lực?
Có blocker nào không?
```

---

## 12. Error Analysis

Khi xuất hiện bug hoặc scientific issue không trivial, phần investigation nằm trong:

```text
docs/analysis_error/
```

Một issue report hữu ích nên gồm:

```text
observed behavior
expected behavior
affected files
root cause
impact
recommended correction direction
```

Không patch downstream symptom nếu root cause nằm upstream.

---

## 13. Output Rules

Scientific results phải được lưu trong `outputs/`.

Ví dụ:

```text
outputs/figures/time_series_plot.png
outputs/results/summary_statistics.csv
```

Không dùng tên kiểu:

```text
temp
new
final_final
result2
test123
```

Tên file phải mô tả đúng nội dung.

---

## 14. Coding Rules

Quy ước Python:

```text
module/function: snake_case
class: PascalCase
constant: UPPER_SNAKE_CASE
path handling: pathlib.Path
```

Code phải:

```text
có ownership rõ ràng
dùng focused functions
tránh hidden mutation
tránh absolute paths
tránh broad exception swallowing
không fabricate result
```

---

## 15. Reproducibility

Khi có randomness:

```text
dùng explicit seed
ghi lại seed
không phụ thuộc hidden notebook state
giữ processing deterministic khi có thể
```

Notebook phải chạy được theo intended order sau kernel restart.

Canonical end-to-end validation phải dùng kernel `time-series-practice-1`, chạy tests
trước, sau đó execute notebook bằng command được khóa trong master plan.

---

## 16. Change-Control Gate

Cần Human approval trước khi:

```text
đổi canonical folder structure
chuyển responsibility giữa các module
đổi data lifecycle
thêm top-level folder mới
đổi notebook/source ownership
đổi forecasting split protocol
đổi evaluation protocol
```

Không được âm thầm sửa architecture document để hợp thức hóa một implementation đã vi phạm kiến trúc.

---

## 17. Validation Checklist

Trước khi báo một exercise complete:

```text
[ ] Requirement đã được đáp ứng.
[ ] Relevant code chạy được.
[ ] Raw dataset không bị thay đổi.
[ ] Time order được bảo toàn.
[ ] Không có silent data repair.
[ ] Không có data leakage.
[ ] Missing/outlier experiment chỉ tác động working copy.
[ ] Statistical conclusion có execution evidence.
[ ] Expected outputs tồn tại.
[ ] Result đã được kiểm tra thực tế.
[ ] Documentation phản ánh đúng current state.
[ ] Không sửa unrelated file.
```

---

## 18. Activation Gate

Tài liệu này chỉ active sau khi Human approval.

Trạng thái hiện tại:

```text
ARCHITECTURE_RULE_CREATED=true
ARCHITECTURE_RULE_APPROVED=true
IMPLEMENTATION_GOVERNED_BY_THIS_RULE=true
```

Human approval recorded for Practice 1 scoped architecture governance.
