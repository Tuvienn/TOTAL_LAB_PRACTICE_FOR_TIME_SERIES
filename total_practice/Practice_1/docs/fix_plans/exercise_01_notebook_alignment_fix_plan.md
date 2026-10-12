# EXERCISE 01 — KẾ HOẠCH SỬA LỖI ĐỒNG BỘ NOTEBOOK

## 1. Thông tin kế hoạch

```text
Practice: Practice_1
Exercise: 01 — Phân tích ACF/PACF
Mục sửa: Đồng bộ notebook chính với các owner Exercise 1 đã được kiểm chứng
Trạng thái kế hoạch: ĐÃ_TRIỂN_KHAI_VÀ_XÁC_MINH
Được phép triển khai: CÓ
```

Tài liệu phân tích lỗi tương ứng:

```text
docs/error_analysis/exercise_01_notebook_alignment_issue.md
```

## 2. Mục tiêu sửa lỗi

Đồng bộ phần Exercise 1 trong `notebooks/practice_1_present.ipynb` với phần triển khai
do source sở hữu và đã được kiểm chứng, bảo đảm notebook chính có thể tái lập, chính
xác về mặt khoa học và đủ tin cậy để làm bằng chứng đầu vào cho Exercise 2.

Việc sửa không được thay đổi phương pháp phân tích hoặc các kết luận Exercise 1 đã được
xác minh.

## 3. Phạm vi notebook đã chốt

Người dùng đã chọn phạm vi notebook sau:

```text
Notebook chính và duy nhất trong scope: notebooks/practice_1_present.ipynb
```

Mọi hoạt động kiểm tra, sửa, thực thi và validation notebook trong kế hoạch này chỉ áp
dụng cho `notebooks/practice_1_present.ipynb`.

## 4. Phạm vi thay đổi đề xuất

Các file được phép sửa sau khi người dùng phê duyệt:

```text
notebooks/practice_1_present.ipynb
outputs/figures/01_time_series_overview.png
outputs/figures/02_acf_40_lags.png
outputs/figures/03_pacf_40_lags.png
outputs/results/acf_values.csv
outputs/results/pacf_values.csv
outputs/results/exercise_01_findings.json
docs/logs/exercise_01_notebook_alignment_execution.md
docs/status/current_status.md
```

Các file cần đọc nhưng không được sửa:

```text
config/practice_1.json
src/practice_1/data/air_passengers.py
src/practice_1/analysis/acf_pacf.py
src/practice_1/visualization/diagnostic_plots.py
tests/test_air_passengers.py
tests/test_acf_pacf.py
docs/exercise_details/exercise_01_acf_pacf.md
docs/plans/exercise_01_before_process.md
```

Các file và nội dung nằm ngoài phạm vi sửa:

```text
datasets/raw/air_passengers.csv
các rule đã được duyệt
các exercise specification đã được duyệt
các before-process plan đã được duyệt
các cell triển khai Exercise 2–5
```

## 5. Các bước triển khai theo thứ tự

### Bước 1 — Ghi nhận trạng thái toàn vẹn ban đầu

Ghi checksum trước khi thay đổi cho:

```text
notebooks/practice_1_present.ipynb
datasets/raw/air_passengers.csv
```

Kiểm tra các outputs Exercise 1 hiện tại và lưu lại những giá trị đã được xác minh để
đối chiếu sau khi sửa.

### Bước 2 — Đồng bộ runtime và imports của notebook

Cập nhật metadata của notebook chính theo runtime contract Python 3.12 và kernel
`time-series-practice-1` đã được duyệt.

Thay các phần xử lý dùng lại bằng imports từ public package `practice_1`. Không thêm
`sys.path` mutation hoặc đường dẫn tuyệt đối phụ thuộc máy.

### Bước 3 — Thay thế luồng đọc dữ liệu độc lập

Thay việc đọc CSV trực tiếp và tự chuyển đổi timestamp bằng:

```text
practice_1.data.load_air_passengers
```

Sử dụng `DatetimeIndex` đã được kiểm chứng và trường canonical
`passengers_thousands`.

Notebook phải hiển thị bảng tóm tắt validation gồm:

