# E5 PLAN — BACKTESTING (EXPANDING & ROLLING WINDOW)

## 1. Mục tiêu
Đánh giá độ ổn định và khả năng khái quát hóa của mô hình qua nhiều mốc thời gian trong lịch sử thay vì chỉ dựa vào một lần chia train/test duy nhất.

## 2. Thiết lập thực nghiệm
- **Bắt buộc**: Expanding Window Backtesting (kích thước tập train tăng dần qua từng fold).
- **Mở rộng**: Rolling Window Backtesting (kích thước tập train cố định, loại bỏ dữ liệu cũ nhất).
- **Nguyên tắc chống rò rỉ**: Trong mỗi fold backtest, toàn bộ quy trình tiền xử lý (imputation, scaling) và huấn luyện mô hình phải được thực hiện cách ly độc lập, chỉ dùng dữ liệu trước forecast origin của fold đó.
- Cấu hình đề xuất:
  - Forecast horizon: $H = 12$ bước (hoặc theo tần suất dữ liệu).
  - Step size: Dịch chuyển origin mỗi 6 hoặc 12 bước.
  - Số lượng fold: Tối thiểu 3–5 folds.

## 3. Output mong đợi
- Cấu hình chi tiết của từng fold backtest (`backtesting_config.json`).
- `backtesting_folds_summary.csv`: Thống kê train start, train end, test start, test end và metric của từng fold.
- Bảng tổng hợp Mean và Standard Deviation của performance qua các fold.
- `05_backtesting_folds.png`: Sơ đồ các fold backtest qua dòng thời gian.
- `06_performance_across_folds.png`: Biểu đồ biểu thị sự biến thiên của sai số qua từng fold.
- Nhận xét chi tiết về độ ổn định của mô hình qua các giai đoạn khác nhau của lịch sử.
