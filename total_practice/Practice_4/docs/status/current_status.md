# Current Status — Practice 4

Trạng thái dự án: `NOTEBOOK_EXECUTED_AND_REPORTED`.

## Dataset và provenance

Bộ dữ liệu được chọn là **Hourly energy demand, generation and weather**.
Notebook sử dụng canonical processed file:

```text
datasets/processed/electricity_load_weather_hourly.csv
```

Thông tin audit read-only của processed dataset:

| Thuộc tính | Giá trị |
|---|---:|
| Số dòng | 35.064 |
| Số cột | 5 |
| Khoảng thời gian | 2014-12-31 23:00 UTC → 2018-12-31 22:00 UTC |
| Tần suất | Hourly, không có khoảng lệch |
| Missing values | 36 missing `load` targets; weather inputs complete |
| Duplicate timestamps | 0 |
| Cột | `time`, `load`, `temperature`, `humidity`, `wind_speed` |
| SHA-256 processed file | `9dd198be2b630b75bb679d8c7b3cb6fe1c655638114b81cf655fc5576ade3e6f` |

Raw source checksums được ghi nhận để truy xuất:

```text
datasets/raw/energy_dataset.csv
14cd13e020d87af0ab49db8e0f1e4d308320ec5b8d2dec23bab4d27c75c7733a

datasets/raw/weather_features.csv
3566c3c21179d4fc6691eec6d37a6cfe8fe6a4d9e097f95e4fda4a29dc683b18
```

Canonical processed dataset giữ nguyên 36 missing `load` targets. Notebook chỉ
forward-fill `load` theo quá khứ cho input; các mốc có target gốc bị thiếu được
đánh dấu và loại khỏi validation/test metrics. Duplicate timestamp và interval
bất thường không được tự động sửa.

## Đã triển khai và kiểm chứng

- `notebooks/practice4.ipynb` đã được gắn nhãn Phase 1–10.
- Project root và các đường dẫn dataset/log/results không còn phụ thuộc vào thư mục khởi chạy.
- Các cell cài package `%pip install` đã được loại khỏi notebook.
- Data-quality audit đã được thêm vào Phase 1.
- Protocol recursive rolling one-step-ahead cho VAR, XGBoost và LSTM đã được triển khai trong Phase 9; prediction được append vào history và không retrain sau mỗi bước.
- Notebook đã chạy lại trên môi trường macOS hiện tại bằng kernel Practice 4.
- 49/49 code cells thực thi, không có execution error.
- Log hiện tại: `docs/logs/practice4.log`.
- Kết quả hiện tại: `results/model_evaluation.csv`, `results/model_evaluation.xlsx` và các model summaries.

## Kết quả chạy hiện tại

- VAR Test RMSE: `4614.2743`
- XGBoost Test RMSE: `3664.4820`
- LSTM Test RMSE: `4855.8257`
- XGBoost đang đứng đầu theo Test RMSE trong lần chạy hiện tại; LSTM đứng đầu Validation RMSE.

Baseline Naive/Seasonal Naive không nằm trong scope bắt buộc của lần triển khai này.

## Final report

Sáu câu hỏi phân tích của đề đã được trả lời trong notebook và được tổng hợp tại
<a href="../results/phase_10_final_report.md" style="color:#1f6feb;">Phase 10 — Results và Final Report</a>.

Baseline Naive/Seasonal Naive chỉ bổ sung khi phạm vi yêu cầu.
