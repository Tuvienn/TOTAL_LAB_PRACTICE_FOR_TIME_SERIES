# PHASE 03 — X / y PREPARATION

## 1. Phase Identity

**Phase:** 03  
**Name:** X / y Preparation  
**Practice:** Practice 3 — Machine Learning Time Series Forecasting  
**Status:** `PASS`

**Implementation authorized:** `YES`

**Approved by:** `Human`

**Approval date:** `2026-10-19`

**Completion date:** `2026-10-19`

## 2. Objective

Tạo các supervised datasets có `X`, `y` và timestamp alignment rõ ràng từ feature logic của Phase 2. Phase này áp dụng một common validity mask để mọi feature configuration được so sánh trên cùng tập timestamp.

Phase này không scaling, imputation, feature selection, train/test split, shuffle, model training hoặc lựa chọn cấu hình tốt nhất.

```text
Phase 1 processed data
    +
Phase 2 feature source/config
    ↓
recreate validated feature table
    ↓
common maximal validity mask
    ↓
six aligned supervised datasets
```

## 3. Input and Entry Gate

Input có thể tái tạo gồm:

```text
datasets/processed/aep_hourly_prepared.csv
config/feature_engineering.json
src/practice_3/analysis/feature_engineering.py
```

Phase 3 chỉ được thực thi khi:

```text
Phase 1 = PASS
Phase 2 = PASS
```

Input feature table phải giữ nguyên 121.296 timestamp và có:

```text
Datetime
AEP_MW
source_count
quality_flag
lag_1 ... lag_168
rolling_mean_24
rolling_std_24
rolling_mean_168
rolling_std_168
```

Phase 3 không đọc feature table stale từ artifact ngoài contract; bảng feature phải được tái tạo bằng đúng source và configuration đã được Phase 2 xác minh.

## 4. Target, Timestamp and Metadata Contract

### 4.1 Target

```text
y(t) = AEP_MW(t)
```

Tên target chính thức tiếp tục là `AEP_MW`.

### 4.2 Timestamp

`Datetime` phải được giữ làm index hoặc khóa alignment có thể truy vết. Timestamp không phải model feature.

### 4.3 Metadata

```text
source_count
quality_flag
```

Metadata phải được giữ song song và alignment với supervised dataset để audit chất lượng dữ liệu, nhưng không được nằm trong `X`.

## 5. Approved Feature Configurations

### 5.1 Lag-only Configurations

```text
lag_only_p24  = lag_1 ... lag_24
lag_only_p72  = lag_1 ... lag_72
lag_only_p168 = lag_1 ... lag_168
```

### 5.2 Lag + Rolling Configurations

Mọi cấu hình dưới đây thêm cùng bốn rolling features:

```text
rolling_mean_24
rolling_std_24
rolling_mean_168
rolling_std_168
```

Feature definitions:

```text
lag_rolling_p24  = lag_1 ... lag_24  + rolling features
lag_rolling_p72  = lag_1 ... lag_72  + rolling features
lag_rolling_p168 = lag_1 ... lag_168 + rolling features
```

Feature order phải deterministic: lag tăng dần trước, rolling features theo đúng thứ tự đã liệt kê sau.

## 6. Common Maximal Validity Mask

Tất cả sáu configurations dùng cùng một mask:

```text
common_valid =
    AEP_MW is finite
    AND lag_1 ... lag_168 are finite
    AND rolling_mean_24 is finite
    AND rolling_std_24 is finite
    AND rolling_mean_168 is finite
    AND rolling_std_168 is finite
```

Không được dùng mask riêng theo từng configuration cho model-comparison workflow chính. Quyết định này bảo đảm chênh lệch metric downstream phản ánh feature/model thay vì khác evaluation population.

Trade-off được chấp nhận: cấu hình nhỏ như `p=24` bỏ thêm các timestamp mà riêng nó có thể sử dụng được.

## 7. Expected Sample Counts

Dựa trên Phase 1 timeline dự kiến và 27 missing targets, các số pre-implementation là:

| Validity scope | Usable samples | Removed samples |
|---|---:|---:|
| Riêng `p=24` | 120.597 | 699 |
| Riêng `p=72` | 119.267 | 2.029 |
| Riêng `p=168` | 116.675 | 4.621 |
| Common maximal mask | 116.675 | 4.621 |

Expected common output:

```text
initial_rows = 121296
usable_rows = 116675
removed_unique_rows = 4621
first_usable_timestamp = 2004-10-08 01:00:00
last_usable_timestamp = 2018-08-03 00:00:00
```

Các số trên là expected acceptance values, không phải execution result. Phase 3 phải tính lại từ output thực tế và dừng nếu có sai lệch chưa giải thích được.

## 8. Row-loss Audit

Phải tạo các reason masks riêng, tối thiểu gồm:

```text
invalid_target
invalid_lag_history
invalid_rolling_history
non_finite_feature
```

Một row có thể thuộc nhiều reason masks. Không được cộng riêng từng nguyên nhân để suy ra tổng số row bị loại.

```text
removed_unique_rows = count(union of all invalid reason masks)
```

Audit phải ghi:

- số row theo từng reason mask;
- số row giao nhau giữa các nhóm khi cần giải thích;
- tổng unique rows bị loại;
- số row còn lại;
- timestamp đầu/cuối sau mask.

## 9. Required Tasks

### 9.1 Recreate and Validate Feature Table

Tái tạo feature table từ đúng Phase 1 artifact và Phase 2 source/config. Kiểm tra schema, timestamp alignment, feature order và tính deterministic.

### 9.2 Build Common Mask

Tạo common maximal validity mask đúng Section 6 và row-loss audit đúng Section 8.

