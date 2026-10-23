# PHASE 06 — FORECASTING & EVALUATION

## 1. Phase Identity

**Phase:** 06  
**Name:** Forecasting & Evaluation  
**Practice:** Practice 3 — Machine Learning Time Series Forecasting  
**Status:** `PASS`
**Implementation authorized:** `YES`
**Approved by:** `Human`  
**Approval date:** `2026-10-16`

## 2. Objective

Mở sealed final test đúng một lần để đánh giá các candidates đã được Phase 5 khóa bằng hai forecasting protocols riêng:

```text
one-step rolling forecast
multi-step recursive 24-hour forecast
```

Phase này phải:

- dựng lại các locked candidates từ Phase 5;
- refit ML models trên full top-level TRAIN mà không dùng test target;
- tạo one-step predictions trên common final-test timestamps;
- tạo recursive multi-step predictions trên common eligible daily origins;
- tính MAE/RMSE riêng cho từng protocol;
- tạo các bảng, prediction artifacts và hình đánh giá có thể truy vết;
- giữ nguyên model, feature và hyperparameter đã khóa sau khi xem test result.

```text
Phase 5 locked candidate registry
    + full TRAIN
    + sealed final test
    ↓
open final test for final evaluation
    ├── rolling one-step evaluation
    └── recursive 24-hour evaluation
    ↓
fixed metrics + fixed figures + evaluation audit
```

Phase 6 không tuning, không chọn lại feature configuration, không thay model lock và không viết final interpretation thay Phase 7.

## 3. Input and Entry Gate

Input bắt buộc:

```text
Phase 3 supervised dataset reconstruction contract
Phase 4 train_indices and sealed test_indices
Phase 5 phase_05_model_lock.json
Phase 5 phase_05_cv_results.json
approved model-training and forecasting configurations
```

Phase 6 chỉ được thực thi khi:

```text
Phase 1 = PASS
Phase 2 = PASS
Phase 3 = PASS
Phase 4 = PASS
Phase 5 = PASS
```

Entry contract:

- `phase_05_model_lock.json` có đầy đủ `locked_candidates` và `cv_selected_candidate`;
- feature configuration đã được chọn bằng TRAIN/CV;
- model parameters, seeds, metrics và fold identity đã được khóa;
- full TRAIN và final-test indices tái tạo đúng Phase 4;
- test chưa được dùng để feature selection, tuning hoặc model selection;
- final-test state là `SEALED` trước execution;
- one-step và multi-step protocols trong tài liệu này chưa bị thay đổi.

Nếu một điều kiện không đạt, không được mở final test.

## 4. Final-test Opening Policy

Final test chỉ được mở sau khi entry gate `PASS`. Evaluation audit phải ghi:

```text
state_before = SEALED
purpose = FINAL_EVALUATION_ONLY
opened_after_phase_05_lock = true
opened_at
locked_candidate_registry_identity
split_identity
state_after = OPENED_FOR_FINAL_EVALUATION
```

Sau khi test được mở:

- không quay lại thay feature definition;
- không đổi candidate parameters;
- không chạy thêm search để cải thiện test metric;
- không loại khoảng test khó;
- không chọn lại CV candidate dựa trên test result;
- không âm thầm thay evaluation population.

Nếu phát hiện implementation bug thật sự, phải dừng, ghi error analysis và xin Human phê duyệt fix plan trước khi chạy lại. Không xem test metric thấp là bug.

## 5. Locked Candidate Registry

Phase 6 đánh giá đúng các candidates đã được khóa từ Phase 5:

```text
seasonal_naive_24
persistence
xgboost_baseline
xgboost_tuned
random_forest
```

Registry phải chứa đủ:

```text
candidate_id
candidate_family
selected_feature_configuration, nếu là ML model
parameters
random_seed, nếu áp dụng
training_data_identity, nếu áp dụng
forecast_protocol_compatibility
CV evidence reference
```

`cv_selected_candidate` là candidate được Phase 5 chọn bằng CV. Phase 6 được báo cáo test ranking nhưng không được sửa `cv_selected_candidate` hoặc gọi test winner là lựa chọn CV.

## 6. Shared Evaluation Contract

