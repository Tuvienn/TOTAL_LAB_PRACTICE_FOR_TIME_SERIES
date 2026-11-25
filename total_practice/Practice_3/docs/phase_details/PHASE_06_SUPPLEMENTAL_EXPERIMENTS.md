# PHASE 06 — SUPPLEMENTAL ASSIGNMENT EXPERIMENTS

## 1. Experiment identity

```text
Project: Practice_3
Parent phase: Phase 6 — Baseline, Training, Tuning & Model Lock
Purpose: bổ sung evidence để trả lời câu hỏi bài tập
Design status: APPROVED
Human design approval: GRANTED
Implementation authorization: GRANTED
Implementation status: READY — SOURCE/TESTS/PREFLIGHT PASS
Execution status: COMPLETED — PASS
Timing disclosure: designed after Phase 8 and after historical holdout evaluation
Selection authority: NONE
```

Đây là addendum của Phase 6, không phải phase mới trong workflow. Hai experiments
không thuộc model selection ban đầu và không được thay đổi `xgboost_tuned`, model
lock hoặc official Phase 6–8 conclusions đã tồn tại.

## 2. Mục tiêu

Bổ sung bằng chứng development-only để trả lời hai câu hỏi còn thiếu của đề:

1. XGBoost khác Linear Regression như thế nào trên cùng time-series validation
   population?
2. Chất lượng dự báo và chi phí dữ liệu/tính toán thay đổi ra sao khi tăng số lag
   liên tiếp `p`?

Phase 9 sẽ dùng official supplemental artifacts để viết câu trả lời cuối. Addendum
này chỉ tạo evidence, không sở hữu final conclusion.

## 3. Scientific disclosure và scope boundary

Các experiments được thiết kế sau khi historical holdout đã được xem trong Phase 7.
Do đó:

- chỉ được dùng development data và five-fold expanding-window validation;
- không được đọc, materialize feature hoặc đánh giá historical holdout;
- không được gọi kết quả là pre-registered model-selection evidence;
- không được thêm Linear Regression vào candidate registry ban đầu;
- không được thay model lock dù supplemental result tốt hơn XGBoost;
- không tuning hyperparameter hoặc chọn lại feature schema chính;
- kết quả phải mang nhãn `post_hoc_supplemental_evidence`.

Nếu Linear Regression tốt hơn `xgboost_tuned`, Phase 9 phải báo đây là giới hạn của
candidate registry ban đầu và là đề xuất cho lần chạy tương lai, không được sửa lại
lịch sử model selection.

## 4. Locked upstream evidence

```text
Phase 5 audit:
  outputs/results/phase_05_supervised_dataset.json
  SHA256: 21d6590a0b4acf5d58d26cb0af36f52b300eacd8a884d7153dad125c3ff81eb5

Phase 6 CV results:
  outputs/results/phase_06_cv_results.json
  SHA256: 1c1647a458b9261956e831045ed1c4b2f84791fd9843839bd088b31a239d31d4

Phase 6 model lock:
  outputs/results/phase_06_model_lock.json
  SHA256: ad31cb65daa36c394d7d5afc2cf0af333760c8e75ba718e702368e260db70eee

Feature contract SHA256:
  3191bb66323b96c305722511808a8c5dfa18a5a64b0527709696bc47f75dca5e

Supervised-data contract SHA256:
  5b1960fb6ca841df9e0dc619f54374152f793e75f596235408fdd3e7b337c649

Temporal-split contract SHA256:
  abcd404e9d6509564391a60e152faa7fd2241fa979333ed249c1fb55454f788b
```

Mọi checksum, package version, fold boundary hoặc prepared-data identity thay đổi
đều làm entry gate FAIL.

## 5. Experiment A — Linear Regression benchmark

### 5.1 Population

- Dùng đúng 108.083 eligible development X/y samples của Phase 5.
- Dùng đúng 22 features và exact feature order của model lock.
- Dùng đúng five expanding-window folds và exact validation timestamps của Phase 6.
- Không shuffle và không tạo split mới.

### 5.2 Estimator pipeline