### 9.3 Build Six Supervised Datasets

Tạo sáu cấu hình trên cùng timestamp index:

```text
datasets["lag_only_p24"]
datasets["lag_only_p72"]
datasets["lag_only_p168"]
datasets["lag_rolling_p24"]
datasets["lag_rolling_p72"]
datasets["lag_rolling_p168"]
```

Mỗi entry phải chứa hoặc truy cập rõ ràng:

```text
X
y
timestamp_index
feature_names
aligned_metadata
```

### 9.4 Validate Alignment and Leakage

Với từng configuration:

```text
len(X) == len(y) == len(timestamp_index)
X.index equals y.index
X.index equals metadata.index
X columns equal ordered feature_names
AEP_MW not in X
Datetime not in X
source_count not in X
quality_flag not in X
X and y contain no NaN, inf or -inf
```

## 10. Expected In-memory Output Contract

Kết quả Phase 3 là mapping sáu supervised datasets dùng cùng timestamp index:

```text
lag_only_p24
lag_only_p72
lag_only_p168
lag_rolling_p24
lag_rolling_p72
lag_rolling_p168
```

Mỗi `X` có số column dự kiến:

| Configuration | Expected feature count |
|---|---:|
| `lag_only_p24` | 24 |
| `lag_only_p72` | 72 |
| `lag_only_p168` | 168 |
| `lag_rolling_p24` | 28 |
| `lag_rolling_p72` | 76 |
| `lag_rolling_p168` | 172 |

Mỗi configuration dự kiến có 116.675 samples trên cùng index.

## 11. Persistence and Reproducibility Policy

Không lưu mặc định sáu bộ `X/y` thành CSV. Chúng phải tái tạo được từ:

```text
datasets/processed/aep_hourly_prepared.csv
config/feature_engineering.json
src/practice_3/analysis/feature_engineering.py
src/practice_3/data/supervised_dataset.py
```

Machine-readable audit phải được lưu tại:

```text
outputs/results/phase_03_supervised_quality.json
```

Nếu Human yêu cầu persist full supervised datasets, format, compression và Git policy phải được phê duyệt riêng.

## 12. Validation Criteria

Phase 3 chỉ `PASS` khi:

- Phase 1 và Phase 2 đều `PASS`;
- common mask đúng maximal feature definition;
- sáu configurations tồn tại với đúng feature names/order;
- sáu configurations có cùng 116.675 timestamp hoặc sai lệch đã kích hoạt stop condition;
- `X`, `y`, timestamps và metadata alignment tuyệt đối;
- target, timestamp và metadata không nằm trong `X`;
- không còn `NaN`, `inf` hoặc `-inf` trong `X/y`;
- row-loss audit không double-count tổng unique rows;
- input feature table không bị mutation ngoài ý muốn;
- output deterministic và reproducible.

## 13. Data Leakage Checks

Không được:

- đưa `AEP_MW(t)` vào `X(t)`;
- đưa timestamp hoặc quality metadata vào model features;
- impute bằng current/future information;
- chọn validity mask dựa trên final test result;
- dùng per-configuration timestamp population trong fair-comparison workflow chính;
- shuffle chronology;
- thực hiện scaling hoặc fitted transformation trước temporal split.

## 14. Implementation Scope

Các owner dự kiến sau khi Human duyệt implementation:

```text
src/practice_3/data/supervised_dataset.py
tests/test_supervised_dataset.py
outputs/results/phase_03_supervised_quality.json
docs/logs/PHASE_03_EXECUTION.md
```

Không thuộc phạm vi Phase 3:

```text
README.md
notebook presentation
full X/y persistence
imputation hoặc scaling
feature selection
train/test split hoặc TimeSeriesSplit
model training, tuning, forecasting hoặc evaluation
Phase 4–7 implementation
```

## 15. Risks and Trade-offs

- Common maximal mask giảm số mẫu của các cấu hình nhỏ nhưng tạo comparison population công bằng.
- Dense lags làm số feature tăng đến 172, ảnh hưởng memory và training time downstream.
- Missing target tạo các invalid windows có thể overlap; audit không đúng có thể double-count row loss.
- Không persist full `X/y` giảm storage nhưng Phase 4 phải dùng đúng source/config để tái tạo output.
- Feature correlation chưa được xử lý ở Phase 3 và phải được cân nhắc khi diễn giải feature importance.

## 16. Stop Conditions

STOP nếu:

- Phase 1 hoặc Phase 2 chưa `PASS`;
- processed input, Phase 2 source hoặc config chưa tồn tại;
- feature schema/order khác approved definition;
- expected row counts hoặc timestamp boundary sai lệch chưa giải thích được;
- sáu configurations không dùng cùng timestamp index;
- target, timestamp hoặc metadata lọt vào `X`;
- còn `NaN`, `inf` hoặc `-inf` trong output `X/y`;
- row-loss audit không nhất quán;
- input bị mutation ngoài ý muốn;
- cần thay đổi mask, feature configuration, dependency hoặc persistence policy.

## 17. Completion Condition

```text
six supervised configurations
+ one common timestamp population
+ X/y/metadata alignment valid
+ no target leakage
+ no invalid numeric values
+ row-loss audit traceable
+ reproducible construction
```

## 18. Downstream Role

Output Phase 3 là input cho `PHASE 04 — TEMPORAL SPLIT & VALIDATION DESIGN`.

Phase 4 phải:

- dùng nguyên common timestamp index từ Phase 3;
- áp dụng cùng temporal boundary cho cả sáu configurations;
- không tự thay đổi validity mask hoặc feature definitions;
- không shuffle;
- giữ final test set tách biệt khỏi tuning.
