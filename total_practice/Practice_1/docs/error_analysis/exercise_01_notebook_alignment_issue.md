# EXERCISE 01 — PHÂN TÍCH LỖI ĐỒNG BỘ NOTEBOOK

## 1. Thông tin vấn đề

```text
Practice: Practice_1
Exercise: 01 — Phân tích ACF/PACF
Vấn đề: Notebook chính chưa đồng bộ với phần triển khai Exercise 1 đã được kiểm chứng
Trạng thái phân tích: ĐÃ_PHÂN_TÍCH
Trạng thái triển khai sửa lỗi: ĐÃ_HOÀN_THÀNH_VÀ_XÁC_MINH
```

Người dùng đã chọn `notebooks/practice_1_present.ipynb` làm notebook duy nhất trong phạm
vi xử lý và là notebook thực thi chính thức của Practice 1.

## 2. Hiện trạng quan sát được

Phần Exercise 1 trong `practice_1_present.ipynb` tạo ra các giá trị ACF/PACF cốt lõi
đúng, nhưng notebook đang tự triển khai lại việc đọc dữ liệu, chuyển đổi timestamp,
tính tương quan, vẽ biểu đồ và diễn giải thay vì sử dụng package `practice_1` đã được
kiểm chứng.

Các hành vi hiện tại trong notebook:

```text
đọc dataset trực tiếp bằng pandas.read_csv
đường dẫn tương đối phụ thuộc thư mục làm việc của notebook
bỏ cột định danh dòng mà không chạy quy trình kiểm tra schema đã xác nhận
tự chuyển fractional year thành timestamp ngay trong notebook
kiểm tra dòng trùng lặp thay vì kiểm tra timestamp trùng lặp
không trình bày rõ missing value, frequency, chronology và khoảng thời gian chính xác
trình bày giá trị như số hành khách thay vì đơn vị nghìn hành khách
biểu đồ ACF/PACF trong notebook không có khoảng tin cậy 95%
mô tả ACF tại lag 12 không nhất quán giữa giá trị xấp xỉ 0.74 và 0.75
phần phân tích và kết luận lặp lại nội dung
kết luận đề cập chuẩn bị cho SARIMA vượt ra ngoài mục tiêu Exercise 1
```

Metadata của notebook đang khai báo kernel Python 3.11 thuộc project
`credit-default-prediction`, trong khi runtime đã xác nhận của Practice 1 là Python 3.12
với kernel `time-series-practice-1`.

## 3. Hành vi mong đợi

Notebook chính phải:

```text
đọc AirPassengers qua practice_1.data.load_air_passengers
sử dụng DatetimeIndex theo tháng và trường passengers_thousands đã được kiểm chứng
hiển thị schema, shape, khoảng thời gian, frequency, missing value, duplicate timestamp và chronology
sử dụng các hàm ACF/PACF trong practice_1.analysis với max_lag=40 và alpha=0.05
hiển thị biểu đồ ACF/PACF có khoảng tin cậy 95%
trình bày đúng đơn vị nghìn hành khách
báo cáo nhất quán các giá trị thực tế tại lag 1, 12, 24 và 36
trả lời trực tiếp bốn câu hỏi diễn giải của Exercise 1
không lựa chọn hoặc đề xuất ARIMA/SARIMA order từ chuỗi raw
chạy theo runtime contract Python 3.12 đã xác nhận
tái tạo outputs Exercise 1 mà không thay đổi raw data
```

## 4. Bằng chứng và cách tái hiện

Bằng chứng được thu thập bằng cách đọc các cell 0–21 trong
`notebooks/practice_1_present.ipynb` và đối chiếu với:

```text
config/practice_1.json
docs/exercise_details/exercise_01_acf_pacf.md
docs/rules/architecture_rule.md
docs/rules/rule_code.md
src/practice_1/data/air_passengers.py
src/practice_1/analysis/acf_pacf.py
src/practice_1/visualization/diagnostic_plots.py
tests/test_air_passengers.py
tests/test_acf_pacf.py
outputs/results/acf_values.csv
outputs/results/pacf_values.csv
outputs/results/exercise_01_findings.json
```

Phần source dùng lại đã kiểm tra đầy đủ data contract và tạo đúng các giá trị của
Exercise 1. Các automated tests hiện có cho phần triển khai này đều đạt. Vì vậy, vấn
đề nằm ở lớp tích hợp và trình bày trong notebook, không nằm ở thuật toán source đã
được kiểm chứng.

