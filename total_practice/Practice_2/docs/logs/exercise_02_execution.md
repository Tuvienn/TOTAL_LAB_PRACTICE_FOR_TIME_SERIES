# EXERCISE 02 — EXECUTION LOG

## Scope

ADF test on the original training series from E01. No differencing, ACF/PACF,
model fitting or forecasting was performed.

## Evidence

```text
input: original training series only
train observations: 163
test observations: 41, excluded
alpha: 0.05
ADF statistic: 2.230893
p-value: 0.998907
used lag: 14
n observations: 148
decision: fail to reject H0
```

H0 states that the series has a unit root. Since p-value is greater than 0.05,
there is insufficient evidence to reject H0; the original training series is
not supported as stationary by this test.

## Outputs

- `outputs/results/adf_original_series.csv`
- `outputs/results/adf_original_critical_values.csv`

## Validation

`python -m pytest -q`: 3 passed.
Notebook execution completed successfully.
