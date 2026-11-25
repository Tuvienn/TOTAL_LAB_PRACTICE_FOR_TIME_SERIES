# Phase 3 — TRAIN-only Exploratory Data Analysis

## Mục tiêu

Mô tả trend, distribution, seasonality, lag structure và missingness chỉ trên
development period; holdout không tham gia EDA.

## Kết quả chính

- EDA dùng `112,535` development rows và loại holdout khỏi mọi quyết định.
- Có `26` missing targets trong development; không imputation.
- Trend, seasonality theo giờ/ngày/năm và lag correlation được ghi thành
  official presentation artifacts.

## Evidence

- <a href="../../notebooks/Practice_3_present.ipynb" style="color:#1f6feb;">Notebook chính — cells 10–14</a>
- <a href="../../src/practice_3_v2/analysis/eda.py" style="color:#1f6feb;">Source: eda.py</a>
- <a href="../../src/practice_3_v2/analysis/eda_presentation.py" style="color:#1f6feb;">Source: eda_presentation.py</a>
- <a href="../../tests/test_eda.py" style="color:#1f6feb;">Tests</a>
- <a href="../../outputs/results/phase_03_eda_summary.json" style="color:#1f6feb;">EDA summary</a> · <a href="../../outputs/results/phase_03_eda_presentation.json" style="color:#1f6feb;">Presentation JSON</a>
- <a href="../phase_details/PHASE_03_TRAIN_ONLY_EDA.md" style="color:#1f6feb;">Phase detail</a>
- <a href="../logs/PHASE_03_EXECUTION.md" style="color:#1f6feb;">Execution log</a>

## Figures

<a href="../../outputs/figures/phase_03_trend.png" style="color:#1f6feb;">Trend</a> ·
<a href="../../outputs/figures/phase_03_distribution.png" style="color:#1f6feb;">Distribution</a> ·
<a href="../../outputs/figures/phase_03_anomaly_screening.png" style="color:#1f6feb;">Anomaly screening</a> ·
<a href="../../outputs/figures/phase_03_annual_stability.png" style="color:#1f6feb;">Annual stability</a> ·
<a href="../../outputs/figures/phase_03_hour_day_heatmap.png" style="color:#1f6feb;">Hour/day heatmap</a> ·
<a href="../../outputs/figures/phase_03_lag_correlation.png" style="color:#1f6feb;">Lag correlation</a> ·
<a href="../../outputs/figures/phase_03_seasonality_profiles.png" style="color:#1f6feb;">Seasonality profiles</a>

## Trạng thái

`PASS` — EDA chỉ dùng development data.
