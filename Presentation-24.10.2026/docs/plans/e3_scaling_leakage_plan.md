# E3 PLAN — SCALING DATA LEAKAGE

## 1. Trạng thái thực hiện
- **Trạng thái**: `[COMPLETED]`
- **Thời điểm hoàn thành**: 2026-10-25
- **Công cụ chuẩn hóa**: `StandardScaler` (Z-score normalization).

## 2. Mục tiêu
Thực hiện thực nghiệm kiểm chứng hiện tượng Data Leakage khi chuẩn hóa dữ liệu (Scaling Leakage), làm rõ sự nguy hại khi dùng thông tin tương lai trong tiền xử lý.

## 3. Thiết lập 2 Pipeline tiền xử lý
- **Pipeline A — Leakage (Sai phạm)**:
  - Fit scaler trên TOÀN BỘ dataset trước khi chia train/test.
  - Transform toàn bộ dataset sau đó mới cắt ra train và test.
- **Pipeline B — Correct (Chuẩn mực)**:
  - Chia dữ liệu theo thời gian (Temporal Split) trước.
  - Scaler chỉ được fit trên dữ liệu Train.
  - Dùng scaler đã fit trên train để transform cho cả Train và Test.
- Giữ nguyên toàn bộ cấu hình: Dataset, thuật toán mô hình hóa, đặc trưng đầu vào, khoảng thời gian train/test và các metric đo lường.

## 4. Kết quả thực nghiệm đối chứng
### 4.1. Sự sai lệch tham số Scaler (`scaler_parameters_comparison.csv`)
| Pipeline | Mean ($\mu$) | Std ($\sigma$) | Bản chất hiện tượng |
|---|:---:|:---:|---|
| **Pipeline A** (Leakage - Fit toàn bộ) | 291.89 | 115.42 | Bị kéo lệch mạnh do "nhìn trộm" các giá trị cao ở tương lai |
| **Pipeline B** (Correct - Fit chỉ trên Train) | 254.26 | 90.44 | Độc lập 100%, bảo toàn đúng thực tế lịch sử mà mô hình có quyền biết |

### 4.2. Độ bóp méo sai số (`scaling_leakage_metrics.csv`)
| Pipeline | MAE | RMSE | MAPE (%) | Đánh giá |
|---|:---:|:---:|:---:|---|
| **Pipeline A** (Leakage) | 15.22 | 19.07 | 3.65% | Phân phối bị biến dạng, sai số bị sai lệch |
| **Pipeline B** (Correct) | 14.78 | 18.59 | 3.56% | Phản ánh đúng hiệu năng cách ly |

## 5. Output bàn giao thực tế
- [x] `scaler_parameters_comparison.csv`: Bảng đối chiếu $\mu, \sigma$ học được của scaler giữa 2 pipeline.
- [x] `scaling_leakage_metrics.csv`: Bảng số liệu MAE, RMSE, MAPE đối chiếu giữa Pipeline A và Pipeline B.
- [x] `03_scaling_leakage_comparison.png` (Visual 3): Biểu đồ phân phối Histogram đối chiếu giữa cách ly chuẩn và rò rỉ toàn chuỗi.
- [x] **Kết luận E3**: Việc fit scaler trên toàn chuỗi vi phạm nguyên tắc nhân quả, làm thay đổi phân phối đặc trưng. Bắt buộc fit scaler CHỈ trên tập Train.

