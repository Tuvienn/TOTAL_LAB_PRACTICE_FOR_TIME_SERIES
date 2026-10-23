# PHASE 05 — MODEL TRAINING & SELECTION

## 1. Phase Identity

**Phase:** 05  
**Name:** Model Training & Selection  
**Practice:** Practice 3 — Machine Learning Time Series Forecasting  
**Status:** `PASS`
**Implementation authorized:** `YES`
**Approved by:** `Human`  
**Approval date:** `2026-10-16`

## 2. Objective

Huấn luyện, validation và khóa một feature/model configuration bằng dữ liệu TRAIN và năm temporal CV folds đã được Phase 4 phê duyệt.

Phase này phải:

- thiết lập forecasting baselines trước mô hình machine learning;
- so sánh sáu feature configurations trên cùng evaluation population;
- chọn một feature configuration chỉ bằng CV;
- tuning XGBoost trên configuration đã chọn;
- so sánh tuned XGBoost với XGBoost baseline và Random Forest;
- khóa model/configuration trước khi Phase 6 mở final test.

```text
six aligned feature configurations
    + shared TRAIN indices
    + shared temporal CV folds
    ↓
forecasting baselines
    ↓
feature-configuration screening
    ↓
XGBoost tuning + Random Forest comparison
    ↓
CV-only model lock
```

Phase 5 không tính final-test metric, không dùng final test để chọn feature/model và không trình bày kết luận cuối của bài.

## 3. Input and Entry Gate

Input bắt buộc từ Phase 3–4:

```text
six supervised configurations
common timestamp index
shared train_indices
shared cv_fold_indices
sealed test_indices metadata
validation configuration
```

Sáu configurations:

```text
lag_only_p24
lag_only_p72
lag_only_p168
lag_rolling_p24
lag_rolling_p72
lag_rolling_p168
```

Phase 5 chỉ được thực thi khi:

```text
Phase 1 = PASS
Phase 2 = PASS
Phase 3 = PASS
Phase 4 = PASS
```

Entry contract:

- cả sáu configurations dùng cùng common timestamp population;
- cùng `train_indices` và cùng năm CV folds được áp dụng cho mọi configuration;
- chronological order được giữ nguyên;
- `X/y` không chứa `NaN`, `inf` hoặc `-inf`;
- schema, feature order và target alignment hợp lệ;
- final test vẫn ở trạng thái sealed;
- không materialize `X_test/y_test` trong training và selection functions.

## 4. Approved Evaluation Protocol

### 4.1 Forecasting Scope

Phase 5 sử dụng core one-step forecasting protocol đã được Phase 4 hỗ trợ.

Nếu Phase 6 chọn direct multi-step hoặc target construction khác one-step, Phase 4 và Phase 5 phải được mở lại để review gap, label overlap và forecast protocol. Không được tái sử dụng âm thầm kết quả CV one-step cho một protocol khác.

### 4.2 Metrics

```text
primary_selection_metric = MAE
secondary_metric = RMSE
cv_summary = mean ± standard deviation across 5 folds
```

Training time được ghi để tham khảo về chi phí tính toán, nhưng không phải metric chính để tuyên bố model tốt hơn.

### 4.3 Fair-comparison Contract

Mọi candidate trong cùng comparison stage phải dùng:

```text
same training timestamp population
same validation timestamps per fold
same target definition
same one-step forecast protocol
same metric definitions
same fold aggregation rule
```

Không được so sánh các con số được tạo từ population, horizon hoặc split khác nhau như thể chúng cùng một experiment.

## 5. Approved Forecasting Baselines

### 5.1 Primary Baseline — Seasonal Naive 24

```text
y_hat(t) = y(t - 24)
```

Baseline này phản ánh chu kỳ ngày của chuỗi điện năng theo giờ và là forecasting baseline chính để đối chiếu mô hình ML.

### 5.2 Supplementary Baseline — Persistence

```text
y_hat(t) = y(t - 1)
```

Persistence được báo cáo như baseline bổ sung để kiểm tra mức lợi ích so với việc giữ nguyên quan sát gần nhất.

