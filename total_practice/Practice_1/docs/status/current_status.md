# PRACTICE 1 — CURRENT STATUS

## 1. Status Identity

```text
Practice: Practice_1
Document type: Current Flow / Current Status
Primary dataset: AirPassengers
Current stage: EXERCISE_5_COMPLETED / PRACTICE_1_TECHNICAL_CLOSURE_COMPLETED
Implementation started: YES
Model training required: NO
```

Tài liệu này là nguồn trạng thái hiện tại của Practice 1.

Mục đích:

- giúp Human và agent biết project đang ở đâu;
- tránh chạy lại công việc đã hoàn thành;
- chỉ rõ task hiện tại;
- chỉ rõ bước tiếp theo;
- ghi blocker trước khi implementation.

---

## 2. Completed

Các công việc đã hoàn thành:

```text
[COMPLETED] Project folder structure for Practice 1 created
[COMPLETED] Scoped rule documents created
[COMPLETED] Practice 1 requirements reviewed
[COMPLETED] Practice 1 overview created
[COMPLETED] Practice 1 scientific scope defined
[COMPLETED] Dataset direction selected: AirPassengers
[COMPLETED] Exercise 1 specification created
[COMPLETED] Exercise 2 specification created
[COMPLETED] Exercise 3 specification created
[COMPLETED] Exercise 4 specification created
[COMPLETED] Exercise 5 specification created
[COMPLETED] Master before-process plan created
[COMPLETED] Exercise 1 before-process plan created
[COMPLETED] Exercise 2 before-process plan created
[COMPLETED] Exercise 3 before-process plan created
[COMPLETED] Exercise 4 before-process plan created
[COMPLETED] Exercise 5 before-process plan created
[COMPLETED] AirPassengers canonical source contract standardized
[COMPLETED] Exercise 1–5 scientific parameters standardized for Human review
[COMPLETED] Exercise 6 excluded from AI planning and retained as TuVien-owned Word report
[COMPLETED] Practice 1 architecture rule approved and activated by Human
[COMPLETED] Practice 1 code/execution rule approved and activated by Human
[COMPLETED] Group 1 runtime/package/import contract standardized
[COMPLETED] Group 2 scientific API details standardized
[COMPLETED] Group 3 minimum test matrix and validation commands standardized
[COMPLETED] Group 4 Python 3.12 environment and editable package initialized
[COMPLETED] AirPassengers raw dataset acquired and integrity-verified
[COMPLETED] Reusable data, ACF/PACF, and plotting modules implemented
[COMPLETED] Exercise 1 notebook executed end-to-end
[COMPLETED] Exercise 1 tests, figures, tables, and findings validated
[COMPLETED] practice_1_present.ipynb confirmed as the sole primary notebook
[COMPLETED] Exercise 1 notebook alignment fix implemented and validated
[COMPLETED] Exercise 2 specification and before-process plan approved
[COMPLETED] Reusable white-noise generator and visualization logic implemented
[COMPLETED] Exercise 2 notebook cells 22–27 aligned and executed
[COMPLETED] Exercise 2 tests, figures, ACF table, and interpretation validated
[COMPLETED] Practice 1 folders standardized to datasets and simplified docs structure
[COMPLETED] Error-analysis and fix-plan workflow standardized in dedicated folders
[COMPLETED] Exercise 3 error analysis and fix plan approved
[COMPLETED] Reusable log-STL decomposition and residual diagnostic logic implemented
[COMPLETED] Exercise 3 notebook cells 28–31 aligned and executed
[COMPLETED] Exercise 3 tests, figures, component table, diagnostics, and interpretation validated
[COMPLETED] Exercise 4 error analysis and fix plan approved
[COMPLETED] Reusable missing-value and residual-IQR logic implemented
[COMPLETED] Exercise 4 notebook cells 32–44 aligned and executed
[COMPLETED] Exercise 4 tests, figures, result tables, and interpretation validated
[COMPLETED] Exercise 5 error analysis and fix plan approved
[COMPLETED] Reusable rolling-statistics and seasonal-matrix logic implemented
[COMPLETED] Exercise 5 notebook cells 45–51 aligned and executed
[COMPLETED] Exercise 5 tests, four figures, rolling table, and interpretation validated
[COMPLETED] Practice 1 technical closure for Exercise 1–5
```

Exercise 6 không có exercise specification riêng.

Exercise 6 được xem là:

```text
User-owned Final Word Report
```

TuVien tự viết báo cáo trên Word. Agent không tạo exercise specification, before-process
plan hoặc report artifact cho Exercise 6; phần AI implementation dừng ở validated
evidence từ Exercise 1–5.

