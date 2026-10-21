# EXERCISE 06 — KẾ HOẠCH SỬA RESIDUAL DIAGNOSTICS

## 1. Thông tin kế hoạch

```text
Practice: Practice_2
Exercise: EXERCISE_06
Issue source: docs/error_analysis/exercise_06_residual_diagnostics_issue.md
Plan type: Scientific diagnostics remediation
Status: IMPLEMENTED_AND_VALIDATED
Implementation authorized: YES_FOR_RESIDUAL_FIX_SCOPE
E06 implementation gate: RESIDUAL_FIX_SCOPE_COMPLETED
E06 completion claim: NOT ALLOWED
```

Plan này chỉ sửa residual diagnostics đã được xác nhận sai. Việc tạo plan không mở
quyền triển khai E06 khi E05 chưa được Human hoàn tất review và E06 chưa được phê
duyệt theo approval gate hiện hành.

## 2. Mục tiêu

Tạo một residual diagnostics flow duy nhất, tái sử dụng được cho cả ARIMA và SARIMA,
trong đó mean, plot, ACF và Ljung–Box đều dùng đúng post-burn-in residual series.

Diễn giải đúng được kỳ vọng:

```text
ARIMA: residual autocorrelation còn lại tại lag 12 và 24
SARIMA: chưa có bằng chứng residual autocorrelation tại lag 12 và 24
Phạm vi kết luận: chỉ tại các lag đã kiểm tra và alpha=0.05
```

Các expected values chỉ là review evidence. Implementation không được hard-code
p-value hoặc conclusion.

## 3. Điều kiện tiên quyết

Trước khi triển khai phải xác nhận:

```text
[x] Human reviewed and approved this fix plan
[x] E05 formal review gate is resolved
[x] E06 specification/before-process approval permits the residual fix
[x] Current dirty worktree changes are preserved
[x] Raw AirPassengers checksum still matches the contract
```

Nếu một gate chưa đạt: dừng ở documentation state, không sửa code hoặc chạy lại E06.

## 4. Phạm vi

### 4.1. File được phép chỉnh sửa sau khi phê duyệt

```text
src/practice_2/analysis/forecasting.py
src/practice_2/analysis/__init__.py, only if the public API changes
src/practice_2/visualization/plots.py, only for reusable post-burn-in plotting
tests/test_exercise_05.py, only for regression protection if required
tests/test_exercise_06.py
notebooks/Practice_2_advanced_sarima.ipynb
outputs/figures/06_airpassengers_residual_diagnostics.png
outputs/results/06_airpassengers_model_diagnostics.csv
docs/exercise_details/exercise_06_sarima_extension.md
docs/plans/exercise_06_before_process.md
docs/error_analysis/exercise_06_residual_diagnostics_issue.md
docs/fix_plans/exercise_06_residual_diagnostics_fix_plan.md
docs/logs/exercise_06_execution.md
docs/status/current_status.md
```

### 4.2. File và trách nhiệm ngoài phạm vi

```text
datasets/raw/a10.csv
datasets/raw/airline-passengers.csv
notebooks/Practice_2_present.ipynb
notebooks/Practice2_latest.ipynb
E01–E05 source results and output artifacts
E06 dataset split, scale, differencing and model-order decisions
E06 forecast inverse-transform policy
README.md
repository and Practice rules
unrelated Practice/Lab files
```

Nếu fix cần thay model order, transformation, holdout, dependency hoặc architecture:
`STOP → giải thích tác động → cập nhật phạm vi → chờ Human phê duyệt`.

## 5. Thay đổi đã lên kế hoạch

### Bước 1 — Giữ và xác minh entry evidence

Ghi lại trước khi sửa:

```text
raw checksum
115/29 chronological split
current fitted orders
model convergence
current incorrect residual values and Ljung–Box results
forecast MAE/RMSE
```

Không dùng forecast metrics để thay đổi residual protocol.

### Bước 2 — Mở rộng reusable residual owner

Tái sử dụng `compute_residual_diagnostics()` trong
`src/practice_2/analysis/forecasting.py` và mở rộng an toàn cho SARIMA:

1. lấy `fitted.resid` và giữ đúng timestamp index;
2. đọc `fitted.loglikelihood_burn`;
3. loại đúng `burn_in` observations trước mean, ACF và Ljung–Box;
4. đọc non-seasonal order `(p,d,q)`;
5. đọc seasonal order `(P,D,Q,s)` khi model có thuộc tính này;
6. tính `model_df = p + q + P + Q`;
7. validate mỗi lag lớn hơn `model_df` và nhỏ hơn residual length;
8. trả về cùng một post-burn-in residual mapping và diagnostics table;
9. không thay đổi E5 result đối với model không seasonal.

Không tạo helper residual thứ hai chỉ dành cho notebook E06.

### Bước 3 — Bổ sung targeted regression test

Tạo `tests/test_exercise_06.py` với các kiểm tra tối thiểu:

```text
ARIMA burn_in = 1
SARIMA burn_in = 13
ARIMA residual observations = 114
SARIMA residual observations = 102
ARIMA model_df = 2
SARIMA model_df = 3
initialization residuals are absent from returned series
diagnostic residual index starts after the model burn-in
Ljung–Box uses lags 12 and 24 with alpha 0.05
ARIMA rejects no-autocorrelation at both tested lags
SARIMA fails to reject no-autocorrelation at both tested lags
input fitted results are not mutated
```

Numeric comparisons phải dùng tolerance phù hợp với library version. Test không được
hard-code output chỉ để làm đẹp kết quả và không được thay raw data.

Chạy lại E5 tests để bảo đảm seasonal extension không làm thay đổi ARIMA diagnostics
đã validated.

### Bước 4 — Thay notebook-local diagnostics

Trong `Practice_2_advanced_sarima.ipynb`:

1. bỏ cell tự tạo residual từ toàn bộ `fitted.resid`;
2. gọi reusable diagnostics owner;
3. dùng returned post-burn-in residuals cho time plot và ACF;
4. hiển thị bảng gồm model, residual mean, observations, burn-in, model_df, lag,
   Ljung–Box statistic, p-value và decision;
5. giải thích kết luận giới hạn ở lag 12/24;
6. loại bỏ hoàn toàn p-value và kết luận residual cũ;
7. không sửa ADF, differencing, ACF/PACF candidate hoặc forecast protocol trong
   fix này.

### Bước 5 — Chỉ tạo lại evidence bị ảnh hưởng

Tạo lại từ actual approved execution:

```text
outputs/figures/06_airpassengers_residual_diagnostics.png
outputs/results/06_airpassengers_model_diagnostics.csv
```

Figure phải dùng cùng post-burn-in residual series với CSV. Không giữ figure cũ có
initialization spikes như canonical output.

### Bước 6 — Clean execution và kiểm tra

Validation order:

```text
targeted E06 tests
→ E05 regression tests
→ full Practice 2 test suite
→ clean-kernel execution of the advanced notebook
→ inspect residual CSV and figure
→ verify forecast metrics remain consistent
→ verify raw checksum and E01–E05 artifacts remain unchanged
```

Notebook phải chạy tuần tự; không chấp nhận code cell có persisted output nhưng
`execution_count=None` hoặc phụ thuộc hidden state.

### Bước 7 — Đồng bộ tài liệu và trạng thái

Sau khi validation đạt:

- cập nhật E06 execution log bằng actual post-burn-in results;
- cập nhật current status nhưng không tự đánh dấu E06 completed;
- chuyển error analysis sang `RESOLVED_AND_VALIDATED`;
- chuyển fix plan sang implemented/validated;
- ghi rõ forecast metrics không thay đổi bởi residual-only fix;
- ghi nhận quyết định Human giữ E6 ở mức exploratory theo Phương án A.

Nếu validation không đạt, giữ issue unresolved và không thay conclusion cũ bằng một
conclusion chưa được kiểm chứng.

## 6. Quy tắc quyết định khoa học

Với từng model và từng lag:

```text
p-value <= 0.05
→ reject the no-autocorrelation null
→ residual autocorrelation remains at that tested lag
```

```text
p-value > 0.05
→ fail to reject the no-autocorrelation null
→ no evidence of autocorrelation at that tested lag
```

Không được chuyển “fail to reject” thành khẳng định residual hoàn toàn là white noise.
Residual mean gần 0 cũng không tự chứng minh white noise.

## 7. Các phương án đã cân nhắc

