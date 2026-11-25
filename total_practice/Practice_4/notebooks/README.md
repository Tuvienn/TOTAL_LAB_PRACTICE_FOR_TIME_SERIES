# Notebooks – Practice 4

Thư mục này chứa Jupyter Notebook dùng để thực hiện **Practice 4 – Multivariate Time Series Forecasting: Electricity Load + Weather**.

## 1. Notebook chính

| Tệp | Mô tả |
|---|---|
| `practice4.ipynb` | Notebook chính: khám phá dữ liệu, preprocessing, feature engineering, huấn luyện VAR/XGBoost/LSTM, backtesting và tạo model summary. |

## 2. Mục tiêu thực nghiệm

Sử dụng dữ liệu điện năng và thời tiết theo giờ để dự báo **load tại thời điểm kế tiếp** từ lịch sử 24 giờ gần nhất.

Các biến đầu vào:

- `load`: điện năng tiêu thụ.
- `temperature`: nhiệt độ.
- `humidity`: độ ẩm.
- `wind_speed`: tốc độ gió.

## 3. Nội dung notebook

Notebook được tổ chức theo các bước chính:

1. **Data Loading:** đọc dữ liệu, chuyển `time` sang kiểu datetime và sắp xếp theo thời gian.
2. **Time-based Split:** chia dữ liệu theo thứ tự thời gian, không shuffle: Train 70%, Validation 15%, Test 15%.
3. **Data Understanding / EDA:** kiểm tra chất lượng dữ liệu; phân tích missing values, duplicate, dấu hiệu bất thường cảm biến, outliers, seasonality và trực quan hóa. Các phân tích dùng để định hướng mô hình được thực hiện trên Train.
4. **Preprocessing:** fit `StandardScaler` trên Train; dùng scaler đã fit để transform Validation và Test.
5. **Feature Engineering:** tạo cửa sổ lịch sử 24 giờ. LSTM sử dụng tensor 3D `(samples, 24, 4)`; XGBoost sử dụng 96 lag features và 3 rolling features.
6. **VAR:** kiểm định tính dừng bằng ADF, sai phân các biến không dừng (nếu cần), chọn lag theo BIC và huấn luyện VAR đa biến.
7. **XGBoost:** huấn luyện mô hình hồi quy, điều chỉnh `max_depth` và `n_estimators` trên Validation, sử dụng early stopping.
8. **LSTM:** kiến trúc `LSTM(64) → LSTM(32) → Dense(1)`, loss MSE, optimizer Adam và early stopping dựa trên Validation Loss.
9. **Walk-forward Backtesting:** dự báo lần lượt từng bước thời gian theo chiến lược rolling one-step-ahead; khi một thời điểm đã được quan sát, cập nhật lịch sử trước khi dự báo bước tiếp theo.
10. **Evaluation & Model Summaries:** tính RMSE, MAE, MAPE trên thang đo `load` ban đầu; hiển thị so sánh Validation/Test và tạo báo cáo riêng cho từng mô hình.

## 4. Dữ liệu đầu vào

Notebook đọc file đã xử lý tại đường dẫn tương đối:

```text
../datasets/processed/electricity_load_weather_hourly.csv
```

Vì vậy, cần bảo đảm tệp dữ liệu tồn tại đúng vị trí này trước khi chạy notebook.

## 5. Môi trường và thư viện

Notebook được xây dựng bằng Python và Jupyter Notebook. Các thư viện chính:

- `numpy`, `pandas`
- `matplotlib`, `seaborn`
- `scikit-learn`
- `statsmodels`
- `xgboost`
- `torch` (PyTorch)

Cài đặt các thư viện bằng Jupyter hoặc Anaconda Prompt:

```bash
python -m pip install numpy pandas matplotlib seaborn scikit-learn statsmodels xgboost torch jupyter
```

Nếu sử dụng cell trong Jupyter Notebook, có thể thay `python -m pip` bằng `%pip`.

## 6. Cách mở và chạy notebook

**Quan trọng:** Notebook sử dụng các đường dẫn tương đối như `../datasets` và `../docs/logs`. Nên khởi chạy Jupyter với thư mục làm việc hiện tại là `notebooks` để các đường dẫn được phân giải chính xác.

Trên Windows, mở Anaconda Prompt và chạy:

```bat
cd /d <duong_dan_project>\notebooks
jupyter notebook
```

Sau khi Jupyter mở trong trình duyệt:

1. Mở `practice4.ipynb`.
2. Chọn đúng Python kernel đã cài các thư viện cần thiết.
3. Chạy notebook tuần tự từ trên xuống dưới (**Run All** hoặc chạy từng cell theo thứ tự).

Không nên chạy riêng các cell huấn luyện hoặc tạo summary khi các biến đầu vào và mô hình chưa được khởi tạo.

## 7. Kết quả đầu ra

Khi chạy các cell tương ứng, notebook tạo các báo cáo trong thư mục cấp project:

```text
../results/model_summaries/
```

Các tệp được tạo gồm:

| Tệp | Nội dung |
|---|---|
| `VAR_summary.txt` | Kết quả ADF, lag order, AIC/BIC/HQIC và thống kê VAR. |
| `XGBoost_summary.txt` | Cấu hình tốt nhất, best iteration, validation metrics và top feature importance. |
| `XGBoost_feature_importance.csv` | Mức độ quan trọng của các đặc trưng XGBoost. |
| `XGBoost_tuning_results.csv` | Kết quả thử nghiệm các cấu hình XGBoost. |
| `LSTM_summary.txt` | Kiến trúc, số lượng tham số và cấu hình huấn luyện LSTM. |
| `LSTM_training_history.csv` | Train Loss và Validation Loss theo epoch. |

Log thực thi được ghi tại:

```text
../docs/logs/practice4.log
```

Các biểu đồ được hiển thị trực tiếp trong notebook. Nếu cần quản lý ảnh độc lập, lưu/export các hình cần thiết vào `../outputs/figures/`.

## 8. Lưu ý về đánh giá và tránh data leakage

- Giữ nguyên thứ tự thời gian; không shuffle dữ liệu khi chia tập.
- Chỉ `fit` `StandardScaler` trên Train. Validation và Test chỉ được `transform` bằng scaler đã fit.
- Các thống kê EDA dùng để lựa chọn đặc trưng hoặc quyết định xử lý mô hình cần dựa trên Train; không dùng kết quả Test để điều chỉnh mô hình.
- Dùng Validation để chọn hyperparameters và theo dõi early stopping.
- Chỉ sử dụng Test cho đánh giá cuối cùng sau khi đã chốt mô hình.
- Các chỉ số RMSE, MAE, MAPE được tính sau khi đưa dự báo `load` về đơn vị ban đầu.
- Walk-forward trong notebook là **rolling one-step-ahead**: tại mỗi bước, mô hình dự báo giờ kế tiếp rồi cập nhật bằng quan sát thực tế khi thời điểm đó đã xảy ra. Đây không phải dự báo đệ quy nhiều giờ mà không có quan sát mới.

## 9. Ghi chú

- Có thể chạy lại notebook; các file summary/log có cùng tên sẽ được ghi đè theo nội dung của lần chạy mới.
- Nếu thay đổi dữ liệu, cách chia tập, cấu hình mô hình hoặc seed, cần chạy lại các cell phụ thuộc và cập nhật kết quả báo cáo.
- Không chỉnh sửa trực tiếp dữ liệu gốc trong quá trình EDA; sử dụng các DataFrame bản sao cho preprocessing và modeling.
