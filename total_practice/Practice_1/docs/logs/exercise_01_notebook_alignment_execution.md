# EXERCISE 01 — NHẬT KÝ ĐỒNG BỘ NOTEBOOK

## 1. Phạm vi

```text
Practice: Practice_1
Exercise: 01 — Phân tích ACF/PACF
Ngày thực thi: 2026-10-12
Notebook chính: notebooks/practice_1_present.ipynb
Trạng thái: HOÀN_TẤT_VÀ_ĐÃ_XÁC_MINH
Exercise 2–5 được phép sửa: KHÔNG
```

## 2. Thay đổi đã thực hiện

- thay luồng đọc CSV và chuyển đổi thời gian thủ công bằng
  `practice_1.data.load_air_passengers`;
- hiển thị schema chuẩn, số dòng, khoảng thời gian, tần suất, missing value,
  timestamp trùng lặp, thứ tự thời gian và đơn vị;
- sử dụng `compute_acf_table` và `compute_pacf_table` với 40 lag,
  `alpha=0.05` và PACF `method="ywm"`;
- tạo ba biểu đồ bằng các hàm trong `practice_1.visualization`;
- sửa đơn vị thành nghìn hành khách;
- bổ sung khoảng tin cậy 95% và diễn giải riêng cho lag 12, 24 và 36;
- bỏ kết luận lựa chọn bậc ARIMA/SARIMA từ chuỗi gốc;
- cập nhật metadata thành Python 3.12.15 và kernel
  `time-series-practice-1`;
- giữ các biến cầu nối `df`, `series`, `acf_values` và `pacf_values`
  để không thay đổi source của Exercise 2–5.

## 3. Bằng chứng toàn vẹn

```text
SHA-256 notebook trước sửa:
be03a79273f5cddbb22376255bb6eec17dd8b23a732524230d65fc8d18d3981b

SHA-256 notebook sau thực thi E1:
56a1d70a28e28ea666f45047c1b1edf46312abdf202f1267c0af94d6122dfca8

SHA-256 raw data trước và sau:
bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8

SHA-256 source cell Exercise 2–5 trước và sau:
80b64197b1c394868e380d30ea60d4bd6a6a8467a9e05c2c1826e8c088db9117
```

Raw data không thay đổi. Source và loại cell từ Exercise 2 đến Exercise 5 không
thay đổi.

## 4. Kết quả kiểm thử

```text
JSON notebook: hợp lệ
Biên dịch source E1: đạt
compileall src: đạt
pytest tests/test_air_passengers.py tests/test_acf_pacf.py: 2 passed
Kernel: time-series-practice-1
Code cell E1 đã chạy: 12
Error output: 0
Kiểm tra trực quan ba hình: đạt
```

Kernel phát cảnh báo tiêu chuẩn về kết nối TCP nội bộ không mã hóa. Cảnh báo không
ảnh hưởng đến kết quả phân tích.

## 5. Kết quả khoa học đã đối chiếu

```text
ACF lag 1:  0.9480473407524913
ACF lag 12: 0.7603950422625557
ACF lag 24: 0.5321898304658020
ACF lag 36: 0.33702359902053575
PACF lag 13: -0.5396912419071259
```

Lag 12 có khoảng tin cậy 95% không chứa 0. Lag 24 và 36 có ACF dương nhưng
khoảng tin cậy chứa 0, nên chỉ được diễn giải là bằng chứng hỗ trợ mẫu lặp chứ
không khẳng định riêng lẻ có ý nghĩa thống kê ở mức 5%.

## 6. Output đã kiểm tra

```text
outputs/figures/01_time_series_overview.png
outputs/figures/02_acf_40_lags.png
outputs/figures/03_pacf_40_lags.png
outputs/results/acf_values.csv
outputs/results/pacf_values.csv
outputs/results/exercise_01_findings.json
```

Các biểu đồ có nhãn rõ ràng, không bị cắt hoặc chồng lấn và thể hiện đúng khoảng
tin cậy khi áp dụng.

## 7. Ranh giới tiếp theo

Exercise 1 đã hoàn tất. Exercise 2 chưa được triển khai hoặc sửa trong lần này và
vẫn cần authorization riêng theo quy trình của project.
