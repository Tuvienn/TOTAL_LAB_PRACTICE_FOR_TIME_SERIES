# EXERCISE 04 — KẾ HOẠCH ĐỒNG BỘ NOTEBOOK

## 1. Trạng thái

```text
Practice: Practice_1
Exercise: 04 — Time Series Data Quality
Phạm vi cell: 32–44
Trạng thái kế hoạch: ĐÃ_TRIỂN_KHAI_VÀ_XÁC_MINH
Được phép triển khai: CÓ
Ngày xác nhận: 2026-10-12
```

## 2. Mục tiêu

- mask đúng sáu timestamp đã khóa trên working copy;
- lưu ground truth trước masking;
- so sánh forward-fill và time interpolation công bằng;
- tính MAE chỉ trên sáu masked positions;
- chạy IQR 1.5 trên validated log-STL residual E3;
- chỉ flag và inspect outlier candidates;
- tạo ba figure, hai CSV và diễn giải đủ 12 câu hỏi;
- giữ nguyên E1–E3, E5 và raw dataset.

## 3. File được phép thay đổi

```text
notebooks/practice_1_present.ipynb, chỉ cell 32–44
src/practice_1/analysis/data_quality.py
src/practice_1/analysis/__init__.py
src/practice_1/visualization/diagnostic_plots.py
src/practice_1/visualization/__init__.py
tests/test_data_quality.py
outputs/figures/10_missing_values_simulation.png
outputs/figures/11_missing_treatment_comparison.png
outputs/figures/12_outlier_analysis.png
outputs/results/missing_value_comparison.csv
outputs/results/outlier_candidates.csv
docs/logs/exercise_04_execution.md
docs/status/current_status.md
E4 specification/plan/error/fix status fields
```

## 4. Bản đồ cell

| Cell | Nội dung |
|---:|---|
| 32 | Heading, imports, locked parameters, validated input |
| 33 | Existing missing count, ground truth, masking, figure 10 |
| 34 | Forward-fill và time interpolation |
| 35 | Comparison table, MAE và CSV |
| 36–37 | Giải thích phương pháp và forecasting-safety caveat |
| 38 | Figure 11 |
| 39 | Validate E3 components và chạy residual-IQR |
| 40–41 | Giải thích IQR và flag-only protocol |
| 42 | Lưu/hiển thị outlier candidates |
| 43 | Figure 12, không clipping |
| 44 | Diễn giải động đủ 12 câu hỏi |

## 5. Reusable API và tests

Tạo owner cho:

```text
simulate_missing_values
apply_missing_value_treatments
build_missing_value_comparison
summarize_reconstruction_mae
detect_residual_iqr_outliers
```

Tests phải kiểm tra đúng timestamp, ground truth, sáu NaN, treatment isolation,
`method=time`, MAE baseline, 14 candidate timestamp, no clipping và invalid input.

## 6. Validation

```text
compileall đạt
toàn bộ tests E1–E4 đạt
cell 0–44 chạy sạch bằng kernel time-series-practice-1
ba figure được inspect
hai CSV khớp notebook
raw checksum không đổi
E1–E3 source/output không đổi
E5 source/type checksum không đổi
không thêm dependency
```

## 7. Điều kiện dừng

Dừng nếu timestamp không tồn tại, ground truth chưa lưu, treatments dùng vị trí khác
nhau, residual E3 sai schema/alignment, IQR không dùng multiplier 1.5, cần clipping,
cần dependency mới hoặc gây regression upstream/downstream.

## 8. Xác nhận kỹ thuật

the project scope requires “lên plan và bắt đầu triển khai plan” ngày 2026-10-12. Yêu cầu này
được ghi nhận là authorization rõ ràng để triển khai đúng phạm vi tài liệu này.

## 9. Kết quả triển khai

```text
Triển khai hoàn tất: CÓ
Validation hoàn tất: CÓ
Ngày hoàn tất: 2026-10-12
Execution log: docs/logs/exercise_04_execution.md
```

