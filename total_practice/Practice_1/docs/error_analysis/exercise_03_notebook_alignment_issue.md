# EXERCISE 03 — PHÂN TÍCH HIỆN TRẠNG NOTEBOOK

## 1. Thông tin vấn đề

```text
Practice: Practice_1
Exercise: 03 — Time Series Decomposition
Notebook chính: notebooks/practice_1_present.ipynb
Phạm vi cell: 28–31
Trạng thái phân tích: ĐÃ_PHÂN_TÍCH
Trạng thái triển khai: ĐÃ_HOÀN_THÀNH_VÀ_XÁC_MINH
Chờ Human phê duyệt: KHÔNG
```

Mục tiêu của lần rà soát này là giữ nguyên những phần E3 đang làm đúng, xác định
chính xác các điểm chưa khớp specification và lập ranh giới an toàn trước khi sửa.

Tài liệu này chỉ ghi nhận hiện trạng. Việc tạo tài liệu không cho phép sửa notebook,
source code, tests hoặc generated outputs.

## 2. Phạm vi đã xác minh

```text
Exercise 1–2: cell 0–27
Exercise 3: cell 28–31
Exercise 4 bắt đầu: cell 32
Tổng số cell notebook: 52
```

Cell 32 đã chuyển sang mô phỏng missing values nên không thuộc E3. Mọi thay đổi E3
sau khi được duyệt phải dừng tại cell 31.

## 3. Phần đang làm tốt và cần giữ

### Cell 28 — STL decomposition

Các lựa chọn sau phù hợp với cấu hình khoa học và cần được giữ:

```text
decomposition method: STL
seasonal period: 12
robust: True
four components: Observed, Trend, Seasonal, Residual
shared time axis
grid và bố cục bốn panel
```

### Cell 29 — Diễn giải cấu trúc chuỗi

Các ý đúng cần giữ:

- trend của AirPassengers tăng trong giai đoạn 1949–1960;
- seasonal pattern lặp lại theo chu kỳ 12 tháng;
- không kết luận residual là white noise chỉ bằng quan sát trực quan;
- cần kết hợp residual ACF và Ljung–Box.

### Cell 30 — Residual diagnostics

Các thành phần đúng cần giữ:

```text
residual ACF maximum lag: 40
Ljung–Box diagnostic
ACF figure có title rõ ràng
```

### Cell 31 — Quy tắc đọc p-value

Quy tắc `p-value ≤ 0.05` là đúng về mặt diễn giải bằng chứng chống lại giả thuyết
không có tự tương quan. Tuy nhiên, quy tắc này phải được gắn với kết quả thực tế và
chỉ được xem là supplementary evidence.

## 4. Điểm chưa phù hợp

### 4.1. STL đang chạy trên sai thang đo

Cell 28 hiện chạy:

```python
series = df.set_index("date")["value"].asfreq("MS")
stl = STL(series, period=12, robust=True)
```

Trong khi configuration, specification và before-process plan đã chốt:

```text
transform: natural logarithm
decomposition: transformed-additive STL
period: 12
robust: True
```

Notebook chưa tạo working copy và chưa tính `log(y)`. Vì vậy decomposition, residual,
ACF và Ljung–Box hiện tại đều thuộc thang số hành khách gốc, không phải thang log đã
duyệt.

### 4.2. Thiếu kiểm tra điều kiện trước log transform

Notebook chưa chứng minh:

```text
mọi giá trị đều lớn hơn 0
không có NaN hoặc infinity
index được sắp xếp tăng dần
tần suất là monthly start (MS)
index được bảo toàn sau biến đổi
raw series không bị sửa
```

Kiểm tra chẩn đoán chỉ đọc xác nhận dataset hiện có 144 giá trị dương, không thiếu
và đủ điều kiện lấy log. Các kiểm tra này vẫn phải xuất hiện trong implementation
chính thức thay vì được giả định ngầm.

### 4.3. Logic dùng lại đang nằm trong notebook

Notebook hiện trực tiếp sở hữu:

```text
log/STL workflow
component extraction
residual ACF
Ljung–Box diagnostic
decomposition plotting
residual plotting
```

Theo architecture rule, reusable analytical logic phải thuộc
`src/practice_1/analysis/`, còn reusable plotting logic phải thuộc
`src/practice_1/visualization/`.

### 4.4. Thiếu figure của chuỗi log

Output bắt buộc chưa tồn tại:

```text
outputs/figures/07_log_transformed_series.png
```

Notebook cũng chưa trình bày sự khác nhau giữa seasonal amplitude trên thang gốc và
thang log.

### 4.5. Decomposition figure chưa được lưu

Cell 28 chỉ hiển thị figure trong notebook bằng `plt.show()`. Output bắt buộc chưa
tồn tại:

```text
outputs/figures/08_stl_decomposition.png
```

Title và axis label hiện chưa nói rõ các component nằm trên natural-log scale.

### 4.6. Residual figure chưa đầy đủ

Specification yêu cầu `09_decomposition_residual.png` gồm:

```text
residual time plot
residual ACF đến 40 lag
95% confidence interval
```

Notebook hiện chỉ hiển thị ACF residual trong một figure riêng và không lưu file.

### 4.7. Chưa xuất kết quả machine-readable

Các output sau chưa tồn tại:

```text
outputs/results/decomposition_components.csv
outputs/results/residual_diagnostics.csv
```

Bảng component cần có timestamp, `observed_log`, `trend_log`, `seasonal_log` và
`residual_log`. Bảng diagnostic phải ghi actual lag 12, Ljung–Box statistic và
p-value.

