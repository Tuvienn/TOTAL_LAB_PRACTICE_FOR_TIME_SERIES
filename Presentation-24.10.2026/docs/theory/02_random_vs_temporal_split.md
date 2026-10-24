# 2. RANDOM SPLIT VÀ TEMPORAL SPLIT

> **Khung nghiên cứu**: Tuân thủ chuẩn 5W1H Research Template (What, Why, When, Where, Who, How, Example/Illustration, Advantages & Limitations).

---

### 1. WHAT — Khái niệm là gì?
- **Random Split**: Trộn ngẫu nhiên các quan sát trong toàn bộ chuỗi rồi phân bổ theo tỷ lệ vào tập Train và Test (ví dụ: 80% train, 20% test). Phương pháp này giả định các quan sát độc lập và phân phối đồng nhất (I.I.D.).
- **Temporal Split**: Chia chuỗi thời gian tại một mốc thời gian xác định (cutoff date). Toàn bộ quan sát xảy ra trước mốc đó được đưa vào Train, toàn bộ quan sát sau mốc đó được đưa vào Test.

### 2. WHY — Tại sao quan trọng?
- Dữ liệu chuỗi thời gian có đặc tính phụ thuộc tự tương quan (autocorrelation), xu hướng (trend) và tính mùa vụ (seasonality).
- Chia ngẫu nhiên khiến mô hình được học từ các quan sát xảy ra **sau** thời điểm cần dự báo, biến bài toán dự báo tương lai thành bài toán nội suy (interpolation), tạo ra ảo tưởng về hiệu năng cao nhưng vô dụng khi triển khai.

### 3. WHEN — Khi nào cần chú ý?
- Bắt buộc dùng **Temporal Split** khi dữ liệu có timestamp, phụ thuộc độ trễ, có xu hướng hoặc thay đổi phân phối theo thời gian.
- **Random Split** chỉ áp dụng khi có bằng chứng chắc chắn các mẫu dữ liệu hoàn toàn độc lập với nhau và thứ tự thời gian không mang ý nghĩa nghiệp vụ.

### 4. WHERE — Xuất hiện ở đâu trong workflow?
- Nằm ở bước đầu tiên của quy trình chia tách dữ liệu (Data Splitting) trước khi tiền xử lý và huấn luyện.

### 5. WHO — Thành phần liên quan
- **Dòng dữ liệu lịch sử**: Tập hợp các quan sát liên tục theo thời gian $t_1, t_2, \dots, t_N$.
- **Forecast Origin (Mốc cắt)**: Thời điểm ranh giới phân tách quá khứ và tương lai.

### 6. HOW — Hoạt động như thế nào?
- **Temporal Split**:
  1. Xác định tỷ lệ hoặc mốc ngày phân tách (ví dụ 80% thời gian đầu làm train).
  2. Sắp xếp chuỗi tăng dần theo timestamp: $t_1 < t_2 < \dots < t_N$.
  3. Cắt: $\text{Train} = \{y_{t_1}, \dots, y_{t_k}\}$, $\text{Test} = \{y_{t_{k+1}}, \dots, y_{t_N}\}$.
  4. Giữ nguyên sự phân tách này qua toàn bộ các bước tiền xử lý tiếp theo.

### 7. EXAMPLE / ILLUSTRATION — Minh họa
- Giả sử chuỗi có 8 thời điểm: $T_1, T_2, T_3, T_4, T_5, T_6, T_7, T_8$.
  - **Random Split (SAI)**:
    - Train: $T_1, T_3, T_4, T_6, T_7$
    - Test: $T_2, T_5, T_8$
    - *Hậu quả*: Mô hình dùng thông tin tại $T_6, T_7$ để dự báo giá trị tại $T_5$ (thực tế tại $T_5$ thì $T_6, T_7$ chưa hề xuất hiện).
  - **Temporal Split (ĐÚNG)**:
    - Train: $T_1, T_2, T_3, T_4, T_5$
    - Test: $T_6, T_7, T_8$
    - *Bảo toàn*: Quá khứ chỉ dự báo tương lai, tương lai hoàn toàn vô hình với tập train.

### 8. ADVANTAGES & LIMITATIONS — Ưu điểm & Hạn chế
| Tiêu chí | Random Split | Temporal Split |
|---|---|---|
| **Thứ tự thời gian** | Bị xáo trộn nghiêm trọng | Được bảo toàn tuyệt đối |
| **Thông tin sử dụng** | Bị rò rỉ thông tin tương lai | Chỉ sử dụng dữ liệu quá khứ |
| **Độ tin cậy trong forecasting** | Không thực tế, lạc quan giả tạo | Phản ánh chân thực điều kiện thực tế |
| **Hạn chế** | Sai lệch nghiêm trọng | Một mốc chia đơn lẻ có thể chưa đại diện cho mọi chu kỳ |
