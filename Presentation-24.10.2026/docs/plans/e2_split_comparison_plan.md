# E2 PLAN — RANDOM SPLIT VS TEMPORAL SPLIT

## 1. Mục tiêu
Thực hiện và so sánh thực nghiệm giữa Random Split và Temporal Split trên cùng một bài toán mô hình hóa để chứng minh:
- Vì sao chia ngẫu nhiên gây sai lệch đánh giá lạc quan phi thực tế (optimistic bias).
- Tại sao dự báo chuỗi thời gian bắt buộc phải tôn trọng chiều thời gian.

## 2. Thiết lập thực nghiệm
- **Thiết lập A (Random Split)**: Xáo trộn ngẫu nhiên các quan sát rồi chia theo tỷ lệ (ví dụ: 80% train, 20% test).
- **Thiết lập B (Temporal Split)**: Chọn một mốc thời gian (cutoff date), toàn bộ dữ liệu trước mốc làm Train, toàn bộ dữ liệu sau mốc làm Test.
- Giữ nguyên kiến trúc mô hình, siêu tham số và chỉ số đánh giá giữa 2 thiết lập.

## 3. Output mong đợi
- Mô tả chi tiết 2 evaluation setups.
- `02_random_vs_temporal_split.png`: Sơ đồ hoặc biểu đồ phân bố quan sát trên dòng thời gian giữa 2 cách chia.
- `split_comparison_metrics.csv`: Bảng đối chiếu MAE, RMSE, MAPE giữa Random Split và Temporal Split.
- Nhận xét và lý giải nguyên nhân dẫn đến sự chênh lệch kết quả dựa trên bằng chứng thực nghiệm.
