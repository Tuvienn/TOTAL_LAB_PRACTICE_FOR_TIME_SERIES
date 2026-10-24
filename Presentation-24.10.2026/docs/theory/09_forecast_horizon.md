# 9. FORECAST HORIZON (ĐÁNH GIÁ THEO CHÂN TRỜI DỰ BÁO)

> **Khung nghiên cứu**: Tuân thủ chuẩn 5W1H Research Template (What, Why, When, Where, Who, How, Example/Illustration, Advantages & Limitations).

---

### 1. WHAT — Khái niệm là gì?
- **Forecast Horizon ($H$)**: Là khoảng cách số bước thời gian giữa thời điểm bắt đầu đưa ra dự báo (Forecast Origin $t$) và thời điểm mục tiêu cần dự báo ($t+h$):
  $$h \in \{1, 2, \dots, H\}$$
- Ví dụ:
  - $h=1$: Dự báo bước kế tiếp (Short-term / 1 bước).
  - $h=H$: Dự báo điểm xa nhất ở cuối chu kỳ dự báo.
- Đơn vị của $h$ phụ thuộc vào tần suất của dữ liệu (1 giờ, 1 ngày, 1 tháng).

### 2. WHY — Tại sao phải phân tích sai số theo từng bước $h$?
- Sai số dự báo thường không bất biến mà có xu hướng biến đổi khi khoảng cách dự báo tăng lên. Dự báo càng xa thì độ bất định càng lớn và thông tin quá khứ suy giảm giá trị.
- Việc chỉ tính một con số trung bình duy nhất cho toàn bộ horizon sẽ che khuất bức tranh thực tế: Mô hình có thể dự báo rất xuất sắc ở các bước đầu ($h=1..3$) nhưng hoàn toàn hỏng ở các bước sau ($h=10..12$).
- Phân tích theo horizon giúp doanh nghiệp biết được ngưỡng thời gian nào mô hình còn đủ độ tin cậy để ra quyết định tác nghiệp hoặc chiến lược.

### 3. WHEN — Khi nào cần đánh giá?
- Trong mọi bài toán dự báo đa bước (Multi-step Ahead Forecasting), ví dụ: dự báo 24 giờ tới cho phụ tải điện, dự báo 12 tháng tới cho doanh thu bán hàng.

### 4. WHERE — Vị trí trong báo cáo kết quả
- Nằm ở khâu phân tích chi tiết sau Backtesting: Trích xuất ma trận kết quả $(N_{\text{folds}} \times H)$ và tổng hợp sai số theo từng cột $h$.

### 5. WHO — Các thông số chính
- $h$: Chỉ số bước dự báo ($1 \le h \le H$).
- $e_h$: Sai số tại bước dự báo $h$.

### 6. HOW — Cách thức thực hiện
1. Thu thập tất cả các cặp $(y_{t+h}, \hat{y}_{t+h})$ trên mọi fold backtest.
2. Với mỗi giá trị $h \in \{1, \dots, H\}$, tính riêng:
   $$\text{MAE}(h) = \frac{1}{N_{\text{folds}}} \sum_{k=1}^{N_{\text{folds}}} |y_{t_k+h} - \hat{y}_{t_k+h}|$$
   $$\text{RMSE}(h) = \sqrt{\frac{1}{N_{\text{folds}}} \sum_{k=1}^{N_{\text{folds}}} (y_{t_k+h} - \hat{y}_{t_k+h})^2}$$
3. Vẽ đồ thị đường biểu thị sai số theo trục hoành $h$.
4. **Nguyên tắc thực nghiệm**: Không được giả định tiên nghiệm rằng sai số bắt buộc phải tăng tuyến tính theo $h$; phải tôn trọng kết quả thực nghiệm thực tế (đặc biệt khi có yếu tố mùa vụ mạnh tại một số bước $h$).

### 7. EXAMPLE / ILLUSTRATION — Minh họa
- Dự báo nhu cầu điện 24 giờ tiếp theo ($H=24$):
  - $h=1$: Dự báo giờ thứ 1 (ngay sau mốc hiện tại).
  - $h=12$: Dự báo buổi trưa.
  - $h=24$: Dự báo cùng giờ ngày hôm sau.

```text
Sai số (MAE)
 │        . . . . .  (Mô hình thoái hóa ở horizon xa)
 │      .
 │    .
 │  .                (Dự báo ngắn hạn chính xác cao)
 └───────────────────────> Chân trời dự báo h
   h=1  h=2  h=3 ... h=H
```

### 8. ADVANTAGES & LIMITATIONS — Ưu điểm & Hạn chế
- **Ưu điểm**: Cung cấp bức tranh toàn diện và trung thực về khả năng suy giảm hiệu năng theo thời gian của mô hình; hỗ trợ xác định chính xác thời điểm cần tái huấn luyện (retrain).
- **Hạn chế**: Đòi hỏi quy trình thu thập và cấu trúc ma trận dự báo phức tạp hơn so với việc tính toán 1 chỉ số gộp.
