# Practice 2 — ADF and ARIMA/SARIMA

Practice 2 thực hành kiểm định tính dừng, transformation, ACF/PACF, ARIMA và
mở rộng SARIMA trên dữ liệu chuỗi thời gian monthly. Notebook core là
`notebooks/Practice_2_Exercise.ipynb`; notebook nâng cao là
`notebooks/Practice_2_Advanced.ipynb`.

<p>
<a href="docs/results/README.md" style="color:#1f6feb; font-weight:600;">🔗 Mở Dashboard kết quả</a>
&nbsp; · &nbsp;
<a href="notebooks/Practice_2_Exercise.ipynb" style="color:#1f6feb; font-weight:600;">🔗 Mở Notebook chính</a>
&nbsp; · &nbsp;
<a href="docs/plans/project_overview.md" style="color:#1f6feb; font-weight:600;">🔗 Project Overview</a>
&nbsp; · &nbsp;
<a href="docs/status/current_status.md" style="color:#1f6feb; font-weight:600;">🔗 Current Status</a>
</p>

## Mục lục

1. [Mục tiêu](#1-mục-tiêu)
2. [Dataset và integrity](#2-dataset-và-integrity)
3. [Notebook và môi trường](#3-notebook-và-môi-trường)
4. [Workflow theo Exercise](#4-workflow-theo-exercise)
5. [Protocol chính](#5-protocol-chính)
6. [Kết quả chính](#6-kết-quả-chính)
7. [Dashboard và output](#7-dashboard-và-output)
8. [Cấu trúc thư mục](#8-cấu-trúc-thư-mục)
9. [Giới hạn hiện tại](#9-giới-hạn-hiện-tại)
10. [Kiểm tra trước khi merge](#10-kiểm-tra-trước-khi-merge)

## 1. Mục tiêu

- Nhận diện chuỗi dừng và không dừng bằng ADF.
- Xác định transformation và regular differencing order `d`.
- Dùng ACF/PACF để đề xuất ARIMA candidates.
- Fit model, kiểm tra residual và Ljung–Box.
- Forecast trên chronological holdout và đánh giá bằng MAE, RMSE, MAPE.
- Khảo sát SARIMA trên AirPassengers ở E06.

## 2. Dataset và integrity

| Dataset | File | Scope |
|---|---|---|
| Monthly Retail Sales | `datasets/raw/a10.csv` | E01–E05 |
| AirPassengers | `datasets/raw/airline-passengers.csv` | E06 |

Các file trong `datasets/raw/` là source of truth và không được chỉnh sửa.
Transformation, differencing, train/test split và forecast được tạo trên working
objects trong memory. `datasets/processed/` hiện không chứa processed dataset.

## 3. Notebook và môi trường

### Notebook chính

- <a href="notebooks/Practice_2_Exercise.ipynb" style="color:#1f6feb; font-weight:600;">Mở notebook core E01–E05</a>
- <a href="notebooks/Practice_2_Advanced.ipynb" style="color:#1f6feb;">Mở notebook Advanced E06</a>

Notebook Advanced là exploratory extension độc lập; không thay thế trạng thái
của core practice.

### Cách chạy

Khuyến nghị chọn kernel `practice2-timeseries` từ project root.

```bash
cd "/Users/vientu/Time Series/TOTAL_LAB_PRACTICE_FOR_TIME_SERIES/total_practice/Practice_2"

PRACTICE_2_RUN_ID="YYYY-MM-DD_core_protocol" \
"/Users/vientu/Time Series/TOTAL_LAB_PRACTICE_FOR_TIME_SERIES/Presentation-24.10.2026/.venv/bin/jupyter" \
nbconvert \
--to notebook \
--execute \
--stdout \
--ExecutePreprocessor.kernel_name=practice2-timeseries \
--ExecutePreprocessor.timeout=1800 \
notebooks/Practice_2_Exercise.ipynb \
> /private/tmp/Practice_2_Exercise_run.ipynb
```

Raw runtime log của mỗi run nằm tại `runs/<RUN_ID>/Practice_2_Exercise.log`.

## 4. Workflow theo Exercise

```text
E01 — EDA và chuẩn bị chuỗi
  ↓
E02 — ADF trên original training series
  ↓
E03 — Log transformation, differencing và ADF retest
  ↓
E04 — ACF/PACF và provisional candidates
  ↓
E05 — ARIMA/SARIMA fitting, diagnostics và 41-month evaluation
  ↓
E06 — AirPassengers SARIMA exploratory extension
```

E01–E05 dùng Monthly Retail Sales. E06 là extension độc lập trên AirPassengers.

## 5. Protocol chính

- Chronological boundary: `163` train observations và `41` test observations.
- Test set được sealed cho đến E05.
- E02 chạy ADF trên original training series.
- E03 dùng natural-log first difference và kết luận chính thức `d=1`.
- E04 tính ACF/PACF trên log-first-difference training series.
- E05 fit hai ARIMA candidates trên log training levels với `d=1`.
- E05 forecast đúng 41 tháng, inverse-log về original sales scale.
- Seasonal-naive baseline có seasonal period `12` được dùng để tham chiếu.
- Residual ACF và Ljung–Box phải được xem xét trước khi claim white noise.

## 6. Kết quả chính

Kết luận và artifact được trình bày theo từng exercise trong
<a href="docs/results/README.md" style="color:#1f6feb; font-weight:600;">Dashboard kết quả</a>.

- E01: completed và validated.
- E02: train-only evidence validated.
- E03: natural-log first difference, `d=1`, evidence validated.
- E04: ACF/PACF và candidates đã được xác nhận.
- E05: fitting, 41-month forecast, baseline và residual diagnostics đã được kiểm tra; residual autocorrelation là limitation cần ghi nhận.
- E06: đã xác nhận phạm vi SARIMA exploratory; validation và execution evidence chưa hoàn tất.

### Kết quả từng Exercise

- <a href="docs/results/exercise_01.md" style="color:#1f6feb;">E01 — EDA và chuẩn bị chuỗi</a>
- <a href="docs/results/exercise_02.md" style="color:#1f6feb;">E02 — ADF trên training series</a>
- <a href="docs/results/exercise_03.md" style="color:#1f6feb;">E03 — Transformation và differencing</a>
- <a href="docs/results/exercise_04.md" style="color:#1f6feb;">E04 — ACF/PACF</a>
- <a href="docs/results/exercise_05.md" style="color:#1f6feb;">E05 — ARIMA và forecast 41 tháng</a>
- <a href="docs/results/exercise_06.md" style="color:#1f6feb;">E06 — SARIMA extension</a>

## 7. Dashboard và output

<a href="docs/results/README.md" style="color:#1f6feb; font-weight:600;">🔗 Mở Dashboard Practice 2</a>

Dashboard liên kết tới kết luận, hình, model summary, execution evidence và raw
run log tương ứng của từng exercise.

Notebook dùng `pandas Styler` để hiển thị bảng có màu: màu xanh cho
baseline/reference hoặc trạng thái đạt; màu vàng cho candidate cần review hoặc
reconciliation. Artifact legacy được tách trong `outputs/legacy/`.

Execution evidence dạng Markdown nằm trong `docs/logs/`; raw runtime log nằm
trong `runs/` và không thay thế execution evidence đã diễn giải.

## 8. Cấu trúc thư mục

```text
Practice_2/
├── config/
├── datasets/raw/              # raw data bất biến
├── datasets/processed/        # không có processed dataset hiện tại
├── docs/
│   ├── exercise_details/
│   ├── plans/
│   ├── logs/
│   ├── results/               # dashboard và diễn giải E01–E06
│   ├── rules/
│   └── status/
├── runs/                      # raw runtime logs theo run ID
├── notebooks/
├── outputs/
│   ├── figures/
│   ├── legacy/
│   └── results/
├── src/practice_2/
├── tests/
└── pyproject.toml
```

## 9. Giới hạn hiện tại

E04/E05 đã completed và được xác nhận bằng clean-kernel run. Residual
Ljung–Box vẫn cho thấy autocorrelation, vì vậy không được kết luận residual là
white noise. E06 là exploratory extension, không thay thế core E01–E05.

## 10. Kiểm tra trước khi merge

```bash
cd "/Users/vientu/Time Series/TOTAL_LAB_PRACTICE_FOR_TIME_SERIES/total_practice/Practice_2"
PYTHONPATH=src .venv/bin/pytest -q
.venv/bin/jupyter nbconvert --to script --stdout notebooks/Practice_2_Exercise.ipynb > /private/tmp/Practice_2_Exercise.py
.venv/bin/python -m py_compile /private/tmp/Practice_2_Exercise.py
git diff --check
```

Các kiểm tra bao phủ data loading, stationarity, ACF/PACF, forecasting,
forecast-index alignment, table styling và project-root portability. Trước khi
merge cần xác nhận test không bị dùng trong E02–E04, E05 có đúng 41 forecast
observations, baseline/residual diagnostics được báo cáo và log–outputs–status
cùng phản ánh một run.