Các giá trị cốt lõi đã xác minh:

```text
ACF lag 1: 0.9480473407524913
ACF lag 12: 0.7603950422625557
ACF lag 24: 0.5321898304658020
ACF lag 36: 0.33702359902053575
PACF lag 13: -0.5396912419071259
```

## 5. Nguyên nhân gốc

Notebook ban đầu được phát triển như một workflow khám phá độc lập. Sau đó, các hàm
dùng lại và outputs đã được kiểm chứng của Exercise 1 được bổ sung vào repository,
nhưng các cell trong notebook chưa được đồng bộ với những owner này.

Do đó hiện đang tồn tại hai luồng xử lý song song:

```text
phần triển khai đã kiểm chứng và do source trong src/practice_1 sở hữu
phần triển khai độc lập nằm trong practice_1_present.ipynb
```

Luồng do notebook tự sở hữu có mức bảo đảm thấp hơn về validation và presentation.
Điều này tạo ra nguy cơ lệch logic dù các kết quả số cốt lõi hiện vẫn khớp với outputs
đã được kiểm chứng.

## 6. File và outputs bị ảnh hưởng

File bị ảnh hưởng trực tiếp:

```text
notebooks/practice_1_present.ipynb
```

Các outputs cần được tạo lại và đối chiếu trong quá trình sửa:

```text
outputs/figures/01_time_series_overview.png
outputs/figures/02_acf_40_lags.png
outputs/figures/03_pacf_40_lags.png
outputs/results/acf_values.csv
outputs/results/pacf_values.csv
outputs/results/exercise_01_findings.json
```

Các file được bảo vệ:

```text
datasets/raw/air_passengers.csv
các rule, specification và before-process plan đã được xác nhận
```

## 7. Ảnh hưởng đến các bước sau

Exercise 2 cần sử dụng ACF của AirPassengers đã được kiểm chứng để so sánh với white
noise. Nếu Exercise 2 tiếp tục dùng các biến do notebook tự tính, project sẽ duy trì
logic trùng lặp và kết quả không còn truy vết trực tiếp về phần triển khai Exercise 1
đã được kiểm chứng.

Đơn vị sai và việc thiếu khoảng tin cậy cũng có thể khiến người đọc hiểu sai scale và
ý nghĩa thống kê. Việc phụ thuộc vào thư mục làm việc làm giảm khả năng restart kernel
và chạy lại notebook theo cách tái lập được.

## 8. Yêu cầu sửa lỗi

Quá trình sửa phải:

```text
chỉ thay đổi notebook chính practice_1_present.ipynb và các generated outputs đã xác nhận
tái sử dụng các hàm source đã được kiểm chứng thay vì tạo thêm implementation khác
giữ nguyên các kết quả số Exercise 1 đã được xác minh
hiển thị đầy đủ bằng chứng data integrity và khoảng tin cậy
sửa đơn vị, label, heading và các giá trị làm tròn chưa nhất quán
loại bỏ diễn giải trùng lặp hoặc vượt phạm vi
giữ raw dataset nguyên vẹn theo từng byte
hoàn tất validation Exercise 1 trước khi bắt đầu triển khai Exercise 2
```

Trình tự sửa và validation được quy định trong
`docs/fix_plans/exercise_01_notebook_alignment_fix_plan.md`.

## 9. Kết quả xử lý

Vấn đề đã được xử lý và xác minh ngày 2026-10-12:

```text
notebook chính sử dụng load_air_passengers
ACF/PACF được tính bằng các hàm dùng chung trong practice_1.analysis
ba biểu đồ được tạo bằng các hàm trong practice_1.visualization
bảng kiểm tra hợp đồng dữ liệu được hiển thị trong notebook
đơn vị được thống nhất là nghìn hành khách
biểu đồ ACF/PACF có khoảng tin cậy 95%
metadata dùng Python 3.12.15 và kernel time-series-practice-1
12 code cell E1 chạy sạch, không có error output
hai test E1 đều đạt
checksum raw data không thay đổi
source của các cell Exercise 2–5 không thay đổi
```

Bằng chứng thực thi được ghi tại
`docs/logs/exercise_01_notebook_alignment_execution.md`.
