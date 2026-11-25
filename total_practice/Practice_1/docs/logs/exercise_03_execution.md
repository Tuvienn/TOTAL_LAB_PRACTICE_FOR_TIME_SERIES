# EXERCISE 03 — NHẬT KÝ TRIỂN KHAI VÀ XÁC MINH

## 1. Phạm vi thực thi

```text
Practice: Practice_1
Exercise: 03 — Time Series Decomposition
Ngày thực thi: 2026-10-12
Notebook chính: notebooks/practice_1_present.ipynb
Cell được sửa: 28–31
Cell được chạy: 0–31
Cell Exercise 4–5 được sửa hoặc chạy: KHÔNG
Trạng thái: HOÀN_THÀNH_VÀ_XÁC_MINH
```

Đã xác nhận error analysis và fix plan E3 trước khi implementation bắt đầu.

## 2. Phần triển khai

### Analysis

Tạo `src/practice_1/analysis/decomposition.py` với các public API:

```text
validate_decomposition_series
log_transform_series
compute_stl_decomposition
compute_residual_diagnostics
```

Implementation kiểm tra positive, finite, missing values, chronology, duplicate
timestamp và complete monthly-start frequency. Log transform không sửa input. STL
dùng đúng `period=12`, `robust=True` và kiểm tra component reconstruction.

Residual diagnostics tái sử dụng `compute_acf_table`, tạo ACF đến 40 lag với khoảng
tin cậy 95% và Ljung–Box đúng lag 12.

### Visualization

Bổ sung:

```text
plot_log_transformed_series
plot_stl_decomposition
plot_decomposition_residual_diagnostics
```

Các figure ghi rõ natural-log scale. Residual figure gồm time plot và ACF trong hai
panel.

### Tests

Tạo `tests/test_decomposition.py` để kiểm tra:

- input không bị sửa và index được bảo toàn;
- dữ liệu zero, negative, missing, non-finite hoặc thiếu tháng bị từ chối;
- component schema, row count, alignment và reconstruction;
- residual ACF và Ljung–Box khớp baseline runtime.

## 3. Notebook

Notebook giữ nguyên bốn cell E3:

```text
cell 28: heading, validation, log transform, STL, figure 07 và 08
cell 29: hướng dẫn đọc evidence trên log scale
cell 30: component export, residual diagnostics, figure 09
cell 31: diễn giải động trả lời đủ 10 câu hỏi
```

Notebook được chạy bằng kernel sạch `time-series-practice-1` chỉ đến cell 31.

```text
Số code cell đã chạy: 19
Execution count: 1–19 liên tục
Error output: 0
```

Kernel phát standard warning về TCP không mã hóa; warning này không ảnh hưởng kết
quả tính toán và không phải notebook error.

## 4. Output đã tạo và inspect

### Figures

```text
07_log_transformed_series.png
SHA-256: 19f33885b18808f404783ca5295597258ee64bb8364a858555edaa0d22b33ee8

08_stl_decomposition.png
SHA-256: db3ba5e5fe11203aabc294222090635c5647f3f07186d07c6555e0b67041b6f6

09_decomposition_residual.png
SHA-256: 137273906eb49b9f87c48a084bbf4afb2fd3606dce1e03dd5c9109adcaeadf78
```

Ba hình đã được kiểm tra trực quan. Không có title, axis label hoặc panel bị cắt;
log scale, period, robust setting và confidence interval được trình bày rõ.

### Machine-readable results

```text
decomposition_components.csv
SHA-256: 133d60b97887e997f7f17616589d5a4441af4664d14e8e86dbcdd71b9eeb90d0
Shape: 144 × 5
Columns: timestamp, observed_log, trend_log, seasonal_log, residual_log
Missing values: 0

residual_diagnostics.csv
SHA-256: a884f8fc43e4599fc9070bd1f2b5f3ca65c5708ab22963895b4cc1436e55eca5
Rows: 1
Required lag: 12
```

## 5. Kết quả khoa học chính

```text
Trend log: 4.7985 → 6.1925
Trend change, first half: 0.7601
Trend change, second half: 0.6339
Seasonal strength: 0.9593
Seasonal component correlation at lag 12: 0.9978
Original yearly amplitude CV: 0.5197
Log yearly amplitude CV: 0.1373
Residual mean: 0.000290
Residual sample standard deviation: 0.026527
Residual ACF lag 1: 0.374728
Residual ACF lag 12: -0.133553
Residual significant ACF lags: 1, 2
Ljung–Box lag-12 statistic: 41.709381
Ljung–Box lag-12 p-value: 0.000037
Largest absolute residual timestamp: 1953-04
Largest residual value: 0.115555
```

Kết luận: log transform làm seasonal amplitude ổn định hơn và STL loại bỏ phần lớn
trend/mùa vụ 12 tháng. Residual chưa giống white noise hoàn toàn vì còn tự tương quan
ngắn hạn và Ljung–Box lag 12 có p-value nhỏ. Điểm 1953-04 chỉ được chuyển thành ứng
viên cần kiểm tra ở E4, không bị tự động xóa hoặc thay thế.

## 6. Validation

```text
compileall src/tests: ĐẠT
pytest toàn bộ suite: 20 passed
notebook JSON: HỢP_LỆ
notebook cell 0–31: CHẠY_SẠCH
figure inspection: ĐẠT
component schema/alignment: ĐẠT
component reconstruction: ĐẠT
Ljung–Box output contract: ĐẠT
git diff --check: ĐẠT
```

## 7. Bằng chứng không regression

```text
Notebook sau E3 SHA-256:
f24166e60abddecd515a2951eaff5b1612b27025ba5be6538ba4e83d52e77597

Source/type cell E1–E2:
baa231632af529bcf729d6b0f7278f25c63219e44c8211d73fa587dca586fe2d

Source/type cell E3 sau sửa:
f09125cf3fc9fcfc518bf9efa59d134b72a465d7486625e57b5000761c6d57a7

Source/type cell E4–E5:
d95ada507e4fc960ea3757804cdec9feb5d12fcbf951e7f808610f6ab38f7c26

Raw dataset SHA-256:
bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8

Validated E1 ACF SHA-256:
dace4669019161485248d41afcf8bdbfcad4532e22ebd8ccc2c4ffc19d40b69d

Validated E2 white-noise ACF SHA-256:
4bc90dc8de41e39801a74a5fb8a6f05c6b3983802e06ed2f64dc5539dd0aa304
```

Checksum source/type của E1–E2 và E4–E5 khớp baseline. Raw dataset, validated E1
ACF và E2 outputs không thay đổi.

## 8. Kết luận thực thi

```text
Exercise 3 implementation: COMPLETED
Exercise 3 validation: COMPLETED
Exercise 4 authorization: NOT_GRANTED
```

E3 đã sẵn sàng làm upstream evidence cho E4. Không triển khai E4 nếu chưa hoàn tất
review/error-analysis/fix-plan và chưa có scope confirmation riêng.

