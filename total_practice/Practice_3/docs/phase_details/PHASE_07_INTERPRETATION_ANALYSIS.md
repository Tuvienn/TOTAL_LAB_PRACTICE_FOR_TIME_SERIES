# PHASE 07 — INTERPRETATION & FINAL ANALYSIS

## 1. Phase Identity

**Phase:** 07  
**Name:** Interpretation & Final Analysis  
**Practice:** Practice 3 — Machine Learning Time Series Forecasting  
**Status:** `PASS`
**Implementation authorized:** `YES`
**Approved by:** `Human`  
**Implementation-plan approval date:** `2026-10-23`

## 2. Objective

Tổng hợp và diễn giải toàn bộ empirical evidence của Practice 3, phân tích feature importance, trả lời ba câu hỏi bắt buộc và tạo final analysis có thể truy vết về output thật.

Phase này phải:

- phân biệt CV evidence với final-test evidence;
- phân biệt one-step với multi-step results;
- lấy feature importance từ đúng tuned XGBoost và đúng feature names;
- phân tích important lags, rolling contribution và tác động của số lag `p`;
- so sánh forecasting baselines và locked ML candidates;
- trả lời ba câu hỏi bắt buộc, ghi rõ empirical hay theoretical;
- tạo final conclusion không vượt quá bằng chứng execution;
- ghi đầy đủ limitations.

```text
Phase 5 CV evidence + model lock
    + Phase 6 final-test evidence
    + approved feature/model definitions
    ↓
feature importance
    + controlled comparisons
    + required questions
    ↓
traceable final analysis
```

Phase 7 không tuning, không chọn lại model/feature, không tạo test experiment mới và không thay đổi upstream artifacts.

## 3. Input and Entry Gate

Input bắt buộc:

```text
Phase 1 data-quality audit
Phase 2 feature-quality audit
Phase 3 supervised-data audit
Phase 4 split audit
Phase 5 CV results and model lock
Phase 6 predictions, metrics, figures and evaluation audit
approved source/configuration required to reconstruct tuned XGBoost
```

Phase 7 chỉ được thực thi khi:

```text
Phase 1 = PASS
Phase 2 = PASS
Phase 3 = PASS
Phase 4 = PASS
Phase 5 = PASS
Phase 6 = PASS
```

Entry contract:

- Phase 5 `locked_candidates` và `cv_selected_candidate` hợp lệ;
- selected feature configuration và model parameters đã khóa;
- Phase 6 final-test population, candidate registry và metrics đã validation;
- one-step và multi-step evidence có protocol identity riêng;
- result artifacts có provenance và không bị chỉnh tay;
- CV results chưa bị ghi đè bởi test ranking;
- Linear Regression và ARIMA chưa được tuyên bố là experiment nếu chúng không được train thật.

## 4. Evidence Classification Policy

Mọi nhận định trong final analysis phải thuộc một trong bốn loại:

```text
EMPIRICAL_RESULT
DATA_OBSERVATION
THEORETICAL_EXPLANATION
UNRESOLVED_LIMITATION
```

### 4.1 Empirical Result

Chỉ dùng khi có output execution hỗ trợ, ví dụ:

- CV MAE/RMSE của sáu feature configurations;
- Phase 5 candidate comparison;
- one-step final-test metrics;
- recursive 24-hour metrics;
- XGBoost gain importance.

### 4.2 Data Observation

Dùng cho fact từ data audit, ví dụ:

- raw row count;
- duplicate timestamps;
- missing timestamps;
- time boundary;
- timezone-naive source.

### 4.3 Theoretical Explanation

Dùng cho kiến thức mô hình không được trực tiếp thử trong Practice 3, đặc biệt Linear Regression và ARIMA.

### 4.4 Unresolved Limitation

Dùng cho giới hạn chưa được giải quyết hoặc không thể suy luận từ execution hiện tại.

Mỗi bảng, hình và empirical claim phải chỉ được source artifact hỗ trợ. Không chuyển theoretical explanation thành empirical result bằng cách diễn đạt mơ hồ.

## 5. Approved Feature-importance Protocol

### 5.1 Model and Population

Primary importance model:

```text
candidate_id = xgboost_tuned
feature_configuration = Phase 5 selected feature configuration
importance_type = gain
fit_population = full top-level TRAIN
```

Tuned XGBoost được dùng vì đây là XGBoost configuration hoàn chỉnh sau tuning và đáp ứng yêu cầu phân tích feature importance của bài.

Nếu không lưu model binary, Phase 7 được phép:

