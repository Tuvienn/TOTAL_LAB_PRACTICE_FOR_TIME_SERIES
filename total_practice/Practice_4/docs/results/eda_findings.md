# Stage S3 — Train-Only Exploratory Data Analysis (v2)

- **Scope:** Train split only (`18,412` hours, `2012-01-01T00:00:00+00:00` → `2014-02-06T03:00:00+00:00`). Validation and test were never accessed.
- **Missing load:** `0` | **DST fall-back split hours:** `4` | **Weather physical anomalies:** `0`

## 1. Variable Distributions & Extrema (Train)

| Variable | Min | Mean | Std | Max | P0.5 | P99.5 | Missing |
|---|---:|---:|---:|---:|---:|---:|---:|
| `load` | 85,981.76 | 204,690.87 | 80,138.15 | 446,935.42 | 91,471.48 | 403,430.92 | 0 |
| `temp` | 0.39 | 15.33 | 5.62 | 35.99 | 4.19 | 31.49 | 0 |
| `humidity` | 21.90 | 75.93 | 15.43 | 100.00 | 32.71 | 98.35 | 0 |
| `wind_speed` | 0.30 | 3.94 | 1.73 | 13.96 | 0.91 | 9.45 | 0 |

## 2. Load–Weather Association (Train, Non-Causal)

| Weather Variable | Pearson r | Spearman ρ |
|---|---:|---:|
| `temp` | 0.6767 | 0.6018 |
| `humidity` | -0.6404 | -0.6016 |
| `wind_speed` | 0.1113 | 0.1202 |

## 3. Temporal Dependence (ACF)

- Lag 1h ACF: `0.9574`
- Lag 24h (daily) ACF: `0.9863`
- Lag 168h (weekly) ACF: `0.9623`
