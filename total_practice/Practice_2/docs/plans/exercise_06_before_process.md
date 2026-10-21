# EXERCISE 06 — KẾ HOẠCH TRƯỚC KHI THỰC THI

## 1. Thông tin kế hoạch

```text
Practice: Practice_2
Exercise ID: EXERCISE_06
Topic: AirPassengers ARIMA Baseline and SARIMA Extension
Plan type: Exercise Before-Process Plan
Dataset: AirPassengers
Status: REVIEWED_RESIDUAL_FIX_SCOPE_APPROVED
Implementation authorized: RESIDUAL_FIX_SCOPE_ONLY
Scientific dependency: independent Dataset 2 workflow
Process gate: EXERCISE_05_COMPLETED
Downstream gate: CLOSED_PENDING_E06_VALIDATION
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_06_execution.md
```

File này chỉ mô tả kế hoạch chi tiết cho E06. Việc tạo plan không cho phép triển khai
code, chỉnh notebook, tạo output hoặc cập nhật trạng thái E06 khi chưa hoàn thành E05,
chưa review lại reusable interfaces và chưa có Human approval riêng cho E06.

## 2. Mục tiêu

- sử dụng AirPassengers để thực hành mô hình hóa chuỗi có seasonality 12 tháng;
- validate dữ liệu và tạo chronological holdout riêng cho E06;
- kiểm tra stationarity trên training series;
- kiểm chứng regular differencing và seasonal differencing bằng evidence;
- dùng ACF/PACF của transformed training series để đề xuất ARIMA/SARIMA candidates;
- fit một non-seasonal ARIMA baseline và một SARIMA trên cùng evaluation setup;
- kiểm tra convergence và residuals của hai model;
- forecast cùng test horizon và so sánh bằng MAE/RMSE;
- kết luận giới hạn trong AirPassengers holdout, không dùng kết quả của Dataset 1.

## 3. Quan hệ với E1–E5

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

## 4. Tài liệu bắt buộc

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

## 5. Dataset contract

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

## 6. Holdout và leakage contract

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

## 7. Tham số khoa học

### 7.1. Stationarity và differencing

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

### 7.2. Quyết định scale

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

### 7.4. So sánh model

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

## 8. File tạm thời được phép tạo hoặc chỉnh sửa

Chỉ sau khi E05 hoàn thành và E06 plan được Human phê duyệt, E06 dự kiến được phép
tạo hoặc cập nhật:

```text
docs/exercise_details/exercise_06_sarima_extension.md, only when Human requests it
docs/plans/exercise_06_before_process.md
approved existing modules under src/practice_2/data/
approved existing modules under src/practice_2/analysis/
approved existing modules under src/practice_2/visualization/
tests/test_exercise_06.py
notebooks/Practice_2_advanced_sarima.ipynb
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

## 9. File không được chỉnh sửa

```text
datasets/raw/a10.csv
datasets/raw/airline-passengers.csv
working_rule.md
AGENTS.md
.agents/ rules and workflows
approved Practice_2 rule files
E01–E05 validated evidence and outputs
notebooks/Practice2_latest.ipynb
README.md before the approved final-documentation stage
unrelated Practice/Lab files
```

Nếu cần sửa E01–E05 hoặc thay đổi architecture để hoàn thành E06:
`STOP → giải thích lý do và tác động → đề xuất cập nhật phạm vi → chờ phê duyệt`.

## 10. Các bước thực thi tuần tự

### Bước 0 — Xác minh entry gate

Xác minh E05 đã completed và được Human duyệt, required documents đã đọc, E06 plan
đã approved và reusable interfaces đã được review. Nếu chưa đạt thì không code.

### Bước 1 — Nạp và kiểm tra AirPassengers

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

### Bước 2 — Tạo và niêm phong holdout E6

Tạo chronological split 115/29, xác nhận boundary và niêm phong test values. Lưu
machine-readable split metadata, không lưu test information vào candidate-selection
artifacts.

### Bước 3 — Kiểm tra cấu trúc train và chọn scale

Vẽ training series, nhận diện trend, annual seasonality và variance behavior. Chọn
raw hoặc natural-log scale chỉ từ training evidence và ghi rationale.

### Bước 4 — Chạy ADF trên train gốc

Chạy ADF trên training series ở approved scale. Ghi null hypothesis, statistic,
p-value, critical values, used lag, nobs, regression, autolag và decision.

### Bước 5 — Đánh giá regular và seasonal differencing

Tạo và kiểm tra tuần tự:

```text
regular difference: d = 1
seasonal difference: D = 1, s = 12
combined regular-seasonal difference when justified
```

Với mỗi series cần ghi observation count, intentional NaN count, remaining missing
values, timestamp alignment, plot và ADF evidence khi phù hợp. Chốt transformed
training series có đủ stationarity evidence cho model identification.

### Bước 6 — Phân tích ACF/PACF và đề xuất candidate

Tính ACF/PACF trên đúng stationary transformed training series. Inspect short lags
và seasonal lags 12, 24, 36; đề xuất số lượng candidate nhỏ, có rationale cho
`(p,q,P,Q)`. Không dùng order từ Dataset 1 hoặc test performance.

### Bước 7 — Fit ARIMA baseline trên AirPassengers

Fit approved non-seasonal ARIMA candidate trên full E06 training set ở approved
scale. Capture convergence, warnings, AIC, BIC và residuals.

### Bước 8 — Fit SARIMA candidate

Fit approved SARIMA candidate với `s = 12` trên cùng training set và scale. Capture
convergence, warnings, AIC, BIC và residuals. Không bỏ qua fitting failure.

### Bước 9 — Chạy residual diagnostics

Với cả hai model, kiểm tra residual mean, residual plot, residual ACF và Ljung–Box.
Kết luận residual structure từ actual statistical evidence, không chỉ từ hình.

### Bước 10 — Forecast và đánh giá trên cùng holdout

Sau khi model selection đã khóa, mở test set và forecast đúng 29 bước. Xác nhận
forecast index bằng test index trước khi tính MAE/RMSE và optional MAPE. Lưu forecast
và error theo từng timestamp.

### Bước 11 — So sánh ARIMA và SARIMA

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

### Bước 12 — Cập nhật advanced notebook riêng

Trình bày E06 trong `Practice_2_advanced_sarima.ipynb` với cấu trúc ngắn:

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
`Practice_2_present.ipynb` giữ phạm vi core E01–E05 và không chứa cell E06.

### Bước 13 — Xác nhận và ghi evidence

Chạy targeted tests, relevant full tests và notebook từ clean kernel. Inspect CSV,
figures, forecast alignment, notebook outputs và raw checksum. Chỉ sau khi tất cả
validation đạt mới tạo execution log và cập nhật current status.

## 11. Kế hoạch kiểm thử

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
[ ] Core notebook remains limited to E01–E05 and its existing cells remain unchanged
[ ] E01–E05 validated evidence remains unchanged
```

