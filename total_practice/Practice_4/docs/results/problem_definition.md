# Practice 4 (v2) — Problem Definition

- **Tài liệu tham chiếu:** `references/chapter4-5.pdf` (*Chương 4-5: Mô hình Dự đoán Chuỗi thời gian Đa biến*).
- **Cấu hình khóa v2:** `config/practice_4_v2.json`.

## 1. 5W1H

| Câu hỏi | Định nghĩa chính thức (v2) |
|---|---|
| **What** | Bài thực hành dự báo chuỗi thời gian đa biến 1 bước tiếp theo: so sánh các đường cơ sở (`Persistence`, `Seasonal-24`, `Seasonal-168`), mô hình thống kê cổ điển (`Stationary VAR`), Machine Learning (`GPU XGBoost + SHAP`) và Deep Learning (`GPU PyTorch LSTM`). |
| **Why** | Phân tích tương tác phụ tải điện – thời tiết – lịch, kiểm chứng ưu/nhược điểm từng họ mô hình theo `chapter4-5.pdf` và trả lời 6 câu hỏi đề bài bằng bằng chứng định lượng. |
| **Where** | Nguồn chính thức `UCI ElectricityLoadDiagrams20112014` (Bồ Đào Nha, `CC BY 4.0`) kết hợp thời tiết tái phân tích `Open-Meteo ERA5` (Lisbon `0.50`, Porto `0.35`, Coimbra `0.15`, `CC BY 4.0`). |
| **When** | Giai đoạn ổn định `2012-01-01T00:00:00+00:00` → `2014-12-31T23:00:00+00:00` (`26,304` giờ UTC liên tục, xử lý chuyển giờ DST `Europe/Lisbon`, lọc `321/370` khách hàng hoạt động từ tháng 1/2012). |
| **How** | Pipeline 9 stage (`S0 → S8`) với cổng kiểm thử `pytest` riêng cho từng stage, chống rò rỉ tương lai tuyệt đối và đồng bộ `docs/plans/file_map.csv`. |

## 2. Công thức bài toán & Biến đầu vào

Tại cuối mỗi giờ $t$ (origin), hệ thống quan sát véc-tơ 4 biến vật lý:

$$X_t = [\text{load}_t\;(\text{kW}),\; \text{temp}_t\;({}^\circ\text{C}),\; \text{humidity}_t\;(\%),\; \text{wind\_speed}_t\;(\text{m/s})]$$

- **Mục tiêu:** Dự báo phụ tải thực tế ở giờ tiếp theo $\hat{y}_{t+1} = \widehat{\text{load}}_{t+1}$ trên thang đo gốc (**kW**).
- **Thông tin cho phép tại origin $t$:** Lịch sử nhân quả $\le t$ (không sử dụng phụ tải hay thời tiết quan sát tại $\ge t+1$) và các đặc trưng lịch tất định (`hour`, `day_of_week`, `day_of_year`, `is_weekend`, `is_dst`, `is_holiday` quốc gia `PT`) tại $t+1$.
- **Ngoài phạm vi:** Dự báo đa bước (`multi-step`), triển khai dịch vụ production hay tự động thu thập thời gian thực.

## 3. Sáu câu hỏi nghiên cứu cần trả lời bằng bằng chứng

1. Biến thời tiết nào liên hệ mạnh nhất với điện năng?
2. Khi nào mô hình VAR thất bại?
3. XGBoost học được thông tin gì từ thời tiết và feature engineering?
4. LSTM thể hiện chu kỳ ngày/tuần như thế nào?
5. LSTM có bị overfitting không?
6. Machine Learning (XGBoost) và Deep Learning (LSTM) khác nhau như thế nào trên bài toán này?