1. dựng lại `xgboost_tuned` từ Phase 5 model lock;
2. tái tạo selected training dataset từ approved source/configuration;
3. refit trên full TRAIN bằng đúng parameters và seed đã khóa;
4. lấy importance mà không dùng final test.

Refit này chỉ phục vụ tái tạo locked model và importance; không phải model selection hoặc tuning mới.

### 5.2 Gain Extraction

Lấy raw gain bằng XGBoost Booster API:

```text
get_score(importance_type="gain")
```

Feature không xuất hiện trong split tree phải được thêm vào bảng với:

```text
gain = 0
```

Feature names phải map đúng ordered feature list của selected configuration. Không dựa vào vị trí `f0`, `f1`, ... mà không xác minh mapping.

Normalized gain:

```text
normalized_gain(feature) = gain(feature) / sum(all feature gains)
```

STOP nếu tổng gain bằng 0 hoặc mapping không đầy đủ.

### 5.3 Feature-importance Output Schema

```text
feature
feature_group
gain
normalized_gain
rank
candidate_id
feature_configuration
importance_type
training_population
```

`feature_group` chỉ nhận:

```text
lag
rolling
```

Rows được sort theo `gain` giảm dần; khi hòa, sort theo approved feature order để deterministic.

### 5.4 Interpretation Boundary

Feature importance chỉ phản ánh cách fitted model sử dụng feature trong configuration đã chạy.

Không được:

- diễn giải importance thành causality;
- gọi một lag là nguyên nhân làm thay đổi điện năng;
- khẳng định seasonality chỉ từ importance;
- bỏ qua correlated-feature limitation;
- so importance giữa hai model như cùng scale nếu chưa có protocol chuẩn hóa phù hợp.

## 6. Important-lag Analysis

Phân tích các lag đứng đầu theo gain và liên hệ có điều kiện:

```text
lag_1   → short-term dependence / persistence
lag_24  → pattern consistent with daily recurrence
lag_168 → pattern consistent with weekly recurrence
```

Chỉ dùng cụm từ `consistent with`, không dùng importance riêng lẻ để chứng minh daily/weekly seasonality.

Với mỗi important lag phải ghi:

```text
rank
gain / normalized_gain
feature configuration
possible time-series interpretation
interpretation limitation
```

Nếu `lag_24` hoặc `lag_168` không quan trọng trong output thật, không được viết trước rằng chúng quan trọng.

## 7. Rolling-feature Contribution Analysis

Dùng Phase 5 CV screening, so sánh ba cặp trên cùng `p`:

```text
lag_only_p24  vs lag_rolling_p24
lag_only_p72  vs lag_rolling_p72
lag_only_p168 vs lag_rolling_p168
```

Relative CV MAE improvement:

```text
improvement_% =
    (lag_only_mean_MAE - lag_rolling_mean_MAE)
    / lag_only_mean_MAE
    × 100
```

Approved classification:

```text
improvement >  1%  → HELPFUL
-1% <= improvement <= 1% → NEUTRAL
improvement < -1% → HARMFUL
```

RMSE, fold standard deviation và training time được dùng làm supporting context, không thay primary MAE classification.

Không chạy lại sáu feature configurations trên final test. Rolling conclusion phải ghi rõ đây là CV evidence.

## 8. Lag-p Analysis

Phân tích `p = 24, 72, 168` riêng trong từng feature family:

```text
lag-only family
lag + rolling family
```

Cho mỗi configuration phải theo dõi:

```text
feature_count
CV mean/std MAE
CV mean/std RMSE
training_time
```

Không so `p` bằng population khác nhau; Phase 5 common-mask contract tiếp tục là điều kiện bắt buộc.

Kết luận phải đánh giá:

- lịch sử dài hơn có cải thiện metric không;
- mức cải thiện có vượt ngưỡng 1% không;
- variability giữa folds thay đổi ra sao;
- compute cost tăng ra sao;
- có dấu hiệu diminishing return hoặc degradation không.

Không kết luận càng nhiều lag luôn tốt hơn.

## 9. Model-comparison Analysis

### 9.1 CV Evidence

Dùng Phase 5 để báo cáo:

```text
five locked candidates
CV mean/std MAE
CV mean/std RMSE
cv_selected_candidate
selection rule
```

### 9.2 Final-test Evidence

Dùng Phase 6 để báo cáo riêng:

```text
one-step MAE/RMSE
recursive 24-hour pooled MAE/RMSE
per-horizon MAE/RMSE
final-test ranking
```

Không gộp one-step và multi-step metrics. Không gọi test winner là CV-selected candidate nếu hai candidate khác nhau.

### 9.3 Relative Improvement

