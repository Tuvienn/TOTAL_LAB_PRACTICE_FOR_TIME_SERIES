# 8. BASELINE FORECAST (MÔ HÌNH THAM CHIẾU CƠ SỞ)

> **Khung nghiên cứu**: Tuân thủ chuẩn 5W1H Research Template (What, Why, When, Where, Who, How, Example/Illustration, Advantages & Limitations).

---

### 1. WHAT — Khái niệm là gì?
- **Baseline Forecast**: Là mô hình dự báo sử dụng các quy tắc suy diễn đơn giản, không cần huấn luyện phức tạp, được dùng làm **mốc tham chiếu chuẩn** để đánh giá giá trị thực sự của các mô hình học máy hay thuật toán thống kê phức tạp hơn.
- Hai baseline phổ biến và quan trọng nhất trong Time Series:
  1. **Naive Forecast (Persistence Forecast)**:
     $$\hat{y}_{t+h} = y_t$$
     Dự báo toàn bộ tương lai bằng chính giá trị quan sát gần nhất ở thời điểm hiện tại.
  2. **Seasonal Naive Forecast**:
     $$\hat{y}_{t+h} = y_{t+h-m}$$
     Dự báo bằng giá trị quan sát ở cùng vị trí của chu kỳ mùa vụ gần nhất ($m$ là độ dài chu kỳ, ví dụ $m=12$ cho dữ liệu tháng, $m=7$ cho ngày trong tuần).

### 2. WHY — Tại sao bắt buộc phải so sánh với Baseline?
- Một mô hình phức tạp (Deep Learning, XGBoost, Prophet) không tự động có giá trị nếu sai số của nó không vượt qua được một phép gán đơn giản của Naive Forecast.
- So sánh với Baseline là bài kiểm tra liêm chính đầu tiên: Xác định xem mô hình có thực sự trích xuất được quy luật thông tin hữu ích hay chỉ đang ghi nhớ nhiễu và lãng phí tài nguyên tính toán.

### 3. WHEN — Khi nào cần triển khai Baseline?
- Phải được xây dựng **đầu tiên** trước khi tiến hành bất kỳ thử nghiệm mô hình phức tạp nào (Nguyên tắc *Baseline First*).
- Dùng Naive cho chuỗi Random Walk hoặc chuỗi không có tính mùa vụ rõ rệt.
- Dùng Seasonal Naive cho các chuỗi có chu kỳ lặp lại mạnh mẽ (điện lực, hàng không, du lịch).

### 4. WHERE — Vị trí trong quy trình
- Nằm song song với mô hình chính tại bước **Evaluation**: Baseline được áp dụng trên chính xác cùng tập test và tính toán cùng các chỉ số đo lường.

### 5. WHO — Các thành phần tham gia
- Dữ liệu lịch sử quan sát cuối cùng ($y_t$).
- Chu kỳ mùa vụ ($m$).
- Mô hình máy học chính cần so sánh.

### 6. HOW — Cách thức áp dụng chuẩn
1. Tính dự báo Baseline trên đúng tập Test của từng fold.
2. Tính các chỉ số $\text{MAE}_{\text{base}}, \text{RMSE}_{\text{base}}, \text{MAPE}_{\text{base}}$.
3. Tính chỉ số Relative Improvement:
   $$\text{Improvement} = \frac{\text{MAE}_{\text{base}} - \text{MAE}_{\text{model}}}{\text{MAE}_{\text{base}}} \times 100\%$$
4. Đưa ra kết luận:
   - Nếu $\text{Improvement} > 0$: Mô hình có giá trị gia tăng.
   - Nếu $\text{Improvement} \le 0$: Mô hình thất bại, cần dừng lại rà soát lại feature, data hoặc thuật toán.

### 7. EXAMPLE / ILLUSTRATION — Ví dụ thực tế
- Dữ liệu phụ tải điện lúc 9:00 sáng là 120 MW:
  - **Naive**: Dự báo cho 10:00 là 120 MW.
- Dữ liệu hành khách hàng không tháng 07/1959 là 548 ngàn người ($m=12$):
  - **Seasonal Naive**: Dự báo cho tháng 07/1960 chính là giá trị của tháng 07/1959 (548 ngàn người).

### 8. ADVANTAGES & LIMITATIONS — Ưu điểm & Hạn chế
- **Ưu điểm**:
  - Cực kỳ đơn giản, trực quan, không tốn tài nguyên huấn luyện.
  - Thiết lập ranh giới sàn (benchmark) rõ ràng, ngăn ngừa việc tự lừa dối bằng các con số sai số vô nghĩa.
- **Hạn chế**:
  - Không thể mô hình hóa xu hướng tăng/giảm dài hạn hoặc các biến động ngoại sinh.
  - Phụ thuộc lớn vào việc xác định đúng chu kỳ $m$.