### 5.3 Baseline Alignment

Hai baseline:

- không cần fit hoặc tuning;
- phải dự báo đúng các validation timestamp của từng fold;
- phải dùng target history hợp lệ tại forecast origin;
- được tính cùng MAE/RMSE như ML models;
- không được đánh giá trên final test trong Phase 5.

## 6. Feature-configuration Screening

### 6.1 Screening Model

Chạy cùng một fixed XGBoost baseline trên cả sáu feature configurations và đúng năm shared CV folds.

Approved baseline parameters:

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

`n_jobs=-1` được dùng cho tính thực tiễn. Vì vậy training time chỉ mang tính mô tả; model metrics và lựa chọn phải được tái lập bằng fixed data, folds, parameters và seed.

### 6.2 Selection Rule

Chọn một feature configuration theo thứ tự:

1. CV mean MAE thấp nhất;
2. CV mean RMSE dùng làm tiêu chí phụ khi cần;
3. nếu chênh lệch mean MAE tương đối không quá 1%, chọn configuration có ít features hơn;
4. nếu vẫn hòa, chọn configuration có CV MAE standard deviation thấp hơn;
5. nếu vẫn hòa, chọn configuration có tên đứng trước theo approved configuration order trong Section 3.

Ngưỡng 1% được tính tương đối so với configuration có mean MAE thấp nhất.

Kết quả screening phải ghi đủ cả sáu configurations, không chỉ configuration thắng.

## 7. Approved XGBoost Tuning

Tuning chỉ thực hiện trên feature configuration đã được Section 6 khóa.

```text
search_method = RandomizedSearchCV
n_iter = 24
scoring = {
    mae: negative_mean_absolute_error,
    rmse: negative_root_mean_squared_error
}
cv = shared TimeSeriesSplit from Phase 4
random_state = 42
refit = mae
```

Approved search space:

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

Phase 5 chưa dùng early stopping trong CV. Nếu muốn bổ sung early stopping, cách tạo evaluation set bên trong từng fold phải được thiết kế và Human phê duyệt riêng trước khi thay đổi protocol.

Tuning summary phải lưu candidate parameters, fold metrics, mean/std MAE, mean/std RMSE và selected parameters.

## 8. Approved Random Forest Comparison

Random Forest là comparison model, không tuning trong phạm vi chính của Practice 3.

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

Random Forest phải dùng feature configuration đã chọn và cùng năm CV folds như XGBoost.

## 9. Model-comparison and Lock Rule

Candidates ở model-comparison stage:

```text
seasonal_naive_24
persistence
xgboost_baseline on selected feature configuration
xgboost_tuned on selected feature configuration
random_forest on selected feature configuration
```

Model lock áp dụng cùng decision order:

1. CV mean MAE thấp nhất;
2. CV mean RMSE làm tiêu chí phụ;
3. nếu mean MAE tương đối chênh không quá 1%, ưu tiên model đơn giản hơn theo thứ tự:
   - Seasonal Naive 24;
   - Persistence;
   - XGBoost baseline;
   - Random Forest;
   - tuned XGBoost;
4. nếu vẫn hòa, chọn model có CV MAE standard deviation thấp hơn;
5. nếu vẫn hòa, dùng thứ tự candidate ở trên.

Model lock phải giữ cả candidate registry và candidate được CV chọn:

```text
selected_feature_configuration
locked_candidates:
    seasonal_naive_24
    persistence
    xgboost_baseline
    xgboost_tuned
    random_forest
cv_selected_candidate
parameters and seed for each ML candidate
forecast_protocol
metric_definitions
cv_fold_identity
selection_evidence
final_test_state = SEALED
```

`cv_selected_candidate` là candidate thắng theo decision rule của Phase 5. `locked_candidates` giữ đủ năm cấu hình đã được chốt trước khi mở test để Phase 6 có thể thực hiện model comparison theo yêu cầu bài tập mà không retune sau khi thấy test result.

