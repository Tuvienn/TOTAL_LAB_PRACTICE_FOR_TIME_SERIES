# PHASE 03 — EXECUTION LOG

## 1. Trạng thái

```text
Phase: 03 — X/y Preparation
Execution date: 2026-10-19
Result: PASS
```

## 2. Môi trường đã dùng

```text
Python: 3.14.3
pandas: 3.0.6
NumPy: 2.5.4
pytest: 9.1.1
```

## 3. Thành phần đã chạy

1. Xác minh audit `PASS` của Phase 1 và Phase 2.
2. Tái tạo feature table từ processed dataset và config Phase 2.
3. Tạo common maximal validity mask.
4. Audit row loss bằng union của các reason masks.
5. Tạo sáu supervised datasets trên cùng timestamp population.
6. Kiểm tra alignment, feature order, chronology và leakage.
7. Kiểm tra input mutation và deterministic construction.
8. Chạy pipeline chính thức, automated tests và compile source/tests.

## 4. Kết quả common validity mask

| Chỉ số | Kết quả |
|---|---:|
| Initial rows | 121.296 |
| Invalid target | 27 |
| Invalid lag history | 4.595 |
| Invalid rolling history | 4.595 |
| Removed unique rows | 4.621 |
| Usable rows | 116.675 |
| First usable timestamp | 2004-10-08 01:00:00 |
| Last usable timestamp | 2018-08-03 00:00:00 |

Các reason masks có overlap nên tổng unique row bị loại được tính bằng union, không cộng trực tiếp các reason counts.

Lag-only validity counts trước khi áp dụng common maximal mask:

```text
p=24:  120597
p=72:  119267
p=168: 116675
```

## 5. Kết quả supervised datasets

| Configuration | Samples | Features |
|---|---:|---:|
| `lag_only_p24` | 116.675 | 24 |
| `lag_only_p72` | 116.675 | 72 |
| `lag_only_p168` | 116.675 | 168 |
| `lag_rolling_p24` | 116.675 | 28 |
| `lag_rolling_p72` | 116.675 | 76 |
| `lag_rolling_p168` | 116.675 | 172 |

Tất cả cấu hình dùng cùng timestamp index, giữ `source_count` và `quality_flag` làm aligned metadata, đồng thời loại `Datetime`, `AEP_MW` và metadata khỏi `X`.

## 6. Kết quả validation

```text
Phase 3 tests: 13 passed
Full project tests: 46 passed
Source/tests compile: PASS
Phase 1/2 entry gate: PASS
Common-mask acceptance values: PASS
X/y/timestamp/metadata alignment: PASS
NaN/inf validation: PASS
Target and metadata leakage validation: PASS
Input mutation validation: PASS
Deterministic construction: PASS
Audit JSON round trip: PASS
```

## 7. Artifacts bàn giao

- Source implementation: `src/practice_3/data/supervised_dataset.py`
- Automated tests: `tests/test_supervised_dataset.py`
- Machine-readable audit: `outputs/results/phase_03_supervised_quality.json`

Sáu full supervised datasets không được persist theo policy. Chúng được tái tạo từ Phase 1 processed data, Phase 2 config/source và Phase 3 source.

## 8. Giới hạn được giữ lại

- Phase 3 không impute, scale hoặc feature-select.
- Phase 3 chưa chia train/test và không shuffle chronology.
- Phase 3 chưa sử dụng `TimeSeriesSplit`.
- Phase 3 chưa train, tune hoặc đánh giá model.
- Common maximal mask cố ý giảm sample của cấu hình nhỏ để bảo đảm fair comparison population.

## 9. Kết luận

```text
PHASE 03: PASS
HANDOFF TO PHASE 04: READY
```

Phase 4 chịu trách nhiệm chia train/test theo thời gian và thiết kế `TimeSeriesSplit`; Phase 3 không thực hiện các nhiệm vụ đó.
