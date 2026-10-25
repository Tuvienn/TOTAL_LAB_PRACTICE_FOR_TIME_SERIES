# PHASE 05 — X/Y CONSTRUCTION & SPLIT APPLICATION

## 1. Phase identity

```text
Project: Practice_3_v2
Phase: 5
Name: X/y Construction & Split Application
Design status: APPROVED
Human approval: GRANTED
Implementation authorization: GRANTED
Execution status: PASS — HUMAN APPROVED
```

## 2. Mục tiêu

Căn chỉnh 22 time-safe features của Phase 4 với one-step target, xác định sample eligibility và áp dụng năm expanding-window folds đã khóa ở Phase 2.

```text
prepared development timeline
→ time-safe features tại target timestamp T
→ y(T) = AEP_MW(T)
→ forecast origin = T - 1 giờ
→ eligibility mask
→ full-development supervised population
→ five expanding-window CV folds
```

Phase này không impute, không scale, không target transform, không train model, không tuning, không tính metric và không mở holdout để chọn sample hoặc model.

## 3. Sample semantics

Mỗi candidate sample sử dụng:

```text
sample key: target timestamp T
forecast origin: T - 1 hour
X(T): exact 22-feature schema từ Phase 4
y(T): AEP_MW tại T
```

`target_timestamp` và `forecast_origin` là metadata. `AEP_MW` là label. Ba trường này không nằm trong X.

## 4. Exact X schema

X phải dùng đúng thứ tự trong `config/features.json` và `config/supervised_dataset.json`:

```text
8 lag features
4 shifted rolling features
10 calendar features
total = 22
```

Không được bổ sung target, timestamp, `quality_flag`, `source_count`, anomaly flag hoặc trường eligibility vào X.

## 5. Eligibility policy

Sample hợp lệ khi đồng thời:

```text
y observed and finite
AND
all 22 X values observed and finite
```

Không impute và không sửa feature/target. Candidate timeline được giữ nguyên để audit; eligible X/y là view lọc cho modeling.

Mutually exclusive exclusion priority:

1. `invalid_feature_vector`: ít nhất một feature missing hoặc non-finite;
2. `missing_target_with_valid_features`: features hợp lệ nhưng y missing/non-finite;
3. `eligible`: X và y đều hợp lệ.

Priority này bảo đảm tổng ba nhóm bằng số development rows và không double count.

## 6. One-step alignment

Feature row tại `T` chỉ dùng actual target history đến `T-1 giờ`. `y(T)` chỉ là label và không được đưa vào X.

Khi đánh giá one-step tuần tự, actual target của giờ validation trước được phép dùng cho giờ tiếp theo vì approved update cadence là hourly. Đây là rolling one-step protocol, không phải recursive 24-hour protocol.

## 7. CV split application

Năm fold dùng nguyên boundary của `config/temporal_split.json`:

- method: expanding window;
- split key: target timestamp;
- shuffle: false;
- gap: 0 giờ;
- train và validation không overlap;
- validation luôn nằm sau train;
- eligibility được áp dụng sau khi feature/target alignment đã hoàn tất.

Mọi baseline và candidate model ở Phase 6 phải dùng cùng eligible timestamps trong từng fold.

## 8. Full-development population

Phase 5 cung cấp full-development eligible X/y population để Phase 6 fit final locked candidate sau model selection. Population này vẫn không chứa holdout.

## 9. Holdout boundary

Phase 5 không materialize holdout feature matrix và không báo target-derived holdout statistics.

```text
holdout reservation: preserved
holdout feature construction: Phase 7
holdout evaluation: Phase 7
```

Việc đọc prepared file để kiểm tra checksum/schema không đồng nghĩa với dùng holdout target trong X/y construction. Official Phase 5 feature calculation chỉ chạy trên development extraction.

## 10. Recursive 24-hour boundary

Phase 5 không tạo static recursive matrix. Phase 7 phải dùng recursive row builder của Phase 4, append prediction sau mỗi bước và không đọc future actual target sau origin.

