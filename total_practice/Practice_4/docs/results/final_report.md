# Practice 4 — Final report

## Objective and data

Forecast Spanish hourly electricity demand one hour ahead from lagged demand and weather proxies. The canonical dataset spans 2014–2018; records are kept on a UTC hourly index. Weather predictors are unweighted means across five cities and are proxies for the load region.

## Method

The project used chronological train, validation and held-out test partitions. Preprocessing, features, model configurations and model selection were fixed from training/validation evidence before test evaluation. The final walk-forward scored five locked models on the same 5,259 observed targets over 5,261 test candidates. Each forecast was issued before the next observed truth was revealed. Two missing target truths were excluded; there were no input-invalid exclusions.

Candidate models were persistence, seasonal-24, VAR(24), XGB_full and a 24×4 LSTM. Validation selected the LSTM across the five candidates. No test results were used to tune or refit a model.

## Results

| Model | MAE (MW) | RMSE (MW) | MAPE (%) |
|---|---:|---:|---:|
| XGBoost | 283.67 | 445.95 | 0.9888 |
| LSTM | 301.80 | 458.51 | 1.0551 |
| VAR(24) | 477.26 | 681.53 | 1.6857 |
| Persistence | 1,045.96 | 1,383.86 | 3.6882 |
| Seasonal-24 | 2,531.02 | 3,618.58 | 8.7584 |

XGBoost ranks first on this test interval, while LSTM had been selected on validation. The test ranking is descriptive and does not replace the validation decision. See [full metrics and diagnostics](model_comparison.md).

## Findings

Training Pearson association was strongest by absolute value for humidity (r = −0.367); temperature had the largest XGBoost weather feature-gain total. The G01 validation ablation did not show a gain from weather: full XGBoost RMSE was 508.94 MW versus 496.16 MW for load-only. These statistics describe association, not causality.

LSTM residual correlations suggest daily dependence more clearly than weekly dependence (test lag-24 r = 0.2449; lag-168 r = 0.1301). The selected LSTM's validation loss reached its best at epoch 47 and rose through stop epoch 50 while training loss remained near 0.0091, supporting restore-best-weights early stopping.

## Limitations

The test window covers only late May through December 2018. Weather is a five-city proxy. The one-step protocol assumes each newly observed load is available for the next forecast. Results do not establish causal weather effects or year-round performance.

## Reproducible evidence

- H01 run: `20261120_system312_h01_03`; manifest binds predictions, eligibility, diagnostic context and evaluation protocol.
- H02 run: `20261120_system312_h02_02`; grouped scores and three figures are under its `artifacts/` directory.
- Presentation: `notebooks/practice_4_end_to_end.ipynb`; reads the official outputs and H02 grouped table without loading raw data or fitting models.
- Runtime: dedicated Python 3.12.10 environment from `requirements.lock.txt`; `pip check` passed.
