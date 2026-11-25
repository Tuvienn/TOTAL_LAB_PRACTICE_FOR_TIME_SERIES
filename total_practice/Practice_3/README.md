# Practice 3 — Time-Series Forecasting với Machine Learning

Practice 3 xây dựng workflow dự báo điện năng theo giờ từ dữ liệu AEP, từ định
nghĩa bài toán đến chuẩn bị dữ liệu, EDA, feature engineering, model selection,
forecasting, phân tích lỗi và kết luận. Nội dung hiện tại là implementation chính thức;
namespace Python `practice_3` được giữ để bảo toàn import và test đã kiểm chứng.

<p>
<a href="docs/results/README.md" style="color:#1f6feb; font-weight:600;">🔗 Mở Dashboard kết quả</a>
&nbsp; · &nbsp;
<a href="notebooks/Practice_3_present.ipynb" style="color:#1f6feb; font-weight:600;">🔗 Mở Notebook chính</a>
&nbsp; · &nbsp;
<a href="docs/plans/PROJECT_OVERVIEW.md" style="color:#1f6feb; font-weight:600;">🔗 Project Overview</a>
&nbsp; · &nbsp;
<a href="docs/status/current_status.md" style="color:#1f6feb; font-weight:600;">🔗 Current Status</a>
</p>

## Mục lục

