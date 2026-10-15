# PHASE 02 — FEATURE ENGINEERING

## 1. Phase Identity

**Phase:** 02  
**Name:** Feature Engineering  
**Practice:** Practice 3 — Machine Learning Time Series Forecasting  
**Status:** `APPROVED`  
**Implementation authorized:** `YES_AFTER_PHASE_01_PASS`  
**Approved by:** `Human`  
**Approval date:** `2026-10-16`

## 2. Objective

Chuyển working time series thành bảng feature an toàn theo thời gian, gồm lag features, rolling mean và rolling standard deviation. Phase này không chia `X/y`, không split train/test và không train model.

```text
prepared hourly data
    ↓
lag features
    ↓
past-only rolling features
    ↓
validated in-memory feature table
```

## 3. Input and Entry Gate

Input bắt buộc từ Phase 1:

```text
datasets/processed/aep_hourly_prepared.csv
```

Schema đầu vào:

```text
Datetime
AEP_MW
source_count
quality_flag
```

Phase 2 chỉ được thực thi khi Phase 1 đã `PASS` và input thỏa:

- 121.296 timestamp duy nhất;
- timeline tăng dần và liên tục theo giờ;
- duplicate timestamp bằng 0;
- 27 target `AEP_MW` đang thiếu được giữ là `NaN`;
- `source_count` và `quality_flag` hợp lệ;
- raw dataset vẫn bất biến.

## 4. Approved Feature Configuration

### 4.1 Lag Experiment

Ba cấu hình `p` dùng để nghiên cứu ảnh hưởng của số lag:

```text
small_p = 24
medium_p = 72
large_p = 168
```

Ý nghĩa:

- `p = 24`: lịch sử một ngày;
- `p = 72`: lịch sử ba ngày;
- `p = 168`: lịch sử một tuần.

Phase 2 tạo `lag_1 ... lag_168` một lần. Các thí nghiệm downstream chọn subset:

```text
p = 24  → lag_1 ... lag_24
p = 72  → lag_1 ... lag_72
p = 168 → lag_1 ... lag_168
```

Thiết kế dense lag được chọn để bám đúng yêu cầu `lag_1 ... lag_p` và giúp so sánh tác động khi tăng `p`. Sparse lag set không được dùng làm phương án chính vì sẽ thay đổi ý nghĩa của thí nghiệm này.

### 4.2 Rolling Configuration

```text
rolling_windows = [24, 168]
min_periods = window
ddof = 0
center = false
```

Mọi rolling feature phải được tạo từ:

```text
historical_target = AEP_MW.shift(1)
```

Công thức tại thời điểm `t`:

```text
rolling_mean_24(t)  = mean(y(t-1) ... y(t-24))
rolling_std_24(t)   = std(y(t-1) ... y(t-24), ddof=0)
rolling_mean_168(t) = mean(y(t-1) ... y(t-168))
rolling_std_168(t)  = std(y(t-1) ... y(t-168), ddof=0)
```

`min_periods = window` được dùng để không tính rolling statistics từ cửa sổ lịch sử chưa đầy đủ.

## 5. Required Tasks

### 5.1 Validate Input Contract

Kiểm tra schema, dtype, số dòng, timestamp order, hourly continuity, duplicate, missing target và metadata trước khi tạo feature.

### 5.2 Create Lag Features

```text
lag_k(t) = AEP_MW(t-k hours), với 1 ≤ k ≤ 168
```

Vì input đã được hourly reindex, row shift tương ứng với số giờ. Phase 2 vẫn phải xác minh điều kiện này trước khi dùng `shift()`.

### 5.3 Validate Lag Alignment

Kiểm tra thủ công và tự động tối thiểu:

```text
lag_1(t) = y(t-1)
lag_24(t) = y(t-24)
lag_72(t) = y(t-72)
lag_168(t) = y(t-168)
```

Mẫu kiểm tra phải gồm timestamp bình thường và timestamp gần một missing target để xác minh `NaN` được truyền đúng.

### 5.4 Create Rolling Features

Tạo:

```text
rolling_mean_24
rolling_std_24
rolling_mean_168
rolling_std_168
```

Không được dùng `AEP_MW(t)`, centered rolling hoặc future target trong feature tại `t`.

### 5.5 Preserve Missing Feature Values

NaN có thể xuất hiện do:

- đầu chuỗi chưa đủ lag/window;
- 27 target bị thiếu từ Phase 1;
- lag tham chiếu đến một missing target;
- rolling window chứa missing target.

Phase 2 không fill và không loại bất kỳ sample nào. Phase này giữ nguyên toàn bộ timestamp và ghi lại số lượng `NaN` theo từng feature.

### 5.6 Preserve Traceability Metadata

Giữ `source_count` và `quality_flag` trong feature table để truy vết. Hai field này là metadata và không được tự động đưa vào model feature set.

