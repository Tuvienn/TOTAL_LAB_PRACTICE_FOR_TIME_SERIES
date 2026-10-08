# EXERCISE 04 — TIME SERIES DATA QUALITY

## 1. Exercise Identity

```text
Practice: Practice_1
Exercise ID: EXERCISE_04
Topic: Time Series Data Quality
Dataset: AirPassengers
Frequency: Monthly
Missing-value methods:
- Forward-fill
- Time interpolation
Primary outlier basis: Decomposition residual
Model training required: NO
Status: READY_FOR_HUMAN_APPROVAL
```

---

## 2. Objective

Mục tiêu của bài tập:

- phát hiện missing values trong dữ liệu chuỗi thời gian;
- tạo missing values giả lập trên working copy;
- so sánh hai phương pháp xử lý missing;
- đánh giá kết quả bằng true values đã lưu;
- phát hiện các điểm bất thường;
- phân biệt outlier tiềm năng với seasonal peak;
- quan sát ảnh hưởng trước và sau khi xử lý dữ liệu;
- bảo toàn raw dataset.

---

## 3. Input

Dataset chính:

```text
AirPassengers
```

Thông tin liên quan:

```text
Frequency: monthly
Seasonal period: 12
Raw dataset: immutable
```

Exercise 4 sử dụng:

```text
validated AirPassengers series
```

từ các exercise trước.

Đối với outlier analysis, có thể tái sử dụng:

```text
decomposition residual
```

đã được tạo và validate ở Exercise 3.

---

## 4. Data Safety Boundary

Raw data:

```text
data/raw/
```

không được sửa.

Mọi thí nghiệm missing values phải thực hiện trên:

```text
working copy
```

Luồng bắt buộc:

```text
validated original series
→ copy
→ select positions
→ save true values
→ mask selected positions
→ apply treatment methods
→ compare reconstructed values with true values
```

Không ghi dữ liệu giả lập missing trở lại raw dataset.

---

## 5. Required Steps

### Step 1 — Load Validated Series

Sử dụng cùng AirPassengers dataset đã được xác minh trước đó.

Kiểm tra lại tối thiểu:

```text
shape
time range
missing count
chronological order
```

### Step 2 — Check Existing Missing Values

Dùng:

```text
isna().sum()
```

để xác định dataset ban đầu có missing values hay không.

Kết quả phải được ghi lại trước khi tạo missing giả lập.

### Step 3 — Create Working Copy

Tạo working copy từ validated series.

```text
raw series
→ unchanged

working series
→ experiment only
```

### Step 4 — Select Missing Positions

Chọn một tập vị trí để mô phỏng missing values.

Các vị trí phải:

```text
được ghi lại
không làm thay đổi timestamp
không xóa observation
có true values được lưu trước khi mask
```

Missing-position protocol đã khóa:

```text
Isolated timestamps: 1952-03, 1954-11, 1959-04
Consecutive block: 1956-06 through 1956-08
Total masked observations: 6
Boundary rule: no masked point occurs in the first or last 12 observations
```

Không được chọn vị trí khác nhau cho từng treatment method.

### Step 5 — Mask Selected Values

Tại các vị trí đã chọn:

```text
observed value → NaN
```

Chỉ thay đổi working copy.

### Step 6 — Verify Missing Values

Dùng lại:

```text
isna().sum()
```

để xác nhận số missing được tạo đúng như thiết kế.

### Step 7 — Apply Forward-Fill

Tạo một treatment copy và áp dụng:

```text
forward-fill
```

Không overwrite working series dùng cho phương pháp khác.

### Step 8 — Apply Time Interpolation

Tạo treatment copy khác và áp dụng:

```text
Series.interpolate(method="time", limit_area="inside")
```

Không extrapolate ở boundary. Locked missing positions đều nằm bên trong chuỗi nên
hai phương pháp phải reconstruct đủ sáu vị trí; nếu còn NaN thì phải dừng.

Hai phương pháp phải sử dụng:

```text
cùng original series
cùng missing positions
cùng true values
```

