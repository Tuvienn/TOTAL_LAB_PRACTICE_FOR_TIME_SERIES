# PRACTICE 3 — PROJECT WORKFLOW

## 1. Purpose

Tài liệu này mô tả luồng thực hiện chính thức cho Practice 3:

**Dự đoán chuỗi thời gian sử dụng Machine Learning Models**

Workflow được thiết kế theo đúng 7 bước chính của đề bài, đồng thời tích hợp 4 yêu cầu nâng cao vào đúng vị trí logic trong pipeline thay vì tách thành một phần riêng sau khi hoàn thành core practice.

---

# 2. Official Workflow

```text
STEP 1 — Data Preparation
        ↓
STEP 2 — Feature Engineering
        ├── Lag Features
        ├── Rolling Mean
        └── Rolling Std
        ↓
STEP 3 — X / y Preparation
        ↓
STEP 4 — Time-Based Train/Test Split
        └── TimeSeriesSplit for tuning
        ↓
STEP 5 — Model Training
        ├── Forecasting Baseline
        ├── XGBoost Baseline
        ├── Tuned XGBoost
        └── Random Forest
        ↓
STEP 6 — Forecasting & Evaluation
        ├── One-step Forecasting
        ├── Multi-step Forecasting
        ├── MAE
        ├── RMSE
        └── Model Comparison
        ↓
STEP 7 — Interpretation & Final Analysis
        ├── Feature Importance
        ├── Important Lag Analysis
        ├── Rolling Feature Analysis
        ├── Model Comparison
        └── Required Questions
```

## 2.1 Delivery Phases

Workflow được thực hiện tuần tự theo bảy delivery phases tương ứng trực tiếp với bảy steps:

```text
PHASE 1 — Data Preparation
        → STEP 1

PHASE 2 — Feature Engineering
        → STEP 2

PHASE 3 — X/y Preparation
        → STEP 3

PHASE 4 — Time-Based Split and Validation Design
        → STEP 4

PHASE 5 — Model Training and Tuning
        → STEP 5

PHASE 6 — Forecasting and Evaluation
        → STEP 6

PHASE 7 — Interpretation and Final Conclusion
        → STEP 7
```

Advanced requirements tiếp tục được tích hợp vào phase sở hữu tương ứng, không tạo phase `Advanced` riêng.

Trước mỗi phase:

```text
inspect current evidence
→ create or update phase implementation plan
→ discuss unresolved decisions
→ Human approval
→ implement only that phase
→ run and validate
→ report before the next phase
```

Không tạo trước toàn bộ phase-detail files khi nội dung implementation chưa được thảo luận. Không đi sang phase kế tiếp khi validation gate của phase hiện tại chưa đạt.

---

# 3. Step 1 — Data Preparation

## Goal

Hiểu và chuẩn bị dataset trước khi tạo feature hoặc train model.

## Dataset Contract

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

Contract xác định input của workflow nhưng không tự quyết định data-cleaning protocol.

## Required Checks

Kiểm tra:

- số dòng và số cột;
- tên cột;
- kiểu dữ liệu;
- timestamp column;
- target column;
- thời gian bắt đầu và kết thúc;
- thứ tự timestamp;
- duplicate timestamps;
- missing values;
- missing timestamps;
- frequency thực tế.

## Rule

Không tự động:

- interpolate;
- fill missing;
- remove outlier;
- resample;

Không sort, deduplicate hoặc sửa raw file. Mọi treatment cần thiết phải được đề xuất trong plan chi tiết của Phase 1, nêu rõ impact và được Human duyệt trước implementation.

## Validation Gate

Không đi tiếp nếu chưa:

```text
xác nhận file tuân theo dataset contract
audit chronological order
audit duplicate timestamps
audit missing cell values
audit missing timestamps
xác minh actual frequency
chốt approved treatment nếu treatment là bắt buộc
```

Known issue chỉ được ghi nhận ở bước này; cách xử lý không được suy ra từ overview hoặc tự động áp dụng.

---

# 4. Step 2 — Feature Engineering

## Goal

Chuyển Time Series thành Supervised Learning Dataset.

## 4.1 Lag Features

Tạo:

```text
lag_1
lag_2
...
lag_p
```

Trong đó:

```text
lag_1 = y(t-1)
lag_2 = y(t-2)
...
lag_p = y(t-p)
```

## Validation

Phải kiểm tra thủ công:

```text
lag_1 at time t = target at time t-1
lag_2 at time t = target at time t-2
```

## 4.2 Rolling Mean

Tạo rolling mean từ dữ liệu quá khứ.

Ví dụ:

```text
rolling_mean_k
```

đại diện cho mức trung bình gần đây của chuỗi.

## 4.3 Rolling Std

Tạo rolling standard deviation từ dữ liệu quá khứ.

