# Dashboard kết quả — Practice 2

Đây là trang tổng quan để xem nhanh kết quả từng Exercise. Mỗi liên kết mở một
trang Markdown riêng, trong đó có kết luận, điểm cần chú ý và liên kết tới
evidence gốc.

| Exercise | Chủ đề | Trạng thái | Kết quả |
|---|---|---|---|
| <a href="./exercise_01.md" style="color:#1f6feb;">E01</a> | Khám phá và chuẩn bị dữ liệu | Đã kiểm tra | <a href="./exercise_01.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="./exercise_02.md" style="color:#1f6feb;">E02</a> | Kiểm định ADF | Đã kiểm tra | <a href="./exercise_02.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="./exercise_03.md" style="color:#1f6feb;">E03</a> | Sai phân và tính dừng | Đã kiểm tra | <a href="./exercise_03.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="./exercise_04.md" style="color:#1f6feb;">E04</a> | ACF/PACF và candidates | Đã xác nhận | <a href="./exercise_04.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="./exercise_05.md" style="color:#1f6feb;">E05</a> | ARIMA, diagnostics và forecast | Đã xác nhận, có limitation | <a href="./exercise_05.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="./exercise_06.md" style="color:#1f6feb;">E06</a> | SARIMA AirPassengers | Đã xác nhận phạm vi triển khai | <a href="./exercise_06.md" style="color:#1f6feb;">Mở kết quả</a> |

## Quy ước thư mục

- `docs/results/`: tóm tắt kết quả dễ đọc và các liên kết điều hướng.
- `docs/logs/`: execution evidence đã diễn giải theo từng Exercise.
- `outputs/results/`: kết quả máy đọc được như TXT, CSV hoặc JSON.
- `outputs/figures/`: hình được sinh từ execution.
- `runs/`: raw runtime log của từng lần chạy.

## Cảnh báo chung

E04 và E05 đã được xác nhận từ clean-kernel run. E05 vẫn ghi rõ limitation về
residual autocorrelation. E06 đã được xác nhận để triển khai nhưng chưa completed;
nó không thay thế trạng thái của core practice.
