# E5 — Visualization

## Mục tiêu

Trực quan hóa toàn bộ chuỗi, rolling mean/std, seasonality theo tháng và
month-year heatmap để làm rõ trend, biến động và mùa vụ.

## Kết luận chính

Các biểu đồ cho phép quan sát trend dài hạn, seasonal repetition và sự thay đổi
của mức độ biến động theo thời gian. Rolling statistics dùng cửa sổ quá khứ,
không đưa future observations vào phép tính.

## Mở kết quả

- <a href="../../notebooks/practice_1_present.ipynb" style="color:#1f6feb;">Notebook chính</a>
- <a href="../../outputs/figures/13_full_time_series.png" style="color:#1f6feb;">Full time series</a>
- <a href="../../outputs/figures/14_rolling_mean_std.png" style="color:#1f6feb;">Rolling mean/std</a>
- <a href="../../outputs/figures/15_monthly_seasonal_plot.png" style="color:#1f6feb;">Monthly seasonal plot</a>
- <a href="../../outputs/figures/16_month_year_heatmap.png" style="color:#1f6feb;">Month-year heatmap</a>
- <a href="../../outputs/results/rolling_statistics.csv" style="color:#1f6feb;">Rolling statistics</a>
- <a href="../logs/exercise_05_execution.md" style="color:#1f6feb;">Execution log</a>
- <a href="../../src/practice_1/analysis/rolling_statistics.py" style="color:#1f6feb;">Source code</a>
- <a href="../../src/practice_1/visualization/diagnostic_plots.py" style="color:#1f6feb;">Visualization source</a>

## Điểm cần chú ý

Visualization hỗ trợ chẩn đoán forecastability và data quality; Practice 1 không
huấn luyện forecasting model.