Mục tiêu:

```text
đo mức biến động gần đây của chuỗi
```

## Leakage Rule

Lag và rolling feature tại thời điểm `t` chỉ được dùng thông tin đã tồn tại trước thời điểm cần dự báo.

Không được sử dụng:

```text
y(t)
y(t+1)
y(t+2)
...
```

để tạo feature dự báo chính `y(t)`.

## Comparison Design

Giữ khả năng so sánh:

```text
Lag-only Features
vs
Lag + Rolling Features
```

## Validation Gate

Không đi tiếp nếu:

- lag alignment sai;
- rolling feature dùng dữ liệu hiện tại/tương lai;
- còn leakage.

---

# 5. Step 3 — X / y Preparation

## Goal

Tạo input và target cho Machine Learning.

## X

Có thể gồm:

```text
lag_1
lag_2
...
lag_p
rolling_mean
rolling_std
```

## y

```text
target
```

## Validation

Kiểm tra:

- X và y có cùng số sample;
- không còn NaN ngoài dự kiến;
- target không xuất hiện trong feature set;
- feature order rõ ràng.

## Validation Gate

Chỉ đi tiếp khi supervised dataset hợp lệ.

---

# 6. Step 4 — Time-Based Train/Test Split

## Goal

Chia dữ liệu theo đúng logic thời gian.

## Main Split

```text
PAST                               FUTURE

|------------- TRAIN -------------|--- TEST ---|
```

Không sử dụng random shuffle.

## Required Check

```text
max(train_time) < min(test_time)
```

## TimeSeriesSplit

TimeSeriesSplit được tích hợp trong bước này để phục vụ tuning ở Step 5.

Luồng:

```text
TRAIN SET
   ↓
TimeSeriesSplit
   ↓
multiple chronological validation folds
```

Ví dụ:

```text
Fold 1
Train: 1 2 3
Valid: 4

Fold 2
Train: 1 2 3 4
Valid: 5

Fold 3
Train: 1 2 3 4 5
Valid: 6
```

## Rule

Test set cuối cùng không được dùng để tune hyperparameter.

## Validation Gate

Không đi tiếp nếu:

- train/test overlap;
- có future leakage;
- TimeSeriesSplit không giữ thứ tự thời gian.

---

# 7. Step 5 — Model Training

## Goal

Thiết lập forecasting baseline và huấn luyện các model cần thiết cho Practice 3.

## 7.1 Forecasting Baseline

Thiết lập một mốc dự báo đơn giản:

```text
Persistence hoặc Naive baseline
```

Định nghĩa chính xác, gồm one-step hay seasonal-naive và cách áp dụng cho multi-step, chỉ được chốt trong implementation plan của Phase 5.

Forecasting baseline không phải model XGBoost và phải được đánh giá trên cùng forecasting protocol với các model Machine Learning.

## 7.2 XGBoost Baseline

Train:

```text
XGBRegressor
```

Mục tiêu:

- kiểm tra pipeline;
- có mốc hiệu năng ban đầu;
- chưa tuning.

Baseline phải:

```text
simple
reproducible
understandable
```

## 7.3 Tuned XGBoost

Sau baseline:

```text
XGBoost
+
TimeSeriesSplit
+
Hyperparameter Search
```

Candidate hyperparameters có thể gồm:

```text
n_estimators
max_depth
learning_rate
subsample
```

Giá trị cụ thể chỉ chốt khi implementation.

## 7.4 Random Forest

Train:

```text
RandomForestRegressor
```

trên cùng dữ liệu để so sánh với XGBoost.

## Fair Comparison Rule

Các model phải sử dụng:

```text
same feature set
same train set
same test set
same forecast horizon
same evaluation metrics
```

## Validation Gate

Forecasting baseline phải:

- tạo được prediction đúng forecast horizon;
- align đúng timestamp với target evaluation.

Mỗi trained model phải:

- fit thành công;
- predict được;
- không lỗi shape;
- không dùng test set trong training/tuning.

---

# 8. Step 6 — Forecasting & Evaluation

## Goal

Dự báo và đánh giá chất lượng các model.

## 8.1 One-step Forecasting

Core forecasting:

```text
t → t+1
```

Dùng dữ liệu quá khứ để dự đoán bước kế tiếp.

## 8.2 Multi-step Forecasting

Tích hợp bài nâng cao:

```text
t → t+1
   → t+2
   → t+3
   → ...
```

Phải ghi rõ strategy multi-step được sử dụng khi implementation.

Không được giả định rằng multi-step giống hoàn toàn one-step.

## 8.3 Evaluation Metrics

Project sử dụng:

```text
MAE
RMSE
```

## 8.4 Visualization

Tạo:

```text
Actual vs Predicted
```

