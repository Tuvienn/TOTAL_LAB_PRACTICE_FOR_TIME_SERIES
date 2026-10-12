# EXERCISE 02 — KẾ HOẠCH ĐỒNG BỘ NOTEBOOK

## 1. Thông tin kế hoạch

```text
Practice: Practice_1
Exercise: 02 — White Noise
Notebook chính: notebooks/practice_1_present.ipynb
Phạm vi cell: 22–27
Mục tiêu: sửa tối thiểu, giữ nguyên các phần E2 đang đúng
Trạng thái kế hoạch: ĐÃ_TRIỂN_KHAI_VÀ_XÁC_MINH
Được phép triển khai: CÓ
```

Tài liệu phân tích:

```text
docs/error_analysis/exercise_02_notebook_alignment_issue.md
```

## 2. Nguyên tắc sửa

- không viết lại toàn bộ E2;
- giữ tham số khoa học và bố cục trực quan đang đúng;
- thay generator không đúng contract;
- tái sử dụng ACF đã kiểm chứng từ E1;
- chuyển logic dùng lại về đúng source owner;
- không thay đổi E1 hoặc E3–E5.

## 3. File được phép thay đổi sau phê duyệt

```text
notebooks/practice_1_present.ipynb, chỉ cell 22–27 và output tương ứng
src/practice_1/analysis/white_noise.py
src/practice_1/analysis/__init__.py
src/practice_1/visualization/diagnostic_plots.py
src/practice_1/visualization/__init__.py
tests/test_white_noise.py
outputs/figures/04_white_noise_series.png
outputs/figures/05_white_noise_acf.png
outputs/figures/06_white_noise_vs_airpassengers_acf.png
outputs/results/white_noise_acf_values.csv
docs/logs/exercise_02_execution.md
docs/status/current_status.md
docs/exercise_details/exercise_02_white_noise.md, chỉ trạng thái
docs/plans/exercise_02_before_process.md, chỉ approval/status
```

Không thêm Ljung–Box hoặc `white_noise_diagnostics.csv` trong lần này vì đây là
diagnostic tùy chọn, không cần thiết để hoàn thành yêu cầu gốc.

## 4. File và nội dung không được thay đổi

```text
cell 0–21 của Exercise 1
cell 28 trở đi của Exercise 3–5
datasets/raw/
outputs/results/acf_values.csv
outputs/results/pacf_values.csv
ba hình đã kiểm chứng của Exercise 1
config/practice_1.json
pyproject.toml
```

## 5. Bản đồ giữ và sửa theo cell

| Cell | Quyết định | Nội dung |
|---:|---|---|
| 22 | Sửa tối thiểu | Chuyển thành tiêu đề và mục tiêu E2 |
| 23 | Giữ bố cục, sửa logic | Sinh white noise đúng contract, hiển thị thống kê và biểu đồ |
| 24 | Giữ | Giữ công thức và cách giải thích khoảng tin cậy xấp xỉ |
| 25 | Giữ bố cục, sửa owner | Gọi hàm dùng chung để tính, lưu và vẽ ACF 40 lag |
| 26 | Giữ bố cục, sửa nguồn | Tái sử dụng validated E1 ACF và lưu hình so sánh |
| 27 | Giữ năm ý, cập nhật evidence | Trả lời đủ câu hỏi bằng actual results |

Số cell E2 vẫn là sáu. E3 tiếp tục bắt đầu tại cell 28.

## 6. Các bước triển khai

### Bước 1 — Ghi nhận baseline

Ghi checksum notebook, source/type của E1, E2 và E3–E5, raw dataset và
`outputs/results/acf_values.csv`.

### Bước 2 — Tạo owner cho white-noise analysis

Tạo `src/practice_1/analysis/white_noise.py` với hàm dùng:

```python
rng = numpy.random.default_rng(seed)
rng.normal(loc=mean, scale=standard_deviation, size=size)
```

Hàm phải kiểm tra `size > 0`, `standard_deviation > 0`, trả về
`pandas.Series` tên `white_noise`, không thay đổi NumPy global random state
và tái tạo đúng kết quả khi dùng cùng seed.

ACF tiếp tục gọi `compute_acf_table`; không tạo implementation ACF thứ hai.

### Bước 3 — Bổ sung hàm trực quan hóa

Bổ sung vào `src/practice_1/visualization/diagnostic_plots.py`:

```text
plot_white_noise_series
plot_acf_table
plot_acf_comparison
```

Các hàm nhận dữ liệu đã tính, thể hiện confidence interval và lưu hình bằng
`_save_figure`. Không đổi hành vi của ba hàm E1 hiện có.

### Bước 4 — Thêm kiểm thử tập trung

Tạo `tests/test_white_noise.py` để kiểm tra:

- đúng 1.000 quan sát và đúng tên Series;
- cùng seed tạo cùng kết quả;
- không thay đổi NumPy global random state;
- mean và sample standard deviation khớp baseline trong tolerance;
- bảng ACF chứa lag 0–40 và confidence interval;
- tham số không hợp lệ bị từ chối.