Mọi candidate trong cùng protocol phải dùng:

```text
same target definition
same evaluation timestamps/origins
same forecast horizon
same actual values
same metric implementation
same missing-value policy
same output schema
```

ML models chỉ dùng selected feature configuration đã được Phase 5 khóa. Sáu feature configurations không được thử lại trên final test.

Kết quả so sánh `p` và rolling contribution thuộc CV evidence Phase 5. Phase 6 không dùng final test để chọn lại `p`, lag-only hoặc lag + rolling.

## 7. Approved One-step Forecasting Protocol

### 7.1 Definition

Tại mỗi final-test timestamp `t`:

```text
forecast_origin = t - 1 hour
prediction_target = y(t)
available_actual_history <= t - 1 hour
```

Đây là rolling observed-history one-step evaluation. Sau khi actual tại `t` được quan sát, nó có thể trở thành history cho lần dự báo `t+1`.

### 7.2 Model Fitting

Mỗi locked ML candidate được dựng lại và fit đúng một lần trên toàn bộ top-level TRAIN bằng parameters và seed đã khóa.

Không được:

- refit tại từng test timestamp;
- fit bằng test row;
- dùng test target để điều chỉnh model;
- thay hyperparameter sau khi xem prediction.

### 7.3 Feature Availability

One-step feature tại `t` chỉ được chứa target history trước `t`.

Việc feature matrix của các test row sau sử dụng actual test history là hợp lệ duy nhất dưới rolling one-step assumption: actual của thời điểm trước đã được quan sát trước forecast origin kế tiếp.

Implementation phải xác minh:

```text
lag_k(t) = actual or available history at t-k
rolling features at t use history <= t-1
no y(t) or later value appears in X(t)
```

### 7.4 One-step Population

Expected population theo Phase 4:

```text
one_step_test_rows = 8592
test_start = 2017-08-03 00:00:00
test_end = 2018-08-03 00:00:00
```

Tất cả candidates phải tạo prediction trên cùng 8.592 timestamps. Sai lệch phải kích hoạt stop condition; không tự loại thêm row theo từng model.

### 7.5 One-step Baselines

```text
seasonal_naive_24: y_hat(t) = y(t-24)
persistence:       y_hat(t) = y(t-1)
```

Baseline history phải tuân thủ cùng information boundary và common test timestamp population.

## 8. Approved Multi-step Forecasting Protocol

### 8.1 Strategy and Horizon

```text
strategy = recursive
horizon = 24 hours
forecast_frequency = daily
target_frequency = hourly
```

Recursive 24-hour forecasting được chọn để tái sử dụng one-step estimators đã khóa và đánh giá error accumulation trong một ngày.

### 8.2 Forecast-origin Schedule

Scheduled origin là `23:00`, dự báo 24 giờ của ngày kế tiếp:

```text
origin = day D at 23:00
targets = day D+1 at 00:00 ... 23:00
```

Origins cách nhau 24 giờ để target windows không overlap.

Origin đầu có thể nằm ở cuối TRAIN nếu toàn bộ 24 target timestamps của nó thuộc final test. Mọi origin sau sử dụng actual history chỉ đến chính origin đó.

### 8.3 Eligible-origin Rule

Một origin chỉ hợp lệ khi:

- đủ 24 hourly target timestamps liên tục sau origin;
- cả 24 targets nằm trong final-test boundary;
- cả 24 actual targets đều finite để tính metric;
- historical values cần cho selected feature configuration đều có sẵn trước hoặc tại origin;
- lag và rolling features tại mọi recursive step có thể tạo đúng contract;
- cùng origin dùng được cho toàn bộ locked candidates.

Nếu một future target trong block bị thiếu, loại toàn bộ origin khỏi multi-step evaluation. Không tính partial 24-hour block.

Eligible origins phải được tạo một lần rồi dùng chung. Số origin và lý do loại phải được ghi vào evaluation audit; đây là execution result, không được tuyên bố trước khi Phase 1–5 chạy thật.

### 8.4 Recursive Feature Update

Với ML model:

```text
h = 1:
    build features from actual history available at origin
    predict y_hat(origin + 1)

h = 2...24:
    append previous predictions to synthetic history
    rebuild required lag and rolling features
    predict next horizon
```

