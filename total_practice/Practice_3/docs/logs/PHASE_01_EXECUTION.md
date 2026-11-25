# PHASE 01 — EXECUTION LOG

## 1. Scope

Triển khai và xác minh Structural Data Preparation từ raw `AEP_hourly.csv` đến prepared CSV và machine-readable audit. Phase này không thực hiện split, EDA, feature engineering, training hoặc prediction.

## 2. Environment

```text
Python: 3.14.3
NumPy: 2.5.4
pandas: 3.1.0
pytest: 9.1.1
Package mode: editable local install
```

Môi trường riêng:

```text
Practice_3/.venv
```

## 3. Official execution

```bash
.venv/bin/python -m practice_3.data.data_preparation
```

Official outputs:

```text
datasets/processed/aep_hourly_prepared.csv
outputs/results/phase_01_data_quality.json
```

## 4. Checksums

```text
Raw CSV:
109d122f7b485555c609eecdec2cd5a03172e0a08acd358d863acc93eb452585

Prepared CSV:
5b61ab66e585ba479233e7a5597fa42fc5f73bc54c46317b1408bd7a65cab587

Audit JSON:
d53235227f6375c2b75e9e695848a953151823daa8c1a3af16834ce36bf8fe0a
```

Raw checksum trước và sau execution giống nhau.

## 5. Result summary

```text
Raw rows: 121,273
Prepared rows: 121,296
Unique prepared timestamps: 121,296
Duplicate rows before: 8
Duplicate timestamps before: 4
Duplicate timestamps after: 0
Missing hourly timestamps inserted: 27
Missing targets preserved: 27
source_count = 0: 27
source_count = 1: 121,265
source_count = 2: 4
sum(source_count): 121,273
Timeline continuous hourly: true
Status: PASS
```

Audit lưu danh sách cụ thể của 4 duplicate timestamps và 27 missing timestamps.

## 6. Validation

```text
Phase 0 contract tests: PASS
Phase 1 focused tests: PASS
Full Practice 3 regression suite: 20/20 PASS
Serialized artifact validation: PASS
Independent checksum/count recalculation: PASS
Deterministic official rerun: PASS
git diff --check: PASS
Legacy runtime import: NONE
```

Deterministic official rerun giữ nguyên prepared SHA256:

```text
5b61ab66e585ba479233e7a5597fa42fc5f73bc54c46317b1408bd7a65cab587
```

## 7. Implementation notes

Trong pre-official validation, một path-identity issue xuất hiện khi test ghi artifact ngoài project root. Fix đã được Human duyệt và chỉ thay đổi serialization metadata path handling; data-treatment logic không thay đổi. Official artifacts chưa được tạo tại thời điểm issue xảy ra.

## 8. Notebook presentation

Notebook trình bày:

```text
notebooks/Practice_3_present.ipynb
Scope: Phase 0–1
Mode: read-only artifact presentation
Clean-kernel execution: PASS
Executed code cells: 5/5
Error outputs: 0
Pipeline/training/prediction calls: NONE
```

Notebook chỉ đọc forecasting contract, data contract, prepared CSV và audit JSON chính thức. Notebook không tái chạy data-preparation pipeline; EDA chưa được đưa vào Phase 1 vì phải thực hiện trên TRAIN sau Phase 2.

## 9. Completion

```text
Phase 1 status: PASS
Next phase: Phase 2 — Temporal Split & Validation Design
Phase 2 implementation authorization: NOT GRANTED
```
