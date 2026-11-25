# EXERCISE 06 — AIRPASSENGERS SARIMA EXTENSION

## 1. Exercise Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_06
Topic: AirPassengers ARIMA Baseline and SARIMA Extension
Dataset: AirPassengers
Frequency: Monthly
Seasonal period: s = 12
Chronological split: 80% train / 20% test
Model training required: YES, after confirmation
Specification status: CONFIRMED_FOR_IMPLEMENTATION
Implementation authorized: YES
Direct data dependency on E01–E05: NO
Process gate: EXERCISE_05_COMPLETED
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_06_execution.md
```

Specification này định nghĩa yêu cầu khoa học của E06. E06 đã được xác nhận để
triển khai; completion vẫn phụ thuộc clean-kernel validation và execution evidence.

## 2. Objective

Mục tiêu của bài tập:

- validate AirPassengers và nhận diện annual seasonality;
- tạo chronological holdout riêng, không dùng boundary của Dataset 1;
- chạy ADF trên original training series;
- kiểm chứng regular và seasonal differencing;
- xác định candidate `(p,q,P,Q)` từ training-only ACF/PACF evidence;
- fit một non-seasonal ARIMA baseline và một SARIMA với `s = 12`;
- kiểm tra convergence và residuals của hai model;
- forecast cùng test horizon;
- so sánh ARIMA và SARIMA bằng MAE/RMSE trên cùng observations;
- kết luận tác động của seasonal modeling trong phạm vi holdout hiện tại.

E06 không được dùng model order, transformation, fitted model hoặc metrics của
Dataset 1 làm kết quả cho AirPassengers.

## 3. Input Contract

```text
File: datasets/raw/airline-passengers.csv
Dataset identity: AirPassengers — Monthly Airline Passengers
Timestamp column: Month
Timestamp format: YYYY-MM
Target column: Passengers
Expected observations: 144
Expected date range: 1949-01 through 1960-12
Frequency: monthly start (MS)
Seasonal period: 12
Expected missing target values: 0
Expected duplicate timestamps: 0
Expected missing monthly intervals: 0
Raw SHA-256: 8cb51be753a718d9be5d76d7e238cc224792754676adc21faa59e954b0201621
```

Raw file là immutable source evidence. Parsing, sorting, splitting, scale
transformation và differencing chỉ được thực hiện trên working objects hoặc confirmed
derived artifacts.

## 4. Relationship with Core Practice

```text
E01–E05: Core Practice on datasets/raw/a10.csv
E06: Advanced Extension on datasets/raw/airline-passengers.csv
Direct result dependency: NO
Reusable method/code dependency: YES, when compatible
Recommended execution order: E04 → E05 → E06
```

E06 phải xác định lại train/test boundary, scale, `d`, `D`, `p`, `q`, `P`, `Q` và
model results từ AirPassengers evidence. E06 completion không thay thế trạng thái
của E01–E05.

## 5. Required Steps

1. Verify E05 completion, E06 confirmation state và reusable interfaces.
2. Load, inspect và validate AirPassengers schema/time index/data quality.
3. Tạo chronological 80/20 split, không shuffle, rồi seal test set.
4. Vẽ training series để nhận diện trend, seasonality và variance behavior.
5. Chốt raw hoặc natural-log scale chỉ từ training evidence.
6. Chạy ADF trên original training series ở confirmed scale.
7. Thực hiện và đánh giá regular differencing `d = 1` khi evidence yêu cầu.
8. Thực hiện và đánh giá seasonal differencing `D = 1, s = 12` khi evidence yêu cầu.
9. Validate NaN handling, timestamp alignment và stationarity sau transformation.
10. Tính ACF/PACF trên stationary transformed training series.
11. Đề xuất số lượng nhỏ ARIMA/SARIMA candidates có rationale cho `(p,q,P,Q)`.
12. Fit non-seasonal ARIMA baseline trên AirPassengers train.
13. Fit SARIMA `(p,d,q)(P,D,Q,12)` trên cùng train và analysis scale.
14. Kiểm tra convergence, AIC/BIC và residual diagnostics của cả hai model.
15. Khóa model/evaluation setup trước khi mở test set.
16. Forecast đúng test horizon và validate forecast/test index alignment.
17. Tính MAE/RMSE trên cùng test observations; MAPE chỉ là metric bổ sung.
18. So sánh model và kết luận từ actual evidence.

## 6. Scientific Method

### 6.1. Chronological Holdout

```text
Split method: chronological 80/20
Shuffle: NO
Expected training observations: 115
Expected training period: 1949-01 through 1958-07
Expected test observations: 29
Expected test period: 1958-08 through 1960-12
Forecast horizon: 29 months
```

ADF, scale decision, differencing, ACF/PACF, order selection và fitting chỉ dùng
training data. Test values chỉ được mở ở final evaluation.

### 6.2. Stationarity and Differencing

ADF kiểm tra null hypothesis rằng chuỗi có unit root. Với `alpha = 0.05`:

```text
p-value <= 0.05 → reject H0 → evidence supports stationarity
p-value > 0.05 → fail to reject H0 → insufficient stationarity evidence
```

`d = 1` và `D = 1` là gợi ý của đề, không phải kết luận mặc định. E06 phải kiểm tra
evidence của regular differencing, seasonal differencing và combined transformed
series; không over-difference để đạt p-value mong muốn.

### 6.3. Scale Decision

Nếu training evidence cho thấy variance tăng cùng level, E06 được phép đánh giá
natural-log scale. Khi log được chọn:

- ARIMA và SARIMA phải dùng cùng scale;
- inverse-transform policy phải được ghi rõ và áp dụng nhất quán;
- forecast phải trở lại target scale trước khi so sánh với test;
- không được silently đổi scale sau khi xem test performance.

### 6.4. Order Identification

ACF/PACF trên stationary transformed training series cung cấp evidence để đề xuất
`p`, `q`, `P`, `Q`. Các lag 12, 24 và 36 phải được inspect. Candidate order chỉ là
provisional cho đến khi có fitting, convergence và residual evidence.

### 6.5. Model Comparison

ARIMA và SARIMA phải dùng cùng:

```text
AirPassengers training set
confirmed analysis scale
test boundary
forecast horizon
target observations
metric implementation
```

Primary comparison nên giữ non-seasonal structure tương đương khi evidence cho phép
để quan sát tác động của seasonal terms. Không chọn model bằng test metric trước khi
evaluation setup được khóa.

## 7. Scientific Parameters

```text
ADF alpha: 0.05
ADF regression: c
ADF autolag: AIC
Suggested regular differencing: d = 1, evidence required
Suggested seasonal differencing: D = 1, evidence required
Seasonal period: s = 12
ACF/PACF maximum lag: 36
ACF/PACF confidence level: 95%
PACF method: ywm
Seasonal reference lags: 12, 24, 36
Required models: non-seasonal ARIMA and SARIMA
Required fit evidence: convergence, warnings, AIC, BIC
Required residual evidence: mean, time plot, ACF, Ljung–Box
Ljung–Box alpha: 0.05
Reference Ljung–Box lags: 12 and 24 when statistically valid
Required forecast metrics: MAE and RMSE
Optional supplementary metric: MAPE
```

Không hard-code final `(p,d,q)(P,D,Q,12)` trước actual E06 evidence.

## 8. Expected Outputs

```text
outputs/figures/06_airpassengers_original_series.png
outputs/figures/06_airpassengers_differencing.png
outputs/figures/06_airpassengers_acf_pacf.png
outputs/figures/06_airpassengers_residual_diagnostics.png
outputs/figures/06_airpassengers_forecast_comparison.png
outputs/results/06_airpassengers_validation.csv
outputs/results/06_airpassengers_split.csv
outputs/results/06_airpassengers_adf_results.csv
outputs/results/06_airpassengers_model_candidates.csv
outputs/results/06_airpassengers_model_diagnostics.csv
outputs/results/06_airpassengers_forecasts.csv
outputs/results/06_airpassengers_metrics.csv
```

Output phải cho phép truy vết:

```text
dataset and split identity
scale and differencing decisions
ADF/ACF/PACF evidence
model orders and convergence
residual diagnostics
aligned forecasts and actuals
MAE/RMSE comparison
```

Execution result phải được truy vết qua `docs/logs/exercise_06_execution.md` và
`docs/status/current_status.md`; specification này không thay thế execution evidence.

## 9. Interpretation Questions

1. AirPassengers có trend và annual seasonality không?
2. Original training series có stationary không?
3. Raw hay natural-log scale phù hợp hơn với training evidence?
4. Regular `d` và seasonal `D` nào có evidence?
5. Transformed training series đã đủ stationary để phân tích ACF/PACF chưa?
6. ACF/PACF hỗ trợ candidate `(p,q,P,Q)` nào?
7. ARIMA và SARIMA có hội tụ không?
8. Residuals của từng model có còn autocorrelation không?
9. Model nào có MAE thấp hơn trên cùng test observations?
10. Model nào có RMSE thấp hơn trên cùng test observations?
11. SARIMA có mô tả seasonal timing tốt hơn ARIMA không?
12. Sai lệch lớn nhất của từng model xảy ra tại timestamp nào?
13. Evidence có hỗ trợ lợi ích của seasonal modeling trên holdout này không?
14. Những limitation nào còn lại?

Không viết kết luận hoặc metrics trước khi actual outputs được tạo và inspect.

## 10. Validation Criteria

```text
[ ] E05 completion và E06 confirmation state được xác minh
[ ] Raw checksum, schema, date range và monthly continuity hợp lệ
[ ] Missing values và duplicate timestamps được kiểm tra
[ ] Split đúng 115 train / 29 test, không shuffle
[ ] Test set được sealed đến final evaluation
[ ] Scale decision chỉ dùng training evidence
[ ] Original-training ADF có statistic, p-value, critical values và metadata
[ ] d, D và s có traceable evidence
[ ] Differencing NaN và timestamp alignment được kiểm tra
[ ] ACF/PACF chỉ dùng stationary transformed training series
[ ] Candidate orders có actual rationale
[ ] ARIMA và SARIMA dùng cùng confirmed evaluation setup
[ ] Convergence, warnings, AIC và BIC được ghi
[ ] Residual mean, plot, ACF và Ljung–Box được ghi
[ ] Forecasts có đúng 29 observations và khớp test index
[ ] MAE/RMSE dùng cùng observations
[ ] Largest-error timestamps được tính, không đoán bằng mắt
[ ] Conclusion giới hạn trong dataset/holdout hiện tại
[ ] Raw data và E01–E05 evidence không bị sửa
[ ] Notebook chạy từ clean kernel và outputs được inspect
```

## 11. Stop Conditions

Phải dừng nếu E05 chưa hoàn thành, E06 chưa confirmed, dataset contract sai, xuất hiện
test leakage, scale/inverse-transform policy chưa rõ, differencing thiếu evidence,
ACF/PACF input chưa stationary, model không hội tụ, forecast index lệch test index,
hai model không dùng cùng setup hoặc scope/dependency cần mở rộng.

Khi dừng: `STOP → document issue → explain impact → propose next action → chờ xác nhận`.

## 12. Completion Condition

```text
AirPassengers validated
AND independent chronological holdout sealed
AND scale and differencing decisions supported by training evidence
AND ACF/PACF candidates documented
AND ARIMA and SARIMA fitted on the same confirmed training setup
AND convergence and residual diagnostics inspected
AND forecasts aligned to the same test horizon
AND MAE/RMSE comparison reproduced
AND conclusion supported by actual evidence
AND tests and clean notebook execution pass
AND no unresolved blocking issue
```

## 13. Downstream Role

E06 hoàn thành Advanced Extension và cung cấp kết luận về tác động của seasonal
modeling trên AirPassengers. E06 không thay thế, sửa lại hoặc che lấp completion state
của Core Practice E01–E05.

## 14. confirmation gate

```text
EXERCISE_06_SPECIFICATION_CREATED=true
EXERCISE_06_SPECIFICATION_REVIEWED=true
EXERCISE_06_SPECIFICATION_CONFIRMED=true
EXERCISE_06_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_06_WAITING_FOR_E05=false
```
