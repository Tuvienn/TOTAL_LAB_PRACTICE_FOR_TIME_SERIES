# PHASE 07 — FINAL FORECASTING & EVALUATION

## 1. Phase identity

```text
Project: Practice_3_v2
Phase: 7
Name: Final Forecasting & Evaluation
Design status: APPROVED
Human design approval: GRANTED
Implementation authorization: GRANTED
Human result approval: GRANTED
Execution status: COMPLETED — HUMAN APPROVED
```

## 2. Mục tiêu

Refit model đã khóa trên toàn bộ eligible development population, sau đó đánh
giá one-step và recursive 24-hour trên historical re-evaluation holdout.

```text
Phase 6 model lock
+ full development X/y
+ historical holdout
→ one-step rolling-observed-history evaluation
→ recursive 24-hour stress test
→ predictions, metrics, figures and evaluation audit
```

Phase 7 không tuning, không chọn lại feature/model, không thay model lock và
không thực hiện error interpretation thay Phase 8.

## 3. Claim boundary

Holdout đã từng được quan sát trong legacy Practice 3. Vì vậy mọi artifact phải
gọi partition này là `historical_re_evaluation_holdout`, không được gọi là
untouched/unseen final test.

Phase 7 result đo historical generalization trong giai đoạn đã khóa, không chứng
minh hiệu năng cho mọi future regime.

## 4. Entry gate

Phase 7 chỉ được mở holdout sau khi:

- Phase 0–6 `PASS — HUMAN APPROVED`;
- Phase 6 model lock checksum khớp contract;
- selected candidate đúng `xgboost_tuned`;
- locked parameters, seed, feature order và package versions đầy đủ;
- full development population vẫn có 108.083 eligible samples;
- prepared data và upstream artifacts giữ nguyên identity;
- preflight PASS mà chưa đọc holdout target.

Nếu entry gate sai, Phase 7 phải dừng trước holdout opening.

## 5. Evaluation registry

Chỉ đánh giá ba candidates:

```text
persistence
seasonal_naive_24
xgboost_tuned
```

`xgboost_baseline` và `random_forest` đã thua trong TRAIN-only CV nên không được
đưa trở lại holdout để tạo model-selection vòng hai.

## 6. Locked-model refit

`xgboost_tuned` được dựng lại từ `phase_06_model_lock.json` và fit đúng một lần
trên toàn bộ 108.083 eligible development samples.

Không được:

- dùng holdout target trong fit;
- refit theo từng holdout timestamp hoặc origin;
- thay parameter/seed/package protocol;
- thay feature order;
- persist binary model.

## 7. One-step protocol

Tại target timestamp `T`:

```text
forecast origin = T - 1 hour
available actual history <= T - 1 hour
prediction target = y(T)
update cadence = hourly after actual becomes available
```

Đây là rolling observed-history evaluation. Actual tại `T` chỉ được dùng cho
forecast tiếp theo sau khi thời điểm đó đã được quan sát.

Population contract:

```text
holdout structural rows = 8,761
expected common eligible rows = 8,592
target finite = required
all 22 features finite = required
imputation = none
same timestamps for all candidates = true
```

Nếu common eligible population khác 8.592, dừng và báo Human; không tự thay
expected count hoặc loại riêng timestamp theo model.

Baseline formulas:

```text
persistence(T) = actual(T-1h)
seasonal_naive_24(T) = actual(T-24h)
```

## 8. Recursive 24-hour protocol

```text
strategy = recursive
horizon = 24 hours
scheduled origin hour = 23:00
origin spacing = 24 hours
target block = next calendar day 00:00–23:00
target-window overlap = false
```

Origin đầu có thể nằm ở cuối development nếu toàn bộ 24 targets tiếp theo thuộc
holdout. Một origin chỉ hợp lệ khi:

- đủ 24 hourly target timestamps liên tục trong holdout;
- cả 24 actual targets finite;
- actual history đến origin đủ cho 22 features;
- cùng origin hợp lệ cho cả ba candidates;
- persistence origin value finite.

Nếu một target trong block thiếu, loại toàn bộ origin; không tính partial block.

Recursive update cho `xgboost_tuned`:

```text
h = 1: build feature row from actual history through origin
h = 2..24: append prior predictions to synthetic history
           rebuild all 22 features
           predict next horizon
```

Actual target sau origin tuyệt đối không được đưa vào synthetic history.

Recursive baselines:

```text
persistence(origin+h) = actual(origin), h=1..24
seasonal_naive_24(origin+h) = actual(origin+h-24), h=1..24
```

## 9. Metric contract

One-step cho từng candidate:

```text
MAE
RMSE
n_observations
evaluation_start
evaluation_end
```

Recursive cho từng candidate và horizon `1..24`:

```text
MAE_h
RMSE_h
n_origins
```

Recursive pooled metrics:

