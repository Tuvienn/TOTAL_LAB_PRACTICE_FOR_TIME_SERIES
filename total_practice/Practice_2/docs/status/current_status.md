# PRACTICE 2 — CURRENT STATUS

## Current Stage

```text
EXERCISE_01_COMPLETED
EXERCISE_02_COMPLETED
EXERCISE_03_COMPLETED_WITH_LOG_TRANSFORMATION
EXERCISE_04_COMPLETED
EXERCISE_05_COMPLETED_WITH_RESIDUAL_AUTOCORRELATION_LIMITATION
EXERCISE_06_ADVANCED_WORKFLOW_VALIDATED
EXERCISE_06_COMPLETED_AS_EXPLORATORY_EXTENSION
```

## Exercise 04–05 Status Note

```text
confirmed state: E04 and E05 completed
Canonical core notebook: notebooks/Practice_2_Exercise.ipynb
Notebook contents: validated clean-kernel execution evidence
E04/E05 formal execution logs and status reconciliation: completed
```

The E04 and E05 specifications and before-process plans are now confirmed and
validated. E05 retains a documented residual-autocorrelation limitation.

## Protocol Reconciliation Rerun

```text
execution source: notebooks/Practice_2_Exercise.ipynb, clean-kernel rerun
execution date: 2026-11-25
train observations: 163
test observations: 41
E02 input: original training series only
E03 transformation: natural_log + first difference
E03 selected d: 1
E04 input: log-first-difference training series
E05 fit scale: log training levels with d=1
E05 forecast horizon: 41 months
E05 baseline: seasonal-naive, seasonal period 12
E05 residual diagnostics: Ljung–Box included
formal completion: confirmed in the project record with residual-autocorrelation limitation
```

The rerun establishes reproducible train-only and holdout boundaries for the
confirmed E04/E05 workflow. The residual limitation remains part of the formal
result and does not get hidden by the model comparison.

## Exercise 06 — AirPassengers Advanced Extension Status

```text
implementation source: notebooks/Practice_2_Advanced.ipynb, existing notebook adjusted in place
implementation authorization: true
validation status: completed clean-kernel execution
completion status: completed as an exploratory extension
dataset: airline-passengers.csv
rows: 144
train observations: 115
test observations: 29
split: chronological 80/20, shuffle=false
model comparison: ARIMA(0,1,1) baseline and SARIMA(0,1,1)(0,1,1,12)
completed diagnostics: residual plot, residual ACF and Ljung–Box at lags 12 and 24
completed evaluation: MAE and RMSE on the same 29-month holdout
execution evidence: docs/logs/exercise_06_execution.md
official run: 2026-11-27_e06_113951
official raw log: runs/2026-11-27_e06_113951/Practice_2_Advanced.log
```

Historical exploratory outputs are not used as evidence for the adjusted workflow.
E06 is an advanced extension; the official clean-kernel run and final output
inspection are recorded above. It remains separate from the core E01–E05 result.

## Exercise 01 Evidence

```text
dataset validated: true
rows: 204
monthly index: valid
missing values: 0
duplicate timestamps: 0
missing intervals: 0
train observations: 163
test observations: 41
test set sealed: true
original plot created: true
```

## Scientific Boundary

E01 only records EDA observations. No ADF, differencing, model fitting or forecasting
was performed. The initial EDA assessment is increasing trend, possible annual
seasonality and likely non-stationarity; E02 is required for statistical testing.

## Authorization State

The authorization block below preserves the existing formal E01–E04 record.
`EXERCISE_04_HANDOFF_OPEN=false`; E04 has handed confirmed ARIMA candidates
to E05. E05 is complete with the residual-autocorrelation limitation recorded.

```text
EXERCISE_01_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_01_IMPLEMENTED=true
EXERCISE_01_VALIDATED=true
EXERCISE_01_COMPLETED=true
EXERCISE_02_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_02_IMPLEMENTED=true
EXERCISE_02_VALIDATED=true
EXERCISE_02_COMPLETED=true
EXERCISE_03_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_03_IMPLEMENTED=true
EXERCISE_03_VALIDATED=true
EXERCISE_03_COMPLETED=true
EXERCISE_03_BLOCKED_BY_SCIENTIFIC_RESULT=false
EXERCISE_04_HANDOFF_OPEN=false
```

## Exercise 03 Result

```text
raw first difference created: true
raw first-difference ADF statistic: -1.706074
raw first-difference p-value: 0.427986
raw first-difference decision: fail to reject H0
remediation transformation: natural logarithm
regular differencing order: 1
log first-differenced observations: 162
remaining missing values: 0
ADF statistic: -3.659486
p-value: 0.004720
used lag: 13
n observations: 148
decision: reject H0
selected d: 1
stationarity supported: true on log first-differenced training scale
test set used: false
E04 handoff: completed and closed
```

## Exercise 03 Limitation

ADF evidence supports removal of the non-seasonal unit root on the log first-differenced
training scale. The inspected plot still shows recurring annual spikes, so this result
does not claim that seasonal dependence has disappeared. E04 must use the exact
transformed training series and report seasonal ACF/PACF structure honestly.
