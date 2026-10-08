# EXERCISE 01 — ACF/PACF ANALYSIS

## 1. Exercise Identity

```text
Practice: Practice_1
Exercise ID: EXERCISE_01
Topic: ACF/PACF
Dataset: AirPassengers
Frequency: Monthly
Maximum lag: 40
Model training required: NO
Status: COMPLETED
```

---

## 2. Objective

Mục tiêu của bài tập:

- kiểm tra cấu trúc phụ thuộc theo thời gian của chuỗi;
- phân tích autocorrelation bằng ACF;
- phân tích partial autocorrelation bằng PACF;
- xác định các lag nổi bật;
- quan sát dấu hiệu trend hoặc seasonality;
- tạo evidence phục vụ các exercise tiếp theo.

---

## 3. Input

Dataset chính:

```text
AirPassengers
```

Thông tin dự kiến:

```text
Frequency: monthly
Seasonal period: 12
Time index: month
Observed variable: passenger count in thousands
```

Canonical dataset contract:

```text
CSV URL: https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv
Documentation: https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html
Expected rows: 144
Expected date range: 1949-01 through 1960-12
Expected raw value unit: thousands of passengers
Canonical analysis field: passengers_thousands
```

Schema phải được kiểm tra từ file tải thực tế. Nếu CSV có cột index `rownames`, cột
này không được xem là biến phân tích. Cột thời gian dạng fractional year phải được
validate theo tài liệu nguồn trước khi tạo monthly `DatetimeIndex`; không parse số
thập phân thành timestamp bằng suy đoán.

Trước khi phân tích phải xác minh:

- source của dataset;
- schema;
- timestamp;
- chronological order;
- missing values;
- duplicate timestamps;
- frequency thực tế.

---

## 4. Required Steps

### Step 1 — Load dataset

Đọc dataset mà không làm thay đổi raw data.

### Step 2 — Inspect dataset

Thực hiện tối thiểu:

```text
head
info
shape
time range
missing-value check
duplicate timestamp check
```

### Step 3 — Validate time index

Xác minh:

```text
timestamp parse được
chronological order đúng
frequency phù hợp
không có timestamp bất thường chưa được giải thích
```

### Step 4 — Plot original series

Vẽ toàn bộ chuỗi để quan sát:

```text
trend
seasonality
variance behavior
possible anomalies
```

### Step 5 — Compute ACF

Tính:

```text
Maximum lag: 40
Confidence level: 95%
```

### Step 6 — Compute PACF

Tính:

```text
Maximum lag: 40
Confidence level: 95%
```

Nếu số lượng observations hoặc phương pháp PACF không hỗ trợ 40 lags hợp lệ thì phải dừng và báo cáo, không tự giảm lag.

### Step 7 — Interpret results

Phải trả lời các câu hỏi ở Section 8.

---

## 5. Scientific Method

### 5.1 ACF

ACF được sử dụng để đánh giá mức độ tương quan giữa:

```text
y_t
và
y_(t-k)
```

ở các lag khác nhau.

Phân tích tập trung vào:

- mức độ decay của ACF;
- các spike vượt confidence interval;
- pattern lặp lại theo lag;
- dấu hiệu seasonal dependence.

### 5.2 PACF

PACF được dùng để đánh giá mối quan hệ trực tiếp giữa:

```text
y_t
và
y_(t-k)
```

sau khi loại ảnh hưởng tuyến tính của các lag trung gian.

PACF trong Exercise 1 dùng để khám phá temporal structure, không dùng để tự động chọn forecasting model.

### 5.3 Confidence Interval

Sử dụng:

```text
Confidence level: 95%
```

Các lag vượt confidence bound được xem là evidence cần xem xét, không đồng nghĩa tự động với causal relationship.

---

## 6. Scientific Parameters

```text
Dataset: AirPassengers
Frequency: monthly
Seasonal period: 12
Maximum ACF lag: 40
Maximum PACF lag: 40
Confidence level: 95%
Statsmodels alpha: 0.05
PACF method: ywm
```

Không có:

```text
train/validation/test split
model fitting
forecast generation
model evaluation
```

trong Exercise 1.

---

## 7. Expected Outputs

### Figures

```text
01_time_series_overview.png
02_acf_40_lags.png
03_pacf_40_lags.png
```

Lưu tại:

```text
outputs/figures/
```

### Machine-readable results

Nếu cần:

```text
acf_values.csv
pacf_values.csv
```

Lưu tại:

```text
outputs/results/
```

### Narrative output

Phải có interpretation bằng văn bản dựa trên actual outputs.

---

## 8. Interpretation Questions

Exercise 1 phải trả lời:

1. Chuỗi có tự tương quan mạnh không?
2. ACF giảm nhanh hay giảm chậm?
3. Có spike lặp lại theo chu kỳ không?
4. Có dấu hiệu seasonality ở lag 12, 24, 36 hay không?
5. PACF cho thấy lag nào nổi bật?
6. Lag nào có thể xem là quan trọng nhất dựa trên evidence?
7. ACF/PACF có cho thấy chuỗi giống white noise không?
8. Có dấu hiệu trend hoặc non-stationary behavior cần kiểm tra thêm không?

Không được trả lời trước khi actual ACF/PACF được tạo.

---

## 9. Validation Criteria

Exercise 1 đạt khi:

```text
[ ] Dataset đã được load thành công
[ ] Raw data không bị sửa
[ ] Time index đã được validate
[ ] Chronological order được bảo toàn
[ ] Missing values đã được kiểm tra
[ ] Duplicate timestamps đã được kiểm tra
[ ] Original series plot đã được tạo
[ ] ACF đã được tính đến 40 lags
[ ] PACF đã được tính đến 40 lags
[ ] Confidence level là 95%
[ ] Statsmodels alpha = 0.05
[ ] PACF method = ywm
[ ] Figures đã được inspect
[ ] Interpretation dựa trên actual outputs
[ ] Không fabricate lag hoặc conclusion
```

---

## 10. Stop Conditions

Phải dừng Exercise 1 nếu:

```text
dataset source chưa được xác minh
timestamp không parse được
time index không hợp lệ
không đủ observations để tính requested lag
ACF/PACF computation fail
missing values làm analysis không hợp lệ
raw dataset bị thay đổi
scientific parameter cần đổi ngoài specification
```

Khi gặp stop condition:

```text
STOP
→ document issue
→ explain impact
→ propose next action
→ wait for approval
```

---

## 11. Completion Condition

Exercise 1 chỉ được xem là `COMPLETED` khi:

```text
dataset validation complete
AND original series inspected
AND ACF output validated
AND PACF output validated
AND interpretation questions answered
AND outputs saved
AND no unresolved blocking issue
```

---

## 12. Downstream Role

Kết quả Exercise 1 sẽ được dùng làm evidence cho:

```text
Exercise 2 — White Noise comparison
Exercise 3 — Decomposition interpretation
Exercise 5 — Visualization synthesis
User-owned Word report — outside the AI implementation plan
```

Exercise 1 không tự quyết định forecasting model.
