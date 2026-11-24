# Stage S6 — GPU-Accelerated XGBoost, Ablation & SHAP Findings (v2)

- **Device:** NVIDIA RTX 5050 (`device=cuda`, `tree_method=hist`)
- **CV-Selected Hyperparameters (3-fold Expanding CV on Train):** `max_depth=6`, `learning_rate=0.02`, `min_child_weight=5.0`, `colsample_bytree=0.7`, `reg_lambda=5.0` (CV RMSE `5,252.61 ± 770.40 kW`)
- **Selected Winning Subset on Validation:** **`XGB_full`**
- **SHAP Additivity Max Error:** `0.631271 kW`

## 1. Validation Ablation Study

| Subset | Features | Trees | Fit (s) | MAE (kW) | RMSE (kW) | MAPE (%) |
|---|---:|---:|---:|---:|---:|---:|
| `XGB_full` | 121 | 707 | 3.38 | 2,996.39 | 4,358.22 | 1.5564 |
| `XGB_load_calendar` | 43 | 506 | 2.01 | 3,036.55 | 4,463.62 | 1.5775 |
| `XGB_load_weather` | 106 | 464 | 2.26 | 3,097.71 | 4,513.26 | 1.6327 |
| `XGB_load_only` | 34 | 623 | 2.17 | 3,106.24 | 4,577.17 | 1.6185 |
| `XGB_24h_4var` | 102 | 1041 | 4.89 | 3,610.86 | 5,122.91 | 1.8994 |

## 2. SHAP Group Attribution (`XGB_full`)

| Feature Group | Sum of Mean |SHAP| (kW) |
|---|---:|
| `load_lags_24h` | 39,096.84 |
| `load_rolling_weekly` | 28,740.64 |
| `cross_interactions` | 2,700.73 |
| `temperature_lags` | 1,702.68 |
| `calendar_dst_holiday` | 1,372.96 |
| `humidity_lags` | 739.89 |
| `wind_speed_lags` | 324.71 |

## 3. Top 10 Individual Features by Mean |SHAP|

| Feature | Group | Mean |SHAP| (kW) |
|---|---|---:|
| `lag23_load` | `load_lags_24h` | 31,805.18 |
| `lag167_load` | `load_rolling_weekly` | 18,532.06 |
| `lag47_load` | `load_rolling_weekly` | 6,291.63 |
| `lag00_load` | `load_lags_24h` | 4,474.62 |
| `trend24h` | `load_rolling_weekly` | 2,101.39 |
| `load_per_temp_k` | `cross_interactions` | 1,449.37 |
| `lag22_load` | `load_lags_24h` | 1,201.23 |
| `lag00_temperature` | `temperature_lags` | 1,056.58 |
| `temp_diff_24h` | `cross_interactions` | 451.01 |
| `target_hour_cos` | `calendar_dst_holiday` | 389.72 |
