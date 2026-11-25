# EXERCISE 05 — ARIMA TRAINING, DIAGNOSTICS, FORECASTING AND EVALUATION

## 1. Exercise Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_05
Topic: ARIMA Training, Residual Diagnostics, Forecasting and Evaluation
Dataset: Monthly Retail Sales
Input: E01 chronological holdout + E04 provisional ARIMA candidates
Inherited transformation: natural_log
Inherited regular differencing order: d = 1
Specification status: CONFIRMED_AND_VALIDATED
Implementation authorized: YES
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_05_execution.md
```

This specification defines E05's scientific and reporting contract. It does not
authorize implementation, notebook edits, model fitting, output creation, or an
E05 completion status until the specification and applicable execution scope have
been confirmed.

## 2. Objective

- fit one or two ARIMA candidates handed off by E04;
- compare candidates using training-fit evidence, convergence, residual diagnostics,
  and out-of-sample evaluation;
- compare ARIMA forecasts with an confirmed seasonal-naive baseline;
- preserve the E01 chronological train/test boundary;
- report MAE, RMSE, and MAPE on the original sales scale;
- identify the largest absolute forecast error for each evaluated model;
- make a final assessment limited to the observed holdout and evidence.

E05 is the core ARIMA exercise. SARIMA on AirPassengers belongs to the separate
advanced E06 exercise and must not be added to this E05 scope.

## 3. Upstream Dependencies

```text
E01: validated Monthly Retail Sales + chronological train/test boundary
E02: original-training ADF evidence
E03: natural-log transformation + selected d = 1 + stationarity evidence
E04: ACF/PACF evidence + 1–2 provisional ARIMA candidates
E05: fit + residual diagnostics + forecast + evaluation
```

E05 may proceed only when the upstream handoffs and their evidence are verified.
The current status record and confirmation records must be reconciled before E05 is
formally treated as started or completed.

## 4. Input Contract

```text
Source: datasets/raw/a10.csv
Dataset identity: Monthly Retail Sales
Timestamp column: date
Target column: value
Frequency: monthly start (MS)
Expected total observations: 204
Expected training observations: 163
Expected test observations: 41
Expected training period: 1991-07 through 2005-01
Expected test period: 2005-02 through 2008-06
Chronological ordering: required
Shuffle: prohibited
Duplicate timestamps: 0
Missing target values: 0
Missing monthly intervals: 0
```

```text
Analysis scale: natural_log
ARIMA regular differencing order: d = 1
Model-fit input: log(training level series)
Order-identification input: E03 log-first-differenced training series
Forecast metric scale: original sales scale
```

ARIMA must be fit to the log-transformed training **level** series with `d=1`.
Do not pass the already differenced E03 series to an ARIMA model with `d=1`, as
that would apply differencing twice. The E03 differenced series is used for
stationarity evidence and E04 order identification.

The test set remains sealed for E02–E04, scale decisions, candidate selection,
and model fitting. It may be used only after candidates and the evaluation
protocol have been fixed, for final forecast evaluation.

## 5. Required Steps

1. Verify E01–E04 completion evidence and current confirmation/status state.
2. Load the validated Monthly Retail Sales series without changing the raw file.
3. Reproduce and verify the E01 chronological 163/41 train/test split.
4. Confirm that E02–E04 did not use test observations.
5. Verify the E03 natural-log transformation and selected `d = 1`.
6. Verify one or two provisional ARIMA candidates and their rationale from E04.
7. Create a seasonal-naive baseline with seasonal lag 12 using training data.
8. Fit each confirmed ARIMA candidate on log-transformed training levels.
9. Record convergence, fitting warnings, AIC, and BIC for each candidate.
10. Inspect residual mean, residual time plot, residual ACF, and Ljung–Box results.
11. Lock the candidate/evaluation setup before opening test values.
12. Forecast exactly 41 monthly observations for every candidate and baseline.
13. Verify forecast timestamps match the test index exactly.
14. Invert the log transformation using the confirmed, explicitly recorded policy.
15. Compute MAE, RMSE, and MAPE on the same original-scale test observations.
16. Compare all candidates against each other and the seasonal-naive baseline.
17. Compute the largest absolute error timestamp and value for each candidate.
18. Answer the required interpretation questions from actual outputs.
19. Record execution evidence and update current status only after validation.

## 6. Scientific Method

### 6.1 Chronological Split and Holdout Protection

```text
Split method: chronological 80/20
Train observations: 163
Test observations: 41
Shuffle: NO
Model identification data: training only
Model fitting data: training only
Forecast horizon: exactly 41 monthly observations
Test usage: final evaluation only
```

Do not recompute a different split in E05. Reuse the E01 boundary. Any test
information used for transformation, order selection, or candidate changes
invalidates the evaluation and requires a new confirmed procedure.

### 6.2 Candidate Models

- Use one or two candidates supplied by the E04 handoff.
- Preserve each candidate's stated rationale and inherited `d = 1`.
- Do not add candidates based on test metrics.
- Do not select a final model solely from AIC/BIC.
- Record any convergence failure or warning explicitly; do not present an
  unsuccessful fit as a valid result.

### 6.3 Seasonal-Naive Baseline

Use a seasonal-naive baseline with seasonal lag 12, generated from the training
series and extended to the same 41-month horizon. Evaluate it on the same test
timestamps and original target scale as the ARIMA candidates.

### 6.4 Residual Diagnostics

For each fitted ARIMA candidate, record:

```text
residual mean
residual time plot
residual ACF
Ljung–Box test statistic and p-value
Ljung–Box lag(s), model degrees of freedom, and significance level
```

Use `alpha = 0.05` for Ljung–Box unless a separately confirmed protocol specifies
otherwise. Choose statistically valid lags and record them. A residual mean near
zero or visual inspection alone is not sufficient to claim white noise.

### 6.5 Forecast Inverse Transformation

Models are fitted on the natural-log scale, but required metrics are reported on
the original sales scale. The inverse-transform method must be explicit and
consistent for every candidate. Record whether exponentiating the predicted log
mean is used and state its interpretation/limitations; do not silently apply a
bias correction or change inverse-transform policy after viewing test metrics.

### 6.6 Evaluation Metrics

Compute the required metrics using identical actual/forecast index pairs:

```text
MAE  = mean absolute error
RMSE = square root of mean squared error
MAPE = mean absolute percentage error × 100
```

The target values are expected to be positive. If any actual value is zero, MAPE
is undefined for that observation and the issue must be explicitly reported; do
not silently drop observations.

## 7. Required Interpretation Questions

Answer all questions from execution evidence:

1. Why must the time series not be shuffled, and what is the test set for?
2. What do the selected `p`, `d`, and `q` represent?
3. Did each model converge? Were fitting warnings emitted?
4. Do residuals show evidence of white noise? What do residual ACF and
   Ljung–Box indicate?
5. If residual autocorrelation remains, what model change should be investigated?
6. Does the forecast follow the observed test-period behavior?
7. At which timestamp does each model have its largest absolute error?
8. Which metric is most sensitive to large errors/outliers, and why?
9. What does the observed RMSE indicate in the target's units?

Distinguish evidence from interpretation. Do not claim forecast quality beyond
the tested dataset and holdout period.

## 8. Expected Outputs

```text
outputs/figures/05_arima_residual_diagnostics.png
outputs/figures/05_arima_forecast_comparison.png
outputs/results/05_arima_fit_summary.csv
outputs/results/05_arima_residual_diagnostics.csv
outputs/results/05_arima_forecasts.csv
outputs/results/05_arima_metrics.csv
docs/logs/exercise_05_execution.md
docs/status/current_status.md
```

Exact filenames may be aligned with existing confirmed outputs during planning;
do not overwrite E01–E04 evidence. Machine-readable forecast output must retain
model name, timestamp, actual value, forecast, and error so the largest-error
claim is reproducible.

## 9. Validation Criteria

```text
[ ] E01–E04 handoffs and confirmation/status state verified
[ ] Raw input remains unchanged
[ ] Split matches E01: 163 train / 41 test, chronological, no shuffle
[ ] Test observations excluded from E02–E04 and all fitting/model selection
[ ] E03 natural-log transformation and d=1 are inherited correctly
[ ] ARIMA fit uses log(training levels), not an already differenced series with d=1
[ ] One or two candidates have traceable E04 rationale
[ ] Seasonal-naive baseline uses lag 12 and training-only history
[ ] Convergence, warnings, AIC, and BIC are recorded
[ ] Residual mean, time plot, ACF, and Ljung–Box are inspected
[ ] Evaluation setup is locked before opening test values
[ ] Each forecast has exactly 41 observations
[ ] Forecast indices equal the test index
[ ] Inverse-log policy is explicit and consistent
[ ] MAE, RMSE, and MAPE use the same original-scale test observations
[ ] Candidates are compared with the seasonal-naive baseline
[ ] Largest-error timestamp is computed, not estimated visually
[ ] All required questions are answered from actual evidence
[ ] Notebook runs sequentially from a clean kernel
[ ] Outputs are inspected and execution evidence is recorded
```

## 10. Stop Conditions

Stop E05 if:

- E04 handoff or its candidate rationale is missing or unresolved;
- the E01 boundary cannot be reproduced;
- any test observation influenced fitting or candidate selection;
- the model input scale or differencing contract is ambiguous;
- an ARIMA candidate does not converge or has an unresolved fitting warning;
- residual diagnostics or forecast/test alignment cannot be reproduced;
- actual and forecast indices differ;
- a metric is computed on mismatched observations or scales;
- completing E05 requires an unconfirmed dependency, architecture, or scope change.

When blocked:

```text
STOP
→ record observed evidence and expected behavior
→ explain impact
→ propose the next action
→ chờ xác nhận where required
```

## 11. Completion Condition

```text
upstream handoffs verified
AND chronological holdout preserved
AND confirmed ARIMA candidates and seasonal-naive baseline fitted
AND convergence and residual evidence recorded
AND forecasts aligned to the 41-observation test horizon
AND MAE/RMSE/MAPE computed on the same original-scale observations
AND candidate/baseline comparison and all questions answered
AND outputs inspected and reproducible
AND execution log and current status updated
AND no unresolved blocking issue
```

## 12. confirmation gate

```text
EXERCISE_05_SPECIFICATION_CREATED=true
EXERCISE_05_SPECIFICATION_REVIEWED=true
EXERCISE_05_SPECIFICATION_CONFIRMED=true
EXERCISE_05_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_05_IMPLEMENTED=true
EXERCISE_05_VALIDATED=true
EXERCISE_05_COMPLETED=true
```
