# TIME SERIES PRACTICE 01 — QUY TẮC CODE VÀ THỰC THI

## 1. Mục đích

File này định nghĩa cách code, analysis, debugging, refactoring và exercise execution phải được thực hiện bên trong `total_practice/Practice_1`.

Workflow cốt lõi:

```text
Read
→ Understand
→ Analyze
→ Plan
→ Human Approval
→ Execute
→ Run
→ Verify
→ Report
```

Không được bỏ qua các gate quan trọng.

---

## 2. Phạm vi áp dụng

Rule này áp dụng cho:

```text
source code
notebooks
data-processing logic
time-series analysis
time-index validation
ACF/PACF analysis
white-noise experiments
decomposition
missing-value experiments
outlier analysis
forecastability assessment
visualization logic
tests
bug fixes
refactors
folder changes
documentation liên quan đến execution
exercise implementation
```

Rule này không cho phép tự mở rộng Practice 1 sang model fitting, ARIMA/SARIMA, Machine Learning, Deep Learning, hyperparameter tuning hoặc model backtesting.

---

## 3. Các nguồn rule bắt buộc

Trước implementation, công việc liên quan phải tuân thủ:

```text
.agents/RULES_INDEX.md và các canonical source được router này nạp
total_practice/Practice_1/docs/RULE_BASE/architecture_rule.md
total_practice/Practice_1/docs/RULE_BASE/rule_code.md
relevant approved exercise detail when it exists
approved before-process plan when implementation is requested
```

Nếu mandatory rules conflict:

```text
STOP
→ xác định conflict
→ giải thích impact
→ chờ Human quyết định
```

---

## 4. Hiểu trước khi code

Không code khi chưa hiểu task.

Agent phải biết:

```text
task là gì
tại sao cần
input
expected output
affected files
validation method
```

Nếu thiếu thông tin ảnh hưởng trực tiếp đến implementation, phải hỏi trước.

---

## 5. Plan trước implementation

Với meaningful file/code change:

```text
tạo hoặc cập nhật active before-process plan
→ trình bày cho Human
→ chờ approval
→ mới implementation
```

Yêu cầu “chuẩn bị task” không đồng nghĩa với approval để execute.

---

## 6. Sequential Execution

Chỉ nên có một logical execution task active tại một thời điểm.

Pattern chuẩn:

```text
Step 1
→ implement
→ run
→ verify

Step 2
→ implement
→ run
→ verify
```

Nếu Step N fail, không sang Step N+1 cho tới khi hiểu được lỗi.

---

## 7. Small Change Sets

Mỗi step nên chỉ có một focused logical change.

Không trộn:

```text
unrelated refactoring
new analysis
dependency updates
folder restructuring
bug fixes
```

trong cùng một change set nếu chưa được approve.

---

## 8. Không sửa unrelated files

Chỉ sửa file thuộc approved scope.

Nếu phát sinh file mới hoặc scope rộng hơn:

```text
STOP
→ giải thích lý do
→ cập nhật plan
→ xin approval
```

---

## 9. Data Integrity Rule

Không âm thầm:

```text
sort
drop rows
fill NaN
interpolate
deduplicate
resample
clip values
remove outliers
change timestamps
```

Mọi data repair phải:

```text
intentional
documented
scientifically justified
approved khi làm thay đổi protocol
```

Raw dataset là immutable source of truth. Missing values và outliers giả lập chỉ được tạo trên working copy; không được ghi ngược vào raw file.

Mỗi data-quality experiment phải phân biệt rõ:

```text
observed raw values
simulated corruption
detected issue
proposed treatment
treated working copy
```

---

## 10. Time Series Safety

Luôn bảo toàn:

```text
chronological order
timestamp semantics
lag direction
rolling-window direction
future-information boundaries
```

Khi diễn giải khả năng forecasting:

```text
không xem centered rolling statistics là feature có sẵn tại forecast time
không xem backward-fill là treatment an toàn cho forecasting
không xem two-sided interpolation là treatment real-time mặc định
phải phân biệt historical analysis với forecasting-time availability
```

Practice 1 không huấn luyện forecasting model và không tạo train/validation/test split.

---

## 11. Notebook Rule

Notebook dùng cho:

```text
learning
exploration
presentation
interpretation
exercise execution
```

Reusable logic thuộc installable package `src/practice_1/`.

Không phụ thuộc hidden notebook state.

Relevant notebooks phải chạy được theo intended order sau restart.

---

## 12. Bug Investigation Rule

Khi xuất hiện lỗi:

```text
đọc evidence
→ mô tả observed vs expected
→ kiểm tra relevant files
→ trace root cause
→ document issue nếu non-trivial
→ tạo fix plan
→ chờ approval
→ fix
→ validate
```

Không nhảy thẳng từ traceback sang patch.

---

## 13. Fix đúng owner, không fix symptom

Nếu root cause nằm upstream module, sửa ở upstream owner.

Không patch downstream chỉ để execution tiếp tục.

---

## 14. No Silent Fallback

Nếu intended implementation path fail:

```text
không âm thầm đổi sang method khác
không âm thầm đổi parameter
không âm thầm giảm mức validation
```

Phải report issue và đề xuất next action.

---

## 15. Không fabricate result

Không bao giờ bịa:

```text
dataset values
metrics
plots
validation results
statistical conclusions
model performance
```

Conclusion phải đến từ actual execution hoặc theoretical reasoning được ghi rõ là lý thuyết.

### 15.1 Scientific Evidence Rules cho Practice 1

Mọi phân tích phải ghi rõ configuration đã dùng, bao gồm các tham số liên quan như random seed, maximum lag, confidence level, rolling window, seasonal period và decomposition settings.

ACF/PACF:

```text
không suy ra trực tiếp ARIMA order chỉ từ raw non-stationary series
phải phân biệt autocorrelation do trend, seasonality và short-term dependence
phải ghi rõ số lag và confidence level
```

White noise:

```text
phải dùng explicit random seed
không kết luận chỉ từ việc một vài lag vượt confidence band
phải kết hợp ACF với Ljung-Box test khi đưa ra kết luận thống kê
```

Decomposition:

```text
phải ghi rõ additive, multiplicative hoặc transformed-additive assumption
phải ghi rõ seasonal period
nếu dùng log transform, interpretation phải nói rõ scale
residual white-noise assessment phải có evidence ngoài visual inspection
```

Missing values:

```text
simulated missing phải được tạo trên working copy
true values tại các vị trí bị mask phải được giữ để đánh giá
forward-fill và interpolation phải được so sánh trên cùng vị trí
historical interpolation không được trình bày như forecasting-safe mặc định
```

Outliers:

```text
không tự động xóa hoặc thay thế outlier
phải phân biệt seasonal peak với anomaly
với chuỗi có trend và seasonality, ưu tiên detection trên decomposition residual
before/after plot phải nói rõ dữ liệu nào là raw và dữ liệu nào là treated copy
```

---

## 16. Run và Verify mọi change

Sau code change phải validation phù hợp.

Có thể gồm:

```text
syntax/import
function output
data shape
timestamp order
missing-value behavior
expected plot
expected result table
exercise acceptance criteria
```

Chỉ đọc code chưa đủ để kết luận complete.

---

## 17. Regression Awareness

Khi sửa reusable code, phải xem xét:

```text
current task
upstream assumptions
downstream consumers
notebooks đang dùng function
tests đang dùng function
```

Regression scope phải tương ứng với mức ảnh hưởng.

---

## 18. Dependency Rule

Không thêm hoặc upgrade dependency chỉ để làm task dễ hơn.

Dependency change phải có:

```text
reason
impact analysis
compatibility check
approval khi significant
```

---

## 19. Source Code Quality

Ưu tiên:

```text
clear names
small cohesive functions
explicit inputs
explicit outputs
deterministic behavior
single responsibility
```

Tránh:

```text
hard-coded absolute paths
broad except blocks
silent exception swallowing
duplicate logic
hidden global state
```

Import contract:

```text
install package từ pyproject.toml
import reusable logic qua practice_1.*
không dùng sys.path mutation
không dùng machine-specific path
không duplicate reusable function trong notebook
```

---

## 20. Validation trước Completion

Không báo:

```text
done
fixed
passed
complete
```

nếu chưa có validation evidence.

Minimum expectation:

```text
approved scope đã implement
code đã execute
required output đã inspect
không còn blocking error
exercise requirement đã đạt
current flow được cập nhật khi cần
```

---

## 21. Exercise Execution Workflow

Với mỗi exercise:

```text
1. Đọc exercise detail.
2. Đọc current flow.
3. Inspect relevant data/code/notebook.
4. Chuẩn bị before-process plan.
5. Chờ Human approval.
6. Implement từng step.
7. Run và verify từng step.
8. Lưu outputs.
9. Ghi lại important findings.
10. Cập nhật current flow.
11. Report result và remaining issues.
```

---

## 22. Fix Workflow

Với bug không trivial:

```text
Evidence
→ Root-cause investigation
→ Issue document
→ Fix plan
→ Human approval
→ Sequential fix
→ Local validation
→ Impact validation
→ Report
```

---

## 23. Stop Conditions

Phải dừng execution khi:

```text
requirement chưa rõ
rule conflict
required file chưa đọc
unexpected schema
cần dependency mới
scope cần mở rộng
validation fail ngoài dự kiến
xuất hiện data leakage risk
upstream logic bị lỗi
thiếu Human approval
```

---

## 24. Current Task State

Tại một thời điểm dùng một trạng thái thực tế:

```text
NOT_STARTED
PLANNING
WAITING_APPROVAL
IN_PROGRESS
BLOCKED
VALIDATING
COMPLETED
```

Chỉ một main task được ở trạng thái `IN_PROGRESS`.

---

## 25. Reporting

Sau implementation phải report:

```text
đã thay đổi gì
files affected
đã chạy gì
validation result
outputs created
remaining risk hoặc limitation
next step
```

---

## 26. Final Hard Rules

```text
RULE 01 — Hiểu trước khi code.
RULE 02 — Plan trước meaningful implementation.
RULE 03 — Human approval trước approved-scope execution khi cần.
RULE 04 — Execute tuần tự.
RULE 05 — Mỗi lần chỉ một focused logical change.
RULE 06 — Không sửa unrelated files.
RULE 07 — Bảo toàn chronological order.
RULE 08 — Ngăn future leakage.
RULE 09 — Không silent data repair.
RULE 10 — Reusable logic thuộc src.
RULE 11 — Điều tra trước khi fix bug không trivial.
RULE 12 — Fix root-cause owner, không fix downstream symptom.
RULE 13 — Không fabricate result.
RULE 14 — Run và verify mọi change.
RULE 15 — Không claim completion khi chưa có evidence.
RULE 16 — Stop và ask khi scope, protocol hoặc architecture chưa rõ.
RULE 17 — Missing và outlier experiment chỉ được thực hiện trên working copy.
RULE 18 — Không kết luận white noise chỉ bằng visual inspection.
RULE 19 — Không xóa hoặc thay thế outlier tự động.
RULE 20 — Mọi statistical conclusion phải truy vết được về configuration và execution evidence.
RULE 21 — Không mở rộng Practice 1 sang forecasting model khi chưa có task và approval riêng.
```

---

## 27. Activation Gate

File này chỉ active sau Human approval.

Trạng thái hiện tại:

```text
RULE_CODE_CREATED=true
RULE_CODE_APPROVED=true
EXECUTION_GOVERNED_BY_THIS_RULE=true
```

Human approval recorded for Practice 1 scoped code and execution governance.
