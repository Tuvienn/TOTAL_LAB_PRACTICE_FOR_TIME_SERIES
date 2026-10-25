# PRACTICE 3 V2 — PROJECT WORKFLOW

## 1. Mục đích

Tài liệu này mô tả workflow kỹ thuật end-to-end của Practice 3 v2, luồng artifact giữa các phase và validation gate cần vượt qua trước khi chuyển phase.

Đây không phải workflow quản trị AI–Human. Quy tắc phê duyệt và triển khai nằm tại `docs/rules/workflow_rule.md`.

## 2. Official workflow

```text
PHASE 0 — Problem & Forecasting Definition
        ↓
PHASE 1 — Structural Data Preparation
        ↓
PHASE 2 — Temporal Split & Validation Design
        ↓
PHASE 3 — TRAIN-only EDA
        ↓
PHASE 4 — Feature Engineering
        ↓
PHASE 5 — X/y Construction & Split Application
        ↓
PHASE 6 — Baseline, Training, Tuning & Model Lock
        ↓
PHASE 7 — Final Forecasting & Evaluation
        ↓
PHASE 8 — Error & Interpretation Analysis
        ↓
PHASE 9 — Final Conclusion
```

## 3. Phase workflow

### Phase 0 — Problem & Forecasting Definition

Chốt:

- dataset và target contract;
- one-step primary task;
- recursive 24-hour secondary task;
- temporal boundary;
- metric và model-selection policy;
- phạm vi claim.

Gate: không xử lý dữ liệu hoặc train model khi forecasting contract chưa được duyệt.

### Phase 1 — Structural Data Preparation

```text
immutable raw CSV
→ validate schema/checksum
→ strict datetime normalization
→ chronological sort
→ duplicate aggregation
→ complete hourly timeline
→ preserve missing targets
→ prepared dataset + audit
```

Gate: schema, chronology, source conservation và data-quality counts phải PASS.

### Phase 2 — Temporal Split & Validation Design

Khóa development/holdout boundaries và tạo 5 expanding-window folds. Split theo timestamp, không shuffle và không dùng row order để thay thế time semantics.

Gate: mọi sample thuộc đúng temporal region; holdout vẫn bị cô lập.

### Phase 3 — TRAIN-only EDA

Phân tích missingness, distribution, trend, seasonality, lag correlation và anomaly trên development period. EDA chỉ đề xuất bounded feature hypotheses, không tự khóa feature schema.

Gate: không đọc holdout target và mọi figure phải có provenance.

### Phase 4 — Feature Engineering

Tạo 22 time-safe features gồm lag, rolling và calendar features. Mọi lag/rolling value tại forecast origin phải chỉ dùng thông tin có sẵn trong quá khứ.

Gate: alignment, leakage, schema, determinism và recursive compatibility phải PASS.

### Phase 5 — X/y Construction & Split Application

```text
feature timestamp t
→ X(t) từ lịch sử đến t
→ y(t+1)
→ loại sample có invalid X hoặc missing target
→ áp dụng 5 expanding folds
→ tạo full-development population
```

Gate: X/y alignment, exact 22-feature order, sample conservation và fold ownership phải PASS.

### Phase 6 — Baseline, Training, Tuning & Model Lock

So sánh trên cùng validation timestamps:

- Persistence (`lag_1h`);
- Seasonal Naive 24 (`lag_24h`);
- XGBoost baseline;
- Random Forest;
- tuned XGBoost.

Selection chỉ dùng one-step TRAIN-only CV theo thứ tự MAE → RMSE → MAE standard deviation → simplicity order. Output là comparison evidence và model specification đã khóa; không mở holdout.

Gate: dependency smoke test, identical validation population, deterministic metrics và model-lock contract phải PASS.

Execution boundary: AI chuẩn bị code, tests, preflight và lệnh chạy rồi phải dừng.
Human trực tiếp chạy hoặc resume training trên Terminal. AI chỉ review artifacts
sau khi Human thông báo execution đã kết thúc hoặc bị gián đoạn.

