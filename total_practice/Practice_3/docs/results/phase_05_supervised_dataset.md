# Phase 5 — Time Series to Supervised Learning

## Mục tiêu

Ghép feature vector với target theo `target_timestamp`, áp dụng eligibility rule
và giữ chronological expanding-window folds.

## Kết quả chính

- Feature count: `22`.
- Development eligible samples: `108,083`.
- Target phải observed/finite; feature vector phải đầy đủ/finite.
- Không shuffle và không imputation target.

## Evidence

- <a href="../../notebooks/Practice_3_present.ipynb" style="color:#1f6feb;">Notebook chính — cells 19–22</a>
- <a href="../../src/practice_3/data/supervised_dataset.py" style="color:#1f6feb;">Source: supervised_dataset.py</a>
- <a href="../../src/practice_3/analysis/supervised_presentation.py" style="color:#1f6feb;">Source: supervised_presentation.py</a>
- <a href="../../tests/test_supervised_dataset.py" style="color:#1f6feb;">Tests</a>
- <a href="../../outputs/results/phase_05_supervised_dataset.json" style="color:#1f6feb;">Supervised dataset audit</a> · <a href="../../outputs/results/phase_05_supervised_presentation.json" style="color:#1f6feb;">Presentation JSON</a>
- <a href="../../outputs/figures/phase_05_time_series_to_supervised.png" style="color:#1f6feb;">Time-series-to-supervised figure</a>
- <a href="../phase_details/PHASE_05_XY_CONSTRUCTION.md" style="color:#1f6feb;">Phase detail</a> · <a href="../logs/PHASE_05_EXECUTION.md" style="color:#1f6feb;">Execution log</a>

## Trạng thái

`PASS` — X/y alignment và eligibility đã được audit.
