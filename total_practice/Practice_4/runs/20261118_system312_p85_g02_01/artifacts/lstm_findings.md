# G02 LSTM findings

Run `20261118_system312_p85_g02_01`. **PENDING HUMAN REVIEW**.

## Trials

| Trial | Best epoch | Stop epoch | CPU fit seconds | MAE MW | RMSE MW | MAPE % |
|---|---:|---:|---:|---:|---:|---:|
| lstm_lr_001 | 47 | 50 | 223.54 | 320.692 | 504.751 | 1.1309 |
| lstm_lr_0005 | 50 | 50 | 223.07 | 341.066 | 535.976 | 1.1932 |

C02 selected **lstm_lr_001**. Both trials used seed 42, chronological batches of 64 and validation-only early stopping.

## Q4. Daily and weekly patterns

[Validation trace](../../runs/20261118_system312_p85_g02_01/artifacts/validation_trace.png) and [Madrid group errors](../../runs/20261118_system312_p85_g02_01/artifacts/temporal_errors.png) retain UTC alignment. Repeated local DST hours contribute as separate observations. Residuals are observed minus forecast.

| UTC lag (hours) | Available pairs | LSTM | Persistence | Seasonal24 |
|---:|---:|---:|---:|---:|
| 24 | 5231 | 0.2416 | 0.8168 | -0.1848 |
| 168 | 5087 | 0.0958 | 0.7579 | 0.1747 |

By hour, D01 training means range from 22,635 MW (04:00) to 32,007 MW (13:00). LSTM validation MAE ranges from 144.7 MW (03:00, n=219) to 924.5 MW (00:00, n=219).
By weekday, D01 training means range from 26,307 MW (Sunday) to 29,506 MW (Wednesday). LSTM validation MAE ranges from 302.6 MW (Saturday, n=764) to 356.9 MW (Sunday, n=744).

Daily error variation and the matched baselines describe how predictive accuracy changes across the day. Weekly learning is inconclusive from group errors and residual correlations. The 24-hour input contains no direct lag-168 observation.

## Q5. Overfitting

[Learning curves](../../runs/20261118_system312_p85_g02_01/artifacts/learning_curves.png) show per-epoch train and validation scaled MSE. The selected trial ran 3 epochs after its earliest best validation epoch. Inference MSE with restored weights is 0.010732 (train) and 0.012380 (validation), a gap of +0.001648. The gap reflects generalization across these chronological periods. Using the same validation set for stopping and trial selection can make reported performance optimistic.

## Q6. ML versus DL

| Model | MAE MW | RMSE MW | MAPE % |
|---|---:|---:|---:|
| persistence | 1115.634 | 1507.303 | 3.9116 |
| seasonal24 | 2429.289 | 3507.533 | 8.4332 |
| VAR(24) | 514.620 | 799.962 | 1.8166 |
| XGB_full | 300.186 | 508.939 | 1.0523 |
| LSTM | 320.692 | 504.751 | 1.1309 |

C02 cross-model selection on these five candidates gives **LSTM**.
LSTM uses 24 x 4 sequential inputs with 30,113 trainable parameters. XGB_full uses flattened lags and derived load features including the 25-hour trend context. G01 ran 18 CPU trials in 46.5 s of fit time. G02 ran two CPU trials in 446.6 s of fit time. F02 compared 24 lag candidates before its VAR(24) validation forecast. The baselines have no fitted parameters. VAR coefficients are explicit, XGB gain is associative, and LSTM state is harder to interpret directly.

Validation scored 5,257 of 5,259 candidates with two missing truths and zero invalid contexts. Train scored 24,435 of 24,519 candidates with 32 missing truths and 52 invalid contexts. MAPE excludes zero truths.

## Proposed model lock

- Weights SHA256: `512715c5249f35bcfe46d1ecdbfc4413dbb1d3f263fe73f41dc9845fe5a69a1c`
- Architecture SHA256: `c858df9f6417ac508d9b4d2195ce0b29a539ab89d4bb5d10950ac12f6d7af807`
- Config SHA256: `866aa8fb59048789010f09c4355ea7a484c7a5e51d06c655e156575a3d0a87fc`
- Reload maximum absolute difference: 0 MW across 5,257 validation rows.

G02 acceptance, LSTM model lock and Phase 8 sign-off are **PENDING HUMAN REVIEW**.
