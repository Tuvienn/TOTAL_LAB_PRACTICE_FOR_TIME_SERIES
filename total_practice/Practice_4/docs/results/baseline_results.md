# F01 Baseline Results

Run `20261118_system312_f01_01` · **APPROVED / COMPLETED** by Human on 2026-11-18 via Director review. The F01 manifest retains the report hash from execution before this approval update.

Warm-up: 25 target rows. MAPE is a percentage computed from original MW truths.

| Model | Split | Candidates | Missing | Invalid context | Scored | MAE MW | RMSE MW | MAPE % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| persistence | train | 24519 | 32 | 52 | 24435 | 1057.144465 | 1423.175861 | 3.775262 |
| persistence | validation | 5259 | 2 | 0 | 5257 | 1115.634012 | 1507.303309 | 3.911556 |

persistence complexity 0, RV2 model configuration SHA256 `f0bce270c71b033af288c8f2b43ab05a66730d98aaa00ba0694c70fd24925d63`.
| seasonal24 | train | 24519 | 32 | 52 | 24435 | 2440.233804 | 3509.274071 | 8.648751 |
| seasonal24 | validation | 5259 | 2 | 0 | 5257 | 2429.289138 | 3507.532671 | 8.433175 |

seasonal24 complexity 0, RV2 model configuration SHA256 `2c8b93b4f663e69f6ef62229ab8c3df79d4f3959a5cb803ec9521682aac7dce3`.

Forecasts use fixed D02 scaling and the common E02 eligible origins. The one-step lab protocol assumes input measurements are available at the end of the origin hour.
