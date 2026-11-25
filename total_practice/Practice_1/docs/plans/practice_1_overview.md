# PRACTICE 1 — TỔNG QUAN BÀI THỰC HÀNH

## 1. Danh tính tài liệu

```text
Document ID: TS-PRACTICE-01-OVERVIEW-v1
Practice root: total_practice/Practice_1
Learning source: Chương 2 — Khám phá đặc tính dữ liệu chuỗi thời gian
Status: CONFIRMED
Implementation authorization: true for Initialization and Exercise 1
```

Tài liệu này mô tả mục tiêu, phạm vi khoa học, workflow, deliverables và completion boundary cấp cao của Practice 1.

Tài liệu này không thay thế exercise specification hoặc before-process plan.

## 2. Bối cảnh

Practice 1 chuyển các khái niệm trong Chương 2 thành một quy trình phân tích có thể kiểm tra và tái tạo.

Bài thực hành không nhằm tối ưu độ chính xác của forecasting model. Trọng tâm là hiểu temporal structure, phát hiện vấn đề chất lượng dữ liệu và đánh giá dữ liệu có đủ cơ sở để tiếp tục sang forecasting hay không.

## 3. Learning objectives

Sau khi hoàn thành Practice 1, người học cần có khả năng:

1. Kiểm tra dataset và time index trước phân tích.
2. Giải thích ý nghĩa của ACF và PACF.
3. Phân biệt chuỗi có temporal structure với white noise.
4. Phân tích trend, seasonality và residual qua decomposition.
5. Nhận diện missing values, irregularity và outliers.
6. So sánh có evidence hai phương pháp xử lý missing values.
7. Chọn visualization phù hợp với dữ liệu theo tháng.
8. Viết kết luận khoa học từ actual outputs.
9. Đánh giá forecastability mà không tuyên bố model performance chưa được kiểm chứng.

## 4. Scientific questions

Practice 1 phải cung cấp evidence để thảo luận các câu hỏi:

```text
Chuỗi có autocorrelation mạnh không?
Trend hoặc seasonality thể hiện như thế nào?
Lag nào nổi bật và vì sao?
White noise khác AirPassengers như thế nào?
Seasonal amplitude có thay đổi theo level của chuỗi không?
Residual sau decomposition còn temporal structure không?
Forward-fill hay time interpolation phù hợp hơn trong thí nghiệm đã thiết kế?
Điểm bất thường là anomaly hay seasonal peak?
Dữ liệu có phù hợp để tiếp tục sang forecasting không?
```

## 5. Dataset rationale

Dataset đã được xác định là `AirPassengers`.

Dataset phù hợp vì có:

- monthly frequency;
- trend tăng;
- seasonality chu kỳ 12 tháng;
- seasonal amplitude thay đổi theo level;
- độ dài phù hợp để phân tích tối đa 40 lags;
- cấu trúc trực quan phù hợp cho seasonal plot và month-year heatmap.

Dataset chỉ được sử dụng sau khi source, license, checksum, schema, timestamp semantics và frequency được xác minh.

Canonical source contract:

```text
CSV: https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv
Documentation: https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html
Expected observations: 144
Expected range: 1949-01 through 1960-12
Expected frequency: monthly
Unit: thousands of international airline passengers
```

Query parameter `?utm_source` không thuộc canonical URL. Actual schema, retrieval
date và SHA-256 checksum chỉ được ghi sau dataset acquisition. Provenance phải nêu
rõ Rdatasets không xác nhận dứt khoát standalone license cho mọi underlying dataset.

## 6. Quan hệ giữa sáu bài tập

### 6.1 Bài 1 — ACF/PACF

Xác định chuỗi có temporal dependence, trend hoặc seasonal signatures hay không.

### 6.2 Bài 2 — White noise

Tạo baseline khái niệm cho một chuỗi không có cấu trúc dự báo và so sánh với AirPassengers.

### 6.3 Bài 3 — Decomposition

Tách observed series thành trend, seasonal và residual để giải thích nguồn của temporal structure.

### 6.4 Bài 4 — Data quality

Mô phỏng missing values trên working copy, so sánh treatment methods và phân tích outliers mà không làm thay đổi raw data.

### 6.5 Bài 5 — Visualization

Tổng hợp trend, seasonal pattern, variance behavior và các điểm bất thường qua nhiều góc nhìn.

