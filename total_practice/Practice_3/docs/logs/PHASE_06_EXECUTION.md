# PHASE 06 — EXECUTION LOG

## 1. Trạng thái

```text
Implementation authorization: GRANTED
Dependency gate: PASS
Source and tests: READY
Preflight: PASS
Project-data training: COMPLETED BY HUMAN
Holdout evaluated: false
Current gate: READY FOR PHASE 7 DESIGN DISCUSSION
```

## 2. Những gì đã triển khai

- Bổ sung optional dependency group `modeling` trong `pyproject.toml`.
- Cài dependency vào `.venv` riêng của `Practice_3`.
- Tạo approved machine-readable contract `config/model_training.json`.
- Tạo metric owner cho MAE, RMSE và five-fold aggregate với `ddof=0`.
- Tạo development-only training runner, candidate registry và deterministic tuning sampler.
- Tạo checkpoint/resume validation và Human-readable `.log` theo format đã duyệt.
- Khóa official promotion: incomplete/interrupted run không được tạo model lock.
- Không persist binary model trong Phase 6.

## 3. Dependency evidence

```text
Python: 3.14.3
NumPy: 2.5.4
Pandas: 3.1.0
scikit-learn: 1.9.1
XGBoost: 3.4.1
Synthetic Random Forest fit/predict: PASS
Synthetic XGBoost fit/predict: PASS
```

## 4. Preflight evidence

```text
Eligible development samples: 108,083
Feature count: 22
Expanding-window folds: 5
Tuning parameter candidates: 24
Sampled parameter-set SHA256:
e957053165058e4a08ae8cee591606766bea228de5f99774fcf5482781e84384
Training started: false
Holdout evaluated: false
Status: PASS
```

## 5. Test evidence

```text
Focused Phase 6 tests: 25/25 PASS
Full v2 regression suite: 107/107 PASS
```

## 6. Human execution boundary

AI đã dừng trước training thật. Human phải trực tiếp chạy lệnh training trên
Terminal. Nếu run bị dừng, Human cũng là người chạy lệnh resume. AI chỉ review
`run.log`, `checkpoint.json` và result JSON sau khi Human báo trạng thái.

Human đã chạy training hoàn tất; AI chỉ bắt đầu review và cập nhật official
presentation sau khi nhận được trạng thái `COMPLETED` từ Human.

## 7. Human training result

```text
Run: runs/P6_model_selection_20261025_002459_c83b80bb
Run status: COMPLETED
Completed tasks: 140/140
Fixed baselines: 2 × 5 folds
Fixed ML candidates: 2 × 5 folds
XGBoost tuning: 24 × 5 folds
Selected tuning candidate: 22
Selected model candidate: xgboost_tuned
Holdout evaluated: false
Binary model persisted: false
```

## 8. CV comparison

| Candidate | Mean CV MAE (MW) | Mean CV RMSE (MW) | MAE std (MW) |
|---|---:|---:|---:|
| Persistence | 416.456221 | 538.292770 | 3.040430 |
| Seasonal Naive 24 | 958.057702 | 1290.709170 | 51.809113 |
| XGBoost baseline | 118.614038 | 156.642573 | 3.185480 |
| Random Forest | 125.403438 | 169.881847 | 4.433046 |
| XGBoost tuned | **108.254067** | **143.850149** | 3.144269 |

`xgboost_tuned` có mean CV MAE thấp nhất và được chọn đúng selection contract.

## 9. Independent technical review

```text
Checkpoint tasks: 140/140 PASS
Tuning configurations: 24/24 PASS
Fold records per candidate/configuration: COMPLETE
Fold aggregates independently recomputed: PASS
Selected tuning configuration: candidate 22 PASS
CV-results/model-lock checksum linkage: PASS
Focused tests: 25/25 PASS
Full regression suite: 107/107 PASS
Notebook clean execution: 19/19 code cells, 0 errors
AI technical review: PASS
Human result review: APPROVED
```

Official artifacts:

- `outputs/results/phase_06_cv_results.json`
- `outputs/results/phase_06_model_lock.json`
- `outputs/figures/phase_06_cv_comparison.png`
- `outputs/results/phase_06_training_diagnostics.json`
- `outputs/figures/phase_06_tuning_candidates.png`
- `outputs/figures/phase_06_selected_candidate_folds.png`
- `notebooks/Practice_3_present.ipynb`

Presentation diagnostics được tạo từ completed tuning JSON, kiểm tra chéo với
official CV result và model lock; không retrain, không đổi selection authority và
không mở historical holdout. Hai figure mới không phải epoch learning curves.

## 10. Human sign-off

```text
Phase 6 result: APPROVED
Model lock accepted: xgboost_tuned
Phase 7 design discussion: AUTHORIZED
Phase 7 implementation: NOT YET AUTHORIZED
Historical holdout evaluated: false
```
