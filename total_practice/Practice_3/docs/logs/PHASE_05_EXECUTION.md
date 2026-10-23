# PHASE 05 — EXECUTION LOG

## 1. Trạng thái

```text
Phase: 05 — Model Training & Selection
Current checkpoint: Phase 5 completed and model lock reviewed
Execution date: 2026-10-21 to 2026-10-22
Screening result: PASS
Full Phase 5 result: PASS
```

Phase 5 đã hoàn thành. Final test chưa được predict hoặc tính metric và vẫn được giữ sealed cho Phase 6.

## 2. Môi trường đã dùng

```text
Python: 3.14.3
matplotlib: 3.11.2
NumPy: 2.5.4
pandas: 3.0.6
scikit-learn: 1.9.1
XGBoost: 3.4.1
pytest: 9.1.1
```

## 3. Run identity

```text
Run ID: P5_xgb_screening_20261021_093122_5f9ebe35
Execution identity: b68f1bf379e5415c16696318c4b9342a0f5d759fbc0019504be9ff0bb8f28898
Completed folds: 30/30
Warnings: 0
Final test evaluated: NO
```

Run cục bộ nằm tại `runs/P5_xgb_screening_20261021_093122_5f9ebe35/`. Bản kết quả trong run và `outputs/results/phase_05_screening_results.json` có cùng SHA-256:

```text
8f8102371857429a3848e66345fe956a66b0b147721f68099cdae28c7e0f2c91
```

## 4. Forecasting baselines

| Baseline | Mean MAE | Std MAE | Mean RMSE | Std RMSE |
|---|---:|---:|---:|---:|
| Seasonal Naive 24 | 902.7222 | 55.8447 | 1212.5890 | 64.0780 |
| Persistence | 429.5620 | 74.1336 | 546.1221 | 76.9045 |

Hai baseline được đánh giá trên đúng năm validation folds của Phase 4 và không sử dụng final test.

## 5. XGBoost feature screening

| Configuration | Features | Mean MAE | Std MAE | Mean RMSE | Std RMSE | Training time (s) |
|---|---:|---:|---:|---:|---:|---:|
| `lag_only_p24` | 24 | 141.9273 | 8.7142 | 188.1851 | 14.3920 | 3.9891 |
| `lag_only_p72` | 72 | 134.9939 | 7.1257 | 177.2558 | 11.5086 | 7.3166 |
| `lag_only_p168` | 168 | 132.1500 | 5.3571 | 172.5856 | 8.3094 | 11.7888 |
| `lag_rolling_p24` | 28 | 141.3808 | 8.6172 | 187.4431 | 14.8566 | 4.5426 |
| `lag_rolling_p72` | 76 | 134.6228 | 6.6485 | 176.7809 | 10.4864 | 6.8039 |
| `lag_rolling_p168` | 172 | 131.7834 | 5.5706 | 171.9402 | 8.8840 | 12.7565 |

## 6. Feature-configuration selection

```text
Best raw mean MAE: lag_rolling_p168 = 131.7834
1% MAE threshold: 133.1013
Candidates within threshold: lag_only_p168, lag_rolling_p168
Selected configuration: lag_only_p168
```

`lag_only_p168` có mean MAE cao hơn `lag_rolling_p168` khoảng 0,278%, vẫn nằm trong ngưỡng 1% đã duyệt. Vì `lag_only_p168` dùng 168 features thay vì 172, deterministic selection rule ưu tiên configuration ít features hơn.

Selection này không khẳng định hai configuration tương đương thống kê; đây là quyết định theo policy đã duyệt của Phase 5.

## 7. XGBoost tuning

```text
Run ID: P5_xgb_tuning_20261021_223345_570615e3
Candidates: 24/24
CV fold metrics: 120/120
Unique parameter configurations: 24
Warnings: 0
Execution time: 387.394 seconds
Result: PASS
```

Best candidate là candidate index 6:

```text
subsample = 0.85
reg_lambda = 1.0
reg_alpha = 0.1
n_estimators = 800
min_child_weight = 5
max_depth = 7
learning_rate = 0.05
colsample_bytree = 1.0
```

Các fixed parameters còn lại:

```text
objective = reg:squarederror
tree_method = hist
random_state = 42
n_jobs = -1
```

| Candidate | Mean MAE | Std MAE | Mean RMSE | Std RMSE |
|---|---:|---:|---:|---:|
| XGBoost baseline trên `lag_only_p168` | 132.1500 | 5.3571 | 172.5856 | 8.3094 |
| Tuned XGBoost trên `lag_only_p168` | **115.4782** | 6.8425 | **151.3981** | 8.9931 |

Tuned XGBoost giảm CV mean MAE khoảng 12,62% và mean RMSE khoảng 12,28% so với fixed XGBoost baseline trên cùng feature configuration và cùng CV folds. Đây là kết quả CV TRAIN-only, chưa phải final-test performance.

## 8. Validation evidence

