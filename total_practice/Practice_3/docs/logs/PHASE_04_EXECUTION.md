# PHASE 04 — EXECUTION LOG

## 1. Trạng thái

```text
Phase: 04 — Temporal Split & Validation Design
Execution date: 2026-10-20
Result: PASS
```

## 2. Môi trường đã dùng

```text
Python: 3.14.3
pandas: 3.0.6
NumPy: 2.5.4
scikit-learn: 1.9.1
pytest: 9.1.1
```

## 3. Thành phần đã chạy

1. Xác minh audit `PASS` của Phase 1–3.
2. Tái tạo sáu supervised datasets từ source chính thức của Phase 3.
3. Tạo shared top-level train/test indices theo cutoff đã duyệt.
4. Tạo năm expanding-window `TimeSeriesSplit` folds trong top-level train.
5. Áp dụng và kiểm tra cùng indices trên sáu configurations.
6. Kiểm tra chronology, overlap, union và final-test sealing.
7. Kiểm tra config contract và deterministic split generation.
8. Chạy pipeline chính thức, automated tests và compile source/tests.

## 4. Kết quả top-level split

```text
cutoff = 2017-08-03 00:00:00
TRAIN  = timestamp < cutoff
TEST   = timestamp >= cutoff
```

| Chỉ số | Kết quả |
|---|---:|
| Total rows | 116.675 |
| Train rows | 108.083 |
| Test rows | 8.592 |
| Train start | 2004-10-08 01:00:00 |
| Train end | 2017-08-02 23:00:00 |
| Test start | 2017-08-03 00:00:00 |
| Test end | 2018-08-03 00:00:00 |

Train và test không overlap, hợp lại đúng toàn bộ common timestamp population và thỏa `max(train_time) < min(test_time)`.

## 5. Kết quả TimeSeriesSplit

```text
strategy = expanding_window
n_splits = 5
test_size = 2160
gap = 0
max_train_size = null
```

| Fold | Train samples | Validation samples | Train end | Validation start | Validation end |
|---:|---:|---:|---|---|---|
| 1 | 97.283 | 2.160 | 2016-05-02 22:00:00 | 2016-05-02 23:00:00 | 2016-07-31 22:00:00 |
| 2 | 99.443 | 2.160 | 2016-07-31 22:00:00 | 2016-07-31 23:00:00 | 2016-10-29 22:00:00 |
| 3 | 101.603 | 2.160 | 2016-10-29 22:00:00 | 2016-10-29 23:00:00 | 2017-01-27 22:00:00 |
| 4 | 103.763 | 2.160 | 2017-01-27 22:00:00 | 2017-01-27 23:00:00 | 2017-05-04 23:00:00 |
| 5 | 105.923 | 2.160 | 2017-05-04 23:00:00 | 2017-05-05 00:00:00 | 2017-08-02 23:00:00 |

Training windows mở rộng tuần tự, validation folds không overlap và final test không xuất hiện trong bất kỳ CV fold nào.

## 6. Shared-index và final-test sealing

Sáu configurations dùng chung:

```text
train indices
test indices
CV train indices của từng fold
CV validation indices của từng fold
```

Final test được đánh dấu sealed và chưa được dùng cho feature selection, tuning, model selection hoặc metric calculation.

## 7. Kết quả validation

```text
Phase 4 tests: 22 passed
Full project tests: 68 passed
Source/tests compile: PASS
Phase 1–3 entry gate: PASS
Validation config contract: PASS
Top-level chronology and partition: PASS
Shared indices across six configurations: PASS
Training-only TimeSeriesSplit: PASS
Final-test sealing: PASS
Deterministic split generation: PASS
Audit JSON round trip: PASS
```

## 8. Artifacts bàn giao

- Configuration: `config/validation.json`
- Source implementation: `src/practice_3/data/temporal_split.py`
- Automated tests: `tests/test_temporal_split.py`
- Machine-readable audit: `outputs/results/phase_04_split_audit.json`

Full train/test datasets không được persist. Phase 5 phải tái tạo supervised datasets và áp dụng đúng shared indices từ Phase 4.

## 9. Giới hạn được giữ lại

- Phase 4 không scaling, imputation hoặc feature selection.
- Phase 4 không train, tune hoặc chọn model.
- Phase 4 không đọc final-test target để tính metric.
- `test_size=2160` biểu diễn số sample hợp lệ, không bảo đảm chính xác 90 ngày lịch.
- `gap=0` chỉ được phê duyệt cho core one-step protocol; direct multi-step với overlapping labels phải mở lại gap decision.

## 10. Kết luận

```text
PHASE 04: PASS
HANDOFF TO PHASE 05: READY
FINAL TEST: SEALED
```

Phase 5 được phép sử dụng top-level train và các CV folds để huấn luyện/tuning. Final test vẫn bị khóa cho đến final evaluation ở Phase 6.
