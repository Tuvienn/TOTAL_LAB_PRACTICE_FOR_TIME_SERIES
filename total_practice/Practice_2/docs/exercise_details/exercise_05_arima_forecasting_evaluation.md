# EXERCISE 05 — HUẤN LUYỆN, DIAGNOSTICS, FORECAST VÀ ĐÁNH GIÁ ARIMA

## 1. Thông tin bài tập

```text
Practice: Practice_2
Exercise ID: EXERCISE_05
Topic: ARIMA Training, Residual Diagnostics, Forecasting and Evaluation
Dataset: Monthly Retail Sales
Input: E01 chronological holdout + E04 provisional ARIMA candidates
Inherited transformation: natural_log
Inherited regular differencing order: d = 1
Specification status: APPROVED
Implementation authorized: YES
Current execution result: COMPLETED_AND_VALIDATED
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_05_execution.md
```

Specification này định nghĩa contract khoa học và báo cáo của E5. Implementation và
trạng thái hoàn thành chỉ hợp lệ sau khi phạm vi thực thi tương ứng được Human phê
duyệt. Các approval gate này hiện đã đạt.

## 2. Mục tiêu

- Fit một hoặc hai ARIMA candidate do E4 bàn giao.
- So sánh candidate bằng training-fit evidence, convergence, residual diagnostics và
  out-of-sample evaluation.
- So sánh ARIMA forecast với seasonal-naive baseline đã phê duyệt.
- Bảo toàn chronological train/test boundary từ E1.
- Báo cáo MAE, RMSE và MAPE trên original sales scale.
- Xác định forecast error tuyệt đối lớn nhất của từng model.
- Kết luận trong đúng phạm vi holdout và evidence quan sát được.

E5 là bài ARIMA chính. SARIMA trên AirPassengers thuộc E6 nâng cao và không được thêm
vào phạm vi E5.

## 3. Dependency từ các bài trước

```text
E01: validated Monthly Retail Sales + chronological train/test boundary
E02: original-training ADF evidence
E03: natural-log transformation + selected d = 1 + stationarity evidence
E04: ACF/PACF evidence + 1–2 provisional ARIMA candidates
E05: fit + residual diagnostics + forecast + evaluation
```

E5 chỉ bắt đầu sau khi các handoff trước đó và evidence tương ứng được xác nhận.

## 4. Input contract

```text
Source: datasets/raw/a10.csv
Dataset identity: Monthly Retail Sales
Timestamp column: date
Target column: value
Frequency: monthly start (MS)
Expected total observations: 204
Expected training observations: 163
Expected test observations: 41
Expected training period: 1991-07 through 2005-01
Expected test period: 2005-02 through 2008-06
Chronological ordering: required
Shuffle: prohibited
Duplicate timestamps: 0
Missing target values: 0
Missing monthly intervals: 0
```

```text
Analysis scale: natural_log
ARIMA regular differencing order: d = 1
Trend policy: no drift (`trend='n'`)
Model-fit input: log(training level series)
Order-identification input: E03 log-first-differenced training series
Forecast metric scale: original sales scale
```

ARIMA phải fit trên chuỗi **level** của train sau log transformation với `d=1`.
Không đưa chuỗi E3 đã differencing vào ARIMA có `d=1`, vì như vậy sẽ differencing
hai lần. Chuỗi E3 chỉ dùng làm stationarity evidence và input nhận diện order ở E4.

Test set được niêm phong trong E2–E4, scale decision, candidate selection và model
fitting. Chỉ sau khi candidate cùng evaluation protocol đã khóa, test mới được dùng
cho final forecast evaluation.

## 5. Các bước bắt buộc