### 4.8. Ljung–Box chưa theo đúng output contract

Cell 30 đang chạy đồng thời lag 12 và 24 rồi chỉ in bảng ra notebook. Lag 24 có thể
được xem là thông tin bổ sung, nhưng required diagnostic đã khóa tại lag 12 và phải
được lưu thành CSV. Kết luận không được dựa duy nhất vào p-value.

### 4.9. Diễn giải chưa dựa đầy đủ trên actual results

Cell 29 chủ yếu là nhận xét tổng quát; cell 31 chỉ ghi quy tắc đọc p-value. Phần hiện
tại chưa trả lời đầy đủ mười câu hỏi bắt buộc về:

```text
tốc độ thay đổi của trend
độ mạnh và chu kỳ seasonality
seasonal amplitude trên original scale
tác động của log transform
remaining residual pattern
remaining seasonality
white-noise similarity
residual bất thường nổi bật
```

### 4.10. E3 chưa có heading và chưa được chạy sạch trong luồng hiện tại

Cell 28 bắt đầu bằng code ngay sau phần kết luận E2. E3 chưa có heading hoặc mục tiêu
riêng. Execution count hiện là 19 và 20, trong khi E1–E2 đã được chạy lại bằng kernel
sạch; đây là output cũ và không phải bằng chứng validation cho trạng thái hiện tại.

## 5. Bằng chứng chẩn đoán chỉ đọc

Kết quả kiểm tra trước triển khai:

```text
observations: 144
frequency: MS
missing values: 0
all values positive: True

STL trên original scale:
residual mean: 0.274142
residual sample standard deviation: 6.916402
ACF lag 1: 0.248284
ACF lag 12: -0.059194
Ljung–Box lag-12 p-value: 0.000239
largest absolute residual: 1959-03

STL trên natural-log scale theo contract:
residual mean: 0.000290
residual sample standard deviation: 0.026527
ACF lag 1: 0.374728
ACF lag 12: -0.133553
Ljung–Box lag-12 p-value: 0.000037
ACF lags vượt confidence interval 95%: 1, 2
largest absolute residual: 1953-04
```

Các số trên chỉ là baseline chẩn đoán. Kết quả chính thức phải được tái tạo bằng API
đã kiểm thử, xuất ra file và chạy trong notebook sau khi Human phê duyệt.

Baseline cho thấy residual trên thang log vẫn còn bằng chứng tự tương quan. Vì vậy
không được kết luận residual là white noise hoàn toàn.

## 6. Nguyên nhân gốc

Phần E3 hiện có được viết như một đoạn exploratory notebook độc lập trước khi project
chuẩn hóa:

```text
scientific configuration
source ownership
output naming
validation gates
machine-readable evidence
```

Do đó code hiện thể hiện đúng ý tưởng cơ bản của decomposition nhưng chưa được đồng
bộ với contract `log transform + STL`, kiến trúc package và quy trình xác minh đã
duyệt.

## 7. Ảnh hưởng

Nếu giữ nguyên E3 hiện tại:

- decomposition không đúng scientific design decision;
- residual scale bị diễn giải sai;
- Ljung–Box hiện tại không phải bằng chứng cho residual log;
- kết quả không thể tái sử dụng an toàn ở E4 để phân tích outlier;
- notebook thiếu output truy vết được và chưa đạt completion gate;
- người đọc không thể kiểm tra đầy đủ mười kết luận bắt buộc.

## 8. Ranh giới bảo vệ

```text
Exercise 1–2: không sửa
Exercise 3: chỉ cell 28–31
Exercise 4–5: không sửa
raw dataset: không sửa
validated E1/E2 outputs: không ghi đè
config/practice_1.json: không sửa
không thêm dependency
không train model hoặc tạo forecast
```

Checksum baseline ngày 2026-10-12:

```text
notebook:
0cb6ed1f6f167093469e66b69e5a4fc5ba11090ce201bcdf7389a75af0ed66bf

source và loại cell E1–E2:
baa231632af529bcf729d6b0f7278f25c63219e44c8211d73fa587dca586fe2d

source và loại cell E3:
5d3670253e28673d1396263b437ca89b9883df8ad611eac7345d7e8dbbed3f1f

source và loại cell E4–E5:
d95ada507e4fc960ea3757804cdec9feb5d12fcbf951e7f808610f6ab38f7c26

raw dataset:
bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8
```

Trình tự sửa và validation được đề xuất trong
`docs/fix_plans/exercise_03_notebook_alignment_fix_plan.md`.

## 9. Trạng thái quyết định

```text
Phân tích lỗi đã hoàn tất: CÓ
Fix plan đã được tạo: CÓ
Human đã phê duyệt fix plan: CÓ
Cho phép triển khai E3: CÓ
```

## 10. Kết quả xử lý

Vấn đề đã được xử lý và xác minh ngày 2026-10-12:

```text
STL đã chuyển sang natural-log working series
precondition và component reconstruction đã được kiểm tra
reusable logic thuộc src/practice_1/analysis/ và visualization/
ba figure và hai CSV E3 đã được tạo, inspect và đối chiếu
residual được đánh giá bằng time plot, ACF 40 lag và Ljung–Box lag 12
mười câu hỏi được trả lời bằng actual output
19 code cell từ E1 đến hết E3 chạy sạch
20 test E1–E3 đều đạt
raw data, E1–E2 và cell E4–E5 không thay đổi
```

Bằng chứng chi tiết được ghi tại `docs/logs/exercise_03_execution.md`.

