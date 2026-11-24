# Raw Dataset – Hourly Energy Demand Generation and Weather

Thư mục này lưu trữ dữ liệu thô nguyên bản (read-only) phục vụ cho bài thực hành **Practice 4 – Multivariate Time Series Forecasting: Electricity Load + Weather**.

> **Nguyên tắc quản lý:** Không chỉnh sửa hoặc ghi đè trực tiếp lên các tệp trong thư mục này. Mọi bước làm sạch, ghép bảng và biến đổi đặc trưng đều được thực hiện tự động thông qua script `src/build_dataset.py` và xuất kết quả sang `datasets/processed/`.

## 1. Nguồn gốc & Bối cảnh dữ liệu
* **Tên bộ dữ liệu:** Hourly Energy Demand Generation and Weather (Spain)
* **Liên kết nguồn (Kaggle):** [Energy consumption, generation, prices and weather](https://www.kaggle.com/datasets/nicholasjhana/energy-consumption-generation-prices-and-weather)
* **Nguồn thu thập gốc:**
  * **Phụ tải & Sản lượng điện:** ENTSO-E (Cổng dữ liệu công khai của Mạng lưới các nhà điều hành hệ thống truyền tải điện châu Âu).
  * **Giá thanh toán điện năng:** Red Eléctrica de España (REE – Đơn vị vận hành hệ thống truyền tải điện Tây Ban Nha).
  * **Dữ liệu khí tượng:** OpenWeather API (dữ liệu thời tiết theo giờ tại 5 thành phố lớn nhất Tây Ban Nha).
* **Phạm vi thời gian:** 4 năm dữ liệu theo từng giờ, từ `2015-01-01 00:00:00+01:00` đến `2018-12-31 23:00:00+01:00`.

## 2. Chi tiết các tệp dữ liệu thô

### A. `energy_dataset.csv`
* **Kích thước:** 35,064 dòng × 29 cột.
* **Nội dung:** Dữ liệu theo giờ về tổng phụ tải thực tế, dự báo phụ tải từ TSO, sản lượng phát điện phân theo từng loại hình năng lượng (nhiệt điện than/khí, thủy điện, điện gió, mặt trời, hạt nhân, sinh khối...) và giá điện thực tế/dự báo tại Tây Ban Nha.
* **Các cột liên quan trực tiếp đến bài toán:**
  * `time`: Mốc thời gian ghi nhận theo từng giờ (định dạng ISO 8601).
  * `total load actual`: Tổng phụ tải điện năng tiêu thụ thực tế (MW) – biến mục tiêu chính (`load`).
  * `total load forecast`: Dự báo phụ tải từ TSO (có thể dùng làm mốc tham chiếu/benchmark nếu cần mở rộng phân tích).

### B. `weather_features.csv`
* **Kích thước:** 178,396 dòng × 17 cột.
* **Nội dung:** Dữ liệu quan trắc thời tiết theo giờ tại 5 thành phố lớn nhất Tây Ban Nha (`Madrid`, `Valencia`, `Bilbao`, ` Barcelona`, `Seville`).
* **Các cột được trích xuất cho bài toán:**
  * `dt_iso`: Mốc thời gian ghi nhận thời tiết (khớp với cột `time` của bảng phụ tải).
  * `city_name`: Tên thành phố quan trắc.
  * `temp`: Nhiệt độ không khí (đơn vị gốc: **Kelvin**).
  * `humidity`: Độ ẩm tương đối (%).
  * `wind_speed`: Tốc độ gió (m/s).

## 3. Các vấn đề dữ liệu thô đã ghi nhận (cần xử lý ở bước `build_dataset.py`)
* **Trùng lặp bản ghi thời tiết:** Tệp `weather_features.csv` chứa 3,076 dòng trùng cặp `(dt_iso, city_name)` do ghi nhận nhiều trạng thái thời tiết trong cùng một khung giờ.
* **Khoảng trắng dư thừa:** Giá trị `' Barcelona'` ở cột `city_name` có chứa dấu cách ở đầu chuỗi.
* **Khuyết dữ liệu phụ tải:** Cột `total load actual` trong `energy_dataset.csv` thiếu 36 giá trị tại một số khung giờ rời rạc.