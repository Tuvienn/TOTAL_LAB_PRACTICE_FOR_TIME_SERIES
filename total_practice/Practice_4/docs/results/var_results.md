# Stage S5 — Stationary VAR Results (v2)

- **Selected VAR:** `VAR_diff1` (`p=24`, `d=1`)
- **Selection Rationale:** Selected VAR_diff1 per chapter4-5.pdf Slide 5 (KPSS rejects level stationarity; diff1 achieves both ADF & KPSS stationarity and stable eigenvalues).
- **Training Rows Used:** `18,411` (100% of causal training history — fixes v1 62% data loss).

## 1. Stationarity Diagnostics (ADF + KPSS on Full Train)

| Variable | Level ADF p | Level KPSS p | Level Stationary? | Diff-1 ADF p | Diff-1 KPSS p | Diff-1 Stationary? |
|---|---:|---:|---|---:|---:|---|
| `load` | 0.01639 | 0.01 | `False` | 0 | 0.1 | `True` |
| `temperature` | 0.001105 | 0.01 | `False` | 0 | 0.1 | `True` |
| `humidity` | 3.999e-11 | 0.01304 | `False` | 0 | 0.1 | `True` |
| `wind_speed` | 1.593e-20 | 0.01 | `False` | 0 | 0.1 | `True` |

## 2. VAR Variants & Baseline Validation Comparison

| Model | d | p | Max |λ| | Whiteness p | MAE (kW) | RMSE (kW) | MAPE (%) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `persistence` | - | - | - | - | 14,490.64 | 21,265.95 | 8.5874 |
| `seasonal24` | - | - | - | - | 5,792.47 | 8,846.94 | 2.9552 |
| `seasonal168` | - | - | - | - | 12,407.93 | 21,537.95 | 5.5045 |
| `VAR_diff1` | 1 | 24 | 0.999809 | 0 | 3,317.19 | 4,793.35 | 1.7830 |
| `VAR_level` | 0 | 24 | 0.999828 | 0 | 4,935.83 | 6,992.35 | 2.6693 |