Sau khi khóa, nếu `cv_selected_candidate` là mô hình ML, Phase 5 được phép refit model đó trên toàn bộ top-level TRAIN để xác minh fit thành công. Nếu selected candidate là forecasting baseline thì không có bước fit. Không được predict hoặc tính metric trên final test. Phase 6 sẽ dựng lại cả năm locked candidates một cách deterministic và refit ba ML candidates trên full TRAIN chỉ để final evaluation.

## 10. Required Tasks

### 10.1 Validate Upstream Contracts

Kiểm tra Phase 3 datasets, Phase 4 indices/folds, schema, alignment, chronology và final-test sealing state.

### 10.2 Evaluate Forecasting Baselines

Tính validation MAE/RMSE của Seasonal Naive 24 và Persistence trên đúng năm folds.

### 10.3 Screen Six Feature Configurations

Chạy fixed XGBoost baseline và chọn một configuration theo Section 6.

### 10.4 Tune XGBoost

Thực hiện approved randomized search chỉ trên selected configuration và chỉ bằng TRAIN/CV.

### 10.5 Evaluate Random Forest

Chạy fixed Random Forest trên cùng selected configuration và folds.

### 10.6 Compare and Lock

Tổng hợp baseline/model CV results, áp dụng deterministic decision rule và tạo model lock cho Phase 6.

### 10.7 Record Audit

Ghi package versions, parameters, seeds, configuration names, fold identities, runtime, warnings và final-test sealing state.

### 10.8 Run Logging, Checkpoint and Resume

Feature screening phải tạo một run cục bộ có định danh dạng:

```text
runs/P5_xgb_screening_<timestamp>_<hash>/
```

Mỗi run chứa:

```text
<run_id>.log
run_metadata.json
config_snapshot.json
checkpoint.json
training_progress.png
fold_duration.png
screening_results.json sau khi hoàn tất
```

Checkpoint phải được ghi atomically sau từng fold. Khi Human dừng bằng `Ctrl+C`, run chuyển sang `INTERRUPTED`, giữ nguyên fold đã `PASS` và không tạo official screening result. Resume phải kiểm tra execution identity trước khi bỏ qua fold đã hoàn thành; fold đang chạy dở được chạy lại từ đầu.

Hai lệnh thực thi:

```bash
python -m practice_3.analysis.model_training --run-screening
python -m practice_3.analysis.model_training --resume-screening runs/<run_id>
```

### 10.9 Tuning Execution Boundary

Tuning dùng đúng `RandomizedSearchCV` đã duyệt và tạo run cục bộ dạng:

```text
runs/P5_xgb_tuning_<timestamp>_<hash>/
```

Dry-run và execution commands:

```bash
python -m practice_3.analysis.model_training --dry-run-tuning
python -m practice_3.analysis.model_training --run-tuning
```

Tuning run ghi `run_metadata.json`, `config_snapshot.json`, `tuning_manifest.json`, `<run_id>.log` và `tuning_results.json` sau khi hoàn tất. `tuning_results.json` phải chứa đủ 24 candidates, fold-level MAE/RMSE, aggregate metrics, selected parameters, full reconstruction parameters, warnings, runtime và final-test sealing state.

`RandomizedSearchCV` nguyên bản không hỗ trợ checkpoint/resume theo từng fold. Nếu Human dừng tuning, run được ghi `INTERRUPTED`, không tạo `tuning_results.json` và lần sau phải chạy lại tuning từ đầu. Không thay bằng custom search protocol nếu chưa có phê duyệt riêng.

### 10.10 Random Forest Execution Boundary

Random Forest comparison tạo run cục bộ dạng:

```text
runs/P5_random_forest_<timestamp>_<hash>/
```

Dry-run, execution và resume commands:

```bash
python -m practice_3.analysis.model_training --dry-run-random-forest --tuning-result runs/<tuning_run_id>/tuning_results.json
python -m practice_3.analysis.model_training --run-random-forest --tuning-result runs/<tuning_run_id>/tuning_results.json
python -m practice_3.analysis.model_training --resume-random-forest runs/<random_forest_run_id> --tuning-result runs/<tuning_run_id>/tuning_results.json
```