1. Xác minh evidence hoàn thành E1–E4 và trạng thái approval.
2. Nạp Monthly Retail Sales mà không sửa raw file.
3. Tái tạo và xác nhận split 163/41 theo thời gian từ E1.
4. Xác nhận E2–E4 không sử dụng test observation.
5. Xác nhận natural-log transformation và `d=1` từ E3.
6. Đọc một hoặc hai provisional candidate cùng rationale từ E4.
7. Tạo seasonal-naive baseline chu kỳ 12 chỉ từ train.
8. Fit mỗi candidate trên log-transformed training levels.
9. Ghi convergence, warning, AIC, BIC và no-drift trend policy tường minh.
10. Kiểm tra residual mean, residual time plot, residual ACF và Ljung–Box.
11. Khóa candidate/evaluation setup trước khi mở test.
12. Forecast đúng 41 tháng cho mọi candidate và baseline.
13. Xác nhận forecast timestamp trùng hoàn toàn test index.
14. Inverse log bằng policy đã phê duyệt.
15. Tính MAE, RMSE và MAPE trên cùng original-scale test observation.
16. So sánh candidate với nhau và với seasonal-naive baseline.
17. Tính timestamp và giá trị absolute error lớn nhất của từng model.
18. Trả lời các câu hỏi diễn giải từ actual output.
19. Chỉ cập nhật execution evidence và current status sau khi validation đạt.

## 6. Phương pháp khoa học

### 6.1. Chronological split và bảo vệ holdout

```text
Split method: chronological 80/20
Train observations: 163
Test observations: 41
Shuffle: NO
Model identification data: training only
Model fitting data: training only
Forecast horizon: exactly 41 monthly observations
Test usage: final evaluation only
```

Không tạo split mới trong E5. Mọi test information tham gia transformation, order
selection hoặc thay candidate đều làm evaluation mất hiệu lực và cần quy trình mới
được phê duyệt.

### 6.2. Candidate model

- Chỉ dùng một hoặc hai candidate từ E4 handoff.
- Giữ rationale và `d=1` của từng candidate.
- Không thêm candidate từ test metric.
- Không chọn final model chỉ bằng AIC/BIC.
- Ghi rõ convergence failure hoặc warning; không trình bày failed fit như valid result.

### 6.3. Seasonal-naive baseline

Baseline dùng seasonal lag 12, sinh hoàn toàn từ training series và có cùng horizon
41 tháng. Baseline được đánh giá trên cùng timestamp và original target scale với ARIMA.

### 6.4. Residual diagnostics

Mỗi fitted candidate phải ghi:

```text
residual mean
residual time plot
residual ACF
Ljung–Box test statistic and p-value
Ljung–Box lag(s), model degrees of freedom, and significance level
```

Dùng `alpha=0.05` nếu chưa có protocol khác được phê duyệt. Loại
`loglikelihood_burn` trước diagnostics, chọn lag hợp lệ và ghi rõ. Residual mean gần
0 hoặc visual inspection không đủ để kết luận white noise. Autocorrelation còn lại
ngăn final-model-adequacy claim, nhưng không phủ nhận việc hoàn thành forecast
comparison nếu giới hạn được báo cáo trung thực.

### 6.5. Inverse transformation của forecast

Model fit trên natural-log scale nhưng metrics được báo cáo trên original sales scale.
E5 dùng `exp(predicted log mean)` không bias correction. Giá trị này gần với
conditional median trên thang gốc và có thể thấp hơn conditional mean. Không được
đổi policy sau khi xem test metric.

### 6.6. Evaluation metrics

```text
MAE  = mean absolute error
RMSE = square root of mean squared error
MAPE = mean absolute percentage error × 100
```

Mọi metric dùng cùng actual/forecast index pair. Nếu actual bằng 0, MAPE không xác
định tại quan sát đó; phải báo cáo thay vì silently drop.

## 7. Câu hỏi diễn giải bắt buộc

1. Vì sao không được shuffle chuỗi thời gian và test set dùng để làm gì?
2. `p`, `d`, `q` đã chọn biểu diễn điều gì?
3. Từng model có hội tụ không và có fitting warning không?
4. Residual có evidence white noise không? Residual ACF và Ljung–Box cho biết gì?
5. Nếu còn residual autocorrelation, hướng model nào cần được nghiên cứu tiếp?
6. Forecast có bám observed behavior trong test period không?
7. Absolute error lớn nhất của mỗi model xảy ra tại timestamp nào?
8. Metric nào nhạy với lỗi lớn/outlier nhất và vì sao?
9. RMSE quan sát được có ý nghĩa gì theo đơn vị target?

