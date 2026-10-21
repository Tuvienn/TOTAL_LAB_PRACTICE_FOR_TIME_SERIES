# EXERCISE 06 — VẤN ĐỀ RESIDUAL DIAGNOSTICS

## 1. Thông tin vấn đề

```text
Practice: Practice_2
Exercise: EXERCISE_06
Issue type: Scientific diagnostics error
Current state: RESOLVED_AND_VALIDATED
Affected result: ARIMA/SARIMA residual interpretation
Forecast metrics affected: NO
E06 completion impact: BLOCKING
Review date: 2026-10-20
```

Issue này được phát hiện khi review read-only notebook
`notebooks/Practice_2_advanced_sarima.ipynb`. Không có source code, notebook hoặc
output nào được sửa trong quá trình xác minh.

## 2. Hành vi kỳ vọng

Residual diagnostics của mỗi fitted model phải:

1. lấy residual từ chính fitted result;
2. đọc `loglikelihood_burn` của từng model;
3. loại toàn bộ residual thuộc giai đoạn khởi tạo trước khi tính mean, ACF và
   Ljung–Box;
4. dùng `model_df = p + q + P + Q`, không tính `d`, `D` hoặc seasonal period;
5. ghi rõ số residual còn lại, burn-in, lag, alpha và p-value;
6. giới hạn kết luận white-noise vào đúng các lag đã kiểm định;
7. dùng cùng post-burn-in residual series cho bảng và biểu đồ.

## 3. Hành vi quan sát được

Notebook hiện tạo residual như sau:

```python
residuals = pd.Series(
    np.asarray(fitted.resid),
    index=train_model.index,
).dropna()
```

Logic này không loại `fitted.loglikelihood_burn`. Vì vậy residual dùng cho mean,
time plot, ACF và Ljung–Box chứa các giá trị khởi tạo không đại diện cho model error
sau khi state-space initialization hoàn tất.

Các residual khởi tạo nổi bật trong output hiện tại:

```text
ARIMA first residual: 4.718499
SARIMA first residual: 4.718499
SARIMA seasonal-initialization residual near observation 13: -2.385002
```

Hai spike này làm scale của residual plot bị kéo giãn và làm ACF/Ljung–Box không phản
ánh đúng residual sau burn-in.

## 4. Bằng chứng tái tạo

Read-only reproduction dùng:

```text
Dataset: datasets/raw/airline-passengers.csv
Raw SHA-256: 8cb51be753a718d9be5d76d7e238cc224792754676adc21faa59e954b0201621
Training observations: 115
Analysis scale: natural_log
ARIMA order: (1,1,1)
SARIMA order: (1,1,1)(0,1,1,12)
Ljung–Box lags: 12, 24
Alpha: 0.05
statsmodels: 0.15.0
```

### 4.1. Kết quả khi còn residual thuộc giai đoạn khởi tạo

| Model | Burn-in bị notebook bỏ sót | Lag | Ljung–Box p-value | Diễn giải cũ của notebook |
|---|---:|---:|---:|---|
| ARIMA | 1 | 12 | 0.999957 | Không phát hiện autocorrelation |
| ARIMA | 1 | 24 | 1.000000 | Không phát hiện autocorrelation |
| SARIMA | 13 | 12 | 0.010010 | Còn autocorrelation |
| SARIMA | 13 | 24 | 0.408396 | Không phát hiện autocorrelation |

### 4.2. Kết quả diagnostics sau khi áp dụng model burn-in

| Model | Burn-in đã áp dụng | Số residual | Lag | Ljung–Box p-value | Quyết định tại alpha 0.05 |
|---|---:|---:|---:|---:|---|
| ARIMA | 1 | 114 | 12 | 2.944816e-16 | Bác bỏ H0 không có autocorrelation |
| ARIMA | 1 | 114 | 24 | 2.308263e-27 | Bác bỏ H0 không có autocorrelation |
| SARIMA | 13 | 102 | 12 | 0.573996 | Không bác bỏ H0 |
| SARIMA | 13 | 102 | 24 | 0.473545 | Không bác bỏ H0 |

