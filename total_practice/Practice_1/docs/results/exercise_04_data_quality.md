# E4 — Data quality

## Mục tiêu

Kiểm tra missing values, mô phỏng missing trên working copy, so sánh forward-fill
với time interpolation và phát hiện outlier tiềm năng.

## Kết luận chính

Raw dataset được giữ bất biến. Missing-value experiment chỉ chạy trên working
copy; các phương pháp xử lý được so sánh trên cùng vị trí missing. Outlier được
đánh dấu là candidate và phải phân biệt với seasonal peak hợp lệ.

## Mở kết quả

- <a href="../../notebooks/practice_1_present.ipynb" style="color:#1f6feb;">Notebook chính</a>
- <a href="../../outputs/figures/10_missing_values_simulation.png" style="color:#1f6feb;">Missing simulation</a>
- <a href="../../outputs/figures/11_missing_treatment_comparison.png" style="color:#1f6feb;">Missing treatment comparison</a>
- <a href="../../outputs/figures/12_outlier_analysis.png" style="color:#1f6feb;">Outlier analysis</a>
- <a href="../../outputs/results/missing_value_comparison.csv" style="color:#1f6feb;">Missing-value comparison</a>
- <a href="../../outputs/results/outlier_candidates.csv" style="color:#1f6feb;">Outlier candidates</a>
- <a href="../logs/exercise_04_execution.md" style="color:#1f6feb;">Execution log</a>
- <a href="../../src/practice_1/analysis/data_quality.py" style="color:#1f6feb;">Source code</a>

## Điểm cần chú ý

Không ghi missing giả lập trở lại raw dataset. Candidate outlier không được tự
động xóa nếu chưa có bằng chứng domain.

