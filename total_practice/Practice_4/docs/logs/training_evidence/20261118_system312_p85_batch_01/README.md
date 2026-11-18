# Phase 8.5 replay training evidence

**PENDING HUMAN REVIEW**. Phase 9 H01 test opening remains gated.

Python 3.12.10 on CPU. Versions: numpy 2.5.5, pandas 2.3.3, statsmodels 0.14.6, xgboost 3.4.1, tensorflow 2.20.0, keras 3.11.3.
Seed 42 applies to XGBoost and LSTM; deterministic baselines and VAR have no random seed.

| Model / trial | Accepted run | Replay run | Log | Log SHA256 |
|---|---|---|---|---|
| persistence | 20261118_system312_f01_01 | 20261118_system312_p85_f01_01 | [persistence.log](persistence.log) | `9da98eaf87c0c5d7e463fbae0a2590ab4db1b6eb44cbcca562658e169c328d26` |
| seasonal24 | 20261118_system312_f01_01 | 20261118_system312_p85_f01_01 | [seasonal24.log](seasonal24.log) | `178bc5478fa09949085ce6e093c5338c906a27dfe300506d275f0774fc934d6e` |
| VAR(24) | 20261118_system312_f02_02 | 20261118_system312_p85_f02_01 | [var24.log](var24.log) | `b1fb2e288a6c8181a793347850d73613c5b5a5187fc30e0ee1d74cfae1ed58e2` |
| XGB_full | 20261118_system312_g01_01 | 20261118_system312_p85_g01_01 | [xgb_full.log](xgb_full.log) | `2a41fa2e13ea651cdcd0ef8ec62efcb0c0758916d04f0d40ccb80755457279a9` |
| XGB_load_only | 20261118_system312_g01_01 | 20261118_system312_p85_g01_01 | [xgb_load_only.log](xgb_load_only.log) | `6c62ec956bad39bb3f159346f741438286372f9460b1412b5067639b7d9bd641` |
| lstm_lr_001 | 20261118_system312_g02_01 | 20261118_system312_p85_g02_01 | [lstm_lr_001.log](lstm_lr_001.log) | `eaaf2205665b1d703ad07149b089ff86bab034faada19f2a945bdca1456f190b` |
| lstm_lr_0005 | 20261118_system312_g02_01 | 20261118_system312_p85_g02_01 | [lstm_lr_0005.log](lstm_lr_0005.log) | `8a6271b33b79bfe7bb65a71c67992bad7282e25971cba736f053c592fe8f967c` |

## Replay manifests and commands

- 20261118_system312_p85_f01_01 manifest SHA256 `b97f319b087579ce0da5e0c52d038316abeb14a986487e7dc465d082ea5047af`; command `py -3.12 -m practice_4.models.baselines --run-id 20261118_system312_p85_f01_01 --replay`.
- 20261118_system312_p85_f02_01 manifest SHA256 `4168ad3fdc05290c859355112a47e6cacad57f1c18ea6bde3e345f29d93def4d`; command `py -3.12 -m practice_4.models.var_model --run-id 20261118_system312_p85_f02_01 --config runs/20261118_system312_f02_02/config.json --baseline-run-id 20261118_system312_f01_01 --replay`.
- 20261118_system312_p85_g01_01 manifest SHA256 `5668014aea50f31b2fac5e1fbe9620c15e5fc6ead6e60db56dd0331f43e8caae`; command `py -3.12 -m practice_4.models.xgboost_model --run-id 20261118_system312_p85_g01_01 --config runs/20261118_system312_g01_01/config.json --replay`.
- 20261118_system312_p85_g02_01 manifest SHA256 `ffed3024761c8f378e06f732a2a7eafa18eec41f133ef3274fb502cc1af76332`; command `py -3.12 -m practice_4.models.lstm_model --run-id 20261118_system312_p85_g02_01 --config runs/20261118_system312_g02_01/config.json --replay`.

## Validation parity

All comparisons use 5,257 common target keys and identical observed truths.

