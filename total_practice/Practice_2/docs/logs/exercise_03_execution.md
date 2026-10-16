# EXERCISE 03 — EXECUTION LOG

## Scope

First-order differencing and ADF retest on the original training series. No ACF/PACF,
model fitting or forecasting was performed.

## Evidence

```text
original training observations: 163
differenced observations: 162
ADF statistic: -1.706074
p-value: 0.427986
used lag: 13
n observations: 148
alpha: 0.05
decision: fail to reject H0
selected d: REVIEW_REQUIRED
```

## Outputs

- `outputs/figures/02_first_differenced_series.png`
- `outputs/results/adf_differenced_series.csv`
- `outputs/results/adf_differenced_critical_values.csv`
- `outputs/results/differencing_decision.csv`

## Blocker

The first difference did not reject the ADF unit-root null hypothesis. Therefore the
workflow must not silently increase differencing or continue to E04. `d = 1` is not
confirmed by the current evidence; the decision remains `REVIEW_REQUIRED`.

## Validation

Notebook execution completed successfully. `python -m pytest -q`: 4 passed.
