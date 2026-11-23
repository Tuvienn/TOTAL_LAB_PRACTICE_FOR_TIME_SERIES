# Stage S7 — PyTorch CUDA LSTM Findings & Ablation (v2)

- **Device:** `cuda (NVIDIA GeForce RTX 5050)` (zero `np.repeat(64)` workaround; native `batch=1` & batched inference verified)
- **Selected Winning LSTM Variant:** **`LSTM_24h_cal`**

## 1. Variant & Ablation Comparison (Validation)

| Variant | Window | Input Dim | Params | Best/Stop Epoch | Fit (s) | Train MSE (scaled) | Val MSE (scaled) | MAE (kW) | RMSE (kW) | MAPE (%) |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `LSTM_24h_load_only` | 24h | 1 | 29,729 | 39/49 | 29.92 | 0.007155 | 0.005581 | 4,418.33 | 5,986.57 | 2.4220 |
| `LSTM_24h_core` | 24h | 4 | 30,497 | 37/47 | 26.93 | 0.004498 | 0.005473 | 4,115.95 | 5,928.51 | 2.2192 |
| `LSTM_24h_cal` | 24h | 13 | 32,801 | 19/29 | 18.29 | 0.005131 | 0.005427 | 4,096.36 | 5,903.38 | 2.1921 |
| `LSTM_168h_diag` | 168h | 13 | 32,801 | 19/29 | 19.90 | 0.007248 | 0.006467 | 4,700.52 | 6,444.57 | 2.5218 |

## 2. Multi-Seed Stability (`LSTM_24h_cal`)

| Seed | Best Epoch | MAE (kW) | RMSE (kW) | MAPE (%) |
|---:|---:|---:|---:|---:|
| 42 | 19 | 4,096.36 | 5,903.38 | 2.1921 |
| 123 | 31 | 3,935.22 | 5,901.19 | 2.1015 |
| 2026 | 14 | 4,516.90 | 6,273.03 | 2.4434 |

- Seed RMSE Mean ± Std: **6,025.87 ± 174.77 kW**
