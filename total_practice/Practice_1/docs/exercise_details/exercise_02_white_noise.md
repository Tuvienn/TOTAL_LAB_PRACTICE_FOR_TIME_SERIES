# EXERCISE 02 — WHITE NOISE ANALYSIS

## 1. Exercise Identity

```text
Practice: Practice_1
Exercise ID: EXERCISE_02
Topic: White Noise
Reference series: AirPassengers
Synthetic sample size: 1000
Confidence level: 95%
Random seed: 42
Synthetic distribution: Normal(0, 1)
Maximum ACF lag: 40
Model training required: NO
Status: COMPLETED
```

---

## 2. Objective

Mục tiêu của bài tập:

- hiểu đặc điểm của một chuỗi white noise;
- tạo chuỗi white noise bằng NumPy;
- kiểm tra autocorrelation của white noise bằng ACF;
- quan sát confidence interval 95%;
- so sánh white noise với chuỗi AirPassengers;
- phân biệt chuỗi không có temporal structure với chuỗi có temporal dependence.

---

## 3. Input

Exercise 2 sử dụng hai input.

### 3.1 Synthetic White Noise

Sinh bằng NumPy:

```text
Number of observations: 1000
Random seed: 42
Distribution: Normal(mean=0, standard deviation=1)
```

Random seed phải được cố định để kết quả có thể tái tạo.

Generator contract:

```text
NumPy Generator: numpy.random.default_rng(42)
Distribution: normal(loc=0.0, scale=1.0, size=1000)
```

### 3.2 AirPassengers

Chuỗi AirPassengers được dùng làm chuỗi thực tế để so sánh ACF.

Thông tin liên quan:

```text
Frequency: monthly
Seasonal period: 12
```

Dataset phải là cùng nguồn dữ liệu đã được xác minh ở Exercise 1.

---

## 4. Required Steps

### Step 1 — Generate White Noise

Tạo chuỗi white noise gồm:

```text
1000 observations
```

với explicit random seed:

```text
seed = 42
```

Không regenerate với seed khác trong cùng experiment.

### Step 2 — Inspect White Noise

Kiểm tra tối thiểu:

```text
shape
mean
standard deviation
basic visualization
```

Mục đích là xác nhận chuỗi synthetic đã được tạo đúng.

### Step 3 — Plot White Noise

Vẽ chuỗi white noise theo observation order để quan sát behavior.

### Step 4 — Compute White Noise ACF

Tính và vẽ ACF của white noise.

Phải hiển thị:

```text
Maximum lag: 40
95% confidence interval
```

Quan sát xem các autocorrelation tại các lag có chủ yếu nằm trong confidence bounds hay không.

### Step 5 — Obtain AirPassengers ACF

Sử dụng ACF của AirPassengers.

Ưu tiên tái sử dụng validated output hoặc reusable logic từ Exercise 1, không duplicate unnecessary logic.

### Step 6 — Compare ACF Patterns

So sánh:

```text
White Noise ACF
vs
AirPassengers ACF
```

Tập trung vào:

```text
significant spikes
decay pattern
repeated seasonal pattern
strength of temporal dependence
```

### Step 7 — Write Comparison

Viết tối thiểu:

```text
5 dòng mô tả sự khác nhau
```

theo đúng yêu cầu bài tập.

---

## 5. Scientific Method

### 5.1 White Noise

Trong Exercise 2, white noise được dùng như một conceptual baseline cho chuỗi không có temporal structure đáng kể.

Expected characteristics cần kiểm tra bằng actual output:

```text
mean gần ổn định
variance gần ổn định
autocorrelation tại các lag khác 0 gần 0
đa số ACF spikes nằm trong confidence interval
```

Không được kết luận các đặc điểm này đã đạt trước khi chạy actual experiment.

### 5.2 ACF Comparison

ACF được dùng để so sánh mức độ temporal dependence giữa:

```text
synthetic white noise
và
AirPassengers
```

White noise được kỳ vọng có ACF yếu hơn đáng kể so với AirPassengers.

Tuy nhiên kết luận cuối phải dựa trên actual plots.

### 5.3 Confidence Interval

Sử dụng:

```text
Confidence level: 95%
```

Một số spike riêng lẻ vượt confidence bounds vẫn có thể xuất hiện ngẫu nhiên.

