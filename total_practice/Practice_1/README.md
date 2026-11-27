# Practice 1 — Time-Series Diagnostics

Practice 1 là bài thực hành khám phá và chẩn đoán chuỗi thời gian theo nội dung
Chương 2. Mục tiêu là đánh giá temporal structure, seasonality và data quality
trước khi chuyển sang bài toán forecasting. Practice 1 không huấn luyện mô hình
dự báo.

<p>
<a href="docs/results/README.md" style="color:#1f6feb; font-weight:600;">🔗 Mở Dashboard kết quả</a>
&nbsp; · &nbsp;
<a href="notebooks/practice_1_present.ipynb" style="color:#1f6feb; font-weight:600;">🔗 Mở Notebook chính</a>
&nbsp; · &nbsp;
<a href="docs/plans/practice_1_overview.md" style="color:#1f6feb; font-weight:600;">🔗 Project Overview</a>
&nbsp; · &nbsp;
<a href="docs/status/current_status.md" style="color:#1f6feb; font-weight:600;">🔗 Current Status</a>
</p>

## Mục lục

1. [Mục tiêu](#1-mục-tiêu)
2. [Dataset và provenance](#2-dataset-và-provenance)
3. [Notebook và môi trường](#3-notebook-và-môi-trường)
4. [Workflow theo Exercise](#4-workflow-theo-exercise)
5. [Protocol chính](#5-protocol-chính)
6. [Kết quả chính](#6-kết-quả-chính)
7. [Dashboard kết quả](#7-dashboard-kết-quả)
8. [Cấu trúc thư mục](#8-cấu-trúc-thư-mục)
9. [Phạm vi và giới hạn](#9-phạm-vi-và-giới-hạn)
10. [Trạng thái và kiểm tra](#10-trạng-thái-và-kiểm-tra)

## 1. Mục tiêu

- Phân tích ACF/PACF.
- Kiểm tra white noise.
- Phân rã chuỗi thời gian.
- Kiểm tra missing values và outlier candidates.
- Trực quan hóa trend, rolling statistics và seasonality.
- Chuẩn bị validated evidence cho báo cáo forecastability ở E6.

## 2. Dataset và provenance

Dataset chính là `AirPassengers`.

| Thuộc tính | Giá trị |
|---|---|
| Số quan sát | 144 |
| Khoảng thời gian | 1949-01 đến 1960-12 |
| Tần suất | Hằng tháng |
| Đơn vị | Nghìn hành khách hàng không quốc tế |

- <a href="https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv" style="color:#1f6feb;">Nguồn CSV Rdatasets</a>
- <a href="https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html" style="color:#1f6feb;">Tài liệu R `datasets::AirPassengers`</a>
- <a href="datasets/raw/air_passengers.csv" style="color:#1f6feb;">Raw dataset trong repository</a>
- <a href="datasets/README.md" style="color:#1f6feb;">Provenance, schema và checksum</a>

Raw dataset được giữ bất biến. Các thí nghiệm missing values chỉ thao tác trên
working copy. License của underlying AirPassengers được giữ ở mức provenance đã
được xác minh, không gán GPL-3 trực tiếp cho dữ liệu.

## 3. Notebook và môi trường

- <a href="notebooks/practice_1_present.ipynb" style="color:#1f6feb; font-weight:600;">Mở notebook chính</a>
- Kernel: `time-series-practice-1`.
- Python: `3.12`.
- Package path: `src/practice_1/`.
- Notebook và tests import package qua `practice_1.*`, không dùng `sys.path` mutation hoặc absolute path.
- Dependency và package metadata nằm trong `pyproject.toml`.

## 4. Workflow theo Exercise

```text
E1 — ACF/PACF
  ↓
E2 — White noise
  ↓
E3 — STL decomposition
  ↓
E4 — Data quality, missing values và outlier candidates
  ↓
E5 — Visualization và rolling statistics
  ↓
E6 — Báo cáo forecastability ngoài repository
```

E1–E5 được triển khai và kiểm chứng trong notebook chính. E6 sử dụng evidence
đã xác nhận để viết báo cáo Word bên ngoài repository; không tạo forecasting
model trong Practice 1.

## 5. Protocol chính

- ACF/PACF dùng để nhận diện temporal structure, không tự động suy ra ARIMA order.
- White noise được sinh từ `Normal(0, 1)` với 1000 observations, seed `42`, maximum lag `40` và confidence level `95%`.
- Ljung–Box chỉ là supplementary diagnostic.
- Decomposition dùng log transform và STL với seasonal period phù hợp chuỗi tháng.
- Missing values được tạo trên working copy; forward-fill và time interpolation được so sánh trên cùng vị trí mask.
- Outlier được đánh dấu để phân tích, không tự động xóa hoặc thay thế.
- Outlier detection ưu tiên thực hiện trên decomposition residual khi chuỗi có trend và seasonality.
- Rolling statistics dùng trailing window `12`, `min_periods=12`, `center=False`, và standard deviation với `ddof=1`.

## 6. Kết quả chính

Notebook tổng hợp toàn bộ E1–E5 tại
<a href="notebooks/practice_1_present.ipynb" style="color:#1f6feb;">`notebooks/practice_1_present.ipynb`</a>.

| Exercise | Nội dung | Artifact chính | Execution evidence |
|---|---|---|---|
| **E1** | ACF/PACF | <a href="outputs/results/acf_values.csv" style="color:#1f6feb;">ACF</a>, <a href="outputs/results/pacf_values.csv" style="color:#1f6feb;">PACF</a>, <a href="outputs/results/exercise_01_findings.json" style="color:#1f6feb;">Findings</a> | <a href="docs/logs/exercise_01_execution.md" style="color:#1f6feb;">Log E1</a> |
| **E2** | White noise | <a href="outputs/results/white_noise_acf_values.csv" style="color:#1f6feb;">White-noise ACF</a> | <a href="docs/logs/exercise_02_execution.md" style="color:#1f6feb;">Log E2</a> |
| **E3** | STL decomposition | <a href="outputs/results/decomposition_components.csv" style="color:#1f6feb;">Components</a>, <a href="outputs/results/residual_diagnostics.csv" style="color:#1f6feb;">Residual diagnostics</a> | <a href="docs/logs/exercise_03_execution.md" style="color:#1f6feb;">Log E3</a> |
| **E4** | Data quality | <a href="outputs/results/missing_value_comparison.csv" style="color:#1f6feb;">Missing comparison</a>, <a href="outputs/results/outlier_candidates.csv" style="color:#1f6feb;">Outlier candidates</a> | <a href="docs/logs/exercise_04_execution.md" style="color:#1f6feb;">Log E4</a> |
| **E5** | Visualization | <a href="outputs/results/rolling_statistics.csv" style="color:#1f6feb;">Rolling statistics</a> | <a href="docs/logs/exercise_05_execution.md" style="color:#1f6feb;">Log E5</a> |

Các figures tương ứng nằm trong
<a href="outputs/figures/" style="color:#1f6feb;">`outputs/figures/`</a>.

### Kết quả từng Exercise

- <a href="docs/results/exercise_01_acf_pacf.md" style="color:#1f6feb;">E1 — ACF/PACF</a>
- <a href="docs/results/exercise_02_white_noise.md" style="color:#1f6feb;">E2 — White noise</a>
- <a href="docs/results/exercise_03_decomposition.md" style="color:#1f6feb;">E3 — STL decomposition</a>
- <a href="docs/results/exercise_04_data_quality.md" style="color:#1f6feb;">E4 — Data quality</a>
- <a href="docs/results/exercise_05_visualization.md" style="color:#1f6feb;">E5 — Visualization</a>

## 7. Dashboard kết quả

Mở <a href="docs/results/README.md" style="color:#1f6feb; font-weight:600;">Dashboard kết quả E1–E5</a> để đi tới từng trang
diễn giải, figure, CSV/JSON, source code và execution log. Dashboard chỉ điều
hướng tới artifact đã có, không thay đổi kết quả notebook.

## 8. Cấu trúc thư mục

```text
Practice_1/
├── config/
├── datasets/raw/             # raw AirPassengers bất biến
├── docs/
│   ├── exercise_details/
│   ├── plans/
│   ├── error_analysis/
│   ├── fix_plans/
│   ├── logs/
│   ├── results/              # dashboard và diễn giải E1–E5
│   ├── rules/
│   └── status/
├── notebooks/practice_1_present.ipynb
├── outputs/
│   ├── figures/
│   └── results/
├── src/practice_1/
├── tests/
└── pyproject.toml
```

Tài liệu rule chính gồm
<a href="docs/rules/architecture_rule.md" style="color:#1f6feb;">architecture rule</a> và
<a href="docs/rules/rule_code.md" style="color:#1f6feb;">code rule</a>.

## 9. Phạm vi và giới hạn

Practice 1 không bao gồm ARIMA/SARIMA fitting, Machine Learning, Deep Learning,
train/validation/test modeling protocol, hyperparameter tuning hoặc model
backtesting. E6 là báo cáo Word ngoài repository, được xây dựng từ evidence E1–E5.

## 10. Trạng thái và kiểm tra

- E1–E5: completed và validated.
- Notebook chính: `notebooks/practice_1_present.ipynb`.
- Notebook execution: 32 code cells, 0 errors.
- Tests: 31 passed.
- Dataset AirPassengers: integrity verified.
- Figures và machine-readable results: đã tạo và kiểm chứng.

Trước khi thay đổi implementation, cần đối chiếu
<a href="../../.agents/RULES_INDEX.md" style="color:#1f6feb;">`.agents/RULES_INDEX.md`</a>, exercise details và before-process plans.
