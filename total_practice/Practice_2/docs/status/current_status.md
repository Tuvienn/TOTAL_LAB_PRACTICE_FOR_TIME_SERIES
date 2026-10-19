# PRACTICE 2 — CURRENT STATUS

## Current Stage

```text
EXERCISE_01_COMPLETED
EXERCISE_02_COMPLETED
EXERCISE_03_COMPLETED_WITH_LOG_TRANSFORMATION
EXERCISE_04_HANDOFF_OPEN
```

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
EXERCISE_04_HANDOFF_OPEN=true
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
E04 handoff: open for review
```

## Exercise 03 Limitation

ADF evidence supports removal of the non-seasonal unit root on the log first-differenced
training scale. The inspected plot still shows recurring annual spikes, so this result
does not claim that seasonal dependence has disappeared. E04 must use the exact
transformed training series and report seasonal ACF/PACF structure honestly.
