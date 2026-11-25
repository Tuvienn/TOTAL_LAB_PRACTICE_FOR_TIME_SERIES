# PHASE 06 SUPPLEMENTAL — EXECUTION LOG

## 1. Trạng thái

```text
Parent phase: Phase 6 — Baseline, Training, Tuning & Model Lock
Design: APPROVED
Implementation: COMPLETED
Focused tests after execution: 23/23 PASS
Full regression suite after execution: 176/176 PASS
Preflight: PASS
Human execution: COMPLETED — 35/35 FITS
Official supplemental artifacts: PASS
Artifact technical review: PASS
Notebook presentation: PASS — 30/30 CODE CELLS, NO ERRORS
Selection authority: NONE
Model lock changed: NO
Current gate: HUMAN SUPPLEMENTAL RESULT REVIEW
```

Đây là post-hoc supplemental evidence phục vụ hai câu hỏi của đề bài, không phải
model selection mới. Kết quả không được thay candidate `xgboost_tuned` đã khóa.

## 2. Thành phần đã triển khai

```text
config/supplemental_experiments.json
src/practice_3_v2/analysis/supplemental_experiments.py
src/practice_3_v2/visualization/supplemental_experiments.py
tests/test_supplemental_experiments.py
```

Implementation gồm:

- Linear Regression dùng `StandardScaler → LinearRegression`, scaler chỉ fit trên
  từng fold-train;
- đúng 22 features, 5 folds và 42.413 official validation predictions của Phase 6;
- lag sensitivity với `p = [1, 6, 12, 24, 48, 168]`;
- mọi `p` dùng cùng train/validation timestamps hợp lệ tại `p=168`;
- fixed locked XGBoost parameters, không tuning và không selection lại;
- checkpoint sau từng fit, resume identity và atomic bundle promotion;
- không đọc holdout rows vào development dataframe, không đánh giá holdout và
  không persist binary model.

## 3. Preflight evidence

Command AI đã chạy:

```bash
MPLCONFIGDIR=/private/tmp/practice3v2-mpl \
  .venv/bin/python -m practice_3_v2.analysis.supplemental_experiments --preflight
```

Kết quả:

```text
status: PASS
linear folds: 5
linear features: 22
lag p values: 1, 6, 12, 24, 48, 168
planned project-data fits: 35
project-data training started: false
holdout accessed/evaluated: false/false
official supplemental outputs: not created
```

Natural development eligibility:

| p | Eligible samples |
|---:|---:|
| 1 | 112.482 |
| 6 | 112.347 |
| 12 | 112.185 |
| 24 | 111.861 |
| 48 | 111.213 |
| 168 | 108.083 |

Eligibility giảm đơn điệu đúng thiết kế. Common comparison population tại
`p=168` có fold counts trùng official Phase 6 population.

## 4. Validation evidence

```text
tests/test_supplemental_experiments.py: 23/23 PASS
Full v2 regression suite: 176/176 PASS
```

Tests kiểm tra contract mutation, checksum/package/fold/feature lock, lag alignment,
current/future leakage, missing-value policy, common timestamps, fold-local scaler,
known metric result, checkpoint/resume identity, 35-task contract, bundle rollback,
no tuning/model selection/binary persistence và notebook presentation-only boundary.

## 5. Human execution evidence

Human đã chạy tại project root và hoàn tất:

```text
Run: P6_supplemental_20261025_165310_678c64f3
Checkpoint: COMPLETED
Completed tasks: 35/35
Official outputs promoted: true
Holdout accessed/evaluated: false/false
Selection authority: none
Model lock changed: false
Status: PASS
```

## 6. Technical review

Technical review xác nhận:

1. checkpoint có đủ 5 Linear Regression fits và 30 lag-p XGBoost fits;
2. official JSON/PNG khớp checksum trong audit và run-local artifacts;
3. Linear Regression và XGBoost reference dùng cùng 42.413 validation samples;
4. mọi `p` dùng cùng fold populations hợp lệ tại `p=168`;
5. natural eligibility giảm đơn điệu từ 112.482 xuống 108.083 samples;
6. model-lock SHA-256 vẫn là
   `ad31cb65daa36c394d7d5afc2cf0af333760c8e75ba718e702368e260db70eee`;
7. không tuning, không selection lại, không holdout evaluation và không binary model;
8. hai PNG hợp lệ ở kích thước 1582×943 và 1741×1418;
9. focused tests 23/23 PASS, full regression suite 176/176 PASS.

Kết quả chính:

| Experiment | MAE (MW) | RMSE (MW) |
|---|---:|---:|
| Linear Regression — 22 features | 136,762 | 186,096 |
| Official tuned XGBoost reference | 108,254 | 143,850 |
| Lag p=1 | 418,024 | 537,415 |
| Lag p=6 | 181,480 | 253,183 |
| Lag p=12 | 164,377 | 228,723 |
| Lag p=24 | 135,706 | 185,067 |
| Lag p=48 | 132,157 | 177,091 |
| Lag p=168 | 135,620 | 180,438 |

Trên cùng official CV population, tuned XGBoost có MAE thấp hơn Linear Regression
20,845%. Với lag-only experiment, lỗi giảm mạnh từ `p=1` đến `p=24`, cải thiện
nhẹ tại `p=48`, rồi tăng trở lại tại `p=168`. Vì đây là post-hoc evidence, kết quả
không có quyền chọn lại official model hoặc official feature schema.

## 7. Notebook presentation

Notebook đã bổ sung subsection Phase 6 Supplemental ngay sau kết luận Phase 6:

- bảng Linear Regression so với official tuned XGBoost reference;
- bảng lag sensitivity cho `p = 1, 6, 12, 24, 48, 168`;
- official model-comparison và lag-sensitivity figures;
- kết luận ngắn gọn và post-hoc scientific disclosure.

Notebook chỉ đọc official JSON/PNG, không import training source, không `.fit()` và
không `.predict()`. Clean-kernel execution PASS **30/30 code cells**, không có error.
Sau notebook execution, focused tests vẫn 23/23 PASS và full suite 176/176 PASS.

## 8. Next gate

Chờ Human duyệt supplemental results trước khi thiết kế chi tiết Phase 9.
