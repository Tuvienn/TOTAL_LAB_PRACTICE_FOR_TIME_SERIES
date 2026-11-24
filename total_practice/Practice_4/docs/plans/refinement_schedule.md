# Practice 4 (v2) — Refinement Stage Schedule & Review Log (`R1 → R5`)

Tài liệu lịch trình thực thi và nhật ký kiểm duyệt (review gate) cho 5 stage nâng cấp toàn diện `Practice_4` v2 sau đợt audit độc lập.

| Stage | Tên giai đoạn | Phạm vi chính | Gate kiểm định bắt buộc | Trạng thái |
|---|---|---|---|---|
| **R1** | Clean v1 Residue & Zero Warnings | Xóa 17 file tài liệu/dead-code v1 (`Spain/MW`), viết lại `README.md`, `problem_definition.md`, `evaluation_contract.md`, `requirements.lock.txt`, fresh-clone guard, khử 6 warnings, sync `file_map.csv` | `pytest` 19/19 pass **0 warnings**; 0 tàn dư `Spain\|20261118\|tensorflow\|keras` | `DONE & REVIEWED` |
| **R2** | Metric Schema `kW` Standardization | Đổi toàn bộ key/cột `mae_mw`, `rmse_mw` → `mae_kw`, `rmse_kw` trong `src/` & `tests/`; chạy lại Stage `S5` | Quét `mae_mw\|rmse_mw` = **0 kết quả**; `test_s0..test_s5` pass **0 warnings** | `DONE & REVIEWED` |
| **R3** | Nested XGBoost Ablation & 24h Fairness (`[M1]`) | Tái thiết kế 5 tập con lồng nhau chặt (`XGB_24h_4var` thuần 24h không dùng `trend168h`/`trend24h(t-24)`, `XGB_load_only ⊂ XGB_load_weather ⊂ XGB_full`, `XGB_load_only ⊂ XGB_load_calendar ⊂ XGB_full`); chạy lại `S4` + `S6` trên RTX 5050 | Test **strict subset nesting** & **24h window invariance**; `test_s4`, `test_s6` pass **0 warnings** | `DONE & REVIEWED` |
| **R4** | Balanced LSTM Tuning & Target Calendar (`[M2]`) | Nâng cấp `MultivariateLSTM` hỗ trợ nối `target_cal(t+1)` (`future_cal_dim=9`) vào tầng cuối; chạy đủ 4 hyperparameter trials cho CẢ 4 biến thể (`16` trials) + 3-seed stability trên RTX 5050 | `test_s7` kiểm chứng 4 biến thể × 4 trials, reload parity `batch=1` & `batch=256` `< 1e-2 kW`, **0 warnings** | `DONE & REVIEWED` |
| **R5** | Locked Test Walk-Forward (`S8`), Dynamic Report & Transparent Notebook | Chạy lại `S8` với `XGB_24h_4var` & `LSTM` mới; xóa toàn bộ số hardcode trong `error_analysis.py`; bổ sung cell hiển thị code cốt lõi trong `practice_4.ipynb`; sync `file_map.csv` & `walkthrough.md` | Toàn bộ `pytest` **100% pass, 0 warnings**; `nbconvert` **0 lỗi**; 0 số hardcode | `DONE & REVIEWED` |

---

## Stage Review Logs

### Stage R1 Review — `PASS`
- **Artifacts updated/pruned:** Xóa 17 file v1 (`walk_forward.py`, `alignment_audit.md`, `phase_00..09.md`, `plan_overview.md`, `plan_review.md`, `PROJECT_OVERVIEW.md`, `b01_core_environment.md`); viết chuẩn v2 cho `README.md`, `problem_definition.md`, `evaluation_contract.md`, `requirements.lock.txt`.
- **`file_map.csv` sync:** `103` file `EXISTING`, prune `17` mục đã xóa.
- **Verification:** Quét tàn dư v1 = `0`; `py -3.12 -m pytest tests/ -v -p no:cacheprovider` → **`19 passed in 19.25s`** (**0 failed, 0 warnings**).

### Stage R2 Review — `PASS`
- **Changes:** Đổi toàn bộ `mae_mw`/`rmse_mw` → `mae_kw`/`rmse_kw` trong `metrics.py`, `baselines.py`, `var_model.py`, `xgboost_model.py`, `lstm_model.py`, `h01_evaluation.py`, `error_analysis.py`, `pipeline.py`, và `tests/test_s5..s8`; chạy lại Stage `S5`.
- **`file_map.csv` sync:** Đăng ký `docs/plans/refinement_schedule.md` → `104` file `EXISTING`.
- **Verification:** Quét `mae_mw|rmse_mw` trong `src/` & `tests/` = `0`; `pytest tests/test_s0..test_s5` → **`15 passed in 8.61s`** (**0 failed, 0 warnings**).

