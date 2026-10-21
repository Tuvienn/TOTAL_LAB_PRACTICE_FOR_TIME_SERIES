# EXERCISE 01 — NHẬT KÝ THỰC THI

## Phạm vi

Thực hiện EDA, chuyển cột ngày thành time index, trực quan hóa chuỗi gốc và thiết
lập ranh giới train/test theo thời gian. Không chạy ADF, differencing, huấn luyện
model hoặc forecast.

## Các bước đã thực hiện

- Nạp `datasets/raw/a10.csv` mà không thay đổi raw file.
- Xác nhận schema `date,value`.
- Parse `date` và đặt làm `DatetimeIndex` theo tháng.
- Kiểm tra thứ tự thời gian, timestamp trùng, missing values và tháng bị thiếu.
- Chia train/test 80/20 theo thời gian và niêm phong phần test.
- Tạo và kiểm tra `outputs/figures/01_original_time_series.png`.

## Bằng chứng

```text
rows: 204
date range: 1991-07-01 to 2008-06-01
frequency: monthly start (MS)
missing values: 0
duplicate timestamps: 0
missing monthly intervals: 0
train: 163 observations, 1991-07-01 to 2005-01-01
test: 41 observations, 2005-02-01 to 2008-06-01
```

## Nhận xét EDA

Chuỗi có xu hướng tăng dài hạn rõ ràng. Chuyển động lặp lại trong năm cho thấy
khả năng tồn tại mùa vụ chu kỳ 12 tháng. Vì level và mean thay đổi theo thời gian,
EDA ban đầu nhận định chuỗi có khả năng non-stationary. Đây chỉ là nhận xét trực
quan; kiểm định ADF thuộc E2.

## Output

- `outputs/figures/01_original_time_series.png`
- `outputs/results/dataset_validation.csv`
- `outputs/results/train_test_boundary.csv`

## Xác nhận

`python -m pytest -q`: 2 test đạt.
