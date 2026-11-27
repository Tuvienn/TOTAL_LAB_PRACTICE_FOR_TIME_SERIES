# Exercise 05 — Execution Evidence

## Run context

- Source: `notebooks/Practice_2_Exercise.ipynb`
- Fit scale: log training levels
- Regular differencing order: `d=1`
- Train/test: `163/41`
- Forecast horizon: `41` months
- Baseline: seasonal-naive with period `12`
- Status: confirmed and validated with residual-autocorrelation limitation

## Candidate fit and diagnostics

All candidates converged. Lower AIC/BIC alone was not used as the final model
decision. Ljung–Box rejected the white-noise null at lags 12 and 24 for every
candidate in this run, so residual dependence remains to be discussed.

| Model | AIC | BIC | Ljung–Box p(12) | Ljung–Box p(24) |
|---|---:|---:|---:|---:|
| ARIMA(1,1,1) | -131.049 | -121.786 | <0.001 | <0.001 |
| ARIMA(1,1,0) | -109.330 | -103.154 | <0.001 | <0.001 |
| ARIMA(0,1,1) | -120.448 | -114.273 | <0.001 | <0.001 |

## Holdout metrics

Metrics are calculated on the original sales scale over the same 41-month test
horizon.

| Model | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| ARIMA(1,1,1) | 3.833 | 4.866 | 18.494% |
| ARIMA(1,1,0) | 3.567 | 4.214 | 20.066% |
| ARIMA(0,1,1) | 3.466 | 4.177 | 18.170% |
| Seasonal naive (s=12) | 4.256 | 5.186 | 20.097% |

The ARIMA(0,1,1) candidate outperformed the baseline on this holdout, but the
remaining Ljung–Box signal prevents an unconditional white-noise conclusion.
E05 is formally completed with this residual-autocorrelation limitation recorded.

## Output

- `outputs/figures/05_forecast_comparison_log_d1.png`
- `outputs/figures/05_residual_diagnostics_log_d1.png`
- `outputs/results/Model_Summary_Prac2_Exercise.txt`