để đảm bảo comparison công bằng.

### Step 9 — Compare Treatments

So sánh reconstructed values tại đúng các vị trí đã mask.

Comparison tối thiểu phải xem:

```text
true value
forward-fill value
interpolated value
absolute reconstruction error
```

Summary metric bắt buộc là:

```text
MAE calculated only on the six masked positions
```

Không tính MAE trên toàn bộ dataset để đánh giá reconstruction.

### Step 10 — Detect Potential Outliers

Đề bài cho phép một trong các phương pháp:

```text
Rolling mean / variance
Z-score
IQR
```

Trong Practice 1, project ưu tiên phân tích:

```text
decomposition residual
```

từ Exercise 3 để tránh nhầm seasonal peaks với outliers.

Outlier protocol đã khóa:

```text
Input: STL residual on the natural-log scale from Exercise 3
Method: IQR
Lower fence: Q1 - 1.5 × IQR
Upper fence: Q3 + 1.5 × IQR
Action: flag and inspect only
Automatic deletion/replacement: NO
```

### Step 11 — Inspect Potential Outliers

Các điểm được flag phải được đối chiếu với:

```text
original series
timestamp
seasonal pattern
decomposition residual
```

Không được tự động kết luận mọi flagged point là anomaly thực sự.

### Step 12 — Plot Before and After

Phải trực quan hóa ít nhất:

```text
original series
series with simulated missing values
forward-filled series
interpolated series
potential outliers
```

Mục tiêu là quan sát tác động của data treatment.

### Step 13 — Write Interpretation

Trả lời các câu hỏi ở Section 9.

---

## 6. Scientific Method

### 6.1 Missing-Value Experiment

Thí nghiệm missing-value phải có ground truth.

Do AirPassengers ban đầu được dùng như validated complete series, ta:

```text
giữ lại true values
→ cố ý che một số observation
→ reconstruction
→ so sánh reconstructed value với true value
```

Nhờ đó comparison giữa forward-fill và interpolation có evidence thay vì chỉ nhìn bằng mắt.

### 6.2 Forward-Fill

Forward-fill thay missing observation bằng giá trị quan sát gần nhất trong quá khứ.

Ưu điểm:

```text
simple
không dùng future value
```

Hạn chế:

```text
có thể tạo plateau
không phản ánh tốt series đang tăng/giảm nhanh
```

Không mặc định forward-fill tốt hay xấu trước actual experiment.

### 6.3 Time Interpolation

Time interpolation ước lượng missing value dựa trên vị trí thời gian và các observation xung quanh.

Có thể phù hợp hơn khi biến thay đổi tương đối trơn theo thời gian.

Tuy nhiên:

```text
interpolation có thể dùng thông tin ở cả hai phía của missing point
```

nên trong bài này nó là phương pháp **data reconstruction/quality analysis**, không được hiểu mặc định là forecasting-safe preprocessing.

### 6.4 Outlier Analysis

AirPassengers có seasonality mạnh.

Vì vậy:

```text
giá trị lớn theo mùa
≠
tự động là outlier
```

Project ưu tiên decomposition residual vì trend và seasonality đã được tách trước.

Một residual lớn chỉ là:

```text
potential outlier
```

cho đến khi được inspect.

---

## 7. Scientific Parameters

```text
Dataset: AirPassengers
Frequency: monthly
Missing detection: isna().sum()
Treatment method 1: forward-fill
Treatment method 2: time interpolation
Interpolation method: time
Interpolation limit_area: inside
Missing positions: identical across methods
Ground truth: preserved before masking
Primary outlier evidence: STL decomposition residual
Masked observations: 6
Isolated masked timestamps: 1952-03, 1954-11, 1959-04
Consecutive masked block: 1956-06 through 1956-08
Reconstruction summary metric: MAE on masked positions only
Outlier method: IQR on log-STL residual
Outlier multiplier: 1.5
Automatic outlier removal: NO
```

---

## 8. Expected Outputs

### Figures

