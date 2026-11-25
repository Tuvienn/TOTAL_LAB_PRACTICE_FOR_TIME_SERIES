# PHASE 05 — EXECUTION LOG

## 1. Scope

Triển khai one-step X/y alignment, sample eligibility và five-fold expanding-window application trên development period. Phase này không impute, không scale, không train model, không tính metric và không materialize holdout hoặc recursive 24-hour matrix.

## 2. Official execution

```bash
MPLCONFIGDIR=/private/tmp/practice3v2-mpl \
.venv/bin/python -m practice_3.data.supervised_dataset
```

Official result:

```text
outputs/results/phase_05_supervised_dataset.json
SHA256: 261dc58db3bfd4621c444c6c08fc51182622247239d8c1f5b848ee08dc7a59e0
```

Không có X/y CSV hoặc Parquet được tạo.

## 3. Alignment result

```text
Sample key: target timestamp T
Forecast origin: T - 1 hour
X: exact 22-feature order
y: AEP_MW(T)
Primary horizon: 1 hour
```

Target, timestamp, metadata, eligibility và exclusion reason không nằm trong X.

## 4. Eligibility result

```text
Development candidate rows: 112,535
Eligible samples: 108,083
Excluded samples: 4,452
Invalid feature vector: 4,427
Missing target with valid features: 25
Eligible start: 2004-10-08 01:00:00
Eligible end: 2017-08-02 23:00:00
```

Ba nhóm exclusion là mutually exclusive. Không feature hoặc target nào được impute.

## 5. Fold result

| Fold | Train raw | Train eligible | Validation raw | Validation eligible |
|---:|---:|---:|---:|---:|
| 1 | 68.711 | 65.670 | 8.760 | 8.253 |
| 2 | 77.471 | 73.923 | 8.760 | 8.363 |
| 3 | 86.231 | 82.286 | 8.760 | 8.591 |
| 4 | 94.991 | 90.877 | 8.784 | 8.615 |
| 5 | 103.775 | 99.492 | 8.760 | 8.591 |

Tất cả raw counts khớp Phase 2. Train mở rộng theo thời gian, validation sau train, không overlap, không shuffle và gap bằng 0.

## 6. Protocol boundary

- One-step validation dùng actual history đến `T-1 giờ`; actual của giờ validation trước được phép cập nhật cho giờ kế tiếp.
- Recursive 24-hour matrix không được tạo trong Phase 5.
- Holdout features không được materialize và holdout target statistics không được báo cáo.
- Mọi baseline/model ở Phase 6 phải dùng cùng eligible timestamps trong từng fold.

## 7. Validation evidence

```text
Focused Phase 5 tests: 17/17 PASS
Full Practice 3 regression suite: 82/82 PASS
Exact X schema/order: PASS
X/y timestamp alignment: PASS
Eligible X/y finite: PASS
Exclusion accounting: PASS
Five-fold chronology/non-overlap: PASS
Current/future-target mutation isolation: PASS
Holdout-mutation isolation: PASS
Input immutability: PASS
Deterministic JSON: PASS
Legacy runtime import: NONE
git diff --check: PASS
```

## 8. Notebook boundary

Notebook chỉ đọc official Phase 5 audit để trình bày alignment, exclusion accounting và fold counts. Notebook không gọi feature builder hoặc supervised-data source.

```text
Scope: Phase 0–5
Clean-kernel execution: PASS
Executed code cells: 17/17
Error outputs: 0
Pipeline/training/prediction calls: NONE
```

## 9. Completion state

```text
Phase 5 technical status: PASS
Human result review: APPROVED
Phase 6 design/implementation: NOT AUTHORIZED
```
