# Stage S8 — Test Comparison, Diebold–Mariano Test & Error Analysis (v2)

## 1. Official Test Metrics (Locked Walk-Forward)

| Model | Scored | MAE (kW) | RMSE (kW) | MAPE (%) | Resid ACF Lag-24 | Resid ACF Lag-168 |
|---|---:|---:|---:|---:|---:|---:|
| `XGB_best` | 3,947 | 3,564.37 | 5,499.38 | 1.7776 | -0.0357 | 0.0708 |
| `LSTM_core` | 3,947 | 4,156.48 | 5,872.02 | 2.1322 | 0.3703 | 0.3753 |
| `LSTM_best` | 3,947 | 4,301.28 | 6,191.98 | 2.1765 | 0.4589 | 0.3832 |
| `VAR` | 3,947 | 4,183.93 | 6,259.22 | 2.0989 | -0.2075 | 0.1917 |
| `XGB_4var` | 3,947 | 4,129.84 | 6,328.82 | 2.0922 | 0.0263 | 0.2318 |
| `seasonal24` | 3,947 | 7,716.33 | 13,502.14 | 3.8434 | -0.2341 | 0.1576 |
| `seasonal168` | 3,947 | 12,247.95 | 19,011.91 | 5.5608 | 0.6515 | -0.2675 |
| `persistence` | 3,947 | 16,345.12 | 25,507.75 | 8.7756 | 0.9651 | 0.9508 |

## 2. Diebold–Mariano Significance Tests (Squared Error Loss, h=1)

| Model A | Model B | DM Statistic | p-value | Significant (5%) | Better |
|---|---|---:|---:|---|---|
| `XGB_best` | `LSTM_best` | -4.9617 | 6.988e-07 | `True` | `XGB_best` |
| `XGB_best` | `VAR` | -6.3744 | 1.837e-10 | `True` | `XGB_best` |
| `LSTM_best` | `VAR` | -0.4670 | 0.6405 | `False` | `LSTM_best` |
| `XGB_best` | `seasonal168` | -22.7686 | 9.397e-115 | `True` | `XGB_best` |
| `LSTM_best` | `seasonal168` | -21.5291 | 8.316e-103 | `True` | `LSTM_best` |
| `XGB_4var` | `LSTM_core` | 3.2468 | 0.001167 | `True` | `LSTM_core` |
