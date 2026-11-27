# E3 — STL decomposition

## Mục tiêu

Phân rã chuỗi AirPassengers thành trend, seasonal và residual; sử dụng log
transform để làm seasonal amplitude ổn định hơn trước khi phân rã cộng tính.

## Kết luận chính

Chuỗi có trend tăng và seasonality lặp lại. STL tách được các thành phần chính;
residual được kiểm tra thêm bằng ACF và chẩn đoán residual để đánh giá phần cấu
trúc còn sót lại.

## Mở kết quả

- <a href="../../notebooks/practice_1_present.ipynb" style="color:#1f6feb;">Notebook chính</a>
- <a href="../../outputs/figures/07_log_transformed_series.png" style="color:#1f6feb;">Log-transformed series</a>
- <a href="../../outputs/figures/08_stl_decomposition.png" style="color:#1f6feb;">STL decomposition</a>
- <a href="../../outputs/figures/09_decomposition_residual.png" style="color:#1f6feb;">Residual diagnostics</a>
- <a href="../../outputs/results/decomposition_components.csv" style="color:#1f6feb;">Decomposition components</a>
- <a href="../../outputs/results/residual_diagnostics.csv" style="color:#1f6feb;">Residual diagnostics</a>
- <a href="../logs/exercise_03_execution.md" style="color:#1f6feb;">Execution log</a>
- <a href="../../src/practice_1/analysis/decomposition.py" style="color:#1f6feb;">Source code</a>

## Điểm cần chú ý

Residual gần white noise là tín hiệu chẩn đoán, không phải bằng chứng rằng mọi
forecasting model đều phù hợp.

