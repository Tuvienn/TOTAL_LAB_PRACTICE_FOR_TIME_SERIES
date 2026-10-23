# TIME SERIES PRACTICE 03 — QUY TẮC CODE VÀ THỰC THI

## 1. Danh tính và mục đích

```text
Document ID: TS-PRACTICE-03-CODE-v1.1
Phạm vi: total_practice/Practice_3
Trạng thái: APPROVED_AND_ACTIVE
Ngày cập nhật: 2026-10-21
```

File này quy định cách thay đổi file, viết code, chạy notebook, xử lý dữ liệu, tạo feature, train model, tuning, dự báo, đánh giá và báo cáo trong Practice 3.

Workflow bắt buộc:

```text
Read
→ Understand
→ Plan
→ Human Approval
→ Execute one focused step
→ Run
→ Verify
→ Report
```

---

## 2. Nguồn bắt buộc và phạm vi

Trước implementation phải tuân thủ:

```text
working_rule.md
.agents/RULES_INDEX.md và các canonical rule được router này nạp
total_practice/Practice_3/docs/rules/architecture_rule.md
total_practice/Practice_3/docs/rules/rule_code.md
relevant approved plan hoặc specification
```

Rule áp dụng cho source code, notebook, data processing, feature engineering, split, modeling, tuning, forecasting, evaluation, visualization, tests, bug fix và documentation liên quan execution.

Chỉ thực thi phần đã được Human duyệt. Không tự mở rộng sang model, metric, feature, dependency hoặc artifact ngoài phạm vi.

---

## 3. Thay đổi tuần tự và có owner

Mỗi change set chỉ giải quyết một trách nhiệm chính:

```text
implement
→ run or inspect
→ verify
→ report
→ chuyển sang bước kế tiếp khi được phép
```

Không trộn unrelated refactor, dependency update, data repair, model experiment và folder restructuring.

Reusable hoặc correctness-critical logic phải đặt trong owner thích hợp dưới `src/practice_3/`. Notebook gọi logic đó để trình bày, không sao chép nhiều phiên bản độc lập.

Không sửa file ổn định hoặc file ngoài approved scope. Không tạo file/folder mới, đổi dependency direction hoặc đổi kiến trúc để hợp thức hóa implementation chưa được duyệt.

---

## 4. Quy tắc source code

Code phải ưu tiên:

```text
explicit inputs and outputs
small cohesive functions
clear snake_case names
deterministic behavior
Path-based portable paths
validated assumptions
actionable errors
```

Không được:

- dùng đường dẫn tuyệt đối theo máy cá nhân;
- dùng `sys.path` hack;
- nuốt exception rộng hoặc im lặng fallback sang phương pháp khác;
- hard-code secret;
- thêm dependency khi chưa được duyệt;
- thêm comment chỉ kể lại code đang làm gì;
- bịa output, metric, benchmark hoặc execution evidence.

---

## 5. Load và kiểm tra dữ liệu

File raw phải được mở read-only về mặt workflow; code không được ghi đè `datasets/raw/AEP_hourly.csv`.

Trước xử lý phải validate:

```text
required columns: Datetime, AEP_MW
Datetime parseability
AEP_MW numeric validity
row and column counts
date range
chronological ordering
duplicate timestamps
missing cell values
missing timestamps
frequency and interval irregularity
```

Không được tự động sort, deduplicate, fill, interpolate, resample, clip hoặc loại outlier trên raw data. Nếu một thao tác là cần thiết cho modeling, phải:

1. lưu bằng chứng trạng thái gốc;
2. mô tả observed và expected behavior;
3. đề xuất treatment và impact;
4. chờ Human duyệt;
5. áp dụng trên working copy hoặc processed artifact;
6. kiểm tra lại sau xử lý.

Missing cell value và missing timestamp là hai vấn đề khác nhau, không được báo cáo như một khái niệm duy nhất.

---

## 6. Feature engineering an toàn theo thời gian

Với target tại thời điểm `t`:

```text
lag_k(t) = y(t-k), k > 0
```

