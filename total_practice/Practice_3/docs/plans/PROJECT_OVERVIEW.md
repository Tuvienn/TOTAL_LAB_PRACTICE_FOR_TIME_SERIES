# PRACTICE 3 — TỔNG QUAN DỰ ÁN

## 1. Mô tả

`Practice_3` xây dựng lại Practice 3 thành một workflow dự báo chuỗi thời gian end-to-end, có kiểm soát temporal leakage và có bằng chứng kiểm thử cho từng phase.

Bài toán chính là dùng lịch sử tiêu thụ điện theo giờ để dự báo `AEP_MW` ở giờ kế tiếp. Dự báo recursive 24 giờ được dùng như một secondary stress test sau khi model đã được lựa chọn và khóa.

## 2. Bài toán và dữ liệu

| Thành phần | Nội dung |
|---|---|
| Dataset | AEP Hourly Energy Consumption |
| Nguồn | [Kaggle — Hourly Energy Consumption](https://www.kaggle.com/datasets/robikscube/hourly-energy-consumption?select=AEP_hourly.csv) |
| Raw file | `datasets/raw/AEP_hourly.csv` |
| Timestamp | `Datetime` |
| Target | `AEP_MW` |
| Đơn vị | MW |
| Tần suất | Theo giờ |
| Khoảng thời gian | `2004-10-01 01:00:00` đến `2018-08-03 00:00:00` |
| Raw-data policy | Bất biến |

Machine-readable contract nằm tại `config/data_contract.json` và `config/forecasting_contract.json`.

## 3. Mục tiêu dự báo

### Primary task

- One-step hourly forecasting: tại forecast origin `t`, dự báo `y(t+1)`.
- Được dùng làm mục tiêu chính để validation và lựa chọn model.

### Secondary task

- Recursive 24-hour forecasting: dự báo từ `y(t+1)` đến `y(t+24)` mà không dùng actual target sau forecast origin.
- Chỉ dùng để đánh giá khả năng suy giảm theo forecast horizon; không được thay đổi model đã khóa bằng primary task.

## 4. Phạm vi

### Trong phạm vi

- Structural data preparation và data-quality audit.
- Temporal split trước EDA.
- TRAIN-only EDA.
- Time-safe lag, rolling và calendar features.
- X/y construction và expanding-window validation.
- Persistence và Seasonal Naive 24 baselines.
- XGBoost baseline, tuned XGBoost và Random Forest.
- One-step evaluation, recursive 24-hour evaluation, error analysis và interpretation.

### Ngoài phạm vi ban đầu

- ARIMA/SARIMA.
- Deep learning.
- Prediction interval.
- Deployment và production serving.

Mọi mở rộng ngoài phạm vi phải được Human duyệt riêng.

## 5. Temporal design

```text
Development/TRAIN:
    timestamp < 2017-08-03 00:00:00

Historical re-evaluation holdout:
    2017-08-03 00:00:00
    → 2018-08-03 00:00:00

TRAIN validation:
    5 expanding-window temporal folds

Shuffle:
    false
```

Holdout đã từng được quan sát trong legacy implementation nên không được mô tả là untouched hoặc unseen final test. Evidence khoa học chính cho model selection là TRAIN-only temporal CV.

## 6. Metrics và model selection

- Primary metric: MAE.
- Secondary metric: RMSE.
- Stability evidence: standard deviation của MAE qua các temporal folds.

Thứ tự lựa chọn model:

1. Mean CV MAE thấp nhất.
2. Nếu cần phân giải: mean CV RMSE thấp hơn.
3. Nếu vẫn cần phân giải: CV MAE standard deviation thấp hơn.
4. Nếu vẫn tương đương: ưu tiên candidate đơn giản hơn theo thứ tự đã khóa trước training.

## 7. Workflow end-to-end

```text
Problem & Forecasting Definition
→ Structural Data Preparation
→ Temporal Split & Validation Design
→ TRAIN-only EDA
→ Feature Engineering
→ X/y Construction
→ Baseline, Training, Tuning & Model Lock
→ Final Forecasting & Evaluation
→ Error & Interpretation Analysis
→ Final Conclusion
```

Chi tiết luồng dữ liệu và validation gate nằm tại `docs/plans/PROJECT_WORKFLOW.md`. Trạng thái từng phase nằm tại `docs/plans/PLAN_OVERVIEW.md` và `docs/status/current_status.md`.

## 8. Nguyên tắc bằng chứng

- Raw data không được chỉnh sửa.
- Feature tại forecast origin chỉ được dùng dữ liệu đã có trong quá khứ.
- EDA, feature decision, tuning và model selection không được đọc holdout target.
- Notebook chỉ trình bày official artifacts; không sở hữu pipeline, training hoặc prediction logic.
- `runs/` chỉ lưu execution state cục bộ; `outputs/results/` và `outputs/figures/` mới là official evidence sau validation.
- Mỗi phase phải PASS validation gate và được Human review trước khi phase kế tiếp được triển khai.

## 9. Tiêu chí hoàn thành dự án

Project hoàn thành khi:

- toàn bộ Phase 0–9 đạt validation gate;
- model được lựa chọn chỉ từ TRAIN-only temporal CV;
- model lock xảy ra trước khi mở historical holdout;
- one-step và recursive 24-hour results được báo cáo riêng;
- error/interpretation analysis được hoàn tất;
- conclusion nêu đúng giới hạn của historical re-evaluation;
- notebook trình bày được toàn bộ official evidence mà không chạy lại pipeline.
