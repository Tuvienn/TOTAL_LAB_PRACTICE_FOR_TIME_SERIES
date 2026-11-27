# E2 — White noise

## Mục tiêu

Tạo chuỗi white noise, kiểm tra ACF của nó và so sánh với ACF của AirPassengers.

## Kết luận chính

White noise có autocorrelation gần 0 ở các lag và đóng vai trò baseline khái
niệm. AirPassengers có temporal structure rõ ràng hơn, nên không thể xem là
white noise.

## Mở kết quả

- <a href="../../notebooks/practice_1_present.ipynb" style="color:#1f6feb;">Notebook chính</a>
- <a href="../../outputs/figures/04_white_noise_series.png" style="color:#1f6feb;">White-noise series</a>
- <a href="../../outputs/figures/05_white_noise_acf.png" style="color:#1f6feb;">White-noise ACF</a>
- <a href="../../outputs/figures/06_white_noise_vs_airpassengers_acf.png" style="color:#1f6feb;">So sánh ACF</a>
- <a href="../../outputs/results/white_noise_acf_values.csv" style="color:#1f6feb;">White-noise ACF values</a>
- <a href="../logs/exercise_02_execution.md" style="color:#1f6feb;">Execution log</a>
- <a href="../../src/practice_1/analysis/white_noise.py" style="color:#1f6feb;">Source code</a>

## Điểm cần chú ý

So sánh này chỉ nhằm giải thích khái niệm autocorrelation; không phải benchmark
forecasting giữa hai chuỗi.