Quy tắc:

- actual future target sau origin không được đưa vào synthetic history;
- lag features được cập nhật từ actual pre-origin history và recursive predictions;
- rolling mean/std được tính lại từ cùng synthetic history;
- `source_count` và `quality_flag` không trở thành model features;
- model không được refit giữa các horizons hoặc forecast origins.

### 8.5 Multi-step Baselines

Persistence:

```text
y_hat(origin+h) = y(origin), với h=1...24
```

Seasonal Naive 24:

```text
y_hat(origin+h) = y(origin+h-24), với h=1...24
```

Với horizon 24, Seasonal Naive chỉ dùng actual values thuộc ngày trước và đã có sẵn tại forecast origin.

## 9. Approved Metrics

### 9.1 One-step Metrics

Mỗi candidate báo cáo:

```text
MAE
RMSE
n_observations
evaluation_start
evaluation_end
```

Primary one-step comparison metric tiếp tục là MAE; RMSE là metric phụ.

### 9.2 Multi-step Per-horizon Metrics

Cho từng `h = 1...24`:

```text
MAE_h
RMSE_h
n_origins
```

### 9.3 Multi-step Overall Metrics

Tính thêm trên toàn bộ cặp `(origin, horizon)`:

```text
pooled_MAE
pooled_RMSE
n_predictions
```

Vì mọi eligible origin có đủ 24 horizons, pooled MAE tương đương trung bình các `MAE_h`. Pooled RMSE không được thay thế hoặc gọi là trung bình các `RMSE_h`.

Không gộp one-step và multi-step metrics thành một giá trị. Mọi metric phải ghi rõ protocol và horizon scope.

## 10. Approved Visualizations

Tạo đúng ba core figures:

```text
outputs/figures/phase_06_one_step_full_test.png
outputs/figures/phase_06_one_step_first_14_days.png
outputs/figures/phase_06_multistep_error_by_horizon.png
```

### 10.1 Full-test One-step Figure

Hiển thị actual, `cv_selected_candidate` và Seasonal Naive 24 trên toàn bộ one-step test window.

### 10.2 Fixed 14-day Diagnostic Figure

Hiển thị common one-step timestamps nằm trong fixed calendar window:

```text
2017-08-03 00:00:00
→ 2017-08-16 23:00:00
```

Khoảng này được chốt trước execution, không được thay bằng giai đoạn có hình đẹp hơn. Nếu common mask làm thiếu điểm trong cửa sổ, hình phải giữ khoảng trống hoặc thể hiện đúng timestamps còn hợp lệ, không được âm thầm đổi window.

Hình có thể dùng small multiples nếu năm candidate lines làm mất khả năng đọc.

### 10.3 Error-by-horizon Figure

Hiển thị multi-step `MAE_h` và `RMSE_h` theo `h=1...24`, có label model/protocol rõ ràng. Nếu cùng figure làm hai metric khó đọc, dùng hai panels trong cùng file.

Mọi figure phải truy vết được về execution, candidate registry, selected feature configuration và test boundary.

## 11. Required Tasks

### 11.1 Validate Entry Contract

Xác minh Phase 1–5 `PASS`, split identity, model lock, candidate registry, selected feature configuration và test sealing state.

### 11.2 Open Final Test for Evaluation

Chuyển trạng thái từ `SEALED` sang `OPENED_FOR_FINAL_EVALUATION` và ghi audit. Không mở trước entry gate.

### 11.3 Reconstruct and Refit Candidates

Dựng lại forecasting baselines và refit ba ML candidates trên full TRAIN bằng locked parameters.

### 11.4 Execute One-step Forecasting

Tạo aligned predictions cho năm candidates trên common 8.592 test timestamps.

### 11.5 Build Multi-step Origins

Tạo scheduled origins, áp dụng eligibility rules và ghi lý do loại origin.

### 11.6 Execute Recursive Multi-step Forecasting

Tạo 24-hour predictions cho năm candidates trên cùng eligible origins, không dùng future actual target.

### 11.7 Calculate Metrics

Tính one-step, per-horizon và pooled multi-step MAE/RMSE theo Section 9.

