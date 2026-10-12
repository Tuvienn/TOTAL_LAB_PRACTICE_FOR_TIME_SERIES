# EXERCISE 02 — PHÂN TÍCH HIỆN TRẠNG NOTEBOOK

## 1. Thông tin vấn đề

```text
Practice: Practice_1
Exercise: 02 — White Noise
Notebook chính: notebooks/practice_1_present.ipynb
Phạm vi cell: 22–27
Trạng thái phân tích: ĐÃ_PHÂN_TÍCH
Trạng thái triển khai: ĐÃ_HOÀN_THÀNH_VÀ_XÁC_MINH
```

Mục tiêu của lần rà soát này là giữ nguyên các phần E2 đang làm tốt và chỉ sửa
những điểm không đáp ứng specification, before-process plan hoặc kiến trúc đã duyệt.

## 2. Phần đang làm tốt và cần giữ

### Cell 22 — Khởi tạo white noise

Giữ các tham số khoa học:

```text
số quan sát: 1000
seed: 42
phân phối: Normal(0, 1)
tên chuỗi: white_noise
```

### Cell 23 — Biểu đồ chuỗi

Giữ cách trình bày chuỗi theo thứ tự quan sát, kích thước hình và các thành phần
title, xlabel, ylabel, grid.

### Cell 24 — Công thức khoảng tin cậy

Giữ công thức xấp xỉ `±1.96 / sqrt(n)`. Phần giải thích đã nêu đúng đây là
ngưỡng xấp xỉ 95% và một spike vượt ngưỡng không tự động phủ nhận hành vi white noise.

### Cell 25 — ACF của white noise

Giữ maximum lag 40, confidence level 95%, stem plot và đường tham chiếu tại 0.

### Cell 26 — So sánh ACF

Giữ bố cục hai biểu đồ cạnh nhau để so sánh white noise và AirPassengers.

### Cell 27 — Diễn giải

Giữ cấu trúc tối thiểu năm ý so sánh. Nội dung chỉ cập nhật ở những vị trí cần
gắn với kết quả thực thi thực tế.

## 3. Điểm chưa phù hợp

### 3.1. Generator không đúng hợp đồng đã duyệt

Notebook hiện dùng:

```python
np.random.seed(42)
np.random.normal(...)
```

Specification yêu cầu:

```python
rng = np.random.default_rng(42)
rng.normal(loc=0.0, scale=1.0, size=1000)
```

Hai API tạo ra hai chuỗi khác nhau dù dùng cùng seed. Vì vậy hình, ACF và diễn
giải phải được tái tạo từ generator đúng hợp đồng.

Kết quả chẩn đoán chỉ đọc với generator đã duyệt:

```text
mean: -0.028891550995946837
sample standard deviation: 0.9892170876543358
approximate 95% bound: ±0.061980642139300234
lag vượt approximate bound: lag 1, ACF khoảng 0.08705487216529355
```

Các giá trị này chỉ là baseline kiểm tra trước triển khai; kết quả chính thức phải
được tạo lại trong execution cycle đã phê duyệt.

### 3.2. Thiếu kiểm tra dữ liệu tổng hợp

Notebook chỉ hiển thị năm giá trị đầu. Specification yêu cầu thêm shape, mean,
sample standard deviation, sample size, seed và distribution.

### 3.3. Logic dùng lại đang nằm trong notebook

Việc sinh white noise và vẽ hình E2 đang được triển khai trực tiếp trong notebook.
Kiến trúc quy định reusable analytical logic thuộc `src/practice_1/analysis/`
và reusable plotting logic thuộc `src/practice_1/visualization/`.

### 3.4. AirPassengers ACF bị tính lại

Cell 26 gọi lại `statsmodels.tsa.stattools.acf` trên `df["value"]` thay vì tái
sử dụng `outputs/results/acf_values.csv` hoặc bảng ACF đã được E1 xác minh.

### 3.5. Protocol khoảng tin cậy chưa đồng nhất

So sánh hiện dùng ngưỡng cố định `±1.96/sqrt(n)` cho cả hai chuỗi, trong khi
E1 lưu confidence interval do `statsmodels` tính. Công thức xấp xỉ có thể giữ
để giảng giải, nhưng bảng và hình so sánh phải dùng cùng protocol đã duyệt.

### 3.6. Output bắt buộc chưa tồn tại

```text
outputs/figures/04_white_noise_series.png
outputs/figures/05_white_noise_acf.png
outputs/figures/06_white_noise_vs_airpassengers_acf.png
outputs/results/white_noise_acf_values.csv
```

### 3.7. Diễn giải chưa gắn với kết quả thực tế

Cell 27 nói một vài spike có thể vượt ngưỡng nhưng không chỉ rõ số lượng, vị trí
và giá trị thực tế. Các câu hỏi diễn giải bắt buộc của E2 chưa được trả lời đầy đủ.

### 3.8. Thiếu tiêu đề E2

Cell 22 bắt đầu bằng code ngay sau ranh giới E1. Notebook cần tiêu đề rõ ràng để
phân biệt E2 với các exercise khác.

## 4. Ảnh hưởng

Nếu giữ nguyên toàn bộ phần hiện tại:

- kết quả không khớp generator contract;
- notebook không chứng minh đầy đủ mean và standard deviation;
- AirPassengers ACF có hai owner;
- output E2 không được lưu theo cấu trúc repository;
- diễn giải không truy vết được về số liệu thực tế;
- E2 không đạt completion gate dù hình hiển thị hợp lý.

## 5. Ranh giới bảo vệ

```text
Exercise 1: không sửa
Exercise 2: chỉ cell 22–27
Exercise 3–5: không sửa
raw dataset: không sửa
validated E1 outputs: chỉ đọc, không ghi đè
```

Checksum baseline:

```text
notebook:
56a1d70a28e28ea666f45047c1b1edf46312abdf202f1267c0af94d6122dfca8

source và loại cell E2:
9ad620833628b0ada61eedb07a4bfd323110ab80d8e2deb926c27e2a8fcfb3f4

raw data:
bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8

validated E1 ACF:
dace4669019161485248d41afcf8bdbfcad4532e22ebd8ccc2c4ffc19d40b69d
```

Trình tự sửa được đề xuất trong
`docs/fix_plans/exercise_02_notebook_alignment_fix_plan.md`.

## 6. Kết quả xử lý

Vấn đề đã được xử lý và xác minh ngày 2026-10-12:

```text
generator đã chuyển sang numpy.random.default_rng(42)
logic sinh white noise thuộc src/practice_1/analysis/
logic vẽ hình E2 thuộc src/practice_1/visualization/
cell 22–27 được đồng bộ, phần tốt được giữ theo kế hoạch
AirPassengers ACF được đọc từ output E1 đã kiểm chứng
ba hình và CSV E2 đã được tạo, kiểm tra
16 code cell từ E1 đến hết E2 chạy sạch
12 test E1/E2 đều đạt
raw data, E1 và cell E3–E5 không thay đổi
```

Bằng chứng chi tiết được ghi tại `docs/logs/exercise_02_execution.md`.