```text
shape và columns
timestamp đầu và cuối
frequency
số missing value
số duplicate timestamp
trạng thái chronological order
```

### Bước 4 — Đồng bộ cách trình bày chuỗi thời gian

Tạo và hiển thị biểu đồ toàn chuỗi thông qua visualization owner hiện có. Dùng thống
nhất label `Passengers (thousands)` trong biểu đồ và phần diễn giải.

Sửa khoảng thời gian thành tháng 01/1949 đến tháng 12/1960.

### Bước 5 — Thay thế phần tính ACF/PACF độc lập

Sử dụng:

```text
practice_1.analysis.compute_acf_table
practice_1.analysis.compute_pacf_table
```

với các tham số đã duyệt:

```text
max_lag = 40
alpha = 0.05
PACF method = ywm
```

Tạo lại các bảng ACF/PACF và lưu vào đúng đường dẫn output đã duyệt.

### Bước 6 — Hiển thị biểu đồ chẩn đoán đã được kiểm chứng

Tạo và hiển thị biểu đồ ACF/PACF qua các visualization functions hiện có. Cả hai biểu
đồ phải có khoảng tin cậy 95% và đầy đủ lag 0–40.

### Bước 7 — Tổ chức lại phần diễn giải

Thay các phần mô tả trùng lặp bằng một phần phân tích dựa trên bằng chứng, trả lời trực
tiếp các câu hỏi:

```text
Chuỗi có tự tương quan mạnh không?
ACF giảm nhanh hay giảm chậm?
Có pattern mùa vụ lặp lại không?
Bằng chứng tại lag 12, 24 và 36 là gì?
```

Thêm bảng ngắn cho lag 1, 12, 24 và 36. Các giá trị phải được lấy từ result table thực
tế và dùng nhất quán trong toàn bộ notebook.

Ghi rõ ACF/PACF trên raw series chỉ là descriptive evidence và không được dùng để chọn
ARIMA hoặc SARIMA order trong Practice 1.

### Bước 8 — Giữ ranh giới Exercise

Không thay đổi implementation hoặc conclusion của Exercise 2–5 trong lần sửa này.
Nếu việc sửa Exercise 1 khiến các cell sau cần thay đổi để nhận biến mới, phải dừng tại
ranh giới cuối Exercise 1.

Mọi thay đổi downstream cần thiết phải được đề xuất trong kế hoạch của Exercise tương
ứng.

### Bước 9 — Chạy validation

Chạy tests Exercise 1 đã duyệt và thực thi notebook chính từ kernel vừa restart đến hết
Exercise 1.

Đối chiếu results được tạo lại với baseline đã xác minh và kiểm tra trực quan cả ba
figures.

### Bước 10 — Ghi bằng chứng và cập nhật trạng thái

Sau khi validation thành công:

```text
tạo docs/logs/exercise_01_notebook_alignment_execution.md
ghi lại commands, checksums, values, outputs và limitations
cập nhật docs/status/current_status.md để xác nhận practice_1_present.ipynb là notebook chính
giữ Exercise 2 ở trạng thái chưa bắt đầu cho đến khi kế hoạch riêng được phê duyệt
```

## 6. Kế hoạch validation

### Automated validation

```text
chạy pytest cho các tests Exercise 1 hiện có
kiểm tra compile và import của package practice_1
kiểm tra cấu trúc định dạng notebook
chạy notebook chính từ kernel vừa restart đến hết Exercise 1
```

### Data validation

```text
144 observations
thời gian từ 1949-01-01 đến 1960-12-01
monthly start frequency
không có missing value
không có duplicate timestamp
index tăng theo thứ tự thời gian
SHA-256 của raw data không thay đổi
```

### Analytical validation

```text
bảng ACF/PACF chứa đầy đủ lag 0–40
ACF lag 1 xấp xỉ 0.9480473408
ACF lag 12 xấp xỉ 0.7603950423
ACF lag 24 xấp xỉ 0.5321898305
ACF lag 36 xấp xỉ 0.3370235990
PACF sử dụng method ywm
có khoảng tin cậy 95%
```

### Visual validation

