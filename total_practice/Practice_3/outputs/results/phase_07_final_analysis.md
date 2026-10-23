# PHASE 07 — PHÂN TÍCH VÀ KẾT LUẬN CUỐI

## 1. Dataset

Dữ liệu AEP theo giờ có `121273` dòng raw, từ nguồn đã khóa trong Practice 3. Phase 1 đã sắp xếp thời gian, aggregate duplicate timestamp bằng mean và reindex hourly timeline; timezone của nguồn không được cung cấp. Source of truth: [Phase 1 audit](phase_01_data_quality.json).

## 2. Thiết kế feature

Sáu cấu hình lag/rolling được so sánh trên cùng common population. Cấu hình được khóa là `lag_only_p168`, gồm 168 lag và không có rolling feature. Source: [Phase 5 screening](phase_05_screening_results.json).

## 3. CV selection

Candidate được chọn hoàn toàn từ TRAIN-only CV là `xgboost_tuned` với MAE `115.4782` và RMSE `151.3981`. Final test không tham gia chọn model. Source: [Phase 5 CV](phase_05_cv_results.json) và [model lock](phase_05_model_lock.json).

## 4. One-step final-test result

`xgboost_tuned` đạt MAE `113.3278` và RMSE `150.2444` trên 8.592 timestamp. So với Seasonal Naive 24, MAE cải thiện `87.890%`. Source: [one-step metrics](phase_06_one_step_metrics.json).

## 5. Recursive 24-hour result

Trên 350 origin đủ điều kiện, `xgboost_tuned` đạt pooled MAE `547.5021` và pooled RMSE `763.0003`. MAE theo horizon chuyển từ `100.7813` ở horizon 1 thành `702.6645` ở horizon 24; đây là evidence của error accumulation, không được gộp với one-step metric. Source: [multi-step metrics](phase_06_multistep_metrics.json).

## 6. Feature importance

Gain importance được lấy từ đúng tuned XGBoost refit trên full top-level TRAIN. Top features thực tế:

- `lag_1`: rank 1, normalized gain `0.802177`; Consistent with short-term dependence/persistence. Giới hạn: Gain alone does not prove seasonality or causality; correlated features can share importance.
- `lag_166`: rank 2, normalized gain `0.022978`; Consistent with predictive dependence on the value 166 hours earlier. Giới hạn: Gain alone does not prove seasonality or causality; correlated features can share importance.
- `lag_22`: rank 3, normalized gain `0.020535`; Consistent with predictive dependence on the value 22 hours earlier. Giới hạn: Gain alone does not prove seasonality or causality; correlated features can share importance.
- `lag_23`: rank 4, normalized gain `0.013454`; Consistent with predictive dependence on the value 23 hours earlier. Giới hạn: Gain alone does not prove seasonality or causality; correlated features can share importance.
- `lag_21`: rank 5, normalized gain `0.013235`; Consistent with predictive dependence on the value 21 hours earlier. Giới hạn: Gain alone does not prove seasonality or causality; correlated features can share importance.
- `lag_3`: rank 6, normalized gain `0.011900`; Consistent with predictive dependence on the value 3 hours earlier. Giới hạn: Gain alone does not prove seasonality or causality; correlated features can share importance.
- `lag_2`: rank 7, normalized gain `0.010218`; Consistent with predictive dependence on the value 2 hours earlier. Giới hạn: Gain alone does not prove seasonality or causality; correlated features can share importance.
- `lag_142`: rank 8, normalized gain `0.007598`; Consistent with predictive dependence on the value 142 hours earlier. Giới hạn: Gain alone does not prove seasonality or causality; correlated features can share importance.
- `lag_27`: rank 9, normalized gain `0.007117`; Consistent with predictive dependence on the value 27 hours earlier. Giới hạn: Gain alone does not prove seasonality or causality; correlated features can share importance.
- `lag_26`: rank 10, normalized gain `0.005762`; Consistent with predictive dependence on the value 26 hours earlier. Giới hạn: Gain alone does not prove seasonality or causality; correlated features can share importance.

