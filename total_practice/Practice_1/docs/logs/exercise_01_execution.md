# Exercise 1 Execution Record

## Scope

```text
Practice: Practice_1
Exercise: 01 — ACF/PACF analysis
Execution date: 2026-10-08
Status: COMPLETED_AND_VALIDATED
Next exercise authorized: NO
```

This record covers repository initialization and Exercise 1 only. Exercise 2 was not
started.

## Runtime and data evidence

```text
Python: 3.12.15
Kernel: time-series-practice-1
Dataset: AirPassengers
Source: https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv
Raw schema: rownames, time, value
Observations: 144 monthly values
Reconstructed range: 1949-01-01 through 1960-12-01
Raw SHA-256: bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8
```

Resolved dependency versions are preserved in `environment_snapshot.txt`.

## Produced evidence

Figures:

```text
outputs/figures/01_time_series_overview.png
outputs/figures/02_acf_40_lags.png
outputs/figures/03_pacf_40_lags.png
```

Machine-readable results:

```text
outputs/results/acf_values.csv
outputs/results/pacf_values.csv
outputs/results/exercise_01_findings.json
```

The notebook `notebooks/practice_1.ipynb` was executed end-to-end with four
ordered code-cell execution counts and no error output.

## Validation

```text
pytest: 2 passed
compileall: passed
notebook execution: passed
figure visual inspection: passed
raw checksum after analysis: unchanged
```

Notebook execution initially encountered the restricted environment's local-port
permission. The same approved notebook command was rerun outside that restriction and
completed successfully. Jupyter emitted only its standard warning about an unencrypted
local TCP kernel connection; it did not affect the analysis or outputs.

## Scientific findings

- The raw monthly series has a clear upward trend, annual seasonal recurrence, and
  increasing seasonal amplitude; it is visually non-stationary.
- Lag-1 ACF is approximately `0.948`, showing strong serial dependence and rejecting a
  white-noise interpretation of the raw series.
- ACF values at lags 12, 24, and 36 are approximately `0.760`, `0.532`, and `0.337`,
  supporting a 12-month seasonal pattern.
- PACF lag 1 is the strongest short-term effect. Lag 13 is the largest later effect by
  absolute magnitude, while lag 12 remains the required seasonal reference.
- ACF/PACF evidence is descriptive here and is not used to choose an ARIMA order.

## Approval boundary

Exercise 1 is complete. Exercise 2 remains `READY_FOR_HUMAN_APPROVAL`; no Exercise 2
implementation is authorized by this record.
