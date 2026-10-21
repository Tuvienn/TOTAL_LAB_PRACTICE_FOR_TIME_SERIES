# TIME SERIES PRACTICE 02 — QUY TẮC CODE VÀ THỰC THI

## 1. Mục đích và trạng thái

```text
Document ID: TS-PRACTICE-02-CODE-v2.0
Phạm vi: total_practice/Practice_2
Trạng thái: APPROVED_AND_ACTIVE
Ngày đồng bộ: 2026-10-14
```

Workflow bắt buộc:

```text
Read → Understand → Plan → Human Approval → Implement → Run → Verify → Report
```

---

## 2. Phạm vi code

Rule áp dụng cho source code, notebook, tests, data loading, ADF/differencing,
ACF/PACF, ARIMA/SARIMA, residual diagnostics, forecasting, evaluation,
visualization và bug fixes thuộc E01–E06.

Không tự mở rộng sang Machine Learning, Deep Learning, automated tuning hoặc bài
toán ngoài approved plan.

---

## 3. Nguồn yêu cầu

Trước khi code phải đọc các rule cấp repository, `architecture_rule.md`,
`project_overview.md`, `plan_overview.md` và tài liệu Exercise riêng nếu tồn tại.

Approved scope trong `plan_overview.md` đủ làm implementation contract khi Human
không yêu cầu một specification riêng.

---

## 4. Nguyên tắc triển khai

- Chỉ thực hiện một logical change có phạm vi rõ tại một thời điểm.
- Không sửa file không liên quan.
- Reusable/correctness-critical logic đặt trong `src/practice_2/`.
- Notebook dùng để điều phối, trình bày và diễn giải.
- Không duplicate reusable function giữa nhiều notebook/cell.
- Không dùng silent fallback hoặc tự sửa dữ liệu khi contract không khớp.
- Không hard-code absolute machine paths.

---

## 5. Data integrity

- Raw CSV là bất biến.
- Validate schema trước khi phân tích.
- Parse datetime tường minh và sắp xếp theo thời gian.
- Kiểm tra duplicate timestamp, missing value và missing monthly interval.
- Mọi transformation phải tạo object mới hoặc được đặt tên rõ ràng.
- Forecast và actual phải khớp index trước khi tính metric.

---

## 6. Chronological split và leakage

- Không shuffle time series.
- Split E01 được tái sử dụng nhất quán đến E05.
- E02–E04 không được đọc test values để chọn transformation hoặc model order.
- Chỉ fit scaler, transform hoặc model bằng training data nếu chúng học tham số.
- Test set chỉ được mở trong evaluation stage của E05.
- E06 dùng split riêng; ARIMA và SARIMA dùng cùng boundary/horizon.

Nếu test information đã ảnh hưởng model selection, kết quả phải bị vô hiệu hóa và
pipeline phải chạy lại từ boundary hợp lệ.

---

## 7. Quy tắc thống kê

### 7.1 ADF

Phải ghi rõ null hypothesis, significance level, test statistic, p-value, critical
values, regression option và autolag/lag settings. Không kết luận stationarity chỉ
từ plot.

### 7.2 Differencing

Regular/seasonal differencing phải ghi rõ order và seasonal period. Phải loại NaN
phát sinh có chủ đích và giữ đúng timestamp alignment. Không over-difference chỉ
để đạt p-value mong muốn.

### 7.3 ACF/PACF

Chỉ dùng chuỗi đã đạt điều kiện stationarity phù hợp để đề xuất ARIMA orders.
Phải ghi rõ số lag, confidence level và phương pháp PACF. ACF/PACF là evidence để
đề xuất candidate, không tự động chứng minh model tốt nhất.

### 7.4 ARIMA/SARIMA

- Fit trên training data.
- Ghi rõ `(p,d,q)` và `(P,D,Q,s)`.
- Ghi nhận convergence warning hoặc fitting failure; không bỏ qua im lặng.
- So sánh candidates bằng tiêu chí đã chốt và residual evidence.
- E06 dùng `s=12` trừ khi evidence và Human approval thay đổi protocol.

### 7.5 Residual diagnostics

Phải kiểm tra residual plot, residual ACF và Ljung–Box. Không kết luận white noise
chỉ bằng quan sát trực quan. Ghi rõ lag và significance level.

### 7.6 Forecast evaluation

E05 phải có seasonal-naive baseline. Báo cáo tối thiểu MAE và RMSE trên cùng test
horizon. Việc model không thắng baseline vẫn là kết quả hợp lệ và phải được báo cáo.

---

## 8. Notebook

Notebook phải:

- chạy tuần tự từ kernel sạch;
- import package thay vì sửa `sys.path`;
- phân tách Markdown explanation, code và interpretation;
- hiển thị tham số quan trọng;
- không phụ thuộc biến ẩn từ lần chạy trước;
- không chứa secret hoặc path tuyệt đối;
- không trình bày output cũ như bằng chứng của code mới chưa chạy.

---

## 9. Code quality và tests

Function phải có trách nhiệm rõ, tên phản ánh nghiệp vụ và lỗi contract phải có
message dễ hiểu. Type hints/docstrings được dùng cho public hoặc non-trivial logic.

Sau mỗi change:

1. chạy test liên quan;
2. chạy smoke test/import check;
3. chạy notebook hoặc execution path bị ảnh hưởng khi phù hợp;
4. kiểm tra output/index/metric;
5. báo cáo chính xác điều đã và chưa xác minh.

---

## 10. Debug và sửa lỗi

Với lỗi không hiển nhiên:

```text
reproduce → isolate → document evidence → propose fix → obtain approval → fix → regress
```

Sửa tại owner của root cause, không vá downstream symptom. Không xóa hoặc chỉnh
raw data để làm test đi qua.

---

## 11. Không fabricate kết quả

Không được tự tạo p-value, AIC/BIC, coefficients, residual conclusion, forecast,
MAE/RMSE hoặc biểu đồ chưa sinh từ execution. Kết luận lý thuyết phải được ghi rõ
là dự kiến, không phải actual result.

---

## 12. Stop conditions

Dừng và báo Human khi:

- input contract sai hoặc dataset không đọc được;
- timestamp/frequency/alignment không xác định;
- có leakage hoặc test contamination;
- model không hội tụ mà chưa có protocol xử lý;
- dependency hoặc environment không tái tạo được;
- approved plan và implementation yêu cầu trái nhau.

---

## 13. Completion và báo cáo

Không claim hoàn thành nếu code chưa chạy, validation chưa đạt hoặc notebook/output
chưa phản ánh implementation hiện tại. Báo cáo phải nêu file đã đổi, kiểm tra đã
chạy, kết quả chính và giới hạn còn lại.

---

## 14. Activation Gate

```text
RULE_CODE_CREATED=true
RULE_CODE_APPROVED=true
EXECUTION_GOVERNED_BY_THIS_RULE=true
```

Đã ghi nhận Human approval cho governance code và thực thi của Practice 2.
