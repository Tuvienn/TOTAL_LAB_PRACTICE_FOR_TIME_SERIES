# EXERCISE 04 — ACF/PACF VÀ NHẬN DIỆN ARIMA CANDIDATE

## 1. Thông tin bài tập

```text
Practice: Practice_2
Exercise ID: EXERCISE_04
Topic: ACF/PACF and ARIMA Candidate Identification
Dataset: Monthly Retail Sales
Input: Stationary log first-differenced training series from E03
Inherited transformation: natural_log
Inherited regular differencing order: d = 1
Model training required: NO
Specification status: APPROVED
Current execution result: COMPLETED_AND_VALIDATED
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_04_execution.md
```

Specification này định nghĩa yêu cầu khoa học của E04. Nó không cho phép triển khai
code, chỉnh notebook, tạo output hoặc mở handoff sang E05 khi chưa có Human approval.

## 2. Mục tiêu

Mục tiêu của bài tập:

- phân tích ACF và PACF của stationary training series do E03 bàn giao;
- nhận diện temporal dependence tại các lag ngắn và lag mùa vụ;
- trả lời ACF/PACF có cutoff, decay hoặc pattern nào đáng chú ý;
- đề xuất candidate `p` và `q` dựa trên actual evidence;
- kế thừa `natural_log` và `d = 1` từ E03;
- bàn giao từ một đến hai provisional ARIMA candidates cho E05.

Exercise 4 không fit model, không tính AIC/BIC, không kiểm tra residuals, không
forecast và không mở test set.

## 3. Input contract

```text
Source: E03 scientific handoff
Original training observations: 163
Transformation: natural logarithm
Regular differencing order: 1
Analysis series: log_first_differenced_training
Expected transformed observations: 162
Expected remaining missing values: 0
Expected first timestamp: second timestamp of the original training series
Expected last timestamp: last timestamp of the original training series
Test observations: 41, sealed and excluded
Stationarity evidence: ADF reject H0 at alpha 0.05
```

E04 không được dùng full series, raw first-differenced series, `df_diff1` từ notebook
legacy hoặc bất kỳ test observation nào.

## 4. Các bước bắt buộc

1. Verify E03 completion, transformation metadata, selected `d` và sealed test set.
2. Reproduce đúng log first-differenced training series bằng approved reusable logic.
3. Validate identity, length, timestamps, missing values và stationarity handoff.
4. Tính ACF đến lag 36 với confidence interval 95%.
5. Tính PACF đến lag 36 bằng `method="ywm"` với confidence interval 95%.
6. Tạo machine-readable tables gồm lag, correlation, confidence interval và significant flag.
7. Vẽ combined ACF/PACF figure và inspect actual output.
8. Phân tích các lag ngắn cùng lag mùa vụ 12, 24 và 36.
9. Đề xuất từ một đến hai provisional ARIMA `(p,1,q)` candidates trên log scale.
10. Ghi rationale, limitation và E05 handoff mà không tuyên bố final model.

## 5. Phương pháp khoa học

ACF/PACF phải được tính trên stationary transformed training series. Lag 0 có thể
được giữ trong output kỹ thuật nhưng không được dùng để chọn `p` hoặc `q`.

Candidate interpretation phải xem đồng thời:

```text
significant short lags
cutoff or gradual decay pattern
agreement or disagreement between ACF and PACF
remaining seasonal-lag structure
sample size and uncertainty
```

ACF thường cung cấp evidence cho MA order `q`; PACF thường cung cấp evidence cho AR
order `p`. Đây chỉ là heuristic để đề xuất candidates, không phải proof rằng candidate
là model tốt nhất. Final model cần E05 fitting, convergence, AIC/BIC, residuals và
out-of-sample evaluation.

## 6. Tham số khoa học

```text
Input series: log_first_differenced_training
Expected observations: 162
ACF maximum lag: 36
PACF maximum lag: 36
Confidence level: 95%
Alpha: 0.05
PACF method: ywm
Lag 0 in p/q interpretation: NO
Seasonal reference lags: 12, 24, 36
Inherited analysis scale: natural_log
Inherited regular differencing: d = 1
Candidate count: 1–2
Test set usage: NO
Model fitting: NO
Forecast generation: NO
SARIMA identification: NOT IN E04
```

