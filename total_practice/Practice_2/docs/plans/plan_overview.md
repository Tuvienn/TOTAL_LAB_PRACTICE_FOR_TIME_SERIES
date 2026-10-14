# PLAN OVERVIEW — PRACTICE 2

## 1. Document Identity

**Document:** `plan_overview.md`  
**Practice:** Practice 2 — ADF and ARIMA/SARIMA  
**Planning level:** High-level execution plan  
**Core scope:** Exercise 01–05  
**Advanced scope:** Exercise 06  
**Status:** APPROVED

Tài liệu này xác định trình tự, input, nhiệm vụ, evidence, output và điều kiện hoàn thành của từng Exercise. Mục tiêu, dataset, phạm vi và Definition of Done tổng thể thuộc `project_overview.md`.

---

## 2. Purpose and Source Basis

Plan được xây dựng từ các yêu cầu trong [đề bài Practice 2](../../../../references/excercise_stats_models.pdf):

1. Khám phá dữ liệu.
2. Kiểm định ADF trên chuỗi gốc.
3. Sai phân và kiểm định lại.
4. Phân tích ACF/PACF.
5. Thiết lập ARIMA, chẩn đoán phần dư, dự báo và đánh giá.
6. Bài tập nâng cao với SARIMA.

Hai dataset được sử dụng:

- Dataset 1: Monthly Retail Sales — dữ liệu chính cho Exercise 01–05.
- Dataset 2: AirPassengers — dữ liệu cho Exercise 06.

Plan không mô tả implementation ở mức tên hàm hoặc code cell. Chi tiết đó thuộc exercise specification được phê duyệt trước khi triển khai.

---

## 3. Planning Principles

### 3.1. Sequential Dependency

```text
Dataset 1
→ E01: validated time series
→ sealed chronological holdout
→ E02: original-series ADF conclusion
→ E03: stationary series + d
→ E04: p/q + ARIMA candidates
→ E05: fitted models + diagnostics + forecast evaluation
→ Core complete

Dataset 2
→ E06: ARIMA baseline and SARIMA comparison
→ Advanced complete
```

Không thực hiện downstream Exercise nếu upstream Exercise chưa cung cấp đủ input và evidence.

### 3.2. Evidence Before Decision

```text
ADF evidence → stationarity decision → selected d
ACF/PACF evidence → candidate p/q → ARIMA candidates
Convergence + AIC/BIC + residual diagnostics + forecast metrics → model assessment
```

Không được hard-code kết luận, thay đổi candidate model âm thầm hoặc đánh giá model chỉ bằng một metric.

### 3.3. Chronology and Holdout Protection

- Dữ liệu phải giữ nguyên thứ tự thời gian.
- Không shuffle train/test observations.
- Sau E01, ranh giới train 80% và test 20% được xác định theo thời gian.
- Test set được niêm phong và không được dùng để chọn `d`, `p`, `q` hoặc candidate model.
- E02–E04 sử dụng original training series và các transformation của training series.
- E05 mới được sử dụng test set để đánh giá forecast ngoài mẫu.
- Notebook có thể trình bày train/test split chính thức trong E05, nhưng boundary phải được xác định trước E02 để ngăn leakage.

### 3.4. Raw-Data Integrity

- Không ghi đè `datasets/raw/a10.csv`.
- Không âm thầm sort, fill, interpolate, deduplicate, resample hoặc đổi tên cột trong raw file.
- Mọi xử lý chỉ áp dụng trên working copy.
- Các vấn đề time index phải được ghi nhận trước khi xử lý.

### 3.5. One Exercise, One Main Decision

| Exercise | Main decision |
|---|---|
| E01 | Dữ liệu đã sẵn sàng cho phân tích chưa? |
| E02 | Original training series có stationary không? |
| E03 | Sau differencing chuỗi có stationary và `d` bằng bao nhiêu? |
| E04 | Những `p/q` và ARIMA candidates nào có căn cứ? |
| E05 | Candidate nào phù hợp hơn theo fit, diagnostics và out-of-sample forecast? |
| E06 | SARIMA có xử lý seasonality tốt hơn ARIMA trên AirPassengers không? |

---

## 4. Exercise Flow

```text
E01 — EDA and Time-Series Preparation
 ↓
E02 — ADF on Original Series
 ↓
E03 — Differencing and ADF Retest
 ↓
E04 — ACF/PACF and ARIMA Candidate Identification
 ↓
E05 — ARIMA Training, Diagnostics, Forecasting and Evaluation
 ↓
CORE COMPLETE

E06 — Advanced SARIMA Extension
```