Phải kiểm tra thủ công ít nhất một số hàng đại diện để xác nhận alignment.

Rolling feature cho dự báo `y(t)` phải chỉ dùng lịch sử trước `t`. Cách triển khai phải có hiệu lực tương đương:

```text
historical_target = target.shift(1)
rolling_mean_k(t) = mean(historical_target over window k)
rolling_std_k(t) = std(historical_target over window k)
```

Không dùng centered rolling, `y(t)` hoặc future target trong feature của `y(t)`.

Sau khi tạo feature phải xác minh:

- index của feature và target khớp nhau;
- target không nằm trong `X`;
- thứ tự feature rõ ràng;
- NaN đầu chuỗi đúng với lag/window lớn nhất;
- không xóa hàng một cách rộng khiến issue dữ liệu khác bị che khuất.

Mọi giá trị lag `p`, rolling window và feature set phải đến từ bước đã được duyệt và được ghi lại trong execution evidence.

---

## 7. X/y và chronological split

Supervised dataset phải giữ timestamp làm khóa alignment hoặc index truy vết được.

Trước split phải kiểm tra:

```text
len(X) == len(y)
X.index equals y.index
X contains no target leakage
required features contain no unexpected NaN or inf
timestamps are in the approved order
```

Train/test split phải theo thời gian, không shuffle, không overlap và thỏa:

```text
max(train_time) < min(test_time)
```

Mọi transformation có `fit` phải fit trên training data của boundary tương ứng rồi mới transform validation/test. Không fit scaler, imputer, selector hoặc feature transformation trên toàn bộ dữ liệu trước split.

---

## 8. Baseline, model training và tuning

Trước model phức tạp phải có forecasting baseline đơn giản đã được Human duyệt và đánh giá trên cùng protocol. Không gọi một cấu hình XGBoost là bằng chứng cải thiện forecasting nếu chưa so với baseline thích hợp.

Thứ tự model theo plan:

```text
approved forecasting baseline
→ XGBoost baseline
→ tuned XGBoost
→ Random Forest comparison
```

Mỗi execution phải ghi:

```text
feature set
train/test boundary
forecast protocol
random seed
model class
hyperparameters
metric definitions
runtime errors or warnings that affect interpretation
```

Training job dài phải lưu log và checkpoint theo đơn vị công việc đã duyệt. Với Phase 5 feature screening, checkpoint được ghi atomically sau từng CV fold; resume chỉ được phép khi configuration, upstream inputs, runtime contract, source identity và fold identity còn khớp. Fold đã `PASS` không được train lại khi resume.

Kết quả tạm trong `runs/` không được promote sang `outputs/results/` trước khi toàn bộ run hoàn thành và validation tương ứng đạt. Khi Human dừng execution, trạng thái phải ghi `INTERRUPTED`; không được báo `PASS` hoặc tạo official result.

Tuning chỉ dùng training set với `TimeSeriesSplit`. Test set cuối không được tham gia chọn hyperparameter, lag, rolling window, feature set, early stopping decision hoặc model winner.

Các model so sánh phải dùng cùng dữ liệu, feature set, split, horizon và metric. Nếu khác, phải ghi rõ đây không phải fair head-to-head comparison.

Không suppress training error hoặc warning quan trọng. Không âm thầm đổi estimator, search space, seed, metric hay CV settings khi execution thất bại.

---

## 9. One-step và multi-step forecasting

One-step và multi-step phải có code path, configuration hoặc metadata đủ rõ để phân biệt.

One-step phải xác nhận prediction tại mỗi timestamp chỉ dùng dữ liệu có sẵn trước timestamp đó.

Multi-step phải chốt trước khi code:

```text
horizon
strategy: recursive, direct hoặc phương án được duyệt khác
feature update rule
evaluation alignment
metric aggregation
```

Với recursive strategy, prediction của bước trước có thể được dùng theo protocol đã duyệt; actual target tương lai không được đưa ngược vào lag. Với direct strategy, mỗi horizon phải có target shift và alignment được kiểm tra riêng.