### 11.8 Create Fixed Visualizations

Tạo ba core figures theo Section 10, không cherry-pick window.

### 11.9 Record Evaluation Audit

Ghi identities, package versions, candidate specs, population counts, missing/exclusion reasons, timestamp ranges, metric definitions và final-test opening event.

### 11.10 Run Logging, Checkpoint and Resume

Official evaluation phải tạo một local run có định danh:

```text
runs/P6_final_evaluation_<timestamp>_<hash>/
```

Run lưu manifest, configuration snapshot, metadata, log và checkpoint theo candidate/protocol unit. Final-test opening event chỉ được ghi sau khi entry gate đạt. Khi Human dừng execution, run chuyển sang `INTERRUPTED`; resume phải xác minh source, configuration, upstream identities, model lock và split identity trước khi giữ lại unit đã `PASS`.

Không tạo một opening event mới khi resume cùng run. Run `INTERRUPTED` hoặc `FAILED` không được promote output vào `outputs/results/` hoặc `outputs/figures/`.

## 12. Expected Output Contract

### 12.1 One-step Predictions

```text
outputs/results/phase_06_one_step_predictions.csv
```

Long-form schema:

```text
timestamp
candidate_id
actual
prediction
error
absolute_error
squared_error
forecast_protocol
feature_configuration
```

### 12.2 One-step Metrics

```text
outputs/results/phase_06_one_step_metrics.json
```

Phải chứa metrics cho đủ năm candidates trên cùng population.

### 12.3 Multi-step Predictions

```text
outputs/results/phase_06_multistep_predictions.csv
```

Long-form schema:

```text
forecast_origin
horizon
target_timestamp
candidate_id
actual
prediction
error
absolute_error
squared_error
forecast_protocol
feature_configuration
```

### 12.4 Multi-step Metrics

```text
outputs/results/phase_06_multistep_metrics.json
```

Phải chứa per-horizon và pooled metrics cho đủ năm candidates trên cùng eligible origins.

### 12.5 Evaluation Audit

```text
outputs/results/phase_06_evaluation_audit.json
```

Audit là machine-readable evidence cho test-opening state, population alignment, candidate reconstruction và validation checks.

## 13. Persistence and Reproducibility Policy

Source of truth dự kiến:

```text
config/forecasting.json
src/practice_3/analysis/forecasting.py
src/practice_3/analysis/evaluation.py
src/practice_3/visualization/forecast_evaluation.py
tests/test_forecasting.py
tests/test_evaluation.py
```

Results và figures:

```text
outputs/results/phase_06_one_step_predictions.csv
outputs/results/phase_06_one_step_metrics.json
outputs/results/phase_06_multistep_predictions.csv
outputs/results/phase_06_multistep_metrics.json
outputs/results/phase_06_evaluation_audit.json
outputs/figures/phase_06_one_step_full_test.png
outputs/figures/phase_06_one_step_first_14_days.png
outputs/figures/phase_06_multistep_error_by_horizon.png
docs/logs/PHASE_06_EXECUTION.md
```

Prediction artifacts phải được tạo lại từ approved source/configuration và upstream evidence. Không chỉnh tay prediction hoặc metric files.

## 14. Validation Criteria

Phase 6 chỉ `PASS` khi:

- Phase 1–5 đều `PASS` trước khi test được mở;
- candidate registry khớp Phase 5 model lock;
- final-test opening event được audit;
- ba ML models được refit chỉ trên full TRAIN;
- one-step predictions có đúng 8.592 timestamps cho mỗi candidate;
- one-step feature information boundary hợp lệ;
- actual/prediction alignment đúng timestamp và order;
- mọi compared candidates dùng cùng one-step population;
- multi-step origins tuân thủ schedule và eligibility rules;
- mọi compared candidates dùng cùng eligible multi-step origins;
- mỗi eligible origin có đủ horizons 1–24;
- recursive features không dùng actual tương lai;
- baseline formulas đúng cho cả hai protocols;
- predictions, errors và metrics đều finite;
- MAE/RMSE được kiểm tra lại bằng independent test calculation;
- pooled và per-horizon metrics nhất quán;
- ba core figures được tạo từ đúng result artifacts;
- không thay candidate, feature hoặc parameter sau test opening;
- execution reproducible từ source/configuration đã ghi.