Exercise 01–05 tạo thành Core Practice. Exercise 06 là Advanced Extension và không thay thế Core Practice.

---

## 5. Exercise 01 — EDA and Time-Series Preparation

### 5.1. Objective

Chuẩn bị Dataset 1 thành monthly time series hợp lệ, quan sát cấu trúc ban đầu và xác lập chronological holdout boundary.

### 5.2. Input

```text
datasets/raw/a10.csv
date column: date
target column: value
```

### 5.3. Required Tasks

- load dữ liệu mà không thay đổi raw file;
- kiểm tra schema và kiểu dữ liệu;
- parse `date` thành datetime;
- thiết lập time index;
- xác nhận chronological order;
- kiểm tra duplicate timestamps;
- kiểm tra missing values và missing monthly intervals;
- xác nhận monthly frequency;
- vẽ original time-series plot;
- nhận xét trend, seasonality và khả năng stationarity ban đầu;
- xác định ranh giới chronological train 80% và test 20%;
- niêm phong test set cho đến E05.

### 5.4. Required Evidence

- số quan sát và schema;
- date range và frequency;
- missing/duplicate checks;
- original-series visualization;
- nhận xét trend;
- nhận xét seasonality;
- nhận xét stationarity ban đầu;
- train/test boundary và số quan sát mỗi tập.

### 5.5. Required Output

```text
Validated full monthly series
+
Original-series visualization
+
EDA observations
+
Sealed chronological train/test boundary
```

### 5.6. Exit Condition

```text
[ ] Dataset load thành công
[ ] date và value được xác định đúng
[ ] Time order và monthly frequency được xác nhận
[ ] Missing và duplicate checks hoàn thành
[ ] Original series được visualize và diễn giải
[ ] Train/test boundary được xác định theo thời gian
[ ] Test set được đánh dấu không sử dụng trước E05
```

### 5.7. Stop Condition

Dừng trước E02 nếu timestamp không parse được, frequency không xác định, có duplicate hoặc missing interval chưa được giải thích, hoặc train/test boundary chưa được xác lập.

### 5.8. Downstream Handoff

E01 cung cấp original training series chưa biến đổi cho E02 và giữ test set niêm phong đến E05.

---

## 6. Exercise 02 — ADF on Original Series

### 6.1. Objective

Kiểm định stationarity của original training series bằng Augmented Dickey-Fuller test.

### 6.2. Input

```text
Original untransformed training series from E01
Significance level α = 0.05
```

### 6.3. Required Tasks

- chạy ADF trên original training series;
- ghi ADF statistic;
- ghi p-value;
- ghi critical values;
- ghi số lag và số quan sát được sử dụng khi output cung cấp;
- giải thích giả thuyết H₀;
- so sánh p-value với `α = 0.05`;
- kết luận stationary hoặc non-stationary.

### 6.4. Required Evidence

Phải trả lời:

- H₀ của ADF là gì?
- p-value cho biết điều gì?
- Original training series có stationary không?

### 6.5. Required Output

```text
Original-series ADF result
+
Stationarity conclusion
```

### 6.6. Exit Condition

```text
[ ] ADF đã chạy trên original training series
[ ] ADF statistic, p-value và critical values đã được ghi
[ ] H₀ và decision rule đã được giải thích
[ ] Stationarity conclusion có bằng chứng
```

### 6.7. Stop Condition

Dừng trước E03 nếu ADF input không đúng chuỗi train nguyên bản, test observations bị sử dụng hoặc kết luận không truy vết được đến output.

### 6.8. Downstream Handoff

E02 cung cấp original-series stationarity conclusion cho E03.

---

## 7. Exercise 03 — Differencing and ADF Retest

### 7.1. Objective

Thực hiện first-order differencing trên training series, kiểm định lại stationarity và xác định tham số `d`.

### 7.2. Input

```text
Original training series
+
Stationarity conclusion from E02
```

### 7.3. Required Tasks

- tạo first-differenced working series;
- loại giá trị `NaN` sinh trực tiếp từ phép sai phân trên working copy;
- không thay đổi raw data;
- vẽ differenced series;
- chạy ADF trên differenced series;
- ghi ADF statistic, p-value và critical values;
- kết luận chuỗi sau sai phân đã stationary chưa;
- xác định và giải thích `d`.

### 7.4. Required Evidence

Phải trả lời:

- Sau first-order differencing, chuỗi đã stationary chưa?
- ADF evidence trước và sau sai phân khác nhau như thế nào?
- Giá trị `d` được chọn là bao nhiêu và vì sao?

### 7.5. Required Output

```text
Differenced training series
+
Differenced-series visualization
+
Post-differencing ADF result
+
Selected d
+
Stationary working series
```

### 7.6. Exit Condition

```text
[ ] First-order differencing hoàn thành trên working copy
[ ] Differenced series được visualize
[ ] ADF retest hoàn thành
[ ] Stationarity sau differencing được kết luận
[ ] d được xác định có căn cứ
```

### 7.7. Stop Condition

Dừng trước E04 nếu working series chưa stationary, `d` chưa xác định hoặc test observations đã tham gia transformation/model identification.

### 7.8. Downstream Handoff

E03 cung cấp stationary training series và selected `d` cho E04.

---

## 8. Exercise 04 — ACF/PACF and ARIMA Candidate Identification

### 8.1. Objective

Phân tích ACF/PACF của stationary training series để đề xuất `p`, `q` và 1–2 ARIMA candidates.

### 8.2. Input

```text
Stationary training series
+
Selected d from E03
```

### 8.3. Required Tasks

- vẽ ACF của stationary training series;
- vẽ PACF của stationary training series;
- phân tích lag nổi bật, cutoff hoặc decay pattern;
- đề xuất candidate `p`;
- đề xuất candidate `q`;
- kết hợp `p`, `d`, `q`;
- xác định 1–2 ARIMA candidates để fit trong E05.

### 8.4. Required Evidence

Phải trả lời:

- ACF cắt cụt hoặc suy giảm như thế nào?
- PACF cắt cụt hoặc suy giảm như thế nào?
- Những lag nào hỗ trợ candidate `p/q`?
- Vì sao từng ARIMA candidate được đề xuất?

ACF/PACF chỉ dùng để đề xuất candidates, không tự động xác nhận final model.

### 8.5. Required Output

```text
ACF plot and interpretation
+
PACF plot and interpretation
+
Candidate p/q values
+
1–2 ARIMA candidates
```

### 8.6. Exit Condition

```text
[ ] ACF/PACF được tạo từ stationary training series
[ ] p và q candidates có evidence
[ ] d được kế thừa đúng từ E03
[ ] 1–2 ARIMA candidates được xác định
```

### 8.7. Stop Condition

Dừng trước E05 nếu ACF/PACF được tính trên full series, raw non-stationary series hoặc ARIMA candidates được chọn tùy ý.

### 8.8. Downstream Handoff

E04 cung cấp 1–2 ARIMA candidates cho E05.

---

## 9. Exercise 05 — ARIMA Training, Diagnostics, Forecasting and Evaluation

### 9.1. Objective

Fit các ARIMA candidates trên train set, kiểm tra model và residuals, forecast trên sealed test set và đánh giá out-of-sample performance.

### 9.2. Input

```text
Chronological train/test boundary from E01
+
1–2 ARIMA candidates from E04
+
Sealed test set
```

### 9.3. Required Tasks

#### Stage A — Chronological Split Report

- trình bày train 80% và test 20%;
- xác nhận time order;
- xác nhận không shuffle;
- giải thích vai trò của test set;
- xác nhận test set chưa được dùng trong E02–E04.

#### Stage B — Baseline and Model Fitting

- tạo seasonal-naive baseline với seasonal lag 12;
- fit từng ARIMA candidate trên train set;
- kiểm tra convergence;
- ghi AIC và BIC;
- giải thích ý nghĩa của `p`, `d`, `q`;
- không chọn final model chỉ bằng AIC/BIC.

#### Stage C — Residual Diagnostics

Với mỗi fitted candidate:

- vẽ residual theo thời gian;
- tính residual mean;
- vẽ residual ACF;
- kiểm tra residual autocorrelation;
- đánh giá residual có gần white noise không;
- dùng Ljung–Box như kiểm định bổ sung khi phù hợp;
- ghi hướng điều chỉnh nếu residual còn autocorrelation.

#### Stage D — Forecasting and Evaluation

- forecast đúng test horizon;
- căn chỉnh forecast index với test index;
- vẽ Train/Test/Forecast;
- tính MAE, RMSE và MAPE;
- tính cùng metric cho seasonal-naive baseline;
- so sánh candidates và baseline;
- xác định timestamp có absolute error lớn nhất;
- đưa ra final ARIMA assessment từ tổng hợp evidence.

### 9.4. Required Evidence