Phải phân biệt evidence và interpretation; không suy rộng chất lượng forecast ra
ngoài dataset và holdout đã kiểm tra.

## 8. Output dự kiến

```text
outputs/figures/05_arima_residual_diagnostics.png
outputs/figures/05_arima_forecast_comparison.png
outputs/results/05_arima_fit_summary.csv
outputs/results/05_arima_residual_diagnostics.csv
outputs/results/05_arima_forecasts.csv
outputs/results/05_arima_metrics.csv
docs/logs/exercise_05_execution.md
docs/status/current_status.md
```

Không ghi đè evidence E1–E4. Machine-readable forecast output phải giữ model name,
timestamp, actual, forecast và error để tái tạo largest-error claim.

## 9. Tiêu chí xác nhận

```text
[x] E01–E04 handoffs and approval/status state verified
[x] Raw input remains unchanged
[x] Split matches E01: 163 train / 41 test, chronological, no shuffle
[x] Test observations excluded from E02–E04 and all fitting/model selection
[x] E03 natural-log transformation and d=1 are inherited correctly
[x] ARIMA fit uses log(training levels), not an already differenced series with d=1
[x] ARIMA no-drift policy is explicit and reproducible
[x] One or two candidates have traceable E04 rationale
[x] Seasonal-naive baseline uses lag 12 and training-only history
[x] Convergence, warnings, AIC, and BIC are recorded
[x] Residual mean, time plot, ACF, and Ljung–Box are inspected
[x] Evaluation setup is locked before opening test values
[x] Each forecast has exactly 41 observations
[x] Forecast indices equal the test index
[x] Inverse-log policy is explicit and consistent
[x] MAE, RMSE, and MAPE use the same original-scale test observations
[x] Candidates are compared with the seasonal-naive baseline
[x] Largest-error timestamp is computed, not estimated visually
[x] All required questions are answered from actual evidence
[x] Canonical setup + E05 runs from a clean kernel without E06
[x] Outputs are inspected and execution evidence is recorded
```

## 10. Điều kiện dừng

Dừng E5 nếu:

- E4 handoff hoặc candidate rationale thiếu/chưa giải quyết;
- không tái tạo được boundary E1;
- test observation ảnh hưởng fit hoặc candidate selection;
- input scale hay differencing contract không rõ;
- ARIMA không hội tụ hoặc còn fitting warning chưa xử lý;
- residual diagnostics hoặc forecast/test alignment không tái tạo được;
- actual và forecast index khác nhau;
- metric dùng observation hoặc scale không khớp;
- cần dependency, architecture hoặc scope chưa được phê duyệt.

Khi bị chặn:

```text
STOP
→ ghi observed evidence và expected behavior
→ giải thích tác động
→ đề xuất hành động tiếp theo
→ chờ Human phê duyệt khi cần
```

## 11. Điều kiện hoàn thành

```text
upstream handoffs verified
AND chronological holdout preserved
AND approved ARIMA candidates and seasonal-naive baseline fitted
AND convergence and residual evidence recorded
AND forecasts aligned to the 41-observation test horizon
AND MAE/RMSE/MAPE computed on the same original-scale observations
AND candidate/baseline comparison and all questions answered
AND outputs inspected and reproducible
AND execution log and current status updated
AND no unresolved blocking issue
```

## 12. Approval gate

```text
EXERCISE_05_SPECIFICATION_CREATED=true
EXERCISE_05_SPECIFICATION_REVIEWED=true
EXERCISE_05_SPECIFICATION_APPROVED=true
EXERCISE_05_IMPLEMENTATION_AUTHORIZED=true
EXERCISE_05_IMPLEMENTED=true
EXERCISE_05_VALIDATED=true
EXERCISE_05_COMPLETED=true
```
