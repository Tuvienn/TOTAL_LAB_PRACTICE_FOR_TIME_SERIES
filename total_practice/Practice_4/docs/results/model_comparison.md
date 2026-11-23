# Stage S8 — Test Comparison, Diebold–Mariano Test & Error Analysis (v2)

## 1. Official Test Metrics (Locked Walk-Forward)

| Model | Scored | MAE (kW) | RMSE (kW) | MAPE (%) | Resid ACF Lag-24 | Resid ACF Lag-168 |
|---|---:|---:|---:|---:|---:|---:|
| `XGB_best` | 3,947 | 3,564.37 | 5,499.38 | 1.7776 | -0.0357 | 0.0708 |
| `LSTM_core` | 3,947 | 4,156.48 | 5,872.02 | 2.1322 | 0.3703 | 0.3753 |
| `XGB_4var` | 3,947 | 3,756.09 | 5,889.87 | 1.8802 | -0.1457 | 0.1329 |
| `VAR` | 3,947 | 4,183.93 | 6,259.22 | 2.0989 | -0.2075 | 0.1917 |
| `LSTM_best` | 3,947 | 4,557.90 | 6,433.83 | 2.4024 | 0.4965 | 0.4505 |
| `seasonal24` | 3,947 | 7,716.33 | 13,502.14 | 3.8434 | -0.2341 | 0.1576 |
| `seasonal168` | 3,947 | 12,247.95 | 19,011.91 | 5.5608 | 0.6515 | -0.2675 |
| `persistence` | 3,947 | 16,345.12 | 25,507.75 | 8.7756 | 0.9651 | 0.9508 |

## 2. Diebold–Mariano Significance Tests (Squared Error Loss, h=1)

| Model A | Model B | DM Statistic | p-value | Significant (5%) | Better |
|---|---|---:|---:|---|---|
| `XGB_best` | `LSTM_best` | -6.3783 | 1.79e-10 | `True` | `XGB_best` |
| `XGB_best` | `VAR` | -6.3744 | 1.837e-10 | `True` | `XGB_best` |
| `LSTM_best` | `VAR` | 1.1930 | 0.2329 | `False` | `VAR` |
| `XGB_best` | `seasonal168` | -22.7686 | 9.397e-115 | `True` | `XGB_best` |
| `LSTM_best` | `seasonal168` | -21.2928 | 1.325e-100 | `True` | `LSTM_best` |
| `XGB_4var` | `LSTM_core` | 0.1275 | 0.8986 | `False` | `LSTM_core` |
