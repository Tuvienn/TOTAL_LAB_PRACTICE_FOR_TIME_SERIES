# PHASE 04 — TEMPORAL SPLIT & VALIDATION DESIGN

## 1. Phase Identity

**Phase:** 04  
**Name:** Temporal Split & Validation Design  
**Practice:** Practice 3 — Machine Learning Time Series Forecasting  
**Status:** `APPROVED_WAITING_PHASE_03_PASS`  
**Implementation authorized:** `YES_AFTER_PHASE_03_PASS`  
**Approved by:** `Human`  
**Approval date:** `2026-10-16`

## 2. Objective

Tạo một temporal split và validation design dùng chung cho sáu supervised configurations của Phase 3, bảo đảm final test được cô lập khỏi feature selection, tuning và model selection.

```text
Phase 3 common timestamp population
    ↓
one shared top-level temporal split
    ├── TRAIN
    │     └── shared expanding-window TimeSeriesSplit
    └── SEALED FINAL TEST
```

Phase này không train model, không tuning, không tính test metrics và không chọn configuration tốt nhất.

## 3. Input and Entry Gate

Input từ Phase 3 gồm sáu configurations:

```text
lag_only_p24
lag_only_p72
lag_only_p168
lag_rolling_p24
lag_rolling_p72
lag_rolling_p168
```

Mỗi configuration phải có:

```text
X
y
timestamp_index
feature_names
aligned_metadata
```

Phase 4 chỉ được thực thi khi:

```text
Phase 1 = PASS
Phase 2 = PASS
Phase 3 = PASS
```

Entry contract:

- cả sáu configurations có chung 116.675 timestamp;
- timestamp tăng dần và không trùng;
- `X/y/metadata` alignment hợp lệ;
- `X/y` không còn `NaN`, `inf` hoặc `-inf`;
- common mask và feature definitions không được thay đổi trong Phase 4.

## 4. Approved Top-level Split

### 4.1 Cutoff

```text
test_start = 2017-08-03 00:00:00
```

Quy tắc:

```text
TRAIN: timestamp <  2017-08-03 00:00:00
TEST:  timestamp >= 2017-08-03 00:00:00
```

Cutoff theo thời gian được chọn thay cho ratio-based split để final test bao phủ khoảng một năm lịch và dễ truy vết.

### 4.2 Expected Boundaries and Counts

```text
train_rows = 108083
train_start = 2004-10-08 01:00:00
train_end = 2017-08-02 23:00:00

test_rows = 8592
test_start = 2017-08-03 00:00:00
test_end = 2018-08-03 00:00:00

total_rows = 116675
```

Final test không có đủ mọi clock-hour của một năm vì common validity mask Phase 3 đã loại vùng bị ảnh hưởng bởi missing target. Phase 4 không được bổ sung, fill hoặc khôi phục các timestamp đã bị mask.

## 5. Approved TimeSeriesSplit Configuration

`TimeSeriesSplit` chỉ áp dụng trên top-level training set:

```text
strategy = expanding_window
n_splits = 5
test_size = 2160
gap = 0
max_train_size = null
```

`test_size = 2160` tương đương 90 ngày theo số hourly samples hợp lệ. Do common timestamp index có các vùng bị loại, calendar duration thực tế của một validation fold có thể dài hơn 90 ngày.

Expected fold sample counts:

| Fold | Train samples | Validation samples |
|---|---:|---:|
| 1 | 97.283 | 2.160 |
| 2 | 99.443 | 2.160 |
| 3 | 101.603 | 2.160 |
| 4 | 103.763 | 2.160 |
| 5 | 105.923 | 2.160 |

Expected timestamp boundaries:

