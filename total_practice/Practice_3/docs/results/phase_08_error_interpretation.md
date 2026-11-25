# Phase 8 — Error và Interpretation

## Mục tiêu

Phân tích residual, error theo thời gian/load regime và feature importance sau
đánh giá; không refit hoặc thay đổi model chính.

## Kết quả chính

- Phân tích là post-hoc và không được dùng để chọn lại model.
- One-step `xgboost_tuned` có MAE `102.841 MW`, RMSE `137.929 MW`.
- Residual còn autocorrelation ở các lag đầu; không tuyên bố residual hoàn toàn
  là white noise.

## Evidence

- <a href="../../notebooks/Practice_3_present.ipynb" style="color:#1f6feb;">Notebook chính — cells 38–43</a>
- <a href="../../src/practice_3/analysis/interpretation.py" style="color:#1f6feb;">Source: interpretation.py</a> · <a href="../../src/practice_3/visualization/error_analysis.py" style="color:#1f6feb;">error_analysis.py</a>
- <a href="../../tests/test_interpretation.py" style="color:#1f6feb;">Interpretation tests</a>
- <a href="../../outputs/results/phase_08_error_analysis.json" style="color:#1f6feb;">Error analysis JSON</a> · <a href="../../outputs/results/phase_08_feature_importance.csv" style="color:#1f6feb;">Feature importance CSV</a>
- Figures: <a href="../../outputs/figures/phase_08_error_by_load_regime.png" style="color:#1f6feb;">load regime</a> · <a href="../../outputs/figures/phase_08_error_by_time.png" style="color:#1f6feb;">error by time</a> · <a href="../../outputs/figures/phase_08_feature_importance.png" style="color:#1f6feb;">feature importance</a> · <a href="../../outputs/figures/phase_08_residual_diagnostics.png" style="color:#1f6feb;">residual diagnostics</a>
- <a href="../phase_details/PHASE_08_ERROR_INTERPRETATION.md" style="color:#1f6feb;">Phase detail</a> · <a href="../logs/PHASE_08_EXECUTION.md" style="color:#1f6feb;">Execution log</a> · <a href="../../runs/P8_error_interpretation_20261025_112108_e89bbd23/P8_error_interpretation_20261025_112108_e89bbd23.log" style="color:#1f6feb;">Raw `.log`</a>

## Trạng thái

`PASS` — Interpretation hoàn tất, không thay đổi official model.
