<div align="center">
<h1>Time Series Practice 1</h1>
</div>


## 1. Mục tiêu

Practice 1 là bài thực hành khám phá và chẩn đoán dữ liệu chuỗi thời gian dựa trên nội dung Chương 2.

Mục tiêu cuối cùng là đánh giá chuỗi có cấu trúc thời gian và chất lượng dữ liệu phù hợp để tiếp tục sang bài toán forecasting hay không.

Practice 1 không huấn luyện forecasting model.

## 2. Phạm vi bài thực hành

Practice 1 gồm sáu phần:

1. Tính và phân tích ACF/PACF.
2. Kiểm tra white noise.
3. Phân rã chuỗi thời gian.
4. Kiểm tra và xử lý chất lượng dữ liệu.
5. Trực quan hóa dữ liệu chuỗi thời gian.
6. Viết báo cáo và đánh giá forecastability.

Exercise 6 là báo cáo Word do TuVien tự thực hiện. Repository không tạo exercise
specification hoặc before-process plan riêng cho Exercise 6; AI implementation chỉ
chuẩn bị validated evidence từ Exercise 1–5.

Ngoài phạm vi:

```text
ARIMA/SARIMA fitting
Machine Learning
Deep Learning
train/validation/test modeling protocol
hyperparameter tuning
model backtesting
```

## 3. Dataset đã chốt

Dataset chính được Human phê duyệt cho Practice 1 là `AirPassengers`.

Nguồn canonical:

```text
CSV: https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv
Documentation: https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html
Expected observations: 144
Expected time range: 1949-01 through 1960-12
Expected frequency: monthly
Unit: thousands of international airline passengers
```

Không dùng URL có query parameter `?utm_source`. CSV tải về được giữ nguyên trong
`data/raw/`; checksum SHA-256 và ngày tải chỉ được ghi sau actual acquisition.

Rdatasets công bố license cho code của mirror nhưng không xác nhận dứt khoát một
standalone license cho mọi underlying dataset. Vì vậy provenance phải ghi đúng giới
hạn này, không gán GPL-3 trực tiếp cho dữ liệu AirPassengers.

Lý do lựa chọn:

- Dữ liệu có tần suất theo tháng.
- Có trend tăng rõ ràng.
- Có seasonality chu kỳ 12 tháng.
- Biên độ mùa vụ thay đổi theo mức của chuỗi.
- Phù hợp cho ACF/PACF, decomposition, seasonal plot và heatmap.
- Phù hợp để so sánh với white noise giả lập.

Raw dataset chưa được thêm vào repository. Source response, schema thực tế, checksum,
time semantics và data integrity vẫn phải được xác minh bằng execution trước analysis.

## 4. Hướng phân tích đã thống nhất

- ACF/PACF được dùng để nhận diện temporal structure, không tự động suy ra ARIMA order từ raw series.
- White noise được sinh từ `Normal(0, 1)` với 1000 observations và seed 42; ACF dùng
  maximum lag 40 và confidence level 95%.
- Ljung-Box là supplementary diagnostic, không thay thế yêu cầu ACF của đề bài.
- Decomposition dự kiến dùng log transform và STL với seasonal period phù hợp dữ liệu tháng.
- Missing values được giả lập trên working copy; raw dataset không bị thay đổi.
- Forward-fill và time interpolation được so sánh trên cùng các vị trí bị mask.
- Outlier được đánh dấu và phân tích, không tự động xóa hoặc thay thế.
- Với chuỗi có trend và seasonality, outlier detection ưu tiên thực hiện trên decomposition residual.
- Rolling statistics dùng trailing window 12, `min_periods=12`, `center=False` và
  rolling standard deviation với `ddof=1`.

## 4.1 Runtime contract

```text
Python: 3.12
Local environment: .venv
Package metadata: pyproject.toml
Installable package: practice_1
Package path: src/practice_1/
Notebook kernel: time-series-practice-1
```

Notebook và tests import reusable logic qua `practice_1.*`; không dùng `sys.path`
mutation hoặc absolute path. Tạo environment, cài dependencies và register kernel
chỉ được thực hiện sau approval Nhóm 4.

## 5. Workflow tổng quát

```text
Dataset provenance
→ Load raw data
→ Validate time index and data quality
→ Visualize the series
→ Analyze ACF/PACF
→ Run white-noise experiment
→ Decompose the series
→ Evaluate missing-value treatments
→ Analyze outliers
→ Assess forecastability
→ Hand validated evidence to TuVien for the user-owned Word report
```

## 6. Cấu trúc canonical dự kiến

```text
Practice_1/
├── .gitignore
├── README.md
├── pyproject.toml
├── config/
├── data/
│   ├── README.md
│   ├── raw/
│   └── processed/
├── docs/
│   ├── RULE_BASE/
│   ├── plan/
│   ├── current_flow/
│   ├── analysis_error/
│   ├── logs/
│   └── learning_notes/
├── notebooks/
├── src/
│   └── practice_1/
│       ├── __init__.py
│       ├── data/
│       ├── analysis/
│       └── visualization/
├── outputs/
│   ├── figures/
│   └── results/
└── tests/
```

Folder trong kiến trúc chỉ được sử dụng khi có artifact thực tế thuộc trách nhiệm của folder đó.

## 7. Rule routing

Nguồn bắt buộc:

1. [`.agents/RULES_INDEX.md`](../../.agents/RULES_INDEX.md)
2. [`docs/RULE_BASE/architecture_rule.md`](docs/RULE_BASE/architecture_rule.md)
3. [`docs/RULE_BASE/rule_code.md`](docs/RULE_BASE/rule_code.md)
4. Exercise detail đã được duyệt.
5. Before-process plan đã được duyệt.

Rule precedence tuân theo `.agents/RULES_INDEX.md`.

Nếu có conflict giữa các rule, phải dừng và chờ Human quyết định.

## 8. Deliverables dự kiến

```text
validated dataset summary
data-quality report
time-series overview plot
ACF/PACF plot
white-noise comparison
decomposition plot
missing-value method comparison
outlier analysis
rolling-statistics plot
monthly seasonal plot
month-year heatmap
forecastability conclusion
```

Danh sách filename và acceptance criteria đã được chuẩn hóa trong Exercise 1–5
specifications và đang chờ Human approval.

## 9. Trạng thái hiện tại

```text
Repository governance: active
Practice architecture/code rules: approved and active
README: created
Practice overview: approved
Exercise 1 specification and before-process plan: approved and completed
Exercise 2–5 specifications and before-process plans: standardized, waiting sequential approval
Current-flow document: updated
Exercise 6 plan: not required; TuVien owns the Word report
Dataset: AirPassengers added and integrity-verified
Source code: reusable Exercise 1 implementation completed
Notebook: Exercise 1 executed end-to-end
Outputs: Exercise 1 figures and machine-readable results generated and validated
```

Repository hiện có runnable, tested artifact cho Exercise 1. Exercise 2–5 chưa được
triển khai và vẫn chịu approval gate riêng.

## 10. Approval boundary

Việc duyệt README và overview không đồng nghĩa với approval để:

```text
thêm dataset
tạo config
viết source code
tạo notebook
chạy analysis
sinh outputs
kích hoạt architecture rule hoặc code rule
```

Các bước trên đã được Human phê duyệt và hoàn thành cho initialization cùng Exercise 1.
Approval này không mở rộng sang Exercise 2–5.
