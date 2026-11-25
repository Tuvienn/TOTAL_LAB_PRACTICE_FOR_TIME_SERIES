# PHASE 03 — TRAIN-ONLY EXPLORATORY DATA ANALYSIS

## 1. Phase identity

```text
Project: Practice_3
Phase: 3
Name: TRAIN-only Exploratory Data Analysis
Design status: APPROVED
Human approval: GRANTED
Implementation authorization: GRANTED
Execution status: PASS — AWAITING HUMAN REVIEW
```

## 2. Mục tiêu

Phân tích development period để hiểu quality, distribution, trend, seasonality, temporal dependence và anomaly candidates trước khi thiết kế feature.

```text
validated prepared data
→ apply approved development mask
→ verify holdout isolation
→ calculate TRAIN-only summaries
→ create deterministic figures
→ record bounded feature hypotheses
```

Phase này không tạo modeling feature, không xây dựng X/y, không fit transformer, không train model, không prediction và không tính holdout metric.

## 3. Approved input boundary

Canonical data input:

```text
datasets/processed/aep_hourly_prepared.csv
SHA256: 5b61ab66e585ba479233e7a5597fa42fc5f73bc54c46317b1408bd7a65cab587
```

Canonical split evidence:

```text
config/temporal_split.json
outputs/results/phase_02_temporal_split.json
```

EDA input chỉ gồm development mask đã được Phase 2 khóa:

```text
Start inclusive: 2004-10-01 01:00:00
End exclusive: 2017-08-03 00:00:00
Timeline rows: 112,535
Observed targets: 112,509
Missing targets: 26
```

Historical holdout không thuộc EDA input:

```text
Start inclusive: 2017-08-03 00:00:00
End inclusive: 2018-08-03 00:00:00
Rows excluded from EDA: 8,761
```

Pipeline phải dừng nếu prepared identity hoặc Phase 2 split evidence không khớp approved contracts.

## 4. Holdout isolation contract

Mọi EDA statistic và figure phải được tạo sau khi lấy development subset. Trước model lock, Phase 3 không được:

- tính holdout mean, median, quantile hoặc distribution;
- quan sát holdout trend, seasonality, correlation hoặc anomaly;
- dùng holdout để chọn lag, rolling window hoặc calendar feature;
- hiển thị holdout target trong notebook hoặc official figure;
- ghi holdout target-derived evidence vào Phase 3 JSON.

Phase 3 chỉ được giữ structural statement từ Phase 2 rằng holdout tồn tại và đã bị loại khỏi EDA.

## 5. Missing-data analysis

Giữ toàn bộ 112,535 development timestamps. Không impute hoặc nén timeline.

Phân tích gồm:

- tổng target thiếu trong development;
- danh sách missing timestamps;
- missing count theo year và month;
- xác nhận missing rows giữ `quality_flag = missing_timestamp` và `source_count = 0`;
- xác nhận observed target vẫn finite và positive.

Missing targets không được dùng trong descriptive statistic, correlation, anomaly score hoặc aggregation denominator ngoài hành vi bỏ qua `NaN` được ghi rõ.

## 6. Distribution analysis

Trên 112,509 observed development targets, tính:

```text
count
mean
standard deviation
minimum
Q01
Q05
Q25
median
Q75
Q95
Q99
maximum
IQR
```

Official distribution figure gồm histogram và boxplot của development target. Figure chỉ mô tả dữ liệu; không tự động quyết định scaling, clipping hoặc target transformation.

## 7. Trend analysis

Hourly series quá dày để trình bày toàn bộ một cách rõ ràng. Approved trend view:

```text
Daily aggregation: mean of observed hourly targets
Smoothing: trailing 30-day rolling mean on daily means
Rolling minimum periods: 30 complete daily observations
Centered window: false
```

Official trend figure phải thể hiện daily mean và trailing 30-day rolling mean. Rolling series này chỉ dùng cho EDA presentation, không trở thành feature của Phase 4.

Không extrapolate, detrend hoặc difference target trong Phase 3.

## 8. Seasonality analysis

Tạo development-only profiles:

1. Mean target theo hour-of-day `0–23`.
2. Mean target theo day-of-week `Monday–Sunday`.
3. Mean target theo month `January–December`.
4. Heatmap mean target theo `day-of-week × hour-of-day`.

Mỗi group summary phải lưu cả observed count để tránh diễn giải mean mà không biết sample support.