### Phase 7 — Final Forecasting & Evaluation

Phase 7 đã:

- đọc locked model specification;
- refit model trên full development population;
- mở historical re-evaluation holdout đúng một lần theo protocol;
- đánh giá one-step và recursive 24-hour riêng biệt;
- lưu final predictions, metrics và figures.

Phase 7 đã PASS technical review và được Human phê duyệt.

### Phase 8 — Error & Interpretation Analysis

Phân tích residual, error theo thời gian/horizon/regime và model interpretation từ official Phase 7 evidence. Phase này không được quay lại đổi model dựa trên holdout error.

Source, tests và preflight Phase 8 đã PASS. Human đã refit đúng locked XGBoost trên
full development population; official error/interpretation bundle, technical review
và notebook clean execution đều PASS. Phase 8 đã được Human phê duyệt.

### Phase 9 — Final Conclusion

Tổng hợp kết quả, trả lời câu hỏi bài tập, nêu giới hạn dữ liệu và giới hạn historical re-evaluation, đồng thời hoàn thiện notebook/README và trạng thái bàn giao.

Phase 9 đã tạo deterministic final conclusion từ 15 upstream artifact identities,
không train/predict và không đánh giá lại holdout. Official JSON, result document,
README và notebook đã PASS technical validation; Human final handoff review đang
chờ.

## 4. Data and artifact flow

```text
datasets/raw/AEP_hourly.csv
        ↓ Phase 1
datasets/processed/aep_hourly_prepared.csv
        ↓ Phase 2–5
outputs/results/phase_02...phase_05*.json
        ↓ Phase 6
outputs/results/phase_06_cv_results.json
outputs/results/phase_06_model_lock.json
        ↓ Phase 7
final prediction/evaluation artifacts
        ↓ Phase 8
error and interpretation artifacts
        ↓ Phase 9
final conclusion and handoff
```

## 5. Storage ownership

| Nơi lưu | Vai trò |
|---|---|
| `config/` | Machine-readable approved contracts |
| `datasets/raw/` | Raw data bất biến |
| `datasets/processed/` | Dữ liệu dẫn xuất có thể tái tạo |
| `src/practice_3_v2/` | Pipeline, analysis, metric và visualization logic |
| `tests/` | Contract, alignment, leakage và determinism tests |
| `runs/` | Checkpoint/execution state cục bộ, không phải official evidence |
| `outputs/results/` | Official machine-readable results |
| `outputs/figures/` | Official figures |
| `notebooks/` | Presentation-only, chỉ đọc official artifacts |
| `docs/` | Rules, plans, phase details, logs và status |

## 6. Universal validation rules

Mọi phase phải tuân thủ:

1. Không sửa raw dataset.
2. Không dùng thông tin tương lai để tạo feature hoặc sample.
3. Không dùng holdout để EDA, tuning, chọn feature hoặc chọn model.
4. Không ghi `PASS` nếu chưa có evidence thực tế.
5. Không chuyển phase khi validation gate hoặc Human review chưa hoàn tất.
6. Notebook không chạy pipeline, training hoặc prediction.
7. Scientific validity error phải dừng và báo Human, không silently fix.

## 7. Current position

```text
Completed and Human-approved: Phase 0–8 + Phase 6 Supplemental
Phase 7 technical review: PASS
Locked candidate: xgboost_tuned
Historical holdout evaluated: true
Historical holdout label: historical_re_evaluation_holdout
Phase 8 design: APPROVED
Phase 8 implementation/preflight: PASS
Phase 8 Human execution: COMPLETED — PASS
Phase 8 technical review: PASS
Phase 8 Human result review: APPROVED
Phase 9 design: APPROVED
Phase 9 implementation: COMPLETED — TECHNICAL PASS
Phase 9 focused/table-style/presentation-loader/full tests: 23/23, 2/2, 2/2 and 203/203 PASS
Phase 9 notebook: 34/34 code cells, 0 errors
Human final review and handoff: PENDING
```