Với metric cần so sánh:

```text
relative_improvement_% =
    (reference_metric - candidate_metric)
    / reference_metric
    × 100
```

Reference chính:

```text
Seasonal Naive 24
```

Persistence được giữ như supplementary baseline. Các comparison cần thiết khác:

```text
xgboost_tuned vs xgboost_baseline
xgboost_tuned vs random_forest
cv_selected_candidate vs Seasonal Naive 24
```

Khi nói một candidate tốt hơn phải ghi:

- metric nào;
- protocol nào;
- evaluation population nào;
- chênh lệch tuyệt đối và tương đối;
- limitation nào còn tồn tại.

Không tuyên bố statistical significance vì Practice 3 chưa có significance-testing protocol.

## 10. Required Question 1 — XGBoost vs Linear Regression

Header bắt buộc:

```text
THEORETICAL COMPARISON ONLY — Linear Regression was not trained in Practice 3
```

Nội dung tối thiểu:

| Khía cạnh | XGBoost | Linear Regression |
|---|---|---|
| Quan hệ | Học phi tuyến và threshold | Chủ yếu tuyến tính nếu không tự tạo nonlinear terms |
| Interaction | Học interaction giữa features | Phải thiết kế interaction rõ ràng |
| Scaling | Tree model thường ít nhạy với scaling | Scaling hữu ích cho regularization/numerical behavior |
| Interpretability | Importance không phải coefficient/causality | Coefficient dễ đọc hơn nhưng phụ thuộc assumptions |
| Extrapolation | Tree boosting thường yếu ngoài range đã thấy | Có thể extrapolate theo linear form |
| Complexity | Nhiều hyperparameters, dễ overfit nếu kiểm soát kém | Đơn giản hơn, baseline dễ kiểm tra |

Không tạo Linear Regression metric hoặc tuyên bố XGBoost thắng trên dataset này nếu model chưa được chạy theo cùng protocol.

## 11. Required Question 2 — Effect of Increasing Lag p

Đây là câu hỏi có empirical evidence từ Phase 5.

Câu trả lời phải:

1. trình bày kết quả `p=24,72,168` cho lag-only;
2. trình bày kết quả `p=24,72,168` cho lag + rolling;
3. nêu feature count và training time;
4. chỉ ra configuration tốt nhất theo approved CV rule;
5. nêu trade-off giữa lịch sử dài hơn, correlation, compute cost và generalization;
6. không dùng final-test ranking để chọn lại `p`.

Nếu metric không cải thiện đơn điệu, phải trình bày đúng kết quả đó.

## 12. Required Question 3 — XGBoost vs ARIMA

Header bắt buộc:

```text
THEORETICAL COMPARISON ONLY — ARIMA was not trained in Practice 3
```

Nội dung tối thiểu:

| Trường hợp | XGBoost | ARIMA |
|---|---|---|
| Quan hệ phi tuyến | Phù hợp hơn khi feature interactions quan trọng | Không phải thế mạnh chính của ARIMA chuẩn |
| Nhiều engineered/exogenous features | Linh hoạt | Cần ARIMAX/SARIMAX và specification phù hợp |
| Univariate linear autocorrelation | Có thể dùng nhưng cần feature engineering | Là trường hợp tự nhiên của ARIMA |
| Statistical interpretation | Hạn chế hơn | Rõ hơn qua AR/MA/differencing assumptions |
| Forecast uncertainty | Không có sẵn từ point XGBoost workflow này | Statistical models thường hỗ trợ interval tự nhiên hơn |
| Data/compute | Hợp với dữ liệu lớn và nonlinear patterns | Có thể hiệu quả với chuỗi nhỏ, cấu trúc rõ |

Không tuyên bố XGBoost tốt hơn ARIMA trên AEP dataset vì ARIMA chưa được thực nghiệm trong scope đã duyệt.

## 13. Final Conclusion Contract

Final conclusion phải theo đúng thứ tự:

1. **Dataset:** source, target, time range và data-quality treatments.
2. **Feature design:** lag `p`, rolling windows và common comparison population.
3. **CV selection:** selected feature configuration và `cv_selected_candidate`.
4. **One-step result:** exact MAE/RMSE và baseline improvement.
5. **Multi-step result:** recursive horizon 24, pooled metric và error-by-horizon behavior.
6. **Feature importance:** tuned XGBoost top features và interpretation boundary.
7. **Rolling and lag-p findings:** kết luận từ Phase 5 CV evidence.
8. **Required questions:** empirical/theoretical labels đúng.
9. **Limitations:** đầy đủ và cụ thể.
10. **Final suitability statement:** model hữu ích ở protocol nào, không suy rộng ngoài evidence.

