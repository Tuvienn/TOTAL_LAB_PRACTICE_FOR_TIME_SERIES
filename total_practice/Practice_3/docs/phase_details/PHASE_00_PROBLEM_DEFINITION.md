# PHASE 00 — PROBLEM & FORECASTING DEFINITION

## 1. Phase identity

```text
Project: Practice_3
Phase: 0
Name: Problem & Forecasting Definition
Status: APPROVED
Human approval: GRANTED
```

## 2. Mục tiêu

Chốt bài toán, dữ liệu, forecast protocol, temporal boundary, metric và claim boundary trước khi Data Preparation, EDA, Feature Engineering hoặc model training bắt đầu.

Phase này không xử lý dữ liệu, không tạo feature, không train model và không tính metric.

## 3. 5W1H

| Thành phần | Nội dung |
|---|---|
| What | Dự báo mức tiêu thụ điện theo giờ với target `AEP_MW`. |
| Why | Đánh giá khả năng dùng Machine Learning cho hour-ahead forecasting và kiểm tra độ suy giảm khi dự báo recursive 24 giờ. |
| Who | Người phân tích dữ liệu và đơn vị cần theo dõi hoặc dự báo nhu cầu điện. |
| Where | Dataset `AEP_hourly.csv` từ Kaggle; source không cung cấp timezone hoặc UTC offset cho từng timestamp. |
| When | Dữ liệu từ `2004-10-01 01:00:00` đến `2018-08-03 00:00:00`, tần suất theo giờ. |
| How | Structural preparation → temporal split → TRAIN-only EDA → features → X/y → TRAIN-only model selection → historical re-evaluation → analysis → conclusion. |

## 4. Data contract

```text
Raw file: datasets/raw/AEP_hourly.csv
Expected columns: Datetime, AEP_MW
Timestamp: Datetime
Target: AEP_MW
Target unit: MW
Expected frequency: hourly
Timezone: timezone-naive vì source không cung cấp offset
Raw policy: immutable
SHA256: 109d122f7b485555c609eecdec2cd5a03172e0a08acd358d863acc93eb452585
```

Canonical machine-readable contract: `config/data_contract.json`.

## 5. Forecasting contract

### 5.1 Primary task

```text
Task: one-step hourly forecasting
Forecast origin: t
Available target history: đến hết t
Output: y(t+1)
Update cadence: mỗi giờ khi actual mới xuất hiện
Role: model selection objective
```

### 5.2 Secondary task

```text
Task: recursive 24-hour forecasting
Forecast origin: t
Outputs: y(t+1), ..., y(t+24)
Actual target sau origin: không được sử dụng
Role: secondary stress test
```

Recursive 24-hour evidence không được dùng để thay đổi model đã khóa bằng primary one-step CV.

## 6. Temporal contract

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

Holdout này đã từng được quan sát trong legacy implementation. Vì vậy Practice 3 không gọi đây là untouched hoặc unseen final test. Scientific selection evidence chính là TRAIN-only temporal CV.

Exact fold boundaries và `gap` phải được thiết kế, kiểm tra và Human duyệt trong Phase 2.

## 7. EDA boundary

EDA phục vụ thiết kế feature chỉ được đọc development/TRAIN period. Holdout target không được dùng để chọn lag, rolling window, calendar feature, model hoặc hyperparameter.

## 8. Metric contract

```text
Primary metric: MAE
Secondary metric: RMSE
Stability evidence: MAE standard deviation qua temporal folds
```

One-step và recursive 24-hour metrics phải được báo cáo riêng. Multi-step phải giữ cả pooled metrics và per-horizon metrics.

## 9. Model-selection contract

Candidate được lựa chọn chỉ từ one-step TRAIN-only CV theo thứ tự:

1. Mean CV MAE thấp hơn.
2. Nếu cần phân giải tiếp, mean CV RMSE thấp hơn.
3. Nếu vẫn cần phân giải, CV MAE standard deviation thấp hơn.
4. Nếu vẫn tương đương, ưu tiên candidate đơn giản hơn theo order được chốt trước Phase 6.

Không được thay đổi decision order sau khi xem historical holdout.

## 10. Baseline và model scope

Forecasting baselines:

- Persistence.
- Seasonal Naive 24.

Machine Learning candidates:

- XGBoost baseline.
- Tuned XGBoost.
- Random Forest.

ARIMA, deep learning, uncertainty interval và deployment nằm ngoài core scope ban đầu. Mọi mở rộng phải được Human duyệt riêng.

## 11. Success criteria

Workflow được xem là hợp lệ khi:

- không có temporal leakage;
- EDA và model selection chỉ dùng development/TRAIN;
- baseline và ML candidates dùng cùng validation population;
- model được khóa trước historical holdout evaluation;
- one-step result được báo cáo riêng với recursive 24-hour result;
- residual/error analysis được thực hiện trước final conclusion;
- mọi claim ghi đúng giới hạn của historical re-evaluation holdout.

Không chốt trước một tỷ lệ cải thiện tối thiểu so với baseline khi Practice 3 chưa tạo baseline evidence.

## 12. Output và completion gate

Phase 0 hoàn thành khi:

- `config/data_contract.json` hợp lệ;
- `config/forecasting_contract.json` hợp lệ;
- raw checksum khớp contract;
- primary/secondary task, metrics và holdout label đã được Human duyệt;
- contract tests PASS;
- chưa có processed data, model hoặc metric được tạo.

Sau Phase 0 mới được thảo luận và thiết kế Phase 1 — Structural Data Preparation.
