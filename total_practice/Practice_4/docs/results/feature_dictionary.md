# Stage S4 — Causal Feature Dictionary (v2)

- **Common Causal Context:** `168` hours (`t-167 .. t`) to predict observed raw `load(t+1)`.
- **Train Eligible:** `18,244` / `18,244`
- **Validation Eligible:** `3,945` / `3,945`
- **Total `XGB_full` Features:** `121`
- **LSTM Core Shape:** `(N, 24, 4)` | **LSTM Calendar Shape:** `(N, 24, 13)`

## Ablation Feature Subsets

| Subset | Count | Description |
|---|---:|---|
| `XGB_24h_4var` | 102 | Strictly 24h (`t-23..t`) 4-variable lags (96) + 6 pure-24h load stats (exact window match to `LSTM_24h_core`) |
| `XGB_load_only` | 34 | 24h load lags + `lag47_load`/`lag167_load` + 8 rolling load stats |
| `XGB_load_weather` | 106 | Strictly nested: `XGB_load_only` + 72 weather lags (24h) |
| `XGB_load_calendar` | 43 | Strictly nested: `XGB_load_only` + 9 local calendar/DST/holiday features at `t+1` |
| `XGB_full` | 121 | Strictly nested superset: `XGB_load_weather` + 9 target calendar + 6 cross-variable interactions |

## Cross-Variable Interaction Features (Slide 7, `chapter4-5.pdf`)

- `load_per_temp_k`: `load_input(t) / (temp_input(t) + 273.15)`
- `hdd_proxy`: `max(0, 18.0 - temp_input(t))` (heating load nonlinearity)
- `cdd_proxy`: `max(0, temp_input(t) - 22.0)` (cooling load nonlinearity)
- `temp_x_humidity`: `temp_input(t) * humidity_input(t)`
- `temp_diff_1h`, `temp_diff_24h`: 1-hour and 24-hour temperature change at origin `t`