Vì vậy không được kết luận:

```text
"không phải white noise"
```

chỉ dựa trên một spike riêng lẻ.

---

## 6. Scientific Parameters

```text
Synthetic process: White Noise
Number of observations: 1000
Random seed: 42
Distribution: Normal(0, 1)
Maximum ACF lag: 40
Confidence level: 95%
Reference dataset: AirPassengers
Reference frequency: monthly
Reference seasonal period: 12
```

### Supplementary Diagnostic

Nếu Practice 1 overview vẫn giữ định hướng đã thống nhất, có thể sử dụng:

```text
Ljung-Box test
```

như một diagnostic bổ sung.

Lưu ý:

```text
Ljung-Box = supplementary analysis
không phải yêu cầu bắt buộc của đề gốc
```

Kết quả Ljung-Box không được thay thế ACF comparison mà đề bài yêu cầu.

---

## 7. Expected Outputs

### Figures

Tối thiểu:

```text
04_white_noise_series.png
05_white_noise_acf.png
06_white_noise_vs_airpassengers_acf.png
```

Lưu tại:

```text
outputs/figures/
```

Có thể dùng side-by-side comparison hoặc hai figure riêng, miễn comparison rõ ràng.

### Machine-readable Results

Nếu cần:

```text
white_noise_acf_values.csv
white_noise_diagnostics.csv
```

Lưu tại:

```text
outputs/results/
```

### Narrative Output

Phải có ít nhất:

```text
5 dòng so sánh White Noise và AirPassengers
```

Nội dung phải dựa trên actual ACF outputs.

---

## 8. Interpretation Questions

Exercise 2 phải trả lời:

1. White noise series có pattern rõ ràng theo thời gian không?
2. Phần lớn ACF spikes của white noise có nằm trong confidence interval 95% không?
3. Có spike nào vượt confidence interval không?
4. Nếu có, một vài spike riêng lẻ có đủ để phủ nhận white-noise behavior không?
5. ACF của AirPassengers khác white noise như thế nào?
6. AirPassengers có temporal dependence mạnh hơn không?
7. Có pattern lặp lại theo seasonal lags trong AirPassengers không?
8. Kết quả này giúp hiểu gì về khái niệm white noise?

Không được viết kết luận trước khi actual output được tạo.

---

## 9. Validation Criteria

Exercise 2 đạt khi:

```text
[ ] Random seed được cố định ở 42
[ ] White noise có đúng 1000 observations
[ ] White noise được sinh từ Normal(0, 1)
[ ] White noise series đã được inspect
[ ] White noise plot đã được tạo
[ ] ACF của white noise đã được tạo
[ ] ACF của white noise dùng maximum lag = 40
[ ] Confidence level là 95%
[ ] AirPassengers ACF được lấy từ validated logic/output
[ ] Hai ACF đã được so sánh
[ ] Ít nhất 5 dòng comparison đã được viết
[ ] Interpretation dựa trên actual outputs
[ ] Không fabricate statistical result
```

Nếu dùng Ljung-Box:

```text
[ ] Ljung-Box được ghi rõ là supplementary diagnostic
[ ] p-value được đọc từ actual execution
[ ] không dùng Ljung-Box để thay thế ACF requirement
```

---

## 10. Stop Conditions

Phải dừng Exercise 2 nếu:

```text
random seed không được kiểm soát
white noise không có đúng 1000 observations
ACF computation fail
confidence interval không được hiển thị hoặc xác định
AirPassengers ACF chưa được validate
comparison đang dùng output không cùng protocol
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

Exercise 2 chỉ được xem là `COMPLETED` khi:

```text
white noise generated reproducibly
AND white-noise series inspected
AND white-noise ACF validated
AND AirPassengers ACF available
AND comparison completed
AND minimum 5-line interpretation written
AND outputs inspected
AND no unresolved blocking issue
```

---

## 12. Downstream Role

Kết quả Exercise 2 sẽ được dùng làm evidence cho:

```text
Exercise 3 — đánh giá residual sau decomposition
User-owned Word report — outside the AI implementation plan
```

Đặc biệt, khái niệm white noise từ Exercise 2 sẽ được dùng khi trả lời:

```text
"Residual sau decomposition có giống white noise không?"
```
