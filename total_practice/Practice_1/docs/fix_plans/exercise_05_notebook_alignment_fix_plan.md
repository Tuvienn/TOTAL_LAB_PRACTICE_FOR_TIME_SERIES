# EXERCISE 05 — KẾ HOẠCH ĐỒNG BỘ NOTEBOOK

## 1. Trạng thái

```text
Practice: Practice_1
Exercise: 05 — Time Series Visualization
Phạm vi cell: 45–51
Trạng thái kế hoạch: ĐÃ_TRIỂN_KHAI_VÀ_XÁC_MINH
Được phép triển khai: CÓ
Ngày tạo: 2026-10-12
Ngày phê duyệt: 2026-10-12
```

Tài liệu này là fix plan cho các vấn đề đã ghi tại
`docs/error_analysis/exercise_05_notebook_alignment_issue.md`. Chỉ khi Human duyệt
rõ ràng thì agent mới được sửa code, notebook, tạo output và chạy E5.

## 2. Mục tiêu

- dùng validated AirPassengers series với DatetimeIndex chuẩn;
- tạo full-series visualization riêng cho E5;
- tính rolling mean và rolling standard deviation theo explicit protocol;
- bảo đảm trailing rolling không sử dụng future observations;
- tạo monthly seasonal plot phân biệt đủ 12 năm;
- tạo month-year heatmap sau khi validate duplicate và shape;
- đối chiếu visual evidence với E1, E3 và 14 candidates của E4;
- trả lời đủ 12 interpretation questions từ actual outputs;
- tạo output có thể tái tạo và kiểm thử;
- giữ nguyên E1–E4, raw dataset và dependency contract.

## 3. Phạm vi được phép thay đổi sau approval

```text
notebooks/practice_1_present.ipynb, chỉ cell 45–51
src/practice_1/analysis/rolling_statistics.py
src/practice_1/analysis/__init__.py
src/practice_1/visualization/diagnostic_plots.py
src/practice_1/visualization/__init__.py
tests/test_rolling_statistics.py
outputs/figures/13_full_time_series.png
outputs/figures/14_rolling_mean_std.png
outputs/figures/15_monthly_seasonal_plot.png
outputs/figures/16_month_year_heatmap.png
outputs/results/rolling_statistics.csv
docs/logs/exercise_05_execution.md
docs/status/current_status.md
E5 specification/plan/error/fix status fields
```

## 4. File và phạm vi không được sửa

```text
notebook cell 0–44
datasets/raw/air_passengers.csv
validated E1–E4 scientific logic
validated E1–E4 result tables
working_rule.md
.agents rules
docs/rules/
approved Practice overview và initialization plan
pyproject.toml hoặc dependency versions
Practice/Lab khác
```

Notebook cũ không thuộc phạm vi. Chỉ
`notebooks/practice_1_present.ipynb` được xem là notebook chính.

## 5. Reusable analysis API dự kiến

Tạo `src/practice_1/analysis/rolling_statistics.py` với các trách nhiệm tập trung:

```text
compute_rolling_statistics
prepare_monthly_seasonal_data
build_month_year_matrix
summarize_monthly_pattern
```

### `compute_rolling_statistics`

Input:

```text
validated monthly pd.Series với DatetimeIndex
window = 12
min_periods = 12
center = False
std_ddof = 1
```

Output:

```text
DataFrame cùng index
observed_value
rolling_mean_12
rolling_std_12
```

Validation tối thiểu:

```text
index là DatetimeIndex
index tăng dần và không duplicate
series không rỗng và không missing
frequency phù hợp monthly start
window và min_periods hợp lệ
center phải là False theo E5 protocol
```

### `prepare_monthly_seasonal_data`

Tạo long-form table với timestamp, year, month và observed value mà không mutate
canonical input.

### `build_month_year_matrix`

Trước khi pivot phải xác minh đúng một observation trên mỗi cặp month-year. Không
dùng `pivot_table` hoặc aggregation fallback. Output phải có shape `12 × 12`, month
order 1–12 và year order 1949–1960.

### `summarize_monthly_pattern`

Tạo monthly summary từ actual data để xác định month mean cao nhất/thấp nhất và hỗ
trợ interpretation động. Không hard-code July hoặc November trong notebook narrative.

## 6. Visualization API dự kiến

Tái sử dụng:

```text
plot_time_series
```

