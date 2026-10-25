# PHASE 06 — BASELINE, TRAINING, TUNING & MODEL LOCK

## 1. Phase identity

```text
Project: Practice_3_v2
Phase: 6
Name: Baseline, Training, Tuning & Model Lock
Design status: APPROVED
Human plan approval: GRANTED
Implementation authorization: GRANTED
Execution status: PASS — HUMAN APPROVED
```

## 2. Mục tiêu

Thiết lập forecasting baselines, huấn luyện các Machine Learning candidates, tuning XGBoost và khóa một candidate chỉ bằng one-step development CV.

```text
Phase 5 eligible X/y + five expanding-window folds
→ forecasting baselines
→ fixed ML candidates
→ XGBoost randomized tuning
→ deterministic CV comparison
→ model lock
```

Historical re-evaluation holdout tiếp tục bị khóa. Phase này không materialize holdout X/y, không predict holdout và không tính holdout metric.

## 3. Entry gate

Phase 6 chỉ được chạy khi:

- Phase 5 status `PASS — HUMAN APPROVED`;
- official Phase 5 audit checksum khớp contract;
- có đúng 108.083 eligible development samples;
- X có đúng 22 features theo exact order;
- năm folds đúng Phase 2 và Phase 5;
- eligible X/y finite, aligned, chronological;
- holdout chưa được materialize hoặc evaluate.

## 4. Fair-comparison contract

Mọi baseline và ML candidate phải dùng:

```text
same one-step target definition
same 22-feature schema
same eligible validation timestamps per fold
same metric definitions
same fold aggregation policy
same holdout-sealed state
```

Không thực hiện feature-configuration screening. Legacy Practice 3 có feature population khác nên kết quả legacy không phải official evidence của v2.

## 5. Candidate registry

### 5.1 Persistence

```text
y_hat(T) = lag_1h(T)
```

### 5.2 Seasonal Naive 24

```text
y_hat(T) = lag_24h(T)
```

### 5.3 XGBoost baseline

```text
objective = reg:squarederror
n_estimators = 300
max_depth = 6
learning_rate = 0.05
subsample = 1.0
colsample_bytree = 1.0
min_child_weight = 1
reg_alpha = 0.0
reg_lambda = 1.0
tree_method = hist
random_state = 42
n_jobs = -1
```

### 5.4 Random Forest

```text
n_estimators = 300
max_depth = null
min_samples_split = 2
min_samples_leaf = 1
max_features = 1.0
bootstrap = true
random_state = 42
n_jobs = -1
```

### 5.5 Tuned XGBoost

Tuned candidate dùng 24 parameter combinations và năm approved folds.

Không scaling vì tất cả ML candidates đều là tree-based.

## 6. Metric contract

Fold-level metrics:

```text
MAE = mean(abs(y - y_hat))
RMSE = sqrt(mean((y - y_hat)^2))
validation sample count
training duration for ML candidates
```

CV aggregate:

```text
mean MAE
mean RMSE
MAE standard deviation, ddof=0
RMSE standard deviation, ddof=0
```

Training duration chỉ là operational evidence và không tham gia model selection.

## 7. XGBoost tuning contract

```text
search protocol: deterministic randomized parameter sampling
parameter candidates: 24
folds per candidate: 5
random_state: 42
early stopping: false
primary tuning metric: mean CV MAE
```

Search space:

```text
n_estimators: [300, 500, 800]
max_depth: [3, 5, 7]
learning_rate: [0.03, 0.05, 0.10]
subsample: [0.70, 0.85, 1.00]
colsample_bytree: [0.70, 0.85, 1.00]
min_child_weight: [1, 5, 10]
reg_alpha: [0.0, 0.1, 1.0]
reg_lambda: [1.0, 5.0, 10.0]
```

Custom execution loop được dùng thay cho opaque search execution để hỗ trợ checkpoint sau từng fold/candidate. Parameter sampling vẫn phải deterministic và toàn bộ sampled configurations phải được ghi trước khi training bắt đầu.

## 8. Selection contract

Candidate selection giữ nguyên Phase 0:

1. mean CV MAE thấp nhất;
2. nếu hòa, mean CV RMSE thấp hơn;
3. nếu vẫn hòa, CV MAE standard deviation thấp hơn;
4. nếu vẫn hòa, candidate đơn giản hơn.

Simplicity order được khóa trước training:

```text
persistence
seasonal_naive_24
xgboost_baseline
random_forest
xgboost_tuned
```