Không gộp metric one-step và multi-step thành một con số mà không ghi rõ cách tổng hợp.

---

## 10. Evaluation và model comparison

MAE và RMSE phải được tính từ cặp actual/predicted đã alignment trên cùng timestamp và horizon.

Trước khi tính metric phải kiểm tra:

```text
same number of observations
same timestamp order
no unexpected NaN or inf
no train/test contamination
same evaluation window for compared models
```

Kết quả phải chứa đủ context để truy vết về experiment. Không chỉ print một con số không có model, feature set, split hoặc horizon.

Khi tuyên bố model tốt hơn phải nêu metric nào tốt hơn, trên protocol nào, chênh lệch bao nhiêu và limitation nào còn tồn tại. Không suy rộng ngoài tập thời gian đã đánh giá.

---

## 11. Feature importance và câu hỏi phân tích

Feature importance phải lấy từ đúng fitted model và map đúng thứ tự tên feature. Tổng hợp hoặc biểu đồ phải hiển thị rõ loại importance nếu library cung cấp nhiều định nghĩa.

Không diễn giải importance thành causality. Correlated lag/rolling features có thể chia sẻ hoặc làm lệch importance và limitation này phải được nêu khi phù hợp.

Ba câu hỏi về XGBoost với Linear Regression, ảnh hưởng của lag `p`, và XGBoost với ARIMA phải phân biệt rõ:

```text
kết quả đã thực nghiệm trong Practice 3
giải thích lý thuyết
kết luận chưa có bằng chứng execution
```

Không được bịa metric cho Linear Regression hoặc ARIMA nếu các model này chưa thực sự được chạy theo scope đã duyệt.

---

## 12. Notebook execution

Notebook phải chạy theo thứ tự từ trên xuống trong kernel sạch và không phụ thuộc hidden state.

Notebook phải:

- định nghĩa ngắn gọn bài toán, input và output;
- dùng path tương đối hoặc path được resolve từ project root;
- import reusable logic từ `practice_3` theo package structure;
- trình bày output ngay gần bước tạo output;
- phân biệt data observation, model result và interpretation;
- không giữ output stale không còn khớp với code.

Không được chỉnh tay output notebook để làm kết quả đẹp hơn.

---

## 13. Testing và validation

Validation tối thiểu theo phạm vi bước gồm:

```text
schema and dtype checks
timestamp ordering, duplicates and gaps
raw-data immutability
lag and rolling alignment
expected leading NaN behavior
X/y alignment
chronological split and non-overlap
TimeSeriesSplit restricted to train
prediction shape and timestamp alignment
metric calculation
reproducibility with fixed seed where supported
output existence and provenance
```

Đọc code hoặc thấy không có syntax error chưa đủ để tuyên bố đúng. Phải kiểm tra output thực tế phù hợp với acceptance criteria của bước.

---

## 14. Error handling và stop conditions

Phải dừng, báo observed/expected, impact và hướng xử lý khi:

- schema hoặc time index không đúng assumption;
- cần chọn protocol xử lý duplicate hoặc missing timestamp;
- phát hiện leakage, overlap hoặc misalignment;
- dependency thiếu và cần cài/thay đổi;
- tuning hoặc model training thất bại chưa rõ nguyên nhân;
- metric giữa các model không còn cùng evaluation scope;
- output notebook và source result mâu thuẫn;
- scope phải mở rộng ngoài plan đã duyệt.

Sau ba lần thử tương tự không giải quyết được cùng một lỗi, phải dừng và thực hiện self-retrospective theo canonical rules trước lần thử tiếp theo.

---

## 15. Báo cáo hoàn thành

Chỉ được báo `COMPLETED`, `PASS` hoặc `DONE` khi approved scope đã được thực thi, validation tương ứng đạt và output đã được kiểm tra.

Báo cáo phải nêu:

```text
files changed
what was implemented
execution evidence
validation result
outputs created
remaining risks and limitations
next approved step
```

Không commit hoặc push nếu Human chưa yêu cầu.
