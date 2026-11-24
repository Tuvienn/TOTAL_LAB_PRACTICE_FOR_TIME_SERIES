# Stage S7 — PyTorch CUDA LSTM Findings & Ablation (v2)

- **Device:** `cuda (NVIDIA GeForce RTX 5050)` (zero `np.repeat(64)` workaround; native `batch=1` & batched inference verified)
- **Selected Winning LSTM Variant:** **`LSTM_168h_diag`**

## 1. Variant & Ablation Comparison (Validation)

| Variant | Window | Seq Dim | Target Cal (t+1) | Best Trial | Params | Best/Stop Epoch | Fit (s) | Train MSE (scaled) | Val MSE (scaled) | MAE (kW) | RMSE (kW) | MAPE (%) |
|---|---:|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|
| `LSTM_24h_load_only` | 24h | 1 | 0 | `lr1e3_d10` | 29,729 | 39/49 | 30.13 | 0.007155 | 0.005581 | 4,418.33 | 5,986.57 | 2.4220 |
| `LSTM_24h_core` | 24h | 4 | 0 | `lr1e3_d00` | 30,497 | 37/47 | 27.59 | 0.004498 | 0.005473 | 4,115.95 | 5,928.51 | 2.2192 |
| `LSTM_24h_cal` | 24h | 13 | 9 | `lr1e3_d00` | 32,810 | 27/37 | 22.80 | 0.004104 | 0.005709 | 4,235.27 | 6,054.99 | 2.3615 |
| `LSTM_168h_diag` | 168h | 13 | 9 | `lr1e3_d00` | 32,810 | 27/37 | 25.32 | 0.004058 | 0.005405 | 4,004.98 | 5,891.69 | 2.1596 |

## 2. Multi-Seed Stability (`LSTM_168h_diag`)

| Seed | Best Epoch | MAE (kW) | RMSE (kW) | MAPE (%) |
|---:|---:|---:|---:|---:|
| 42 | 27 | 4,004.98 | 5,891.69 | 2.1596 |
| 123 | 19 | 4,349.23 | 5,963.24 | 2.4035 |
| 2026 | 14 | 4,479.42 | 6,227.93 | 2.4190 |

- Seed RMSE Mean ± Std: **6,027.62 ± 144.62 kW**
