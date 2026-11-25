# Phase 4 — Leakage-safe Feature Engineering

## Mục tiêu

Tạo lag, rolling và calendar features với timestamp semantics rõ ràng, không
dùng target hiện tại hoặc tương lai.

## Kết quả chính

- Feature schema gồm `22` features.
- Rolling features được shift một giờ; không centered rolling.
- Holdout target không được dùng để tính feature statistics.
- Eligibility và null handling được bàn giao cho Phase 5.

## Evidence

- <a href="../../notebooks/Practice_3_present.ipynb" style="color:#1f6feb;">Notebook chính — cells 15–18</a>
- <a href="../../src/practice_3/analysis/feature_engineering.py" style="color:#1f6feb;">Source: feature_engineering.py</a>
- <a href="../../src/practice_3/analysis/feature_presentation.py" style="color:#1f6feb;">Source: feature_presentation.py</a>
- <a href="../../tests/test_feature_engineering.py" style="color:#1f6feb;">Tests</a>
- <a href="../../outputs/results/phase_04_feature_validation.json" style="color:#1f6feb;">Feature validation</a> · <a href="../../outputs/results/phase_04_feature_presentation.json" style="color:#1f6feb;">Feature presentation</a>
- <a href="../../outputs/figures/phase_04_temporal_feature_correlation.png" style="color:#1f6feb;">Temporal feature correlation</a>
- <a href="../phase_details/PHASE_04_FEATURE_ENGINEERING.md" style="color:#1f6feb;">Phase detail</a> · <a href="../logs/PHASE_04_EXECUTION.md" style="color:#1f6feb;">Execution log</a>

## Trạng thái

`PASS` — Feature contract không có leakage.