1. [Mục tiêu và protocol](#mục-tiêu-và-protocol)
2. [Dataset và provenance](#dataset-và-provenance)
3. [Workflow theo Phase](#workflow-theo-phase)
4. [Kết quả chính](#kết-quả-chính)
5. [Kết quả từng Phase](#kết-quả-từng-phase)
6. [Notebook và môi trường](#notebook-và-môi-trường)
7. [Cấu trúc thư mục](#cấu-trúc-thư-mục)
8. [Giới hạn khoa học](#giới-hạn-khoa-học)
9. [Trạng thái và kiểm tra](#trạng-thái-và-kiểm-tra)

## Mục tiêu và protocol

- Target: `AEP_MW`.
- Primary protocol: one-step hourly forecasting.
- Secondary protocol: recursive 24-hour forecasting.
- Validation: expanding-window, 5 folds, không shuffle.
- Historical holdout chỉ là historical re-evaluation, không tuyên bố truly unseen.
- Model selection chỉ dùng development period; holdout chỉ mở ở Phase 7.

## Dataset và provenance

Dataset canonical là AEP Hourly Energy Consumption:

- Raw: `datasets/raw/AEP_hourly.csv`.
- Processed: `datasets/processed/aep_hourly_prepared.csv`.
- Prepared rows: `121,296`.
- Missing targets được giữ lại: `27`; không imputation target.
- Raw SHA-256 và processed SHA-256 được ghi trong
  <a href="docs/status/current_status.md" style="color:#1f6feb;">current_status.md</a>
  và Phase 1 data-quality audit.

Raw data không bị chỉnh sửa trong notebook. Chi tiết structural preparation nằm
ở <a href="docs/results/phase_01_data_preparation.md" style="color:#1f6feb;">kết quả Phase 1</a>.

## Workflow theo Phase

```text
Phase 0 — Problem Definition
  ↓
Phase 1 — Structural Data Preparation
  ↓
Phase 2 — Temporal Split và Validation
  ↓
Phase 3 — TRAIN-only EDA
  ↓
Phase 4 — Leakage-safe Feature Engineering
  ↓
Phase 5 — X/y Construction
  ↓
Phase 6 — Model Selection và Model Lock
  ↓
Phase 7 — Final Forecasting và Evaluation
  ↓
Phase 8 — Error và Interpretation
  ↓
Phase 9 — Final Conclusion và Handoff
```

Protocol và acceptance criteria chi tiết nằm trong
<a href="docs/phase_details/" style="color:#1f6feb;">docs/phase_details/</a>.

## Kết quả chính

Model được khóa là `xgboost_tuned` với `22` features.

| Protocol | MAE (MW) | RMSE (MW) | Population |
|---|---:|---:|---:|
| One-step historical holdout | 102,841 | 137,929 | 8,592 timestamps |
| Recursive 24-hour pooled | 509,652 | 720,451 | 357 origins / 8,568 predictions |

Tuned XGBoost có mean CV MAE thấp hơn Linear Regression khoảng **20,85%** trên
cùng `42.413` development validation samples. Đây là development-only comparison,
không phải holdout comparison.

Lag-only error giảm mạnh đến `p=24`, cải thiện tại `p=48` rồi tăng lại tại
`p=168`; đây là supplemental evidence và không thay official feature schema.

## Kết quả từng Phase

Dashboard chỉ là mục lục; mỗi Phase có một trang kết quả riêng với notebook,
source code, tests, result JSON/CSV, figures và execution evidence:

- <a href="docs/results/phase_00_problem_definition.md" style="color:#1f6feb;">Phase 0 — Problem Definition</a>
- <a href="docs/results/phase_01_data_preparation.md" style="color:#1f6feb;">Phase 1 — Data Preparation</a>
- <a href="docs/results/phase_02_temporal_split.md" style="color:#1f6feb;">Phase 2 — Temporal Split</a>
- <a href="docs/results/phase_03_eda.md" style="color:#1f6feb;">Phase 3 — TRAIN-only EDA</a>
- <a href="docs/results/phase_04_feature_engineering.md" style="color:#1f6feb;">Phase 4 — Feature Engineering</a>
- <a href="docs/results/phase_05_supervised_dataset.md" style="color:#1f6feb;">Phase 5 — X/y Construction</a>
- <a href="docs/results/phase_06_model_selection.md" style="color:#1f6feb;">Phase 6 — Model Selection</a>
- <a href="docs/results/phase_07_evaluation.md" style="color:#1f6feb;">Phase 7 — Evaluation</a>
- <a href="docs/results/phase_08_error_interpretation.md" style="color:#1f6feb;">Phase 8 — Error Interpretation</a>
- <a href="docs/results/phase_09_final_conclusion.md" style="color:#1f6feb;">Phase 9 — Final Conclusion</a>

## Notebook và môi trường

Notebook chính là
<a href="notebooks/Practice_3_present.ipynb" style="color:#1f6feb;">`notebooks/Practice_3_present.ipynb`</a>.
Notebook chỉ trình bày official artifacts; pipeline và reusable logic nằm trong
`src/practice_3/`.

Trong VS Code:

1. Mở thư mục `total_practice/Practice_3`.
2. Chọn kernel **Practice 3 (Time Series)** hoặc kernelspec
   `practice3-timeseries`.
3. Mở `notebooks/Practice_3_present.ipynb` và chọn **Run All**.

Không cài package trong notebook. Dependency và package metadata nằm trong
<a href="pyproject.toml" style="color:#1f6feb;">pyproject.toml</a>; environment
local nằm ở `.venv/` và không được commit.

Kiểm tra bằng terminal:

```bash
cd "/Users/vientu/Time Series/TOTAL_LAB_PRACTICE_FOR_TIME_SERIES/total_practice/Practice_3"
.venv/bin/python -m practice_3.analysis.final_conclusion --preflight
.venv/bin/python -m pytest -q
```

## Cấu trúc thư mục

```text
Practice_3/
├── config/                 # contracts và configuration
├── datasets/               # raw bất biến và processed dataset
├── docs/
│   ├── phase_details/      # protocol từng Phase
│   ├── results/            # README dashboard + 10 trang kết quả
│   ├── logs/               # execution evidence Markdown
│   ├── plans/              # project overview và workflow
│   ├── rules/              # architecture/code/workflow rules
│   └── status/             # provenance và current status
├── notebooks/              # notebook trình bày chính
├── outputs/
│   ├── figures/            # official figures
│   └── results/            # JSON/CSV machine-readable artifacts
├── runs/                   # raw runtime log theo run ID nếu có
├── src/practice_3/      # data, analysis và visualization logic
├── tests/                  # regression và contract tests
└── pyproject.toml
```

## Giới hạn khoa học

- Historical holdout không phải truly unseen test set.
- Không có prediction interval hoặc uncertainty calibration.
- Recursive error tăng theo horizon; residual còn autocorrelation.
- Gain importance không phải causal importance.
- Supplemental experiments là post-hoc development-only evidence.
- Chưa có ARIMA benchmark, external validation hoặc production drift monitoring.
- Project không tuyên bố production readiness.

## Trạng thái và kiểm tra

Lần chạy notebook hiện tại:

- `27/27` code cells, không có execution error.
- `212/212` tests passed.
- `28/28` HTML table outputs có style light/dark.
- Local Markdown/HTML links: `0 missing`.
- Phase 0–9 official artifacts: `PASS`.

Chi tiết trạng thái và provenance nằm tại
<a href="docs/status/current_status.md" style="color:#1f6feb;">docs/status/current_status.md</a>.
Raw runtime log nếu có nằm trong `runs/`; execution evidence diễn giải nằm trong
<a href="docs/logs/" style="color:#1f6feb;">docs/logs/</a>.
