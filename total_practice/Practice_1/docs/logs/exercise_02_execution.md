# EXERCISE 02 — NHẬT KÝ THỰC THI WHITE NOISE

## 1. Phạm vi

```text
Practice: Practice_1
Exercise: 02 — White Noise
Ngày thực thi: 2026-10-12
Notebook chính: notebooks/practice_1_present.ipynb
Cell E2: 22–27
Trạng thái: HOÀN_TẤT_VÀ_ĐÃ_XÁC_MINH
Exercise 3–5 được phép sửa: KHÔNG
```

## 2. Thay đổi đã thực hiện

- thêm `generate_white_noise` dùng `numpy.random.default_rng`;
- giữ đúng 1.000 quan sát, seed 42 và Normal(0, 1);
- thêm kiểm tra tham số và bảo vệ NumPy global random state;
- tái sử dụng `compute_acf_table`, không tạo ACF implementation mới;
- bổ sung hàm vẽ chuỗi, bảng ACF và hình so sánh;
- giữ đúng sáu cell E2, không làm dịch ranh giới E3;
- giữ nguyên công thức confidence bound xấp xỉ trong cell 24;
- tái sử dụng `outputs/results/acf_values.csv` của E1;
- tạo ba hình và một CSV bắt buộc của E2;
- tạo diễn giải động từ kết quả thực thi thực tế;
- không thêm Ljung–Box vì đây là diagnostic tùy chọn.

## 3. Phần E2 được giữ lại

```text
sample size 1000
seed 42
Normal(0, 1)
bố cục biểu đồ chuỗi
công thức ±1.96/sqrt(n)
maximum ACF lag 40
confidence level 95%
bố cục so sánh hai ACF
cấu trúc diễn giải nhiều ý
```

## 4. Bằng chứng thực thi

```text
Python: 3.12.15
Kernel: time-series-practice-1
Notebook chạy từ cell 0 đến cell 27
Tổng code cell đã chạy: 16
Execution count: 1 đến 16
Error output: 0
```

Kernel phát cảnh báo tiêu chuẩn về kết nối TCP nội bộ không mã hóa. Cảnh báo không
ảnh hưởng kết quả phân tích.

## 5. Kết quả kiểm thử

```text
JSON notebook: hợp lệ
Biên dịch source E1–E2: đạt
compileall src và tests: đạt
pytest E1 và E2: 12 passed
kiểm tra trực quan ba hình E2: đạt
```

Test E2 xác nhận:

- generator tái tạo đúng kết quả với cùng seed;
- generator không làm thay đổi NumPy global random state;
- tham số không hợp lệ bị từ chối;
- mean, sample standard deviation và ACF lag 1 khớp baseline;
- bảng ACF có đủ lag 0–40 và confidence interval.

## 6. Kết quả khoa học

```text
Sample size: 1000
Mean: -0.028891550995946837
Sample standard deviation: 0.9892170876543358
Approximate 95% bound: ±0.061980642139300234
White-noise ACF lag 1: 0.08705487216529355
Số lag 1–40 vượt confidence interval: 1
Lag vượt confidence interval: 1

AirPassengers ACF lag 1: 0.9480473407524913
AirPassengers ACF lag 12: 0.7603950422625557
AirPassengers ACF lag 24: 0.5321898304658020
AirPassengers ACF lag 36: 0.33702359902053575
```

Một spike white-noise riêng lẻ vượt CI không đủ phủ nhận hành vi white noise khi
toàn bộ ACF còn lại chủ yếu nằm quanh 0 và không tạo decay hoặc mẫu lặp rõ ràng.

## 7. Output đã tạo và kiểm tra

```text
outputs/figures/04_white_noise_series.png
outputs/figures/05_white_noise_acf.png
outputs/figures/06_white_noise_vs_airpassengers_acf.png
outputs/results/white_noise_acf_values.csv
```

Ba hình có nhãn rõ, không bị cắt hoặc chồng lấn, hiển thị đủ lag 0–40 và khoảng
tin cậy 95%.

## 8. Checksum

```text
Notebook trước E2:
56a1d70a28e28ea666f45047c1b1edf46312abdf202f1267c0af94d6122dfca8

Notebook sau thực thi E2:
0cb6ed1f6f167093469e66b69e5a4fc5ba11090ce201bcdf7389a75af0ed66bf

Source/type E2 trước:
9ad620833628b0ada61eedb07a4bfd323110ab80d8e2deb926c27e2a8fcfb3f4

Source/type E2 sau:
513e24d1818c8e737af6456b44af1ed7f84a8cc41eb4a413188a93e951ac1f30

Source/type E1 trước và sau:
16d9c0a85ae393fde6cfecc3b728c6913fce921936b58ade74c6bf8fa6328c56

Source/type E3–E5 trước và sau:
b92915cb3d9e2ff08031ae4c525cf975ebe061ad7134ff46c166a729ef5da08b

Raw data trước và sau:
bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8

Validated E1 ACF trước và sau:
dace4669019161485248d41afcf8bdbfcad4532e22ebd8ccc2c4ffc19d40b69d
```

## 9. Ranh giới tiếp theo

Exercise 2 đã hoàn tất. Exercise 3 chưa được sửa hoặc triển khai trong lần này và
vẫn cần người dùng review, phê duyệt plan và cấp authorization riêng.
