# EXERCISE 03 — KẾ HOẠCH SỬA STATIONARITY

## 1. Thông tin kế hoạch

```text
Practice: Practice_2
Exercise: EXERCISE_03
Issue source: docs/error_analysis/exercise_03_stationarity_blocker.md
Plan type: Scientific blocker remediation
Status: IMPLEMENTED_AND_VALIDATED
Implementation authorized: YES
E04 handoff: OPEN_FOR_REVIEW
E04/E05 modification: NOT ALLOWED
```

## 2. Mục tiêu

Tạo một stationary training series có evidence để bàn giao cho E04 mà không dùng
test observations, không sửa raw data và không tự tăng differencing order chỉ để đạt
p-value mong muốn.

Hướng ưu tiên của plan là:

```text
original training series
→ validate strictly positive values
→ natural-log transformation
→ regular first-order differencing
→ NaN and timestamp-alignment validation
→ ADF retest
→ stationarity and d decision
```

## 3. Bằng chứng hiện tại

Attempt hiện tại dùng first difference trên raw training scale:

```text
training observations: 163
differenced observations: 162
ADF statistic: -1.706074
p-value: 0.427986
decision: fail to reject H0
selected d: REVIEW_REQUIRED
```

Diagnostic read-only dùng `log(train_series)` rồi first difference:

```text
all training values positive: true
ADF statistic: -3.659486
p-value: 0.004720
decision: reject H0 at alpha=0.05
```

Diagnostic này chỉ hỗ trợ lựa chọn candidate; implementation phải chạy lại từ
kernel/process sạch và không được hard-code kết quả dự kiến.

## 4. Phạm vi

### 4.1. File được phép chỉnh sửa sau khi phê duyệt

```text
total_practice/Practice_2/src/practice_2/analysis/stationarity.py
total_practice/Practice_2/notebooks/Practice_2_present.ipynb
total_practice/Practice_2/tests/test_exercise_01.py
total_practice/Practice_2/docs/exercise_details/exercise_03_differencing_adf_retest.md
total_practice/Practice_2/docs/plans/exercise_03_before_process.md
total_practice/Practice_2/docs/logs/exercise_03_execution.md
total_practice/Practice_2/docs/status/current_status.md
total_practice/Practice_2/outputs/figures/
total_practice/Practice_2/outputs/results/
```

Nếu test E3 được tách thành file riêng theo pattern hiện có, việc tạo file test mới
phải được ghi rõ trong implementation report.

### 4.2. File và trách nhiệm ngoài phạm vi

```text
datasets/raw/a10.csv
notebooks/Practice2_latest.ipynb
Exercise 4 implementation, notebook section and outputs
Exercise 5 implementation, notebook section and outputs
Practice 1, Practice 3 and unrelated files
repository and Practice architecture rules
```

Không dùng notebook legacy làm canonical owner và không sửa notebook legacy trong fix này.

## 5. Ranh giới khoa học được kế hoạch đề xuất

```text
input: original training series from E01
training observations: 163
test observations: 41, sealed and excluded
transformation: natural logarithm
regular differencing order: 1
seasonal differencing order: not introduced
ADF alpha: 0.05
ADF regression: constant (`regression="c"`)
ADF lag selection: AIC (`autolag="AIC"`)
model fitting: NO
forecasting: NO
```

Giá trị `d=1` chỉ mô tả regular differencing trên log-transformed training series.
Notebook và outputs phải ghi rõ analysis scale là `log` để tránh diễn giải như raw scale.

## 6. Thay đổi đã lên kế hoạch

### Bước 1 — Đồng bộ E3 contract

Cập nhật E03 specification và before-process plan để ghi nhận protocol đã được Human
duyệt: log transformation trước first differencing, training-only boundary, output
contract, validation criteria và stop conditions.

Không đổi E01/E02 results và không mở E04 ở bước này.

### Bước 2 — Khai báo tường minh cấu hình ADF

Cập nhật reusable ADF owner để truyền tường minh:

```python
regression="c"
autolag="AIC"
```

Không thay đổi `alpha=0.05` và không đổi decision rule.

### Bước 3 — Bổ sung transformation path đã phê duyệt

Đặt reusable transformation logic trong `src/practice_2/analysis/` theo ownership
hiện tại. Logic phải:

1. từ chối empty series;
2. từ chối missing values;
3. từ chối giá trị `<= 0` trước natural log;
4. không mutate input;
5. trả về log-transformed, first-differenced series có index đúng;
6. loại đúng `NaN` phát sinh từ first difference.

Không duplicate logic trong notebook.

### Bước 4 — Cập nhật notebook orchestration của E3

Trong `Practice_2_present.ipynb`:

1. giữ raw first-difference attempt và kết luận blocker làm evidence;
2. tạo approved log-transformed training series;
3. tạo log first-differenced training series;
4. hiển thị số observations và NaN count;
5. vẽ và inspect transformed differenced series;
6. chạy ADF bằng reusable owner;
7. hiển thị statistic, p-value, critical values, lag và observations;
8. ghi rõ test set chưa được sử dụng;
9. đưa ra decision từ actual result;
10. không thêm hoặc chạy E04/E05 trong scope này.

Notebook phải chạy tuần tự từ kernel sạch và không phụ thuộc hidden state.

### Bước 5 — Giữ failed evidence và tạo evidence mới

Giữ các output raw-first-difference hiện tại làm evidence cho failed attempt:

```text
outputs/figures/02_first_differenced_series.png
outputs/results/adf_differenced_series.csv
outputs/results/adf_differenced_critical_values.csv
```

Tạo output có tên phân biệt rõ analysis scale:

```text
outputs/figures/02_log_first_differenced_series.png
outputs/results/adf_log_first_differenced_series.csv
outputs/results/adf_log_first_differenced_critical_values.csv
outputs/results/e03_transformation_comparison.csv
```

Sau validation, cập nhật canonical decision artifact:

```text
outputs/results/differencing_decision.csv
```

Decision artifact phải ghi tối thiểu transformation, regular differencing order,
ADF statistic, p-value, alpha, decision và handoff state.

### Bước 6 — Bổ sung regression test

Test phải xác nhận:

1. split vẫn là 163 train và 41 test, chronological và không overlap;
2. transformation chỉ dùng train;
3. input không bị mutate;
4. log input validation từ chối zero, negative và missing values;
5. first difference tạo 162 observations;
6. đúng một `NaN` được loại;
7. first and last timestamps alignment đúng;
8. ADF dùng explicit `regression="c"` và `autolag="AIC"`;
9. actual p-value dẫn đến đúng decision;
10. `d=1` chỉ được ghi khi p-value `<= 0.05`;
11. test set không tham gia transformation hoặc ADF.

Float comparisons phải dùng tolerance, không so sánh tuyệt đối.

### Bước 7 — Thực thi và kiểm tra

Thứ tự validation:

```text
targeted unit tests
→ full Practice 2 test suite
→ clean-kernel notebook execution through E03
→ inspect tables and figures
→ compare generated CSV with runtime result
→ verify raw file unchanged
→ verify E04/E05 unchanged
```

Không coi việc code chạy không exception là đủ để mở handoff.

### Bước 8 — Cập nhật evidence và trạng thái

Nếu acceptance criteria đạt:

- cập nhật E03 execution log bằng actual output;
- cập nhật `current_status.md` với transformation và `d` có evidence;
- đánh dấu Scientific Handoff Gate theo actual result;
- ghi rõ notebook present là canonical notebook.

Nếu acceptance criteria không đạt:

- giữ `EXERCISE_03_COMPLETED=false`;
- giữ `selected_d=REVIEW_REQUIRED`;
- giữ E04 handoff đóng;
- ghi actual blocker mới và dừng.

## 7. Quy tắc quyết định