### 5.7 Preserve Comparison Capability

Lag experiment:

```text
Lag-only p=24
vs Lag-only p=72
vs Lag-only p=168
```

Rolling contribution experiment:

```text
Lag-only với cùng p
vs
Lag + Rolling với cùng p
```

Việc chọn cấu hình hoặc kết luận hiệu quả chỉ được thực hiện bằng training data và time-aware validation ở phase downstream, không dùng final test set.

## 6. Expected In-Memory Output

Feature table giữ nguyên 121.296 timestamp và gồm:

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

`AEP_MW` tiếp tục là tên target chính thức. Không đổi tên thành `target` trong Phase 2.

## 7. Persistence and Reproducibility Policy

Không lưu mặc định toàn bộ feature table thành CSV vì 168 lag columns tạo artifact lớn và có thể làm repository phình to.

Khả năng tái tạo phải đến từ:

```text
datasets/processed/aep_hourly_prepared.csv
config/feature_engineering.json
src/practice_3/analysis/feature_engineering.py
```

Machine-readable audit phải được lưu tại:

```text
outputs/results/phase_02_feature_quality.json
```

Nếu Human yêu cầu lưu feature table trung gian, format nén và chính sách Git phải được thảo luận, phê duyệt riêng trước khi tạo artifact.

## 8. Validation Criteria

Phase 2 chỉ `PASS` khi:

- input contract của Phase 1 hợp lệ;
- output vẫn có 121.296 timestamp duy nhất và đúng thứ tự;
- input dataframe không bị mutation ngoài ý muốn;
- `lag_1`, `lag_24`, `lag_72`, `lag_168` alignment đúng;
- rolling feature dùng đúng `AEP_MW.shift(1)`;
- rolling không chứa current hoặc future target;
- `min_periods` và `ddof` đúng configuration;
- NaN count của từng feature được ghi lại và giải thích;
- metadata vẫn được giữ nhưng không nằm trong model feature list;
- Feature Set A/B có thể được tạo trên common validity mask ở Phase 3;
- feature generation deterministic và reproducible.

## 9. Data Leakage Checks

Không được có:

```text
lag_0
AEP_MW(t) trong feature dự báo AEP_MW(t)
negative lag
centered rolling
rolling window chứa current/future target
feature selection dựa trên final test result
```

## 10. Phase Boundary with Phase 3

Phase 2 chỉ tạo và kiểm tra feature. Phase 3 chịu trách nhiệm:

- xác định `X` và `y`;
- tạo validity mask;
- loại các sample có target hoặc required feature không hợp lệ;
- ghi lại số sample còn sử dụng;
- dùng common timestamp set khi so sánh các feature set;
- đảm bảo target không xuất hiện trong `X`.

## 11. Implementation Scope

Các owner dự kiến sau khi Human duyệt implementation:

```text
config/feature_engineering.json
src/practice_3/analysis/feature_engineering.py
tests/test_feature_engineering.py
outputs/results/phase_02_feature_quality.json
docs/logs/PHASE_02_EXECUTION.md
```

Không thuộc phạm vi Phase 2:

```text
README.md
notebook presentation
full feature-table persistence
X/y row filtering
train/test split
model training, tuning hoặc evaluation
Phase 3–7 implementation
```

## 12. Risks and Trade-offs

- `p = 168` tạo nhiều feature hơn, dùng nhiều memory và làm model downstream train lâu hơn.
- Dense lags có thể tương quan mạnh; feature importance cần được diễn giải thận trọng.
- `min_periods = window` làm tăng số `NaN` nhưng đảm bảo rolling feature luôn dùng đủ lịch sử.
- Missing target có thể làm nhiều feature downstream trở thành `NaN`; không được che giấu bằng fill tự động.
- Không lưu full feature table giúp giảm storage nhưng Phase 3 phải tái tạo feature bằng đúng code và config đã duyệt.

## 13. Stop Conditions

STOP nếu:

- Phase 1 chưa `PASS` hoặc processed input chưa tồn tại;
- input contract khác dự kiến;
- hourly continuity không còn đúng;
- lag không đại diện đúng số giờ;
- rolling chứa current/future target;
- số lượng hoặc pattern `NaN` khác bất thường;
- input bị mutation ngoài ý muốn;
- feature generation không deterministic;
- cần đổi lag, rolling configuration, dependency hoặc persistence policy.

## 14. Completion Condition

```text
input contract valid
+ lag alignment correct
+ rolling past-only
+ no future leakage
+ NaN provenance recorded
+ comparison-ready feature definitions
+ reproducible output
```

## 15. Downstream Role

Output logic và configuration là input cho `PHASE 03 — X / y PREPARATION`. Phase 3 phải tái tạo feature table bằng đúng source/config của Phase 2 và chỉ sau đó mới áp dụng common validity mask.