### 6.6 Bài 6 — Report

Báo cáo Word được xây dựng từ validated evidence của Bài 1–5. Exercise 6 không có
implementation plan, không có exercise specification riêng và không phải artifact
do workflow tạo trong task chuẩn hóa này.

## 7. Workflow cấp cao

```text
Verify dataset provenance
→ Validate schema and time index
→ Inspect and visualize the series
→ Analyze ACF/PACF
→ Compare with simulated white noise
→ Decompose the series
→ Evaluate missing-value treatments
→ Analyze outliers
→ Synthesize findings
→ Assess forecastability
```

Mỗi bước phải dùng output đã được verify từ bước trước. Không được patch downstream conclusion khi upstream data validation chưa đạt.

## 8. Scientific direction

Hướng phân tích đã thống nhất ở cấp cao:

```text
AirPassengers là dataset chính.
Maximum ACF/PACF lag là 40.
White noise dùng explicit random seed và 1000 observations.
White noise distribution là Normal(0, 1), ACF maximum lag 40 và confidence level 95%.
White-noise assessment bắt buộc dùng ACF; Ljung-Box chỉ là supplementary diagnostic.
Rolling window là 12 tháng.
Decomposition dùng natural-log transform và STL period 12, robust True.
Missing-value methods là forward-fill và time interpolation.
Missing-value comparison dùng cùng masked positions và true values đã lưu.
Outlier detection ưu tiên decomposition residual.
Outlier protocol là IQR multiplier 1.5 trên natural-log STL residual, chỉ flag và inspect.
Outlier không bị xóa hoặc thay thế tự động.
Missing protocol gồm 3 isolated timestamps và một block 3 tháng đã khóa trong Exercise 4.
Rolling statistics dùng trailing window 12, min_periods 12, center False và std ddof 1.
Python runtime contract là 3.12 với local .venv, pyproject.toml và installable package practice_1.
PACF method là ywm; statsmodels confidence alpha là 0.05.
Time interpolation dùng method time và limit_area inside.
Heatmap dùng month rows, year columns và expected shape 12 × 12.
```

Giá trị tham số và acceptance criteria đã được chuẩn hóa trong các exercise
specification; chúng vẫn cần confirmation trước implementation.

## 9. Deliverable categories

### 9.1 Figures

```text
time-series overview
ACF/PACF
white-noise comparison
decomposition
missing-value comparison
outlier analysis
rolling statistics
monthly seasonal plot
month-year heatmap
```

### 9.2 Machine-readable results

```text
data-quality summary
missing-value method comparison
white-noise diagnostic results
analysis summary
```

### 9.3 Narrative result

Notebook hoặc report phải giải thích:

```text
dataset characteristics
temporal structure
data-quality findings
decomposition findings
white-noise assessment
limitations
forecastability conclusion
```

## 10. Completion boundary cấp cao

Practice 1 chỉ có thể được xem xét completion khi:

```text
dataset provenance đã được xác minh
time index đã được validation
Exercise 1–5 đã có actual execution evidence
raw dataset không bị thay đổi
required figures và result tables đã được inspect
statistical conclusions truy vết được về output
notebook chạy được sau kernel restart
limitations và unresolved issues được báo cáo trung thực
```

Word report của Exercise 6 là deliverable riêng được quản lý ngoài repository và không phải gate
để workflow kết luận phần implementation của Exercise 1–5 đã hoàn thành.

Detailed acceptance criteria đã được viết nhưng chưa kích hoạt cho implementation cho
đến khi Đã xác nhận các plan liên quan.

## 11. Remaining confirmation gate

```text
Exercise 1 evidence review
Exercise 2 before-process confirmation
Exercise 2 explicit implementation authorization
```

Exercise 2–5 vẫn được approve tuần tự trước execution của từng exercise.

## 12. confirmation state

```text
OVERVIEW_CREATED=true
OVERVIEW_UPDATED_FOR_GROUP_1_3=true
OVERVIEW_REVIEWED=true
OVERVIEW_CONFIRMED=true
IMPLEMENTATION_AUTHORIZED=true_FOR_INITIALIZATION_AND_EXERCISE_1
INITIALIZATION_COMPLETED=true
EXERCISE_01_COMPLETED=true
EXERCISE_02_IMPLEMENTATION_AUTHORIZED=false
```