| Fold | Train end | Validation start | Validation end |
|---|---|---|---|
| 1 | `2016-05-02 22:00:00` | `2016-05-02 23:00:00` | `2016-07-31 22:00:00` |
| 2 | `2016-07-31 22:00:00` | `2016-07-31 23:00:00` | `2016-10-29 22:00:00` |
| 3 | `2016-10-29 22:00:00` | `2016-10-29 23:00:00` | `2017-01-27 22:00:00` |
| 4 | `2017-01-27 22:00:00` | `2017-01-27 23:00:00` | `2017-05-04 23:00:00` |
| 5 | `2017-05-04 23:00:00` | `2017-05-05 00:00:00` | `2017-08-02 23:00:00` |

Các giá trị trên là expected acceptance values, không phải execution result. Implementation phải tính lại từ output thật và dừng nếu sai lệch chưa giải thích được.

## 6. Gap Decision and Forecasting Scope

`gap = 0` được duyệt cho core one-step forecasting vì feature của validation sample đầu tiên chỉ dùng historical target đã tồn tại trước forecast timestamp. Lag tham chiếu đến cuối fold train là thông tin hợp lệ tại forecast origin.

TimeSeriesSplit trong Phase 4 phục vụ core one-step training/tuning protocol. Nếu Phase 6 chọn direct multi-step hoặc một target construction có overlapping future labels, Phase 4 phải được mở lại để đánh giá horizon-specific gap. Không được âm thầm dùng `gap = 0` cho protocol khác.

## 7. Shared-index Policy

Split indices phải được tạo đúng một lần từ Phase 3 common timestamp index rồi áp dụng cho cả sáu configurations.

Tất cả configurations phải dùng:

```text
same train timestamps
same test timestamps
same CV train timestamps per fold
same CV validation timestamps per fold
```

Không tạo split riêng theo từng `X`, không shuffle và không để feature configuration làm thay đổi population.

## 8. Final-test Sealing Policy

Phase 4 được phép kiểm tra trên final test:

- số sample;
- timestamp đầu/cuối;
- schema và alignment;
- không overlap với train;
- indices áp dụng nhất quán cho sáu configurations.

Không được dùng target values hoặc metrics từ final test để:

- chọn `p`;
- chọn lag-only hay lag + rolling;
- chọn rolling configuration;
- tune hyperparameter;
- chọn model;
- sửa pipeline nhằm cải thiện test result.

Final test chỉ được dùng cho final evaluation trong Phase 6 sau khi model và configuration đã được khóa theo approved protocol.

## 9. Transformation Boundary

Phase 4 không thực hiện scaling, imputation, feature selection hoặc fitted transformation.

Nếu phase sau bổ sung transformation có bước `fit`, protocol bắt buộc là:

```text
within CV:
fit on fold train
→ transform fold train and fold validation

final model:
fit on full top-level train
→ transform top-level train and final test
```

Không fit transformation trên full dataset trước temporal split.

## 10. Required Tasks

### 10.1 Validate Phase 3 Contract

Xác nhận sáu configurations dùng cùng common index, đúng row count, đúng alignment và không chứa invalid numeric values.

### 10.2 Create Shared Top-level Indices

Tạo `train_indices` và `test_indices` bằng cutoff đã duyệt. Indices phải positional hoặc label-based theo một contract nhất quán và áp dụng được cho cả sáu configurations.

### 10.3 Create Shared CV Fold Indices

Tạo năm expanding-window folds chỉ từ top-level training indices. Lưu positional indices, timestamp boundaries và sample counts của từng fold.

### 10.4 Apply and Verify Indices

Áp dụng cùng indices cho sáu configurations và xác minh không có index drift, overlap hoặc reorder.

### 10.5 Record Split Audit

Ghi configuration, counts, boundaries, fold structure, checks và test-sealing state vào machine-readable audit.

## 11. Expected Output Contract

Phase 4 trả về hoặc cho phép truy cập rõ ràng:

```text
train_indices
test_indices
cv_fold_indices
split_config
top_level_timestamp_boundaries
cv_timestamp_boundaries
configuration_names
```

Indices không được phụ thuộc vào giá trị feature hoặc target ngoài timestamp cutoff và Phase 3 common population.

