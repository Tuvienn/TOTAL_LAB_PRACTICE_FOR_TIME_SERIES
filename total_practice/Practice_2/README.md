# Practice 2 — ADF and ARIMA/SARIMA

Practice 2 thực hành kiểm định tính dừng, sai phân, ACF/PACF, ARIMA và mở rộng
SARIMA trên dữ liệu chuỗi thời gian monthly. Notebook core là
`notebooks/Practice_2_Exercise.ipynb`; notebook nâng cao là
`notebooks/Practice_2_Advanced.ipynb`.

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
Transformation, differencing, train/test split và forecast được tạo trên các
working objects trong memory. `datasets/processed/` hiện không chứa processed
dataset nào.

## 3. Exercise flow

```text
E01 — EDA and time-series preparation
  ↓
E02 — ADF on original training series
  ↓
E03 — Log transformation, differencing and ADF retest
  ↓
E04 — ACF/PACF and provisional candidates
  ↓
E05 — ARIMA/SARIMA fitting, diagnostics and 41-month evaluation
  ↓
E06 — AirPassengers SARIMA exploratory extension
```

E01–E05 dùng Dataset 1. E06 là extension độc lập trên Dataset 2 và không thay
thế trạng thái của core practice.

## 4. Canonical protocol

E01 xác định chronological boundary `163` train observations và `41` test
observations. Test set được sealed cho đến E05.

- E02 chạy ADF trên original training series.
- E03 dùng natural-log first difference và kết luận chính thức `d=1`.
- E04 tính ACF/PACF trên log-first-difference training series.
- E05 fit hai ARIMA candidates trên log training levels với `d=1`.
- E05 forecast đúng 41 tháng, inverse-log về original sales scale và so sánh với
  seasonal-naive baseline có seasonal period `12`.
- Residual ACF và Ljung–Box phải được xem xét trước khi claim white noise.

## 5. Cấu trúc thư mục

```text
Practice_2/
├── config/                    # cấu hình ổn định
├── datasets/raw/              # raw data bất biến
├── datasets/processed/        # derived datasets nếu được phê duyệt
├── docs/
│   ├── exercise_details/      # exercise specifications
│   ├── plans/                 # before-process plans
│   ├── logs/                  # human-readable execution evidence
│   ├── status/                # current project status
│   └── rules/                 # scoped architecture/code rules
├── runs/                      # raw runtime logs theo từng run ID
├── notebooks/                 # canonical core và exploratory extension
├── outputs/
│   ├── figures/                # output chính thức của lần chạy mới
│   ├── legacy/                 # artifact legacy chỉ để truy vết
│   └── results/                # machine-readable summaries
├── src/practice_2/             # reusable analysis/data/visualization logic
├── tests/                     # tests cho reusable logic
└── pyproject.toml
```

## 6. Cách chạy notebook

Khuyến nghị chạy bằng kernel `practice2-timeseries` từ project root. `RUN_ID`
được dùng để tách raw runtime log khỏi các lần chạy khác nhau.

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

Log của run được ghi tại:

```text
runs/<RUN_ID>/Practice_2_Exercise.log
```

Notebook Advanced được chạy độc lập khi E06 được review; nó hiện chỉ là
exploratory draft.

## 7. Dashboard kết quả

Mở [dashboard kết quả](docs/results/README.md) để xem kết luận từng Exercise và
bấm tới execution evidence, hình, model summary và raw run log tương ứng.

## 8. Chạy tests và kiểm tra nhanh

```bash
cd "/Users/vientu/Time Series/TOTAL_LAB_PRACTICE_FOR_TIME_SERIES/total_practice/Practice_2"
PYTHONPATH=src .venv/bin/pytest -q
.venv/bin/jupyter nbconvert --to script --stdout notebooks/Practice_2_Exercise.ipynb > /private/tmp/Practice_2_Exercise.py
.venv/bin/python -m py_compile /private/tmp/Practice_2_Exercise.py
git diff --check
```

Các kiểm tra hiện tại bao phủ data loading, stationarity, ACF/PACF, forecasting,
forecast-index alignment, table styling và project-root portability.

## 9. Bảng và output

Notebook dùng `pandas Styler` để hiển thị bảng có màu, trạng thái và điểm cần
chú ý. Màu xanh được dùng cho baseline/reference hoặc trạng thái đạt; màu vàng
cho candidate cần review hoặc reconciliation; artifact legacy được tách vào
`outputs/legacy/`.

Execution evidence dạng Markdown nằm trong `docs/logs/`:

```text
exercise_01_execution.md
exercise_02_execution.md
exercise_03_execution.md
exercise_04_execution.md
exercise_05_execution.md
```

Raw runtime log nằm trong `runs/` và không thay thế execution evidence đã diễn
giải.

## 10. Trạng thái hiện tại

- E01: completed và validated.
- E02: train-only evidence validated.
- E03: natural-log first difference, `d=1`, evidence validated.
- E04: đã phê duyệt và kiểm tra; bàn giao candidates cho E05.
- E05: đã phê duyệt và kiểm tra; residual-autocorrelation là limitation cần ghi nhận.
- E06: đã duyệt triển khai SARIMA; validation và execution evidence pending.

E04/E05 chưa được ghi là formal completion chỉ vì notebook đã chạy thành công.
Residual Ljung–Box và approval/status reconciliation vẫn phải được review.

## 11. Nguyên tắc merge

Trước khi merge hoặc push cần xác nhận:

1. Notebook chạy được từ clean kernel.
2. E02–E04 không dùng test observations.
3. E05 forecast có đúng 41 observations và index khớp test index.
4. Baseline và residual diagnostics được báo cáo.
5. Log, execution evidence, outputs và current status cùng phản ánh một run.
6. Không có thay đổi raw dataset hoặc absolute machine path trong source/notebook.
