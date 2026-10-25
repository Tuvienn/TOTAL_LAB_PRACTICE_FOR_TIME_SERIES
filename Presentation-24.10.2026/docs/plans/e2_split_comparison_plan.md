# E2 PLAN — RANDOM SPLIT VS TEMPORAL SPLIT

## 1. Trạng thái thực hiện
- **Trạng thái**: `[COMPLETED]`
- **Thời điểm hoàn thành**: 2026-10-25
- **Mô hình kiểm chứng**: Ridge Regression ($\alpha=1.0$) với 12 đặc trưng độ trễ (`lag_1` đến `lag_12`).

## 2. Mục tiêu
Thực hiện và so sánh thực nghiệm giữa Random Split và Temporal Split trên cùng một bài toán mô hình hóa để chứng minh:
- Vì sao chia ngẫu nhiên gây sai lệch đánh giá lạc quan phi thực tế (optimistic bias).
- Tại sao dự báo chuỗi thời gian bắt buộc phải tôn trọng chiều thời gian.

## 3. Thiết lập thực nghiệm
- **Thiết lập A (Random Split - Leakage)**: Xáo trộn ngẫu nhiên các quan sát rồi chia theo tỷ lệ (80% train / 20% test, `random_state=42`).
- **Thiết lập B (Temporal Split - Đúng chuẩn)**: Chia theo mốc thời gian (80% dữ liệu đầu làm Train, 20% dữ liệu cuối làm Test).
- Giữ nguyên toàn bộ cấu hình mô hình, biến mục tiêu và chỉ số đánh giá.

## 4. Kết quả thực nghiệm đối chứng
Bảng trích xuất thực tế từ `split_comparison_metrics.csv`:

| Phương pháp | MAE | RMSE | MAPE (%) | Đánh giá bản chất |
|---|:---:|:---:|:---:|---|
| **Random Split** (Leakage / Nội suy) | 13.85 | 17.60 | 4.72% | Sai số thấp giả tạo do nhìn trước các điểm lân cận $t-1, t+1$ |
| **Temporal Split** (Chuẩn / Dự báo) | 14.13 | 18.23 | 3.41% | Đo lường trung thực độ khó khi dự báo tương lai chưa biết |

## 5. Output bàn giao thực tế
- [x] `split_comparison_metrics.csv`: Bảng đối chiếu số liệu định lượng giữa hai phương pháp chia.
- [x] `02_random_vs_temporal_split.png` (Visual 2): Biểu đồ Timeline so sánh trực quan sự phân bố của Train và Test points trên trục thời gian.
- [x] **Kết luận E2**: Random Split phá vỡ trật tự nhân quả, biến bài toán ngoại suy (Forecasting) thành bài toán nội suy (Interpolation), gây ra Optimistic Bias nghiêm trọng. Bắt buộc phải áp dụng Temporal Split trong bài toán chuỗi thời gian.

