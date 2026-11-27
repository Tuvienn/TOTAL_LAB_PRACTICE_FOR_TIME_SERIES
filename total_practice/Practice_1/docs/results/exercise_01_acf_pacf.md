# E1 — ACF/PACF

## Mục tiêu

Đo autocorrelation và partial autocorrelation của chuỗi AirPassengers để nhận
diện temporal dependence, trend và seasonality ban đầu.

## Kết luận chính

ACF/PACF cho thấy chuỗi có cấu trúc thời gian rõ ràng, không phải white noise.
Các bảng ACF/PACF được dùng cho chẩn đoán khám phá, không tự động quyết định
một forecasting model.

## Mở kết quả

- <a href="../../notebooks/practice_1_present.ipynb" style="color:#1f6feb;">Notebook chính</a>
- <a href="../../outputs/figures/01_time_series_overview.png" style="color:#1f6feb;">Chuỗi gốc</a>
- <a href="../../outputs/figures/02_acf_40_lags.png" style="color:#1f6feb;">ACF 40 lag</a>
- <a href="../../outputs/figures/03_pacf_40_lags.png" style="color:#1f6feb;">PACF 40 lag</a>
- <a href="../../outputs/results/acf_values.csv" style="color:#1f6feb;">ACF values</a>
- <a href="../../outputs/results/pacf_values.csv" style="color:#1f6feb;">PACF values</a>
- <a href="../../outputs/results/exercise_01_findings.json" style="color:#1f6feb;">Findings JSON</a>
- <a href="../logs/exercise_01_execution.md" style="color:#1f6feb;">Execution log</a>
- <a href="../../src/practice_1/analysis/acf_pacf.py" style="color:#1f6feb;">Source code</a>

## Điểm cần chú ý

Confidence interval 95% được hiển thị cùng ACF/PACF. Đây là bằng chứng mô tả
và chẩn đoán, không phải bước fitting mô hình dự báo.

