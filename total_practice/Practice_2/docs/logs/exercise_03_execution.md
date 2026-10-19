# EXERCISE 03 — EXECUTION LOG

## Scope

Raw first-order differencing was retained as failed evidence. The approved remediation
applied natural log and regular first differencing to the original training series,
then reran ADF. No ACF/PACF, model fitting or forecasting was performed.

## Evidence

```text
original training observations: 163
test observations: 41, sealed and excluded
all training values positive: true
raw first-differenced observations: 162
raw first-difference ADF statistic: -1.706074
raw first-difference p-value: 0.427986
raw first-difference decision: fail to reject H0
remediation transformation: natural logarithm
regular differencing order: 1
log first-differenced observations: 162
remaining missing values: 0
ADF regression: c
ADF autolag: AIC
ADF statistic: -3.659486
p-value: 0.004720
used lag: 13
n observations: 148
alpha: 0.05
decision: reject H0
selected d: 1
E04 handoff: OPEN_FOR_REVIEW
```

## Outputs

- `outputs/figures/02_first_differenced_series.png`
- `outputs/figures/02_log_first_differenced_series.png`
- `outputs/results/adf_differenced_series.csv`
- `outputs/results/adf_differenced_critical_values.csv`
- `outputs/results/adf_log_first_differenced_series.csv`
- `outputs/results/adf_log_first_differenced_critical_values.csv`
- `outputs/results/e03_transformation_comparison.csv`
- `outputs/results/differencing_decision.csv`

## Decision

The raw first difference did not reject the ADF unit-root null hypothesis. The approved
log first-difference remediation rejected H0 at `alpha=0.05`, so E03 selects natural-log
transformation and regular `d=1` for the training series. Test observations were not used.

## Limitation

The transformed plot retains recurring annual spikes. ADF supports stationarity against
the tested non-seasonal unit root but does not establish that seasonal dependence is absent.
E04 must inspect and report the seasonal lag structure without changing the E03 scale.

## Validation

```text
python -m pytest -q: 11 passed
notebook code cells executed: 10/10
notebook execution errors: 0
raw SHA-256: 4baa700091ba43f59d762ed7112e203134467ecde3f7bc88da3b153040d384cb
legacy notebook modified: false
E04/E05 modified: false
```
