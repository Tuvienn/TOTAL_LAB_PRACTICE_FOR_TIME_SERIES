# Practice 4 — Multivariate Time Series Forecasting

Practice 4 dự báo điện năng tiêu thụ theo giờ từ lịch sử `load` và các biến thời
tiết bằng VAR, XGBoost và LSTM.

Notebook đã thực thi 50/50 code cells; các kết quả trong tài liệu này tương ứng
với lần chạy hiện tại.

<p>
<a href="docs/results/README.md" style="color:#1f6feb; font-weight:600;">🔗 Mở Dashboard kết quả</a>
&nbsp; · &nbsp;
<a href="notebooks/practice4.ipynb" style="color:#1f6feb; font-weight:600;">🔗 Mở Notebook chính</a>
&nbsp; · &nbsp;
<a href="docs/environment.md" style="color:#1f6feb; font-weight:600;">🔗 Xem môi trường VS Code</a>
</p>

## 1. Mục tiêu

- Dự báo `load` ở bước thời gian kế tiếp.
- Sử dụng 24 giờ lịch sử gần nhất và bốn biến đầu vào.
- So sánh VAR, XGBoost và LSTM bằng RMSE, MAE và MAPE.
- Duy trì thứ tự thời gian, tránh leakage và đánh giá bằng walk-forward
  one-step-ahead.

## 2. Dataset và provenance

Dataset chính là **Hourly energy demand, generation and weather**, với file
canonical:

```text
datasets/processed/electricity_load_weather_hourly.csv
```

Audit hiện tại của processed dataset:

| Thuộc tính | Giá trị |
|---|---:|
| Số dòng / cột | 35.064 / 5 |
| Khoảng thời gian | 2014-12-31 23:00 UTC → 2018-12-31 22:00 UTC |
| Tần suất | Hourly |
| Missing values | 36 missing `load` targets; weather inputs complete |
| Duplicate timestamps | 0 |
| Khoảng thời gian bất thường | 0 |
| SHA-256 | `9dd198be2b630b75bb679d8c7b3cb6fe1c655638114b81cf655fc5576ade3e6f` |

Raw provenance và checksum được ghi trong
<a href="docs/status/current_status.md" style="color:#1f6feb;">docs/status/current_status.md</a>. Raw data không
được chỉnh sửa trong notebook.

## 3. Notebook và môi trường

Notebook chính:

- <a href="notebooks/practice4.ipynb" style="color:#1f6feb;">notebooks/practice4.ipynb</a>

Môi trường VS Code:

- Chọn kernel **Practice 4 (.venv, Python 3.12)**.
- Không cần cài package trong notebook.
- Dependency được pin trong <a href="requirements.txt" style="color:#1f6feb;">requirements.txt</a>.
- Hướng dẫn môi trường nằm tại <a href="docs/environment.md" style="color:#1f6feb;">docs/environment.md</a>.

## 4. Luồng Phase

```text
Phase 1 — Data Preparation
  ↓
Phase 2 — Temporal Split và Validation Design
  ↓
Phase 3 — Training-only Exploratory Data Analysis
  ↓
Phase 4 — Preprocessing và Scaling
  ↓
Phase 5 — Feature Engineering
  ↓
Phase 6 — VAR
  ↓
Phase 7 — XGBoost
  ↓
Phase 8 — LSTM
  ↓
Phase 9 — Walk-forward Evaluation và Error Analysis
  ↓
Phase 10 — Results và Final Report
```

Dashboard kết quả theo từng Phase:
<a href="docs/results/README.md" style="color:#1f6feb; font-weight:600;">docs/results/README.md — Mở Dashboard</a>.

## 5. Protocol chính

- Chia dữ liệu theo thời gian 70% Train, 15% Validation, 15% Test.
- EDA và mọi fitted transformation dùng ranh giới thông tin của Train.
- Missing `load` được forward-fill past-only cho input; các target gốc bị thiếu bị loại khỏi metrics.
- `StandardScaler` chỉ được fit trên Train.
- Validation dùng để chọn cấu hình và early stopping.
- Test chỉ được mở ở bước đánh giá cuối.
- VAR, XGBoost và LSTM dùng cùng các mốc Validation/Test và cùng thang đo
  `load` ban đầu khi tính metrics.
- Backtesting là recursive rolling one-step-ahead: prediction được append vào
  history; XGBoost/LSTM dùng weather quan sát tại timestamp kế tiếp trong
  retrospective evaluation và không retrain sau mỗi bước.

## 6. Kết quả lần chạy hiện tại

| Model | Test RMSE | Test MAE | Test MAPE |
|---|---:|---:|---:|
| LSTM | 4855.8257 | 3884.7037 | 13.3496% |
| XGBoost | 3664.4820 | 2935.2076 | 9.9482% |
| VAR | 4614.2743 | 3952.8715 | 13.9444% |

XGBoost đang đứng đầu theo Test RMSE trong lần chạy hiện tại. Bảng đầy đủ nằm
trong <a href="results/model_evaluation.csv" style="color:#1f6feb;">results/model_evaluation.csv</a> và
<a href="results/model_evaluation.xlsx" style="color:#1f6feb;">results/model_evaluation.xlsx</a>.

## 7. Cấu trúc thư mục

```text
Practice_4/
├── datasets/
│   ├── raw/                  # raw source, bất biến
│   └── processed/            # canonical processed dataset
├── notebooks/
│   └── practice4.ipynb      # notebook end-to-end
├── docs/
│   ├── environment.md       # hướng dẫn môi trường VS Code
│   ├── logs/                # runtime log
│   ├── results/              # dashboard và kết quả diễn giải theo Phase
│   ├── plans/                # kế hoạch và architecture context
│   └── status/               # provenance và current status
├── results/                  # CSV/XLSX/model summaries máy sinh ra
├── runs/                     # reserved cho run artifacts
├── src/                      # reusable source nếu được bổ sung
└── tests/                    # tests nếu được bổ sung
```

## 8. Evidence và kết quả

- Runtime log: <a href="docs/logs/practice4.log" style="color:#1f6feb;">docs/logs/practice4.log</a>
- Dashboard: <a href="docs/results/README.md" style="color:#1f6feb;">docs/results/README.md</a>
- Model summaries: <a href="results/model_summaries/" style="color:#1f6feb;">results/model_summaries/</a>
- Current status và provenance: <a href="docs/status/current_status.md" style="color:#1f6feb;">docs/status/current_status.md</a>

Notebook đã thực thi 50/50 code cells không có execution error trong lần chạy
hiện tại. Các bảng và biểu đồ hiển thị trong notebook; các artifact máy đọc được
được lưu trong `results/`.

## 9. Giới hạn hiện tại

- Baseline Naive/Seasonal Naive chưa nằm trong scope bắt buộc của lần triển khai
  này.
- Sáu câu hỏi phân tích bổ sung của đề chưa được viết thành final report.
- Kết quả hiện tại được tổng hợp từ execution của notebook.

## 10. Kiểm tra trước khi merge

1. Chọn đúng kernel **Practice 4 (.venv, Python 3.12)** trong VS Code.
2. Chạy notebook từ đầu đến cuối bằng **Run All**.
3. Kiểm tra log, metrics và model summaries cùng thuộc một lần chạy.
4. Xác nhận không có thay đổi raw dataset hoặc leakage qua temporal boundary.
5. Mở Dashboard kết quả tại <a href="docs/results/README.md" style="color:#1f6feb;">docs/results/README.md</a>.
