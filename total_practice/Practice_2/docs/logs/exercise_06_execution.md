# E06 execution evidence

- Run ID: `2026-11-27_e06_113951`
- Train/test boundary: 115 / 29 monthly observations
- Raw SHA-256: `8cb51be753a718d9be5d76d7e238cc224792754676adc21faa59e954b0201621`
- Selected differencing: d=1, D=1, s=12
- Models: ARIMA(0,1,1) and SARIMA(0,1,1)(0,1,1,12)
- Raw runtime log: `runs/2026-11-27_e06_113951/Practice_2_Advanced.log`
- Forecast horizon: 29 monthly observations; forecast index aligned with test index

## Artifact paths
- Validation: `outputs/results/06_airpassengers_validation.csv`
- Split: `outputs/results/06_airpassengers_split.csv`
- ADF: `outputs/results/06_airpassengers_adf_results.csv`
- Candidates: `outputs/results/06_airpassengers_model_candidates.csv`
- Diagnostics: `outputs/results/06_airpassengers_model_diagnostics.csv`
- Forecasts: `outputs/results/06_airpassengers_forecasts.csv`
- Metrics: `outputs/results/06_airpassengers_metrics.csv`

## Holdout metrics
```text
                  Model       MAE       RMSE                             Status
           ARIMA(0,1,1) 88.420620 101.104982 Sealed 29-month holdout evaluation
SARIMA(0,1,1)(0,1,1,12) 24.059215  30.580049 Sealed 29-month holdout evaluation
```

## Ljung–Box diagnostics
```text
                  Model  Lag  Ljung-Box statistic      p-value                   Interpretation
           ARIMA(0,1,1)   12            74.201835 5.198989e-11 Autocorrelation evidence remains
           ARIMA(0,1,1)   24           131.904481 7.004943e-17 Autocorrelation evidence remains
SARIMA(0,1,1)(0,1,1,12)   12            17.845024 1.204778e-01     No rejection at selected lag
SARIMA(0,1,1)(0,1,1,12)   24            26.456472 3.304174e-01     No rejection at selected lag
```