để tạo `13_full_time_series.png` với output path riêng.

Bổ sung vào visualization owner hiện tại:

```text
plot_rolling_statistics
plot_monthly_seasonal_pattern
plot_month_year_heatmap
```

Yêu cầu:

- chỉ dùng Matplotlib và dependency hiện có;
- trục thời gian của rolling plot phải là DatetimeIndex;
- labels phải ghi đúng đơn vị `Passengers (thousands)`;
- seasonal plot phải phân biệt được 12 năm;
- heatmap phải dùng matrix đã validate, không tự aggregate;
- figure được lưu bằng cơ chế `_save_figure` hiện có;
- không thêm comment kể lại code và không thêm dependency.

## 7. Bản đồ cell dự kiến

| Cell | Nội dung |
|---:|---|
| 45 | Heading E5, mục tiêu và protocol đã khóa |
| 46 | Imports E5, validate canonical input, tạo và hiển thị figure 13 |
| 47 | Giải thích trailing rolling, boundary NaN và no-future-information rule |
| 48 | Tính rolling statistics, verify 11 NaN, lưu CSV, tạo figure 14 |
| 49 | Tạo monthly seasonal data, summary và figure 15 |
| 50 | Validate E3/E4 evidence, tạo matrix 12 × 12, figure 16 và cross-check candidates |
| 51 | Diễn giải động trả lời đủ 12 câu hỏi và kết luận E5 |

Không thêm cell ngoài phạm vi nếu bảy cell hiện có đủ khả năng trình bày rõ ràng.
Nếu cần thay đổi số cell, phải giữ source/type của cell 0–44 không đổi và ghi lại lý do.

## 8. Output dự kiến

### Figures bắt buộc

```text
outputs/figures/13_full_time_series.png
outputs/figures/14_rolling_mean_std.png
outputs/figures/15_monthly_seasonal_plot.png
outputs/figures/16_month_year_heatmap.png
```

### Machine-readable result

```text
outputs/results/rolling_statistics.csv
```

CSV dự kiến có 144 dòng và các cột:

```text
timestamp
observed_value
rolling_mean_12
rolling_std_12
```

Hai cột rolling phải có đúng 11 giá trị thiếu đầu kỳ do chưa đủ window. Đây là
expected boundary behavior, không phải data-quality error và không được fill.

## 9. Tests dự kiến

Tạo `tests/test_rolling_statistics.py` để kiểm tra:

```text
input index và output index được bảo toàn
output schema đúng
rolling mean/std có đúng 11 initial NaN
first valid timestamp là 1949-12-01
rolling mean dùng đúng 12 observations quá khứ và hiện tại
rolling std dùng ddof=1
center=True bị từ chối
input missing hoặc duplicate bị từ chối
seasonal long table có 144 observations
month order là 1–12 và year order là 1949–1960
duplicate month-year bị từ chối, không aggregate
heatmap shape là 12 × 12
known cells Jan-1949 = 112 và Dec-1960 = 432
monthly summary xác định July cao nhất và November thấp nhất
```

## 10. Diễn giải bắt buộc

Notebook phải trả lời bằng actual variables:

1. Xu hướng chung của AirPassengers là gì?
2. Rolling mean thay đổi như thế nào theo thời gian?
3. Rolling standard deviation có ổn định không?
4. Variance có xu hướng tăng theo level không?
5. Tháng nào thường có lượng hành khách cao?
6. Tháng nào thường thấp?
7. Seasonal pattern có lặp lại giữa các năm không?
8. Seasonal amplitude có thay đổi theo thời gian không?
9. Heatmap cho thấy pattern nổi bật nào?
10. Có observation nào trông bất thường không?
11. Các observation đó có trùng với outlier candidates E4 không?
12. Visualization có hỗ trợ kết luận từ ACF/PACF và decomposition không?

Kết luận phải nói rõ E4 candidates là residual-based flags, không phải confirmed
anomalies. E5 không xóa, clip, replace hoặc điều chỉnh observation.

## 11. Trình tự triển khai sau approval

