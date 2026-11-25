# Phase 7 — XGBoost

## Mục tiêu

Chọn cấu hình XGBoost bằng Validation và early stopping trước khi đánh giá trên
Test.

## Kết quả chính

- Cấu hình tốt nhất theo recursive Validation: `max_depth=7`, `n_estimators=500`.
- `best_iteration=497`; điểm dừng sớm gần giới hạn tìm kiếm.
- Validation: RMSE `3888.1469`, MAE `3078.3164`, MAPE `10.4053%`.
- Test: RMSE `3664.4820`, MAE `2935.2076`, MAPE `9.9482%`.

## Artifact

- <a href="../../results/model_summaries/XGBoost_summary.txt" style="color:#1f6feb;">XGBoost summary</a>
- <a href="../../results/model_summaries/XGBoost_tuning_results.csv" style="color:#1f6feb;">Tuning results</a>
- <a href="../../results/model_summaries/XGBoost_feature_importance.csv" style="color:#1f6feb;">Feature importance</a>
- <a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">Notebook</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>

## Trạng thái

`Đã chạy`.
