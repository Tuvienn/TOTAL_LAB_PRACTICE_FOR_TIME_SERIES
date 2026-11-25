# E04 — ACF/PACF và ARIMA candidates

## Kết luận hiện tại

ACF và PACF đã được tính trên đúng log-first-difference training series gồm 162
observations, với tối đa 36 lag, confidence level 95% và PACF method `ywm`.

Các candidates hiện chỉ là provisional handoff cho E05:

```text
ARIMA(1,1,1)
ARIMA(1,1,0)
ARIMA(0,1,1)
```

SARIMA được dành cho E06 trên Dataset 2/AirPassengers, không phải candidate
formal của E05 core.

## Trạng thái

`Đã phê duyệt và kiểm tra`. E04 bàn giao candidates, không tự chọn final model.

Không chọn model cuối cùng chỉ từ một spike ACF/PACF hoặc chỉ từ AIC/BIC.

## Evidence

- [Execution evidence E04](../logs/exercise_04_execution.md)
- [ACF/PACF figure](../../outputs/figures/03_acf_pacf_log_first_differenced.png)
- [Notebook core](../../notebooks/Practice_2_Exercise.ipynb)