```text
01_time_series_overview.png có time axis và đơn vị chính xác
02_acf_40_lags.png rõ ràng và có khoảng tin cậy
03_pacf_40_lags.png rõ ràng và có khoảng tin cậy
không có nội dung bị cắt, chồng lấn hoặc label gây hiểu nhầm
```

### Integrity validation

```text
checksum của datasets/raw/air_passengers.csv không thay đổi
các cell Exercise 2–5 không thay đổi
```

## 7. Ảnh hưởng

Việc sửa cải thiện notebook chính mà không thay đổi public API của source hoặc các kết
luận khoa học đã được kiểm chứng trong Exercise 1.

Exercise 2 sẽ nhận một AirPassengers series và ACF result duy nhất đã được kiểm chứng,
thay vì phụ thuộc vào các phép tính trùng lặp trong notebook.

## 8. Rủi ro và biện pháp kiểm soát

### Thay đổi JSON của notebook

Rủi ro: việc sửa cell có thể làm thay đổi thứ tự, metadata hoặc các cell downstream.

Kiểm soát: so sánh ranh giới cell trước và sau, kiểm tra định dạng notebook và xác nhận
source của các cell Exercise 2–5 không thay đổi.

### Khác biệt trong generated outputs

Rủi ro: PNG được tạo lại có thể khác binary hash do metadata render hoặc phiên bản thư
viện, dù nội dung khoa học tương đương.

Kiểm soát: kiểm tra data values, labels, kích thước và nội dung trực quan thay vì yêu
cầu PNG có hash giống hệt.

### Khả năng tương thích biến downstream

Rủi ro: Exercise 2 hiện đang sử dụng các biến notebook có tên `df` và `series`.

Kiểm soát: không âm thầm sửa Exercise 2. Duy trì một compatibility boundary rõ ràng
nếu có thể; nếu không, phải dừng và chuyển phần chỉnh sửa sang kế hoạch Exercise 2.

### Thực thi toàn bộ notebook

Rủi ro: Exercise 3–5 hiện còn các vấn đề implementation và dependency chưa được xử lý.

Kiểm soát: lần sửa này chỉ validation đến hết Exercise 1. Việc chạy toàn bộ notebook
thuộc final validation của Practice 1.

## 9. Điều kiện phải dừng

Phải dừng và báo cáo trước khi tiếp tục nếu:

```text
raw dataset bị thay đổi
các giá trị Exercise 1 đã xác minh thay đổi ngoài dự kiến
các source functions hiện có không vượt qua tests
không có Python 3.12 environment đã duyệt
notebook chính không import được package practice_1 đã cài
việc sửa Exercise 1 bắt buộc phải thay đổi logic Exercise 2–5
cần thêm dependency mới
```

## 10. Tiêu chí hoàn thành

Việc sửa chỉ được xem là hoàn thành khi:

```text
notebook chính sử dụng các source owner Exercise 1 đã được kiểm chứng
mọi bằng chứng validation bắt buộc được hiển thị trong notebook
đơn vị, heading, numerical values và conclusions chính xác
biểu đồ ACF/PACF hiển thị khoảng tin cậy
tests Exercise 1 đều đạt
notebook chạy được từ kernel vừa restart đến hết Exercise 1
các outputs bắt buộc tồn tại và đã được kiểm tra
raw dataset vẫn nguyên vẹn
execution evidence và current status đã được cập nhật
```

## 11. Phê duyệt của người dùng

```text
Người dùng đã xem xét kế hoạch: CÓ
Cho phép triển khai: CÓ
Ngày phê duyệt: 2026-10-12
```

Kế hoạch đã được người dùng phê duyệt rõ ràng ngày 2026-10-12; được phép bắt đầu triển khai trong phạm vi đã chốt.

## 12. Kết quả triển khai

```text
Triển khai hoàn tất: CÓ
Validation hoàn tất: CÓ
Ngày hoàn tất: 2026-10-12
Notebook chính: notebooks/practice_1_present.ipynb
Nhật ký: docs/logs/exercise_01_notebook_alignment_execution.md
```

Toàn bộ tiêu chí hoàn thành tại Mục 10 đã được kiểm tra. Exercise 2–5 không bị sửa
trong lần triển khai này.
