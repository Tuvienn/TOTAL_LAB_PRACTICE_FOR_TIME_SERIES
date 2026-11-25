# EXERCISE 05 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_05
Topic: ARIMA Training, Residual Diagnostics, Forecasting and Evaluation
Plan type: Exercise Before-Process Plan
Dataset: Monthly Retail Sales
Status: CONFIRMED_AND_COMPLETED
Implementation authorized: NO
reported execution: YES, notebook evidence requires formal reconciliation
Upstream handoff: E04 ARIMA candidates; formal status discrepancy remains
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_05_execution.md
```

This plan governs review and reproducible validation of E05. Existing notebook
outputs are exploratory evidence and do not by themselves approve implementation
or establish formal Exercise completion.

## 2. Objective

- verify the E01 chronological holdout and the E04 candidate handoff;
- fit the confirmed one or two ARIMA candidates on training data;
- compare each candidate with a seasonal-naive baseline using seasonal lag 12;
- inspect convergence, fitting warnings, AIC/BIC, and residual diagnostics;
- forecast the sealed test horizon and evaluate MAE, RMSE, and MAPE;
- answer the E05 interpretation questions from inspected execution evidence;
- reconcile the reported E04/E05 completion with formal status and confirmation
  records before marking E05 complete.

E05 covers ARIMA on Monthly Retail Sales. SARIMA on AirPassengers is E06 and is
outside this plan.

## 3. Required Documents

```text
working_rule.md
AGENTS.md
.agents/RULES_INDEX.md
.agents/rules/GENERAL_RULES.md
.agents/rules/CODE_RULES.md
.agents/rules/TIME_SERIES_RULES.md
.agents/workflows/WORKFLOW.md
total_practice/Practice_2/README.md
total_practice/Practice_2/docs/rules/architecture_rule.md
total_practice/Practice_2/docs/rules/rule_code.md
total_practice/Practice_2/docs/plans/project_overview.md
total_practice/Practice_2/docs/plans/plan_overview.md
total_practice/Practice_2/docs/status/current_status.md
total_practice/Practice_2/docs/exercise_details/exercise_05_arima_forecasting_evaluation.md
total_practice/Practice_2/docs/exercise_details/exercise_04_acf_pacf_arima_candidates.md
total_practice/Practice_2/docs/plans/exercise_04_before_process.md
E01–E04 validated evidence, execution logs, and outputs
notebooks/Practice_2_Exercise.ipynb
```

If required upstream evidence is missing or status/confirmation records conflict,
stop and report the discrepancy before formal execution or completion.

## 4. Entry Gate and Current State

The current status records that the confirmationd E04/E05 completion and that
validated notebook execution evidence exists. `EXERCISE_04_HANDOFF_OPEN=false`
records the confirmed E04 handoff to E05.

Therefore:

```text
confirmed E05 notebook run: validated
Formal E04 handoff state: resolved
E05 specification confirmation: confirmed
E05 plan confirmation: confirmed
Formal E05 completion: confirmed with residual-autocorrelation limitation
```

The confirmed run is now treated as official E05 evidence. The residual
autocorrelation limitation remains visible in the execution evidence and is not
silently converted into a white-noise claim.

## 5. Upstream Input Contract

```text
Dataset: datasets/raw/a10.csv
Validated observations: 204
Training observations: 163
Test observations: 41
Train period: 1991-07 through 2005-01
Test period: 2005-02 through 2008-06
Frequency: monthly start (MS)
Split: chronological 80/20
Shuffle: false
Transformation: natural_log
Selected regular differencing order: d = 1
E04 handoff: two confirmed ARIMA(p,1,q) candidates with rationale
Test set: sealed until final evaluation
```

The ARIMA fitting input is the natural-log transform of the training **level**
series, with `d=1` supplied to the model. The already log-differenced E03 series
is for stationarity evidence and E04 order identification; do not fit ARIMA with
`d=1` to that pre-differenced series.

Reuse the E01 split exactly. Do not sort, repair, fill, interpolate, resample,
or modify the raw CSV as part of this plan.

## 6. Scientific and Evaluation Parameters

```text
Analysis scale: natural_log
ARIMA d: 1, inherited from E03
Candidate count: 1–2, inherited from E04
Seasonal-naive period: 12
Forecast horizon: 41
Forecast metric scale: original sales scale
Required metrics: MAE, RMSE, MAPE
Residual significance level: 0.05
Residual diagnostics: mean, time plot, ACF, Ljung–Box
```

The inverse transformation from log predictions to original sales scale must be
explicit and consistent across candidates. Record the chosen policy and its
limitations. Do not change this policy after inspecting test metrics.

MAPE is undefined at zero actual values. If any are present, report the issue
explicitly; do not silently remove those observations.

## 7. Files Allowed to Create or Modify

After this plan and the E05 specification are confirmed, work may create or update
only the following, as needed:

```text
docs/exercise_details/exercise_05_arima_forecasting_evaluation.md
docs/plans/exercise_05_before_process.md
notebooks/Practice_2_Exercise.ipynb
outputs/figures/05_arima_residual_diagnostics.png
outputs/figures/05_arima_forecast_comparison.png
outputs/results/05_arima_fit_summary.csv
outputs/results/05_arima_residual_diagnostics.csv
outputs/results/05_arima_forecasts.csv
outputs/results/05_arima_metrics.csv
docs/logs/exercise_05_execution.md
docs/status/current_status.md
```

Reuse existing package owners and interfaces. Do not add a duplicate model,
diagnostic, visualization, or metric module. If reusable code changes are needed,
first identify the confirmed owner and update the file scope with confirmation.

## 8. Files Not to Modify

```text
datasets/raw/a10.csv
datasets/raw/airline-passengers.csv
working_rule.md
AGENTS.md
.agents/rules/ and .agents/workflows/
confirmed Practice_2 rule files
E01–E04 validated source logic, outputs, and execution evidence
historical Practice2_latest.ipynb reference (not present in the current repository)
E06 implementation, outputs, or execution evidence
README.md before the confirmed final-documentation stage
unrelated Practice/Lab files
```

If the work requires modifying an excluded file, changing the E01 split,
changing the dataset or metrics, or expanding architecture/dependencies:

```text
STOP → explain reason and impact → propose scope update → chờ xác nhận
```

## 9. Sequential Execution Steps

### Step 0 — Verify confirmation and Reconcile Existing State

Review the confirmed E05 specification and this plan confirmation state. Confirm the
E04 handoff evidence and the two confirmed ARIMA candidates. The clean-kernel
run is retained as formal evidence, with residual autocorrelation documented as
a limitation.

### Step 1 — Verify the Dataset and E01 Boundary

Use the confirmed data loader and validate the raw dataset contract. Verify:

```text
rows = 204
train observations = 163
test observations = 41
train end = 2005-01
test start = 2005-02
train end < test start
chronological order = true
shuffle = false
```

Keep the raw file immutable. Stop if schema, date range, frequency, missing
values, duplicates, or monthly continuity differ from the contract.

### Step 2 — Verify E03/E04 Handoffs

Reproduce the natural-log and first-difference training transformation through
confirmed reusable logic. Confirm the selected `d=1`, expected 162 transformed
observations, no remaining missing values, and correct timestamp alignment.
Verify that E04 candidates are limited to one or two orders with actual
training-only ACF/PACF rationale.

Do not use E04 candidates from legacy notebook output unless the confirmed E04
handoff confirms them.

### Step 3 — Lock the Model and Evaluation Setup

Before opening test values:

- fix the candidate orders and rationale from E04;
- fix the seasonal-naive period at 12;
- fix the training series and log-scale fit input;
- document the inverse-log policy;
- fix the test horizon and metric definitions.

Do not use test metrics to add, remove, or change candidates.

### Step 4 — Fit Seasonal-Naive Baseline and ARIMA Candidates

Create the seasonal-naive forecast using training data only. Fit each confirmed
ARIMA candidate to log-transformed training levels with its inherited `d=1`.
Record convergence, fitting warnings or failures, AIC, and BIC. Do not silently
discard a warning or failed candidate.

### Step 5 — Inspect Residual Diagnostics

For every fitted ARIMA candidate, inspect and record:

```text
residual mean
residual time plot
residual ACF and confidence level
Ljung–Box statistic, p-value, lag, model_df, and alpha
```

Use statistical evidence together with plots. Do not conclude that residuals are
white noise from the residual mean or visual plot alone. If diagnostics reveal
unresolved structure, stop before asserting a final model and document the issue.

### Step 6 — Forecast and Evaluate

After the setup is locked, evaluate the test set:

- forecast exactly 41 months for each ARIMA candidate and baseline;
- assert forecast index equals the test index;
- transform model forecasts back to the original sales scale using the locked
  policy;
- calculate MAE, RMSE, and MAPE over the same 41 actual/forecast pairs;
- compute absolute error by timestamp and identify its maximum for each model;
- inspect the Train/Test/Forecast figure and metric tables.

Do not use an unaligned forecast, omit test points without an confirmed reason, or
compare metrics computed on different scales or horizons.

### Step 7 — Answer the E05 Questions

Answer all nine questions in the E05 specification using actual outputs:

1. Why no shuffle, and what is the test set for?
2. What do the selected `p`, `d`, and `q` mean?
3. Did each model converge, and were warnings emitted?
4. Do residuals support a white-noise conclusion?
5. What should be investigated if residual autocorrelation remains?
6. Does the forecast follow the test-period behavior?
7. Where is the largest error for each model?
8. Which metric is most sensitive to large errors, and why?
9. What does the observed RMSE mean in target units?

Limit conclusions to Monthly Retail Sales and this holdout. Compare candidates
with the seasonal-naive baseline; do not claim a model is useful solely because
it has a lower AIC/BIC.

### Step 8 — Record Evidence and Update Status

After all checks pass, create `docs/logs/exercise_05_execution.md` with input
identity, split, model parameters, warnings, diagnostics, forecasts, metrics,
largest errors, and validation outcomes. Update `current_status.md` only with
verified state and retain the residual-autocorrelation limitation.

## 10. Test and Validation Plan

```text
[ ] E04 candidate handoff and E05 confirmation state reviewed
[ ] Dataset schema, monthly continuity, and raw immutability verified
[ ] E01 split reproduced exactly as 163/41 with no shuffle
[ ] Test data excluded from order selection and model fitting
[ ] E03 natural-log transform and selected d=1 reproduced
[ ] ARIMA fitted on log(training levels), avoiding double differencing
[ ] One or two candidate orders traceable to E04 evidence
[ ] Seasonal-naive baseline uses lag 12 and training-only history
[ ] Convergence, warnings, AIC, and BIC recorded per candidate
[ ] Residual mean, plot, ACF, and Ljung–Box inspected
[ ] Forecast horizon is 41 and forecast index equals test index
[ ] Inverse transformation is explicit and consistent
[ ] MAE, RMSE, and MAPE use the same original-scale holdout pairs
[ ] Largest-error timestamp is computed from aligned errors
[ ] Candidate comparison includes seasonal-naive baseline
[ ] Notebook runs sequentially from a clean kernel
[ ] Required outputs are inspected against notebook values
[ ] Execution log and status update match verified evidence
[ ] E01–E04 and E06 artifacts remain unchanged
```

## 11. Stop Conditions

Stop and report the issue if:

- E04 handoff, E05 confirmation, or formal E04/E05 status reconciliation is unresolved;
- dataset or E01 split contract fails;
- test leakage is detected;
- the E03 transformation or selected `d` cannot be reproduced;
- candidate rationale is missing or inconsistent with actual E04 evidence;
- a model fails to converge or has unresolved fitting warnings;
- residual diagnostics reveal structure that blocks an evidence-based conclusion;
- forecast timestamps do not align exactly with test timestamps;
- inverse transformation or metric scale is unclear;
- a required file or architecture change is outside this confirmed scope.

When blocked:

```text
STOP
→ document observed and expected behavior
→ explain impact
→ propose the next action
→ chờ xác nhận when required
```

## 12. Risks and Controls

| Risk | Control |
|---|---|
| Treating an exploratory notebook run as formally confirmed | Reconcile confirmation and status records before claiming completion |
| E04 handoff remains formally open | Verify candidate evidence and update status only after review |
| Double differencing the ARIMA input | Fit `ARIMA(log(train levels), order=(p,1,q))` |
| Test leakage during candidate selection | Lock orders and evaluation setup before opening test values |
| Comparing candidates without a baseline | Include seasonal-naive lag-12 forecast |
| Inverse-log scale bias is hidden | Record inverse-transform policy and limitations |
| White noise inferred from plots alone | Include Ljung–Box and report its lags/alpha |
| Forecast/actual timestamps misalign | Assert exact index equality before metrics |
| MAPE undefined for zero actual values | Check target and report undefined cases explicitly |
| Stale notebook outputs presented as current | Run from a clean kernel and inspect refreshed outputs |

## 13. E05 Completion Handoff

E05 is complete only when:

```text
E01–E04 handoffs and confirmation are reconciled
AND confirmed ARIMA candidates and seasonal-naive baseline are evaluated
AND convergence and residual evidence are recorded
AND forecast indices match the 41-observation test horizon
AND MAE/RMSE/MAPE are reproducible on the same original-scale observations
AND all required questions are answered from actual evidence
AND tests and clean-kernel notebook validation pass
AND execution log and status reflect verified state
AND Technical review of the final result
```

## 14. confirmation gate

```text
EXERCISE_05_BEFORE_PROCESS_CREATED=true
EXERCISE_05_BEFORE_PROCESS_REVIEWED=true
EXERCISE_05_BEFORE_PROCESS_CONFIRMED=true
EXERCISE_05_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_05_IMPLEMENTED=true
EXERCISE_05_VALIDATED=true
EXERCISE_05_COMPLETED=true
```
