# Practice 3 v2 — Time-Series Forecasting với Machine Learning

Practice 3 v2 xây dựng workflow dự báo điện năng theo giờ từ dữ liệu AEP, từ định
nghĩa bài toán đến đánh giá, phân tích lỗi và kết luận cuối. Notebook chỉ dùng để
trình bày official artifacts; pipeline, training và evaluation nằm trong source.

## Mục lục

1. [Bài toán](#bài-toán)
2. [Workflow](#workflow)
3. [Kết quả chính](#kết-quả-chính)
4. [Trả lời câu hỏi bài tập](#trả-lời-câu-hỏi-bài-tập)
5. [Liên kết kết quả](#liên-kết-kết-quả)
6. [Chạy kiểm tra](#chạy-kiểm-tra)
7. [Giới hạn khoa học](#giới-hạn-khoa-học)
8. [Trạng thái bàn giao](#trạng-thái-bàn-giao)

## Bài toán

- Dataset: AEP Hourly Energy Consumption.
- Target: `AEP_MW`.
- Primary protocol: one-step hourly forecasting.
- Secondary protocol: recursive 24-hour forecasting.
- Historical holdout không được tuyên bố là truly unseen.

Nguồn dữ liệu: [Kaggle — Hourly Energy Consumption](https://www.kaggle.com/datasets/robikscube/hourly-energy-consumption?select=AEP_hourly.csv).

## Workflow

```text
Problem
→ Data Preparation
→ Temporal Split & Validation
→ TRAIN-only EDA
→ Feature Engineering
→ X/y Construction
→ Model Selection
→ Final Evaluation
→ Error & Interpretation
→ Final Conclusion
```

Thiết kế chi tiết từng phase nằm tại [docs/phase_details](docs/phase_details/).
Trạng thái hiện tại nằm tại [current_status.md](docs/status/current_status.md).

## Kết quả chính

Model chính được khóa là `xgboost_tuned` với 22 features.

| Protocol | MAE (MW) | RMSE (MW) |
|---|---:|---:|
| One-step historical holdout | 102,841 | 137,929 |
| Recursive 24-hour pooled | 509,652 | 720,451 |

One-step dùng 8.592 common timestamps. Recursive evaluation dùng 357 common
origins và 8.568 predictions cho mỗi candidate.

## Trả lời câu hỏi bài tập

- Tuned XGBoost có development CV MAE thấp hơn Linear Regression khoảng 20,845%
  trên cùng 42.413 validation samples.
- Lag-only error giảm mạnh đến `p=24`, tốt nhất quan sát tại `p=48`, rồi tăng lại
  tại `p=168`; nhiều lag hơn không phải lúc nào cũng tốt hơn.
- Project chưa benchmark ARIMA. So sánh XGBoost–ARIMA chỉ là phân tích điều kiện
  áp dụng, không phải empirical superiority claim.

## Liên kết kết quả

- Notebook trình bày: [Practice_3_v2_present.ipynb](notebooks/Practice_3_v2_present.ipynb)
- Tổng quan project: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
- Workflow: [PROJECT_WORKFLOW.md](docs/plans/PROJECT_WORKFLOW.md)
- Plan overview: [PLAN_OVERVIEW.md](docs/plans/PLAN_OVERVIEW.md)
- Phase 9 design: [PHASE_09_FINAL_CONCLUSION.md](docs/phase_details/PHASE_09_FINAL_CONCLUSION.md)
- Kết quả Phase 9: [PHASE_09_RESULT.md](docs/results/PHASE_09_RESULT.md)
- Official final JSON: [phase_09_final_conclusion.json](outputs/results/phase_09_final_conclusion.json)
- Phase 9 execution log: [PHASE_09_EXECUTION.md](docs/logs/PHASE_09_EXECUTION.md)

## Chạy kiểm tra

```bash
cd "/Users/vientu/Time Series/TOTAL_LAB_PRACTICE_FOR_TIME_SERIES/total_practice/Practice_3_v2"
source .venv/bin/activate

python -m practice_3_v2.analysis.final_conclusion --preflight
pytest -q
```

Không cần train lại để đọc final conclusion. Không chạy lại các Human-owned
training/evaluation commands khi official artifacts đã tồn tại.

## Giới hạn khoa học

- Historical holdout không phải truly unseen test set.
- Không có prediction interval hoặc uncertainty calibration.
- Recursive error tăng theo horizon; residual vẫn còn autocorrelation.
- Gain importance không phải causal importance.
- Supplemental experiments là post-hoc development-only evidence.
- Chưa có ARIMA benchmark, external validation hoặc production drift monitoring.
- Project không tuyên bố production readiness.

## Trạng thái bàn giao

Phase 9 đã đạt technical validation:

- official final conclusion JSON: `PASS`;
- focused tests: `23/23 PASS`;
- table-style focused tests: `2/2 PASS`;
- presentation-loader focused tests: `2/2 PASS`;
- full regression suite: `212/212 PASS`;
- notebook clean execution: `27/27` code cells, không có error;
- setup cell đã giảm từ `116` xuống `30` dòng;
- toàn bộ `28` HTML table outputs dùng chung theme light/dark;
- local links trong README: `PASS`.

Project đang chờ Human final review và handoff approval. Chưa có commit hoặc push
nào được thực hiện trong bước hoàn tất Phase 9 này.
