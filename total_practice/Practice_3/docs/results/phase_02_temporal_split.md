# Phase 2 — Temporal Split và Validation

## Mục tiêu

Khóa development/holdout boundary và expanding-window validation trước EDA,
feature engineering và model selection.

## Kết quả chính

- Development: `112,535` timeline rows, `112,509` observed targets.
- Historical holdout: `8,761` rows, `8,760` observed targets.
- Expanding-window validation: `5` folds, không shuffle, không overlap.
- Holdout được đánh dấu historical re-evaluation, không tuyên bố unseen.

## Evidence

- <a href="../../notebooks/Practice_3_present.ipynb" style="color:#1f6feb;">Notebook chính — cells 6–9</a>
- <a href="../../src/practice_3/data/temporal_split.py" style="color:#1f6feb;">Source: temporal_split.py</a>
- <a href="../../tests/test_temporal_split.py" style="color:#1f6feb;">Tests</a>
- <a href="../../outputs/results/phase_02_temporal_split.json" style="color:#1f6feb;">Temporal split JSON</a>
- <a href="../phase_details/PHASE_02_TEMPORAL_SPLIT_VALIDATION.md" style="color:#1f6feb;">Phase detail</a>
- <a href="../logs/PHASE_02_EXECUTION.md" style="color:#1f6feb;">Execution log</a>

## Figures và raw log

Phase 2 không có figure riêng và chưa có raw `.log`.

## Trạng thái

`PASS` — Boundary được khóa trước các bước downstream.
