# 6. ROLLING WINDOW VS EXPANDING WINDOW

> **Khung nghiên cứu**: Tuân thủ chuẩn 5W1H Research Template (What, Why, When, Where, Who, How, Example/Illustration, Advantages & Limitations).

---

### 1. WHAT — Khái niệm là gì?
- **Expanding Window (Cửa sổ mở rộng)**: Bắt đầu với một kích thước tập huấn luyện ban đầu ($N_0$). Khi thời gian tiến lên, mô hình giữ lại toàn bộ dữ liệu lịch sử cũ và bổ sung thêm dữ liệu mới. Kích thước tập huấn luyện tăng dần sau mỗi fold: $N_0, N_0+1, N_0+2, \dots$
- **Rolling Window (Cửa sổ trượt)**: Giữ kích thước tập huấn luyện cố định ($W$). Khi thời gian tiến lên một bước, dữ liệu cũ nhất ở đầu cửa sổ bị loại bỏ và dữ liệu mới nhất được nạp vào. Kích thước tập huấn luyện luôn bằng $W$.

### 2. WHY — Tại sao phải phân biệt hai chiến lược?
- Hai chiến lược phản ánh hai giả định nghiệp vụ khác nhau về giá trị của dữ liệu quá khứ:
  - Expanding Window giả định toàn bộ lịch sử đều có giá trị và càng nhiều dữ liệu thì mô hình học càng tốt.
  - Rolling Window giả định dữ liệu quá xa trong quá khứ đã trở nên lỗi thời do có sự dịch chuyển chế độ (Regime Shift) hoặc thay đổi hành vi thị trường.

### 3. WHEN — Khi nào nên dùng loại nào?
- **Dùng Expanding Window khi**:
  - Dữ liệu ổn định, mẫu quan sát còn ít.
  - Các quy luật chu kỳ dài hạn (mùa vụ năm) đòi hỏi phải có nhiều chu kỳ lịch sử để học.
- **Dùng Rolling Window khi**:
  - Chuỗi thời gian thay đổi cấu trúc nhanh chóng (non-stationary regime change).
  - Chi phí huấn luyện mô hình rất cao (không thể mở rộng tập dữ liệu quá lớn).
  - Môi trường kinh doanh có biến động mạnh và các năm trước không còn đại diện cho hiện tại.

### 4. WHERE — Vị trí trong thiết kế đánh giá
- Nằm trong việc cấu hình chiến lược chia tập huấn luyện ở bước Backtesting.

### 5. WHO — Các thông số cấu hình
- $W_{\text{train}}$: Kích thước cửa sổ (cố định trong Rolling, tối thiểu ban đầu trong Expanding).
- $H$: Forecast Horizon (độ dài tập kiểm chứng mỗi fold).
- $S$: Step size (bước nhảy dịch chuyển giữa các fold).

### 6. HOW — Cách thức hoạt động chi tiết
- **Minh họa Expanding Window (kích thước tăng dần)**:
  - Fold 1: Dữ liệu $[1, 2, 3]$ $\rightarrow$ Dự báo $4$
  - Fold 2: Dữ liệu $[1, 2, 3, 4]$ $\rightarrow$ Dự báo $5$
  - Fold 3: Dữ liệu $[1, 2, 3, 4, 5]$ $\rightarrow$ Dự báo $6$
- **Minh họa Rolling Window (kích thước cố định $W=3$)**:
  - Fold 1: Dữ liệu $[1, 2, 3]$ $\rightarrow$ Dự báo $4$
  - Fold 2: Dữ liệu $[2, 3, 4]$ $\rightarrow$ Dự báo $5$
  - Fold 3: Dữ liệu $[3, 4, 5]$ $\rightarrow$ Dự báo $6$

### 7. EXAMPLE / ILLUSTRATION — Sơ đồ so sánh
```text
[EXPANDING WINDOW]
Fold 1: [====]--------> Test 1
Fold 2: [======]------> Test 2
Fold 3: [========]----> Test 3
(Tập train nở rộng về bên phải, neo chặt mốc bắt đầu)

[ROLLING WINDOW]
Fold 1: [====]--------> Test 1
Fold 2:   [====]------> Test 2
Fold 3:     [====]----> Test 3
(Cửa sổ train trượt dần về phía trước, độ dài không đổi)
```

### 8. ADVANTAGES & LIMITATIONS — Bảng đối chiếu
| Tiêu chí | Expanding Window | Rolling Window |
|---|---|---|
| **Kích thước Train** | Tăng dần theo thời gian | Cố định không đổi |
| **Tận dụng lịch sử** | Tối đa hóa toàn bộ thông tin lịch sử | Bỏ qua dữ liệu cũ quá độ dài cửa sổ |
| **Ứng phó thay đổi regime** | Kém thích ứng nếu quá khứ có quy luật cũ | Thích ứng nhanh với xu hướng mới |
| **Chi phí tính toán** | Tăng dần ở các fold sau | Ổn định qua tất cả các fold |
| **Khó khăn thiết kế** | Phải chọn kích thước ban đầu | Phải chọn độ dài cửa sổ $W$ tối ưu |