Phải trả lời đủ các câu hỏi của đề:

1. Vì sao không được shuffle và test set dùng để làm gì?
2. Ý nghĩa của `p`, `d`, `q` đã chọn?
3. Mô hình có hội tụ không?
4. Residuals có phải white noise không?
5. Nếu residuals còn tự tương quan thì cần điều chỉnh gì?
6. Forecast có bám sát xu hướng không?
7. Sai lệch lớn nhất xảy ra ở đâu?
8. Chỉ số nào nhạy với outlier nhất?
9. RMSE lớn hoặc nhỏ nói lên điều gì?

### 9.5. Required Output

```text
Chronological train/test evidence
+
Seasonal-naive baseline forecast and metrics
+
Fitted ARIMA candidates
+
Convergence status and AIC/BIC
+
Residual diagnostics
+
Forecast values and Train/Test/Forecast plot
+
MAE/RMSE/MAPE comparison
+
Largest-error evidence
+
Final ARIMA assessment
```

### 9.6. Exit Condition

```text
[ ] Train/test split được trình bày và không shuffle
[ ] Test holdout integrity được xác nhận
[ ] Seasonal-naive baseline được đánh giá
[ ] Tất cả approved candidates được fit
[ ] Convergence, AIC và BIC được ghi
[ ] Residual diagnostics hoàn thành
[ ] Forecast đúng test horizon
[ ] MAE, RMSE và MAPE được tính nhất quán
[ ] Candidates được so sánh với baseline
[ ] Chín câu hỏi bắt buộc được trả lời
[ ] Final assessment có evidence
```

### 9.7. Stop Condition

Dừng và ghi nhận issue nếu model không hội tụ, forecast index lệch test index, metric dùng sai observations, residual còn cấu trúc chưa được giải thích hoặc test leakage được phát hiện.

### 9.8. Downstream Handoff

E05 hoàn thành Core Practice. Kết quả ARIMA trên Dataset 1 không được dùng trực tiếp để so metric với SARIMA trên Dataset 2.

---

## 10. Exercise 06 — Advanced SARIMA Extension

### 10.1. Objective

Fit ARIMA baseline và SARIMA trên cùng AirPassengers setup để đánh giá tác động của seasonal modeling.

### 10.2. Input

```text
Dataset 2 — AirPassengers
File: datasets/raw/airline-passengers.csv
Date column: Month
Target column: Passengers
Date format: YYYY-MM
Frequency: Monthly
Seasonal period: s = 12
Suggested differencing: d = 1, D = 1
```

Các giá trị `d = 1` và `D = 1` là gợi ý của đề, không thay thế việc kiểm tra evidence.

### 10.3. Required Tasks

- load và validate AirPassengers;
- vẽ original series và nhận diện seasonality;
- tạo chronological train/test split và niêm phong test set;
- chạy ADF trên original training series;
- thực hiện regular differencing và seasonal differencing trên train;
- phân tích ACF/PACF để đề xuất `(p,q,P,Q)`;
- fit một non-seasonal ARIMA baseline trên AirPassengers train;
- fit SARIMA `(p,d,q)(P,D,Q,12)` trên cùng train set;
- forecast cùng test horizon;
- tính MAE và RMSE cho cả hai model;
- so sánh ARIMA và SARIMA trên cùng test observations.

### 10.4. Required Evidence

- seasonality evidence;
- original-series ADF evidence;
- regular and seasonal differencing evidence;
- rationale cho `(p,q,P,Q)`;
- convergence và residual evidence của model;
- cùng train/test boundary và forecast horizon;
- MAE/RMSE của ARIMA và SARIMA;
- kết luận về lợi ích hoặc hạn chế của seasonal modeling.

### 10.5. Required Output

```text
AirPassengers validation and seasonality evidence
+
Stationarity and differencing evidence
+
ARIMA baseline on AirPassengers
+
Fitted SARIMA model
+
Forecasts on the same test horizon
+
MAE/RMSE comparison
+
Final ARIMA–SARIMA conclusion
```

### 10.6. Exit Condition

```text
[ ] AirPassengers được validate
[ ] Test set không tham gia model identification
[ ] Regular và seasonal differencing có evidence
[ ] ARIMA baseline và SARIMA dùng cùng evaluation setup
[ ] Forecast horizon và test observations giống nhau
[ ] MAE/RMSE được tính nhất quán
[ ] ARIMA–SARIMA comparison có kết luận
```

### 10.7. Stop Condition

