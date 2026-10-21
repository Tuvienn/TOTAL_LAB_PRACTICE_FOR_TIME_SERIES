# EXERCISE 01 — EDA VÀ CHUẨN BỊ CHUỖI THỜI GIAN

## 1. Thông tin bài tập

```text
Practice: Practice_2
Exercise ID: EXERCISE_01
Topic: EDA and Time-Series Preparation
Dataset: Monthly Retail Sales
Frequency: Monthly
Chronological split: approximately 80% train / 20% test
Model training required: NO
Specification status: APPROVED
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_01_execution.md
```

## 2. Mục tiêu

Mục tiêu của bài tập:

- load Dataset 1 và chuyển cột `date` thành time index;
- validate schema và monthly time index;
- bảo toàn chronological order và kiểm tra data quality;
- quan sát trend, seasonality và dấu hiệu non-stationarity ban đầu;
- xác lập chronological train/test boundary;
- niêm phong test set cho đến Exercise 5;
- tạo evidence đầu vào cho ADF, differencing, ACF/PACF và ARIMA.

Exercise 1 không chạy ADF, không differencing, không fit model và không forecast.

## 3. Dữ liệu đầu vào

```text
File: datasets/raw/a10.csv
Meaning: Monthly Retail Sales
Time column: date
Target column: value
Frequency: monthly
```

Schema, data types, date range và frequency phải được kiểm tra từ file thực tế.
Raw file là immutable source evidence; parsing chỉ được thực hiện trên working object.

## 4. Các bước bắt buộc

1. Load và inspect `a10.csv` bằng head, info, shape, schema, date range, missing-value và duplicate checks.
2. Parse cột `date`, set `date` làm `DatetimeIndex`, rồi validate chronological order, monthly frequency và missing monthly intervals.
3. Tạo original time-series plot để quan sát trend, seasonality, variance và possible anomalies.
4. Ghi nhận EDA observations dựa trên actual output; trả lời trend, seasonality và khả năng dừng ban đầu.
5. Xác định approximately 80% train và 20% test theo thời gian, không shuffle.
6. Ghi train/test timestamps, observation counts và forecast horizon.
7. Seal test set; E02–E04 chỉ dùng original training series.

## 5. Tham số khoa học

```text
Time column: date
Target column: value
Frequency: monthly
Train proportion: approximately 80%
Test proportion: approximately 20%
Shuffle: NO
Model training: NO
Forecast generation: NO
ADF and differencing: NOT IN THIS EXERCISE
```

## 6. Output dự kiến

```text
outputs/figures/01_original_time_series.png
outputs/results/dataset_validation.csv
outputs/results/train_test_boundary.csv
```

Phải có narrative interpretation dựa trên actual checks và plot.

Execution result và trạng thái hoàn thành phải được đọc từ `docs/status/current_status.md`
và `docs/logs/exercise_01_execution.md`; specification này không tự sở hữu trạng thái runtime.

## 7. Câu hỏi diễn giải

1. Chuỗi có xu hướng không?
2. Chuỗi có dấu hiệu mùa vụ không?
3. Chuỗi có khả năng dừng không dựa trên EDA?
4. Schema, time index, date range và monthly frequency có hợp lệ không?
5. Có missing values, duplicate timestamps hoặc missing intervals không?
6. Những kết luận nào cần được kiểm tra bằng ADF ở E02?

## 8. Tiêu chí xác nhận

```text
[ ] Dataset load thành công
[ ] Raw data không bị sửa
[ ] date và value được xác định từ schema thực tế
[ ] Cột date được chuyển thành DatetimeIndex
[ ] Timestamp, chronological order và monthly frequency được validate
[ ] Missing values, duplicate timestamps và missing intervals được kiểm tra
[ ] Original-series plot được tạo và inspect
[ ] Trend, seasonality và initial stationarity observations có evidence
[ ] Train/test boundary được xác định theo thời gian
[ ] Test set được sealed cho E02–E04
[ ] Không shuffle, train model hoặc forecast
[ ] Interpretation dựa trên actual outputs
```

## 9. Điều kiện dừng

Phải dừng nếu source/schema/date/frequency không xác minh được, duplicate hoặc
missing interval chưa được giải thích, raw data bị thay đổi, boundary không xác lập
được, figure không inspect được, hoặc scope/dependency cần mở rộng.

Khi dừng: `STOP → document issue → explain impact → propose next action → wait for approval`.

## 10. Điều kiện hoàn thành

```text
dataset validation complete
AND original series inspected
AND EDA observations documented
AND chronological boundary validated
AND test set sealed
AND required output inspected
AND no unresolved blocking issue
```

## 11. Vai trò đối với bước sau

Kết quả cung cấp input cho E02 ADF, E03 differencing, E04 ACF/PACF và E05 ARIMA
evaluation. Exercise 1 không tự quyết định stationarity, `d`, `p`, `q` hoặc final model.