## 15. Data Leakage Checks

Không được có:

```text
test target trong model fit hoặc tuning
test-based candidate/feature/hyperparameter change
y(t) hoặc future target trong one-step X(t)
actual target sau origin trong recursive synthetic history
model-specific test timestamps hoặc origins
partial 24-hour block trong multi-step metrics
refit model tại từng test timestamp/origin
cherry-picked visualization window
test winner được ghi đè thành CV-selected candidate
```

## 16. Implementation Scope

Các owner dự kiến sau khi upstream gates đã `PASS`:

```text
config/forecasting.json
src/practice_3/analysis/forecasting.py
src/practice_3/analysis/evaluation.py
src/practice_3/visualization/forecast_evaluation.py
tests/test_forecasting.py
tests/test_evaluation.py
outputs/results/phase_06_one_step_predictions.csv
outputs/results/phase_06_one_step_metrics.json
outputs/results/phase_06_multistep_predictions.csv
outputs/results/phase_06_multistep_metrics.json
outputs/results/phase_06_evaluation_audit.json
outputs/figures/phase_06_one_step_full_test.png
outputs/figures/phase_06_one_step_first_14_days.png
outputs/figures/phase_06_multistep_error_by_horizon.png
docs/logs/PHASE_06_EXECUTION.md
```

Không thuộc phạm vi Phase 6:

```text
README.md
notebook presentation
feature engineering hoặc feature selection mới
hyperparameter tuning mới
thay model lock
feature importance interpretation
final theoretical answers và conclusion
Phase 7 implementation
```

## 17. Stop Conditions

STOP nếu:

- bất kỳ Phase 1–5 nào chưa `PASS`;
- model lock thiếu candidate, parameter hoặc selected feature identity;
- final test đã được dùng trước approved opening event;
- split, schema hoặc population khác upstream contract;
- one-step prediction count khác 8.592 cho bất kỳ candidate nào;
- candidate predictions dùng evaluation timestamps khác nhau;
- scheduled multi-step origins không thể tạo hoặc không còn complete eligible block;
- recursive feature update sử dụng actual tương lai;
- prediction length, shape hoặc timestamp alignment sai;
- xuất hiện unexpected `NaN`, `inf` hoặc non-finite metric;
- candidate reconstruction khác locked parameters;
- model, feature hoặc hyperparameter bị thay sau khi xem test result;
- implementation muốn đổi horizon/strategy mà chưa review lại Phase 4–6;
- result hoặc figure không truy vết được về source artifacts.

## 18. Risks and Trade-offs

- Rolling one-step dùng actual history đã quan sát trong test, nên metric mô tả repeated one-hour-ahead operation chứ không phải dự báo cả năm từ một origin.
- Recursive 24-hour forecast có thể tích lũy sai số vì prediction được đưa ngược vào lag/rolling history.
- Loại toàn bộ block có missing future target làm giảm số multi-step origins nhưng giữ horizon population nhất quán.
- Non-overlapping daily blocks giảm sample count so với overlapping origins nhưng giúp kết quả dễ diễn giải và tránh một timestamp được tính lặp nhiều lần.
- Final-test ranking có thể khác CV ranking; đây là evidence về generalization, không phải lý do để retune.
- Một năm final test chỉ phản ánh giai đoạn lịch sử đó và không chứng minh hiệu năng cho mọi future regime.

## 19. Completion and Downstream Handoff

Phase 6 hoàn thành khi:

```text
final test opened only after Phase 5 lock
five locked candidates evaluated
one-step evaluation complete
recursive 24-hour evaluation complete
MAE/RMSE artifacts validated
three fixed figures created
evaluation audit complete
no post-test model change
Phase 6 validation = PASS
```

Phase 7 chỉ được nhận empirical evidence từ:

```text
Phase 5 CV results and model lock
Phase 6 one-step metrics/predictions
Phase 6 multi-step metrics/predictions
Phase 6 fixed figures
Phase 6 evaluation audit
```

Phase 7 phải phân biệt rõ CV-selected candidate, final-test ranking, one-step result và multi-step result.
