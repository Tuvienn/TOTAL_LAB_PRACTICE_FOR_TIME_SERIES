# PHASE 04 — FEATURE ENGINEERING

## 1. Phase identity

```text
Project: Practice_3_v2
Phase: 4
Name: Feature Engineering
Design status: APPROVED
Human approval: GRANTED
Implementation authorization: GRANTED
Execution status: PASS — HUMAN APPROVED
```

## 2. Mục tiêu

Xây dựng feature logic dùng chung cho one-step và recursive forecasting, bảo đảm mọi feature của target tại thời điểm `T` chỉ dùng thông tin khả dụng không muộn hơn forecast origin `T-1 giờ`.

```text
validated hourly history
→ lag features
→ shifted rolling features
→ target-time calendar features
→ leakage validation
→ deterministic feature audit
```

Phase này không tạo X/y population, không loại sample, không impute, không fit transformer, không train model và không prediction.

## 3. Time semantics

```text
Target timestamp: T
Forecast origin: T - 1 hour
Allowed target history: through T - 1 hour
Forbidden value: y(T) and every future actual target
```

Lag và rolling feature phải được tạo từ history đứng trước target timestamp. Calendar feature được phép dùng target timestamp vì lịch đã biết trước.

## 4. Approved feature schema

### 4.1 Lag features

```text
lag_1h
lag_2h
lag_3h
lag_23h
lag_24h
lag_25h
lag_48h
lag_168h
```

Công thức:

```text
lag_kh(T) = y(T-k)
```

### 4.2 Rolling features

```text
rolling_mean_24h
rolling_std_24h
rolling_mean_168h
rolling_std_168h
```

Công thức bắt buộc:

```text
history = target.shift(1)
rolling_mean_wh = history.rolling(w, min_periods=w).mean()
rolling_std_wh = history.rolling(w, min_periods=w).std(ddof=1)
```

Không dùng centered window và không đưa target tại `T` vào window.

### 4.3 Calendar features

```text
hour
day_of_week
month
is_weekend
hour_sin
hour_cos
day_of_week_sin
day_of_week_cos
month_sin
month_cos
```

Calendar values lấy từ target timestamp. Cyclical encoding:

```text
hour angle = 2π × hour / 24
day angle = 2π × day_of_week / 7
month angle = 2π × (month - 1) / 12
```

Tổng approved schema: **22 features**, đúng thứ tự trong `config/features.json`.

## 5. Explicit exclusions

Không sử dụng:

- target `AEP_MW(T)` làm feature cho chính `T`;
- lead hoặc negative shift;
- centered rolling;
- `quality_flag` hoặc `source_count` tại target timestamp;
- anomaly flag retrospective từ Phase 3;
- holdout-derived statistic;
- year hoặc elapsed-time trend trong core feature set;
- scaling, differencing hoặc target transformation;
- imputation trong Phase 4.

## 6. Missing-feature policy

Phase 4 giữ nguyên timeline và không xóa row.

- Initial history chưa đủ sẽ tạo `NaN` cho lag/rolling tương ứng.
- Missing target trong lịch sử truyền `NaN` vào lag tương ứng.
- Rolling window yêu cầu đủ `w` observed values vì `min_periods=w`.
- Phase 5 chịu trách nhiệm xác định sample có X/y hợp lệ.

Phase 4 audit được tính trên development period duy nhất; không ghi holdout-derived feature statistics.

## 7. One-step and recursive compatibility

### 7.1 One-step

Mỗi target timestamp dùng actual history đến forecast origin. Khi actual mới xuất hiện, history của forecast origin tiếp theo được phép cập nhật.

### 7.2 Recursive 24-hour

- Bước 1 chỉ dùng actual history đến origin.
- Sau mỗi prediction, predicted value được append vào history.
- Bước tiếp theo dùng actual history cũ và predictions đã sinh.
- Không nhận hoặc đọc actual target sau origin.
- Calendar features vẫn lấy từ target timestamp của từng bước.

Feature owner phải cung cấp hàm tạo một feature row từ history để Phase 7 dùng lại, không sao chép công thức feature sang forecasting code.

## 8. Implementation ownership

```text
config/features.json
src/practice_3_v2/analysis/feature_engineering.py
tests/test_feature_engineering.py
outputs/results/phase_04_feature_validation.json
docs/logs/PHASE_04_EXECUTION.md
```

Không tạo feature CSV trong Phase 4. Phase 5 áp dụng feature owner để tạo aligned X/y theo temporal split.

Proposed functions:

```text
load_phase_04_inputs
validate_feature_contract
build_calendar_features
build_time_safe_features
build_feature_row_from_history
validate_feature_frame
build_phase_04_audit
save_phase_04_artifact
run_phase_04
```

## 9. Official audit contract

