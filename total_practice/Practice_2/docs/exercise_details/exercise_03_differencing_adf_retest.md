# EXERCISE 03 — DIFFERENCING AND ADF RETEST

## 1. Exercise Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_03
Topic: Differencing and ADF Retest
Dataset: Monthly Retail Sales
Input: Original training series and E02 ADF result
Transformation protocol: raw first difference, then approved log + first difference remediation
Regular differencing order tested: 1
Significance level: 0.05
Model training required: NO
Specification status: APPROVED
Current execution result: COMPLETED_WITH_LOG_TRANSFORMATION
Downstream gate: OPEN_FOR_E04_REVIEW
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_03_execution.md
```

## 2. Objective

Mục tiêu của bài tập:

- giữ raw first-difference failure làm evidence;
- áp dụng natural-log transformation trên original training series đã xác nhận dương;
- thực hiện regular first difference trên log-transformed working series;
- vẽ transformed differenced series;
- chạy ADF remediation và kết luận stationarity;
- xác định transformation cùng giá trị `d` từ actual evidence.

Exercise 3 không chạy ACF/PACF, không fit model và không forecast.

## 3. Input

```text
Original training series from Exercise 1
ADF result and stationarity conclusion from Exercise 2
Test set: sealed and excluded
Approved transformation: natural logarithm
Regular differencing: first order
Significance level α: 0.05
```

Log transformation và sai phân chỉ áp dụng trên working copy của training series.
Giá trị `NaN` phát sinh từ sai phân đầu tiên được xử lý trong working series, không
ghi ngược vào raw file.

## 4. Required Steps

1. Verify E02 ADF result và original training-series handoff.
2. Xác minh failed raw first-difference evidence.
3. Xác minh mọi training values đều dương rồi tạo log first-differenced series.
4. Vẽ transformed differenced time-series plot.
5. Chạy ADF với `α = 0.05`, `regression="c"`, `autolag="AIC"`.
6. Ghi statistic, p-value, critical values và metadata.
7. Chỉ xác định transformation=`natural_log` và `d=1` khi evidence đạt; nếu chưa đạt thì ghi `REVIEW_REQUIRED` và dừng.

## 5. Scientific Method

ADF remediation phải chạy trên log first-differenced training series, không chạy trên
test set hoặc raw data đã bị thay đổi.

```text
p-value ≤ 0.05 → reject H₀ → evidence supports stationarity on transformed train
p-value > 0.05 → fail to reject H₀ → remediation chưa đủ evidence stationarity
```

Giá trị `d` phải được xác định từ stationarity evidence, không hard-code trước kết quả.

## 6. Scientific Parameters

```text
Transformation: natural logarithm
Regular differencing order tested: 1
Seasonal differencing: not introduced
ADF significance level α: 0.05
Regression: constant (`regression="c"`)
Lag selection: AIC (`autolag="AIC"`)
Input: original training series
Test set usage: NO
Model training: NO
Forecast generation: NO
```

## 7. Expected Outputs

```text
outputs/figures/02_first_differenced_series.png
outputs/figures/02_log_first_differenced_series.png
outputs/results/adf_differenced_series.csv
outputs/results/adf_differenced_critical_values.csv
outputs/results/adf_log_first_differenced_series.csv
outputs/results/adf_log_first_differenced_critical_values.csv
outputs/results/e03_transformation_comparison.csv
outputs/results/differencing_decision.csv
```

Narrative output phải phân biệt raw first-difference failure với log first-difference
remediation, ghi analysis scale và trả lời `d` bằng bao nhiêu. Nếu evidence chưa đủ,
câu trả lời hợp lệ là `selected_d = REVIEW_REQUIRED`.

Execution result phải được truy vết qua `docs/logs/exercise_03_execution.md` và
`docs/status/current_status.md`; specification này không thay thế execution evidence.

## 8. Interpretation Questions

1. Vì sao raw first difference chưa đạt stationarity gate?
2. Log first-differenced training series đã dừng chưa?
3. ADF statistic và p-value remediation cho evidence gì?
4. Transformation và `d` đã xác định được chưa?

Không được trả lời trước khi differenced plot và ADF result được tạo, inspect.

## 9. Validation Criteria

```text
[x] E02 result và original training series được xác minh
[x] Raw failed attempt được giữ làm evidence
[x] Mọi training values được xác nhận dương trước log
[x] Log transformation và first differencing chỉ áp dụng trên training working copy
[x] Raw data không bị sửa
[x] Transformed differenced plot được tạo và inspect
[x] ADF remediation chạy trên log first-differenced training series
[x] α = 0.05
[x] Regression option được ghi là `c`
[x] Autolag được ghi là `AIC`
[x] ADF statistic, p-value và critical values được ghi
[x] Analysis scale được ghi rõ
[x] Stationarity sau remediation có evidence
[x] Transformation và `d` được xác định từ actual result
[x] Không dùng test set
[x] Không fit model hoặc forecast
```

## 10. Stop Conditions

Phải dừng nếu E02 chưa validated, input không phải original training series, test
leakage xảy ra, có giá trị không dương, log/differencing fail, ADF fail, remediation
chưa stationary hoặc cần đổi parameter/scope.

Khi dừng: `STOP → document issue → explain impact → propose next action → wait for approval`.

## 11. Execution Completion và Scientific Handoff

### 11.1. Execution Completion

```text
raw failed evidence preserved
AND log first-differenced series created
AND plot inspected
AND ADF remediation executed
AND stationarity conclusion documented
AND d decision recorded from actual evidence
```

Execution có thể hoàn thành về mặt kỹ thuật dù kết quả khoa học tạo blocker.

### 11.2. Scientific Handoff Gate

Chỉ mở handoff sang Exercise 4 khi:

```text
stationary log first-differenced training series supported by evidence
AND transformation and d selected with evidence
AND no unresolved scientific blocker
```

Nếu gate chưa đạt, Exercise 3 giữ trạng thái `BLOCKED_BY_SCIENTIFIC_RESULT`,
`selected_d = REVIEW_REQUIRED` và Exercise 4 không được bắt đầu.

## 12. Downstream Role

Khi Scientific Handoff Gate đạt, Exercise 3 cung cấp log first-differenced stationary
training series, transformation metadata và selected `d` cho Exercise 4 — ACF/PACF
and ARIMA Candidate Identification. Nếu gate chưa đạt, downstream handoff vẫn đóng.
