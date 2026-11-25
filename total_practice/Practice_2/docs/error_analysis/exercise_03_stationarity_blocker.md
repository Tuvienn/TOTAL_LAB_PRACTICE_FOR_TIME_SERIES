# EXERCISE 03 — STATIONARITY BLOCKER ANALYSIS

## 1. Issue Identity

```text
Practice: Practice_2
Exercise: EXERCISE_03
Issue type: Scientific result and legacy workflow inconsistency
Current state: BLOCKED_BY_SCIENTIFIC_RESULT
Downstream impact: EXERCISE_04_HANDOFF_OPEN=false
Review scope: historical Practice_2_present.ipynb and Practice2_latest.ipynb
references (neither is present in the current repository)
```

## 2. Expected Behavior

Exercise 3 phải:

1. sử dụng original training series từ chronological split của E01;
2. thực hiện regular first-order differencing trên working copy;
3. loại đúng một `NaN` phát sinh tại quan sát đầu tiên;
4. chạy ADF trên first-differenced training series với `alpha=0.05`,
   `regression="c"` và `autolag="AIC"`;
5. chỉ chốt `d=1` và mở handoff sang E04 khi stationarity được actual evidence hỗ trợ;
6. giữ `selected_d=REVIEW_REQUIRED` và dừng trước E04 nếu `p-value > 0.05`.

## 3. Observed Behavior

### 3.1. Historical intended canonical notebook: `Practice_2_present.ipynb`

```text
full observations: 204
training observations: 163
test observations: 41
split order: chronological
shuffle: false
differencing input: training series
differenced observations: 162
NaN created by differencing: 1
NaN remaining after dropna: 0
ADF statistic: -1.706074
p-value: 0.427986
used lag: 13
ADF observations: 148
decision: fail to reject H0
selected d: REVIEW_REQUIRED
```

Notebook historical thực hiện đúng boundary, differencing và stop condition. Tuy nhiên,
first-differenced training series chưa có evidence stationary nên E03 chưa đạt
Scientific Handoff Gate.

Repository reconciliation note: `Practice_2_Exercise.ipynb` is the current
canonical core notebook. The historical evidence above must not be treated as
execution evidence for that file until its own contents are rerun and validated.

### 3.2. Historical legacy notebook reference: `Practice2_latest.ipynb`

```text
differencing input: full series
full observations: 204
differenced observations: 203
NaN created by differencing: 1
NaN remaining after dropna: 0
ADF statistic: -2.495172
p-value: 0.116653
decision: fail to reject H0
```

Notebook legacy chỉ tạo train/test split tại E05. Vì vậy E02–E04 đã đọc cả 41
observations thuộc test period. Sau khi E03 vẫn có `p-value > 0.05`, notebook này
tiếp tục chạy ACF/PACF và trình bày `d=1`. Hành vi đó vi phạm leakage boundary và
stationarity gate hiện hành.

## 4. Confirmed Findings

1. Chronological split 163/41 của notebook present là đúng và không shuffle.
2. First-order differencing được tính đúng theo `y_t - y_(t-1)`.
3. Một `NaN` phát sinh có chủ đích và được loại; không còn missing value trong ADF input.
4. ADF trên first-differenced training series được tái tạo với statistic
   `-1.706074` và p-value `0.427986`.
5. Với `alpha=0.05`, E03 phải fail to reject H0 và chưa được kết luận stationary.
6. `d=1` chưa hợp lệ theo evidence hiện tại.
7. Notebook present dừng đúng với `REVIEW_REQUIRED`; notebook legacy tiếp tục E04 sai protocol.

## 5. Root-Cause Analysis

### 5.1. Confirmed scientific root cause

Regular first-order differencing trên raw scale không đủ tạo stationary evidence cho
training series. Vấn đề không nằm ở phép tính `.diff()` hoặc xử lý `NaN`; vấn đề là
transformation hiện tại chưa xử lý đầy đủ cấu trúc của chuỗi.

### 5.2. Likely contributing characteristics

EDA cho thấy level tăng, biên độ biến động tăng theo level và có pattern mùa vụ hàng
năm. Các đặc điểm này có thể làm first difference trên raw scale vẫn giữ variance
không ổn định hoặc seasonal dependence. Đây là giả thuyết cần kiểm tra trong fix plan,
không phải kết luận đã được phê duyệt.

### 5.3. Confirmed legacy workflow root cause

Notebook legacy xác lập holdout boundary quá muộn. ADF, differencing và ACF/PACF đã
dùng full series trước khi split tại E05. Sau đó notebook hard-code cách diễn giải
`d=1` dù ADF retest chưa reject H0.

### 5.4. Reproducibility gaps

- `run_adf()` đang dựa vào default `regression="c"` thay vì truyền tham số tường minh.
- Notebook present hiện không lưu rendered code output, nên evidence phải đối chiếu
  qua CSV, execution log và independent rerun.

Hai điểm này không làm thay đổi các con số ADF hiện tại nhưng phải được xử lý trong
fix scope để handoff có thể tái tạo và review.

## 6. Impact

```text
E03 technical execution: validated
E03 scientific completion: false
selected d: REVIEW_REQUIRED
stationary series for E04: unavailable
E04 handoff: closed
E05 evidence from legacy flow: not admissible as canonical evaluation
```

Nếu tiếp tục E04 từ first-differenced raw training series hiện tại, ACF/PACF sẽ được
diễn giải trên một input chưa đạt stationarity gate. Nếu tiếp tục từ notebook legacy,
kết quả còn bị test contamination.

## 7. Diagnostic Evidence for the Next Plan

Một kiểm tra read-only trên training data xác nhận tất cả training values đều dương.
Khi thử `log(train_series)` rồi first difference và chạy ADF với cùng cấu hình:

```text
ADF statistic: -3.659486
p-value: 0.004720
decision: reject H0 at alpha=0.05
```

Kết quả này cho thấy `log + first difference` là candidate đáng đánh giá trong fix
plan. Đây chưa phải canonical E03 result và không tự động mở E04.

Second regular differencing hoặc seasonal differencing chỉ được xem xét sau khi phân
tích risk over-differencing và phân biệt rõ regular order `d` với seasonal order `D`.

## 8. Required Decision Before Fixing

Human cần duyệt một fix plan riêng để chọn transformation protocol. Fix plan tối thiểu
phải xác định:

- transformation candidate và lý do;
- training-only input boundary;
- ADF configuration;
- variance, alignment và NaN validation;
- điều kiện chọn `d`;
- stop condition nếu candidate vẫn không stationary;
- notebook, source, tests, outputs và state files được phép sửa.

## 9. Future Fix Acceptance Criteria

```text
[ ] Only the 163-observation training series is used
[ ] Test values remain sealed
[ ] Transformation protocol is Human-approved
[ ] Transformation scale and differencing order are recorded
[ ] NaN count and timestamp alignment are validated
[ ] ADF uses alpha=0.05, regression="c", autolag="AIC"
[ ] ADF statistic, p-value, critical values, lag and observations are saved
[ ] Stationarity conclusion is based on actual execution
[ ] d is selected only when supported by evidence
[ ] Notebook is executed from a clean kernel and outputs are inspected
[ ] E04 remains untouched until the Scientific Handoff Gate passes
```

## 10. Stop Condition

Không sửa hoặc chạy tiếp E04/E05 từ kết quả E03 hiện tại. Bước kế tiếp là lập và
Human duyệt fix plan cho E03; chỉ sau khi fix được triển khai, kiểm chứng và cập nhật
state thì mới review handoff sang E04.
