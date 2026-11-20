# F02 VAR Results

Run `20261118_system312_f02_02` - F02, VAR(24) model lock SHA256 `0b3820731f3369f57699adaa64a7b1f4a5cbbf659c48331fc5721335572d3e26` and Phase 6 **APPROVED / COMPLETED** by Human on 2026-11-18 via Director review. The F02 manifest retains the run-time report hash from before this approval edit.

Human accepted the artifact as-is. Feature order and scaler hash are not directly embedded in it. The model config hash identifies the F02 config, and the F02 manifest separately records the upstream scaler hash.

## Stationarity

| Variable | ADF statistic | ADF p | KPSS statistic | KPSS p | d |
|---|---:|---:|---:|---:|---:|
| load | -16.2646 | 3.53765e-29 | 0.330654 | 0.1 | 0 |
| temperature | -3.01867 | 0.0331874 | 23.5349 | 0.01 | 0 |
| humidity | -4.24287 | 0.000557042 | 20.6042 | 0.01 | 0 |
| wind_speed | -7.8864 | 4.55744e-12 | 1.09045 | 0.01 | 0 |

KPSS p-values at 0.01 or 0.1 are table bounds. Human selected d=0 using ADF and identified annual weather seasonal drift as a possible explanation of KPSS rejection. These diagnostics alone do not establish the cause. The 9,271-hour block excludes 15,241 earlier observed hours and may not represent earlier regimes.

## Lag selection

| p | BIC |
|---:|---:|
| 1 | -10.94712173 |
| 2 | -12.52501842 |
| 3 | -12.63225953 |
| 4 | -12.71488182 |
| 5 | -12.77661635 |
| 6 | -12.80851819 |
| 7 | -12.85871937 |
| 8 | -12.87684713 |
| 9 | -12.89315432 |
| 10 | -12.98084329 |
| 11 | -13.01487355 |
| 12 | -13.08909620 |
| 13 | -13.21248020 |
| 14 | -13.22203438 |
| 15 | -13.23381369 |
| 16 | -13.30139466 |
| 17 | -13.30243217 |
| 18 | -13.30470113 |
| 19 | -13.33482180 |
| 20 | -13.35756860 |
| 21 | -13.38049997 |
| 22 | -13.38780022 |
| 23 | -13.38072536 |
| 24 | -13.45849879 |

Selected VAR(24), complexity 398, model SHA256 `0b3820731f3369f57699adaa64a7b1f4a5cbbf659c48331fc5721335572d3e26`. Maximum companion eigenvalue modulus 0.9991374249.
Adjusted Portmanteau lag 48 statistic 4297.18, df 384, p-value 0, reject at 5% True.

## Validation metrics

| Model | MAE MW | RMSE MW | MAPE % |
|---|---:|---:|---:|
| persistence | 1115.634012 | 1507.303309 | 3.911556 |
| seasonal24 | 2429.289138 | 3507.532671 | 8.433175 |
| VAR | 514.619863 | 799.962062 | 1.816565 |

All models use 5,257 eligible validation targets. Two missing truths and zero invalid contexts are excluded. Fixed train scaler and coefficients are used throughout.
