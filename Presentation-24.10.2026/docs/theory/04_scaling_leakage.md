# 4. SCALING LEAKAGE (RÒ RỈ TRONG CHUẨN HÓA DỮ LIỆU)

> **Khung nghiên cứu**: Tuân thủ chuẩn 5W1H Research Template (What, Why, When, Where, Who, How, Example/Illustration, Advantages & Limitations).

---

### 1. WHAT — Khái niệm là gì?
- **Scaling Leakage**: Là trường hợp bộ chuẩn hóa dữ liệu (như `StandardScaler`, `MinMaxScaler`, `RobustScaler`) được tính toán (`fit`) trên toàn bộ tập dữ liệu trước khi chia train/test, khiến các tham số thống kê ($\mu, \sigma, \min, \max$) của tương lai bị rò rỉ vào quá khứ.

### 2. WHY — Tại sao sai phạm và nguy hiểm?
- Bộ chuẩn hóa cũng là một mô hình học tham số từ dữ liệu:
  - `StandardScaler`: Học $\mu = \frac{1}{N}\sum y_i$ và $\sigma = \sqrt{\frac{1}{N}\sum (y_i - \mu)^2}$.
  - `MinMaxScaler`: Học $\min(y)$ và $\max(y)$.
- Nếu dữ liệu tương lai có xu hướng tăng mạnh hoặc có ngoại lệ lớn, giá trị $\mu$ hoặc $\max$ của toàn bộ dữ liệu sẽ cao hơn nhiều so với quá khứ. Việc đưa giá trị này vào quá trình chuẩn hóa tập train sẽ ngầm "báo trước" cho mô hình biết biên độ và xu thế của tương lai.

### 3. WHEN — Khi nào lỗi này gây tác động nặng nề nhất?
- Khi chuỗi thời gian có xu hướng tăng/giảm mạnh (Strong Trend).
- Khi mức độ biến động (Variance) hoặc phân phối của chuỗi thay đổi theo thời gian (Regime shift).
- Khi tập tương lai chứa các điểm dị biệt hoặc đỉnh mùa vụ chưa từng gặp trong quá khứ.

### 4. WHERE — Vị trí trong Pipeline
- Nằm ở tầng Preprocessing trong luồng xử lý: ngay trước khi đưa ma trận đặc trưng vào mô hình học máy.

### 5. WHO — Các đối tượng liên quan
- Tham số thống kê: $\mu_{\text{train}}, \sigma_{\text{train}}$ vs $\mu_{\text{all}}, \sigma_{\text{all}}$.
- Tập Train và Tập Test / Validation.

### 6. HOW — Đối chiếu cách làm Sai và cách làm Đúng

#### Cách làm SAI (Pipeline A — Leakage):
```python
# Sai lầm nghiêm trọng: Fit trên toàn bộ dữ liệu
scaler.fit(all_data)
scaled_data = scaler.transform(all_data)
train, test = temporal_split(scaled_data)
```

#### Cách làm ĐÚNG (Pipeline B — Correct):
```python
# Quy trình chuẩn: Chia trước, fit chỉ trên train
train, test = temporal_split(data)
scaler.fit(train)
train_scaled = scaler.transform(train)
test_scaled = scaler.transform(test)
```
*Lưu ý trong Backtesting*: Quy trình chuẩn này phải được thực thi lặp lại độc lập trên từng fold (mỗi fold có một scaler riêng được fit chỉ trên phần train của fold đó).

### 7. EXAMPLE / ILLUSTRATION — Minh họa quy trình
```text
SAI:
Toàn bộ dữ liệu ──> [Fit Scaler] ──> [Transform toàn bộ] ──> Chia Train / Test

ĐÚNG:
Chia dữ liệu theo thời gian ──> Train ──> [Fit Scaler] ──> [Transform Train]
                             └── Test  ──────────────────> [Transform Test (dùng scaler của Train)]
```

### 8. ADVANTAGES & LIMITATIONS — So sánh
| Đặc tính | Pipeline A (Leakage) | Pipeline B (Correct) |
|---|---|---|
| **Tham số Scaler** | Chứa $\mu, \sigma$ của cả tương lai | Chỉ chứa $\mu, \sigma$ của quá khứ |
| **Phân phối tập Train** | Bị biến dạng bởi thông tin tương lai | Phản ánh đúng thực tế lịch sử |
| **Kết quả đánh giá** | Sai số thấp nhân tạo, kết luận sai | Phản ánh trung thực sai số thực tế |
| **Độ phức tạp code** | Đơn giản, viết ẩu | Yêu cầu đóng gói Pipeline nghiêm ngặt |
