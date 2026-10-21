# TỔNG QUAN DỰ ÁN — PRACTICE 2

## 1. Thông tin Practice

**Practice:** Practice 2  
**Topic:** Kiểm định ADF và chuẩn bị mô hình ARIMA/SARIMA  
**Domain:** Time Series Analysis and Forecasting  
**Core scope:** Exercise 01–05  
**Advanced scope:** Exercise 06

Practice 2 xây dựng một workflow từ kiểm tra tính dừng đến huấn luyện, chẩn đoán và đánh giá mô hình dự báo chuỗi thời gian.

---

## 2. Định nghĩa bài toán

Practice 2 cần giải quyết các câu hỏi chính:

- Chuỗi thời gian có dừng hay không?
- Kiểm định ADF được thực hiện và diễn giải như thế nào?
- Chuỗi cần sai phân bao nhiêu lần và tham số `d` bằng bao nhiêu?
- ACF và PACF gợi ý những giá trị `p` và `q` nào?
- Mô hình ARIMA có hội tụ và có phần dư phù hợp không?
- Forecast có bám sát dữ liệu test không?
- MAE, RMSE và MAPE cho biết điều gì về chất lượng dự báo?
- SARIMA cải thiện việc mô hình hóa mùa vụ như thế nào?

Workflow tổng quát:

```text
Raw time series
→ EDA
→ ADF on original series
→ Differencing and ADF retest
→ ACF/PACF
→ ARIMA candidates
→ Chronological train/test split
→ Model fitting
→ Residual diagnostics
→ Forecasting
→ Evaluation
→ Final conclusion
```

Mọi quyết định phải dựa trên kết quả thực tế của dữ liệu và không được giả định trước kết luận.

---

## 3. Mục tiêu học tập

Theo đề bài, Practice 2 có sáu mục tiêu:

1. Nhận diện chuỗi dừng và không dừng.
2. Thực hiện và diễn giải kiểm định ADF.
3. Xác định tham số `d` trong ARIMA.
4. Kết hợp ADF với ACF/PACF.
5. Chuẩn bị dữ liệu đúng cách cho ARIMA/SARIMA.
6. Đánh giá mô hình.

---

## 4. Dataset

### 4.1. Dataset 1 — Monthly Retail Sales

Dataset chính cho Exercise 01–05:

```text
File: datasets/raw/a10.csv
Ý nghĩa: Doanh số bán lẻ theo tháng tại Mỹ
Cột thời gian: date
Cột giá trị: value
Tần suất: Monthly
Đặc điểm chính: Trend + seasonality
```

Dataset 1 được sử dụng để:

- khám phá và chuẩn bị chuỗi thời gian;
- kiểm định ADF;
- thực hiện sai phân;
- phân tích ACF/PACF;
- đề xuất và fit ARIMA;
- forecast và đánh giá trên test set.

### 4.2. Dataset 2 — AirPassengers

Dataset dành cho Exercise 06 — Advanced SARIMA Extension:

```text
File: datasets/raw/airline-passengers.csv
Tên: AirPassengers — Monthly Airline Passengers
Cột thời gian: Month
Định dạng thời gian: YYYY-MM
Cột giá trị: Passengers
Khoảng thời gian: 1949–1960
Số quan sát: 144
Tần suất: Monthly
Chu kỳ mùa vụ: s = 12
```

Dataset 2 được sử dụng để thực hành sai phân mùa vụ, SARIMA và so sánh với ARIMA.

---

## 5. Phạm vi Practice

### 5.1. Core Practice — Exercise 01–05

Core Practice bao gồm:

- load và chuẩn bị Dataset 1;
- kiểm tra time index, time order và chất lượng dữ liệu cơ bản;
- nhận diện trend, seasonality và khả năng stationarity;
- chạy ADF trên chuỗi gốc;
- sai phân và chạy lại ADF;
- xác định `d`;
- phân tích ACF/PACF;
- đề xuất 1–2 ARIMA candidates;
- chia train 80% và test 20% theo thời gian, không shuffle;
- fit model và ghi AIC/BIC;
- kiểm tra convergence và residuals;
- forecast trên test set;
- tính MAE, RMSE và MAPE;
- so sánh candidate models và đưa ra kết luận.

### 5.2. Phần mở rộng exploratory — Exercise 06

Phần mở rộng exploratory bao gồm:

- sử dụng Dataset 2 — AirPassengers;
- nhận diện mùa vụ;
- sai phân thường và sai phân mùa vụ;
- xác định `(p,q,P,Q)`;
- fit SARIMA với seasonal period `s = 12`;
- forecast và đánh giá bằng MAE/RMSE;
- so sánh SARIMA với ARIMA.

Exercise 06 không thay thế việc hoàn thành Exercise 01–05 và không thuộc formal
completion theo Phương án A đã được Human chọn.

### 5.3. Ngoài phạm vi

Practice 2 không đặt mục tiêu:

- xây dựng production forecasting system;
- triển khai API, web application hoặc cloud deployment;
- sử dụng deep learning forecasting;
- thực hiện AutoML hoặc automated hyperparameter search quy mô lớn;
- tối ưu mô hình chỉ để đạt metric tốt nhất;
- thay đổi hoặc ghi đè raw dataset.

