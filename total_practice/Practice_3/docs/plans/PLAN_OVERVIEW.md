# PRACTICE 3 — PLAN OVERVIEW

## 1. Practice Identity

**Practice:** Practice 3
**Topic:** Dự đoán chuỗi thời gian sử dụng Machine Learning Models
**Dataset:** Hourly Energy Consumption — `AEP_hourly.csv`
**Primary Model:** XGBoost Regressor
**Comparison Model:** Random Forest Regressor
**Forecasting:** One-step + Multi-step

---

# 2. Source Requirements

Practice 3 yêu cầu:

## Main Exercise

1. Chuẩn bị dữ liệu.
2. Tạo lag features.
3. Chia X – y.
4. Chia train / test theo thời gian.
5. Huấn luyện XGBoost.
6. Dự đoán và đánh giá.
7. Phân tích feature importance.

## Advanced Exercise

1. Thêm rolling mean / rolling std.
2. Dự báo multi-step.
3. Tune hyperparameter bằng TimeSeriesSplit.
4. So sánh với Random Forest.

## Required Questions

1. So sánh XGBoost với Linear Regression.
2. Điều gì xảy ra khi tăng số lag `p`?
3. Khi nào XGBoost phù hợp hơn ARIMA?

---

# 3. Planning Decision

Practice 3 sẽ **không tách Advanced Exercise thành một workflow riêng**.

Bốn yêu cầu nâng cao được tích hợp trực tiếp vào 7 bước chính theo vị trí logic của chúng.

```text
Rolling Mean / Std
→ Feature Engineering

TimeSeriesSplit
→ Train/Validation Design + Tuning

Random Forest
→ Model Training + Model Comparison

Multi-step Forecasting
→ Forecasting & Evaluation
```

## 3.1 Delivery Phase Decision

Bảy bước chuyên môn được triển khai theo bảy delivery phases tương ứng trực tiếp:

| Phase | Phạm vi |
|---|---|
| Phase 1 | Data Preparation |
| Phase 2 | Feature Engineering |
| Phase 3 | X/y Preparation |
| Phase 4 | Time-Based Split và TimeSeriesSplit Design |
| Phase 5 | Model Training và Tuning |
| Phase 6 | One-step/Multi-step Forecasting và Evaluation |
| Phase 7 | Feature Importance, Interpretation và Final Conclusion |

Mỗi phase chỉ tạo implementation plan chi tiết khi chuẩn bị thực hiện phase đó. Human phải duyệt plan của phase hiện tại trước khi code; chưa cần tạo trước toàn bộ bảy plan.

---

# 4. Overall Goal

Xây dựng một pipeline Machine Learning cho Time Series:

```text
Hourly Energy Consumption
        ↓
Data Preparation
        ↓
Feature Engineering
        ├── Lag Features
        ├── Rolling Mean
        └── Rolling Std
        ↓
Supervised Dataset
        ↓
Time-Based Split
        ↓
Model Training
        ├── Forecasting Baseline
        ├── XGBoost Baseline
        ├── Tuned XGBoost
        └── Random Forest
        ↓
Forecasting
        ├── One-step
        └── Multi-step
        ↓
Evaluation
        ├── MAE
        ├── RMSE
        └── Actual vs Predicted
        ↓
Interpretation
        ├── Feature Importance
        ├── Lag Analysis
        └── Model Comparison
```

---

# 5. Problem Definition

Cho chuỗi đơn biến:

```text
y1, y2, ..., yt
```

sử dụng thông tin quá khứ:

```text
y(t-1), y(t-2), ..., y(t-p)
```

và các feature thống kê từ quá khứ để dự đoán giá trị tương lai.

## Core Target

```text
one-step-ahead forecasting
```

## Extended Target

```text
multi-step forecasting
```

---

# 6. Dataset

## 6.1 Dataset Contract

```text
Dataset name: Hourly Energy Consumption
File: datasets/raw/AEP_hourly.csv
Format: CSV
Source platform: Kaggle
Source URL: https://www.kaggle.com/datasets/robikscube/hourly-energy-consumption
Provider/context: PJM
Timestamp column: Datetime
Target column: AEP_MW
Target meaning: hourly energy consumption
Target unit: MW
Expected granularity: hourly
Raw-data policy: immutable
```

Dataset thuộc Hourly Energy Consumption dataset của PJM. Đề mô tả dữ liệu là mức tiêu thụ năng lượng theo giờ trong hơn 10 năm.

Dataset contract định nghĩa input chính thức của Practice 3. Contract không quyết định cách xử lý data-quality issue và không cho phép sửa trực tiếp raw file.

## 6.2 Known Pre-Audit Observations

Kiểm tra read-only ban đầu đã xác nhận:

```text
columns = Datetime, AEP_MW
timestamp_parseable = yes
target_numeric = yes
raw_order_monotonic = no
duplicate_timestamps_present = yes
missing_hourly_timestamps_present = yes
```

Các quan sát này là input cho Phase 1, không phải quyết định xử lý dữ liệu.

## 6.3 Phase 1 Verification