Dừng nếu hai model không dùng cùng dataset, split, horizon hoặc metrics; nếu model không hội tụ mà chưa được ghi nhận; hoặc nếu test leakage được phát hiện.

### 10.8. Downstream Handoff

E06 hoàn thành Advanced Extension và cung cấp kết luận về seasonal modeling trên Dataset 2.

---

## 11. Dependency Map

```text
Dataset 1: Monthly Retail Sales
        ↓
E01: validated series + sealed holdout boundary
        ↓
E02: original-series ADF conclusion
        ↓
E03: stationary training series + d
        ↓
E04: p/q + ARIMA candidates
        ↓
E05: baseline + fitted ARIMA + diagnostics + evaluation
        ↓
CORE COMPLETE

Dataset 2: AirPassengers
        ↓
E06: same-data ARIMA baseline + SARIMA comparison
        ↓
ADVANCED COMPLETE
```

---

## 12. Exercise Interface Summary

| Exercise | Main Input | Main Decision | Main Output |
|---|---|---|---|
| E01 | Dataset 1 | Dữ liệu có sẵn sàng và holdout boundary có hợp lệ không? | Validated series + sealed boundary |
| E02 | Original training series | Chuỗi gốc có stationary không? | ADF evidence + conclusion |
| E03 | Train series + E02 conclusion | Differencing có tạo stationary series và `d` bằng bao nhiêu? | Stationary series + `d` |
| E04 | Stationary train series + `d` | Candidate `p/q` nào có căn cứ? | 1–2 ARIMA candidates |
| E05 | Candidates + sealed test | Model nào phù hợp hơn ngoài mẫu và so với baseline? | Final ARIMA assessment |
| E06 | AirPassengers | SARIMA có cải thiện seasonal modeling so với ARIMA cùng dữ liệu không? | ARIMA–SARIMA comparison |

---

## 13. Core vs Advanced Boundary

### Core Practice

```text
E01 → E02 → E03 → E04 → E05
```

Core Practice sử dụng Dataset 1 và hoàn thành toàn bộ yêu cầu ARIMA chính.

### Advanced Extension

```text
E06
```

Exercise 06 sử dụng Dataset 2. Completion của E06 không thay thế hoặc che lấp trạng thái của E01–E05.

---

## 14. Approval Gates

### Gate 1 — Overview Approval

```text
PROJECT_OVERVIEW approved
+
PLAN_OVERVIEW approved
```

### Gate 2 — Exercise Design Approval

Trước khi code một Exercise:

```text
approved Exercise scope trong plan hoặc specification riêng khi cần
+
input contract available
+
scientific protocol understood
```

### Gate 3 — Implementation Approval

```text
approved implementation scope
+
entry condition satisfied
+
upstream evidence available
```

### Gate 4 — Exercise Completion Approval

```text
required output generated
+
validation passed
+
interpretation documented
+
Human review completed
```

Không chuyển Exercise nếu gate hiện tại chưa đạt.

---

## 15. Optional Exercise Detail Files

Không bắt buộc tạo một file riêng cho từng Exercise khi scope, input, output và
validation trong plan này đã đủ rõ. Chỉ tạo specification riêng khi Human yêu cầu
hoặc khi Exercise cần quyết định bổ sung trước implementation.

Nếu được tạo, dùng các tên:

```text
exercise_01_eda_time_series_preparation.md
exercise_02_adf_original_series.md
exercise_03_differencing_adf_retest.md
exercise_04_acf_pacf_arima_candidates.md
exercise_05_arima_training_forecasting_evaluation.md
exercise_06_sarima_extension.md
```

Các file tùy chọn này thuộc `docs/exercise_details/`.

Mỗi exercise detail dự kiến bao gồm:

```text
1. Exercise Identity
2. Objective
3. Input Contract
4. Required Steps
5. Scientific Parameters
6. Expected Outputs
7. Interpretation Questions
8. Validation Criteria
9. Stop Conditions
10. Completion Condition
```

---

## 16. Current Status and Next Step

```text
PROJECT_OVERVIEW
        ↓
     APPROVED
        ↓
PLAN_OVERVIEW
        ↓
     APPROVED
```

Trạng thái tiếp theo:

1. Không tự động triển khai Exercise.
2. Hoàn thành readiness cleanup đã được Human yêu cầu.
3. Code tuần tự từ E01 khi implementation scope tương ứng được phê duyệt.
4. Chỉ tạo exercise specification riêng khi Human yêu cầu hoặc plan chưa đủ rõ.

Commit và push Git không thuộc phạm vi của plan này.