Nếu final-test winner khác `cv_selected_candidate`, conclusion phải ghi cả hai:

```text
selected by CV = ...
best observed final-test metric = ...
```

Không thay model lock hoặc viết lại lịch sử selection.

## 14. Required Limitations

Final analysis tối thiểu phải ghi:

- source timestamp không có timezone hoặc UTC offset;
- duplicate timestamps có dấu hiệu DST đã được aggregate bằng mean, làm mất phân biệt observations gốc;
- missing timestamps/targets làm giảm supervised và evaluation population;
- common maximal mask ưu tiên comparison fairness nhưng bỏ thêm usable samples của configurations nhỏ;
- gain importance không phải causality;
- correlated lag/rolling features có thể chia sẻ hoặc làm lệch importance;
- rolling one-step giả định actual trước đó được quan sát trước prediction kế tiếp;
- recursive multi-step có error accumulation;
- non-overlapping complete daily blocks làm giảm multi-step sample count;
- Linear Regression và ARIMA chưa được train;
- final test chỉ đại diện giai đoạn lịch sử được chọn;
- point-forecast workflow hiện tại chưa đánh giá prediction interval hoặc uncertainty calibration.

## 15. Required Tasks

### 15.1 Validate Evidence Chain

Xác minh Phase 1–6 `PASS`, artifact identities, candidate registry, metric protocols và output provenance.

### 15.2 Reconstruct Tuned XGBoost for Importance

Nếu cần, refit locked `xgboost_tuned` trên full TRAIN, map feature names và lấy gain importance.

### 15.3 Build Feature-importance Artifacts

Tạo full importance table và top-20 plot theo approved protocol.

### 15.4 Build Controlled Comparison Summary

Tổng hợp CV feature/model comparisons và Phase 6 final-test comparisons mà không trộn protocol.

### 15.5 Answer Required Questions

Trả lời ba câu hỏi theo Sections 10–12 và gắn đúng empirical/theoretical label.

### 15.6 Write Final Analysis

Viết human-readable Markdown theo Section 13, dẫn tới upstream JSON/CSV/figures và không chứa số liệu không truy vết được.

### 15.7 Record Interpretation Audit

Ghi evidence sources, formula, thresholds, model/feature identity, validation results và unresolved limitations.

## 16. Expected Output Contract

### 16.1 Feature Importance

```text
outputs/results/phase_07_feature_importance.csv
outputs/figures/phase_07_top20_feature_importance.png
```

CSV phải chứa toàn bộ selected features, kể cả feature có gain bằng 0. Figure chỉ hiển thị top 20 để giữ khả năng đọc.

### 16.2 Comparison Summary

```text
outputs/results/phase_07_comparison_summary.csv
```

Schema tối thiểu:

```text
evidence_scope
forecast_protocol
comparison_group
candidate_or_configuration
MAE
RMSE
MAE_std_if_available
RMSE_std_if_available
training_time_if_available
relative_improvement_percent
reference_id
source_artifact
```

### 16.3 Machine-readable Interpretation Summary

```text
outputs/results/phase_07_interpretation_summary.json
```

Phải chứa:

```text
evidence inventory
CV selection facts
final-test facts
important features
rolling classification
lag-p conclusion
required-question labels
limitations
validation checks
```

### 16.4 Human-readable Final Analysis

```text
outputs/results/phase_07_final_analysis.md
```

Markdown này phải liên kết tương đối tới các source artifacts và figures đã tạo. Nó là result artifact của Phase 7, chưa thay thế README hoặc presentation notebook.

## 17. Visualization Contract

Core figure duy nhất của Phase 7:

```text
outputs/figures/phase_07_top20_feature_importance.png
```

Figure phải:

- dùng horizontal bar chart;
- sort để feature quan trọng nhất dễ nhận biết;
- hiển thị normalized gain hoặc raw gain với label rõ;
- ghi `xgboost_tuned`, selected feature configuration và `importance_type=gain`;
- không gọi importance là causal effect;
- có kích thước/label đọc được ở notebook và report.

Không tạo thêm biểu đồ trang trí nếu không trả lời câu hỏi phân tích cụ thể.

## 18. Validation Criteria

Phase 7 chỉ `PASS` khi:

- Phase 1–6 đều `PASS`;
- evidence inventory đầy đủ và truy vết được;
- tuned XGBoost reconstruction khớp locked parameters/feature configuration;
- importance mapping bao phủ toàn bộ ordered feature list;
- feature không dùng có gain bằng 0 thay vì bị bỏ;
- normalized gain finite và tổng xấp xỉ 1 trong numeric tolerance;
- important-lag claims khớp importance artifact;
- rolling classification dùng đúng paired CV comparisons và ngưỡng 1%;
- lag-p analysis dùng common population và Phase 5 CV results;
- model comparison tách CV, one-step và multi-step;
- relative-improvement formulas được kiểm tra lại;
- `cv_selected_candidate` không bị ghi đè bởi test winner;
- Linear Regression và ARIMA có label theoretical-only;
- ba câu hỏi bắt buộc được trả lời đủ;
- mọi exact number trong final analysis có source artifact;
- required limitations được ghi đầy đủ;
- top-20 figure được tạo từ feature-importance CSV;
- Markdown links tới result artifacts tồn tại;
- outputs deterministic và reproducible từ approved inputs.

## 19. Data-leakage and Claim-integrity Checks

Không được có:

```text
new test-based tuning hoặc feature selection
test winner thay thế cv_selected_candidate
CV và final-test metric bị trộn
one-step và multi-step metric bị gộp
importance lấy từ test-fitted model
feature-name mapping theo giả định không kiểm tra
causal claim từ gain importance
Linear Regression/ARIMA metric không có execution
statistical-significance claim không có test protocol
number hoặc conclusion không có source artifact
```

## 20. Implementation Scope

Các owner dự kiến sau khi Phase 1–6 `PASS`:

```text
src/practice_3/analysis/interpretation.py
src/practice_3/visualization/interpretation_plots.py
tests/test_interpretation.py
outputs/results/phase_07_feature_importance.csv
outputs/results/phase_07_comparison_summary.csv
outputs/results/phase_07_interpretation_summary.json
outputs/results/phase_07_final_analysis.md
outputs/figures/phase_07_top20_feature_importance.png
docs/logs/PHASE_07_EXECUTION.md
```

Không thuộc phạm vi Phase 7:

```text
README.md
presentation notebook
new model training for selection
new hyperparameter search
Linear Regression experiment
ARIMA experiment
SHAP dependency hoặc SHAP analysis
new final-test experiment
prediction interval implementation
upstream artifact modification
```

README và notebook chỉ được cập nhật ở bước presentation/documentation sau khi Phase 7 đã `PASS`.

## 21. Stop Conditions

STOP nếu:

- bất kỳ Phase 1–6 nào chưa `PASS`;
- upstream artifacts thiếu, stale hoặc mâu thuẫn;
- CV/model/test comparisons không cùng approved population/protocol;
- feature names không map đầy đủ tới tuned XGBoost;
- gain extraction thất bại hoặc tổng gain bằng 0;
- refitted tuned XGBoost khác locked parameters;
- importance vô tình dùng test-fitted/tuned model;
- exact metric trong narrative không khớp source artifact;
- empirical và theoretical evidence bị trộn;
- one-step và multi-step result bị gộp không nhãn;
- required questions hoặc limitations chưa đầy đủ;
- Linear Regression hoặc ARIMA được mô tả như đã chạy;
- conclusion mâu thuẫn CV/test metrics;
- link trong final analysis trỏ tới artifact không tồn tại;
- cần mở rộng dependency/model/metric ngoài approved scope.

## 22. Risks and Trade-offs

- Gain importance có bias và bị ảnh hưởng bởi correlated features; rank không đại diện causal effect.
- Refit deterministic phụ thuộc package version và implementation stability; provenance phải ghi rõ.
- Ngưỡng 1% cho rolling contribution là decision rule thực dụng, không phải kiểm định thống kê.
- CV-selected candidate và final-test winner có thể khác nhau; final analysis phải giữ hai khái niệm riêng.
- Multi-step pooled metrics có thể che khác biệt theo horizon, nên per-horizon evidence phải được giữ.
- Theoretical comparison với Linear Regression/ARIMA không thay thế empirical benchmark.
- Final analysis súc tích có thể bỏ chi tiết; machine-readable artifacts vẫn là source of truth.

## 23. Completion Condition

Phase 7 hoàn thành khi:

```text
Phase 1–6 evidence validated
feature importance generated and validated
important lags interpreted with limitations
rolling contribution classified from CV
lag-p effect analyzed from CV
CV and final-test model comparisons separated
three required questions answered
all limitations recorded
machine-readable summary created
human-readable final analysis created
Phase 7 validation = PASS
```

Sau Phase 7 `PASS`, project mới sẵn sàng bước presentation/documentation:

```text
build final notebook presentation
update README and navigation links
perform clean-kernel notebook execution
run final repository readiness review
```
