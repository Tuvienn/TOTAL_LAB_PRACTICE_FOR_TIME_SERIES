# E3 PLAN — SCALING DATA LEAKAGE

## 1. Mục tiêu
Thực hiện thực nghiệm kiểm chứng hiện tượng Data Leakage khi chuẩn hóa dữ liệu (Scaling Leakage), làm rõ sự nguy hại khi dùng thông tin tương lai trong tiền xử lý.

## 2. Thiết lập 2 Pipeline tiền xử lý
- **Pipeline A — Leakage (Sai phạm)**:
  - Fit scaler (ví dụ: `StandardScaler` hoặc `MinMaxScaler`) trên TOÀN BỘ dataset trước khi chia train/test.
  - Transform toàn bộ dataset sau đó mới cắt ra train và test.
- **Pipeline B — Correct (Chuẩn)**:
  - Chia dữ liệu theo thời gian (Temporal Split) trước.
  - Scaler chỉ được fit trên dữ liệu Train.
  - Dùng scaler đã fit trên train để transform cho cả Train và Test.
- Giữ nguyên toàn bộ cấu hình: Dataset, thuật toán mô hình hóa, đặc trưng đầu vào, khoảng thời gian train/test và các metric đo lường.

## 3. Output mong đợi
- Bảng so sánh tham số học được của scaler (mean, std, min, max) giữa Pipeline A và Pipeline B.
- `03_scaling_leakage_comparison.png`: Biểu đồ so sánh phân phối hoặc sai số giữa 2 pipeline.
- `scaling_leakage_metrics.csv`: Bảng số liệu MAE, RMSE, MAPE của Pipeline A vs Pipeline B.
- Kết luận khoa học chứng minh mức độ ảnh hưởng của scaling leakage đến kết quả đánh giá.
