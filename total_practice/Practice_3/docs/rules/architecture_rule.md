# TIME SERIES PRACTICE 03 — QUY TẮC KIẾN TRÚC

## 1. Danh tính tài liệu

```text
Document ID: TS-PRACTICE-03-ARCHITECTURE-v1.1
Phạm vi repository: total_practice/Practice_3
Chủ đề: Dự báo chuỗi thời gian bằng Machine Learning
Dataset chính: datasets/raw/AEP_hourly.csv
Trạng thái: APPROVED_AND_ACTIVE
Ngày cập nhật: 2026-10-21
```

Tài liệu này quy định kiến trúc, trách nhiệm thư mục, vòng đời dữ liệu, hướng dependency, ranh giới notebook/source code, quyền sở hữu output và các validation gate cho `Practice_3`.

Tài liệu này bổ sung, không thay thế:

```text
working_rule.md
.agents/RULES_INDEX.md và các canonical rule được router này nạp
total_practice/Practice_3/docs/rules/rule_code.md
total_practice/Practice_3/docs/plans/PLAN_OVERVIEW.md
total_practice/Practice_3/docs/plans/PROJECT_WORKFLOW.md
```

Nếu các nguồn bắt buộc xung đột, phải dừng thực thi, chỉ rõ conflict và chờ Human quyết định.

---

## 2. Mục tiêu và phạm vi kiến trúc

Practice 3 xây dựng pipeline dự báo mức tiêu thụ năng lượng theo giờ từ dữ liệu quá khứ:

```text
Raw hourly series
→ Data validation
→ Time-safe feature engineering
→ Supervised dataset
→ Chronological split
→ Model training and time-aware tuning
→ One-step and multi-step forecasting
→ Evaluation and interpretation
```

Phạm vi chính:

- chuẩn bị và kiểm tra dữ liệu;
- tạo lag features, rolling mean và rolling standard deviation;
- tạo `X` và `y` đúng alignment;
- chia train/test theo thời gian;
- huấn luyện XGBoost baseline, tuned XGBoost và Random Forest;
- dự báo one-step và multi-step;
- đánh giá bằng MAE, RMSE và biểu đồ Actual vs Predicted;
- phân tích feature importance và trả lời các câu hỏi của đề.

Linear Regression và ARIMA chỉ được triển khai thành thí nghiệm nếu một bước sau được Human duyệt. Nếu không, chúng chỉ thuộc phần thảo luận lý thuyết và phải được ghi nhãn rõ.

---

## 3. Canonical Practice Root

Root chuẩn:

```text
total_practice/Practice_3/
```

Cấu trúc sở hữu:

