# 3. DATA LEAKAGE TRONG CHUỖI THỜI GIAN

> **Khung nghiên cứu**: Tuân thủ chuẩn 5W1H Research Template (What, Why, When, Where, Who, How, Example/Illustration, Advantages & Limitations).

---

### 1. WHAT — Khái niệm là gì?
- **Data Leakage (Rò rỉ dữ liệu)**: Xảy ra khi thông tin mà mô hình không thể biết tại thời điểm dự báo thực tế lại vô tình được đưa vào quá trình huấn luyện, tiền xử lý, tạo đặc trưng hoặc tinh chỉnh siêu tham số.

### 2. WHY — Tại sao nguy hiểm?
- Rò rỉ dữ liệu tạo ra sai số đo lường thấp giả tạo trong quá trình phát triển (Overly optimistic performance).
- Khi triển khai vào thực tế sản xuất, thông tin tương lai không còn tồn tại, hiệu năng của mô hình sẽ sụp đổ nghiêm trọng, gây tổn thất lớn về chi phí và quyết định kinh doanh.

### 3. WHEN — Khi nào dễ xuất hiện?
- Khi thực hiện chuẩn hóa (Scaling) hoặc điền khuyết (Imputation) trên toàn bộ dataset trước khi chia tập.
- Khi tạo các đặc trưng trượt (Rolling features) có chứa quan sát tại hoặc sau thời điểm dự báo.
- Khi sử dụng các biến ngoại sinh chỉ được ghi nhận sau khi sự kiện xảy ra.
- Khi lặp lại việc chọn mô hình nhiều lần trên cùng một tập test.

### 4. WHERE — Rò rỉ xuất hiện ở đâu trong Pipeline?
| Vị trí | Ví dụ rò rỉ điển hình |
|---|---|
| **Chia dữ liệu** | Trộn các mốc thời gian (Random Split) rồi dùng tương lai để dự báo quá khứ. |
| **Tiền xử lý** | Tính `mean`, `std`, `min`, `max` hoặc giá trị điền khuyết trên toàn bộ tập dữ liệu. |
| **Feature Engineering** | Tạo rolling mean hoặc rolling sum không dịch chuyển (lag-shift), chứa thông tin tương lai. |
| **Tuning & Selection** | Tối ưu hóa siêu tham số trực tiếp trên tập test cuối cùng thay vì dùng validation/backtest. |

### 5. WHO — Thành phần chịu ảnh hưởng
- Bộ tiền xử lý (Scalers, Imputers, Encoders).
- Ma trận đặc trưng (Feature Matrix $X$).
- Mô hình dự báo (Forecaster).

### 6. HOW — Nguyên tắc phòng tránh triệt để
1. **Chia tập theo thời gian trước tiên**: Luôn thực hiện Temporal Split trước khi chạm vào bất kỳ bước biến đổi dữ liệu nào.
2. **Nguyên tắc đóng băng tham số**: Mọi đối tượng học tham số (`fit`) chỉ được thực hiện trên tập Train. Tập Test chỉ được gọi `transform`.
3. **Đặc trưng độ trễ an toàn**: Các đặc trưng Lag và Rolling phải dịch chuyển về quá khứ ($t-1, t-2, \dots$), tuyệt đối không dùng cửa sổ đối xứng (centered rolling).
4. **Kiểm soát thông tin khả dụng**: Chỉ sử dụng những thông tin sẵn có tại chính xác thời điểm thực hiện dự báo (Forecast Origin).

### 7. EXAMPLE / ILLUSTRATION — Minh họa
```text
[Quy trình RÒ RỈ - SAI]
Toàn bộ dữ liệu ──> Fit Scaler (biết trước Mean/Std tương lai) ──> Chia Train / Test ──> Train mô hình

[Quy trình CHUẨN - ĐÚNG]
Toàn bộ dữ liệu ──> Chia Train / Test theo thời gian
                      ├── Train ──> Fit Scaler ──> Transform Train ──> Train mô hình
                      └── Test  ─────────────────> Transform Test  ──> Đánh giá dự báo
```

### 8. ADVANTAGES & LIMITATIONS — Ưu điểm & Hạn chế
- **Ưu điểm của việc chống rò rỉ**: Bảo đảm tính liêm chính khoa học, phản ánh chính xác 100% năng lực thực tế của mô hình khi đưa vào vận hành.
- **Thách thức**: Đòi hỏi kỹ năng thiết kế pipeline chặt chẽ, phải kiểm soát nghiêm ngặt các bước biến đổi trong từng fold backtesting.
