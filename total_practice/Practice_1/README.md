<div align="center">
<h1>Time Series Practice 1</h1>
</div>


## Mục lục

- <a href="#1-mục-tiêu" style="color:#1f6feb;">1. Mục tiêu</a>
  - <a href="#11-truy-cập-nhanh" style="color:#1f6feb;">1.1. Truy cập nhanh</a>
- <a href="#2-phạm-vi-bài-thực-hành" style="color:#1f6feb;">2. Phạm vi bài thực hành</a>
- <a href="#3-dataset-đã-chốt" style="color:#1f6feb;">3. Dataset đã chốt</a>
- <a href="#4-hướng-phân-tích-đã-thống-nhất" style="color:#1f6feb;">4. Hướng phân tích đã thống nhất</a>
  - <a href="#41-runtime-contract" style="color:#1f6feb;">4.1. Runtime contract</a>
- <a href="#5-workflow-tổng-quát" style="color:#1f6feb;">5. Workflow tổng quát</a>
- <a href="#6-cấu-trúc-canonical-hiện-tại" style="color:#1f6feb;">6. Cấu trúc canonical hiện tại</a>
- <a href="#7-rule-routing" style="color:#1f6feb;">7. Rule routing</a>
- <a href="#8-kết-quả-đã-hoàn-thành" style="color:#1f6feb;">8. Kết quả đã hoàn thành</a>
- <a href="#9-trạng-thái-hiện-tại" style="color:#1f6feb;">9. Trạng thái hiện tại</a>
- <a href="#10-phạm-vi-hoàn-thành" style="color:#1f6feb;">10. Phạm vi hoàn thành</a>

## 1. Mục tiêu

Practice 1 là bài thực hành khám phá và chẩn đoán dữ liệu chuỗi thời gian dựa trên nội dung Chương 2.

Mục tiêu cuối cùng là đánh giá chuỗi có cấu trúc thời gian và chất lượng dữ liệu phù hợp để tiếp tục sang bài toán forecasting hay không.

Practice 1 không huấn luyện forecasting model.

### 1.1. Truy cập nhanh

- <a href="notebooks/practice_1_present.ipynb" style="color:#1f6feb;">Notebook chính</a>
- <a href="datasets/raw/air_passengers.csv" style="color:#1f6feb;">Dữ liệu AirPassengers bản raw</a>
- <a href="datasets/README.md" style="color:#1f6feb;">Nguồn dữ liệu, schema và checksum</a>
- <a href="docs/status/current_status.md" style="color:#1f6feb;">Trạng thái hiện tại của Practice 1</a>
- <a href="src/practice_1/" style="color:#1f6feb;">Source code</a>
- <a href="tests/" style="color:#1f6feb;">Tests</a>
- <a href="outputs/figures/" style="color:#1f6feb;">Toàn bộ biểu đồ</a>
- <a href="outputs/results/" style="color:#1f6feb;">Toàn bộ kết quả dạng bảng</a>

## 2. Phạm vi bài thực hành

Practice 1 gồm sáu phần:

1. Tính và phân tích ACF/PACF.
2. Kiểm tra white noise.
3. Phân rã chuỗi thời gian.
4. Kiểm tra và xử lý chất lượng dữ liệu.
5. Trực quan hóa dữ liệu chuỗi thời gian.
6. Viết báo cáo và đánh giá forecastability.

Repository không tạo exercise specification hoặc before-process plan riêng cho Exercise 6; implementation chỉ
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

Dataset chính được xác nhận cho Practice 1 là `AirPassengers`.

Nguồn canonical:

- CSV: <a href="https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv" style="color:#1f6feb;">Rdatasets — AirPassengers.csv</a>
- Documentation: <a href="https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html" style="color:#1f6feb;">R `datasets::AirPassengers`</a>
- File được sử dụng trong bài: <a href="datasets/raw/air_passengers.csv" style="color:#1f6feb;">`datasets/raw/air_passengers.csv`</a>
- Provenance, schema và checksum: <a href="datasets/README.md" style="color:#1f6feb;">`datasets/README.md`</a>
- Số quan sát: 144.
- Khoảng thời gian: 1949-01 đến 1960-12.
- Tần suất: hằng tháng.
- Đơn vị: nghìn hành khách hàng không quốc tế.

