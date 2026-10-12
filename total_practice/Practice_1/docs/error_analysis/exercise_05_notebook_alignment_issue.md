# EXERCISE 05 — PHÂN TÍCH HIỆN TRẠNG NOTEBOOK

## 1. Thông tin vấn đề

```text
Practice: Practice_1
Exercise: 05 — Time Series Visualization
Notebook chính: notebooks/practice_1_present.ipynb
Phạm vi cell: 45–51
Exercise 5 là exercise implementation cuối cùng
Trạng thái phân tích: ĐÃ_PHÂN_TÍCH
Trạng thái triển khai: ĐÃ_HOÀN_THÀNH_VÀ_XÁC_MINH
Human authorization cho implementation: CÓ — 2026-10-12
Ngày phân tích: 2026-10-12
```

Tài liệu này chỉ ghi nhận evidence, root cause và impact của phần E5 hiện tại. Việc
tạo tài liệu không đồng nghĩa với authorization để sửa source, notebook hoặc chạy E5.

## 2. Phần đang làm tốt và cần giữ

- notebook đã có rolling mean và rolling standard deviation với window 12;
- giá trị mặc định hiện tại của Pandas tương ứng với `min_periods=12`,
  `center=False` và rolling standard deviation `ddof=1`;
- seasonal plot đã tổ chức dữ liệu theo tháng và năm;
- heatmap hiện hiển thị đủ 12 tháng và 12 năm, từ 1949 đến 1960;
- phần kết luận đã nhận diện đúng trend tăng, seasonality rõ và mức biến động tuyệt
  đối tăng theo thời gian;
- phần kết luận không tự động gọi một giá trị cao hoặc thấp là anomaly;
- bố cục rolling plot, seasonal plot và heatmap là nền tảng có thể tiếp tục sử dụng.

Các ý tưởng trên được giữ lại, nhưng implementation phải được chuyển về đúng source
owner, chạy được trong environment chuẩn và tạo output có thể truy vết.

## 3. Hành vi hiện tại và hành vi mong đợi

### 3.1 Khả năng tái thực thi

```text
Observed: cell 48 import seaborn as sn
Observed: seaborn không tồn tại trong .venv và không được khai báo trong pyproject.toml
Expected: E5 chạy bằng dependency đã được duyệt, không cần thêm dependency mới
```

Output hình đang nhúng trong notebook là output cũ. Execution count của ba code cell
E5 là `29`, `32`, `33`, không liên tục sau E4. Vì vậy đây không phải bằng chứng của
một lần chạy sạch theo intended order hiện tại.

### 3.2 Full-series visualization

E5 chưa tạo output bắt buộc:

```text
outputs/figures/13_full_time_series.png
```

E1 đã có reusable function `plot_time_series`; E5 có thể gọi lại function này với
output path riêng, không duplicate plotting logic.

### 3.3 Rolling statistics và trục thời gian

Cell 46 tính rolling statistics bằng:

```python
df["value"].rolling(window=12)
```

Các default hiện cho kết quả số học phù hợp protocol, nhưng tham số khoa học chưa
được khai báo rõ. Quan trọng hơn, plot dùng `df.index`, là `RangeIndex`, nên trục x
hiển thị `0, 20, 40, ...` dù nhãn là `Date`. Hình vì vậy không trình bày đúng timestamp
1949-01 đến 1960-12.

Notebook cũng mutate DataFrame cầu nối `df` bằng các cột `rolling_mean`,
`rolling_std`, `year` và `month`. Expected implementation phải dùng validated
DatetimeIndex của canonical `series`, tạo result object riêng và không phụ thuộc
hidden mutation.

Protocol cần được ghi rõ:

```text
window = 12
min_periods = 12
center = False
rolling std ddof = 1
expected initial NaN count = 11
first valid rolling timestamp = 1949-12-01
```

### 3.4 Monthly seasonal plot

Seasonal plot hiện thể hiện đúng dạng tháng trong năm, nhưng dùng palette `tab10`
cho 12 năm. Hai cặp năm bị lặp màu, làm giảm khả năng phân biệt đường biểu diễn.

Expected plot phải:

```text
dùng đúng month order 1–12
giữ đủ year grouping 1949–1960
dùng màu hoặc encoding phân biệt được 12 năm
dùng đơn vị passengers (thousands)
lưu thành outputs/figures/15_monthly_seasonal_plot.png
```

### 3.5 Month-year heatmap

Cell 50 dùng:

```python
pivot_table(..., aggfunc="mean")
```

Cách này có thể âm thầm lấy trung bình nếu xuất hiện duplicate month-year. Dữ liệu
hiện tại không có duplicate, nhưng implementation vi phạm stop condition của E5 vì
không kiểm tra trước và che giấu lỗi nếu input thay đổi.

Expected implementation phải:

```text
verify đúng một observation cho mỗi month-year
raise error khi có duplicate
dùng pivot không aggregation
verify shape = 12 × 12
verify row order January–December
verify column order 1949–1960
```

### 3.6 Outputs và source ownership

Các output E5 sau chưa tồn tại:

```text
outputs/figures/13_full_time_series.png
outputs/figures/14_rolling_mean_std.png
outputs/figures/15_monthly_seasonal_plot.png
outputs/figures/16_month_year_heatmap.png
outputs/results/rolling_statistics.csv
```

`rolling_statistics.csv` là optional theo exercise specification, nhưng nên được tạo
để kiểm tra 11 boundary NaN, tái sử dụng trong báo cáo và truy vết rolling values.