---

## 3. Current

Task hiện tại:

```text
Exercise 1–5 implementation completed and validated; evidence ready for TuVien report
```

Notebook chính và duy nhất là:

```text
notebooks/practice_1_present.ipynb
```

Initialization và Exercise 1–5 đã có bằng chứng thực thi thực tế. E3 dùng natural-log
transform, STL `period=12`, `robust=True`, residual ACF 40 lag và Ljung–Box lag 12.
E4 mô phỏng đúng 6 giá trị thiếu đã khóa, so sánh forward fill với nội suy theo thời
gian bằng MAE, đồng thời chỉ gắn cờ ứng viên ngoại lai trên residual E3. E5 dùng
trailing rolling 12 tháng, monthly seasonal plot và heatmap 12 × 12, đồng thời đối
chiếu E1, E3 và E4. Notebook đã chạy sạch toàn bộ 52 cell bằng kernel Python 3.12.

---

## 4. Next

Thứ tự tiếp theo:

```text
1. Human reviews the validated Exercise 5 and technical-closure evidence.
2. Hand validated Exercise 1–5 evidence to TuVien for the user-owned Word report.
3. Reopen implementation only if Human identifies a concrete correction.
```

---

## 5. Blockers

### Resolved — Exercise 4 scientific parameters

```text
Masked observations: 6
Isolated timestamps: 1952-03, 1954-11, 1959-04
Consecutive block: 1956-06 through 1956-08
Metric: MAE on masked positions only
Outlier method: IQR multiplier 1.5 on natural-log STL residual
Action: flag and inspect only
```

### Resolved — Scoped-rule approval

Practice architecture/code rules đã được Human phê duyệt và kích hoạt:

```text
ARCHITECTURE_RULE_APPROVED=true
RULE_CODE_APPROVED=true
```

### Resolved — Implementation authorization

Master initialization plan và Exercise 1 before-process plan đã được Human phê duyệt:

```text
IMPLEMENTATION_AUTHORIZED=true
```

theo governance rule hiện hành.

Nhóm 4 được phép tạo environment, package, config, tests, notebook, raw dataset và
Exercise 1 outputs trong phạm vi approved plan.

### Resolved — Dataset provenance and integrity

AirPassengers đã được tải từ canonical URL đã duyệt:

```text
https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv
```

Actual verification:

```text
Schema: rownames, time, value
Rows: 144
Time range after deterministic monthly reconstruction: 1949-01 through 1960-12
Frequency: monthly
Missing values: 0
Duplicate timestamps: 0
SHA-256: bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8
```

### Group 4 execution prerequisites

```text
[SATISFIED] Python 3.12.15 available
[SATISFIED] .venv created
[SATISFIED] pyproject.toml dependencies installed
[SATISFIED] practice_1 installed in editable mode
[SATISFIED] time-series-practice-1 kernel registered
[SATISFIED] resolved versions recorded in docs/logs/environment_snapshot.txt
[SATISFIED] dataset source, schema, chronology, and checksum verified
```

---

## 6. Scientific Configuration