### Bước 5 — Đồng bộ cell 22–27

- Cell 22: tiêu đề, mục tiêu và tham số E2.
- Cell 23: gọi generator, hiển thị size/mean/sample std/seed/distribution; tạo,
  lưu và hiển thị `04_white_noise_series.png`.
- Cell 24: giữ công thức và ý nghĩa hiện tại.
- Cell 25: gọi `compute_acf_table(max_lag=40, alpha=0.05)`; lưu CSV; tạo,
  lưu và hiển thị `05_white_noise_acf.png`.
- Cell 26: dùng bảng ACF E1 đã kiểm chứng, không tính lại AirPassengers ACF; tạo,
  lưu và hiển thị `06_white_noise_vs_airpassengers_acf.png`.
- Cell 27: giữ cấu trúc năm ý, bổ sung actual mean/std, số và vị trí spike vượt
  khoảng tin cậy, decay và seasonal pattern.

### Bước 6 — Thực thi

Khởi động kernel sạch `time-series-practice-1` và chạy tuần tự cell 0–27.
Không chạy hoặc sửa cell 28 trở đi.

### Bước 7 — Xác minh output

Kiểm tra ba hình không bị cắt/chồng lấn, nhãn rõ, lag 0–40 đầy đủ và confidence
interval đúng. Đối chiếu CSV với bảng trong notebook.

### Bước 8 — Cập nhật bằng chứng

Sau khi validation đạt, tạo `docs/logs/exercise_02_execution.md`, cập nhật
`docs/status/current_status.md`, trạng thái specification/plan E2 và giữ E3
ở trạng thái chưa triển khai.

## 7. Baseline và validation

Baseline chẩn đoán với `default_rng(42)`:

```text
sample size: 1000
mean: khoảng -0.0288915510
sample standard deviation: khoảng 0.9892170877
approximate 95% bound: khoảng ±0.0619806421
lag 1 ACF: khoảng 0.0870548722
```

Giá trị chính thức phải lấy từ execution output, không chép cứng làm bằng chứng.

Validation bắt buộc:

```text
JSON notebook hợp lệ
compileall src đạt
test E1 tiếp tục đạt
test white noise mới đạt
cell 0–27 chạy sạch, không có error output
raw data checksum không đổi
validated E1 ACF checksum không đổi
source/type cell E1 không đổi
source/type cell E3–5 không đổi
không thêm dependency
```

## 8. Rủi ro và kiểm soát

### Chuỗi ngẫu nhiên thay đổi

Chuyển từ legacy RNG sang `default_rng` làm thay đổi mẫu. Đây là thay đổi bắt
buộc theo contract; mọi output và diễn giải E2 phải được tạo lại trong cùng một
execution.

### Regression E1

Không sửa chữ ký hoặc thân hàm trực quan hóa E1; chạy lại toàn bộ test E1 và
đối chiếu checksum output đã kiểm chứng.

### Làm thay đổi E3–5

Không thêm cell. Tái sử dụng đúng sáu cell 22–27 và xác minh source/type từ cell
28 trở đi không đổi.

### Diễn giải quá mức một spike

Báo đúng số lượng và vị trí spike; kết luận dựa trên toàn bộ ACF pattern, không
dùng một spike riêng lẻ để phủ nhận white noise.

## 9. Điều kiện dừng

Phải dừng và báo cáo nếu:

```text
generator đúng contract không tái tạo được
white noise không có đúng 1000 quan sát
mean hoặc standard deviation lệch baseline ngoài tolerance
validated E1 ACF cần bị ghi đè
cell E3–5 buộc phải sửa
cần dependency mới
test E1 bị regression
notebook không chạy sạch đến hết E2
```

## 10. Tiêu chí hoàn thành

```text
phần tốt của E2 được giữ theo bản đồ cell
generator đúng default_rng(42)
thống kê mô tả được hiển thị
ACF có lag 0–40 và confidence interval 95%
AirPassengers ACF được tái sử dụng từ E1
ba hình và CSV bắt buộc tồn tại, đã kiểm tra
diễn giải trả lời đủ câu hỏi bằng actual output
test E1 và E2 đều đạt
raw data, E1, E3–5 không đổi
execution log và current status được cập nhật
```

## 11. Phê duyệt của người dùng

```text
Người dùng đã xem xét kế hoạch: CÓ
Cho phép triển khai: CÓ
Ngày phê duyệt: 2026-10-12
```

Người dùng đã phê duyệt rõ ràng kế hoạch ngày 2026-10-12. Được phép triển khai
trong đúng phạm vi đã chốt.

## 12. Kết quả triển khai

```text
Triển khai hoàn tất: CÓ
Validation hoàn tất: CÓ
Ngày hoàn tất: 2026-10-12
Notebook chính: notebooks/practice_1_present.ipynb
Nhật ký: docs/logs/exercise_02_execution.md
```

Toàn bộ tiêu chí hoàn thành tại Mục 10 đã đạt. E1 và E3–E5 không bị thay đổi
ngoài execution output E1 được tạo lại với kết quả tương đương.