### Phương án A — Raw residual sau model-specific burn-in

```text
Status: RECOMMENDED
Benefit: consistent with the validated E5 helper and model result API
Risk: residual variance interpretation remains on the log scale
Control: record scale, burn-in and observation count explicitly
```

### Phương án B — Standardized forecast error sau burn-in

```text
Status: SUPPLEMENTARY, NOT PRIMARY IN THIS FIX
Benefit: normalizes residual scale through model-implied forecast variance
Risk: changes the existing E5 diagnostic contract and comparison semantics
Requirement: separate protocol approval if selected as canonical residual
```

### Phương án C — Loại thủ công một số dòng cố định

```text
Status: REJECTED
Reason: ARIMA and SARIMA have different initialization lengths; a hard-coded drop
does not follow the fitted model and is fragile when orders change
```

## 8. Rủi ro và biện pháp kiểm soát

| Rủi ro | Biện pháp kiểm soát |
|---|---|
| Bỏ sót seasonal degrees of freedom | Suy ra `P + Q` từ fitted seasonal order và test `model_df=3` |
| Phát sinh regression ở E5 | Chạy test E5 hiện có và assert non-seasonal result không đổi |
| Output notebook cũ còn tồn tại | Clean-run advanced notebook và kiểm tra execution count |
| Table và figure dùng residual khác nhau | Sinh cả hai từ cùng returned residual mapping |
| Hard-code expected p-value | Tính từ actual fit; chỉ dùng tolerance trong regression test |
| Phóng đại white-noise claim | Giới hạn diễn giải tại lag và alpha đã kiểm tra |
| Scope mở rộng sang model selection | Giữ nguyên order, split, scale và forecast |
| Ghi đè dirty worktree | Kiểm tra status và giữ unrelated Human change |

## 9. Tiêu chí nghiệm thu

```text
[x] Human phê duyệt fix plan và E6 residual-fix implementation gate
[x] Raw dataset checksum không đổi
[x] Split vẫn theo thời gian 115/29, không shuffle
[x] ARIMA và SARIMA order không đổi
[x] Burn-in được đọc từ từng fitted result
[x] ARIMA dùng 114 post-burn-in residual
[x] SARIMA dùng 102 post-burn-in residual
[x] model_df gồm non-seasonal và seasonal AR/MA term
[x] Residual mean, ACF và Ljung–Box dùng cùng post-burn-in series
[x] Initialization spike không còn trong canonical residual figure
[x] Quyết định ARIMA/SARIMA được suy ra từ actual p-value
[x] Targeted E6 test đạt
[x] Test E5 hiện có đạt và không đổi
[x] Full Practice 2 test suite đạt
[x] Advanced notebook chạy từ kernel sạch, không có lỗi
[x] Residual CSV và figure khớp notebook value
[x] Forecast index và MAE/RMSE nhất quán
[x] E1–E5 logic và canonical notebook không bị thay đổi bởi fix này
[x] Tài liệu ghi giới hạn trung thực
[x] Human đã chọn giữ E6 ở mức exploratory theo Phương án A
```

## 10. Điều kiện dừng

Dừng và báo Human nếu:

- fitted result không cung cấp stable burn-in or seasonal-order metadata;
- post-burn-in residual length không phải 114/102 theo approved setup;
- residual index lệch training index sau burn-in;
- E5 diagnostics thay đổi ngoài seasonal `model_df` extension;
- corrected Ljung–Box result không tái tạo ổn định;
- model cần refit với order, trend, scale hoặc split khác;
- forecast metrics thay đổi dù fix chỉ thuộc residual diagnostics;
- notebook clean execution thất bại;
- cần dependency hoặc architecture mới;
- implementation gate của E06 chưa được Human mở.

## 11. Approval gate

```text
E06_RESIDUAL_FIX_PLAN_CREATED=true
E06_RESIDUAL_FIX_PLAN_REVIEWED=true
E06_RESIDUAL_FIX_PLAN_APPROVED=true
E06_RESIDUAL_FIX_IMPLEMENTATION_AUTHORIZED=true
E06_RESIDUAL_FIX_IMPLEMENTED=true
E06_RESIDUAL_FIX_VALIDATED=true
E06_COMPLETED=false
```
