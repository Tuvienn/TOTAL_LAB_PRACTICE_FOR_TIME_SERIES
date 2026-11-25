# PHASE 02 — TEMPORAL SPLIT & VALIDATION DESIGN

## 1. Phase identity

```text
Project: Practice_3
Phase: 2
Name: Temporal Split & Validation Design
Design status: APPROVED
Human approval: GRANTED
Implementation authorization: GRANTED
Execution status: PASS — AWAITING HUMAN REVIEW
```

## 2. Mục tiêu

Khóa ranh giới thời gian cho development, expanding-window validation và historical re-evaluation holdout trước khi EDA hoặc feature engineering bắt đầu.

```text
prepared hourly dataset
→ validate Phase 1 identity
→ assign development/holdout boundaries
→ define five expanding-window folds
→ audit chronology, coverage and overlap
→ serialize split contract and audit
```

Phase này không thực hiện EDA, feature engineering, X/y construction, scaling, model training, prediction hoặc metric evaluation.

## 3. Input contract

Prepared input:

```text
datasets/processed/aep_hourly_prepared.csv
```

Required Phase 1 identity:

```text
Prepared SHA256: 5b61ab66e585ba479233e7a5597fa42fc5f73bc54c46317b1408bd7a65cab587
Rows: 121,296
Start: 2004-10-01 01:00:00
End: 2018-08-03 00:00:00
Frequency: hourly
Missing targets: 27
Timestamp unique: true
Timeline continuous: true
```

Canonical upstream evidence:

```text
config/forecasting_contract.json
config/data_preparation.json
outputs/results/phase_01_data_quality.json
```

Pipeline phải dừng nếu prepared checksum, schema, timestamp range hoặc structural invariants không khớp upstream evidence.

## 4. Split semantics

### 4.1 Timestamp ownership

Split được xác định bằng **target timestamp** của giá trị cần dự báo.

Với primary one-step task:

```text
forecast origin = t
available target history = through t
target timestamp = t + 1 hour
```

Quy ước này phải được giữ trong Phase 5 khi xây dựng X/y. Không được đổi sang split bằng row order hoặc feature timestamp mà không có Human approval.

### 4.2 Development period

```text
Start: 2004-10-01 01:00:00
End exclusive: 2017-08-03 00:00:00
Rows: 112,535
Observed targets: 112,509
Missing targets: 26
```

Development period được dùng cho TRAIN-only EDA, feature design và model selection. Mọi target timestamp phải thỏa:

```text
target_timestamp < 2017-08-03 00:00:00
```

### 4.3 Historical re-evaluation holdout

```text
Start inclusive: 2017-08-03 00:00:00
End inclusive: 2018-08-03 00:00:00
Rows: 8,761
Observed targets: 8,760
Missing targets: 1
```

End boundary là inclusive để giữ timestamp cuối của source dataset. Mọi holdout target timestamp phải thỏa:

```text
2017-08-03 00:00:00 <= target_timestamp <= 2018-08-03 00:00:00
```

Holdout đã từng được quan sát trong legacy implementation, vì vậy chỉ được gọi là `historical_re_evaluation_holdout`; không được gọi là unseen hoặc untouched final test.

## 5. Expanding-window cross-validation

### 5.1 General policy

```text
Method: expanding window
Number of folds: 5
Shuffle: false
Gap: 0 hours
Validation duration: one calendar year per fold
Selection task: primary one-step forecasting only
```

Mỗi fold fit model một lần trên fold-train. Trong one-step validation, actual target mới có thể trở thành lagged history ở forecast origin kế tiếp vì update cadence đã được chốt là hourly.

`gap = 0` không gây leakage: target của fold-train luôn đứng trước target của fold-validation và không có target timestamp overlap. Recursive 24-hour là secondary stress test, không dùng để định nghĩa CV selection gap.

### 5.2 Exact fold boundaries

Khoảng validation dùng quy ước start inclusive, end exclusive.

| Fold | Train end | Train rows | Train observed | Validation range | Validation rows | Validation observed | Validation missing |
|---:|---|---:|---:|---|---:|---:|---:|
| 1 | `2012-08-02 23:00` | 68,711 | 68,694 | `[2012-08-03 00:00, 2013-08-03 00:00)` | 8,760 | 8,757 | 3 |
| 2 | `2013-08-02 23:00` | 77,471 | 77,451 | `[2013-08-03 00:00, 2014-08-03 00:00)` | 8,760 | 8,757 | 3 |
| 3 | `2014-08-02 23:00` | 86,231 | 86,208 | `[2014-08-03 00:00, 2015-08-03 00:00)` | 8,760 | 8,759 | 1 |
| 4 | `2015-08-02 23:00` | 94,991 | 94,967 | `[2015-08-03 00:00, 2016-08-03 00:00)` | 8,784 | 8,783 | 1 |
| 5 | `2016-08-02 23:00` | 103,775 | 103,750 | `[2016-08-03 00:00, 2017-08-03 00:00)` | 8,760 | 8,759 | 1 |