| Model | Metric | Accepted | Replay | Absolute difference | Relative difference |
|---|---|---:|---:|---:|---:|
| persistence | mae_mw | 1115.63401179 | 1115.63401179 | 0 | 0 |
| persistence | rmse_mw | 1507.30330863 | 1507.30330863 | 0 | 0 |
| persistence | mape_percent | 3.91155621032 | 3.91155621032 | 0 | 0 |
| seasonal24 | mae_mw | 2429.28913829 | 2429.28913829 | 0 | 0 |
| seasonal24 | rmse_mw | 3507.53267102 | 3507.53267102 | 0 | 0 |
| seasonal24 | mape_percent | 8.43317531746 | 8.43317531746 | 0 | 0 |
| VAR(24) | mae_mw | 514.619863168 | 514.619863168 | 1.25056e-12 | 2.43006e-15 |
| VAR(24) | rmse_mw | 799.962062264 | 799.962062264 | 7.95808e-13 | 9.94807e-16 |
| VAR(24) | mape_percent | 1.81656479468 | 1.81656479468 | 1.33227e-15 | 7.33399e-16 |
| XGB_full | mae_mw | 300.186405477 | 300.186405477 | 0 | 0 |
| XGB_full | rmse_mw | 508.938994669 | 508.938994669 | 0 | 0 |
| XGB_full | mape_percent | 1.05225101273 | 1.05225101273 | 0 | 0 |
| XGB_load_only | mae_mw | 285.924510623 | 285.924510623 | 0 | 0 |
| XGB_load_only | rmse_mw | 496.164074552 | 496.164074552 | 0 | 0 |
| XGB_load_only | mape_percent | 1.00475502129 | 1.00475502129 | 0 | 0 |
| LSTM selected | mae_mw | 320.691686129 | 320.691686129 | 0 | 0 |
| LSTM selected | rmse_mw | 504.7505974 | 504.7505974 | 0 | 0 |
| LSTM selected | mape_percent | 1.13092916477 | 1.13092916477 | 0 | 0 |
| lstm_lr_001 | mae_mw | 320.691686129 | 320.691686129 | 0 | 0 |
| lstm_lr_001 | rmse_mw | 504.7505974 | 504.7505974 | 0 | 0 |
| lstm_lr_001 | mape_percent | 1.13092916477 | 1.13092916477 | 0 | 0 |
| lstm_lr_0005 | mae_mw | 341.066003 | 341.066003 | 0 | 0 |
| lstm_lr_0005 | rmse_mw | 535.97610162 | 535.97610162 | 0 | 0 |
| lstm_lr_0005 | mape_percent | 1.19315230848 | 1.19315230848 | 0 | 0 |

Relative differences are absolute differences divided by the absolute accepted metric. VAR floating-point differences can arise from numerical linear algebra execution. Logs are replay evidence. Serialised model bytes may differ without changing accepted model identity.
The accepted F01, F02, G01 and G02 model locks remain authoritative for H01. The 26 pre-run input and report hashes were verified after replay. The accepted ADF/KPSS results in the VAR log are copied provenance; lag search and model diagnostics were recomputed.

## Model hashes and limitations

The replay XGB_full and XGB_load_only model JSON bytes match their accepted SHA256 hashes. The selected LSTM weights and architecture bytes also match their accepted SHA256 hashes. The replay VAR NPZ hash is `e4997a2afbd37a1f8ec1f8c7d8da0df21878b8ffc04f161f198152e7e26d84da`, different from the accepted lock. Its coefficients differ by at most 4.65e-15, intercept by 4.03e-16 and residual covariance by 8.33e-17. These small differences are consistent with numerical linear algebra but the specific cause was not isolated.

For this replay, XGBoost per-round history was written after each completed trial. The console records completed trials, so per-round evidence for an interrupted trial would not have survived. After replay, the runner was changed to stream per-round output when replaying; that logging-only change passed the targeted tests. The fit source recorded in the XGBoost run is a reconstruction of the source before this change. Baseline and VAR wall-clock durations were not instrumented; individual XGBoost trial and LSTM fit durations are recorded. LSTM epoch durations are those printed by Keras in the trial logs.

Before real-data replay, 25 targeted tests passed, including the synthetic XGBoost monitoring comparison. After the final collision/configuration safeguards and logging change, 27 targeted tests passed with eight Keras/NumPy deprecation warnings. TensorFlow logged an ignored MapDataset attribute and NumPy timedelta deprecation warnings in the LSTM console.