Phase 1 phải tái kiểm tra và lưu bằng chứng cho:

```text
date_range
number_of_rows
schema_and_dtypes
chronological_order
actual_frequency
missing_cell_values
missing_timestamps
duplicate_timestamps
invalid_target_values
```

Cách sort working copy, xử lý duplicate, xử lý missing timestamp hoặc tạo processed data chỉ được quyết định trong plan chi tiết của Phase 1 và phải được Human duyệt trước implementation.

---

# 7. Main Plan — 7 Integrated Steps

## Step 1 — Data Preparation

Mục tiêu:

```text
load
inspect
validate
prepare
```

Kiểm tra:

- schema;
- timestamp;
- target;
- frequency;
- missing;
- duplicates;
- chronological order.

---

## Step 2 — Feature Engineering

Tạo:

```text
lag_1
lag_2
...
lag_p
```

và tích hợp bài nâng cao:

```text
rolling_mean
rolling_std
```

Mục tiêu:

```text
Time Series
→
Supervised Learning Features
```

Phải đảm bảo không future leakage.

---

## Step 3 — X / y Preparation

```text
X =
lag features
+
rolling features

y =
target
```

Kiểm tra alignment giữa feature và target.

---

## Step 4 — Time-Based Train/Test Split

Chia:

```text
PAST → TRAIN
FUTURE → TEST
```

Không shuffle.

Tích hợp:

```text
TimeSeriesSplit
```

trên training data để phục vụ tuning.

---

## Step 5 — Model Training

Thiết lập baseline và train:

### Forecasting Baseline

```text
Persistence hoặc Naive baseline
```

Baseline cụ thể chỉ được chốt trong implementation plan của Phase 5 dựa trên forecasting horizon.

### Model A

```text
XGBoost Baseline
```

### Model B

```text
Tuned XGBoost
```

### Model C

```text
Random Forest
```

Forecasting baseline phải có trước để tạo mốc dự báo đơn giản. XGBoost Baseline là cấu hình XGBoost ban đầu trước tuning, không thay thế forecasting baseline.

---

## Step 6 — Forecasting & Evaluation

Thực hiện:

```text
One-step Forecasting
Multi-step Forecasting
```

Đánh giá bằng:

```text
MAE
RMSE
Actual vs Predicted
```

So sánh forecasting baseline và các model trên cùng test set, cùng evaluation window và cùng forecast horizon.

---

## Step 7 — Interpretation & Final Analysis

Phân tích:

```text
Feature Importance
Important Lags
Rolling Features
Model Performance
```

Trả lời 3 câu hỏi cuối bài và viết final conclusion.

---

# 8. Experiment Structure

Practice 3 cần giữ khả năng so sánh từng thay đổi.

## Feature Comparison

```text
Experiment A
Lag-only

vs

Experiment B
Lag + Rolling Mean/Std
```

## Model Comparison

```text
Forecasting Baseline
vs
XGBoost Baseline
vs
Tuned XGBoost
vs
Random Forest
```

## Lag Experiment

Để trả lời câu hỏi về số lag `p`, có thể thử:

```text
small p
medium p
large p
```

và theo dõi:

```text
number of features
training time
MAE
RMSE
```

Giá trị cụ thể của `p` chưa chốt ở overview stage.

---

# 9. Data Leakage Rules

Đây là yêu cầu kỹ thuật quan trọng nhất của Practice 3.

Feature tại thời điểm `t` không được chứa thông tin từ tương lai.

Không được để:

```text
future target
future rolling statistics
future observations
```

lọt vào training features.

Train phải xảy ra trước test theo thời gian.

Test set cuối cùng không được dùng để tuning.

---

# 10. Model Strategy

## Forecasting Baseline

Sử dụng Persistence hoặc Naive baseline làm mốc dự báo đơn giản. Định nghĩa chính xác, gồm one-step hay seasonal-naive và cách áp dụng cho multi-step, chỉ được chốt trong implementation plan của Phase 5.

## XGBoost Baseline

Mục tiêu:

```text
simple
reproducible
easy to understand
```

## Tuned XGBoost

Tune bằng:

```text
TimeSeriesSplit
```

sau khi baseline chạy đúng.

## Random Forest

Dùng làm comparison model theo yêu cầu nâng cao.

---

# 11. Forecasting Strategy

## One-step

```text
t → t+1
```

Đây là bài toán cơ bản.

## Multi-step

```text
t → t+1
   → t+2
   → t+3
   → ...
```

Strategy multi-step cụ thể phải được chốt trong implementation plan, không tự giả định ở overview.

---

# 12. Evaluation Strategy

Project sử dụng:

```text
MAE
RMSE
```

và:

```text
Actual vs Predicted Plot
```

Mục tiêu đánh giá:

- model sai bao nhiêu;
- các model Machine Learning có cải thiện so với forecasting baseline không;
- model có bám pattern không;
- tuning có cải thiện không;
- rolling features có giúp không;
- Random Forest so với XGBoost thế nào;
- multi-step suy giảm ra sao nếu có.

---

# 13. Feature Importance Strategy

Sau khi train XGBoost:

1. lấy feature importance;
2. rank các feature;
3. tìm lag quan trọng;
4. xem rolling feature có quan trọng không;
5. giải thích kết quả dựa trên output thực tế.

Không được suy diễn seasonality nếu chưa có bằng chứng từ kết quả.

---

# 14. Required Questions Plan

## Question 1 — XGBoost vs Linear Regression

Phân biệt:

- tuyến tính vs phi tuyến;
- interaction giữa feature;
- complexity;
- interpretability.

Nếu không train Linear Regression thì ghi rõ đây là theoretical comparison.

## Question 2 — Effect of Increasing Lag p

Thực nghiệm bằng nhiều giá trị `p`.

Theo dõi:

```text
feature count
training time
MAE
RMSE
```

Không giả định nhiều lag luôn tốt hơn.

## Question 3 — XGBoost vs ARIMA

Phân tích:

```text
statistical time-series model
vs
feature-based machine learning model
```

Nếu không train ARIMA trong Practice 3 thì ghi rõ đây là theoretical comparison.

---

# 15. Proposed Notebook Structure

```text
01. Practice Information

02. Imports

03. Load Dataset

04. Dataset Inspection

05. Data Preparation

06. Time-Series Visualization

07. Lag Feature Engineering

08. Rolling Feature Engineering

09. X / y Preparation

10. Time-Based Train/Test Split

11. TimeSeriesSplit Setup

12. Forecasting Baseline

13. XGBoost Baseline

14. XGBoost Tuning

15. Random Forest Training

16. One-step Forecasting

17. Multi-step Forecasting

18. Evaluation

19. Actual vs Predicted

20. Model Comparison

21. Feature Importance

22. Lag Analysis

23. Rolling Feature Analysis

24. Required Questions

25. Final Conclusion
```

---

# 16. Initial File Strategy

Practice 3 sử dụng cấu trúc đã được phê duyệt:

```text
Practice_3/
├── datasets/
│   ├── raw/
│   │   └── AEP_hourly.csv
│   └── processed/
├── notebooks/
├── src/
│   └── practice_3/
│       ├── data/
│       ├── analysis/
│       └── visualization/
├── outputs/
│   ├── figures/
│   └── results/
└── tests/
```

Quyền sở hữu logic:

```text
src/practice_3/data
→ load, validation, approved preprocessing, split và dataset construction

src/practice_3/analysis
→ feature engineering, modeling, tuning, forecasting và evaluation

src/practice_3/visualization
→ reusable visualization logic

notebooks
→ orchestration, presentation, interpretation và conclusions
```

Không tạo nhiều module rỗng trước khi có trách nhiệm thực tế. Tuy nhiên, reusable hoặc correctness-critical logic phải được triển khai trong owner phù hợp dưới `src/practice_3/` ngay từ phase sở hữu logic đó, không chờ notebook hoàn thành rồi mới tách ra.

Tên notebook, module và processed artifact cụ thể phải được chốt trong implementation plan của phase liên quan trước khi tạo file.

---

# 17. Definition of Done

Practice 3 hoàn thành khi:

## Data

- [ ] Dataset đã được inspect.
- [ ] Timestamp xác định đúng.
- [ ] Target xác định đúng.
- [ ] Frequency được xác minh.
- [ ] Missing và duplicates được kiểm tra.

## Features

- [ ] Lag features đúng.
- [ ] Rolling mean đúng.
- [ ] Rolling std đúng.
- [ ] Không future leakage.

## Supervised Dataset

- [ ] X đúng.
- [ ] y đúng.
- [ ] Alignment đúng.

## Split

- [ ] Train/test split theo thời gian.
- [ ] Test set không dùng để tuning.
- [ ] TimeSeriesSplit đúng.

## Models

- [ ] Forecasting baseline được định nghĩa và chạy thành công.
- [ ] XGBoost baseline train thành công.
- [ ] XGBoost tuning hoàn thành.
- [ ] Random Forest train thành công.

## Forecasting

- [ ] One-step forecasting hoàn thành.
- [ ] Multi-step forecasting hoàn thành.

## Evaluation

- [ ] Có MAE.
- [ ] Có RMSE.
- [ ] Có Actual vs Predicted.
- [ ] Có bảng model comparison.

## Interpretation

- [ ] Có Feature Importance.
- [ ] Phân tích lag quan trọng.
- [ ] Phân tích rolling features.
- [ ] So sánh model dựa trên kết quả.

## Questions

- [ ] XGBoost vs Linear Regression.
- [ ] Effect of increasing lag p.
- [ ] XGBoost vs ARIMA.

## Final

- [ ] Có kết luận cuối cùng.
- [ ] Mọi kết luận thực nghiệm đều có output hỗ trợ.
- [ ] Không trình bày suy đoán như kết quả thực nghiệm.

---

# 18. First Implementation Target

Bước đầu tiên:

```text
Inspect AEP_hourly.csv
```

Chỉ sau khi xác minh:

```text
timestamp
target
frequency
missing
duplicates
date range
```

mới bắt đầu Feature Engineering.