## 11. Artifact policy

Phase 5 không lưu CSV/Parquet X/y. Phase 6 phải gọi source owner để tái tạo deterministic supervised data, tránh duplicate hoặc stale artifact.

Official artifact duy nhất:

```text
outputs/results/phase_05_supervised_dataset.json
```

Audit chứa schema, alignment, exclusion counts, eligible range, fold counts, boundaries, leakage checks và upstream identities; không chứa model metric hoặc target distribution.

## 12. Implementation ownership

```text
config/supervised_dataset.json
src/practice_3_v2/data/supervised_dataset.py
tests/test_supervised_dataset.py
outputs/results/phase_05_supervised_dataset.json
docs/logs/PHASE_05_EXECUTION.md
```

Proposed source responsibilities:

```text
load_phase_05_inputs
validate_supervised_contract
build_supervised_candidates
extract_eligible_xy
apply_expanding_window_folds
validate_supervised_population
build_phase_05_audit
save_phase_05_artifact
run_phase_05
```

## 13. Validation contract

Focused tests phải kiểm tra:

1. Prepared, split và Phase 4 artifact identities khớp approved checksums.
2. X có đúng 22 columns theo exact order.
3. `target_timestamp`, forecast origin và y căn chỉnh đúng one-step semantics.
4. Current target và future target không xuất hiện trong X.
5. Metadata và eligibility fields không xuất hiện trong X.
6. Eligible X/y không có NaN hoặc infinity.
7. Exclusion groups mutually exclusive và cộng lại đúng development rows.
8. Không impute hoặc sửa source data.
9. Full-development eligible population chronological và unique.
10. Năm folds đúng boundary, counts, expansion và không overlap.
11. Validation row đầu tiên dùng history trước validation boundary.
12. Validation row sau được phép dùng actual target của giờ trước trong one-step protocol.
13. Mutate current/future target không thay đổi X của sample hiện tại.
14. Mutate holdout target không thay đổi development supervised result.
15. Official audit không có holdout target-derived statistics.
16. Repeated run tạo cùng audit bytes.
17. Invalid contract/checksum/boundary làm pipeline dừng.
18. Không import runtime code từ legacy `practice_3`.

Trước bàn giao phải chạy focused tests, full v2 regression suite, notebook clean-kernel execution và `git diff --check`.

## 14. Stop conditions

Dừng Phase 5 và báo Human nếu:

- eligible counts khác evidence đã review mà chưa giải thích được;
- X/y lệch timestamp hoặc forecast origin;
- fold boundary/count không khớp Phase 2;
- feature calculation cần dùng holdout để hoàn tất;
- phát hiện current/future-target leakage;
- cần đổi Phase 4 feature schema;
- cần thêm dependency hoặc persist X/y table ngoài approved scope.

## 15. Completion gate

Phase 5 chỉ `PASS` khi:

- contract và source owner hợp lệ;
- exact X/y alignment PASS;
- eligibility/exclusion audit PASS;
- five-fold application PASS;
- no-leakage và holdout-isolation tests PASS;
- official JSON được atomic promote và validate;
- focused tests và full regression suite PASS;
- notebook chỉ đọc official artifact và chạy sạch;
- execution log/status được đồng bộ;
- Human review kết quả Phase 5.

Sau Phase 5 mới được thiết kế Phase 6 — Baseline, Training, Tuning & Model Lock.

## 16. Implementation result

```text
Development candidate rows: 112,535
Eligible X/y samples: 108,083
Invalid feature-vector exclusions: 4,427
Missing-target exclusions with valid X: 25
Expanding-window folds: 5
Focused tests: 17/17 PASS
Full v2 regression suite: 82/82 PASS
Official audit: PASS
Human result review: APPROVED
```

Phase 5 đã triển khai đúng approved contract và được Human duyệt. Phase 6 được phép bắt đầu ở bước thảo luận và lập plan; implementation vẫn cần phase-detail được Human duyệt.
