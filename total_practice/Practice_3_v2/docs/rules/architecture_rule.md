# QUY TẮC KIẾN TRÚC — PRACTICE 3 V2

## 1. Phạm vi

Tài liệu này áp dụng cho `total_practice/Practice_3_v2/`. Đây là project độc lập dùng để xây dựng lại Practice 3 theo workflow time-series end-to-end. `Practice_3/` là legacy evidence và không được chỉnh sửa từ quá trình triển khai v2.

## 2. Workflow chuẩn

```text
Phase 0 — Problem & Forecasting Definition
Phase 1 — Structural Data Preparation
Phase 2 — Temporal Split & Validation Design
Phase 3 — TRAIN-only EDA
Phase 4 — Feature Engineering
Phase 5 — X/y Construction & Split Application
Phase 6 — Baseline, Training, Tuning & Model Lock
Phase 7 — Final Forecasting & Evaluation
Phase 8 — Error & Interpretation Analysis
Phase 9 — Final Conclusion
```

Mỗi phase phải hoàn thành validation gate và được Human review trước khi phase tiếp theo được triển khai.

## 3. Ranh giới với legacy project

- Không import runtime code trực tiếp từ package `practice_3`.
- Không đọc kết quả, model lock, prediction hoặc metric trong `Practice_3/outputs` để tạo official result cho v2.
- Logic legacy chỉ được migrate có chọn lọc, review và kiểm thử lại trong namespace `practice_3_v2`.
- Không ghi file từ v2 vào `Practice_3/`.

## 4. Vòng đời dữ liệu

```text
raw data bất biến
→ structural preparation
→ khóa temporal boundaries
→ TRAIN-only EDA
→ time-safe features
→ aligned X/y
→ TRAIN-only validation và model selection
→ locked holdout evaluation
→ error/interpretation analysis
→ conclusion
```

`datasets/raw/AEP_hourly.csv` không được ghi đè, sort, impute, deduplicate hoặc thay đổi schema. Dữ liệu dẫn xuất phải được tạo trong `datasets/processed/` từ source code và configuration của v2.

## 5. Trách nhiệm thư mục

- `config/`: forecasting contract, feature, validation và model configuration đã được duyệt.
- `datasets/raw/`: dữ liệu nguồn bất biến.
- `datasets/processed/`: dữ liệu dẫn xuất có thể tái tạo.
- `src/practice_3_v2/data/`: validation, preparation, split và supervised-data construction.
- `src/practice_3_v2/analysis/`: EDA, feature engineering, training, forecasting, metrics và interpretation.
- `src/practice_3_v2/visualization/`: hàm trực quan hóa tái sử dụng.
- `tests/`: kiểm tra schema, chronology, alignment, leakage, split, metric và deterministic behavior.
- `runs/`: trạng thái execution cục bộ, không phải official result và không commit.
- `outputs/results/`: official machine-readable artifacts đã qua validation gate.
- `outputs/figures/`: official figures có provenance.
- `notebooks/`: chỉ trình bày official artifacts; không sở hữu training hoặc prediction logic.
- `docs/`: rules, phase details, status, execution logs và error-resolution evidence.

## 6. Split và leakage

- Temporal boundaries phải được khóa trước EDA.
- EDA phục vụ thiết kế feature chỉ được đọc TRAIN/development period.
- Final holdout không được dùng để chọn feature, model hoặc hyperparameter.
- Transformation có bước `fit` chỉ được fit trong fold-train hoặc full TRAIN theo đúng giai đoạn.
- Feature tại thời điểm `t` chỉ được dùng thông tin có sẵn tại forecast origin.

## 7. Artifact và notebook

Official artifact phải ghi được input identity, configuration, timestamp range, status và provenance cần thiết để kiểm tra lại. Notebook chỉ đọc artifact đã được duyệt và không chạy lại pipeline, training hoặc prediction.

## 8. Thay đổi kiến trúc

Không đổi phase ownership, folder responsibility, holdout policy hoặc dependency nếu chưa thảo luận và được Human duyệt.
