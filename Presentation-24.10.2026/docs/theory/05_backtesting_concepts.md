# 5. BACKTESTING TRONG CHUỖI THỜI GIAN

> **Khung nghiên cứu**: Tuân thủ chuẩn 5W1H Research Template (What, Why, When, Where, Who, How, Example/Illustration, Advantages & Limitations).

---

### 1. WHAT — Khái niệm là gì?
- **Backtesting (Kiểm chứng lịch sử đa mốc)**: Là quy trình thiết lập nhiều mốc dự báo (Forecast Origin) trong quá khứ. Tại mỗi mốc, mô hình chỉ được phép sử dụng dữ liệu xảy ra trước mốc đó để huấn luyện, sau đó dự báo một khoảng tương lai giả lập (Forecast Horizon) và so sánh với giá trị thực tế đã được ghi nhận.

### 2. WHY — Tại sao một lần train/test duy nhất là chưa đủ?
- Một lần chia train/test duy nhất chỉ đo lường được hiệu năng của mô hình trong **một khoảng thời gian cục bộ**. Nếu khoảng thời gian đó rơi vào giai đoạn quá dễ (ít biến động) hoặc giai đoạn bất thường (khủng hoảng, thiên tai), kết luận rút ra sẽ hoàn toàn thiên lệch.
- Backtesting cung cấp nhiều quan sát sai số qua nhiều chế độ biến động khác nhau, giúp đánh giá độ bền vững và tính ổn định của mô hình.

### 3. WHEN — Khi nào cần dùng Backtesting?
- Khi so sánh và lựa chọn giữa các thuật toán mô hình hóa khác nhau.
- Khi tinh chỉnh siêu tham số (Hyperparameter Tuning).
- Khi đánh giá năng lực dự báo trước khi triển khai chính thức.

### 4. WHERE — Vị trí trong Workflow
- Nằm ở giai đoạn **Validation & Model Evaluation**, thay thế cho K-Fold Cross Validation thông thường của dữ liệu bảng.

### 5. WHO — Các thành phần cấu thành một Fold Backtest
| Thành phần | Định nghĩa & Ý nghĩa |
|---|---|
| **Forecast Origin ($t$)** | Mốc thời gian bắt đầu thực hiện dự báo. |
| **Train Window** | Đoạn dữ liệu lịch sử trước origin được phép sử dụng để fit preprocessing và model. |
| **Validation Window** | Đoạn dữ liệu tương lai giả lập ngay sau origin dùng để tính toán sai số. |
| **Forecast Horizon ($H$)** | Số bước dự báo về phía trước ($h = 1, 2, \dots, H$). |
| **Fold** | Một vòng lặp hoàn chỉnh gồm: Huấn luyện $\rightarrow$ Dự báo $\rightarrow$ Đo lường sai số. |

### 6. HOW — Quy trình thực hiện từng Fold
1. Thiết lập danh sách các Forecast Origin theo bước trượt (step size).
2. Tại mỗi fold:
   - Cắt tập Train từ đầu đến origin.
   - Cắt tập Validation từ origin đến origin + $H$.
   - Fit tiền xử lý và mô hình CHỈ trên tập Train của fold đó.
   - Dự báo cho khoảng Validation.
   - Tính toán các chỉ số sai số (MAE, RMSE, MAPE).
3. Tổng hợp kết quả: Tính trung bình (Mean), độ lệch chuẩn (Std) và biên độ biến thiên của các chỉ số qua toàn bộ các fold.

### 7. EXAMPLE / ILLUSTRATION — Minh họa các Folds
- Giả sử chuỗi có 8 mốc thời gian, dự báo 1 bước ($H=1$):
  - **Fold 1**: Train: $T_1 \dots T_5$ $\rightarrow$ Test: $T_6$
  - **Fold 2**: Train: $T_1 \dots T_6$ $\rightarrow$ Test: $T_7$
  - **Fold 3**: Train: $T_1 \dots T_7$ $\rightarrow$ Test: $T_8$
- Dự báo nhiều bước ($H=3$):
  - **Fold 1**: Train: $T_1 \dots T_5$ $\rightarrow$ Test: $T_6, T_7, T_8$
  - **Fold 2**: Train: $T_1 \dots T_6$ $\rightarrow$ Test: $T_7, T_8, T_9$

### 8. ADVANTAGES & LIMITATIONS — Ưu điểm & Hạn chế
- **Ưu điểm**:
  - Mô phỏng sát nhất với quy trình vận hành dự báo thực tế ngoài đời.
  - Cung cấp phân phối sai số đa dạng, phát hiện mô hình chỉ tốt trong giai đoạn bình lặng.
  - Cho phép phân tích sai số chi tiết theo từng bước thời gian.
- **Hạn chế**:
  - Tốn tài nguyên và thời gian tính toán do phải fit lại mô hình nhiều lần.
  - Các fold có thể phụ thuộc nhau vì dùng chung một phần lịch sử.