Seasonality profiles chỉ tạo giả thuyết cho Phase 4. Không được xem group mean là feature hoặc imputation value.

## 9. Temporal-dependence analysis

Approved lag range:

```text
Minimum lag: 1 hour
Maximum lag: 168 hours
Highlighted lags: 1, 24, 168
```

Với mỗi lag `k`, tính pairwise Pearson correlation giữa:

```text
y(t) và y(t-k)
```

Alignment phải giữ hourly timeline. Chỉ loại cặp mà một trong hai target là missing; không dùng `dropna()` trên toàn series trước khi shift vì thao tác đó sẽ nén khoảng cách thời gian.

Audit phải lưu correlation và valid-pair count của từng lag. Phase 3 không tính PACF hoặc ADF trong core scope vì workflow dùng tree-based Machine Learning, không phải ARIMA order identification.

## 10. Robust anomaly screening

Anomaly screening chỉ dùng để nhận biết candidate, không dùng để sửa target.

Approved grouping:

```text
calendar year × hour-of-week
hour-of-week = day-of-week × 24 + hour-of-day
```

Trong mỗi group, tính median và median absolute deviation (MAD). Modified robust score:

```text
score = 0.6745 × (value - group_median) / group_MAD
candidate if abs(score) > 3.5
```

Policy cho group có `MAD = 0` hoặc không đủ observed support:

- không chia cho zero;
- anomaly status là `not_evaluable`;
- không tự động coi observation là anomaly.

Minimum observed support cho một group phải được khóa trong `config/eda.json`; đề xuất mặc định là 20 observations.

Official result chỉ lưu candidate count, candidate rate, group coverage và một danh sách giới hạn các candidate có absolute score cao nhất để audit. Không xóa, clip, winsorize hoặc thay đổi target.

## 11. Approved figures

```text
outputs/figures/phase_03_trend.png
outputs/figures/phase_03_distribution.png
outputs/figures/phase_03_seasonality_profiles.png
outputs/figures/phase_03_hour_day_heatmap.png
outputs/figures/phase_03_lag_correlation.png
outputs/figures/phase_03_anomaly_screening.png
```

Figure requirements:

- dùng non-interactive backend;
- title, axis label, unit và development boundary rõ ràng;
- không chứa holdout target;
- layout không bị cắt;
- deterministic với cùng input/config;
- mỗi figure phải được đóng sau khi lưu;
- không dùng notebook làm figure owner.

## 12. Official result contract

```text
outputs/results/phase_03_eda_summary.json
```

JSON phải chứa ít nhất:

- phase và contract version;
- prepared input path và SHA256;
- split-audit identity;
- development boundary và counts;
- explicit holdout-excluded statement;
- missingness summary;
- distribution statistics;
- daily trend summary;
- hour/day/month seasonality tables và counts;
- lag correlation từ 1 đến 168 và valid-pair counts;
- highlighted lag values;
- anomaly-screening method, threshold, support và result counts;
- bounded feature hypotheses;
- official figure paths và SHA256;
- validation checks và final status.

JSON không được chứa holdout target statistics hoặc model recommendation dựa trên holdout.

## 13. Bounded feature hypotheses

EDA chỉ được ghi candidate hypotheses dưới dạng có giới hạn, ví dụ:

- short-term lags có thể hữu ích nếu lag correlation tương ứng cao;
- daily lag có thể hữu ích nếu lag 24 thể hiện dependence;
- weekly lag có thể hữu ích nếu lag 168 thể hiện dependence;
- hour/day/month calendar features có thể hữu ích nếu profiles khác nhau rõ ràng;
- rolling features cần được thiết kế time-safe trong Phase 4.

Phase 3 không được tự động chốt feature list. Mọi feature vẫn phải được thiết kế và Human duyệt trong Phase 4.

## 14. Proposed implementation ownership

```text
config/eda.json
src/practice_3_v2/analysis/eda.py
tests/test_eda.py
outputs/results/phase_03_eda_summary.json
outputs/figures/phase_03_*.png
docs/logs/PHASE_03_EXECUTION.md
```

Proposed functions:

```text
load_phase_03_inputs
extract_development_data
validate_development_data
summarize_missingness
summarize_distribution
build_daily_trend
build_seasonality_profiles
calculate_lag_correlations
screen_robust_anomalies
build_phase_03_audit
render_phase_03_figures
save_phase_03_artifacts
run_phase_03
```

