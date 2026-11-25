# EXERCISE 06 — BEFORE-PROCESS PLAN

## 1. Plan Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_06
Topic: AirPassengers ARIMA Baseline and SARIMA Extension
Plan type: Exercise Before-Process Plan
Dataset: AirPassengers
Status: APPROVED_FOR_IMPLEMENTATION
Implementation authorized: YES
Scientific dependency: independent Dataset 2 workflow
Process gate: EXERCISE_05_COMPLETED
Downstream gate: CLOSED_PENDING_E06_VALIDATION
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_06_execution.md
```

File này mô tả kế hoạch chi tiết cho E06. Human đã duyệt scope để triển khai; E06
chỉ được ghi completed sau khi clean-kernel validation và evidence review đạt.

## 2. Objective

- sử dụng AirPassengers để thực hành mô hình hóa chuỗi có seasonality 12 tháng;
- validate dữ liệu và tạo chronological holdout riêng cho E06;
- kiểm tra stationarity trên training series;
- kiểm chứng regular differencing và seasonal differencing bằng evidence;
- dùng ACF/PACF của transformed training series để đề xuất ARIMA/SARIMA candidates;
- fit một non-seasonal ARIMA baseline và một SARIMA trên cùng evaluation setup;
- kiểm tra convergence và residuals của hai model;
- forecast cùng test horizon và so sánh bằng MAE/RMSE;
- kết luận giới hạn trong AirPassengers holdout, không dùng kết quả của Dataset 1.

## 3. Relationship with E01–E05

```text
E01–E05 dataset: datasets/raw/a10.csv
E06 dataset: datasets/raw/airline-passengers.csv
Direct data dependency: NO
Reuse of Dataset 1 model orders or metrics: PROHIBITED
Methodological reuse: YES
Reusable source/API reuse after E05: REQUIRED WHEN COMPATIBLE
Recommended execution order: E04 → E05 → E06
```

E06 độc lập về dữ liệu, split, stationarity evidence, model identification và metrics.
E06 không được kế thừa `d`, `p`, `q`, transformation, fitted model hoặc kết luận từ
E01–E05. E06 chỉ tái sử dụng các reusable utilities đã được E05 kiểm chứng nếu các
utility đó phù hợp với contract của AirPassengers.

## 4. Required Documents

```text
working_rule.md
AGENTS.md
.agents/RULES_INDEX.md
.agents/rules/GENERAL_RULES.md
.agents/rules/CODE_RULES.md
.agents/rules/TIME_SERIES_RULES.md
.agents/workflows/WORKFLOW.md
total_practice/Practice_2/README.md
total_practice/Practice_2/docs/rules/architecture_rule.md
total_practice/Practice_2/docs/rules/rule_code.md
total_practice/Practice_2/docs/plans/project_overview.md
total_practice/Practice_2/docs/plans/plan_overview.md
total_practice/Practice_2/docs/status/current_status.md
approved E05 specification/plan/log when they exist
```

Nếu thiếu tài liệu, E05 chưa hoàn thành, reusable interface chưa ổn định hoặc có
conflict: `STOP → report issue → chờ Human quyết định`.

## 5. Dataset Contract

```text
Source file: datasets/raw/airline-passengers.csv
Dataset identity: AirPassengers — Monthly Airline Passengers
Timestamp column: Month
Timestamp format: YYYY-MM
Target column: Passengers
Target meaning: monthly airline passenger count
Expected rows: 144
Expected date range: 1949-01 through 1960-12
Expected frequency: monthly start (MS)
Seasonal period: 12
Expected missing target values: 0
Expected duplicate timestamps: 0
Expected missing monthly intervals: 0
Raw SHA-256: 8cb51be753a718d9be5d76d7e238cc224792754676adc21faa59e954b0201621
Raw file mutability: immutable
```

Mọi parse, sort, split, transformation và differencing chỉ được thực hiện trên object
trong bộ nhớ hoặc approved derived artifacts. Không sửa hoặc ghi đè raw CSV.

## 6. Holdout and Leakage Contract

```text
Split method: chronological 80/20
Shuffle: false
Expected training observations: 115
Expected training period: 1949-01 through 1958-07
Expected test observations: 29
Expected test period: 1958-08 through 1960-12
Test usage before final evaluation: prohibited
Model identification data: training only
Model fitting data: training only
Forecast horizon: exactly 29 monthly observations
```

Các bước EDA dùng để quyết định transformation, ADF, differencing, ACF/PACF,
candidate selection và model fitting không được đọc test values. Test set chỉ được
mở sau khi model candidates và evaluation protocol đã khóa.

## 7. Scientific Parameters

### 7.1. Stationarity and Differencing

```text
ADF alpha: 0.05
ADF regression: c
ADF autolag: AIC
Suggested regular differencing: d = 1, must be verified
Suggested seasonal differencing: D = 1, must be verified
Seasonal period: s = 12
Over-differencing: prohibited
NaN handling: drop only intentional leading NaN values created by differencing
```

`d = 1` và `D = 1` là gợi ý của đề, không phải kết luận có sẵn. E06 phải ghi evidence
trên training series và không tăng differencing order chỉ để ép p-value xuống dưới
0.05.

### 7.2. Scale Decision

AirPassengers có thể có variance tăng theo level. E06 phải đánh giá training series
trước khi chốt analysis scale:

```text
Allowed primary scale: raw or natural_log
Scale decision source: training evidence only
Same scale for ARIMA and SARIMA comparison: required
Inverse transformation policy: explicit and identical for both models
Silent scale switching: prohibited
```

Exact log/inverse-transform implementation chỉ được chốt sau khi E05 reusable
forecast interface đã được review.

### 7.3. ACF/PACF

```text
Maximum lag: 36
Confidence level: 95%
Alpha: 0.05
PACF method: ywm
Lag 0: excluded from order interpretation
Seasonal reference lags: 12, 24, 36
Input: approved stationary transformed training series only
```

ACF/PACF chỉ cung cấp candidate evidence. Không tự động chứng minh một order là final.

### 7.4. Model Comparison

```text
Baseline model: non-seasonal ARIMA(p,d,q) on AirPassengers training data
Seasonal model: SARIMA(p,d,q)(P,D,Q,12) on the same training data
Candidate selection from test metrics: prohibited
Required fit evidence: convergence, warnings, AIC, BIC
Required residual evidence: residual mean, residual plot, residual ACF, Ljung–Box
Ljung–Box alpha: 0.05
Reference diagnostic lags: 12 and 24 when statistically valid
Required forecast metrics: MAE and RMSE
Optional supplementary metric: MAPE
```

Primary comparison nên giữ cùng non-seasonal structure và analysis scale khi evidence
cho phép để đánh giá tác động của seasonal terms. Nếu hai model cần non-seasonal order
khác nhau, plan phải được cập nhật với rationale trước khi fit.

## 8. Provisional Files Allowed to Create or Modify

Chỉ sau khi E05 hoàn thành và E06 plan được Human phê duyệt, E06 dự kiến được phép
tạo hoặc cập nhật:

```text
docs/exercise_details/exercise_06_sarima_extension.md, only when Human requests it
docs/plans/exercise_06_before_process.md
approved existing modules under src/practice_2/data/
approved existing modules under src/practice_2/analysis/
approved existing modules under src/practice_2/visualization/
tests/test_exercise_06.py
notebooks/Practice_2_Advanced.ipynb (E06 draft notebook only; not execution evidence)
outputs/figures/06_airpassengers_original_series.png
outputs/figures/06_airpassengers_differencing.png
outputs/figures/06_airpassengers_acf_pacf.png
outputs/figures/06_airpassengers_residual_diagnostics.png
outputs/figures/06_airpassengers_forecast_comparison.png
outputs/results/06_airpassengers_validation.csv
outputs/results/06_airpassengers_split.csv
outputs/results/06_airpassengers_adf_results.csv
outputs/results/06_airpassengers_model_candidates.csv
outputs/results/06_airpassengers_model_diagnostics.csv
outputs/results/06_airpassengers_forecasts.csv
outputs/results/06_airpassengers_metrics.csv
docs/logs/exercise_06_execution.md
docs/status/current_status.md
```

Exact source files và public function signatures chưa được chốt trong draft này. Sau
E05 phải ưu tiên mở rộng reusable owner hiện có, không tạo duplicate modeling,
diagnostic hoặc metric modules.

## 9. Files Not to Modify

```text
datasets/raw/a10.csv
datasets/raw/airline-passengers.csv
working_rule.md
AGENTS.md
.agents/ rules and workflows
approved Practice_2 rule files
E01–E05 validated evidence and outputs
historical Practice2_latest.ipynb reference (not present in the current repository)
README.md before the approved final-documentation stage
unrelated Practice/Lab files
```

Nếu cần sửa E01–E05 hoặc thay đổi architecture để hoàn thành E06:
`STOP → explain reason and impact → propose scope update → wait for approval`.

## 10. Sequential Execution Steps

### Step 0 — Verify Entry Gate

Xác minh E05 đã completed và được Human duyệt, required documents đã đọc, E06 plan
đã approved và reusable interfaces đã được review. Nếu chưa đạt thì không code.

### Step 1 — Load and Validate AirPassengers

Load raw CSV qua approved data owner và kiểm tra:

```text
schema
timestamp format and dtype
target numeric type
chronological order
duplicate timestamps
missing values
monthly continuity
date range
row count
raw checksum
```

Không silently repair input contract failure.

### Step 2 — Create and Seal E06 Holdout

Tạo chronological split 115/29, xác nhận boundary và niêm phong test values. Lưu
machine-readable split metadata, không lưu test information vào candidate-selection
artifacts.

### Step 3 — Inspect Training Structure and Select Scale

Vẽ training series, nhận diện trend, annual seasonality và variance behavior. Chọn
raw hoặc natural-log scale chỉ từ training evidence và ghi rationale.

### Step 4 — Run Original-Training ADF

Chạy ADF trên training series ở approved scale. Ghi null hypothesis, statistic,
p-value, critical values, used lag, nobs, regression, autolag và decision.

### Step 5 — Evaluate Regular and Seasonal Differencing

Tạo và kiểm tra tuần tự:

```text
regular difference: d = 1
seasonal difference: D = 1, s = 12
combined regular-seasonal difference when justified
```

Với mỗi series cần ghi observation count, intentional NaN count, remaining missing
values, timestamp alignment, plot và ADF evidence khi phù hợp. Chốt transformed
training series có đủ stationarity evidence cho model identification.

### Step 6 — Analyze ACF/PACF and Propose Candidates

Tính ACF/PACF trên đúng stationary transformed training series. Inspect short lags
và seasonal lags 12, 24, 36; đề xuất số lượng candidate nhỏ, có rationale cho
`(p,q,P,Q)`. Không dùng order từ Dataset 1 hoặc test performance.

### Step 7 — Fit AirPassengers ARIMA Baseline

Fit approved non-seasonal ARIMA candidate trên full E06 training set ở approved
scale. Capture convergence, warnings, AIC, BIC và residuals.

### Step 8 — Fit SARIMA Candidate

Fit approved SARIMA candidate với `s = 12` trên cùng training set và scale. Capture
convergence, warnings, AIC, BIC và residuals. Không bỏ qua fitting failure.

### Step 9 — Run Residual Diagnostics

Với cả hai model, kiểm tra residual mean, residual plot, residual ACF và Ljung–Box.
Kết luận residual structure từ actual statistical evidence, không chỉ từ hình.

### Step 10 — Forecast and Evaluate on the Same Holdout

Sau khi model selection đã khóa, mở test set và forecast đúng 29 bước. Xác nhận
forecast index bằng test index trước khi tính MAE/RMSE và optional MAPE. Lưu forecast
và error theo từng timestamp.

### Step 11 — Compare ARIMA and SARIMA

So sánh trên cùng observations, horizon, scale và metric implementation. Báo cáo:

```text
which model has lower MAE
which model has lower RMSE
whether seasonal timing is represented better
largest-error timestamp for each model
residual limitations
whether SARIMA improvement is supported on this holdout
```

Không dùng từ ngữ tuyệt đối như “hoàn toàn vượt trội” hoặc suy rộng ngoài setup.

### Step 12 — Update E06 Draft Notebook

Thêm E06 vào `Practice_2_Advanced.ipynb` với cấu trúc ngắn. Notebook này chỉ là
draft cho E06 và không là evidence completion cho đến khi entry gate, approval và
validation đều hoàn tất:

```text
# Exercise 6 — Mở rộng SARIMA với AirPassengers
### 1. Dữ liệu và holdout riêng
### 2. Stationarity và differencing
### 3. ACF/PACF và candidates
### 4. ARIMA và SARIMA diagnostics
### 5. Forecast và so sánh
### 6. Kết luận E06
```

Notebook chỉ điều phối và trình bày kết quả/biểu đồ cần thiết; reusable logic thuộc
package. Không sao chép nội dung dài từ plan, rules hoặc notebook legacy.

### Step 13 — Validate and Record Evidence

Chạy targeted tests, relevant full tests và notebook từ clean kernel. Inspect CSV,
figures, forecast alignment, notebook outputs và raw checksum. Chỉ sau khi tất cả
validation đạt mới tạo execution log và cập nhật current status.

## 11. Test Plan

Tests tối thiểu:

```text
[ ] Raw AirPassengers checksum is unchanged
[ ] Schema is exactly Month and Passengers
[ ] Datetime parsing uses YYYY-MM semantics
[ ] Series is chronological and monthly continuous
[ ] Missing and duplicate counts are zero
[ ] Split is chronological 115/29 and not shuffled
[ ] Test timestamps are absent from identification inputs
[ ] Original ADF configuration and result schema are complete
[ ] Differencing orders and seasonal period are explicit
[ ] Intentional differencing NaN values are handled correctly
[ ] Transformed timestamps remain aligned
[ ] ACF/PACF uses only stationary transformed training data
[ ] ARIMA and SARIMA use the same train/test boundary and scale
[ ] Both forecasts contain exactly 29 observations
[ ] Forecast indices equal the test index
[ ] MAE and RMSE are calculated on identical observations
[ ] Convergence and fitting warnings are recorded
[ ] Ljung–Box configuration and results are recorded
[ ] Largest-error timestamp is computed, not guessed visually
[ ] Legacy notebook remains unmodified
[ ] E01–E05 validated evidence remains unchanged
```

## 12. Required Outputs

Machine-readable evidence:

```text
AirPassengers validation and split metadata
ADF and differencing results
ACF/PACF evidence and model candidates
ARIMA/SARIMA fit diagnostics
aligned test forecasts and actual values
MAE/RMSE comparison
```

Visual evidence:

```text
original/training AirPassengers series
approved differenced training series
ACF/PACF of stationary transformed training data
residual diagnostics for both models
same-horizon ARIMA/SARIMA forecast comparison
```

## 13. Acceptance Criteria

```text
[ ] E05 is completed and reusable interfaces are reviewed
[ ] E06 implementation receives explicit Human approval
[ ] AirPassengers contract and checksum are validated
[ ] Test set remains sealed until final evaluation
[ ] Scale decision uses training evidence only
[ ] d, D and s have traceable evidence
[ ] ACF/PACF uses only approved transformed training data
[ ] ARIMA and SARIMA candidates have explicit rationale
[ ] Both models fit the same approved training setup
[ ] Convergence, AIC/BIC and residual diagnostics are recorded
[ ] Forecast horizon and test index are identical
[ ] MAE/RMSE use the same test observations
[ ] Comparison conclusion is supported by actual evidence
[ ] Tests pass
[ ] Notebook runs from a clean kernel without errors
[ ] Outputs match notebook values
[ ] Raw files and E01–E05 evidence remain unchanged
```

## 14. Stop Conditions

Phải dừng E06 nếu:

- E05 chưa hoàn thành hoặc reusable interfaces chưa ổn định;
- dataset checksum, schema, date range hoặc frequency không khớp contract;
- xuất hiện missing interval, duplicate timestamp hoặc invalid target chưa có protocol;
- test information đã tham gia transformation, order selection hoặc fitting;
- scale hoặc inverse-transformation policy chưa rõ;
- differencing chưa có evidence hoặc có dấu hiệu over-differencing;
- ACF/PACF input chưa stationary theo approved evidence;
- model không hội tụ hoặc fitting warning chưa được xử lý;
- forecast index không khớp test index;
- hai model không dùng cùng evaluation setup;
- cần dependency, architecture hoặc scope mới;
- notebook clean execution hoặc tests thất bại.

Khi dừng:

```text
1. Không tiếp tục dependent step.
2. Ghi observed và expected behavior.
3. Xác định owner và impact.
4. Tạo error analysis/fix plan khi issue không hiển nhiên.
5. Chờ Human approval trước khi sửa.
```

## 15. Risks and Controls

| Risk | Control |
|---|---|
| Dùng toàn bộ 144 observations trước split | Split và seal test ngay sau validation |
| Kế thừa model order từ Dataset 1 | Xác định order lại bằng AirPassengers training evidence |
| Tự động áp dụng `d=1, D=1` | Kiểm chứng từng differencing step và ghi ADF evidence |
| So sánh model khác scale hoặc horizon | Khóa common evaluation contract trước fitting |
| Multiplicative variance bị bỏ qua | Training-only scale decision gate |
| Chọn order quá chắc chắn từ ACF/PACF | Dùng ít candidates và yêu cầu fit/residual evidence |
| SARIMA quá phức tạp với 115 training points | Giới hạn candidate count và theo dõi convergence |
| Residual được kết luận bằng mắt | Bắt buộc Ljung–Box cùng residual plot/ACF |
| Output notebook cũ gây nhầm lẫn | `Practice_2_Exercise.ipynb` là canonical cho core; `Practice_2_Advanced.ipynb` chỉ là E06 draft |
| Kết luận quá mức từ một holdout | Giới hạn conclusion trong dataset và split hiện tại |

## 16. E06 Completion Handoff

E06 chỉ được xem là hoàn thành khi:

```text
validated independent AirPassengers workflow
AND no test leakage
AND stationarity/differencing evidence is traceable
AND ARIMA and SARIMA use the same evaluation setup
AND both models have convergence and residual evidence
AND forecasts are index-aligned
AND MAE/RMSE comparison is reproducible
AND tests and clean notebook execution pass
AND Human reviews the final result
```

E06 completion không thay thế, sửa lại hoặc che lấp trạng thái của E01–E05.

## 17. Approval Gate

```text
EXERCISE_06_BEFORE_PROCESS_CREATED=true
EXERCISE_06_BEFORE_PROCESS_REVIEWED=true
EXERCISE_06_BEFORE_PROCESS_APPROVED=true
EXERCISE_06_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_06_WAITING_FOR_E05=false
EXERCISE_06_IMPLEMENTED=false
EXERCISE_06_VALIDATED=false
EXERCISE_06_COMPLETED=false
```
