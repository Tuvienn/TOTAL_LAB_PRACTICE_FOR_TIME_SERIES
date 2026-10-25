# PHASE 08 — ERROR & INTERPRETATION ANALYSIS

## 1. Phase identity

```text
Project: Practice_3_v2
Phase: 8
Name: Error & Interpretation Analysis
Design status: APPROVED
Human design approval: GRANTED
Implementation authorization: GRANTED
Execution status: COMPLETED — PASS — TECHNICAL REVIEW PASS
Human result review: APPROVED
```

## 2. Mục tiêu

Phân tích official Phase 7 prediction evidence để trả lời:

- model sai bao nhiêu và có bias theo hướng nào;
- error thay đổi theo thời gian, load regime và forecast horizon ra sao;
- timestamp nào có one-step error lớn nhất theo tiêu chí cố định;
- feature nào được locked XGBoost sử dụng nhiều theo gain importance.

Phase 8 là post-hoc analysis. Kết quả không được dùng để thay feature, parameter,
candidate hoặc model lock hiện tại.

## 3. Entry gate

Phase 8 chỉ chạy khi:

- Phase 7 `PASS — HUMAN APPROVED`;
- audit, predictions và metrics Phase 7 có checksum đúng contract;
- candidate registry vẫn gồm Persistence, Seasonal Naive 24h và XGBoost tuned;
- one-step có 8.592 common timestamps/candidate;
- recursive có 357 common origins và đủ 24 horizons;
- model lock, feature order, packages và prepared-data identity không đổi.

Nếu entry gate sai, dừng trước mọi analysis hoặc refit.

## 4. One-step residual analysis

Signed error được khóa là:

```text
error = prediction - actual
```

Với từng candidate, báo MAE/RMSE và các thống kê signed error. Với
`xgboost_tuned`, báo thêm:

```text
mean error
median error
error standard deviation
absolute-error P90/P95
over-forecast rate
under-forecast rate
top 10 absolute-error timestamps
```

Top 10 được sort theo `absolute_error` giảm dần, sau đó timestamp tăng dần. Không
chọn khoảng thời gian thủ công sau khi xem kết quả.

## 5. Residual temporal dependence

Tính residual ACF của `xgboost_tuned` cho lag 1–168 giờ bằng exact timestamp
pairs. Không được nén khoảng trống giữa các eligible timestamps.

Approximate 95% reference band:

```text
±1.96 / sqrt(number of exact timestamp pairs at each lag)
```

Đây là diagnostic reference, không phải bằng chứng độc lập rằng residual là white
noise.

## 6. Error theo regime

Ba candidates dùng chung timestamps và cùng regime mapping:

```text
hour: 0..23
day_of_week: 0..6
day_type: weekday / weekend
month: 1..12
actual_load_quartile: low / medium_low / medium_high / high
```

Load quartile boundaries được tính một lần từ unique actual values trên common
one-step timestamps. Đây là post-hoc descriptive grouping, không phải feature hoặc
model-selection input.

Mỗi candidate/regime group báo `n_observations`, MAE, RMSE và mean signed error.

## 7. Recursive 24-hour interpretation

Chỉ đọc official recursive metrics/predictions Phase 7. Không chạy lại forecast.

Với từng candidate và horizon 1–24, báo:

- MAE/RMSE;
- mức tăng MAE/RMSE so với horizon 1;
- chênh lệch của XGBoost so với từng baseline;
- horizon có MAE lớn nhất.

One-step và recursive không được trộn chung thành một metric.

## 8. Feature importance

Phase 7 không lưu binary model. Vì vậy Phase 8 dựng lại đúng `xgboost_tuned` từ
model lock và refit trên đúng 108.083 eligible development samples.

```text
importance type = gain
normalization = gain / total gain
zero-importance features retained = true
group summary = lag / rolling / calendar
```

Không dùng holdout để fit hoặc tính importance. Không persist binary model. Gain
importance không phải causal importance và correlated features có thể chia sẻ hoặc
che khuất importance của nhau.

## 9. Fixed outputs

```text
config/error_analysis.json
outputs/results/phase_08_error_analysis.json
outputs/results/phase_08_feature_importance.csv
outputs/figures/phase_08_residual_diagnostics.png
outputs/figures/phase_08_error_by_time.png
outputs/figures/phase_08_error_by_load_regime.png
outputs/figures/phase_08_feature_importance.png
docs/logs/PHASE_08_EXECUTION.md
```

Notebook chỉ đọc các official artifacts này; không chứa refit hoặc analysis logic.

## 10. Execution boundary

AI triển khai source, tests và preflight rồi dừng. Human chạy command Phase 8 trên
Terminal vì execution có một lần locked-model refit để lấy gain importance.

Run directory:

```text
runs/P8_error_interpretation_<timestamp>_<execution_identity>/
├── P8_error_interpretation_<timestamp>_<execution_identity>.log
├── run_metadata.json
├── config_snapshot.json
└── checkpoint.json
```

Không tạo model binary trong run directory.

## 11. Validation contract

Tests phải kiểm tra:

1. upstream checksums và Human-approved Phase 7 status;
2. exact candidate registry và common populations;
3. signed-error convention và summary formulas;
4. exact-lag ACF không nén timestamp gap;
5. deterministic top-10 ordering;
6. regime population conservation cho mọi candidate;
7. shared load-quartile boundaries;
8. recursive horizon 1–24 và metric transformation;
9. exact locked parameters/feature order/development refit population;
10. normalized gain sums to one khi total gain dương;
11. zero-importance features được giữ lại;
12. no tuning, model selection, holdout fit hoặc binary persistence;
13. interrupted/failed execution không promote official outputs;
14. figures và result checksum linkage;
15. notebook không chạy Phase 8 source logic;
16. không import legacy `practice_3` runtime.

## 12. Stop conditions

Dừng và báo Human nếu:

- Phase 7 identity hoặc population không khớp;
- candidate dùng timestamps/origins khác nhau;
- error hoặc importance có NaN/infinity;
- development refit population khác 108.083;
- locked parameter/feature/package thay đổi;
- cần thêm dependency hoặc đổi interpretation method;
- analysis dẫn đến đề xuất thay model hiện tại;
- official artifact không truy vết được upstream evidence.

## 13. Completion gate

Phase 8 chỉ `PASS` khi:

- Human execution hoàn tất;
- official JSON/CSV và bốn figures hợp lệ;
- checksum/provenance linkage PASS;
- focused/full tests PASS;
- notebook presentation clean execution PASS;
- AI technical review PASS;
- Human review kết quả Phase 8.

Sau đó mới được thiết kế Phase 9 — Final Conclusion.
