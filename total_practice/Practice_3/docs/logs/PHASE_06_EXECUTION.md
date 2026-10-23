# PHASE 06 — EXECUTION LOG

## 1. Trạng thái

```text
Phase: 06 — Forecasting & Evaluation
Run ID: P6_final_evaluation_20261022_234000_26d167d7
Execution time: 2026-10-22 23:40:00 → 2026-10-23 00:02:29 (UTC+07:00)
Final status: COMPLETED
Completed units: 10/10
Official outputs promoted: YES
Phase result: PASS
```

## 2. Final-test opening

```text
State before: SEALED
Purpose: FINAL_EVALUATION_ONLY
Opening events: 1
Opened after Phase 5 model lock: YES
State after: OPENED_FOR_FINAL_EVALUATION
Post-test model change: NO
```

Final test chỉ được mở sau khi entry gate và Phase 5 model lock đạt `PASS`.

## 3. Approved implementation fix

Run đầu tiên hoàn thành năm one-step units rồi dừng trước multi-step vì supervised target có sparse timeline, trong khi validator yêu cầu hourly index liên tục tuyệt đối.

Fix đã được Human phê duyệt:

- reindex supervised target về hourly grid đầy đủ;
- biểu diễn giờ thiếu bằng `NaN`, không impute target;
- loại full origin nếu future block hoặc 168-hour history không finite;
- giữ nguyên model lock, parameters, split và forecasting protocols;
- migration failed run sang execution identity mới;
- giữ opening event duy nhất và năm one-step artifacts đã qua checksum.

Tài liệu liên quan:

- `docs/error_resolution/phase_06_multistep_timeline_error_analysis.md`
- `docs/error_resolution/phase_06_multistep_timeline_fix_plan.md`

## 4. Evaluation populations

```text
One-step rows per candidate: 8,592
One-step candidates: 5
Total one-step prediction rows: 42,960

Scheduled multi-step origins: 365
Eligible origins: 350
Excluded origins: 15
Non-finite future block: 8
Insufficient/non-finite history: 7
Horizon: 24 hours
Total multi-step prediction rows: 42,000
```

Mọi candidate dùng cùng timestamps/origins và cùng actual values trong từng protocol.

## 5. One-step final-test results

| Candidate | MAE | RMSE |
|---|---:|---:|
| Seasonal Naive 24 | 935.8021 | 1212.2738 |
| Persistence | 408.9788 | 520.9399 |
| XGBoost baseline | 131.5880 | 172.5969 |
| **XGBoost tuned** | **113.3278** | **150.2444** |
| Random Forest | 130.7309 | 176.6542 |

`xgboost_tuned` là candidate tốt nhất theo one-step MAE và RMSE. Đây cũng là candidate đã được chọn bằng TRAIN-only CV ở Phase 5.

## 6. Recursive 24-hour results

| Candidate | Pooled MAE | Pooled RMSE |
|---|---:|---:|
| Seasonal Naive 24 | 933.7917 | 1212.2697 |
| Persistence | 1453.0619 | 1781.2956 |
| XGBoost baseline | 607.0989 | 828.8571 |
| **XGBoost tuned** | **547.5021** | **763.0003** |
| Random Forest | 656.5206 | 890.9994 |

`xgboost_tuned` có pooled MAE và RMSE thấp nhất trong recursive 24-hour evaluation. One-step và multi-step metrics không được gộp thành một kết quả duy nhất.

## 7. Independent validation

```text
Checkpoint status: COMPLETED
Run metadata status: COMPLETED
Opening event count: 1
All candidate/protocol units: 10/10 PASS
Official artifact checksums: PASS
One-step population and finite-value checks: PASS
Multi-step origin/horizon and finite-value checks: PASS
Independent MAE/RMSE recalculation: PASS
Automated tests: 136/136 PASS
git diff check: PASS
```

## 8. Official artifacts

| Artifact | SHA-256 |
|---|---|
| `phase_06_one_step_predictions.csv` | `c676c9464101b6886ef7bb502037ba8767dc89729ae46617871a7d760ba4c566` |
| `phase_06_one_step_metrics.json` | `fbfcb29efc143a8d1b4480ec25cd96fbdfda617ce300b237d90d064ccdb82eda` |
| `phase_06_multistep_predictions.csv` | `4a7cb7af34e6a611f7f7302fa684e19692456251f391d4ef418d36576dc1689e` |
| `phase_06_multistep_metrics.json` | `8043fb91cbeb11db0651ec025fdf4136403717e7f6ac077bd22ce72290a9bb6d` |
| `phase_06_evaluation_audit.json` | `1539d38b6ae8397198f9a30ee67c744fb0d352e24876dd36f7402aac461c5f3c` |
| `phase_06_one_step_full_test.png` | `24c4203656ecb1c911cb03cdf5af4f0686e07a70146985c2829ddf8f5dd097f1` |
| `phase_06_one_step_first_14_days.png` | `864f034734f5269da609bf348ae3a7bbca33c4b2a5245ca4e932b9eb0f4e3d51` |
| `phase_06_multistep_error_by_horizon.png` | `6ef3df40556596018d47ba089af7a3447e8514622c89a93a286998cfc23b539b` |

## 9. Kết luận checkpoint

```text
ENTRY GATE: PASS
FINAL-TEST OPENING: PASS — ONE EVENT
ONE-STEP EVALUATION: PASS
RECURSIVE 24-HOUR EVALUATION: PASS
TRANSACTIONAL PROMOTION: PASS
POST-TEST MODEL CHANGE: NO
PHASE 06: PASS
```

Phase 7 được phép sử dụng Phase 5 CV evidence và Phase 6 official final-test artifacts để thực hiện interpretation/final analysis. Phase 7 không được tuning hoặc chọn lại model dựa trên final test.