```text
StandardScaler
→ LinearRegression
```

Với từng fold:

1. fit scaler chỉ trên fold-train X;
2. transform fold-train và fold-validation bằng scaler đã fit;
3. fit `LinearRegression` trên scaled fold-train;
4. predict exact fold-validation timestamps;
5. không persist scaler hoặc model binary.

Scaling nằm trong từng fold để tránh leakage. Không regularization và không tuning.

### 5.3 Metrics và comparison

Báo theo fold và aggregate:

- MAE;
- RMSE;
- MAE/RMSE population standard deviation với `ddof=0`;
- validation sample count;
- fit duration chỉ dùng mô tả, không dùng để chọn model.

So sánh chính là `linear_regression_scaled` với official `xgboost_tuned` CV evidence
trên cùng 42.413 validation predictions. XGBoost không được train lại cho comparison
này.

## 6. Experiment B — Lag-p sensitivity

### 6.1 Fixed p values

```text
p = [1, 6, 12, 24, 48, 168]
```

Với mỗi `p`, feature set chỉ gồm các lag liên tiếp:

```text
lag_1h, lag_2h, ..., lag_ph
```

Không thêm rolling hoặc calendar feature vào experiment này để thay đổi duy nhất là
số lag liên tiếp.

### 6.2 Alignment

Với target timestamp `T`:

```text
forecast origin = T - 1 hour
lag_kh = AEP_MW(T - k hours)
y = AEP_MW(T)
```

Current/future target không được xuất hiện trong X. Missing lag hoặc missing target
không được impute.

### 6.3 Natural eligibility và common comparison population

Với từng `p`, báo natural eligible sample count trước để cho thấy số sample bị mất
khi yêu cầu lịch sử dài hơn.

Để so sánh metric công bằng, mọi `p` phải dùng cùng train/validation timestamps hợp
lệ cho `p=168` trong từng approved temporal fold. Vì vậy khác biệt metric phản ánh
feature information, không phản ánh candidate dùng population khác nhau.

### 6.4 Fixed model

Mọi `p` dùng đúng locked `xgboost_tuned` parameters từ Phase 6:

```text
objective = reg:squarederror
tree_method = hist
random_state = 42
n_estimators = 500
max_depth = 7
learning_rate = 0.1
subsample = 0.7
colsample_bytree = 0.7
min_child_weight = 1
reg_alpha = 1.0
reg_lambda = 10.0
```

Không tuning lại theo `p`; không chọn một `p` mới cho official model.

### 6.5 Evidence

Với mỗi `p`, báo:

- feature count;
- natural eligible development samples;
- common train/validation samples theo fold;
- train MAE và validation MAE/RMSE theo fold;
- aggregate validation MAE/RMSE và `ddof=0` standard deviation;
- descriptive generalization gap;
- fit duration;
- thay đổi metric so với `p` liền trước và so với `p=1`.

Không được kết luận “nhiều lag hơn luôn tốt hơn”. Phase 9 phải dựa trên observed
curve để mô tả improvement, diminishing return hoặc degradation nếu có.

## 7. Execution boundary

AI được phép:

- tạo machine-readable contract;
- triển khai source, visualization và tests;
- chạy dependency/evidence preflight không fit project model;
- cung cấp exact Human execution command.

AI phải dừng trước project-data training. Human trực tiếp chạy hoặc resume:

```text
5 Linear Regression fold fits
6 p values × 5 XGBoost fold fits = 30 fits
Total project-data fits = 35
```

Run directory dự kiến:

```text
runs/P6_supplemental_<timestamp>_<execution_identity>/
├── P6_supplemental_<timestamp>_<execution_identity>.log
├── config_snapshot.json
├── run_metadata.json
├── checkpoint.json
├── linear_regression_results.json
└── lag_sensitivity_results.json
```

Execution phải hỗ trợ checkpoint/resume và không lưu estimator binary.

## 8. Fixed implementation ownership