Không dùng URL có query parameter `?utm_source`. CSV tải về được giữ nguyên trong
`datasets/raw/`; checksum SHA-256 và ngày tải chỉ được ghi sau actual acquisition.

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

Raw dataset đã được thêm tại `datasets/raw/air_passengers.csv` và được xác minh bằng
actual execution. Chi tiết provenance và integrity nằm trong `datasets/README.md` và
`docs/logs/exercise_01_execution.md`.

## 4. Hướng phân tích đã thống nhất

- ACF/PACF được dùng để nhận diện temporal structure, không tự động suy ra ARIMA order từ raw series.
- White noise được sinh từ `Normal(0, 1)` với 1000 observations và seed 42; ACF dùng
  maximum lag 40 và confidence level 95%.
- Ljung-Box là supplementary diagnostic, không thay thế yêu cầu ACF của đề bài.
- Decomposition sử dụng log transform và STL với seasonal period phù hợp dữ liệu tháng.
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
mutation hoặc absolute path. Environment, dependencies và notebook kernel đã được
khởi tạo theo confirmation Nhóm 4.

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
→ Hand validated evidence to báo cáo for the Word report outside the repository
```

## 6. Cấu trúc canonical hiện tại

```text
Practice_1/
├── .gitignore
├── README.md
├── pyproject.toml
├── config/
├── datasets/
│   ├── README.md
│   ├── raw/
│   └── processed/
├── docs/
│   ├── rules/
│   ├── exercise_details/
│   ├── plans/
│   ├── error_analysis/
│   ├── fix_plans/
│   ├── status/
│   └── logs/
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

Khi có bug hoặc scientific issue không trivial:

```text
error_analysis/ = phân tích lỗi và root cause
fix_plans/      = kế hoạch sửa chờ Đã xác nhận
logs/           = bằng chứng thực thi và validation sau khi sửa
```

## 7. Rule routing

Nguồn bắt buộc:

1. <a href="../../.agents/RULES_INDEX.md" style="color:#1f6feb;">`.agents/RULES_INDEX.md`</a>
2. <a href="docs/rules/architecture_rule.md" style="color:#1f6feb;">`docs/rules/architecture_rule.md`</a>
3. <a href="docs/rules/rule_code.md" style="color:#1f6feb;">`docs/rules/rule_code.md`</a>
4. Exercise detail đã được xác nhận.
5. Before-process plan đã được xác nhận.

Rule precedence tuân theo `.agents/RULES_INDEX.md`.

Nếu có conflict giữa các rule, phải dừng và chờ xử lý xung đột.

## 8. Kết quả đã hoàn thành

Notebook tổng hợp toàn bộ bài làm E1–E5 tại
<a href="notebooks/practice_1_present.ipynb" style="color:#1f6feb;">`notebooks/practice_1_present.ipynb`</a>.

