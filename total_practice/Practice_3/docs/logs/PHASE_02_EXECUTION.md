# PHASE 02 — EXECUTION LOG

## 1. Trạng thái

```text
Phase: 02 — Feature Engineering
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

1. Kiểm tra processed input và metadata contract từ Phase 1.
2. Tạo `lag_1 ... lag_168` từ target quá khứ.
3. Tạo rolling mean/std cho cửa sổ 24 và 168 giờ sau `shift(1)`.
4. Kiểm tra alignment tại timestamp bình thường và gần missing target.
5. Kiểm tra config contract, leakage, input mutation và deterministic generation.
6. Chạy pipeline chính thức và lưu audit JSON.
7. Chạy toàn bộ automated tests và compile source/tests.

## 4. Kết quả feature engineering

| Chỉ số | Kết quả |
|---|---:|
| Input rows | 121.296 |
| Output rows | 121.296 |
| Output columns | 176 |
| Lag features | 168 |
| Rolling features | 4 |
| Missing targets được giữ lại | 27 |
| Input dataframe bị mutation | Không |
| Full feature table được persist | Không |

Feature experiment đã duyệt:

```text
Lag-only: p = 24, 72, 168
Lag + Rolling: p = 24, 72, 168
Rolling windows: 24, 168
```

## 5. Kết quả validation

```text
Phase 2 tests: 19 passed
Full project tests: 33 passed
Source/tests compile: PASS
Approved config contract: PASS
Row-level metadata contract: PASS
Independent lag alignment checks: PASS
Independent rolling checks: PASS
Audit JSON round trip: PASS
Future/current-target leakage checks: PASS
```

Các thay đổi không được duyệt đối với lag, rolling hoặc missing-value policy đều làm pipeline dừng thay vì vẫn báo `PASS`.

## 6. Artifacts bàn giao

- Configuration: `config/feature_engineering.json`
- Source implementation: `src/practice_3/analysis/feature_engineering.py`
- Automated tests: `tests/test_feature_engineering.py`
- Machine-readable audit: `outputs/results/phase_02_feature_quality.json`

Full feature table không được lưu theo persistence policy. Phase 3 phải tái tạo bảng feature từ processed dataset, source và config chính thức.

## 7. Giới hạn được giữ lại

- Phase 2 không fill hoặc drop missing value.
- Phase 2 chưa chia `X/y`, chưa tạo common validity mask và chưa split train/test.
- Metadata được giữ để truy vết nhưng không thuộc model feature set.
- Chưa train, tune hoặc đánh giá model.

## 8. Kết luận

```text
PHASE 02: PASS
HANDOFF TO PHASE 03: READY FOR HUMAN APPROVAL
```

Phase 3 chỉ được triển khai sau khi Human phê duyệt. Việc tạo common validity mask và loại sample không hợp lệ thuộc phạm vi Phase 3.