```text
config/supplemental_experiments.json
src/practice_3_v2/analysis/supplemental_experiments.py
src/practice_3_v2/visualization/supplemental_experiments.py
tests/test_supplemental_experiments.py
outputs/results/phase_06_supplemental_linear_regression.json
outputs/results/phase_06_supplemental_lag_sensitivity.json
outputs/results/phase_06_supplemental_audit.json
outputs/figures/phase_06_supplemental_model_comparison.png
outputs/figures/phase_06_supplemental_lag_sensitivity.png
docs/logs/PHASE_06_SUPPLEMENTAL_EXECUTION.md
```

`phase_06_supplemental_audit.json` là completion marker và phải được promote cuối.
Official Phase 5–8 artifacts không được ghi đè.

Notebook chỉ đọc official supplemental JSON/PNG và trình bày trong một subsection
của Phase 6. Notebook không import source module, fit, transform hoặc predict.

## 9. Validation contract

Focused tests phải kiểm tra:

1. exact upstream checksums, packages, 22-feature order và five folds;
2. no holdout access hoặc materialization;
3. scaler fit trong fold-train, không fit toàn development trước CV;
4. Linear Regression dùng exact official Phase 6 validation timestamps;
5. known-array Linear Regression prediction và MAE/RMSE formulas;
6. exact `p` registry và lag formula/alignment;
7. current/future target mutation không đổi lag features tại `T`;
8. missing lag/target không được impute;
9. natural eligibility không tăng khi `p` tăng;
10. mọi `p` dùng exact common train/validation timestamps của `p=168`;
11. mọi `p` dùng exact locked XGBoost parameters và seed;
12. aggregate metrics dùng `ddof=0`;
13. checkpoint/resume identity và 35-task completeness;
14. interrupted/failed run không promote partial official bundle;
15. audit liên kết checksum của hai JSON và hai figures;
16. no tuning, no model selection, no model-lock mutation, no binary persistence;
17. notebook không chạy supplemental training;
18. không import runtime code từ legacy `practice_3`.

Sau Human execution phải chạy focused tests, full regression suite và notebook
clean-kernel execution.

## 10. Stop conditions

Dừng và báo Human nếu:

- upstream identity/fold/package khác contract;
- bất kỳ code path nào đọc historical holdout;
- Linear Regression hoặc lag-p candidates dùng khác comparison timestamps;
- feature có temporal leakage hoặc non-finite value;
- natural eligibility tăng khi `p` tăng;
- cần tuning, đổi p registry, đổi estimator hoặc thêm dependency;
- project-data training được khởi chạy bởi AI;
- official artifact cũ cần bị sửa hoặc ghi đè;
- result bị dùng để thay đổi existing model lock.

## 11. Completion gate

Supplemental experiments chỉ hoàn thành khi:

- Human phê duyệt phase addendum này;
- source/tests/preflight PASS;
- Human execution hoàn tất đủ 35 fits;
- official JSON/PNG/audit bundle hợp lệ;
- focused và full regression tests PASS;
- notebook trình bày kết quả, clean execution PASS;
- AI technical review PASS;
- Human review supplemental results.

Sau đó Phase 9 mới được thiết kế chi tiết và sử dụng supplemental evidence để trả
lời hai câu hỏi bài tập.

## 12. Implementation checkpoint — 25/10/2026

```text
Source implementation: PASS
Visualization implementation: PASS
Focused tests after execution: 23/23 PASS
Full regression suite after execution: 176/176 PASS
Preflight: PASS
Human project-data execution: COMPLETED — 35/35 FITS
Official supplemental artifacts: PASS
Artifact technical review: PASS
Notebook presentation: PASS — 30/30 CODE CELLS, NO ERRORS
Current gate: HUMAN SUPPLEMENTAL RESULT REVIEW
```

Preflight xác nhận đúng 5 folds, 22 official features, registry
`p = [1, 6, 12, 24, 48, 168]`, natural eligibility giảm đơn điệu và common
`p=168` comparison population khớp 108.083 eligible samples của Phase 5. Human đã
hoàn tất run `P6_supplemental_20261025_165310_678c64f3`; checksum, checkpoint,
official bundle và model-lock immutability đều PASS technical review.
