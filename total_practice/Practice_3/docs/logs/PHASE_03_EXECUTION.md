# PHASE 03 — EXECUTION LOG

## 1. Scope

Triển khai TRAIN-only EDA trên development period đã khóa ở Phase 2. Phase này không tạo modeling feature, không xây dựng X/y, không train model và không truy cập holdout target values.

## 2. Environment

```text
Python: 3.14.3
NumPy: 2.5.4
pandas: 3.1.0
matplotlib: 3.11.2
pytest: 9.1.1
Package mode: editable local install
```

## 3. Official execution

```bash
MPLCONFIGDIR=/private/tmp/practice3v2-mpl \
.venv/bin/python -m practice_3.analysis.eda
```

Official result:

```text
outputs/results/phase_03_eda_summary.json
```

Official figures:

```text
outputs/figures/phase_03_trend.png
outputs/figures/phase_03_distribution.png
outputs/figures/phase_03_seasonality_profiles.png
outputs/figures/phase_03_hour_day_heatmap.png
outputs/figures/phase_03_lag_correlation.png
outputs/figures/phase_03_anomaly_screening.png
```

## 4. TRAIN-only boundary

```text
Development rows: 112,535
Observed targets: 112,509
Missing targets: 26
Start inclusive: 2004-10-01 01:00:00
End exclusive: 2017-08-03 00:00:00
Historical holdout rows excluded: 8,761
Holdout target values inspected: false
```

Holdout-mutation isolation test PASS: thay toàn bộ holdout target bằng extreme values không làm development EDA input thay đổi.

## 5. Distribution result

```text
Mean: 15,541.3873 MW
Median: 15,356 MW
Standard deviation: 2,598.2280 MW
Minimum: 9,581 MW
Q25 / Q75: 13,662 / 17,251 MW
Q95 / Q99: 20,156 / 22,069 MW
Maximum: 25,695 MW
IQR: 3,589 MW
```

Mean cao hơn median và upper tail thể hiện rõ trên histogram/boxplot. Đây là descriptive evidence, không phải quyết định transform hoặc clip target.

## 6. Trend and seasonality result

```text
Daily rows: 4,689
Trailing rolling window: 30 days
Rolling available days: 4,660
Centered window: false
```

TRAIN-only profiles thể hiện:

- mức tiêu thụ thay đổi rõ theo hour-of-day;
- cuối tuần thấp hơn ngày làm việc;
- month profile có khác biệt theo mùa;
- heatmap `day-of-week × hour-of-day` xác nhận interaction giữa chu kỳ ngày và tuần.

Các findings chỉ tạo feature hypotheses cho Phase 4, chưa chốt feature list.

## 7. Temporal dependence result

```text
Lag 1 correlation: 0.976061
Lag 24 correlation: 0.873618
Lag 168 correlation: 0.765647
Lag range evaluated: 1–168 hours
Timeline compressed before shift: false
```

Pairwise correlation giữ hourly alignment và chỉ bỏ cặp có target thiếu.

## 8. Robust anomaly screening

```text
Method: modified MAD score
Grouping: calendar year × hour-of-week
Threshold: 3.5
Minimum group support: 20
Evaluable targets: 110,303
Not-evaluable targets: 2,206
Candidates: 1,053
Candidate rate among evaluable targets: 0.9546%
Target treatment: none
```

Candidate chỉ dùng để mô tả. Không observation nào bị xóa, clip, winsorize hoặc thay thế.

## 9. Artifact checksums

```text
Phase 3 JSON:
5d542d5c8cc9f2436ef817646d0413765a62dee6805ee41556991c1c0e125dd7

Trend PNG:
ec411a2eb065d3bf267428205ea92297c570ff85c6484a53c09411ea116eddfa

Distribution PNG:
b67ae23fa29c42673d5d9107cb5fd0d7fd9a9fff58cb4e34d5ee4ba2d477a061

Seasonality profiles PNG:
985e5576184e4f631c9376c7dabd1f9599e079ffb9f48ec6c417f3d1a9d18df5

Hour-day heatmap PNG:
9e813750e0e186d32ea7ce750190add81b68ed71cb67108b0168ef570b852b9c

Lag correlation PNG:
e15ceb0dbb2803ad39e4c0a36d1f04c3711fee8cf981a7bfd52166cceb3972cf

Anomaly screening PNG:
8b97a9171179fa83ce96af4ead94c0f7bf556f6ba4387a1ff64cd211d1979930
```

Official rerun giữ nguyên JSON và toàn bộ figure checksums.

## 10. Validation evidence

```text
Focused Phase 3 tests: 15/15 PASS
Full Practice 3 regression suite: 48/48 PASS
Holdout-mutation isolation: PASS
Hourly lag-alignment test: PASS
Missing-target preservation: PASS
Anomaly target immutability: PASS
Independent artifact bundle validation: PASS
Deterministic JSON and figures: PASS
Visual figure review: PASS
Legacy runtime import: NONE
```

Các API deprecation warning từ pandas/matplotlib được xử lý trước official execution. Official focused test run không còn warning.

## 11. Notebook presentation

```text
notebooks/Practice_3_present.ipynb
Scope: Phase 0–3
Mode: read-only official artifact presentation
Clean-kernel execution: PASS
Executed code cells: 11/11
Error outputs: 0
Pipeline/EDA/training/prediction calls: NONE
```

Notebook hiển thị summary tables, highlighted lag table và sáu official Phase 3 figures; notebook không tính lại EDA.

## 12. Completion state

```text
Phase 3 technical status: PASS
Human result review: APPROVED
Phase 4 implementation: NOT AUTHORIZED
```

Human đã review và chốt Phase 3. Phase 4 được phép bắt đầu ở bước thảo luận và thiết kế; implementation vẫn cần phase-detail được duyệt.
