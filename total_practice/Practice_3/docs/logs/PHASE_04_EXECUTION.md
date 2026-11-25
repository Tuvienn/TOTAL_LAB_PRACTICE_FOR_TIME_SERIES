# PHASE 04 — EXECUTION LOG

## 1. Scope

Triển khai feature engineering dùng chung cho one-step và recursive forecasting. Phase này chỉ tạo feature logic và validation audit trên development period; không tạo X/y population, không loại sample, không impute, không train model và không tính metric trên holdout.

## 2. Environment

```text
Python: 3.14.3
NumPy: 2.5.4
pandas: 3.1.0
pytest: 9.1.1
Package mode: editable local install
```

## 3. Official execution

```bash
.venv/bin/python -m practice_3.analysis.feature_engineering
```

Official result:

```text
outputs/results/phase_04_feature_validation.json
SHA256: 3d4c94bf2a260669c982a3d867bcda6d39aeb3067cd3f2c08ceb7bf607584760
```

## 4. Approved feature schema

```text
Lag features: 8
Shifted rolling features: 4
Calendar features: 10
Total: 22
```

Lag features:

```text
lag_1h, lag_2h, lag_3h, lag_23h,
lag_24h, lag_25h, lag_48h, lag_168h
```

Rolling features:

```text
rolling_mean_24h, rolling_std_24h,
rolling_mean_168h, rolling_std_168h
```

Mọi rolling feature dùng `target.shift(1)` trước trailing window; `std` dùng `ddof=1`. Calendar feature được lấy từ target timestamp vì lịch đã biết trước.

## 5. Development-only result

```text
Development rows: 112,535
Rows with all 22 features: 108,108
First fully available timestamp: 2004-10-08 01:00:00
Holdout rows used for feature calculation: 0
Imputation applied: false
Rows dropped: false
```

Số null của lag/rolling phản ánh initial history và 26 missing targets được giữ nguyên. Phase 5 chịu trách nhiệm chốt sample eligibility.

## 6. Leakage and recursive-safety evidence

```text
Current target excluded: PASS
Future target excluded: PASS
Target-time metadata excluded: PASS
Phase 3 anomaly flag excluded: PASS
Centered rolling excluded: PASS
Holdout-mutation isolation: PASS
Current/future-target mutation isolation: PASS
Batch/recursive feature parity: PASS
Recursive prediction append behavior: PASS
```

Feature row tại `T` chỉ dùng target history đến `T-1 giờ`. Hàm recursive row builder từ chối history chứa target hoặc future timestamp và dùng prediction đã append cho bước kế tiếp.

## 7. Validation evidence

```text
Focused Phase 4 tests: 17/17 PASS
Full Practice 3 regression suite: 65/65 PASS
Official artifact deterministic: PASS
Exact 22-feature order: PASS
Calendar range checks: PASS
Infinite values: NONE
Input mutation: NONE
Legacy runtime import: NONE
git diff --check: PASS
```

## 8. Notebook boundary

Notebook chỉ đọc official Phase 4 audit để trình bày feature dictionary, null counts và leakage controls. Notebook không tạo feature matrix và không chạy source pipeline.

## 9. Completion state

```text
Phase 4 technical status: PASS
Human result review: APPROVED
Phase 5 design/implementation: NOT AUTHORIZED
```