## 12. Output bắt buộc của phạm vi formal

Machine-readable evidence dự kiến:

```text
AirPassengers validation and split metadata
ADF and differencing results
ACF/PACF evidence and model candidates
ARIMA/SARIMA fit diagnostics
aligned test forecasts and actual values
MAE/RMSE comparison
```

Visual evidence dự kiến:

```text
original/training AirPassengers series
approved differenced training series
ACF/PACF of stationary transformed training data
residual diagnostics for both models
same-horizon ARIMA/SARIMA forecast comparison
```

## 13. Tiêu chí nghiệm thu

```text
[x] E5 đã hoàn thành và reusable interface đã được review
[ ] Full E6 implementation được Human phê duyệt tường minh
[x] AirPassengers contract và checksum đã được xác nhận trong exploratory run
[x] Test set được niêm phong tới final evaluation
[x] Scale decision chỉ dùng training evidence
[x] d, D và s có evidence truy vết được
[x] ACF/PACF chỉ dùng approved transformed training data
[x] ARIMA và SARIMA candidate có rationale tường minh
[x] Hai model dùng cùng training setup đã chốt
[x] Convergence, AIC/BIC và residual diagnostics được ghi lại
[x] Forecast horizon và test index giống nhau
[x] MAE/RMSE dùng cùng test observation
[x] Comparison conclusion được actual evidence hỗ trợ
[x] Test đạt
[x] Notebook chạy từ kernel sạch, không có lỗi
[x] Output exploratory khớp giá trị notebook
[x] Raw file và evidence E1–E5 không đổi
```

## 14. Điều kiện dừng

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

## 15. Rủi ro và biện pháp kiểm soát

| Rủi ro | Biện pháp kiểm soát |
|---|---|
| Dùng toàn bộ 144 observations trước split | Split và seal test ngay sau validation |
| Kế thừa model order từ Dataset 1 | Xác định order lại bằng AirPassengers training evidence |
| Tự động áp dụng `d=1, D=1` | Kiểm chứng từng differencing step và ghi ADF evidence |
| So sánh model khác scale hoặc horizon | Khóa common evaluation contract trước fitting |
| Multiplicative variance bị bỏ qua | Training-only scale decision gate |
| Chọn order quá chắc chắn từ ACF/PACF | Dùng ít candidates và yêu cầu fit/residual evidence |
| SARIMA quá phức tạp với 115 training points | Giới hạn candidate count và theo dõi convergence |
| Residual được kết luận bằng mắt | Bắt buộc Ljung–Box cùng residual plot/ACF |
| Output notebook cũ gây nhầm lẫn | Core E01–E05 ở `Practice_2_present.ipynb`; E06 chỉ ở `Practice_2_advanced_sarima.ipynb` |
| Kết luận quá mức từ một holdout | Giới hạn conclusion trong dataset và split hiện tại |

## 16. Handoff formal completion của E6

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

Formal E6 completion hiện không được mở vì Human chọn Phương án A. Exploratory
evidence của E6 không thay thế, sửa lại hoặc che lấp trạng thái của E1–E5.

## 17. Approval gate

```text
EXERCISE_06_BEFORE_PROCESS_CREATED=true
EXERCISE_06_BEFORE_PROCESS_REVIEWED=true
EXERCISE_06_BEFORE_PROCESS_APPROVED=false
EXERCISE_06_IMPLEMENTATION_AUTHORIZED=false
EXERCISE_06_RESIDUAL_FIX_SCOPE_APPROVED=true
EXERCISE_06_RESIDUAL_FIX_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_06_WAITING_FOR_E05=false
EXERCISE_06_IMPLEMENTED=false
EXERCISE_06_VALIDATED=false
EXERCISE_06_COMPLETED=false
```