```text
1. Ghi nhận authorization và baseline checksum.
2. Tạo rolling_statistics.py và public exports.
3. Viết tests cho analysis logic.
4. Chạy targeted tests; dừng nếu fail chưa giải thích được.
5. Bổ sung plotting functions và public exports.
6. Cập nhật duy nhất cell 45–51 của notebook.
7. Chạy compile/import checks và toàn bộ test suite.
8. Execute notebook từ cell 0 đến hết cell 51 bằng kernel đã khóa.
9. Inspect trực quan cả bốn figure.
10. Validate CSV, notebook outputs, checksum raw và protected scope E1–E4.
11. Ghi execution log và cập nhật current status.
12. Thực hiện technical closure review cho E1–E5.
```

## 12. Validation plan

```text
compileall đạt
toàn bộ tests E1–E5 đạt
notebook cell 0–51 chạy sạch theo intended order
execution count của code cells liên tục
không có error output
bốn figure tồn tại, đọc được và đã visual inspection
rolling_statistics.csv đúng schema, 144 dòng và boundary NaN
rolling dùng window=12, min_periods=12, center=False, ddof=1
heatmap không aggregate duplicate và có shape 12 × 12
12 interpretation questions được trả lời từ actual outputs
raw checksum không đổi
E1–E4 source/type checksum không đổi
E1–E4 validated result content không đổi
không thêm dependency
```

Baseline được bảo vệ:

```text
E1–E4 source/type: 8fd09505e835aac7ef494d57686790b64f23cec6d06e147f39ba0a36620ec88a
Raw data: bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8
E3 decomposition components: 133d60b97887e997f7f17616589d5a4441af4664d14e8e86dbcdd71b9eeb90d0
E4 outlier candidates: 6f08fd16b5dd2c240801a83dc78b675302ad6e916dddb0ef8634c3611df77c39
```

## 13. Rủi ro và biện pháp kiểm soát

### Rủi ro: sửa nhầm E1–E4

Kiểm soát bằng cell boundary 45–51 và source/type checksum cell 0–44.

### Rủi ro: rolling dùng future information

Kiểm soát bằng `center=False`, trailing window và exact-value tests.

### Rủi ro: heatmap che duplicate

Kiểm soát bằng duplicate validation trước `pivot`; không dùng aggregation.

### Rủi ro: kết luận anomaly quá mức

Kiểm soát bằng cách đối chiếu E4 residual candidates và dùng ngôn ngữ
`potential candidate`, không `confirmed anomaly`.

### Rủi ro: output đẹp nhưng không tái tạo được

Kiểm soát bằng reusable source, tests, saved artifacts, clean notebook execution và
machine-readable rolling CSV.

## 14. Alternatives

### Thêm seaborn vào dependency

Không chọn vì E5 có thể tạo đầy đủ seasonal plot và heatmap bằng Matplotlib hiện có;
thêm dependency không tạo giá trị khoa học tương xứng và cần approval riêng.

### Giữ toàn bộ logic trong notebook

Không chọn vì rolling và matrix validation là reusable, ảnh hưởng correctness và cần
automated tests theo architecture rule.

### Tái sử dụng trực tiếp figure 01 làm output E5

Không chọn việc đổi tên hoặc ghi đè figure E1. E5 sẽ gọi lại reusable function để tạo
`13_full_time_series.png`, giữ ownership và audit trail tách biệt.

## 15. Điều kiện dừng

Dừng implementation nếu:

```text
plan chưa được Human duyệt
validated AirPassengers input sai schema/index/frequency
cần sửa cell 0–44 hoặc upstream scientific logic
cần thêm dependency
rolling protocol cần thay đổi
centered rolling được yêu cầu
heatmap có duplicate month-year
E3/E4 evidence sai schema hoặc không align timestamp
notebook hoặc tests fail ngoài expected scope
raw data hoặc validated upstream result thay đổi
```

## 16. Phê duyệt

```text
EXERCISE_05_ERROR_ANALYSIS_CREATED=true
EXERCISE_05_FIX_PLAN_CREATED=true
EXERCISE_05_FIX_PLAN_REVIEWED=true
EXERCISE_05_FIX_PLAN_APPROVED=true
EXERCISE_05_IMPLEMENTATION_AUTHORIZED=true
```

Human đã phê duyệt plan và yêu cầu bắt đầu triển khai ngày 2026-10-12.

## 17. Kết quả triển khai

```text
Triển khai hoàn tất: CÓ
Validation hoàn tất: CÓ
Ngày hoàn tất: 2026-10-12
Tests: 27 passed
Notebook execution counts: 1–33
Notebook error outputs: 0
Execution log: docs/logs/exercise_05_execution.md
```