Post-burn-in residual means from the same reproduction:

```text
ARIMA residual mean: 0.011221
SARIMA residual mean: 0.001164
```

Các số trên là diagnostic evidence cho fix plan, chưa phải canonical E06 result.
Canonical values chỉ được ghi sau approved implementation, clean execution và output
inspection.

## 5. Nguyên nhân gốc

Root cause nằm trong notebook orchestration: E06 tự triển khai residual diagnostics
thay vì sử dụng reusable owner hiện có tại
`src/practice_2/analysis/forecasting.py`.

`compute_residual_diagnostics()` của E5 đã loại `loglikelihood_burn`, nhưng E06 không
gọi helper này. Helper hiện cũng chỉ tính `model_df` từ non-seasonal `p + q`; trước
khi dùng cho SARIMA, nó cần được mở rộng để cộng thêm seasonal `P + Q` mà không làm
thay đổi kết quả non-seasonal của E5.

## 6. Tác động

```text
Dataset validation: unaffected
Chronological split: unaffected
ADF and differencing evidence: unaffected
ACF/PACF candidate evidence: unaffected
Model convergence: unaffected
Forecast index alignment: unaffected
MAE/RMSE comparison: unaffected
Residual plots: invalid
Residual ACF: invalid
Ljung–Box interpretation: invalid
Model adequacy conclusion: invalid
E06 validation/completion: blocked
```

Kết luận hiện tại bị đảo chiều:

- không được kết luận ARIMA không còn autocorrelation;
- không được kết luận SARIMA còn autocorrelation tại lag 12 từ output cũ;
- corrected evidence dự kiến cho thấy ARIMA còn autocorrelation mạnh, còn SARIMA
  không có bằng chứng autocorrelation tại lag 12 và 24;
- kết quả này vẫn không chứng minh residual SARIMA là white noise ở mọi lag hoặc mọi
  khía cạnh phân phối.

## 7. Ranh giới sửa lỗi

Fix phải sửa residual extraction tại reusable source owner, thêm seasonal model
degrees of freedom, kiểm thử regression cho ARIMA/SARIMA, tạo lại residual artifacts
và cập nhật phần residual trong notebook, execution log và status.

Fix không được:

- thay raw dataset;
- đổi train/test boundary;
- đổi log scale, `d`, `D`, `s` hoặc model orders;
- chọn model mới từ test metrics;
- thay inverse-transform policy;
- sửa E01–E05 validated results;
- tự đánh dấu E06 completed.

## 8. Bước xử lý đã được phê duyệt

Human đã duyệt `docs/fix_plans/exercise_06_residual_diagnostics_fix_plan.md`. Fix đã
được triển khai tại reusable source owner, kiểm thử và chạy lại notebook từ kernel
sạch.

## 9. Kết quả sửa lỗi

```text
ARIMA burn-in / residual observations: 1 / 114
SARIMA burn-in / residual observations: 13 / 102
ARIMA model_df: 2
SARIMA model_df: 3
ARIMA Ljung–Box p-values at 12/24: 2.944816e-16 / 2.308263e-27
SARIMA Ljung–Box p-values at 12/24: 0.573996 / 0.473545
Targeted E05/E06 tests: 12 passed
Full Practice 2 tests: 30 passed
Advanced notebook clean execution: PASS
Raw checksum unchanged: PASS
```

ARIMA còn autocorrelation tại cả hai lag đã kiểm tra. SARIMA chưa có bằng chứng
autocorrelation tại lag 12/24; kết luận này không được suy rộng thành white noise ở
mọi lag hoặc mọi khía cạnh phân phối. Theo Phương án A đã được Human chọn, E6 được
giữ ở mức exploratory và không được đánh dấu `COMPLETED`.
