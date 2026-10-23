# PHASE 07 — EXECUTION LOG

## 1. Phạm vi

Phase 7 tổng hợp evidence Phase 1–6, refit đúng `xgboost_tuned` trên full top-level TRAIN để lấy gain importance, phân tích rolling/lag-p và tạo kết luận cuối. Phase này không tuning, không chọn lại model và không dùng final test để fit.

## 2. Lệnh Human đã chạy

```bash
python -m practice_3.analysis.interpretation --run
```

Thời điểm tạo official outputs: `2026-10-23 02:59:15 +0700`.

## 3. Kết quả execution

```text
candidate_id: xgboost_tuned
feature_configuration: lag_only_p168
training_population: full_top_level_train
train_rows: 108083
feature_count: 168
training_seconds: 7.7639
warnings: 0
final_test_used_for_fit: false
prediction_executed: false
binary_model_persisted: false
status: PASS
```

Feature đứng đầu là `lag_1`, normalized gain `0.8021766599`. Đây là fitted-model importance, không phải causal effect.

## 4. Official outputs

| Artifact | SHA-256 |
|---|---|
| `outputs/results/phase_07_feature_importance.csv` | `d39cd856e28d8b17612a668414b406d96b6e4e2eefef258f69eb49c790fa1a83` |
| `outputs/results/phase_07_comparison_summary.csv` | `83ed8ca96b547ad350b5e4bfdc5e2407479a80f04afe9d6ad7067d160737cb03` |
| `outputs/results/phase_07_interpretation_summary.json` | `48671f1379d23bf930c6425c2ef3cedd1c1f3ddeefd3a60f2a0ac0cf882ba419` |
| `outputs/results/phase_07_final_analysis.md` | `3ebe1334326a4675cd2909d8ea06d724323542529074127159a6d88b2deba106` |
| `outputs/figures/phase_07_top20_feature_importance.png` | `ba4bce261788ab77a50ec2308890366298fefba8f52b798bf0c2fdd2563b5ada` |

## 5. Post-execution validation

```text
importance rows: 168/168
feature identity: lag_1 ... lag_168, complete
rank identity: 1 ... 168, complete
normalized gain sum: 1.0 within numeric tolerance
comparison rows: 21
TRAIN-only CV and final-test evidence separated: PASS
one-step and recursive 24-hour evidence separated: PASS
Linear Regression and ARIMA labels: THEORETICAL_EXPLANATION
input checksums validated: 12/12
Markdown links validated: 10/10
Top-20 figure visual review: PASS
focused Phase 7 tests: 10/10 PASS
full project regression suite: 146/146 PASS
git diff check: PASS
```

## 6. Kết luận

Phase 7 đáp ứng output contract và validation criteria trong detailed design. Official artifacts có thể dùng cho bước presentation/documentation tiếp theo. Trạng thái cuối: `PASS`.