Importance cho biết cách fitted tree sử dụng feature, không chứng minh causality. Correlated lags có thể chia sẻ hoặc làm lệch gain. Xem [full importance table](phase_07_feature_importance.csv) và [Top-20 figure](../figures/phase_07_top20_feature_importance.png).

## 7. Rolling và số lag p

Rolling contribution theo TRAIN-only CV và ngưỡng ±1%:

- p=24: `NEUTRAL`, cải thiện MAE `0.385%`.
- p=72: `NEUTRAL`, cải thiện MAE `0.275%`.
- p=168: `NEUTRAL`, cải thiện MAE `0.277%`.

Trong lag-only family, cấu hình tốt nhất là `lag_only_p168`; trong lag+rolling family là `lag_rolling_p168`. Kết quả không chứng minh rằng tăng p luôn tốt; cần cân bằng metric, variability và training cost.

## 8. Ba câu hỏi bắt buộc

### 8.1 XGBoost và Linear Regression

**THEORETICAL COMPARISON ONLY — Linear Regression was not trained in Practice 3.**

XGBoost học nonlinear threshold và feature interaction trực tiếp nhưng phức tạp hơn, dễ overfit nếu kiểm soát kém và thường yếu khi extrapolate ngoài range đã thấy. Linear Regression đơn giản, coefficient dễ đọc hơn và có thể extrapolate theo linear form, nhưng nonlinear terms/interactions phải được thiết kế rõ. Không có metric Linear Regression để tuyên bố model nào thắng trên AEP.

### 8.2 Ảnh hưởng khi tăng lag p

**EMPIRICAL_RESULT — TRAIN-only CV.**

Lag-only p=24→168 cải thiện mean MAE `6.889%`; lag+rolling p=24→168 cải thiện `6.788%`. Lịch sử dài hơn cải thiện kết quả trong experiment này nhưng tăng feature count và compute cost; đây không phải quy luật đảm bảo cho dataset khác.

### 8.3 XGBoost và ARIMA

**THEORETICAL COMPARISON ONLY — ARIMA was not trained in Practice 3.**

XGBoost linh hoạt với nonlinear relations và nhiều engineered features. ARIMA tự nhiên hơn cho univariate linear autocorrelation, có statistical assumptions rõ và thường hỗ trợ forecast interval. Với exogenous features cần ARIMAX/SARIMAX. Không có ARIMA metric để tuyên bố XGBoost tốt hơn ARIMA trên AEP.

## 9. Limitations

- Source timestamp không có timezone hoặc UTC offset.
- Duplicate timestamps có dấu hiệu DST được aggregate bằng mean, làm mất phân biệt observations gốc.
- Missing timestamps/targets làm giảm supervised và evaluation population.
- Common maximal mask tăng comparison fairness nhưng bỏ thêm usable samples của configuration nhỏ.
- Gain importance không phải causality và bị ảnh hưởng bởi correlated features.
- Rolling one-step giả định actual trước đó được quan sát trước prediction kế tiếp.
- Recursive multi-step có error accumulation; complete daily-block rule làm giảm origin count.
- Linear Regression và ARIMA chưa được train.
- Final test chỉ đại diện giai đoạn lịch sử đã chọn.
- Workflow chỉ đánh giá point forecast, chưa đánh giá prediction interval hoặc uncertainty calibration.
- Không có significance-testing protocol, nên không tuyên bố statistical significance.

## 10. Kết luận

`xgboost_tuned` là model được chọn bằng TRAIN-only CV và đồng thời có MAE thấp nhất quan sát được trong cả one-step và recursive 24-hour final-test protocol. Model phù hợp nhất cho one-step rolling forecast trong phạm vi evidence hiện tại; recursive forecast vẫn có sai số tích lũy lớn hơn và không nên suy rộng ngoài giai đoạn final test. Xem [comparison summary](phase_07_comparison_summary.csv) và [machine-readable summary](phase_07_interpretation_summary.json).