```text
p-value <= 0.05
AND ADF statistic supports the same decision against the reported critical values
AND input/alignment/NaN checks pass
AND no test leakage is found
→ evidence supports stationarity on log first-differenced train
→ select transformation=log and d=1
→ E03 may pass Scientific Handoff review
```

```text
p-value > 0.05
OR validation fails
OR leakage is detected
→ selected_d=REVIEW_REQUIRED
→ E04 handoff remains closed
→ STOP and report
```

## 8. Các phương án đã cân nhắc

### Phương án A — Log transformation kết hợp first difference

```text
Status: RECOMMENDED
Benefit: addresses increasing variance while retaining regular d=1
Evidence: diagnostic p-value 0.004720 on training data
Risk: forecasts and interpretation later require explicit back-transformation handling
```

### Phương án B — Regular difference bậc hai trên raw scale

```text
Status: NOT SELECTED AS FIRST FIX
Benefit: may remove remaining non-stationarity
Risk: over-differencing, noisier series and less stable model interpretation
Requirement: separate approval and over-differencing diagnostics
```

### Phương án C — Seasonal differencing

```text
Status: NOT SELECTED IN THIS FIX
Benefit: may address annual seasonal dependence
Risk: introduces seasonal order D and changes the non-seasonal E03/E04 contract
Requirement: separate scope decision that distinguishes d from D
```

## 9. Rủi ro và biện pháp kiểm soát

| Rủi ro | Biện pháp kiểm soát |
|---|---|
| Test leakage | Chỉ tạo transformation từ `train_series` và assert boundary |
| Hidden notebook state | Restart kernel và chạy tuần tự |
| Hard-code kết quả thuận lợi | Suy ra quyết định từ actual ADF output |
| Over-differencing | Không dùng `d=2` nếu chưa có phê duyệt riêng |
| Nhầm raw scale với log scale | Ghi transformation trong tên biến, plot, table và artifact |
| Mất output provenance | Lưu failed raw-difference output riêng biệt |
| Reproducibility drift | Truyền tường minh cấu hình ADF và kiểm thử |
| Triển khai E4 quá sớm | Xác nhận E4/E5 không đổi trước khi báo cáo |

## 10. Tiêu chí nghiệm thu

```text
[x] Human đã phê duyệt fix plan
[x] E3 specification và before-process contract đã đồng bộ
[x] Chỉ transform 163 quan sát train
[x] 41 quan sát test tiếp tục được niêm phong
[x] Raw dataset checksum không đổi
[x] Mọi giá trị train được xác nhận dương trước khi log
[x] Log first difference có 162 quan sát
[x] Loại đúng một NaN do differencing
[x] Timestamp alignment đúng
[x] ADF dùng alpha=0.05, regression="c", autolag="AIC"
[x] Lưu ADF output và critical values từ lần chạy thực tế
[x] Quyết định stationarity được suy ra từ actual evidence
[x] Không hard-code d
[x] Test đạt
[x] Notebook chạy từ kernel sạch qua E3
[x] Notebook output được lưu và kiểm tra
[x] Không sửa file và output của E4/E5
```

## 11. Điều kiện dừng

Phải dừng và báo Human nếu:

- training series có zero, negative hoặc missing values;
- input không đúng 163-observation training boundary;
- test values được đọc trong transformation hoặc ADF;
- log/differencing alignment sai;
- ADF fail hoặc không tái tạo được;
- p-value vẫn lớn hơn 0.05;
- cần `d=2`, seasonal differencing hoặc dependency mới;
- implementation cần chạm E04/E05;
- actual result mâu thuẫn với specification hoặc rule hiện hành.

## 12. Approval gate

```text
E03_FIX_PLAN_CREATED=true
E03_FIX_PLAN_REVIEWED=true
E03_FIX_PLAN_APPROVED=true
E03_FIX_IMPLEMENTATION_AUTHORIZED=true
E03_FIX_IMPLEMENTED=true
E03_FIX_VALIDATED=true
E04_HANDOFF_OPEN=true
```

Fix đã được Human phê duyệt, triển khai và kiểm chứng. E04/E05 không bị sửa trong scope này.