## 8.5 Model Comparison

So sánh tối thiểu:

```text
Forecasting Baseline
XGBoost Baseline
XGBoost Tuned
Random Forest
```

Có thể dùng bảng:

```text
Model                  MAE        RMSE
Forecasting Baseline   ...        ...
XGBoost Baseline       ...        ...
XGBoost Tuned          ...        ...
Random Forest          ...        ...
```

## Validation Gate

Evaluation chỉ hợp lệ nếu:

- dùng test set cuối cùng;
- cùng metric;
- cùng evaluation window;
- không cherry-pick khoảng thời gian thuận lợi.

---

# 9. Step 7 — Interpretation & Final Analysis

## Goal

Hiểu model và hoàn thành phần phân tích của Practice 3.

## 9.1 Feature Importance

Phân tích:

```text
lag features
rolling features
```

và rank theo importance.

## 9.2 Important Lag Analysis

Tìm:

```text
lag nào ảnh hưởng mạnh nhất?
```

Nếu một lag như `lag_24` quan trọng, chỉ được liên hệ với pattern 24 giờ khi kết quả thực tế hỗ trợ.

## 9.3 Rolling Feature Analysis

So sánh:

```text
Lag-only
vs
Lag + Rolling
```

để xem rolling mean/std có cải thiện model hay không.

## 9.4 Model Comparison

Kết luận:

```text
Forecasting Baseline
vs
XGBoost Baseline
vs
XGBoost Tuned
vs
Random Forest
```

dựa trên kết quả thực nghiệm.

## 9.5 Required Questions

Trả lời:

1. So sánh XGBoost với Linear Regression.
2. Điều gì xảy ra khi tăng số lag `p`?
3. Khi nào XGBoost phù hợp hơn ARIMA?

## Rule

Phải phân biệt rõ:

```text
theoretical conclusion
```

và:

```text
experimental conclusion
```

Không được trình bày một kết luận như kết quả thực nghiệm nếu experiment đó chưa chạy.

---

# 10. Mapping Advanced Tasks into Main Workflow

```text
Advanced 1 — Rolling Mean / Rolling Std
→ Step 2 — Feature Engineering

Advanced 2 — Multi-step Forecasting
→ Step 6 — Forecasting & Evaluation

Advanced 3 — Tune Hyperparameter bằng TimeSeriesSplit
→ Step 4 + Step 5

Advanced 4 — Random Forest Comparison
→ Step 5 + Step 6
```

Không có phase "Advanced" riêng.

---

# 11. Verification Workflow

Sau mỗi thay đổi:

```text
Understand
   ↓
Implement Small Change
   ↓
Run
   ↓
Inspect
   ↓
Verify
   ↓
Continue
```

Nếu fail:

```text
STOP
 ↓
Find Cause
 ↓
Fix
 ↓
Run Again
 ↓
Verify
```

---

# 12. Main Validation Gates

## Gate 1 — Dataset Valid

```text
timestamp known
target known
frequency known
```

## Gate 2 — Features Valid

```text
lag alignment correct
rolling logic correct
no future leakage
```

## Gate 3 — Supervised Dataset Valid

```text
X correct
y correct
no unintended NaN
```

## Gate 4 — Split Valid

```text
train strictly before test
test untouched by tuning
```

## Gate 5 — Models Valid

```text
forecasting baseline works
XGBoost baseline works
XGBoost tuning works
Random Forest works
```

## Gate 6 — Evaluation Valid

```text
same test set
same metrics
same evaluation rules
same forecast horizon
```

## Gate 7 — Interpretation Valid

```text
feature importance supported by output
comparison supported by metrics
theory separated from experiment
```

---

# 13. Final Execution Order

```text
1. Inspect AEP_hourly.csv
2. Confirm timestamp, target, frequency
3. Prepare chronological dataset
4. Create lag features
5. Validate lag alignment
6. Create rolling mean/std
7. Validate rolling features
8. Create X and y
9. Perform time-based train/test split
10. Prepare TimeSeriesSplit on training data
11. Define and run forecasting baseline
12. Train XGBoost baseline
13. Tune XGBoost
14. Train Random Forest
15. Perform one-step forecasting
16. Perform multi-step forecasting
17. Calculate MAE / RMSE
18. Plot Actual vs Predicted
19. Compare models
20. Analyze Feature Importance
21. Analyze important lags
22. Analyze rolling feature contribution
23. Answer required questions
24. Write final conclusion
```

---

# 14. Workflow Principle

Practice 3 không phải chỉ là:

```text
train XGBoost
```

Mà là:

```text
Understand Time Series
        ↓
Build Historical Features
        ↓
Prevent Leakage
        ↓
Train Models
        ↓
Forecast
        ↓
Evaluate Fairly
        ↓
Interpret Results
```