---

## 6. Tổng quan Exercise

| Exercise | Mục tiêu chính | Kết quả chính |
|---|---|---|
| E01 — EDA | Chuẩn bị và quan sát chuỗi | Validated time series + EDA observations |
| E02 — ADF chuỗi gốc | Kiểm định stationarity của original series | Original-series ADF evidence + conclusion |
| E03 — Sai phân | Sai phân, kiểm định lại và xác định `d` | Stationary working series + selected `d` |
| E04 — ACF/PACF | Đề xuất `p`, `q` và ARIMA candidates | 1–2 ARIMA candidates |
| E05 — ARIMA | Fit, diagnostics, forecast và evaluation | Final ARIMA assessment |
| E06 — SARIMA nâng cao | Mô hình hóa seasonality và so sánh | SARIMA result + ARIMA comparison |

Chi tiết input, output, dependency, exit condition và stop condition của từng Exercise thuộc `plan_overview.md`.

---

## 7. Workflow khoa học

Practice phải duy trì thứ tự khoa học:

```text
Observation
→ Statistical test
→ Transformation
→ Model identification
→ Model estimation
→ Residual diagnostics
→ Forecast
→ Evaluation
→ Conclusion
```

Các nguyên tắc bắt buộc:

- giữ nguyên thứ tự thời gian;
- không shuffle dữ liệu forecast;
- không chọn `d` khi chưa có stationarity evidence;
- không chọn `p` và `q` mà không phân tích ACF/PACF;
- không kết luận model phù hợp chỉ dựa trên AIC/BIC;
- không kết luận residual là white noise chỉ bằng quan sát trực quan;
- forecast phải được đánh giá trên held-out test set;
- kết luận phải truy vết được đến output thực tế.

---

## 8. Sản phẩm bàn giao dự kiến

Core Practice tối thiểu phải tạo được:

1. Original time-series visualization.
2. Original-series ADF result.
3. Differenced-series visualization.
4. Post-differencing ADF result.
5. Selected `d`.
6. ACF và PACF plots.
7. Một đến hai ARIMA candidates.
8. Chronological train/test split.
9. Model fit results, convergence status, AIC và BIC.
10. Residual time plot và residual ACF.
11. Train/Test/Forecast visualization.
12. MAE, RMSE và MAPE.
13. Candidate comparison.
14. Final ARIMA conclusion.

Phần E6 exploratory hiện có thể trình bày:

1. Seasonal differencing evidence.
2. SARIMA specification và fitted model.
3. SARIMA forecast.
4. SARIMA MAE/RMSE.
5. ARIMA–SARIMA comparison.

---

## 9. Định nghĩa hoàn thành

### 9.1. Core Practice

Practice 2 core được xem là hoàn thành khi:

```text
[ ] Dataset 1 được load và xử lý đúng dưới dạng time series
[ ] Time order được bảo toàn
[ ] EDA được hoàn thành
[ ] ADF trên chuỗi gốc được hoàn thành và diễn giải
[ ] Differencing decision có bằng chứng
[ ] d được xác định
[ ] ACF/PACF được phân tích trên working series phù hợp
[ ] 1–2 ARIMA candidates được đề xuất có căn cứ
[ ] Train/test split theo thời gian được hoàn thành
[ ] Không shuffle dữ liệu
[ ] Candidate models được fit
[ ] Convergence được kiểm tra
[ ] AIC/BIC được ghi nhận
[ ] Residual diagnostics được hoàn thành
[ ] Forecast trên test set được tạo
[ ] MAE, RMSE và MAPE được tính
[ ] Candidate models được so sánh
[ ] Các câu hỏi bắt buộc của đề được trả lời
[ ] Final ARIMA conclusion được ghi lại
```

### 9.2. Formal Advanced Extension — chỉ dùng làm tham chiếu

Nếu E6 được formalize trong tương lai, Exercise 06 chỉ được xem là hoàn thành khi:

```text
[ ] AirPassengers được chuẩn bị đúng theo monthly frequency
[ ] Seasonality được nhận diện
[ ] Regular và seasonal differencing được đánh giá
[ ] SARIMA specification được giải thích
[ ] SARIMA được fit và forecast
[ ] MAE/RMSE được tính
[ ] SARIMA được so sánh với ARIMA
[ ] Kết luận và limitation được ghi lại
```

Một Practice vẫn đạt mục tiêu học tập nếu model chưa có sai số thấp, miễn là quy trình đúng, evidence đầy đủ và kết luận trung thực.

---

## 10. Tài liệu liên quan

- [Đề bài Practice 2](../../../../references/excercise_stats_models.pdf)
- [Kế hoạch triển khai cấp cao](plan_overview.md)
- Exercise specifications sẽ được lưu trong `docs/exercise_details/` sau khi được thiết kế và phê duyệt.

`project_overview.md` sở hữu mục tiêu, phạm vi, dataset, deliverables và Definition of Done tổng thể. `plan_overview.md` sở hữu trình tự, dependency, input/output và validation gate của từng Exercise.
