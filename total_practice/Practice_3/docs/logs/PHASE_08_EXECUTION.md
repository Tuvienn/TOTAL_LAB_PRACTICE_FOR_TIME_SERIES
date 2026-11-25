# PHASE 08 — EXECUTION LOG

## 1. Trạng thái

```text
Phase: 8 — Error & Interpretation Analysis
Design: APPROVED
Implementation: COMPLETED
Preflight: PASS
Human execution: COMPLETED — PASS
Locked-model refit: COMPLETED — 108,083 DEVELOPMENT SAMPLES
Official Phase 8 outputs: PASS
Technical review: PASS
Human result review: APPROVED
Current gate: READY FOR PHASE 9 DESIGN
```

AI đã hoàn tất source, visualization, tests và preflight theo phase detail được
duyệt. Human đã chạy refit/analysis; official bundle đã PASS technical review và
được Human phê duyệt.

## 2. Thành phần đã triển khai

```text
config/error_analysis.json
src/practice_3_v2/analysis/interpretation.py
src/practice_3_v2/visualization/error_analysis.py
tests/test_interpretation.py
```

Implementation đã khóa:

- signed error là `prediction - actual`;
- residual summary cho cả ba candidates;
- exact-timestamp residual ACF từ lag 1 đến 168 giờ;
- deterministic top-10 absolute errors;
- error regime chung theo hour, day of week, day type, month và actual-load quartile;
- recursive horizon analysis 1–24 từ official Phase 7 metrics;
- normalized XGBoost gain importance, giữ cả feature có gain bằng 0;
- refit chỉ dùng 108.083 eligible development samples;
- không tuning, không model selection lại, không fit holdout và không lưu binary model;
- bundle promotion có rollback nếu bị lỗi hoặc gián đoạn.

## 3. Preflight evidence

Command đã chạy:

```bash
MPLCONFIGDIR=.matplotlib-cache \
  .venv/bin/python -m practice_3_v2.analysis.interpretation --preflight
```

Kết quả:

```text
status: PASS
locked candidate: xgboost_tuned
one-step rows per candidate: 8,592
recursive rows per candidate: 8,568
recursive common origins: 357
feature count: 22
Python: 3.14.3
NumPy: 2.5.4
pandas: 3.1.0
scikit-learn: 1.9.1
XGBoost: 3.4.1
synthetic dependency fit/predict: PASS
project_model_refit_started: false
official_outputs_created: false
```

Preflight chỉ xác minh official Phase 6–7 evidence, checksum, population, model
lock, feature order và dependency. Nó không refit project model và không tạo output
Phase 8.

## 4. Validation evidence

Focused tests:

```text
tests/test_interpretation.py
23/23 PASS
```

Full regression suite:

```text
153/153 PASS
```

Các gate đã kiểm tra gồm contract mutation, residual formulas, exact timestamp
pairs, deterministic ordering, shared regime mapping, row conservation, recursive
horizon transformation, normalized gain, zero-gain feature retention, Human-owned
run state, bundle rollback, no tuning/model selection/binary persistence, no legacy
runtime import và notebook presentation-only boundary.

## 5. Human execution evidence

Human đã chạy đúng command sau tại project root:

```bash
cd "/Users/vientu/Time Series/TOTAL_LAB_PRACTICE_FOR_TIME_SERIES/total_practice/Practice_3"
source .venv/bin/activate

MPLCONFIGDIR=.matplotlib-cache \
  python -m practice_3_v2.analysis.interpretation --run
```

Run hoàn tất:

```text
Run: P8_error_interpretation_20261025_112108_e89bbd23
Checkpoint: COMPLETED
Official outputs promoted: true
Locked candidate: xgboost_tuned
One-step rows per candidate: 8,592
Recursive common origins: 357
Development refit samples: 108,083
Binary model persisted: false
Status: PASS
```

## 6. Technical review

Technical review xác nhận:

1. official và run-local JSON/CSV/PNG giống nhau theo checksum;
2. 22 feature importance rows có rank 1–22, finite và normalized gain cộng đúng 1;
3. mọi regime bảo toàn 8.592 observations/candidate;
4. residual ACF dùng exact timestamp pairs cho lag 1–168;
5. recursive analysis dùng đủ 357 origins và horizons 1–24;
6. không tuning, không model selection lại, không fit holdout và không lưu binary model;
7. bốn figures hợp lệ, rõ và khớp checksum trong official result;
8. notebook trình bày Phase 8, clean-execute 27/27 code cells, không lỗi;
9. focused tests 23/23 PASS, full regression suite 153/153 PASS.

Kết quả chính:

| Hạng mục | Kết quả |
|---|---:|
| XGBoost one-step mean signed error | −1,192 MW |
| XGBoost one-step MAE / RMSE | 102,841 / 137,929 MW |
| XGBoost absolute-error P95 | 273,097 MW |
| Residual ACF lag 1 | 0,2750 |
| XGBoost recursive hardest horizon | 19 — MAE 813,359 MW |
| `lag_1h` normalized gain | 89,224% |
| Tổng normalized gain nhóm lag | 93,467% |

Residual còn phụ thuộc ở lag 1/2 và các bội 24 giờ. Đây là giới hạn khoa học cần
giữ trong kết luận Phase 9, không phải quyền quay lại thay model ở Phase 8.
