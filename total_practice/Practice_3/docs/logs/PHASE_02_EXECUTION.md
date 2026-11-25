# PHASE 02 — EXECUTION LOG

## 1. Scope

Triển khai và xác minh temporal split từ prepared hourly dataset đến deterministic split audit. Phase này không thực hiện EDA, feature engineering, X/y construction, model training, prediction hoặc metric evaluation.

## 2. Official execution

```bash
.venv/bin/python -m practice_3.data.temporal_split
```

Official output:

```text
outputs/results/phase_02_temporal_split.json
```

## 3. Input identity

```text
Prepared input: datasets/processed/aep_hourly_prepared.csv
Prepared SHA256: 5b61ab66e585ba479233e7a5597fa42fc5f73bc54c46317b1408bd7a65cab587
Prepared rows: 121,296
Prepared missing targets: 27
```

Prepared checksum khớp Phase 1 audit và approved temporal split contract.

## 4. Development and holdout result

```text
Development rows: 112,535
Development observed targets: 112,509
Development missing targets: 26
Development end exclusive: 2017-08-03 00:00:00

Historical holdout rows: 8,761
Historical holdout observed targets: 8,760
Historical holdout missing targets: 1
Holdout start inclusive: 2017-08-03 00:00:00
Holdout end inclusive: 2018-08-03 00:00:00
Holdout claimed unseen: false
```

Development và holdout không overlap, đồng thời phủ đủ 121,296 timestamps.

## 5. Expanding-window result

```text
Method: expanding_window
Folds: 5
Shuffle: false
Gap: 0 hours
Validation rows by fold: 8,760; 8,760; 8,760; 8,784; 8,760
```

Fold 4 chứa ngày nhuận năm 2016 nên có 8,784 giờ. Fold-train mở rộng đơn điệu; validation folds liên tục, không overlap và kết thúc đúng tại development end.

## 6. Missing-target policy

```text
Timeline rows retained: true
Imputation: none
Training-label eligible: false
Metric eligible: false
```

Phase 2 chỉ audit target availability; không đọc holdout target values để tính distribution, trend, seasonality hoặc lựa chọn feature/model.

## 7. Validation evidence

```text
Focused Phase 2 tests: 13/13 PASS
Full Practice 3 regression suite: 33/33 PASS
Independent audit validation: PASS
Deterministic official rerun: PASS
Official audit SHA256: f18452573cedd321ea8097539560899bc5dbce43ba0b47cda3b51dc504bcf735
Trailing-whitespace check: PASS
git diff --check: PASS
Legacy runtime import: NONE
```

## 8. Resolved implementation issues

Hai vấn đề kỹ thuật được phát hiện trước khi có official Phase 2 artifact:

1. `pd.Timestamp.strptime` chưa được pandas 3.1.0 hỗ trợ. Sau Human approval, boundary parser được đổi sang strict `pd.to_datetime(..., format=..., errors="raise")`; split logic không thay đổi.
2. Môi trường đã bị chuyển từ editable install sang wheel khi cài presentation dependencies. Package được khôi phục bằng editable local install để official module command nhận source mới; scientific logic và artifact không thay đổi.

Self-review bổ sung fail-fast validation để đối chiếu toàn bộ temporal boundary, holdout claim, CV method, fold count, shuffle policy và primary target semantics giữa forecasting contract với split contract.

Không có partial official artifact được chấp nhận trước khi hai vấn đề trên được xử lý.

## 9. Completion state

```text
Phase 2 technical status: PASS
Human result review: APPROVED TO PROCEED
Presentation notebook: READY THROUGH PHASE 2
Notebook clean-kernel execution: PASS — 8/8 code cells, no errors
Next phase implementation: NOT AUTHORIZED
```

Human đã yêu cầu chuyển sang Phase 3 sau khi trình bày Phase 2 vào notebook. Phase 3 hiện chỉ được bắt đầu ở bước thảo luận và thiết kế; implementation vẫn cần phase-detail được duyệt.
