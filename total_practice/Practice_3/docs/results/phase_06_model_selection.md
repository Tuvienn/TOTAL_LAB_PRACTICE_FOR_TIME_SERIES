# Phase 6 — Model Selection

## Mục tiêu

So sánh baseline và candidate models bằng expanding-window CV trên development,
sau đó khóa model trước khi mở historical holdout.

## Kết quả chính

- Candidate registry gồm persistence, seasonal-naive 24h, XGBoost baseline,
  Random Forest và XGBoost tuned.
- Model được khóa: `xgboost_tuned` với `22` features.
- Mean CV MAE: `108.254067`; mean CV RMSE: `143.850149`.
- Holdout chưa được đánh giá trong Phase 6.

## Evidence

- <a href="../../notebooks/Practice_3_present.ipynb" style="color:#1f6feb;">Notebook chính — cells 23–31</a>
- <a href="../../src/practice_3_v2/analysis/model_training.py" style="color:#1f6feb;">Source: model_training.py</a> · <a href="../../src/practice_3_v2/analysis/metrics.py" style="color:#1f6feb;">metrics.py</a> · <a href="../../src/practice_3_v2/analysis/supplemental_experiments.py" style="color:#1f6feb;">supplemental_experiments.py</a>
- <a href="../../tests/test_model_training.py" style="color:#1f6feb;">Model tests</a>
- <a href="../../outputs/results/phase_06_model_lock.json" style="color:#1f6feb;">Model lock</a> · <a href="../../outputs/results/phase_06_cv_results.json" style="color:#1f6feb;">CV results</a> · <a href="../../outputs/results/phase_06_training_diagnostics.json" style="color:#1f6feb;">Training diagnostics</a>
- <a href="../../outputs/figures/phase_06_cv_comparison.png" style="color:#1f6feb;">CV comparison</a> · <a href="../../outputs/figures/phase_06_selected_candidate_folds.png" style="color:#1f6feb;">Selected folds</a> · <a href="../../outputs/figures/phase_06_tuning_candidates.png" style="color:#1f6feb;">Tuning candidates</a>
- <a href="../phase_details/PHASE_06_MODEL_SELECTION.md" style="color:#1f6feb;">Phase detail</a> · <a href="../logs/PHASE_06_EXECUTION.md" style="color:#1f6feb;">Execution log</a>
- Raw logs: <a href="../../runs/P6_model_selection_20261025_002459_c83b80bb/P6_model_selection_20261025_002459_c83b80bb.log" style="color:#1f6feb;">model selection</a> · <a href="../../runs/P6_supplemental_20261025_165310_678c64f3/P6_supplemental_20261025_165310_678c64f3.log" style="color:#1f6feb;">supplemental</a>

## Trạng thái

`PASS` — Model lock được tạo trước Phase 7.