## 7. Output dự kiến

```text
outputs/figures/03_acf_pacf_log_first_differenced.png
outputs/results/acf_log_first_differenced.csv
outputs/results/pacf_log_first_differenced.csv
outputs/results/arima_candidates.csv
```

ACF/PACF result schema tối thiểu:

```text
lag
correlation
ci_lower
ci_upper
significant
```

Candidate result schema tối thiểu:

```text
candidate
p
d
q
analysis_scale
acf_evidence
pacf_evidence
status
```

Execution result phải được truy vết qua `docs/logs/exercise_04_execution.md` và
`docs/status/current_status.md`; specification này không thay thế execution evidence.

## 8. Câu hỏi diễn giải

1. ACF có cutoff, decay hoặc pattern nào đáng chú ý?
2. PACF có cutoff, decay hoặc pattern nào đáng chú ý?
3. Những lag ngắn nào có evidence đáng kể?
4. Các lag 12, 24 và 36 có cho thấy seasonal dependence còn lại không?
5. Candidate `p` và `q` nào được ACF/PACF hỗ trợ?
6. Một hay hai ARIMA `(p,1,q)` candidates nào nên chuyển sang E05?
7. Evidence nào chưa đủ để chốt final model?

Không được trả lời bằng expected pattern hoặc kết quả notebook legacy trước khi
actual E04 tables và figure được tạo, inspect.

## 9. Tiêu chí xác nhận

```text
[x] E03 handoff và selected d được xác minh
[x] Analysis input đúng log first-differenced training series
[x] Input có đúng 162 observations và không có missing values
[x] Test observations không xuất hiện trong E04 input
[x] ACF và PACF dùng maximum lag 36
[x] Confidence level là 95%
[x] PACF method là ywm
[x] Significant flag khớp confidence interval
[x] Lag 0 không được dùng để chọn p/q
[x] Seasonal lags 12, 24 và 36 được inspect
[x] Figure và machine-readable tables được tạo, inspect
[x] Candidate count nằm trong khoảng 1–2
[x] Mỗi candidate kế thừa natural_log và d = 1
[x] Mỗi candidate có traceable ACF/PACF rationale
[x] Candidates được ghi là provisional
[x] Không fit model, forecast hoặc mở test set
[x] Không fabricate lag evidence hoặc candidate result
```

## 10. Điều kiện dừng

Phải dừng nếu E03 handoff không tái tạo được, input không phải log first-differenced
training series, có test leakage, missing/alignment sai, stationarity evidence không
còn đạt, ACF/PACF computation fail, parameters cần đổi, hoặc không có candidate nào
có rationale truy vết được.

Khi dừng: `STOP → document issue → explain impact → propose next action → wait for approval`.

## 11. Điều kiện hoàn thành

```text
E03 input identity validated
AND ACF/PACF executed with approved parameters
AND tables and figure inspected
AND short and seasonal lags interpreted from actual evidence
AND one or two provisional candidates recorded
AND no test leakage
AND no unresolved blocking issue
```

## 12. Vai trò đối với bước sau

Khi completion gate đạt, E04 bàn giao cho E05:

```text
analysis series identity
natural_log transformation
d = 1
ACF/PACF configuration and actual evidence
one or two provisional ARIMA candidates
remaining seasonal-dependence limitation when present
```

E04 không chọn final model. E05 phải fit candidates, kiểm tra convergence,
AIC/BIC, residuals và đánh giá trên sealed test set cùng approved baseline.

## 13. Approval gate

```text
EXERCISE_04_SPECIFICATION_CREATED=true
EXERCISE_04_SPECIFICATION_REVIEWED=true
EXERCISE_04_SPECIFICATION_APPROVED=true
EXERCISE_04_IMPLEMENTATION_AUTHORIZED=true
```
