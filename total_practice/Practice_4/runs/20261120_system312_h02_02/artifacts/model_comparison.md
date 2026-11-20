# Practice 4 — Test comparison and error analysis

H02 run `20261120_system312_h02_02` consumes accepted H01 run `20261120_system312_h01_03`. All five models use the common 5,259-target sample. Metrics are in MW; test ranking is descriptive and did not change model selection.

## Test metrics

| Model | MAE (MW) | RMSE (MW) | MAPE (%) |
|---|---:|---:|---:|
| persistence | 1045.96 | 1383.86 | 3.6882 |
| seasonal24 | 2531.02 | 3618.58 | 8.7584 |
| VAR | 477.26 | 681.53 | 1.6857 |
| XGB | 283.67 | 445.95 | 0.9888 |
| LSTM | 301.80 | 458.51 | 1.0551 |

RMSE order: XGB → LSTM → VAR → persistence → seasonal24.

## Analysis questions

### 1. Which weather variable has the strongest relationship with load?
For linear association in observed training data, humidity is strongest by absolute Pearson correlation (r = -0.367), compared with temperature (r = 0.236) and wind (r = 0.209). This is association, not causation or proof of strongest nonlinear predictive value. In G01, temperature has the largest weather feature-gain total, while the validation load-only ablation actually beats full XGB by 12.77 MW RMSE; weather therefore did not improve that selected comparison.

G01 validation full RMSE: 508.94 MW; load-only RMSE: 496.16 MW. Test weather strata are descriptive associations only. See [D01 findings](eda_findings.md).

### 2. When does VAR fail?
VAR has the largest test RMSE among the three learned models. The grouped table reports exact MAE/RMSE by target hour, weekday, season, month, train-defined load regime, and independent weather regimes; inspect the largest VAR RMSE rows there. The accepted Phase 6 residual whiteness test rejected white noise at 5%, indicating remaining residual dependence. Group differences are descriptive and do not establish why errors occur.

### 3. What does XGBoost learn from weather?
G01 gain totals were 22.64 million for temperature, 16.03 million for humidity, and 12.08 million for wind, versus 1,556.96 million for load. These gains are affected by correlated inputs and are not causal importance. Its validation full model was 12.77 MW RMSE worse than load-only, so weather's incremental benefit was not demonstrated in this comparison. H02 weather bins show only test-period error associations.

### 4. Which cycles does LSTM learn?
Evidence supports a daily pattern more clearly than a weekly one. G02 validation residual correlation was 0.2416 at UTC lag 24 and 0.0958 at lag 168 (5,231 and 5,087 pairs). On test these were 0.2449 and 0.1301 (5,235 and 5,091 pairs). Local-hour and weekday errors are in `grouped_errors.csv`; neither correlation proves a learned cycle, and a 24-hour input has no direct lag-168 observation. Local-hour grouping retains both repeated DST fall-back hours.

### 5. Is LSTM overfitting?
The selected trial's best validation epoch was 47 and it stopped at epoch 50. From epoch 47 to 50, training loss stayed near 0.0091 while validation loss rose from 0.012380 to 0.013902; restoring epoch 47 was appropriate. The train/validation inference MSE gap was 0.001648. This is evidence of late overfit pressure, not proof of broad generalization failure; validation also served early stopping and selection.

### 6. How do ML and DL differ here?
On this held-out window XGBoost ranks ahead of LSTM by RMSE (445.95 vs 458.51 MW) and MAE (283.67 vs 301.80 MW). Validation had selected LSTM across the five candidates, illustrating that the single test-period ranking differs; test results do not alter selection. XGBoost uses engineered lag/statistic features and has feature-gain interpretation; LSTM consumes a 24×4 sequence and had 30,113 trainable parameters. G01's 18 CPU trials used 46.5 fit seconds versus 425.1 seconds for G02's two CPU trials. Neither model is causal, and the LSTM is less directly interpretable.

## Temporal error notes

The five dates with highest daily RMSE for at least one model are:
- seasonal24, 2018-10-01: RMSE 9683.55 MW across 24 scored targets.
- seasonal24, 2018-06-02: RMSE 9637.52 MW across 24 scored targets.
- seasonal24, 2018-10-07: RMSE 9459.80 MW across 24 scored targets.
- seasonal24, 2018-07-02: RMSE 8483.47 MW across 24 scored targets.
- seasonal24, 2018-08-04: RMSE 7430.75 MW across 24 scored targets.

Exact UTC residual autocorrelation:

| Model | Lag 24 pairs / correlation | Lag 168 pairs / correlation |
|---|---:|---:|
| persistence | 5235 / 0.8147 | 5091 / 0.7675 |
| seasonal24 | 5235 / -0.2847 | 5091 / 0.1162 |
| VAR | 5235 / 0.2621 | 5091 / 0.2265 |
| XGB | 5235 / 0.1428 | 5091 / 0.0659 |
| LSTM | 5235 / 0.2449 | 5091 / 0.1301 |

## Grouped analysis and limitations

`grouped_errors.csv` reports count, bias, MAE, RMSE, and MAPE for local hour, weekday, month, season, train-defined load regime, and independent train-defined weather proxy regimes. Sparse bins remain visible. Load groups use scored raw target load and are retrospective. Weather groups use origin-hour weather from the H01 sidecar. No canonical test rows were reopened.

The test window is a single held-out segment from late May through December 2018. Weather proxy data are a five-city unweighted mean with known representativeness limits. One-step walk-forward reveals each observed truth after scoring under the lab availability assumption; production availability may differ.
