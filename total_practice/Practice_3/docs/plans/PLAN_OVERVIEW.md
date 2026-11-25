# PRACTICE 3 — PLAN OVERVIEW

## 1. Mục đích

Tài liệu này là bản đồ tổng thể của Practice 3. Nó cho biết mỗi phase sở hữu công việc gì, phụ thuộc vào phase nào và đang ở trạng thái nào.

Phase detail vẫn là nguồn thiết kế chi tiết. `docs/status/current_status.md` vẫn là nguồn trạng thái execution chính thức.

## 2. Quy ước trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| `APPROVED / PASS` | Đã triển khai, validation PASS và Human đã duyệt kết quả |
| `DESIGN APPROVED` | Thiết kế đã được duyệt nhưng chưa có quyền triển khai |
| `IMPLEMENTATION READY` | Source/tests/preflight đã PASS, đang chờ Human execution |
| `TECHNICAL PASS` | Execution/artifacts/tests đã PASS, đang chờ Human duyệt kết quả |
| `PLANNED` | Chỉ mới xác định phạm vi tổng thể, chưa có phase detail được duyệt |

## 3. Bản đồ phase

| Phase | Nội dung | Input chính | Output chính | Trạng thái |
|---|---|---|---|---|
| 0 | Problem & Forecasting Definition | Đề bài, raw dataset contract | Forecasting, temporal, metric và claim contracts | APPROVED / PASS |
| 1 | Structural Data Preparation | Raw dataset, data contract | Prepared hourly dataset và data-quality audit | APPROVED / PASS |
| 2 | Temporal Split & Validation Design | Prepared dataset, forecasting contract | Development/holdout boundaries và 5 expanding folds | APPROVED / PASS |
| 3 | TRAIN-only EDA | Development subset | EDA JSON và 6 official figures | APPROVED / PASS |
| 4 | Feature Engineering | Prepared data, TRAIN-only EDA evidence | 22-feature schema và feature-validation audit | APPROVED / PASS |
| 5 | X/y Construction & Split Application | Feature schema, temporal split | Aligned supervised population và CV fold audit | APPROVED / PASS |
| 6 | Baseline, Training, Tuning & Model Lock | Phase 5 X/y population | CV comparison và locked model specification | APPROVED / PASS |
| 7 | Final Forecasting & Evaluation | Locked model, sealed historical holdout | One-step và recursive 24-hour evaluation | APPROVED / PASS |
| 8 | Error & Interpretation Analysis | Final predictions, locked model | Residual/error analysis và model interpretation | APPROVED / PASS |
| 9 | Final Conclusion | Toàn bộ validated evidence | Kết luận, giới hạn và final handoff | TECHNICAL PASS — HUMAN FINAL REVIEW |

Phase 6 có một supplemental addendum ở trạng thái `APPROVED / PASS`: Linear
Regression benchmark và lag-`p` sensitivity. Human đã hoàn tất 35 fits; official
artifacts và post-execution tests đã PASS. Addendum không thay đổi Phase 6 model
lock hoặc candidate selection đã được Human phê duyệt. Notebook presentation và
clean execution đã PASS; Human đã chấp nhận kết quả trước khi mở Phase 9.

## 4. Dependency chain

```text
P0 contract
  ↓
P1 prepared data
  ↓
P2 temporal boundaries
  ↓
P3 TRAIN-only evidence
  ↓
P4 time-safe feature schema
  ↓
P5 aligned X/y and CV populations
  ↓
P6 TRAIN-only model lock
  ↓
P7 historical holdout evaluation
  ↓
P8 error and interpretation evidence
  ↓
P9 conclusion
```

Không được dùng output của phase sau để thay đổi quyết định đã khóa ở phase trước.

## 5. Phase 6 — phạm vi đã duyệt

Phase 6 sẽ:

- chạy Persistence và Seasonal Naive 24 baselines;
- train XGBoost baseline và Random Forest trên cùng five-fold expanding-window population;
- tìm kiếm 24 cấu hình tuned XGBoost theo protocol đã khóa;
- báo MAE, RMSE và MAE standard deviation;
- chọn một candidate và ghi model lock trước khi đánh giá holdout.

Phase 6 chưa được phép:

- mở historical holdout target;
- chọn model theo holdout result;
- tạo final prediction hoặc final conclusion;
- để AI bắt đầu hoặc resume long training. AI phải dừng sau preflight và cung cấp
  lệnh; Human là người trực tiếp chạy training trên Terminal.

## 6. Phase 8–9 boundary

Phase 8 đã execution PASS, technical review PASS và được Human phê duyệt.
Phase 9 đã hoàn tất phạm vi kỹ thuật được duyệt:

- Phase 7 đã refit locked model trên full development và đánh giá historical holdout.
- Phase 8 đã tạo official analysis bundle và được Human phê duyệt.
- Phase 9 đã tổng hợp kết luận, trả lời ba câu hỏi bài tập, ghi giới hạn khoa học,
  cập nhật notebook/README và tạo official final JSON.
- Phase 9 không train, predict, thay model lock hoặc đánh giá lại holdout.
- Focused tests 23/23, table-style tests 2/2, presentation-loader tests 2/2,
  full regression 212/212 và notebook 27/27 code cells đều
  PASS; Human final review vẫn đang chờ.

Các quyết định chi tiết cho từng phase chỉ được viết khi phase đó chuẩn bị triển khai.

## 7. Current gate

```text
Phase 7 design: APPROVED
Phase 7 implementation: COMPLETED
Phase 7 Human evaluation: COMPLETED
Phase 7 technical review: PASS
Phase 7 Human result review: APPROVED
Selected candidate: xgboost_tuned
One-step holdout MAE: 102.840784 MW
Recursive 24-hour pooled MAE: 509.651550 MW
Holdout label: historical_re_evaluation_holdout
Phase 8 design: APPROVED
Phase 8 implementation: COMPLETED
Phase 8 preflight: PASS
Phase 8 Human execution: COMPLETED — PASS
Phase 8 technical review: PASS
Phase 8 Human result review: APPROVED
Phase 9 design: APPROVED
Phase 9 implementation: COMPLETED — TECHNICAL PASS
Phase 9 official artifact: PASS
Phase 9 focused tests: 23/23 PASS
Full regression suite: 212/212 PASS
Notebook clean execution: 27/27 code cells, 0 errors
Human final review and handoff: PENDING
```

Bước tiếp theo là Human review official Phase 9 evidence và notebook. Chỉ sau khi
Human phê duyệt final handoff mới đổi trạng thái Phase 9 thành `APPROVED / PASS`.
