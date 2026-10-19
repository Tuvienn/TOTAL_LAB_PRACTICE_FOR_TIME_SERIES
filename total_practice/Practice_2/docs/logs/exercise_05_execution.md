# EXERCISE 05 — ARIMA EXECUTION EVIDENCE LOG

## Record Status

```text
record type: retrospective record of persisted notebook output
execution owner: Human-reported notebook run
execution timestamp: not available in the persisted evidence reviewed
assistant rerun in this documentation task: no
formal E05 completion: not established
upstream E04 handoff/status reconciliation: pending
```

This log records the E05 results available in
`notebooks/Practice_2_present.ipynb`. It does not claim clean-kernel
reproducibility or formal approval. The E05 specification and before-process plan
remain drafts, and `docs/status/current_status.md` continues to record the E04
handoff discrepancy.

## Scope and Setup

```text
dataset: Monthly Retail Sales (a10.csv)
observations: 204
train: 163 observations, 1991-07 through 2005-01
test: 41 observations, 2005-02 through 2008-06
split: chronological 80/20; no shuffle
model fitting input: natural_log of training levels
ARIMA differencing order: d = 1
forecast evaluation scale: original sales scale
```

The persisted E01 split evidence gives the boundary above. The notebook results
show two fitted candidates, ARIMA(1,1,1) and ARIMA(2,1,1), and a seasonal-naive
baseline with period 12. The E04 candidate table available in the same notebook
contains three provisional candidates, while the E04 specification allows one
or two. This upstream inconsistency remains unresolved.

## Fit Results

| Model | Converged | AIC | BIC | Captured warnings |
|---|---|---:|---:|---|
| ARIMA(1,1,1) | Yes | -131.048881 | -121.786092 | None recorded |
| ARIMA(2,1,1) | Yes | -129.532608 | -117.182223 | None recorded |

Among these two fits, ARIMA(1,1,1) has lower AIC and BIC. This fit criterion
alone does not establish that it is the better forecasting model.

## Residual Diagnostics

| Model | Residual mean | Ljung–Box p-value, lag 12 | Ljung–Box p-value, lag 24 |
|---|---:|---:|---:|
| ARIMA(1,1,1) | 0.044193 | 5.969958e-14 | 1.216551e-20 |
| ARIMA(2,1,1) | 0.044555 | 2.961168e-14 | 1.118366e-20 |

At the 0.05 significance level, both models' Ljung–Box results reject the
no-autocorrelation null at lags 12 and 24. Residual means near zero do not
override this evidence; neither model's residuals are supported as white noise
at the tested lags.

## Forecast Evaluation

Metrics are reported on the original sales scale for the 41-observation test
horizon:

| Model | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| ARIMA(1,1,1) | 3.833290 | 4.865821 | 18.493973% |
| ARIMA(2,1,1) | 3.806130 | 4.834506 | 18.357607% |
| Seasonal naive (12) | 4.256436 | 5.186466 | 20.097262% |

Both ARIMA candidates have lower recorded test metrics than the seasonal-naive
baseline in this holdout. ARIMA(2,1,1) has slightly lower MAE, RMSE, and MAPE;
ARIMA(1,1,1) has lower AIC and BIC. The multi-step forecasts tend toward a
near-flat level and do not follow the test-period increase and seasonal peaks
well.

Largest absolute error recorded for each ARIMA candidate:

| Model | Timestamp | Actual | Forecast | Absolute error |
|---|---|---:|---:|---:|
| ARIMA(1,1,1) | 2008-01-01 | 29.665356 | 17.032661 | 12.632695 |
| ARIMA(2,1,1) | 2008-01-01 | 29.665356 | 17.073772 | 12.591584 |

## Outputs and Validation

Fit, diagnostics, metrics, and largest-error tables are available as persisted
notebook cell outputs. At the time of this record, dedicated E05 result CSVs and
exported E05 figures were not present in `outputs/results/` or
`outputs/figures/`.

```text
relevant persisted notebook cells: recorded as executed successfully
clean-kernel notebook execution: not verified
forecast/test index equality: not independently reproduced in this task
targeted E05 tests: not run
E04 candidate handoff reconciled: no
formal approval and current-status reconciliation: pending
```

## Decision and Limitations

The saved outputs support a limited comparison on this particular holdout: both
ARIMA models outperform the seasonal-naive baseline on the listed metrics, but
both retain significant residual autocorrelation at lags 12 and 24. The slightly
better test metrics of ARIMA(2,1,1) do not remove the need to resolve the
candidate handoff and residual limitations.

This is a record of notebook evidence, not a formal completion claim. Do not
update E05 to completed until the upstream E04 discrepancy, approval records,
validation, and current status have been reconciled.
