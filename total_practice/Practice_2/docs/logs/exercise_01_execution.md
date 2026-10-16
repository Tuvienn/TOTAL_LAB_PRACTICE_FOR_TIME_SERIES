# EXERCISE 01 — EXECUTION LOG

## Scope

EDA, date-to-time-index conversion, original-series visualization and chronological
train/test boundary. No ADF, differencing, model training or forecasting was run.

## Executed Steps

- Loaded `datasets/raw/a10.csv` without modifying the raw file.
- Validated schema `date,value`.
- Parsed `date` and set it as a monthly `DatetimeIndex`.
- Checked chronology, duplicates, missing values and missing monthly intervals.
- Created chronological 80/20 split and sealed the test portion.
- Created and inspected `outputs/figures/01_original_time_series.png`.

## Evidence

```text
rows: 204
date range: 1991-07-01 to 2008-06-01
frequency: monthly start (MS)
missing values: 0
duplicate timestamps: 0
missing monthly intervals: 0
train: 163 observations, 1991-07-01 to 2005-01-01
test: 41 observations, 2005-02-01 to 2008-06-01
```

## EDA Findings

The series has a clear increasing long-term trend. Repeating within-year movement
is visible in the original plot, indicating a possible annual seasonal pattern.
Because the level and mean change over time, the series is initially assessed as
likely non-stationary. This is an EDA observation only; ADF belongs to E02.

## Outputs

- `outputs/figures/01_original_time_series.png`
- `outputs/results/dataset_validation.csv`
- `outputs/results/train_test_boundary.csv`

## Validation

`python -m pytest -q`: 2 passed.