```text
outputs/results/phase_04_feature_validation.json
```

Audit phải chứa:

- upstream prepared, split và EDA identities;
- development boundary và row count;
- exact ordered feature schema;
- lag, rolling và calendar formulas/policies;
- development-only null count cho từng feature;
- first fully available feature timestamp;
- finite/range checks cho calendar encodings;
- leakage and recursive-safety checks;
- missing/imputation policy;
- deterministic validation status;
- final status.

Audit không chứa holdout-derived feature statistics hoặc model metric.

## 10. Test contract

Focused tests phải kiểm tra:

1. Upstream contracts/audits tồn tại, PASS và checksum khớp.
2. Contract có đúng 22 features theo exact order.
3. Lag values đúng trên synthetic hourly series.
4. Rolling values dùng `shift(1)`, đúng window và `ddof=1`.
5. Thay target tại `T` hoặc tương lai không đổi feature row tại `T`.
6. Calendar integers và cyclical values đúng target timestamp.
7. Cyclical encodings nằm trong `[-1, 1]`.
8. Không impute missing history.
9. Development feature audit không đổi khi mutate holdout target.
10. Recursive row builder chỉ nhận history đến origin.
11. Append predicted value làm thay đổi đúng feature của bước tiếp theo.
12. Input dataframe/history không bị chỉnh sửa.
13. Không dùng `quality_flag`, `source_count`, anomaly flag hoặc current target làm feature.
14. Invalid order, lag, rolling policy hoặc checksum làm pipeline dừng.
15. Official audit deterministic qua repeated run.
16. Không có runtime import từ legacy `practice_3`.

Trước bàn giao phải chạy focused tests, full v2 regression suite và `git diff --check`.

## 11. Atomic and deterministic policy

Official JSON được tạo theo quy trình:

```text
build development features in memory
→ validate feature frame
→ write temporary JSON
→ reload and validate JSON
→ promote official artifact
```

Không promote partial artifact nếu validation thất bại.

## 12. Notebook boundary

Sau Phase 4 PASS, notebook chỉ đọc official audit để trình bày:

- feature dictionary;
- exact 22-feature schema và formula;
- development-only null counts;
- first fully available timestamp;
- leakage controls và recursive compatibility.

Notebook không được tính lại feature matrix.

## 13. Completion gate

Phase 4 chỉ `PASS` khi:

- feature contract hợp lệ;
- source owner và focused tests tồn tại;
- lag/rolling/calendar correctness PASS;
- future-mutation và recursive-safety tests PASS;
- official feature audit được tạo và validate;
- full regression suite PASS;
- execution log/status được đồng bộ;
- Human review kết quả Phase 4.

Sau Phase 4 mới được thiết kế Phase 5 — X/y Construction & Split Application.

## 14. Implementation result

```text
Approved features: 22
Development rows validated: 112,535
Rows with all 22 features: 108,108
First fully available timestamp: 2004-10-08 01:00:00
Focused tests: 17/17 PASS
Full v2 regression suite: 65/65 PASS
Official audit: PASS
Human result review: APPROVED
```

Phase 4 đã triển khai đúng approved contract và được Human duyệt. Phase 5 được phép bắt đầu ở bước thảo luận và thiết kế; implementation vẫn cần phase-detail được Human duyệt.

## 15. Presentation extension

Theo Human approval, notebook giải thích Phase 4 theo chuỗi lập luận tinh gọn:

```text
feature được tạo
→ feature availability
→ correlation context
→ leakage và forecasting compatibility
```

Phần trình bày gồm:

- một feature dictionary gồm ba nhóm và đủ 22 features;
- công thức lag, shifted rolling và cyclical encoding;
- một bảng availability rút gọn theo nhóm lag, rolling và calendar;
- số rows có đủ toàn bộ feature và timestamp khả dụng đầu tiên;
- một heatmap đầy đủ `13 × 13` gồm target, tám lag và bốn rolling features;
- xác nhận ngắn về leakage controls và one-step/recursive compatibility;
- limitation: core feature set không dùng `year` hoặc explicit trend feature.

Heatmap được source owner tạo từ Development bằng pairwise Pearson correlation.
Calendar features không đưa vào heatmap vì integer calendar và từng thành phần
sin/cos riêng lẻ dễ gây diễn giải sai. Correlation chỉ là descriptive linear
association, không phải causal evidence hoặc XGBoost feature importance.

```text
src/practice_3_v2/analysis/feature_presentation.py
outputs/results/phase_04_feature_presentation.json
outputs/figures/phase_04_temporal_feature_correlation.png
tests/test_feature_presentation.py
```

Notebook chỉ đọc Phase 3–4 artifacts; không tính lại feature matrix, không mở
Final Test và không thay đổi approved feature schema hoặc model evidence.