```text
pooled_MAE
pooled_RMSE
n_predictions
n_origins
```

One-step và recursive metrics phải báo riêng. Pooled RMSE phải tính trực tiếp từ
toàn bộ squared errors, không lấy trung bình 24 RMSE_h.

## 10. Official outputs

```text
config/final_evaluation.json
outputs/results/phase_07_one_step_predictions.csv
outputs/results/phase_07_one_step_metrics.json
outputs/results/phase_07_recursive_predictions.csv
outputs/results/phase_07_recursive_metrics.json
outputs/results/phase_07_evaluation_audit.json
outputs/figures/phase_07_one_step_full_holdout.png
outputs/figures/phase_07_one_step_first_14_days.png
outputs/figures/phase_07_recursive_error_by_horizon.png
docs/logs/PHASE_07_EXECUTION.md
```

Prediction CSV phải giữ timestamp/origin, horizon, actual, prediction, signed
error, absolute error, squared error, candidate và protocol để Phase 8 phân tích.

## 11. Fixed visualizations

Ba figures được khóa trước execution:

1. Full-holdout one-step: actual, locked XGBoost và Seasonal Naive 24.
2. Fixed first-14-day one-step window: `2017-08-03 00:00:00` đến
   `2017-08-16 23:00:00`.
3. Recursive MAE/RMSE theo horizon `1..24`.

Không cherry-pick khoảng thời gian sau khi xem prediction.

## 12. Run, logging and checkpoint

```text
runs/P7_final_evaluation_<timestamp>_<execution_identity>/
├── P7_final_evaluation_<timestamp>_<execution_identity>.log
├── run_metadata.json
├── config_snapshot.json
├── checkpoint.json
├── one_step_predictions.csv
└── recursive_predictions.csv
```

Log dùng format:

```text
<timestamp> | <level> | <message>
```

Checkpoint sau mỗi candidate/protocol unit. Interrupted/failed run không được
promote official outputs. Resume phải xác minh configuration, prepared data,
model lock, feature schema và package versions.

## 13. Human execution boundary

AI được chuẩn bị source, tests và preflight rồi phải dừng. Human trực tiếp chạy
hoặc resume final evaluation trên Terminal. Holdout opening event chỉ được ghi
khi Human chạy approved command sau preflight.

## 14. Binary-model policy

Phase 7 không persist `.pkl`, `.joblib` hoặc model binary. Model được tái tạo từ
locked parameters, seed, package versions, feature schema và development data.

## 15. Implementation ownership

```text
config/final_evaluation.json
src/practice_3_v2/analysis/forecasting.py
src/practice_3_v2/analysis/evaluation.py
src/practice_3_v2/visualization/forecast_evaluation.py
tests/test_forecasting.py
tests/test_evaluation.py
```

Notebook chỉ đọc official Phase 7 CSV/JSON/PNG; không fit hoặc predict.

## 16. Validation contract

Tests phải kiểm tra:

1. model-lock/checksum/package identity;
2. selected registry chỉ gồm locked model và hai baselines;
3. refit population chỉ là full development;
4. one-step feature alignment và common timestamps;
5. baseline formulas cho cả hai protocols;
6. expected 8.592 one-step rows;
7. scheduled origin hour và non-overlap;
8. complete 24-hour target blocks;
9. recursive synthetic history không dùng future actual;
10. per-horizon và pooled metric formulas;
11. no tuning/model-selection code;
12. non-finite prediction/metric làm pipeline dừng;
13. interrupted run không promote outputs;
14. prediction CSV schema và row identity;
15. metric JSON linkage với prediction checksum;
16. figure provenance;
17. notebook không chạy evaluation logic;
18. không import legacy `practice_3` runtime.

## 17. Stop conditions

Dừng và báo Human nếu:

- entry/preflight gate không đạt;
- holdout bị mở trước Human execution;
- model/parameters/features khác model lock;
- one-step common population khác 8.592;
- candidates dùng timestamps/origins khác nhau;
- recursive history chứa actual target sau origin;
- không có complete eligible recursive origin;
- prediction/metric có NaN hoặc infinity;
- cần đổi horizon, origin schedule, registry hoặc missing policy;
- muốn thay model vì holdout result;
- official artifact không truy vết được về upstream identities.

## 18. Completion gate

Phase 7 chỉ `PASS` khi:

- Human-run evaluation hoàn tất;
- opening event xảy ra sau model lock và preflight;
- locked model refit đúng full development;
- one-step và recursive predictions/metrics đầy đủ;
- three candidates dùng common populations;
- three official figures hợp lệ;
- prediction/metric/checksum linkage PASS;
- focused/full tests và notebook clean execution PASS;
- AI technical review PASS;
- Human review kết quả Phase 7.

Sau đó mới được thiết kế Phase 8 — Error & Interpretation Analysis.