Fold 4 có 8,784 timestamp vì validation window chứa ngày nhuận năm 2016. Đây là expected calendar behavior, không phải lỗi split.

## 6. Missing-target policy

Phase 2 giữ nguyên toàn bộ 27 target thiếu trên timeline.

```text
timeline membership: retained
target_available: false
imputation: none
training-label eligibility: false
metric eligibility: false
```

Phase này không tự quyết định feature-row eligibility. Việc loại sample vì target hoặc lag/rolling input thiếu thuộc Phase 5 — X/y Construction & Split Application.

## 7. Holdout isolation policy

Trước model lock:

- Không đọc holdout target để tính distribution, trend, seasonality, outlier hoặc correlation.
- Không dùng holdout để chọn lag, rolling window, feature, model hoặc hyperparameter.
- Chỉ được audit structural membership, timestamp coverage và target availability đã biết từ Phase 1.
- Phase 3 EDA chỉ nhận development subset.
- Holdout evaluation chỉ được mở trong Phase 7 sau khi Phase 6 model lock hoàn thành.

## 8. Proposed implementation ownership

```text
config/temporal_split.json
src/practice_3/data/temporal_split.py
tests/test_temporal_split.py
outputs/results/phase_02_temporal_split.json
docs/logs/PHASE_02_EXECUTION.md
```

Không tạo split CSV mới. Prepared dataset tiếp tục là canonical data artifact; downstream code phải áp dụng boundary qua owner duy nhất trong `temporal_split.py`.

Proposed functions:

```text
load_temporal_split_contract
validate_prepared_input
build_development_holdout_masks
build_expanding_window_folds
validate_temporal_split
build_phase_02_audit
save_phase_02_artifact
run_phase_02
```

Source code, identifier, exception và docstring dùng tiếng Anh. Không import runtime code hoặc official output từ legacy implementation.

## 9. Configuration contract

`config/temporal_split.json` phải lưu ít nhất:

- target timestamp semantics;
- development start và end-exclusive;
- holdout start-inclusive và end-inclusive;
- holdout label và claim boundary;
- CV method, fold count, shuffle và gap;
- exact validation start/end-exclusive của năm folds;
- missing-target policy;
- expected prepared SHA256;
- approved status và contract version.

Không hard-code các boundary khoa học chỉ trong source code.

## 10. Audit contract

Official audit:

```text
outputs/results/phase_02_temporal_split.json
```

Audit phải chứa ít nhất:

- phase và contract version;
- prepared input path và SHA256;
- timestamp semantics;
- development và holdout boundaries;
- inclusive/exclusive convention;
- row, observed-target và missing-target counts;
- exact fold boundaries và counts;
- chronology, overlap, coverage và expansion checks;
- shuffle và gap policy;
- holdout label và claim boundary;
- final status.

Audit không chứa target descriptive statistics, EDA finding, feature recommendation hoặc model metric.

## 11. Validation and test contract

Focused tests phải kiểm tra:

1. Prepared input tồn tại và checksum khớp Phase 1.
2. Prepared schema, timestamp range và hourly continuity hợp lệ.
3. Development/holdout boundaries đúng target-timestamp semantics.
4. Holdout end-inclusive giữ timestamp cuối dataset.
5. Development và holdout không overlap.
6. Development cộng holdout phủ đủ 121,296 timestamps.
7. Development/holdout counts và missing-target counts khớp contract.
8. Có đúng năm expanding-window folds.
9. Fold-train luôn đứng trước fold-validation.
10. Fold-train mở rộng đơn điệu.
11. Validation folds không overlap và nằm hoàn toàn trong development.
12. Fold counts, leap-year behavior và target availability khớp contract.
13. `shuffle = false` và `gap = 0` được giữ nguyên.
14. Split deterministic qua nhiều lần chạy.
15. Invalid boundary, checksum hoặc overlap làm pipeline dừng.
16. Không có runtime import từ legacy implementation.

Trước bàn giao phải chạy focused tests, full Practice 3 regression suite và `git diff --check`.

## 12. Atomic and deterministic artifact policy

Official split audit phải được tạo theo quy trình:

```text
build in memory
→ validate in memory
→ write temporary JSON
→ read temporary JSON back
→ validate serialized artifact
→ promote to official path
```

Cùng prepared input và approved configuration phải tạo cùng scientific split fields. Runtime metadata không được làm thay đổi deterministic scientific content.

## 13. Completion gate

Phase 2 chỉ được đánh dấu `PASS` khi:

- temporal split config đã được Human duyệt;
- source owner và focused tests đã tồn tại;
- official audit được tạo và validate;
- prepared checksum khớp Phase 1;
- chronology, overlap, coverage và fold-expansion checks đều PASS;
- full regression suite PASS;
- execution log và current status được đồng bộ;
- Human review kết quả Phase 2.

Sau Phase 2 mới được thiết kế Phase 3 — TRAIN-only EDA.