Tối thiểu:

```text
10_missing_values_simulation.png
11_missing_treatment_comparison.png
12_outlier_analysis.png
```

Có thể tách thêm figure nếu một figure trở nên quá khó đọc.

Lưu tại:

```text
outputs/figures/
```

### Machine-readable Results

Dự kiến:

```text
missing_value_comparison.csv
outlier_candidates.csv
```

`missing_value_comparison.csv` có thể gồm:

```text
timestamp
true_value
forward_fill_value
interpolation_value
forward_fill_absolute_error
interpolation_absolute_error
```

`outlier_candidates.csv` có thể gồm:

```text
timestamp
observed_value
residual_log
q1
q3
iqr
lower_fence
upper_fence
flag
```

Tùy scientific method được khóa sau.

Lưu tại:

```text
outputs/results/
```

---

## 9. Interpretation Questions

Exercise 4 phải trả lời:

1. Dataset gốc có missing values hay không?
2. Có bao nhiêu missing values được tạo giả lập?
3. Forward-fill tái tạo các missing observations như thế nào?
4. Time interpolation tái tạo như thế nào?
5. Phương pháp nào có reconstruction error thấp hơn trong experiment này?
6. Có trường hợp nào forward-fill tốt hơn interpolation không?
7. Có trường hợp nào interpolation tốt hơn forward-fill không?
8. Phương pháp nào làm thay đổi hình dạng chuỗi rõ hơn?
9. Những điểm nào được flag là potential outliers?
10. Các điểm đó có thực sự bất thường hay có thể chỉ là seasonal peaks?
11. Residual decomposition giúp phân biệt outlier với seasonality như thế nào?
12. Có nên tự động xóa các outlier này không? Vì sao?

Không được kết luận treatment nào tốt hơn trước actual comparison.

---

## 10. Validation Criteria

Exercise 4 đạt khi:

```text
[ ] Validated AirPassengers series được sử dụng
[ ] Raw dataset không bị sửa
[ ] Existing missing values đã được kiểm tra
[ ] Working copy được tạo
[ ] True values được lưu trước masking
[ ] Missing positions giống nhau cho cả hai methods
[ ] Missing count sau masking được xác nhận
[ ] Forward-fill được thực hiện
[ ] Time interpolation được thực hiện
[ ] Interpolation dùng method = time và limit_area = inside
[ ] Reconstruction comparison sử dụng đúng masked positions
[ ] MAE được tính riêng cho từng method trên đúng 6 masked positions
[ ] Potential outliers được phát hiện bằng approved method
[ ] Flagged points được inspect
[ ] Không tự động xóa hoặc replace outlier
[ ] Before/after plots được tạo
[ ] Interpretation dựa trên actual outputs
[ ] Không fabricate result
```

---

## 11. Stop Conditions

Phải dừng Exercise 4 nếu:

```text
raw dataset bị sửa
true values không được lưu trước masking
hai treatment methods dùng missing positions khác nhau
timestamp bị mất hoặc thay đổi
forward-fill/interpolation computation fail
masked positions làm experiment không còn hợp lệ
decomposition residual từ Exercise 3 chưa được validate nhưng đang được dùng
outlier protocol không khớp IQR multiplier 1.5 trên log-STL residual
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

## 12. Completion Condition

Exercise 4 chỉ được xem là `COMPLETED` khi:

```text
missing experiment reproducible
AND both treatment methods completed
AND reconstruction comparison validated
AND outlier analysis completed
AND before/after outputs inspected
AND interpretation questions answered
AND raw data remains unchanged
AND no unresolved blocking issue
```

---

## 13. Downstream Role

Kết quả Exercise 4 sẽ được dùng làm evidence cho:

```text
Exercise 5 — Visualization synthesis
User-owned Word report — outside the AI implementation plan
```

Exercise 4 không tạo cleaned dataset mặc định cho forecasting.

Bất kỳ quyết định preprocessing nào cho forecasting về sau phải được đánh giá lại trong lab/modeling stage khác.
