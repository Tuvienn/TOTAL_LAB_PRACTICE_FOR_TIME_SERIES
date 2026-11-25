# PHASE 09 — KẾT QUẢ CUỐI VÀ BÀN GIAO

## 1. Trạng thái

```text
Phase: 9 — Final Conclusion & Handoff
Official artifact: PASS
Selected model: xgboost_tuned
Training trong Phase 9: NO
Prediction trong Phase 9: NO
Holdout re-evaluation trong Phase 9: NO
Model lock changed: NO
```

Official machine-readable conclusion:
[phase_09_final_conclusion.json](../../outputs/results/phase_09_final_conclusion.json)

## 2. Kết quả forecasting chính

| Protocol | Candidate | MAE (MW) | RMSE (MW) | Population |
|---|---|---:|---:|---:|
| One-step | `xgboost_tuned` | 102,841 | 137,929 | 8.592 timestamps |
| Recursive 24h pooled | `xgboost_tuned` | 509,652 | 720,451 | 357 origins / 8.568 predictions |

`xgboost_tuned` tốt hơn Persistence và Seasonal Naive 24h trong cả one-step và
recursive 24-hour evaluation. Tuy nhiên recursive error tăng theo horizon; horizon
19 khó nhất với MAE 813,359 MW.

## 3. Trả lời câu hỏi bài tập

### XGBoost so với Linear Regression

Trên cùng 42.413 development validation samples:

| Model | Mean CV MAE (MW) | Mean CV RMSE (MW) |
|---|---:|---:|
| Linear Regression | 136,762 | 186,096 |
| Tuned XGBoost | 108,254 | 143,850 |

XGBoost có MAE thấp hơn khoảng **20,845%**. Đây là post-hoc development-only
comparison, không phải holdout comparison.

### Khi tăng số lag p

Error giảm mạnh từ `p=1` đến `p=24`, cải thiện nhẹ tại `p=48`, rồi tăng trở lại
tại `p=168`. `p=48` là mức tốt nhất quan sát trong registry đã thử, không phải tối
ưu toàn cục và không thay official feature schema.

### Khi nào XGBoost có thể tốt hơn ARIMA?

XGBoost có thể thuận lợi khi có nhiều lag/rolling/calendar predictors và quan hệ
phi tuyến hoặc interaction. ARIMA có thể thuận lợi với chuỗi ngắn, cấu trúc tuyến
tính sau stationarity treatment và nhu cầu diễn giải AR/MA gọn.

Practice 3 v2 **không triển khai ARIMA benchmark**, nên không có bằng chứng thực
nghiệm để tuyên bố XGBoost tốt hơn ARIMA.

## 4. Error và interpretation

- One-step mean signed error: **−1,192 MW**.
- Absolute-error P95: **273,097 MW**.
- Residual ACF lag 1: **0,2750**, cao hơn reference band khoảng **0,0211**.
- Residual còn short-lag và daily temporal structure, chưa giống white noise.
- Nhóm lag chiếm **93,467%** normalized gain; gain không phải causal importance.

## 5. Kết luận sử dụng

Model phù hợp nhất trong phạm vi bài cho one-step hourly forecasting với observed
history. Recursive 24-hour vẫn tốt hơn hai baselines nhưng có error accumulation,
không được suy rộng từ one-step metric.

Holdout là `historical_re_evaluation_holdout`, không phải truly unseen test set.
Project chưa có prediction interval, external validation, ARIMA benchmark hoặc
production drift monitoring; vì vậy không tuyên bố production readiness.

## 6. Bằng chứng validation

```text
Official JSON: PASS
Focused tests: 23/23 PASS
Table-style focused tests: 2/2 PASS
Presentation-loader focused tests: 2/2 PASS
Full regression suite: 212/212 PASS
Notebook clean execution: 27/27 code cells, 0 errors
Styled HTML outputs: 28/28
Notebook setup cell: 116 → 30 lines
README local links: PASS
AI technical review: PASS
Human final review: PENDING
```

Phase 9 không train, predict, tuning, thay model lock hoặc đánh giá lại holdout.
