# Practice 4 — Test comparison and error analysis

H02 run `20261120_system312_h02_01` consumes accepted H01 run `20261120_system312_h01_03`. All five models use the common 5,259-target sample. Metrics are in MW; test ranking is descriptive and did not change model selection.

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
D01 training-only correlations and the G01 validation ablation are the available predictive evidence. Correlation describes association, while ablation compares model performance under different information sets. The validation ablation results remain the basis for the weather contribution claim; H02 weather-regime results below are test-set associations and do not establish causation.

XGBoost validation full RMSE: 508.94 MW; load-only RMSE: 496.16 MW. # D01 — Training-only EDA findings

### 2. When does VAR fail?
VAR has the largest test RMSE among the three learned models in this test window. Review the `load_regime`, `season`, and local calendar rows in `grouped_errors.csv` for larger errors; the grouping is descriptive and not a causal diagnosis. The accepted Phase 6 residual whiteness diagnostic rejected white noise at 5%, so residual dependence remained after fit.

### 3. What does XGBoost learn from weather?
Use the accepted G01 feature gains and validation weather ablation. The load-only ablation is an explicit comparison of weather and load information, while this test uses the locked XGB_full model. Weather proxy bins in H02 describe error association across regimes; they are not a new test-time tuning step.

### 4. Which cycles does LSTM learn?
The G02 residual correlations at exact UTC lags 24 and 168 hours, their pair counts, and local-hour/weekday errors are the evidence. A lag correlation alone does not prove that the network learned a cycle. The local hour plot includes both repeated observations at the DST fall-back transition.

### 5. Is LSTM overfitting?
The answer is based on G02 training and validation loss curves and the restored best epoch, not on test performance. The accepted LSTM findings report early stopping with restored weights; consult those curves alongside the test error profile. Test metrics are not used to modify the model.

### 6. How do ML and DL differ here?
On this held-out window XGBoost ranks ahead of LSTM by RMSE (445.95 vs 458.51 MW) and MAE (283.67 vs 301.80 MW). This describes the locked models on one test period. XGBoost uses engineered lag/statistic features and has feature-gain interpretation; LSTM consumes a 24×4 sequence and has higher training cost and weaker direct interpretability. Neither test result changes validation selection.

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
