# EXERCISE 05 — NHẬT KÝ TRIỂN KHAI VÀ XÁC MINH

## 1. Phạm vi

```text
Ngày: 2026-10-12
Notebook: notebooks/practice_1_present.ipynb
Cell sửa: 45–51
Cell chạy: 0–51
Trạng thái: HOÀN_THÀNH_VÀ_XÁC_MINH
```

## 2. Implementation

- tạo `analysis/rolling_statistics.py` cho trailing rolling statistics, seasonal
  long-form data, month-year matrix và monthly summary;
- explicit `window=12`, `min_periods=12`, `center=False`, `ddof=1`;
- từ chối centered rolling, missing input, duplicate timestamp và duplicate
  month-year;
- dùng Matplotlib hiện có, không thêm `seaborn` hoặc dependency mới;
- bổ sung ba reusable plotting functions;
- tạo `tests/test_rolling_statistics.py`;
- cập nhật duy nhất cell 45–51 của notebook;
- đối chiếu actual evidence từ E1 ACF, E3 residual diagnostics và 14 candidates E4;
- tạo diễn giải động trả lời đủ 12 câu hỏi E5.

## 3. Kết quả khoa học

```text
Observations: 144
Date range: 1949-01 đến 1960-12
Original missing values: 0
Rolling initial NaN count: 11
First valid rolling timestamp: 1949-12-01
Rolling mean tại 1960-12: 476.166667
Rolling std tại 1960-12: 77.737125
Rolling mean/std correlation: 0.959070
Mean rolling std — first 36 valid values: 19.471693
Mean rolling std — last 36 values: 66.728290
Highest monthly mean: July — 351.333333
Lowest monthly mean: November — 232.833333
Mean yearly amplitude — first 3 years: 51.333333
Mean yearly amplitude — last 3 years: 214.666667
ACF lag 12: 0.760395
E3 residual Ljung–Box lag 12 p-value: 0.000037
E4 residual-IQR candidates cross-checked: 14
```

Visualization cho thấy trend tăng, seasonality 12 tháng và variability trên thang
gốc tăng theo level. Giá trị lớn nhất `622` tại `1960-07` nằm trong mùa cao điểm và
không được tự động xác nhận là anomaly. E5 chỉ đối chiếu E4 candidates, không xóa,
clip hoặc replace observation.

## 4. Outputs

```text
13_full_time_series.png
SHA-256: a6f081790273203f27ede4520285e86f7a8cc9e2070c47a688b0821dd7e1318a

14_rolling_mean_std.png
SHA-256: d14a866f640308f2cfa2bb6f2bbe4f7ef69362c122450a83f86a59891625c39b

15_monthly_seasonal_plot.png
SHA-256: 11e61315ebd05fa7dfe69b684dada4be7404bc4f854c7af7a796cbd236214461

16_month_year_heatmap.png
SHA-256: 0d3e5df6c69357f26089c4ad70ab24cc015d099c3716f157b28fbdfa82a01d22

rolling_statistics.csv
SHA-256: b1470429ce5a9594d786b32df0e45deebe9a6647a57cc8af61435079f77149f6
Shape: 144 × 4
```

Bốn figure đã được visual inspection. Trục rolling dùng date thật, seasonal plot
phân biệt đủ 12 năm và heatmap có đúng 12 tháng × 12 năm với nhãn/đơn vị rõ ràng.
Figure 13 có cùng nội dung và checksum với figure 01 vì E5 chủ động tái sử dụng cùng
validated data và reusable `plot_time_series`, nhưng được lưu thành artifact E5 riêng.

## 5. Validation

```text
pytest: 27 passed
Notebook cells: 52
Notebook code cells: 33
Notebook execution counts: 1–33 liên tục
Notebook error outputs: 0
git diff --check: passed
Raw SHA-256: bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8
E1–E4 source/type: 8fd09505e835aac7ef494d57686790b64f23cec6d06e147f39ba0a36620ec88a
E5 source/type: ecf7d8532db937d97f0783ed36012b99b26de09043cbfea4d907e2673b37421f
Notebook SHA-256: ebef60ac0620cb20204d3e3a58c8a721d06abd4bf142d257eac0ffdf7b1d32c3
Protected raw/E1–E4 artifact checksum changes: 0
```

## 6. Technical closure E1–E5

```text
Required figures 01–16: tồn tại
Required/selected result artifacts: tồn tại
Raw data immutable: đạt
Chronological execution: đạt
Future-information boundary: đạt
No automatic outlier deletion: đạt
No forecasting model training: đạt
Notebook clean execution: đạt
Full test suite: đạt
Unresolved implementation blocker: không
```

Phạm vi implementation E1–E5 đã hoàn tất. Word report tiếp tục được quản lý ngoài repository và
không phải artifact của workflow.

