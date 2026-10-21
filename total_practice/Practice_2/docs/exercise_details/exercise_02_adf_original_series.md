# EXERCISE 02 — KIỂM ĐỊNH ADF TRÊN CHUỖI GỐC

## 1. Thông tin bài tập

```text
Practice: Practice_2
Exercise ID: EXERCISE_02
Topic: ADF on Original Series
Dataset: Monthly Retail Sales
Input: Original training series from Exercise 1
Significance level: 0.05
Model training required: NO
Specification status: APPROVED
Execution state owner: docs/status/current_status.md
Execution evidence: docs/logs/exercise_02_execution.md
```

## 2. Mục tiêu

Mục tiêu của bài tập:

- thực hiện Augmented Dickey-Fuller test trên chuỗi gốc;
- ghi ADF statistic, p-value và critical values;
- giải thích null hypothesis của ADF;
- áp dụng decision rule với `α = 0.05`;
- kết luận chuỗi gốc dừng hay không dừng;
- tạo evidence cho Exercise 3.

Exercise 2 không differencing, không chọn `d`, không chạy ACF/PACF và không fit model.

## 3. Dữ liệu đầu vào

```text
Source: validated original training series from Exercise 1
Dataset: datasets/raw/a10.csv
Time column: date
Target column: value
Test set: sealed and excluded
Significance level α: 0.05
```

ADF phải chạy trên original untransformed training series, không chạy trên full series
khi test observations đã bị sealed và không chạy trên differenced series.

## 4. Các bước bắt buộc

1. Verify Exercise 1 handoff, training boundary và sealed test set.
2. Load original training series từ validated working representation.
3. Chạy ADF với significance level `α = 0.05`.
4. Ghi ADF statistic, p-value, critical values, số lag và số observations nếu output cung cấp.
5. Giải thích `H₀`: chuỗi có unit root, tức là không stationary.
6. So sánh p-value với `α = 0.05` và đưa ra decision.
7. Kết luận original training series là stationary hoặc non-stationary.
8. Lưu actual result và narrative interpretation.

## 5. Phương pháp khoa học

ADF kiểm tra null hypothesis rằng chuỗi có unit root. Với `α = 0.05`:

```text
p-value ≤ 0.05 → reject H₀ → evidence supports stationarity
p-value > 0.05 → fail to reject H₀ → insufficient evidence of stationarity
```

“Fail to reject” không được diễn giải thành proof tuyệt đối rằng chuỗi non-stationary.
Kết luận phải dựa trên actual ADF output.

## 6. Tham số khoa học

```text
Test: Augmented Dickey-Fuller
Input: original training series
Significance level α: 0.05
Regression: constant (`regression="c"`)
Lag selection: AIC (`autolag="AIC"`)
Test set usage: NO
Differencing: NO
Model training: NO
Forecast generation: NO
```

## 7. Output dự kiến

```text
outputs/results/adf_original_series.csv
outputs/results/adf_original_critical_values.csv
```

Result tối thiểu phải có:

```text
ADF statistic
p-value
critical values
significance level
used lag / observations when available
stationarity decision
```

Narrative output phải trả lời đúng ba câu hỏi của đề.

Execution result phải được truy vết qua `docs/logs/exercise_02_execution.md` và
`docs/status/current_status.md`; specification này không thay thế execution evidence.

## 8. Câu hỏi diễn giải

1. `H₀` của ADF là gì?
2. p-value cho biết điều gì?
3. Chuỗi gốc có dừng không với `α = 0.05`?

Không được viết kết luận trước khi actual ADF result được tạo và inspect.

## 9. Tiêu chí xác nhận

```text
[ ] Exercise 1 handoff được xác minh
[ ] ADF chạy trên original training series
[ ] Test set không được sử dụng
[ ] Significance level α = 0.05
[ ] Regression option được ghi là `c`
[ ] Autolag được ghi là `AIC`
[ ] ADF statistic được ghi
[ ] p-value được ghi
[ ] Critical values được ghi
[ ] H₀ được giải thích đúng
[ ] Decision rule được áp dụng đúng
[ ] Stationarity conclusion truy vết được về output
[ ] Không differencing hoặc model fitting
[ ] Không fabricate statistical result
```

## 10. Điều kiện dừng

Phải dừng nếu Exercise 1 chưa có validated training series, test leakage xảy ra,
ADF input không đúng original series, ADF computation fail, output thiếu thông tin
cần thiết, significance level cần đổi ngoài specification hoặc dependency/scope cần mở rộng.

Khi dừng: `STOP → document issue → explain impact → propose next action → wait for approval`.

## 11. Điều kiện hoàn thành

```text
original training series validated
AND ADF executed successfully
AND statistic/p-value/critical values recorded
AND H₀ and p-value explained
AND stationarity conclusion documented
AND output inspected
AND no unresolved blocking issue
```

## 12. Vai trò đối với bước sau

Kết quả E2 cung cấp stationarity evidence cho E3 — Differencing và kiểm định lại
ADF. E2 không tự chọn `d` và không xác nhận ARIMA model.
