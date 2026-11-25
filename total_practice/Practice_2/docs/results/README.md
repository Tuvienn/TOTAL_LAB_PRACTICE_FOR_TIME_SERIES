# Dashboard kết quả — Practice 2

Đây là trang tổng quan để xem nhanh kết quả từng Exercise. Mỗi liên kết mở một
trang Markdown riêng, trong đó có kết luận, điểm cần chú ý và liên kết tới
evidence gốc.

| Exercise | Chủ đề | Trạng thái | Kết quả |
|---|---|---|---|
| [E01](./exercise_01.md) | Khám phá và chuẩn bị dữ liệu | Đã kiểm tra | [Mở kết quả](./exercise_01.md) |
| [E02](./exercise_02.md) | Kiểm định ADF | Đã kiểm tra | [Mở kết quả](./exercise_02.md) |
| [E03](./exercise_03.md) | Sai phân và tính dừng | Đã kiểm tra | [Mở kết quả](./exercise_03.md) |
| [E04](./exercise_04.md) | ACF/PACF và candidates | Đã phê duyệt | [Mở kết quả](./exercise_04.md) |
| [E05](./exercise_05.md) | ARIMA, diagnostics và forecast | Đã phê duyệt, có limitation | [Mở kết quả](./exercise_05.md) |
| [E06](./exercise_06.md) | SARIMA AirPassengers | Đã duyệt triển khai | [Mở kết quả](./exercise_06.md) |

## Quy ước thư mục

- `docs/results/`: tóm tắt kết quả dễ đọc và các liên kết điều hướng.
- `docs/logs/`: execution evidence đã diễn giải theo từng Exercise.
- `outputs/results/`: kết quả máy đọc được như TXT, CSV hoặc JSON.
- `outputs/figures/`: hình được sinh từ execution.
- `runs/`: raw runtime log của từng lần chạy.

## Cảnh báo chung

E04 và E05 đã được phê duyệt từ clean-kernel run. E05 vẫn ghi rõ limitation về
residual autocorrelation. E06 đã được duyệt để triển khai nhưng chưa completed;
nó không thay thế trạng thái của core practice.