```text
Practice_3/
├── README.md
├── pyproject.toml
├── config/
├── datasets/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── rules/
│   ├── plans/
│   ├── exercise_details/
│   ├── error_analysis/
│   ├── fix_plans/
│   ├── status/
│   └── logs/
├── notebooks/
├── runs/
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

Không tạo folder song song có cùng trách nhiệm, không đổi cấu trúc và không thêm dependency nếu chưa được Human duyệt.

---

## 4. Trách nhiệm thư mục

### 4.1 `datasets/`

`datasets/raw/` lưu bằng chứng dữ liệu gốc. File `AEP_hourly.csv` phải bất biến: không ghi đè, sort, deduplicate, impute, resample, đổi schema hoặc sửa timestamp trực tiếp trên file này.

`datasets/processed/` chỉ chứa dữ liệu dẫn xuất theo protocol đã được duyệt. Mọi dữ liệu processed phải có thể tái tạo từ raw data, source code, configuration và bước xử lý đã được ghi nhận.

### 4.2 `config/`

Sở hữu tham số có thể cấu hình như lag, rolling window, split boundary, forecast horizon, random seed, model parameters và TimeSeriesSplit settings sau khi các giá trị này được duyệt.

Không hard-code đường dẫn tuyệt đối theo máy cá nhân trong configuration dùng chung.

### 4.3 `src/practice_3/`

- `data/`: load, schema validation, time-index audit, approved preprocessing, chronological split và supervised-dataset construction.
- `analysis/`: feature engineering, model training, tuning, forecasting, metrics, comparison và feature importance.
- `visualization/`: các hàm trực quan hóa có thể tái sử dụng.

Logic correctness-critical hoặc được dùng lại phải có một owner duy nhất trong `src/practice_3/`, không bị sao chép giữa nhiều notebook cell.

### 4.4 `notebooks/`

Notebook sở hữu phần trình bày và orchestration:

```text
problem definition
data preview
verified observations
calls to reusable source logic
tables and figures
interpretation
final conclusions
```

Notebook không được trở thành owner duy nhất của data repair, feature engineering, split, tuning, metrics hoặc forecast logic cần kiểm thử.

### 4.5 `outputs/`

- `outputs/figures/`: biểu đồ đã tạo từ một execution có thể truy vết.
- `outputs/results/`: bảng metric, prediction, comparison hoặc machine-readable result.

Không đặt source code, raw data hay tài liệu governance trong `outputs/`. Không coi output cũ là bằng chứng cho code hiện tại nếu chưa tái chạy hoặc xác minh provenance.

### 4.6 `docs/`

- `rules/`: quy tắc kiến trúc và thực thi.
- `plans/`: kế hoạch tổng quan và workflow đã được review.
- `exercise_details/`: đặc tả chi tiết khi cần và được duyệt.
- `error_analysis/`: issue khoa học hoặc kỹ thuật không đơn giản.
- `fix_plans/`: kế hoạch sửa đã tách riêng để Human duyệt.
- `logs/`: bằng chứng execution.
- `status/`: trạng thái hiện tại của Practice.

Không bắt buộc tạo tài liệu chi tiết cho từng exercise nếu plan hiện có đã đủ rõ và Human chưa yêu cầu.

### 4.7 `tests/`

Sở hữu kiểm tra tự động cho schema, timestamp, feature alignment, chronology, leakage, split boundary, shape, metric và hành vi deterministic phù hợp với từng bước.

### 4.8 `runs/`

`runs/` lưu lịch sử execution cục bộ của các training job có thể bị gián đoạn. Mỗi run phải có định danh riêng và chỉ chứa log, metadata, configuration snapshot, checkpoint, biểu đồ tiến độ và kết quả tạm của chính run đó.

`runs/` là generated local state và phải được Git ignore. Artifact trong `runs/` không tự trở thành kết quả chính thức. Chỉ run đã hoàn thành đủ validation gate mới được promote kết quả machine-readable sang `outputs/results/`.

Không lưu binary model trong `runs/` nếu chưa có phê duyệt riêng về serialization và Git policy.

---

## 5. Vòng đời dữ liệu

Luồng chuẩn:

```text
datasets/raw/AEP_hourly.csv
→ read-only load
→ schema and time-index audit
→ in-memory working copy
→ approved treatment, if required
→ time-safe feature table
→ chronological train/test split
→ train-only validation and tuning
→ sealed final test evaluation
→ outputs and execution evidence
```

Trước feature engineering phải xác minh ít nhất:

```text
Datetime column
AEP_MW target column
numeric target validity
date range
chronological ordering
duplicate timestamps
missing timestamps
sampling frequency
missing cell values
```

Các bất thường time index đã quan sát phải được báo cáo. Không được tự chọn cách sort, gộp timestamp trùng, chèn giờ thiếu, fill, interpolate hoặc resample khi protocol chưa được Human duyệt.

---

## 6. Ranh giới feature và chống leakage

Tại thời điểm dự báo `t`, feature chỉ được dùng thông tin tồn tại trước `t`.

```text
lag_k(t) = y(t-k), với k > 0
```

Rolling features phải loại `y(t)` khỏi cửa sổ khi target cần dự báo là `y(t)`. Centered rolling hoặc rolling chứa giá trị hiện tại/tương lai không được dùng làm forecasting feature.

Target không được xuất hiện trong feature set. Việc loại các hàng NaN đầu chuỗi do lag/rolling phải có nguyên nhân dự kiến, được kiểm tra và không được che mất các NaN bất thường khác.

Mọi transformation học tham số từ dữ liệu phải fit trong training boundary tương ứng.

---

## 7. Split, validation và model ownership

Train/test split phải theo thời gian, không shuffle, và thỏa:

```text
max(train_time) < min(test_time)
```

Test set cuối cùng là sealed evaluation set, không dùng để chọn lag, rolling window, feature set, model hoặc hyperparameter.

`TimeSeriesSplit` chỉ hoạt động trong training set. Các model được so sánh phải dùng cùng feature definition, split, forecast horizon và metric trừ khi thí nghiệm được ghi rõ là khác mục tiêu.

Một baseline dự báo đơn giản phải được định nghĩa và duyệt trước khi tuyên bố model Machine Learning cải thiện. XGBoost baseline trong đề là baseline giữa các cấu hình XGBoost; nó không tự thay thế forecasting baseline theo canonical Time Series rules.

Random seed, metric chính/phụ, split boundary, lag set, rolling window, CV folds, multi-step horizon và search space phải được ghi nhận trước execution tương ứng; rule này không tự chốt giá trị của chúng.

---

## 8. One-step và multi-step forecasting

One-step và multi-step là hai protocol riêng, không được trộn kết quả.

Multi-step phải ghi rõ:

```text
forecast horizon
recursive, direct hoặc strategy khác
feature update rule
availability of future covariates, nếu có
metric aggregation
```

Recursive forecast không được dùng actual future target để tạo lag cho bước kế tiếp. Direct forecast phải kiểm tra target shift và alignment riêng cho từng horizon.

---

## 9. Evaluation và interpretation

MAE và RMSE phải được tính trên cùng timestamp và cùng horizon cho các model được so sánh. Mỗi bảng hoặc hình kết quả phải truy vết được về model, feature set, split, seed và execution tương ứng.

Feature importance phải gắn với đúng fitted model và đúng tên feature. Importance chỉ phản ánh cách model sử dụng feature trong cấu hình đã chạy; không được diễn giải thành quan hệ nhân quả.

Kết luận phải phân biệt:

```text
evidence từ execution
quan sát từ dữ liệu
giải thích lý thuyết
limitation chưa giải quyết
```

---

## 10. Dependency direction

Hướng dependency hợp lệ:

```text
notebook
→ src/practice_3 data, analysis, visualization
→ approved config and datasets
```

Source module không phụ thuộc vào notebook. Không dùng `sys.path` hack, import từ output, import qua đường dẫn tuyệt đối của máy hoặc duplicate implementation để né package structure.

---

## 11. Validation gates

Không đi tiếp khi gate hiện tại chưa đạt:

1. Dataset gate: schema và time index đã được audit; issue đã được báo cáo.
2. Treatment gate: mọi sửa dữ liệu cần thiết đã có protocol được duyệt.
3. Feature gate: lag/rolling alignment đúng và không leakage.
4. Supervised-data gate: `X`, `y`, index và NaN hợp lệ.
5. Split gate: chronology đúng; test chưa bị dùng trong tuning.
6. Model gate: model fit/predict đúng shape và reproducible theo cấu hình.
7. Forecast gate: one-step/multi-step strategy đúng information boundary.
8. Evaluation gate: metric và comparison cùng phạm vi.
9. Interpretation gate: kết luận truy vết được về output thật.

---

## 12. Stop conditions

Phải dừng và báo Human khi:

- schema hoặc dataset khác với source đã duyệt;
- cần quyết định cách xử lý duplicate/missing timestamp hoặc irregular frequency;
- phát hiện leakage, overlap hoặc alignment sai;
- cần thêm dependency;
- cần mở rộng model, metric, horizon hoặc output ngoài scope;
- notebook và source cho kết quả không nhất quán;
- validation thất bại mà chưa rõ nguyên nhân;
- plan hoặc rule bắt buộc xung đột.

---

## 13. Tiêu chuẩn hoàn thành kiến trúc

Một bước chỉ được xem là hoàn thành khi owner đúng, raw data vẫn bất biến, chronology được bảo toàn, leakage được kiểm soát, output thực tế đã được kiểm tra và kết luận không vượt quá bằng chứng.