Source code, identifier, exception và docstring dùng tiếng Anh. Không import runtime code hoặc official output từ legacy `practice_3`.

## 15. Dependency boundary

Phase 3 cần bổ sung tối thiểu:

```text
matplotlib
```

NumPy và pandas đã có trong core environment. Không cần seaborn hoặc statsmodels cho approved scope; lag correlation được tính bằng aligned pandas series.

Dependency phải được khai báo trong optional group phù hợp trước khi chạy official Phase 3.

## 16. Test contract

Focused tests phải kiểm tra:

1. Prepared input và Phase 2 audit tồn tại, status PASS và checksum khớp.
2. Development extraction có đúng 112,535 rows và 26 missing targets.
3. Development timestamps đúng boundary, unique, tăng dần và hourly continuous.
4. Không có holdout timestamp trong EDA input.
5. Thay mọi holdout target bằng extreme values không làm Phase 3 scientific result thay đổi.
6. Missing timestamps không bị impute hoặc nén timeline.
7. Distribution statistics dùng đúng 112,509 observed targets.
8. Daily aggregation và trailing 30-day rolling policy đúng contract.
9. Hour/day/month profiles có đầy đủ category và observed counts.
10. Heatmap có shape `7 × 24` khi đủ support.
11. Lag correlations giữ hourly alignment và có đủ lag `1–168`.
12. Highlighted lags đúng `1`, `24`, `168`.
13. Synthetic missing gap không bị nén khi tính lag correlation.
14. MAD zero và low-support group được xử lý an toàn.
15. Anomaly screening không sửa input target.
16. Official JSON không chứa holdout-derived target statistics.
17. Figures tồn tại, không rỗng và có checksum được ghi trong audit.
18. Repeated execution tạo cùng scientific JSON fields và figure bytes hoặc approved deterministic rendering identity.
19. Invalid checksum, boundary hoặc split status làm pipeline dừng.
20. Không có runtime import từ legacy `practice_3`.

Trước bàn giao phải chạy focused tests, full v2 regression suite và `git diff --check`.

## 17. Atomic artifact policy

Official JSON và figures phải được tạo trong temporary staging directory:

```text
calculate TRAIN-only evidence in memory
→ render staged figures
→ validate staged figures and checksums
→ write and reload staged JSON
→ validate complete staged bundle
→ promote official artifacts
```

Nếu bất kỳ validation nào thất bại, không promote partial Phase 3 bundle.

## 18. Notebook boundary

Notebook chỉ đọc official Phase 3 JSON và figures sau khi Phase 3 PASS. Notebook không được:

- chạy EDA source logic;
- tính lại statistics;
- tạo lại figures;
- truy cập holdout target;
- trở thành owner của scientific result.

## 19. Completion gate

Phase 3 chỉ được đánh dấu `PASS` khi:

- `config/eda.json` đã được Human duyệt;
- source owner và focused tests đã tồn tại;
- development-only isolation test PASS;
- official JSON và six figures được tạo qua atomic promotion;
- không có holdout-derived EDA evidence;
- focused tests và full regression suite PASS;
- execution log và current status được đồng bộ;
- Human review kết quả Phase 3.

Sau Phase 3 mới được thiết kế Phase 4 — Feature Engineering.

## 20. Presentation extension

Theo Human approval, phần trình bày EDA được mở rộng để người xem hiểu dữ liệu
trước khi đọc Feature Engineering. Extension không thay đổi canonical Phase 3
audit và không làm mất hiệu lực checksum mà Phase 4–9 đang tham chiếu.

```text
src/practice_3_v2/analysis/eda_presentation.py
outputs/results/phase_03_eda_presentation.json
outputs/figures/phase_03_annual_stability.png
tests/test_eda_presentation.py
```

Presentation evidence bổ sung:

- data profile và Development boundary;
- data-quality recap từ Phase 1 và Phase 3;
- descriptive statistics đầy đủ;
- annual mean, annual standard deviation và coverage theo năm;
- Top 10 lag correlations;
- Top 10 robust anomaly candidates;
- bảng nối phát hiện EDA với feature đã được Phase 4 xác nhận.

Năm 2004 và 2017 là partial years nên phải được đánh dấu khi diễn giải annual
stability. Extension chỉ dùng Development và phải ghi rõ
`holdout_target_values_inspected = false`.
