# 7. MAE, RMSE, MAPE VÀ GIỚI HẠN CỦA TỪNG CHỈ SỐ

> **Khung nghiên cứu**: Tuân thủ chuẩn 5W1H Research Template (What, Why, When, Where, Who, How, Example/Illustration, Advantages & Limitations).

---

### 1. WHAT — Khái niệm & Công thức toán học
Bộ ba chỉ số cốt lõi dùng để đo khoảng cách giữa giá trị thực tế ($y_i$) và giá trị dự báo ($\hat{y}_i$):

1. **MAE (Mean Absolute Error — Sai số tuyệt đối trung bình)**:
   $$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|$$
   - Đo độ lớn trung bình của sai số theo đúng đơn vị gốc của chuỗi.

2. **RMSE (Root Mean Squared Error — Căn bậc hai sai số bình phương trung bình)**:
   $$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2}$$
   - Bình phương sai số trước khi lấy trung bình nên phạt rất nặng các lỗi lớn.

3. **MAPE (Mean Absolute Percentage Error — Sai số phần trăm tuyệt đối trung bình)**:
   $$\text{MAPE} = \frac{100\%}{n} \sum_{i=1}^n \left| \frac{y_i - \hat{y}_i}{y_i} \right|$$
   - Biểu diễn sai số dưới dạng phần trăm (%), không phụ thuộc vào thang đo gốc.

### 2. WHY — Tại sao phải sử dụng phối hợp cả ba chỉ số?
- Không có một chỉ số đơn lẻ nào hoàn hảo cho mọi góc nhìn:
  - MAE cho biết mức sai lệch trung bình thông thường một cách trực quan.
  - RMSE cho biết mô hình có gặp phải các sai số đột biến cực lớn (catastrophic errors) hay không.
  - MAPE giúp người quản trị phi kỹ thuật hiểu được sai số tương đối tính theo tỷ lệ phần trăm.

### 3. WHEN — Khi nào nên ưu tiên chỉ số nào?
- **Ưu tiên MAE**: Khi muốn chỉ số đo lường trực quan, ổn định và không muốn các ngoại lệ (outliers) làm biến dạng kết quả.
- **Ưu tiên RMSE**: Khi trong bài toán nghiệp vụ, một sai số lớn gây hậu quả nghiêm trọng hơn rất nhiều so với nhiều sai số nhỏ (ví dụ: dự báo quá tải lưới điện, dự báo thiếu hụt thuốc cấp cứu).
- **Ưu tiên MAPE**: Khi cần so sánh hiệu năng giữa các chuỗi có quy mô khác nhau (ví dụ: sản lượng bán hàng của siêu thị lớn vs cửa hàng tiện lợi nhỏ).
- **CẢNH BÁO NGUY HIỂM VỚI MAPE**: Tuyệt đối không dùng MAPE khi dữ liệu có giá trị bằng 0 hoặc rất gần 0, vì mẫu số $y_i \approx 0$ sẽ khiến MAPE tiến tới vô cùng.

### 4. WHERE — Vị trí trong luồng đánh giá
- Nằm ở tầng cuối cùng của quá trình kiểm chứng: được tính toán trên tập validation/test sau khi mô hình đã xuất ra kết quả dự báo.

### 5. WHO — Các biến số trong phép tính
- $y_i$: Giá trị thực tế tại thời điểm $i$.
- $\hat{y}_i$: Giá trị mô hình dự báo tại thời điểm $i$.
- $e_i = y_i - \hat{y}_i$: Sai số dự báo (Residual / Forecast Error).

### 6. HOW — Cách đọc và so sánh chỉ số
- Luôn thỏa mãn quan hệ: $\text{RMSE} \ge \text{MAE}$.
- Khoảng cách giữa RMSE và MAE càng lớn $\rightarrow$ Phương sai của sai số càng cao (mô hình dự báo có một số điểm sai lệch rất lớn).
- Nếu $\text{RMSE} \approx \text{MAE}$, sai số phân bố đều và mô hình ổn định.

### 7. EXAMPLE / ILLUSTRATION — Ví dụ định lượng
Giả sử có 3 quan sát với sai số thực tế:
- Trường hợp 1: Sai số các điểm là $2, 3, 4$:
  - $\text{MAE} = (2+3+4)/3 = 3$
  - $\text{RMSE} = \sqrt{(4+9+16)/3} = \sqrt{9.67} \approx 3.11$ (RMSE gần bằng MAE).
- Trường hợp 2: Sai số các điểm là $1, 1, 10$:
  - $\text{MAE} = (1+1+10)/3 = 4$
  - $\text{RMSE} = \sqrt{(1+1+100)/3} = \sqrt{34} \approx 5.83$ (RMSE nhảy vọt lên 5.83 do bị phạt nặng bởi sai số 10).

### 8. ADVANTAGES & LIMITATIONS — Bảng tổng kết
| Chỉ số | Đơn vị | Ưu điểm | Nhược điểm lớn nhất |
|---|---|---|---|
| **MAE** | Cùng đơn vị với $y$ | Dễ hiểu, bền vững trước outliers | Không phạt nặng các lỗi nghiêm trọng |
| **RMSE** | Cùng đơn vị với $y$ | Phạt mạnh sai số lớn, toán học khả vi | Nhạy cảm thái quá với ngoại lệ đơn lẻ |
| **MAPE** | Phần trăm (%) | Dễ giải thích cho ban giám đốc, so sánh đa quy mô | Không tính được khi $y=0$, lệch lạc khi $y \approx 0$ |
