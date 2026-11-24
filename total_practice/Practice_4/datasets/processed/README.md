# Processed Dataset – Electricity Load + Weather (Hourly)

Thư mục này chứa dữ liệu chuỗi thời gian đa biến đã được làm sạch và đồng bộ theo từng giờ, phục vụ cho bài thực hành **Practice 4 – Multivariate Time Series Forecasting**.

## 1. Thông tin tệp dữ liệu
* **Tên tệp:** `electricity_load_weather_hourly.csv`
* **Nguồn gốc:** Tổng hợp từ `energy_dataset.csv` và `weather_features.csv` trong thư mục `datasets/raw/` (bộ *Hourly Energy Demand Generation and Weather* – Tây Ban Nha).
* **Script tạo dữ liệu:** `src/build_dataset.py`
* **Phạm vi thời gian:** `2014-12-31 23:00:00+00:00` đến `2018-12-31 22:00:00+00:00` (múi giờ UTC).
* **Tần suất lấy mẫu:** 1 giờ (`1h`).
* **Kích thước:** 35,064 dòng × 4 biến đặc trưng (không còn giá trị khuyết `NaN`).

## 2. Mô tả các cột dữ liệu

| Tên cột | Vai trò | Đơn vị | Nguồn ánh xạ | Mô tả |
| :--- | :--- | :--- | :--- | :--- |
| `time` *(index)* | Timestamp | UTC | `time` / `dt_iso` | Mốc thời gian liên tục theo từng giờ |
| `load` | Biến mục tiêu & đầu vào | MW | `total load actual` | Tổng phụ tải điện năng tiêu thụ thực tế |
| `temperature` | Biến đầu vào | °C | `temp` (Madrid) | Nhiệt độ không khí (đã quy đổi từ Kelvin sang độ C) |
| `humidity` | Biến đầu vào | % | `humidity` (Madrid) | Độ ẩm tương đối |
| `wind_speed` | Biến đầu vào | m/s | `wind_speed` (Madrid) | Tốc độ gió |

## 3. Quy trình tiền xử lý đã áp dụng
1. **Lọc không gian:** Trích xuất dữ liệu khí tượng tại **Madrid** (thủ đô Tây Ban Nha) để đại diện cho điều kiện thời tiết gắn với phụ tải lưới điện quốc gia.
2. **Chuẩn hóa múi giờ & khử trùng lặp:** Chuyển đổi toàn bộ mốc thời gian về chuẩn `UTC`, nhóm theo từng giờ (`time`) và lấy trung bình cộng đối với các bản ghi thời tiết trùng lặp trong cùng một khung giờ.
3. **Quy đổi đơn vị:** Chuyển đổi nhiệt độ từ Kelvin sang độ C (`temp - 273.15`) và cố định tần suất lưới thời gian `1h`.
4. **Xử lý giá trị khuyết:** Áp dụng nội suy tuyến tính hai chiều (`linear interpolation`, `limit_direction="both"`) cho 36 giá trị `NaN` ở cột `load` nhằm bảo toàn tính liên tục của chuỗi thời gian cho cửa sổ trượt 24 giờ.

## 4. Cách nạp dữ liệu trong Python
```python
import pandas as pd

df = pd.read_csv(
    "../datasets/processed/electricity_load_weather_hourly.csv",
    index_col="time",
    parse_dates=True,
)