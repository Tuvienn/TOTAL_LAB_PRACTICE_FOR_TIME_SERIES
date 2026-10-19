# EXERCISE 06 — EXPLORATORY EXECUTION EVIDENCE LOG

## Record Status

```text
record type: exploratory record of persisted notebook output
execution source: Human-run cells based on a chat-provided template
execution timestamp: not available in the persisted evidence reviewed
assistant rerun in this documentation task: no
E06 implementation authorization: false
E06 validation status: not validated
E06 completion status: not completed
```

This file records preliminary notebook evidence for AirPassengers. It is not an
approved execution log or a completion record. E06 approval is pending, and the
current process gate also records E05 as not formally completed. The E06
specification and before-process plan remain drafts.

## Scope and Setup

```text
dataset: airline-passengers.csv (AirPassengers)
observations: 144 monthly values
period: 1949-01 through 1960-12
train: 115 observations, 1949-01 through 1958-07
test: 29 observations, 1958-08 through 1960-12
split: chronological 80/20; no shuffle
analysis scale: natural_log
seasonal period: s = 12
forecast metric scale: passenger counts
```

The series plot shows a rising level and annual seasonality; seasonal amplitude
increases with the level. The exploratory run used a natural-log scale.

## ADF and Differencing Evidence

ADF was applied to the training data on the log scale with `alpha = 0.05`:

| Training series | Input observations | ADF statistic | p-value | Used lag | ADF observations | Decision |
|---|---:|---:|---:|---:|---:|---|
| Original log series | 115 | -1.574027 | 0.496626 | 13 | 101 | Fail to reject H0 |
| Regular difference, d=1 | 114 | -2.635851 | 0.085812 | 12 | 101 | Fail to reject H0 |
| Seasonal difference, D=1, s=12 | 103 | -1.991013 | 0.290527 | 12 | 90 | Fail to reject H0 |
| Combined d=1 and D=1, s=12 | 102 | -3.946340 | 0.001719 | 11 | 90 | Reject H0 |

Only the combined regular and seasonal difference rejects the ADF unit-root
null among these saved tests. The exploratory run therefore used `d=1`, `D=1`,
and `s=12`.

## ACF/PACF and Fitted Orders

Significant lags recorded for the combined-difference training series:

| Diagnostic | Significant lags and correlations |
|---|---|
| ACF | 1: -0.320677; 3: -0.232934; 12: -0.429978 |
| PACF | 1: -0.320677; 3: -0.223399; 12: -0.383332; 23: 0.195020; 36: -0.195495 |

At seasonal reference lags, ACF lag 12 was significant while lags 24 and 36
were not. PACF lag 12 and lag 36 were significant in the stored table; lag 24
was not. The plots do not establish a unique cutoff, so the orders below are
the candidates used in this exploratory run, not uniquely determined orders:

```text
ARIMA baseline: (1,1,1)
SARIMA: (1,1,1)(0,1,1,12)
```

## Fit and Residual Results

Both fits converged; no fitting warnings were recorded:

| Model | Order | Seasonal order | AIC | BIC |
|---|---|---|---:|---:|
| ARIMA | (1,1,1) | — | -197.221464 | -189.012869 |
| SARIMA | (1,1,1) | (0,1,1,12) | -369.862160 | -359.362269 |

Ljung–Box results:

| Model | p-value at lag 12 | p-value at lag 24 | Interpretation at alpha 0.05 |
|---|---:|---:|---|
| ARIMA | 0.999957 | 1.000000 | Fail to reject no-autocorrelation null at these tested lags |
| SARIMA | 0.010010 | 0.408396 | Reject at lag 12; fail to reject at lag 24 |

The saved results indicate remaining autocorrelation in SARIMA residuals at lag
12. Residual mean was not recorded in the inspected table, so no residual-mean
claim is made here.

## Forecast Evaluation

Recorded MAE and RMSE on the same 29-month test period, in passenger-count
units:

| Model | MAE | RMSE |
|---|---:|---:|
| ARIMA(1,1,1) | 84.254386 | 96.327568 |
| SARIMA(1,1,1)(0,1,1,12) | 12.165113 | 14.917604 |

Largest absolute errors recorded:

| Model | Timestamp | Actual | Forecast | Absolute error |
|---|---|---:|---:|---:|
| ARIMA | 1958-11-01 | 310 | 496.108123 | 186.108123 |
| SARIMA | 1960-03-01 | 419 | 452.003028 | 33.003028 |

On this exploratory holdout, SARIMA has lower recorded MAE and RMSE than ARIMA.
This comparison is limited to the stored run and does not establish performance
outside this split. SARIMA also retains the lag-12 residual limitation noted
above.

## Outputs and Validation

The inspected plots and result tables are persisted as notebook cell outputs.
At the time of this record, dedicated E06 result CSVs and exported E06 figures
were not present in `outputs/results/` or `outputs/figures/`.

```text
raw data contract/checksum: not revalidated for this exploratory record
forecast/test index equality: not independently reproduced in this task
targeted E06 tests: not run
clean-kernel notebook execution: not run
E05 formal completion gate: not satisfied in current status
E06 approval gate: pending
E06 validation/completion: not established
```

## Exploratory Conclusion

The saved holdout metrics favor SARIMA over the ARIMA baseline for this run, but
SARIMA residuals still show autocorrelation at lag 12. Treat the result as
exploratory evidence only. Further formal E06 work requires E05 gate
reconciliation, Human approval, reproducible validation, and inspection of
outputs against a clean execution.
