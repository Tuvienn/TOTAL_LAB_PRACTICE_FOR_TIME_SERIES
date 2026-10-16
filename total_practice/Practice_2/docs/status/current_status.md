# PRACTICE 2 — CURRENT STATUS

## Current Stage

```text
EXERCISE_01_COMPLETED
EXERCISE_02_COMPLETED
EXERCISE_03_BLOCKED_BY_SCIENTIFIC_RESULT
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
EXERCISE_03_COMPLETED=false

## Exercise 03 Result

```text
first difference created: true
ADF statistic: -1.706074
p-value: 0.427986
decision: fail to reject H0
selected d: REVIEW_REQUIRED
blocker: first difference is not supported as stationary by current ADF evidence
```
```
