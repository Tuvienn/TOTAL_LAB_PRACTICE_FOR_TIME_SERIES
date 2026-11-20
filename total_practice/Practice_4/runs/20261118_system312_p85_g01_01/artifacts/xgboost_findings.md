# G01 XGBoost findings

Run `20261118_system312_p85_g01_01`. **PENDING HUMAN REVIEW**.

## Trials

| Subset | Trial | Trees | MAE MW | RMSE MW | MAPE % |
|---|---|---:|---:|---:|---:|
| XGB_full | XGB_full_d3_n0300 | 300 | 419.708812 | 637.734486 | 1.464720 |
| XGB_full | XGB_full_d3_n0600 | 599 | 384.806953 | 592.611380 | 1.346787 |
| XGB_full | XGB_full_d3_n1000 | 997 | 363.523950 | 565.921681 | 1.274019 |
| XGB_full | XGB_full_d5_n0300 | 300 | 341.630316 | 545.206606 | 1.197666 |
| XGB_full | XGB_full_d5_n0600 | 600 | 326.464699 | 528.611044 | 1.146293 |
| XGB_full | XGB_full_d5_n1000 | 1000 | 317.629286 | 519.872267 | 1.116383 |
| XGB_full | XGB_full_d7_n0300 | 300 | 307.422395 | 517.551617 | 1.076400 |
| XGB_full | XGB_full_d7_n0600 | 585 | 302.561883 | 511.922328 | 1.060574 |
| XGB_full | XGB_full_d7_n1000 | 931 | 300.186405 | 508.938995 | 1.052251 |
| XGB_load_only | XGB_load_only_d3_n0300 | 300 | 424.670359 | 643.224797 | 1.479797 |
| XGB_load_only | XGB_load_only_d3_n0600 | 599 | 380.032459 | 587.581054 | 1.329063 |
| XGB_load_only | XGB_load_only_d3_n1000 | 1000 | 353.768056 | 556.347148 | 1.239830 |
| XGB_load_only | XGB_load_only_d5_n0300 | 300 | 334.181620 | 536.294486 | 1.172581 |
| XGB_load_only | XGB_load_only_d5_n0600 | 598 | 310.348503 | 511.261107 | 1.090527 |
| XGB_load_only | XGB_load_only_d5_n1000 | 1000 | 298.506091 | 499.341123 | 1.049844 |
| XGB_load_only | XGB_load_only_d7_n0300 | 300 | 293.715043 | 503.342760 | 1.031367 |
| XGB_load_only | XGB_load_only_d7_n0600 | 509 | 285.924511 | 496.164075 | 1.004755 |
| XGB_load_only | XGB_load_only_d7_n1000 | 509 | 285.924511 | 496.164075 | 1.004755 |

## Validation comparison

| Model | MAE MW | RMSE MW | MAPE % |
|---|---:|---:|---:|
| persistence | 1115.634012 | 1507.303309 | 3.911556 |
| seasonal24 | 2429.289138 | 3507.532671 | 8.433175 |
| VAR(24) | 514.619863 | 799.962062 | 1.816565 |
| XGB_full | 300.186405 | 508.938995 | 1.052251 |
| XGB_load_only | 285.924511 | 496.164075 | 1.004755 |

Full minus load-only: MAE 14.261895 MW, RMSE 12.774920 MW, MAPE 0.047496 percentage points.

Validation has 5259 candidates, 2 missing truths, 0 invalid contexts, and 5257 scored. Train has 24519 candidates, 32 missing truths, 52 invalid contexts, and 24435 scored. Initial warm-up contains 25 target rows. MAPE excludes zero truths.

## Gain importance

Group totals sum each feature's mean split gain. These values describe predictive association and are affected by correlated inputs and weather proxies. The validation set supports early stopping and selection, introducing optimism. Neither gain nor ablation establishes causality.
- load: 1556962411.625000
- temperature: 22642889.187500
- humidity: 16032386.531250
- wind_speed: 12084023.281250
- derived_load: 33639766.125000

- XGB_full: `e7386e8cfc38d51d6abc51abad383fb2c9d6360c9c955c6fe3ddb33883aec8ae`

- XGB_load_only: `9ff12725117703eeafbc1d29df114f798f3e6e3f2fb9e40b6b793220efb90006`