## 12. Persistence and Reproducibility Policy

Không lưu mặc định 12 full datasets `X_train/X_test`.

Khả năng tái tạo phải đến từ:

```text
config/validation.json
src/practice_3/data/temporal_split.py
Phase 3 supervised-dataset source/config
```

Machine-readable audit phải được lưu tại:

```text
outputs/results/phase_04_split_audit.json
```

## 13. Validation Criteria

Phase 4 chỉ `PASS` khi:

- Phase 1–3 đều `PASS`;
- train có 108.083 samples và test có 8.592 samples, hoặc sai lệch kích hoạt stop condition;
- `max(train_time) < min(test_time)`;
- train và test disjoint;
- union train/test bằng toàn bộ Phase 3 common index;
- sáu configurations dùng cùng train/test indices;
- năm CV folds chỉ chứa top-level train samples;
- mỗi fold có đúng 2.160 validation samples;
- fold validation luôn sau fold train;
- fold validation không overlap nhau;
- fold train mở rộng dần;
- final test không xuất hiện trong bất kỳ CV fold nào;
- chronological order được giữ;
- split generation deterministic và reproducible;
- final test vẫn ở trạng thái sealed cho model/feature selection.

## 14. Data Leakage Checks

Không được có:

```text
shuffle
random KFold
test sample trong CV
future fold trong train fold
test-based feature selection
test-based hyperparameter tuning
fitted transformation học từ validation/test
configuration-specific split population
```

## 15. Implementation Scope

Các owner dự kiến khi upstream gates đã `PASS`:

```text
config/validation.json
src/practice_3/data/temporal_split.py
tests/test_temporal_split.py
outputs/results/phase_04_split_audit.json
docs/logs/PHASE_04_EXECUTION.md
```

Không thuộc phạm vi Phase 4:

```text
README.md
notebook presentation
full train/test dataset persistence
scaling, imputation hoặc feature selection
model training hoặc tuning
one-step/multi-step prediction
metric calculation hoặc visualization
Phase 5–7 implementation
```

## 16. Risks and Trade-offs

- Final test khoảng một năm cho seasonal coverage nhưng không đại diện mọi historical regime.
- Common mask khiến final test còn 8.592 valid samples thay vì toàn bộ clock-hours trong calendar window.
- `test_size=2160` là row count, không bảo đảm đúng 90 calendar days khi có timestamp bị mask.
- Expanding window làm fold sau lớn hơn fold trước và tăng training cost.
- `gap=0` phù hợp core one-step protocol nhưng phải review lại nếu direct multi-step target được chọn.
- Không persist full split datasets giảm storage nhưng Phase 5 phải tái tạo đúng indices từ source/config.

## 17. Stop Conditions

STOP nếu:

- Phase 1, 2 hoặc 3 chưa `PASS`;
- Phase 3 common population khác approved contract;
- cutoff hoặc expected counts sai lệch chưa giải thích được;
- sáu configurations không dùng cùng indices;
- train/test overlap hoặc chronology sai;
- final test xuất hiện trong CV;
- CV fold count, size hoặc boundaries khác bất thường;
- split generation không deterministic;
- test target/metrics đã bị dùng để thay đổi feature/model pipeline;
- cần đổi cutoff, CV configuration, multi-step gap, dependency hoặc persistence policy.

## 18. Completion Condition

```text
one shared temporal split
+ six configurations aligned
+ expanding-window CV inside train only
+ final test sealed
+ no overlap or leakage
+ deterministic split audit
```

## 19. Downstream Role

Output Phase 4 là input cho `PHASE 05 — MODEL TRAINING`.

Phase 5 phải:

- áp dụng cùng train/test và CV indices cho các configurations được so sánh;
- chỉ dùng top-level train và CV folds để chọn features, hyperparameters và model;
- không đọc final test metrics trong training/tuning;
- ghi lại configuration, split boundaries, random seed và model parameters;
- khóa selected model/configuration trước khi Phase 6 đánh giá final test.