```text
Checkpoint state: COMPLETED
All 30 screening fold states: PASS
All 24 tuning candidates and 120 fold metrics: PASS
Tuning parameter-space validation: PASS
Tuning aggregate and ranking recalculation: PASS
Aggregate metrics recalculation: PASS
Selection-rule recalculation: PASS
Recorded tuning source hash: preserved in the completed tuning run
Current source hash: changed after adding the Random Forest runner
Tuning-critical search protocol after the change: unchanged and regression-tested
Recorded config and upstream hashes match current files: PASS
Random Forest 5/5 folds and aggregate recalculation: PASS
Five-candidate fold identity and population validation: PASS
Deterministic model-selection dry-run: PASS
Official CV-result integrity checks: PASS
Official model-lock integrity checks: PASS
Phase 5 automated tests: 45 passed
Full project tests: 113 passed
git diff check: PASS
```

## 9. Final-test sealing

```text
sealed: true
rows: 8592
feature_matrices_materialized: false
target_values_accessed: false
metrics_computed: false
```

Final test chưa tham gia feature selection, tuning, model selection hoặc metric calculation.

## 10. Artifacts hiện có

- Model-training configuration: `config/model_training.json`
- Screening source: `src/practice_3/analysis/model_training.py`
- Automated tests: `tests/test_model_training.py`
- Official screening result: `outputs/results/phase_05_screening_results.json`
- Local run log/checkpoint/figures: `runs/P5_xgb_screening_20261021_093122_5f9ebe35/`
- Local tuning result/log/metadata: `runs/P5_xgb_tuning_20261021_223345_570615e3/`
- Local Random Forest result/log/checkpoint: `runs/P5_random_forest_20261022_001632_c920098a/`
- Local model-lock run: `runs/P5_model_lock_20261022_160510_a5255bc8/`
- Official CV result: `outputs/results/phase_05_cv_results.json`
- Official model lock: `outputs/results/phase_05_model_lock.json`

## 11. Random Forest execution result

```text
Run ID: P5_random_forest_20261022_001632_c920098a
Feature configuration: lag_only_p168
Features: 168
CV folds: 5/5 PASS
Warnings: 0
Execution time: 1137.679 seconds
Mean MAE: 132.8500
Std MAE: 9.7066
Mean RMSE: 177.7796
Std RMSE: 15.1697
Final test evaluated: NO
Result: PASS
```

Fixed parameters đúng với Phase 5 specification:

```text
n_estimators = 300
max_depth = null
min_samples_split = 2
min_samples_leaf = 1
max_features = 1.0
bootstrap = true
random_state = 42
n_jobs = -1
```

Runner xác minh tuning artifact, configuration, upstream identities, source identity và fold identity trước khi bắt đầu hoặc resume. Fold đã `PASS` được giữ lại; không có model binary và không có final-test access.

## 12. Five-candidate selection và model-lock readiness

| Candidate | Mean MAE | Std MAE | Mean RMSE | Std RMSE |
|---|---:|---:|---:|---:|
| Seasonal Naive 24 | 902.7222 | 55.8447 | 1212.5890 | 64.0780 |
| Persistence | 429.5620 | 74.1336 | 546.1221 | 76.9045 |
| XGBoost baseline | 132.1500 | 5.3571 | 172.5856 | 8.3094 |
| Tuned XGBoost | **115.4782** | 6.8425 | **151.3981** | 8.9931 |
| Random Forest | 132.8500 | 9.7066 | 177.7796 | 15.1697 |

```text
Best mean MAE: 115.4782
1% MAE threshold: 116.6330
Candidates within threshold: xgboost_tuned
CV-selected candidate: xgboost_tuned
Full-TRAIN refit rows: 108083
Prediction in refit: NO
Binary model persistence: NO
Final test included: NO
Runner state: READY_FOR_HUMAN_EXECUTION
```

Full-TRAIN refit đã hoàn thành trên 108.083 rows và 168 features trong 8,355 giây, không warning. Refit không predict và không lưu binary model. Hai official outputs đã được tạo và trùng SHA-256 với bản trong local run:

```text
phase_05_cv_results.json: 02159768a681ead1dd1892d1d87cb08af43b105582c1f4ad91a036505a9d9933
phase_05_model_lock.json: d88354aebf6e41cad481387c9eec07b4079b89b6653a447af9a3058c58c5103f
```

## 13. Kết luận checkpoint

```text
FEATURE SCREENING: PASS
SELECTED FEATURE CONFIGURATION: lag_only_p168
XGBOOST TUNING EXECUTION: PASS
TUNED XGBOOST CV MEAN MAE: 115.4782
RANDOM FOREST RUNNER: READY
RANDOM FOREST COMPARISON: PASS
CV-SELECTED CANDIDATE: xgboost_tuned
MODEL-LOCK RUNNER: PASS
FULL-TRAIN REFIT: PASS
MODEL LOCK: PASS
FINAL TEST: SEALED
PHASE 05: PASS
```

Bước tiếp theo là review lại Phase 6 detailed design và lập implementation plan. Final test chỉ được mở theo protocol Phase 6 sau khi Human duyệt plan.