Không dùng relative performance tolerance 1%. Chỉ dùng numeric tolerance rất nhỏ để nhận diện kết quả thực sự bằng nhau do floating-point representation.

## 9. Dependency gate

Environment hiện tại chưa có `scikit-learn` và `xgboost`. Khi implementation được phép:

1. bổ sung optional dependency group `modeling` trong `pyproject.toml`;
2. cài package vào `.venv` của Practice 3 v2;
3. ghi exact resolved versions;
4. kiểm tra Python 3.14 compatibility;
5. kiểm tra XGBoost/OpenMP import trên macOS;
6. chạy synthetic fit/predict smoke test.

Nếu dependency hoặc OpenMP lỗi, phải dừng và báo Human; không tự đổi model hoặc environment protocol.

## 10. Execution stages

### Stage 0 — Entry and dependency validation

Kiểm tra upstream identities, environment, sample counts, feature order, folds và holdout-sealed state.

### Stage 1 — Metrics and baselines

Triển khai metric owner dùng lại cho Phase 7 và đánh giá hai baselines trên đúng validation populations.

### Stage 2 — Fixed ML candidates

Chạy XGBoost baseline và Random Forest qua năm folds, ghi metrics/duration sau từng fold.

### Stage 3 — XGBoost tuning

Chạy 24 parameter candidates × 5 folds với checkpoint/resume.

### Stage 4 — Comparison and model lock

Tổng hợp năm candidates, áp dụng selection contract và tạo model lock khi toàn bộ required evidence đã PASS.

### Stage 5 — Official outputs and presentation

Atomic promote JSON/PNG, chạy tests, cập nhật log/status và trình bày notebook từ official artifacts.

Long training không được AI tự bắt đầu. AI chỉ được chuẩn bị dependency gate,
source, tests, preflight và lệnh chạy có thể kiểm tra được, sau đó phải dừng.
Human là người trực tiếp chạy lệnh training trên Terminal. Sau khi Human báo run
đã hoàn tất hoặc bị gián đoạn, AI mới được đọc và review log/checkpoint/result để
thực hiện bước tiếp theo.

## 11. Run, checkpoint and resume

Local run owner:

```text
runs/P6_model_selection_<timestamp>_<execution_identity>/
```

Run chứa:

```text
P6_model_selection_<timestamp>_<execution_identity>.log
run_metadata.json
config_snapshot.json
checkpoint.json
baseline_results.json
xgboost_baseline_results.json
xgboost_tuning_results.json
random_forest_results.json
```

File `.log` là execution-status history dành cho Human theo dõi, dùng format:

```text
<timestamp> | <level> | <message>
```

Log phải ghi tối thiểu phase/stage, candidate, fold, thời điểm bắt đầu/kết thúc,
duration và trạng thái `INTERRUPTED`, `RESUMED`, `FAILED` hoặc `COMPLETED`.
Fold metrics có thể xuất hiện để theo dõi execution nhưng file log không phải
official answer và không thay thế official JSON artifacts.

Checkpoint được ghi atomically sau từng fold/candidate. Khi bị dừng:

- run chuyển thành `INTERRUPTED`;
- fold/candidate đã PASS được giữ;
- fold đang chạy dở được chạy lại;
- không tạo official model lock;
- resume phải xác minh dataset, config, feature, X/y và fold identities.

Resume training cũng phải do Human trực tiếp chạy lệnh trên Terminal; AI không
được tự resume long-running execution.

## 12. Binary-model policy

Phase 6 không persist binary model. Model lock chỉ lưu candidate, reconstruction parameters, seed, package versions, feature schema và CV evidence.

Phase 7 sẽ refit candidate đã khóa trên toàn bộ development trước khi đánh giá holdout. Nếu Phase 7 muốn lưu binary model, phải thảo luận riêng.

## 13. Implementation ownership

```text
config/model_training.json
src/practice_3_v2/analysis/metrics.py
src/practice_3_v2/analysis/model_training.py
tests/test_metrics.py
tests/test_model_training.py
outputs/results/phase_06_cv_results.json
outputs/results/phase_06_model_lock.json
outputs/figures/phase_06_cv_comparison.png
docs/logs/PHASE_06_EXECUTION.md
```

Notebook chỉ đọc official Phase 6 JSON/PNG; không import estimator, fit hoặc predict.

## 14. Official artifact contract

### CV results

```text
outputs/results/phase_06_cv_results.json
```