| Exercise | Biểu đồ | Kết quả số liệu | Bằng chứng thực thi |
|---|---|---|---|
| **E1 — ACF/PACF** | <a href="outputs/figures/01_time_series_overview.png" style="color:#1f6feb;">Chuỗi gốc</a>, <a href="outputs/figures/02_acf_40_lags.png" style="color:#1f6feb;">ACF 40 lag</a>, <a href="outputs/figures/03_pacf_40_lags.png" style="color:#1f6feb;">PACF 40 lag</a> | <a href="outputs/results/acf_values.csv" style="color:#1f6feb;">ACF CSV</a>, <a href="outputs/results/pacf_values.csv" style="color:#1f6feb;">PACF CSV</a>, <a href="outputs/results/exercise_01_findings.json" style="color:#1f6feb;">Findings JSON</a> | <a href="docs/logs/exercise_01_execution.md" style="color:#1f6feb;">Exercise 1 execution log</a> |
| **E2 — White noise** | <a href="outputs/figures/04_white_noise_series.png" style="color:#1f6feb;">Chuỗi white noise</a>, <a href="outputs/figures/05_white_noise_acf.png" style="color:#1f6feb;">White-noise ACF</a>, <a href="outputs/figures/06_white_noise_vs_airpassengers_acf.png" style="color:#1f6feb;">So sánh ACF</a> | <a href="outputs/results/white_noise_acf_values.csv" style="color:#1f6feb;">White-noise ACF CSV</a> | <a href="docs/logs/exercise_02_execution.md" style="color:#1f6feb;">Exercise 2 execution log</a> |
| **E3 — Decomposition** | <a href="outputs/figures/07_log_transformed_series.png" style="color:#1f6feb;">Chuỗi log</a>, <a href="outputs/figures/08_stl_decomposition.png" style="color:#1f6feb;">STL decomposition</a>, <a href="outputs/figures/09_decomposition_residual.png" style="color:#1f6feb;">Residual diagnostics</a> | <a href="outputs/results/decomposition_components.csv" style="color:#1f6feb;">Decomposition components</a>, <a href="outputs/results/residual_diagnostics.csv" style="color:#1f6feb;">Residual diagnostics</a> | <a href="docs/logs/exercise_03_execution.md" style="color:#1f6feb;">Exercise 3 execution log</a> |
| **E4 — Data quality** | <a href="outputs/figures/10_missing_values_simulation.png" style="color:#1f6feb;">Missing simulation</a>, <a href="outputs/figures/11_missing_treatment_comparison.png" style="color:#1f6feb;">So sánh xử lý missing</a>, <a href="outputs/figures/12_outlier_analysis.png" style="color:#1f6feb;">Outlier analysis</a> | <a href="outputs/results/missing_value_comparison.csv" style="color:#1f6feb;">Missing-value comparison</a>, <a href="outputs/results/outlier_candidates.csv" style="color:#1f6feb;">Outlier candidates</a> | <a href="docs/logs/exercise_04_execution.md" style="color:#1f6feb;">Exercise 4 execution log</a> |
| **E5 — Visualization** | <a href="outputs/figures/13_full_time_series.png" style="color:#1f6feb;">Toàn bộ chuỗi</a>, <a href="outputs/figures/14_rolling_mean_std.png" style="color:#1f6feb;">Rolling mean/std</a>, <a href="outputs/figures/15_monthly_seasonal_plot.png" style="color:#1f6feb;">Seasonal plot</a>, <a href="outputs/figures/16_month_year_heatmap.png" style="color:#1f6feb;">Heatmap</a> | <a href="outputs/results/rolling_statistics.csv" style="color:#1f6feb;">Rolling statistics</a> | <a href="docs/logs/exercise_05_execution.md" style="color:#1f6feb;">Exercise 5 execution log</a> |

Các tài liệu giải thích yêu cầu và quyết định triển khai nằm trong
<a href="docs/exercise_details/" style="color:#1f6feb;">`docs/exercise_details/`</a>. Phân tích lỗi, kế hoạch sửa và log
kiểm chứng được lưu lần lượt tại <a href="docs/error_analysis/" style="color:#1f6feb;">`docs/error_analysis/`</a>,
<a href="docs/fix_plans/" style="color:#1f6feb;">`docs/fix_plans/`</a> và <a href="docs/logs/" style="color:#1f6feb;">`docs/logs/`</a>.

## 9. Trạng thái hiện tại

```text
Repository governance: active
Practice architecture/code rules: confirmed and active
Exercise 1–5: completed and validated
Exercise 6: Word report outside the repository
Primary notebook: notebooks/practice_1_present.ipynb
Notebook execution: 32 code cells, 0 errors
Tests: 31 passed
Dataset: AirPassengers added and integrity-verified
Outputs: Exercise 1–5 figures and machine-readable results generated and validated
```

Practice 1 đã hoàn thành phần kỹ thuật của E1–E5. Notebook, source code, tests,
biểu đồ và kết quả dạng bảng đã được chạy và kiểm chứng. E6 không nằm trong phạm vi
triển khai của repository; Báo cáo Word sử dụng các bằng chứng E1–E5 đã kiểm chứng.

## 10. Phạm vi hoàn thành

- E1–E5 đã được xác nhận, triển khai, chạy notebook và kiểm thử.
- Raw dataset được giữ bất biến; missing-value simulation chỉ thao tác trên working copy.
- Repository không huấn luyện forecasting model trong Practice 1.
- E6 là báo cáo Word được xây dựng từ các kết quả đã kiểm chứng của E1–E5.
- Mọi thay đổi kỹ thuật mới ngoài phạm vi trên vẫn phải tuân theo confirmation workflow của project.