Run ghi log, metadata, configuration snapshot, manifest, checkpoint theo từng CV fold và `random_forest_results.json` sau khi hoàn tất. Resume phải xác minh source, configuration, upstream inputs, tuning result và fold identity; fold đã `PASS` không được train lại. Kết quả vẫn chỉ thuộc local run cho đến khi được review và tổng hợp vào official Phase 5 outputs.

### 10.11 Model Comparison, Refit and Lock Boundary

Sau khi Random Forest result qua review, dry-run và execution commands:

```bash
python -m practice_3.analysis.model_training --dry-run-model-lock --tuning-result runs/<tuning_run_id>/tuning_results.json --random-forest-result runs/<random_forest_run_id>/random_forest_results.json
python -m practice_3.analysis.model_training --run-model-lock --tuning-result runs/<tuning_run_id>/tuning_results.json --random-forest-result runs/<random_forest_run_id>/random_forest_results.json
```

Runner tổng hợp đủ năm candidates, kiểm tra cùng folds/population, áp dụng deterministic selection rule và refit candidate được CV chọn trên full TRAIN. Refit không predict, không truy cập final test và không lưu model binary. Chỉ khi refit thành công mới tạo `phase_05_cv_results.json` và `phase_05_model_lock.json`. Nếu bị gián đoạn, không promote official output và Human phải chạy lại bước refit.

## 11. Expected Output Contract

Machine-readable outputs:

```text
outputs/results/phase_05_cv_results.json
outputs/results/phase_05_model_lock.json
```

`phase_05_cv_results.json` tối thiểu chứa:

```text
baseline fold metrics
six-configuration screening metrics
tuning candidates and selected parameters
Random Forest fold metrics
mean/std MAE and RMSE
training-time observations
upstream artifact/config identities
```

`phase_05_model_lock.json` chứa:

```text
locked candidate registry
CV-selected candidate
selected feature configuration
parameters and seeds
forecast/metric protocol identity
selection evidence
final-test state
```

Candidate registry không cho phép Phase 6 thay đổi model family hoặc parameters; nó chỉ cho phép đánh giá một lần các candidates đã được chốt trước test.

## 12. Persistence and Reproducibility Policy

Source of truth dự kiến:

```text
config/model_training.json
src/practice_3/analysis/model_training.py
outputs/results/phase_05_cv_results.json
outputs/results/phase_05_model_lock.json
```

Run history cục bộ:

```text
runs/P5_xgb_screening_<timestamp>_<hash>/
```

`runs/` được Git ignore và không thay thế source of truth. `outputs/results/phase_05_screening_results.json` chỉ được tạo atomically sau khi screening hoàn thành đủ mọi fold và deterministic selection đạt. Run bị `INTERRUPTED` hoặc `FAILED` không được promote.

Không tạo thư mục `models/` và không lưu binary model mặc định trong Phase 5. Khả năng tái tạo đến từ approved inputs, configurations, source code, seeds, package versions và model lock.

Nếu Human yêu cầu lưu binary model, serialization format, version compatibility, file size và Git policy phải được phê duyệt riêng.

## 13. Validation Criteria

Phase 5 chỉ `PASS` khi:

- Phase 1–4 đều `PASS`;
- sáu configurations dùng cùng training/validation timestamp population;
- CV folds khớp tuyệt đối Phase 4;
- Seasonal Naive 24 và Persistence được đánh giá trên đúng fold timestamps;
- screening chạy đủ sáu configurations bằng fixed XGBoost baseline;
- selected feature configuration tuân thủ deterministic rule;
- tuning chỉ dùng selected configuration và TRAIN/CV;
- Random Forest dùng cùng selected configuration và folds;
- tất cả candidates dùng cùng metric definitions;
- results có fold-level metrics và aggregate mean/std;
- parameters, seed và package versions được ghi lại;
- rerun cùng môi trường cho kết quả metric nhất quán trong numeric tolerance được test quy định;
- model lock được tạo từ CV evidence;
- model lock chứa đủ năm `locked_candidates` và một `cv_selected_candidate`;
- parameters, seed và selected feature identity của ba ML candidates được khóa trước final-test opening;
- selected candidate có thể được dựng lại; nếu là ML model thì refit thành công trên full TRAIN;
- final test chưa được predict, evaluate hoặc dùng để điều chỉnh pipeline.

