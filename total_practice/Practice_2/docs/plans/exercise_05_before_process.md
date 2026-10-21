# EXERCISE 05 — KẾ HOẠCH TRƯỚC KHI THỰC THI

## 1. Thông tin kế hoạch

```text
Practice: Practice_2
Exercise ID: EXERCISE_05
Topic: ARIMA Training, Residual Diagnostics, Forecasting and Evaluation
Plan type: Exercise Before-Process Plan
Dataset: Monthly Retail Sales
Status: COMPLETED_AND_VALIDATED
Implementation authorized: YES
Previous notebook execution: retained as exploratory history and formally rerun
Upstream handoff: E04 COMPLETED_AND_VALIDATED
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_05_execution.md
```

Kế hoạch này quản lý việc review và xác nhận E5 theo cách tái tạo được. Output cũ
trong notebook chỉ là exploratory evidence và không tự tạo quyền implementation
hoặc trạng thái formal completion. E5 hiện đã được Human review và hoàn thành.

## 2. Mục tiêu

- Xác minh chronological holdout E1 và candidate handoff E4.
- Fit một hoặc hai ARIMA candidate đã phê duyệt chỉ trên train.
- So sánh từng candidate với seasonal-naive baseline có lag 12.
- Kiểm tra convergence, fitting warning, AIC/BIC và residual diagnostics.
- Forecast sealed test horizon và đánh giá MAE, RMSE, MAPE.
- Trả lời câu hỏi E5 từ execution evidence đã kiểm tra.
- Đồng bộ formal status trước khi đánh dấu hoàn thành.

E5 chỉ bao phủ ARIMA trên Monthly Retail Sales. SARIMA trên AirPassengers thuộc E6.

