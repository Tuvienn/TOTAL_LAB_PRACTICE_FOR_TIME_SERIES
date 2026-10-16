# EXERCISE 03 — DIFFERENCING AND ADF RETEST

## 1. Exercise Identity

```text
Practice: Practice_2
Exercise ID: EXERCISE_03
Topic: Differencing and ADF Retest
Dataset: Monthly Retail Sales
Input: Original training series and E02 ADF result
Differencing order tested: 1
Significance level: 0.05
Model training required: NO
Status: PLANNED
```

## 2. Objective

Mục tiêu của bài tập:

- thực hiện sai phân bậc 1 trên original training series;
- tạo differenced working series mà không sửa raw data;
- vẽ lại chuỗi sau sai phân;
- chạy ADF lần 2 trên differenced series;
- kết luận sau sai phân chuỗi đã dừng chưa;
- xác định và giải thích giá trị `d` trong ARIMA.

Exercise 3 không chạy ACF/PACF, không fit model và không forecast.

## 3. Input

```text
Original training series from Exercise 1
ADF result and stationarity conclusion from Exercise 2
Test set: sealed and excluded
Differencing: first order only
Significance level α: 0.05
```

Sai phân chỉ áp dụng trên working copy của training series. Giá trị `NaN` phát sinh
trực tiếp từ sai phân đầu tiên được xử lý trong working series, không ghi ngược vào raw file.

## 4. Required Steps

1. Verify E02 ADF result và original training-series handoff.
2. Tạo first-differenced series từ training series.
3. Vẽ differenced time-series plot.
4. Chạy ADF lần 2 với `α = 0.05`.
5. Ghi ADF statistic, p-value, critical values và metadata khi có.
6. Kết luận sau sai phân chuỗi đã stationary chưa.
7. Xác định `d`: nếu first difference đạt stationarity theo evidence thì `d = 1`; nếu chưa đạt thì không tự tăng differencing, phải ghi issue và chờ protocol tiếp theo.

## 5. Scientific Method

ADF lần 2 phải chạy trên differenced training series, không chạy trên test set hoặc
raw data đã bị thay đổi.

```text
p-value ≤ 0.05 → reject H₀ → evidence supports stationarity after differencing
p-value > 0.05 → fail to reject H₀ → first difference chưa đủ evidence stationarity
```

Giá trị `d` phải được xác định từ stationarity evidence, không hard-code trước kết quả.

## 6. Scientific Parameters

```text
Differencing order tested: 1
ADF significance level α: 0.05
Input: original training series
Test set usage: NO
Model training: NO
Forecast generation: NO
```

## 7. Expected Outputs

```text
outputs/figures/02_first_differenced_series.png
outputs/results/adf_differenced_series.csv
outputs/results/differencing_decision.csv
```

Narrative output phải trả lời: sau sai phân chuỗi đã dừng chưa và `d` bằng bao nhiêu.

## 8. Interpretation Questions

1. Sau sai phân bậc 1, chuỗi đã dừng chưa?
2. ADF statistic và p-value lần 2 cho evidence gì?
3. Giá trị `d` trong ARIMA là bao nhiêu và vì sao?
4. Nếu first difference chưa stationary thì cần dừng lại ở đâu thay vì tự đổi protocol?

Không được trả lời trước khi differenced plot và ADF result được tạo, inspect.

## 9. Validation Criteria

```text
[ ] E02 result và original training series được xác minh
[ ] First differencing chỉ áp dụng trên working copy
[ ] Raw data không bị sửa
[ ] Differenced plot được tạo và inspect
[ ] ADF lần 2 chạy trên differenced training series
[ ] α = 0.05
[ ] ADF statistic, p-value và critical values được ghi
[ ] Stationarity sau differencing có evidence
[ ] d được xác định từ actual result
[ ] Không dùng test set
[ ] Không fit model hoặc forecast
```

## 10. Stop Conditions

Phải dừng nếu E02 chưa validated, input không phải original training series, test
leakage xảy ra, differencing fail, ADF lần 2 fail, first difference chưa stationary
nhưng protocol chưa được duyệt để tiếp tục, hoặc cần đổi parameter/scope.

Khi dừng: `STOP → document issue → explain impact → propose next action → wait for approval`.

## 11. Completion Condition

```text
first differenced series created
AND plot inspected
AND ADF retest executed
AND stationarity conclusion documented
AND d justified by actual evidence
AND no unresolved blocking issue
```

## 12. Downstream Role

Kết quả Exercise 3 cung cấp stationary training series và selected `d` cho Exercise 4
— ACF/PACF and ARIMA Candidate Identification.