Shared configuration hiện tại:

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
Decomposition: natural-log transform + STL
STL period: 12
STL robust: True
Missing observations: 6 at locked timestamps
Outlier method: IQR 1.5 on natural-log STL residual
Model training: NO
Forecast generation: NO
Forecast model evaluation: NO
```

Các config trên không được tự đổi trong implementation.

---

## 7. Exercise Status

### Exercise 1 — ACF/PACF

```text
Specification: APPROVED
Before-process plan: APPROVED
Implementation: COMPLETED
Validation: COMPLETED
Status: COMPLETED
```

### Exercise 2 — White Noise

```text
Specification: APPROVED
Before-process plan: APPROVED
Implementation: COMPLETED
Validation: COMPLETED
Status: COMPLETED
```

### Exercise 3 — Decomposition

```text
Specification: APPROVED
Before-process plan: APPROVED
Implementation: COMPLETED
Validation: COMPLETED
Status: COMPLETED
```

### Exercise 4 — Data Quality

```text
Specification: APPROVED
Before-process plan: APPROVED
Implementation: COMPLETED
Validation: COMPLETED
Scientific parameters: LOCKED_FOR_REVIEW
Upstream Exercise 3 dependency: SATISFIED
Status: COMPLETED
```

### Exercise 5 — Visualization

```text
Specification: APPROVED
Before-process plan: APPROVED
Implementation: COMPLETED
Validation: COMPLETED
Upstream Exercise 1, 3 and 4 evidence: SATISFIED
Status: COMPLETED
```

### Exercise 6 — Final Word Report

```text
Separate exercise specification: NOT_REQUIRED
Implementation: NOT_STARTED
Input dependency: validated outputs from Exercise 1–5 — SATISFIED
Expected deliverable: managed by TuVien outside the AI implementation plan
Status: READY_FOR_USER_REPORT
```

---

## 8. Expected Final Deliverables

### Figures

```text
01_time_series_overview.png
02_acf_40_lags.png
03_pacf_40_lags.png
04_white_noise_series.png
05_white_noise_acf.png
06_white_noise_vs_airpassengers_acf.png
07_log_transformed_series.png
08_stl_decomposition.png
09_decomposition_residual.png
10_missing_values_simulation.png
11_missing_treatment_comparison.png
12_outlier_analysis.png
13_full_time_series.png
14_rolling_mean_std.png
15_monthly_seasonal_plot.png
16_month_year_heatmap.png
```

### Results

Có thể gồm:

```text
acf_values.csv
pacf_values.csv
white_noise_acf_values.csv
white_noise_diagnostics.csv
decomposition_components.csv
residual_diagnostics.csv
missing_value_comparison.csv
outlier_candidates.csv
rolling_statistics.csv
```

Chỉ tạo optional results khi có giá trị cho traceability hoặc downstream reuse.

### Final Report

Word report path and file lifecycle are managed by TuVien. No report file is created
or modified by the agent in the Exercise 1–5 implementation plan.

---

## 9. Data Integrity State

Hiện tại các rule phải tiếp tục được giữ:

```text
raw data immutable
chronological order preserved
timestamp semantics preserved
no random shuffle
no silent data repair
no future leakage
no automatic outlier deletion
no fabricated results
```

Không có cleaned forecasting dataset nào được phê duyệt trong Practice 1.

---

## 10. Current Flow Summary

```text
Planning
  ✅ Overview
  ✅ Exercise 1 specification
  ✅ Exercise 2 specification
  ✅ Exercise 3 specification
  ✅ Exercise 4 specification
  ✅ Exercise 5 specification
  ✅ Master before-process plan
  ✅ Exercise 1 before-process plan
  ✅ Exercise 2 before-process plan
  ✅ Exercise 3 before-process plan
  ✅ Exercise 4 before-process plan
  ✅ Exercise 5 before-process plan

Current
  → Exercise 1–5 completed and validated
  → Practice 1 technical implementation closed
  → Validated evidence ready for TuVien-owned Word report

Implementation
  ✅ INITIALIZATION_COMPLETED
  ✅ EXERCISE_1_COMPLETED
  ✅ EXERCISE_2_COMPLETED
  ✅ EXERCISE_3_COMPLETED
  ✅ EXERCISE_4_COMPLETED
  ✅ EXERCISE_5_COMPLETED
  ✅ PRACTICE_1_TECHNICAL_CLOSURE_COMPLETED

Next execution target
  → No remaining AI implementation exercise; TuVien may prepare the Word report
```

---

## 11. State Update Rule

File này phải được cập nhật khi xảy ra một trong các sự kiện:

```text
an exercise starts
an exercise becomes blocked
an exercise completes validation
a scientific parameter changes
a new blocker appears
a blocker is resolved
implementation authorization changes
TuVien reports an Exercise 6 status change
Practice 1 reaches closure
```

Không cập nhật status dựa trên dự đoán.

Chỉ ghi trạng thái dựa trên actual project evidence.

---

## 12. Current Authorization State

```text
PLANNING_DOCUMENTS_CREATED=true
EXERCISE_SPECIFICATIONS_CREATED=true
BEFORE_PROCESS_PLANS_CREATED=true
IMPLEMENTATION_STARTED=true
INITIALIZATION_COMPLETED=true
EXERCISE_01_COMPLETED=true
INITIALIZATION_AND_EXERCISE_01_AUTHORIZATION_CONSUMED=true
EXERCISE_02_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_02_COMPLETED=true
EXERCISE_02_AUTHORIZATION_CONSUMED=true
EXERCISE_03_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_03_COMPLETED=true
EXERCISE_03_AUTHORIZATION_CONSUMED=true
EXERCISE_04_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_04_COMPLETED=true
EXERCISE_04_AUTHORIZATION_CONSUMED=true
EXERCISE_05_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_05_COMPLETED=true
EXERCISE_05_AUTHORIZATION_CONSUMED=true
PRACTICE_1_TECHNICAL_CLOSURE_COMPLETED=true
PRACTICE_1_COMPLETED=true
```

Không còn exercise implementation nào đang chờ authorization trong Practice 1.