## 3. Tài liệu bắt buộc

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
total_practice/Practice_2/docs/exercise_details/exercise_05_arima_forecasting_evaluation.md
total_practice/Practice_2/docs/exercise_details/exercise_04_acf_pacf_arima_candidates.md
total_practice/Practice_2/docs/plans/exercise_04_before_process.md
E01–E04 validated evidence, execution logs, and outputs
notebooks/Practice_2_present.ipynb
```

Nếu upstream evidence thiếu hoặc approval/status mâu thuẫn, phải dừng và báo sai lệch
trước khi formal execution hoặc completion.

## 4. Entry gate và trạng thái hiện tại

E4 đã hoàn thành với hai provisional candidate. Human phê duyệt E5 implementation
plan ngày 2026-10-20. Lần chạy notebook trước đó được giữ như exploratory history;
formal result được tạo lại từ reusable source và verified artifact.

```text
Previous E05 notebook run: exploratory history
Formal E04 handoff state: completed and open for E05
E05 specification approval: approved
E05 plan approval: approved
Formal E05 state: completed and validated
```

## 5. Input contract từ bước trước

```text
Dataset: datasets/raw/a10.csv
Validated observations: 204
Training observations: 163
Test observations: 41
Train period: 1991-07 through 2005-01
Test period: 2005-02 through 2008-06
Frequency: monthly start (MS)
Split: chronological 80/20
Shuffle: false
Transformation: natural_log
Selected regular differencing order: d = 1
E04 handoff: one or two provisional ARIMA(p,1,q) candidates with rationale
Test set: sealed until final evaluation
```

ARIMA fit trên chuỗi **level** train sau natural-log transformation và nhận `d=1`
trong model. Chuỗi E3 đã log-difference chỉ dùng cho stationarity evidence và nhận
diện order ở E4; không fit ARIMA có `d=1` trên chuỗi đã differencing đó.

Phải dùng chính xác split E1. Không sort, repair, fill, interpolate, resample hoặc
sửa raw CSV trong kế hoạch này.

## 6. Tham số khoa học và đánh giá

```text
Analysis scale: natural_log
ARIMA d: 1, inherited from E03
ARIMA trend policy: no drift (`trend='n'`)
Candidate count: 1–2, inherited from E04
Seasonal-naive period: 12
Forecast horizon: 41
Forecast metric scale: original sales scale
Required metrics: MAE, RMSE, MAPE
Residual significance level: 0.05
Residual diagnostics: mean, time plot, ACF, Ljung–Box
```

Inverse transformation từ log prediction về original sales scale phải tường minh và
nhất quán giữa các candidate. Policy được khóa trước khi xem test metric. Nếu actual
bằng 0, MAPE không xác định và phải được báo cáo, không silently drop.

## 7. File được phép tạo hoặc chỉnh sửa

```text
docs/exercise_details/exercise_05_arima_forecasting_evaluation.md
docs/plans/exercise_05_before_process.md
docs/error_analysis/exercise_05_notebook_alignment_issue.md
src/practice_2/analysis/forecasting.py
src/practice_2/analysis/__init__.py
src/practice_2/visualization/plots.py
tests/test_exercise_05.py
notebooks/Practice_2_present.ipynb
outputs/figures/05_arima_residual_diagnostics.png
outputs/figures/05_arima_forecast_comparison.png
outputs/results/05_arima_fit_summary.csv
outputs/results/05_arima_residual_diagnostics.csv
outputs/results/05_arima_forecasts.csv
outputs/results/05_arima_metrics.csv
docs/logs/exercise_05_execution.md
docs/status/current_status.md
```

Phải dùng owner và interface sẵn có; không tạo module model, diagnostic,
visualization hoặc metric trùng trách nhiệm.

## 8. File không được chỉnh sửa

```text
datasets/raw/a10.csv
datasets/raw/airline-passengers.csv
working_rule.md
AGENTS.md
.agents/rules/ and .agents/workflows/
approved Practice_2 rule files
E01–E04 validated source logic, outputs, and execution evidence
notebooks/Practice2_latest.ipynb
E06 implementation, outputs, or execution evidence
README.md before the approved final-documentation stage
unrelated Practice/Lab files
```

Nếu cần chỉnh file ngoài phạm vi, thay split/dataset/metric hoặc mở rộng architecture:

```text
STOP → giải thích lý do và tác động → đề xuất scope update → chờ approval
```

## 9. Các bước thực thi tuần tự

### Bước 0 — Xác minh approval và trạng thái

Xác nhận E4 formal validation và E5 approval. Không tự nâng exploratory notebook
output thành formal result.

### Bước 1 — Xác minh dataset và boundary E1

```text
rows = 204
train observations = 163
test observations = 41
train end = 2005-01
test start = 2005-02
train end < test start
chronological order = true
shuffle = false
```

Giữ raw file bất biến. Dừng nếu schema, date range, frequency, missing value,
duplicate hoặc monthly continuity khác contract.

### Bước 2 — Xác minh handoff E3/E4

Tái tạo natural-log và first-difference transformation bằng reusable logic đã duyệt.
Xác nhận `d=1`, 162 transformed observations, không còn missing value và timestamp
alignment đúng. Candidate E4 phải giới hạn 1–2 order có training-only ACF/PACF rationale.

### Bước 3 — Khóa model và evaluation setup

Trước khi mở test:

- khóa candidate order và rationale từ E4;
- khóa seasonal-naive period 12;
- khóa training series và log-scale fit input;
- ghi inverse-log policy;
- khóa test horizon và metric definition.

Không dùng test metric để thêm, xóa hoặc thay candidate.

### Bước 4 — Fit baseline và ARIMA candidate

Tạo seasonal-naive forecast chỉ từ train. Fit mỗi ARIMA candidate trên log-transformed
training levels với `d=1` và `trend='n'`. Ghi convergence, warning/failure, AIC và
BIC; không silently discard warning hoặc failed candidate.

### Bước 5 — Kiểm tra residual diagnostics

```text
residual mean
residual time plot
residual ACF and confidence level
Ljung–Box statistic, p-value, lag, model_df, and alpha
```

Loại `loglikelihood_burn` trước khi tính residual evidence. Không suy ra white noise
chỉ từ residual mean hoặc visual plot. Nếu còn autocorrelation, vẫn hoàn thành required
comparison nhưng không tuyên bố final model diagnostically adequate.

### Bước 6 — Forecast và đánh giá

- Forecast đúng 41 tháng cho từng candidate và baseline.
- Assert forecast index bằng test index.
- Chuyển forecast về original sales scale theo policy đã khóa.
- Tính MAE, RMSE, MAPE trên cùng 41 actual/forecast pair.
- Tính absolute error theo timestamp và lấy maximum của từng model.
- Kiểm tra Train/Test/Forecast figure và metric table.

Không dùng forecast lệch index hoặc so sánh metric khác scale/horizon.

### Bước 7 — Trả lời câu hỏi E5

1. Vì sao không shuffle và test set dùng để làm gì?
2. `p`, `d`, `q` biểu diễn điều gì?
3. Từng model có hội tụ và phát sinh warning không?
4. Residual có hỗ trợ kết luận white noise không?
5. Nếu còn residual autocorrelation, cần nghiên cứu gì tiếp?
6. Forecast có bám test-period behavior không?
7. Largest error của mỗi model ở đâu?
8. Metric nào nhạy nhất với lỗi lớn và vì sao?
9. RMSE quan sát được có ý nghĩa gì theo đơn vị target?

Kết luận chỉ áp dụng cho Monthly Retail Sales và holdout hiện tại. Không tuyên bố
model hữu ích chỉ vì AIC/BIC thấp hơn.

### Bước 8 — Ghi evidence và cập nhật trạng thái

Cập nhật execution log bằng input identity, split, parameter, warning, diagnostics,
forecast, metrics, largest error và validation result. Chỉ ghi verified state vào
`current_status.md`.

## 10. Kế hoạch test và validation

```text
[x] E04 candidate handoff and E05 approval state reviewed
[x] Dataset schema, monthly continuity, and raw immutability verified
[x] E01 split reproduced exactly as 163/41 with no shuffle
[x] Test data excluded from order selection and model fitting
[x] E03 natural-log transform and selected d=1 reproduced
[x] ARIMA fitted on log(training levels), avoiding double differencing
[x] No-drift policy is explicit in source, notebook, and fit evidence
[x] One or two candidate orders traceable to E04 evidence
[x] Seasonal-naive baseline uses lag 12 and training-only history
[x] Convergence, warnings, AIC, and BIC recorded per candidate
[x] Residual mean, plot, ACF, and Ljung–Box inspected
[x] Forecast horizon is 41 and forecast index equals test index
[x] Inverse transformation is explicit and consistent
[x] MAE, RMSE, and MAPE use the same original-scale holdout pairs
[x] Largest-error timestamp is computed from aligned errors
[x] Candidate comparison includes seasonal-naive baseline
[x] Canonical setup + E05 runs from a clean kernel without E06
[x] Required outputs are inspected against notebook values
[x] Execution log and status update match verified evidence
[x] E01–E04 and E06 artifacts remain unchanged
```

## 11. Điều kiện dừng

Dừng và báo Human nếu E4 handoff/approval chưa rõ, dataset contract hoặc split sai,
có test leakage, không tái tạo được E3 transformation, candidate thiếu rationale,
model không hội tụ, diagnostics/alignment không tái tạo được, metric scale không rõ
hoặc cần thay đổi ngoài approved scope.

## 12. Rủi ro và biện pháp kiểm soát

| Rủi ro | Biện pháp kiểm soát |
|---|---|
| Nhầm exploratory run là formal result | Đối chiếu approval và status trước completion |
| E4 candidate artifact lệch handoff | Đọc trực tiếp approved E4 CSV |
| Double differencing ARIMA input | Fit `ARIMA(log(train levels), order=(p,1,q))` |
| Test leakage khi chọn candidate | Khóa order và evaluation setup trước khi mở test |
| So sánh thiếu baseline | Bổ sung seasonal-naive lag 12 |
| Che giấu inverse-log bias | Ghi policy và limitation |
| Suy ra white noise chỉ từ plot | Dùng Ljung–Box và ghi lag/alpha |
| Forecast/actual lệch timestamp | Assert exact index equality trước metrics |
| MAPE không xác định khi actual bằng 0 | Kiểm tra target và báo trường hợp undefined |
| Trình bày stale notebook output | Clean-run và kiểm tra output mới |

## 13. Handoff hoàn thành E5

```text
E01–E04 handoffs and approvals reconciled
AND ARIMA candidates and seasonal-naive baseline evaluated
AND convergence and residual evidence recorded
AND forecast indices match the 41-observation test horizon
AND MAE/RMSE/MAPE are reproducible on the same observations
AND required questions answered from actual evidence
AND tests and clean-kernel validation pass
AND execution log and status reflect verified state
AND Human review completed
```

## 14. Approval gate

```text
EXERCISE_05_BEFORE_PROCESS_CREATED=true
EXERCISE_05_BEFORE_PROCESS_REVIEWED=true
EXERCISE_05_BEFORE_PROCESS_APPROVED=true
EXERCISE_05_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_05_IMPLEMENTED=true
EXERCISE_05_VALIDATED=true
EXERCISE_05_COMPLETED=true
```