Notebook hiện chứa trực tiếp toàn bộ analytical và plotting logic E5. Chưa có reusable
owner `src/practice_1/analysis/rolling_statistics.py`, chưa có plotting API E5 trong
`practice_1.visualization` và chưa có `tests/test_rolling_statistics.py`.

### 3.7 Interpretation và liên kết upstream

Cell 51 mới có bốn đoạn kết luận tổng quát, chưa trả lời đủ 12 câu hỏi bắt buộc. Phần
kết luận chưa đối chiếu actual evidence từ:

```text
Exercise 1 — ACF/PACF
Exercise 3 — log-STL decomposition
Exercise 4 — 14 residual-IQR outlier candidates
```

Notebook cần phân biệt rõ:

```text
visual peak hoặc trough
seasonal peak hợp lệ
residual-based potential outlier candidate
confirmed anomaly
```

E5 chỉ được phép nói `potential outlier candidate`; không có evidence để xác nhận
anomaly hoặc tự động loại bỏ observation.

## 4. Baseline chẩn đoán

Validated AirPassengers input hiện có:

```text
Shape: 144 × 1
Date range: 1949-01-01 đến 1960-12-01
Frequency: monthly start
Missing values: 0
Duplicate timestamps: 0
```

Với trailing rolling window 12, `min_periods=12`, `center=False`, `ddof=1`:

```text
Initial NaN count của rolling mean: 11
Initial NaN count của rolling std: 11
First valid timestamp: 1949-12-01
Rolling mean tại 1960-12: 476.166667
Rolling std tại 1960-12: 77.737125
```

Monthly mean baseline:

```text
Tháng có trung bình cao nhất: July — 351.333333
Tháng có trung bình thấp nhất: November — 232.833333
```

Các số trên chỉ là baseline phục vụ review. Output chính thức phải đến từ reusable
logic đã kiểm thử và notebook execution sau khi plan được Human phê duyệt.

## 5. Root cause

Root cause chính là phần E5 ban đầu được viết như exploratory notebook cells độc lập:

- dựa vào DataFrame cầu nối và mutation từ notebook state;
- dùng dependency ngoài runtime contract;
- dựa vào default parameter thay vì explicit scientific configuration;
- tạo figure để hiển thị nhưng không lưu artifact;
- dùng aggregation thuận tiện thay cho validation duplicate;
- viết nhận xét thủ công, chưa nối với outputs E1, E3 và E4;
- chưa có reusable source owner và automated tests.

## 6. Impact

Nếu giữ nguyên, E5:

- không chạy được sau kernel restart trong `.venv` chuẩn;
- có rolling plot gắn nhãn Date nhưng không dùng timestamp;
- không tạo bốn figure bắt buộc;
- không chứng minh được rolling protocol và heatmap integrity;
- không có machine-readable rolling evidence;
- chưa hoàn thành 12 interpretation questions;
- chưa đủ evidence để bàn giao cho báo cáo Word cuối.

## 7. Ranh giới bảo vệ

```text
Cell E1–E4: không sửa, phạm vi 0–44
Cell E5: chỉ 45–51
Raw dataset: không sửa
Validated E1–E4 source và outputs: không thay đổi về nội dung
Không thêm seaborn hoặc dependency mới
Không train forecasting model
Không xác nhận anomaly chỉ từ visualization
Không xóa, clip hoặc replace outlier candidate
```

Checksum baseline:

```text
E1–E4 source/type: 8fd09505e835aac7ef494d57686790b64f23cec6d06e147f39ba0a36620ec88a
E5 source/type: adc6dea2462afb8283c4d6b14915a12fdcd8d29c5eee77ff0d8eaaffccc5c519
Notebook file: a5bd9901cd7e4444e2fd9f3f463eec4a9be728c172e137a643d32952a30666cf
Raw data: bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8
E3 decomposition components: 133d60b97887e997f7f17616589d5a4441af4664d14e8e86dbcdd71b9eeb90d0
E4 outlier candidates: 6f08fd16b5dd2c240801a83dc78b675302ad6e916dddb0ef8634c3611df77c39
```

## 8. Hướng sửa được đề xuất

- giữ lại ý tưởng rolling, seasonal plot, heatmap và nhận xét thận trọng hiện có;
- dùng canonical `series` có DatetimeIndex;
- tạo reusable rolling và seasonal-table logic;
- dùng Matplotlib hiện có thay cho seaborn;
- validate duplicate trước khi tạo heatmap;
- lưu bốn figure và rolling-statistics CSV;
- đối chiếu trực tiếp ACF/PACF, decomposition và outlier candidates;
- tạo diễn giải động trả lời đủ 12 câu hỏi;
- chạy tests và notebook từ đầu đến hết E5 sau khi được duyệt.

## 9. Quyết định hiện tại

```text
Error analysis đã được tạo: CÓ
Fix plan đã được tạo: CÓ
Error analysis reviewed by Human: CÓ
Fix plan approved by Human: CÓ
Cho phép triển khai E5: CÓ
```

## 10. Kết quả xử lý

E5 đã được đồng bộ và xác minh ngày 2026-10-12. Notebook chạy sạch toàn bộ 52 cell,
27 test đạt, bốn figure và rolling CSV đã được inspect. Raw data, source/type E1–E4
và 20 validated upstream outputs không đổi. Chi tiết tại
`docs/logs/exercise_05_execution.md`.