## 14. Data Leakage Checks

Không được có:

```text
final-test metric trong Phase 5
test-informed feature hoặc model selection
test-informed hyperparameter tuning
random KFold hoặc shuffle
configuration-specific validation population
future target trong feature vector
validation data trong fold training
fitted transformation học từ validation/test
manual override model lock dựa trên test result
```

Training function không nhận `X_test` hoặc `y_test`. Test metadata chỉ được dùng để xác nhận sealing và không overlap.

## 15. Implementation Scope

Các owner dự kiến sau khi upstream gates đã `PASS`:

```text
config/model_training.json
src/practice_3/analysis/model_training.py
tests/test_model_training.py
src/practice_3/visualization/training_progress.py
runs/ generated local run history
outputs/results/phase_05_cv_results.json
outputs/results/phase_05_model_lock.json
docs/logs/PHASE_05_EXECUTION.md
```

Dependencies dự kiến khi triển khai:

```text
numpy
pandas
matplotlib
scikit-learn
xgboost
pytest
```

Không tự cài dependency. Nếu dependency chưa có, dừng và xin Human quyết định.

Không thuộc phạm vi Phase 5:

```text
README.md
notebook presentation
final-test prediction hoặc metric
multi-step forecasting implementation
final visualization hoặc conclusion
binary model persistence mặc định
Phase 6–7 implementation
```

## 16. Stop Conditions

STOP nếu:

- bất kỳ Phase 1–4 nào chưa `PASS`;
- dependency cần thiết không tồn tại;
- input schema, common population hoặc folds khác approved contract;
- final test đã bị truy cập để selection/tuning;
- baseline không alignment đúng validation timestamps;
- candidate sử dụng split hoặc metric khác nhau;
- training/tuning phát sinh lỗi hoặc non-finite prediction/metric;
- resume identity không khớp configuration, upstream artifacts, runtime, source hoặc folds của run cũ;
- search vượt giới hạn compute/memory chưa được Human phê duyệt;
- kết quả không deterministic trong tolerance đã định;
- selected candidate không thể được dựng lại hoặc selected ML model không thể refit trên full TRAIN;
- one-step forecasting protocol bị thay đổi mà chưa review lại Phase 4–5.

## 17. Risks and Trade-offs

- Chạy fixed XGBoost trên sáu configurations rồi tuning 24 candidates có chi phí tính toán đáng kể.
- `n_jobs=-1` giảm thời gian chạy nhưng training-time comparison phụ thuộc tài nguyên máy.
- Common maximal mask tạo comparison công bằng nhưng bỏ các sample mà configuration nhỏ hơn có thể sử dụng.
- Quy tắc ưu tiên model đơn giản trong phạm vi chênh MAE 1% là quyết định thực dụng, không chứng minh hai model tương đương thống kê.
- CV one-step performance không tự động đại diện cho direct multi-step forecasting.
- Random Forest với nhiều lag features có thể dùng nhiều RAM; nếu vượt tài nguyên phải dừng, không âm thầm giảm cấu hình.

## 18. Completion and Downstream Handoff

Phase 5 hoàn thành khi:

```text
forecasting baselines evaluated on CV
one feature configuration locked
XGBoost baseline evaluated
XGBoost tuning completed
Random Forest evaluated
five candidate configurations locked before final-test opening
one CV-selected candidate recorded
final test remains sealed
Phase 5 validation = PASS
```

Phase 6 chỉ được nhận:

```text
phase_05_model_lock.json
locked candidate registry
cv_selected_candidate
approved model-training configuration
reproducible training source
sealed final-test indices from Phase 4
```

Phase 6 được final-evaluate cả năm locked candidates nhưng không được thay feature configuration, hyperparameters, candidate registry hoặc `cv_selected_candidate` sau khi nhìn final-test result.