Phải chứa fold metrics, aggregate metrics, candidate parameters, timing, warnings, package versions và upstream identities.

### Model lock

```text
outputs/results/phase_06_model_lock.json
```

Phải chứa:

```text
candidate registry
selected candidate
selection evidence
locked parameters and seed
feature order and source identities
CV results checksum
package versions
holdout_evaluated = false
binary_model_persisted = false
```

### Figure

```text
outputs/figures/phase_06_cv_comparison.png
```

Figure so sánh mean CV MAE/RMSE và fold variability; figure không được thay thế machine-readable metrics.

## 15. Validation contract

Focused tests phải kiểm tra:

1. dependency import và synthetic fit/predict;
2. Phase 5 identity, sample count, schema và folds;
3. MAE/RMSE formulas trên known arrays;
4. `ddof=0` aggregate formulas;
5. persistence và seasonal-naive formulas;
6. mọi candidate dùng exact shared validation timestamps;
7. no shuffle và no holdout access;
8. fixed seed/config propagation;
9. deterministic 24-configuration parameter sampling;
10. checkpoint atomicity và resume identity;
11. interrupted run không promote official outputs;
12. selection decision order và simplicity tie-break;
13. non-finite prediction/metric làm pipeline dừng;
14. CV artifact và model lock checksum linkage;
15. repeated deterministic selection tạo cùng scientific result;
16. notebook không chạy training/prediction;
17. không import runtime code từ legacy `practice_3`.

Trước bàn giao phải chạy focused tests, full regression suite, notebook clean-kernel execution và `git diff --check`.

## 16. Stop conditions

Dừng Phase 6 và báo Human nếu:

- dependency/XGBoost/OpenMP không hoạt động;
- sample/fold identity khác Phase 5;
- candidate không dùng cùng validation timestamps;
- phát hiện holdout materialization hoặc access;
- prediction/metric có NaN hoặc infinity;
- training cần thay đổi feature schema hoặc temporal protocol;
- interruption/resume identity không xác minh được;
- long training thất bại hoặc kết quả thiếu fold/candidate;
- cần đổi search space, metric, seed hoặc selection rule.

## 17. Completion gate

Phase 6 chỉ `PASS` khi:

- dependency gate PASS;
- baselines và ba ML candidates có đủ five-fold evidence;
- 24 tuning configurations hoàn tất;
- model lock được tạo chỉ bằng development CV;
- holdout vẫn chưa evaluate;
- official JSON/PNG được validate và atomic promote;
- focused tests và full regression suite PASS;
- notebook chỉ đọc official artifacts và chạy sạch;
- execution log/status được đồng bộ;
- Human review kết quả Phase 6.

Sau Phase 6 mới được thiết kế Phase 7 — Final Forecasting & Evaluation.

## 18. Implementation result

```text
Human training run: P6_model_selection_20261025_002459_c83b80bb
Run status: COMPLETED
Completed tasks: 140/140
Tuning configurations: 24/24 × 5 folds
Selected candidate: xgboost_tuned
Mean CV MAE: 108.254067 MW
Mean CV RMSE: 143.850149 MW
CV MAE standard deviation: 3.144269 MW
Historical holdout evaluated: false
Binary model persisted: false
Focused tests: 25/25 PASS
Full regression suite: 107/107 PASS
Notebook clean execution: 19/19 code cells, 0 errors
AI technical review: PASS
Human result review: APPROVED
```

Independent review đã tái tính fold aggregates, xác nhận đủ 140 checkpoint tasks,
đủ 24 tuning candidates, kiểm tra selection candidate #22 và xác minh checksum
link giữa CV results với model lock. Human đã duyệt kết quả Phase 6. Phase 7 được
phép bắt đầu ở bước thảo luận và thiết kế chi tiết; implementation vẫn cần Human
duyệt Phase 7 phase detail.

## 19. Historical supplemental addendum

Sau khi Phase 8 hoàn thành, Human yêu cầu bổ sung Linear Regression benchmark và
lag-`p` sensitivity để trả lời câu hỏi bài tập. Thiết kế nằm tại
`PHASE_06_SUPPLEMENTAL_EXPERIMENTS.md`.

Addendum được thiết kế sau khi historical holdout đã được xem. Vì vậy nó chỉ là
`post_hoc_supplemental_evidence`, không thuộc model selection ban đầu, không được
thay đổi model lock và không sửa official Phase 6 result ở trên.
