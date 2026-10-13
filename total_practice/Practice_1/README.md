<div align="center">
<h1>Time Series Practice 1</h1>
</div>


## Mục lục

- [1. Mục tiêu](#1-mục-tiêu)
  - [1.1. Truy cập nhanh](#11-truy-cập-nhanh)
- [2. Phạm vi bài thực hành](#2-phạm-vi-bài-thực-hành)
- [3. Dataset đã chốt](#3-dataset-đã-chốt)
- [4. Hướng phân tích đã thống nhất](#4-hướng-phân-tích-đã-thống-nhất)
  - [4.1. Runtime contract](#41-runtime-contract)
- [5. Workflow tổng quát](#5-workflow-tổng-quát)
- [6. Cấu trúc canonical hiện tại](#6-cấu-trúc-canonical-hiện-tại)
- [7. Rule routing](#7-rule-routing)
- [8. Kết quả đã hoàn thành](#8-kết-quả-đã-hoàn-thành)
- [9. Trạng thái hiện tại](#9-trạng-thái-hiện-tại)
- [10. Phạm vi hoàn thành](#10-phạm-vi-hoàn-thành)

## 1. Mục tiêu

Practice 1 là bài thực hành khám phá và chẩn đoán dữ liệu chuỗi thời gian dựa trên nội dung Chương 2.

Mục tiêu cuối cùng là đánh giá chuỗi có cấu trúc thời gian và chất lượng dữ liệu phù hợp để tiếp tục sang bài toán forecasting hay không.

Practice 1 không huấn luyện forecasting model.

### 1.1. Truy cập nhanh

- [Notebook chính](notebooks/practice_1_present.ipynb)
- [Dữ liệu AirPassengers bản raw](datasets/raw/air_passengers.csv)
- [Nguồn dữ liệu, schema và checksum](datasets/README.md)
- [Trạng thái hiện tại của Practice 1](docs/status/current_status.md)
- [Source code](src/practice_1/)
- [Tests](tests/)
- [Toàn bộ biểu đồ](outputs/figures/)
- [Toàn bộ kết quả dạng bảng](outputs/results/)

## 2. Phạm vi bài thực hành

Practice 1 gồm sáu phần:

1. Tính và phân tích ACF/PACF.
2. Kiểm tra white noise.
3. Phân rã chuỗi thời gian.
4. Kiểm tra và xử lý chất lượng dữ liệu.
5. Trực quan hóa dữ liệu chuỗi thời gian.
6. Viết báo cáo và đánh giá forecastability.

Repository không tạo exercise specification hoặc before-process plan riêng cho Exercise 6; AI implementation chỉ
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

- CSV: [Rdatasets — AirPassengers.csv](https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv)
- Documentation: [R `datasets::AirPassengers`](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html)
- File được sử dụng trong bài: [`datasets/raw/air_passengers.csv`](datasets/raw/air_passengers.csv)
- Provenance, schema và checksum: [`datasets/README.md`](datasets/README.md)
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
khởi tạo theo approval Nhóm 4.

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
fix_plans/      = kế hoạch sửa chờ Human phê duyệt
logs/           = bằng chứng thực thi và validation sau khi sửa
```

## 7. Rule routing

Nguồn bắt buộc:

1. [`.agents/RULES_INDEX.md`](../../.agents/RULES_INDEX.md)
2. [`docs/rules/architecture_rule.md`](docs/rules/architecture_rule.md)
3. [`docs/rules/rule_code.md`](docs/rules/rule_code.md)
4. Exercise detail đã được duyệt.
5. Before-process plan đã được duyệt.

Rule precedence tuân theo `.agents/RULES_INDEX.md`.

Nếu có conflict giữa các rule, phải dừng và chờ Human quyết định.

## 8. Kết quả đã hoàn thành

Notebook tổng hợp toàn bộ bài làm E1–E5 tại
[`notebooks/practice_1_present.ipynb`](notebooks/practice_1_present.ipynb).

| Exercise | Biểu đồ | Kết quả số liệu | Bằng chứng thực thi |
|---|---|---|---|
| **E1 — ACF/PACF** | [Chuỗi gốc](outputs/figures/01_time_series_overview.png), [ACF 40 lag](outputs/figures/02_acf_40_lags.png), [PACF 40 lag](outputs/figures/03_pacf_40_lags.png) | [ACF CSV](outputs/results/acf_values.csv), [PACF CSV](outputs/results/pacf_values.csv), [Findings JSON](outputs/results/exercise_01_findings.json) | [Exercise 1 execution log](docs/logs/exercise_01_execution.md) |
| **E2 — White noise** | [Chuỗi white noise](outputs/figures/04_white_noise_series.png), [White-noise ACF](outputs/figures/05_white_noise_acf.png), [So sánh ACF](outputs/figures/06_white_noise_vs_airpassengers_acf.png) | [White-noise ACF CSV](outputs/results/white_noise_acf_values.csv) | [Exercise 2 execution log](docs/logs/exercise_02_execution.md) |
| **E3 — Decomposition** | [Chuỗi log](outputs/figures/07_log_transformed_series.png), [STL decomposition](outputs/figures/08_stl_decomposition.png), [Residual diagnostics](outputs/figures/09_decomposition_residual.png) | [Decomposition components](outputs/results/decomposition_components.csv), [Residual diagnostics](outputs/results/residual_diagnostics.csv) | [Exercise 3 execution log](docs/logs/exercise_03_execution.md) |
| **E4 — Data quality** | [Missing simulation](outputs/figures/10_missing_values_simulation.png), [So sánh xử lý missing](outputs/figures/11_missing_treatment_comparison.png), [Outlier analysis](outputs/figures/12_outlier_analysis.png) | [Missing-value comparison](outputs/results/missing_value_comparison.csv), [Outlier candidates](outputs/results/outlier_candidates.csv) | [Exercise 4 execution log](docs/logs/exercise_04_execution.md) |
| **E5 — Visualization** | [Toàn bộ chuỗi](outputs/figures/13_full_time_series.png), [Rolling mean/std](outputs/figures/14_rolling_mean_std.png), [Seasonal plot](outputs/figures/15_monthly_seasonal_plot.png), [Heatmap](outputs/figures/16_month_year_heatmap.png) | [Rolling statistics](outputs/results/rolling_statistics.csv) | [Exercise 5 execution log](docs/logs/exercise_05_execution.md) |

Các tài liệu giải thích yêu cầu và quyết định triển khai nằm trong
[`docs/exercise_details/`](docs/exercise_details/). Phân tích lỗi, kế hoạch sửa và log
kiểm chứng được lưu lần lượt tại [`docs/error_analysis/`](docs/error_analysis/),
[`docs/fix_plans/`](docs/fix_plans/) và [`docs/logs/`](docs/logs/).

## 9. Trạng thái hiện tại

```text
Repository governance: active
Practice architecture/code rules: approved and active
Exercise 1–5: completed and validated
Exercise 6: user-owned Word report
Primary notebook: notebooks/practice_1_present.ipynb
Notebook execution: 32 code cells, 0 errors
Tests: 31 passed
Dataset: AirPassengers added and integrity-verified
Outputs: Exercise 1–5 figures and machine-readable results generated and validated
```

Practice 1 đã hoàn thành phần kỹ thuật của E1–E5. Notebook, source code, tests,
biểu đồ và kết quả dạng bảng đã được chạy và kiểm chứng. E6 không nằm trong phạm vi
triển khai của repository; TuVien sử dụng các bằng chứng E1–E5 để viết báo cáo Word.

## 10. Phạm vi hoàn thành

- E1–E5 đã được Human phê duyệt, triển khai, chạy notebook và kiểm thử.
- Raw dataset được giữ bất biến; missing-value simulation chỉ thao tác trên working copy.
- Repository không huấn luyện forecasting model trong Practice 1.
- E6 là báo cáo Word do TuVien thực hiện từ các kết quả đã kiểm chứng của E1–E5.
- Mọi thay đổi kỹ thuật mới ngoài phạm vi trên vẫn phải tuân theo approval workflow của project.