### Stage R3 Review — `PASS`
- **Changes:** Tái thiết kế `xgb_ablation_subsets()` trong `features.py` thành 5 tập con lồng nhau chặt (`XGB_24h_4var` 102 thuần 24h, `XGB_load_only` 34, `XGB_load_weather` 106, `XGB_load_calendar` 43, `XGB_full` 121), lưu thêm `target_cal` `(N, 9)` vào `model_inputs.npz`, chạy lại `S4` & `S6` trên RTX 5050.
- **Validation Ablation (kW):** `XGB_24h_4var` `5,122.91` → `XGB_load_only` `4,577.17` → `XGB_load_weather` `4,513.26` → `XGB_load_calendar` `4,463.62` → **`XGB_full` `4,358.22`** (`reload_max_diff = 0.0`).
- **Verification:** `pytest tests/test_s4_prep_features.py tests/test_s6_xgboost_gpu.py` → **`3 passed in 2.51s`** (**0 failed, 0 warnings**), chứng minh strict nesting + bất biến 24h cho `XGB_24h_4var`.

### Stage R4 Review — `PASS`
- **Changes:** Nâng cấp `MultivariateLSTM` hỗ trợ `future_cal_dim=9` (nối lịch tất định `t+1` vào tầng `Linear` cuối) và cân bằng ngân sách tuning **4 trials × 4 biến thể = 16 trials** + 3 seeds trên RTX 5050 CUDA.
- **Key Scientific Finding:** Khi được tuning công bằng và cấp `target_cal(t+1)`, **`LSTM_168h_diag`** (`5,891.69 kW`, MAE `4,004.98 kW`) đã vượt qua `LSTM_24h_core` (`5,928.51 kW`), `LSTM_24h_load_only` (`5,986.57 kW`) và `LSTM_24h_cal` (`6,054.99 kW`) trên Validation; 3-seed stability `6,027.62 ± 144.62 kW`.
- **Verification:** `pytest tests/test_s7_lstm_gpu.py` → **`2 passed in 3.49s`** (**0 failed, 0 warnings**), xác nhận 4 trials/biến thể và reload parity `batch=1`/`batch=256` `< 1e-2 kW`.

### Stage R5 Review — `PASS`
- **Changes:** Chạy lại Locked Test Walk-Forward (`S8`) với `XGB_24h_4var` (thuần 24h) và `LSTM_168h_diag` (`future_cal_dim=9`), viết lại Q1–Q6 trong `error_analysis.py` 100% động (0 số hardcode), bổ sung `show_code(...)` hiển thị 5 khối mã nguồn cốt lõi trực tiếp trong `practice_4.ipynb`.
- **Official Locked Test Leaderboard (3,947 points, kW):**
  - `XGB_best` (`XGB_full`): MAE `3,564.37`, RMSE **`5,499.38`**, MAPE `1.7776%`
  - `LSTM_core` (`24×4`): MAE `4,156.48`, RMSE **`5,872.02`**, MAPE `2.1322%`
  - `LSTM_best` (`LSTM_168h_diag`): MAE `4,301.28`, RMSE **`6,191.98`**, MAPE `2.1765%`
  - `VAR` (`VAR_diff1`, `d=1, p=24`): MAE `4,183.93`, RMSE **`6,259.22`**, MAPE `2.0989%`
  - `XGB_4var` (`XGB_24h_4var`, pure 24h): MAE `4,129.84`, RMSE **`6,328.82`**, MAPE `2.0922%`
- **Diebold–Mariano Key Findings:**
  - Strict 24h raw window (`XGB_4var` vs `LSTM_core`): `DM = +3.2468`, `p = 0.001167` → **`LSTM_core` thắng có ý nghĩa thống kê**.
  - Full tabular feature engineering (`XGB_best` vs `LSTM_best`): `DM = -4.9617`, `p = 6.988e-07` → **`XGB_best` thắng có ý nghĩa thống kê**.
- **Verification:** `nbconvert` ghi `2,207,514` bytes vào `notebooks/practice_4.ipynb` (`18` cells, `0` errors, `5` rendered Python source blocks); toàn bộ `py -3.12 -m pytest tests/ -v -p no:cacheprovider` → **`19 passed in 7.59s`** (**0 failed, 0 warnings**).
