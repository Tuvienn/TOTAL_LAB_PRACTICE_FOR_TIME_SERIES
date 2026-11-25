# Phase 7 — Final Forecasting và Evaluation

## Mục tiêu

Đánh giá model đã khóa trên historical holdout bằng one-step và recursive
24-hour protocols, không thay đổi model sau khi mở holdout.

## Kết quả chính

- One-step common observations: `8,592`.
- Recursive evaluation: `357` origins và `8,568` predictions.
- `xgboost_tuned` đạt MAE `102.841 MW`, RMSE `137.929 MW` ở one-step.
- Recursive pooled MAE `509.652 MW`, RMSE `720.451 MW`.

## Evidence

- <a href="../../notebooks/Practice_3_present.ipynb" style="color:#1f6feb;">Notebook chính — cells 32–37</a>
- <a href="../../src/practice_3_v2/analysis/forecasting.py" style="color:#1f6feb;">Source: forecasting.py</a> · <a href="../../src/practice_3_v2/analysis/evaluation.py" style="color:#1f6feb;">evaluation.py</a> · <a href="../../src/practice_3_v2/visualization/forecast_evaluation.py" style="color:#1f6feb;">forecast_evaluation.py</a>
- <a href="../../tests/test_evaluation.py" style="color:#1f6feb;">Evaluation tests</a>
- <a href="../../outputs/results/phase_07_evaluation_audit.json" style="color:#1f6feb;">Evaluation audit</a> · <a href="../../outputs/results/phase_07_one_step_metrics.json" style="color:#1f6feb;">One-step metrics</a> · <a href="../../outputs/results/phase_07_recursive_metrics.json" style="color:#1f6feb;">Recursive metrics</a>
- Predictions: <a href="../../outputs/results/phase_07_one_step_predictions.csv" style="color:#1f6feb;">one-step</a> · <a href="../../outputs/results/phase_07_recursive_predictions.csv" style="color:#1f6feb;">recursive</a>
- Figures: <a href="../../outputs/figures/phase_07_one_step_first_14_days.png" style="color:#1f6feb;">first 14 days</a> · <a href="../../outputs/figures/phase_07_one_step_full_holdout.png" style="color:#1f6feb;">full holdout</a> · <a href="../../outputs/figures/phase_07_recursive_error_by_horizon.png" style="color:#1f6feb;">recursive error</a>
- <a href="../phase_details/PHASE_07_FINAL_FORECASTING_EVALUATION.md" style="color:#1f6feb;">Phase detail</a> · <a href="../logs/PHASE_07_EXECUTION.md" style="color:#1f6feb;">Execution log</a> · <a href="../../runs/P7_final_evaluation_20261025_010952_89adcf1a/P7_final_evaluation_20261025_010952_89adcf1a.log" style="color:#1f6feb;">Raw `.log`</a>

## Trạng thái

`PASS` — Holdout evaluation hoàn tất sau preflight.
