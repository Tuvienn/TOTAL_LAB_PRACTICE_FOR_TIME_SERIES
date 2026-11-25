# Practice 4 – Multivariate Time Series Forecasting

**Electricity Load + Weather**

Project thực hiện bài thực hành dự báo chuỗi thời gian đa biến (*Multivariate Time Series Forecasting*). Dữ liệu phụ tải điện được kết hợp với dữ liệu thời tiết theo giờ để dự báo `load` ở thời điểm kế tiếp, sử dụng lịch sử 24 giờ gần nhất. Ba nhóm mô hình được triển khai và so sánh là VAR, XGBoost và LSTM.

> README này mô tả quy trình và cấu trúc dựa trên notebook Practice 4, workspace đã chia sẻ và nội dung `src/build_dataset.py` do người thực hiện cung cấp. Tên file notebook có thể thay đổi theo phiên bản; hãy mở notebook Practice 4 mới nhất trong `notebooks/`.

---

## 1. Mục tiêu bài toán

Tại mỗi thời điểm `t`, vector quan sát gồm bốn biến:

| Biến | Mô tả | Vai trò |
|---|---|---|
| `load` | Phụ tải/điện năng tiêu thụ thực tế | Biến mục tiêu cần dự báo |
| `temperature` | Nhiệt độ môi trường | Biến đầu vào |
| `humidity` | Độ ẩm | Biến đầu vào |
| `wind_speed` | Tốc độ gió | Biến đầu vào |

Bài toán là dự báo một bước phía trước (*one-step-ahead forecasting*): sử dụng 24 giờ dữ liệu lịch sử của cả bốn biến để dự báo `load` tại giờ tiếp theo.

- Tần suất dữ liệu sau xử lý: 1 giờ/quan sát.
- Processed dataset trong notebook được ghi nhận có 35.064 dòng.
- Khoảng thời gian được ghi nhận: `2014-12-31 23:00:00 UTC` đến `2018-12-31 22:00:00 UTC`.
- Biến mục tiêu: `load`.

Các thống kê trên mô tả phiên bản processed dataset đã được kiểm tra; cần cập nhật nếu raw data hoặc quy trình build được thay đổi.

## 2. Cấu trúc project

Cấu trúc tổng quan của workspace:

```text
Practice_4/
├── README.md
│
├── datasets/
│   ├── raw/
│   │   ├── energy_dataset.csv
│   │   ├── weather_features.csv
│   │   └── README.md
│   └── processed/
│       └── electricity_load_weather_hourly.csv
│
├── docs/
│   ├── README.md
│   ├── logs/
│   │   └── practice4.log
│   ├── phase_details/
│   ├── plans/
│   ├── results/
│   ├── rules/
│   └── status/
│
├── notebooks/
│   ├── <Practice 4 notebook>.ipynb
│   └── README.md
│
├── outputs/
│   └── figures/
│
├── results/
│   ├── README.md
│   ├── model_evaluation.csv
│   ├── model_evaluation.xlsx
│   └── model_summaries/
│       ├── VAR_summary.txt
│       ├── XGBoost_summary.txt
│       ├── XGBoost_feature_importance.csv
│       ├── XGBoost_tuning_results.csv
│       ├── LSTM_summary.txt
│       └── LSTM_training_history.csv
│
├── runs/
│   └── <one folder per experiment run>/
│
└── src/
    └── build_dataset.py
```

Một số file trong `results/` và `outputs/` được tạo sau khi chạy các cell export tương ứng; chúng có thể chưa tồn tại trong một bản project mới. `runs/` được dùng để lưu kết quả riêng của từng lần chạy thực nghiệm.

## 3. Dữ liệu

### 3.1. Nguồn và file dữ liệu

Project kết hợp hai nguồn dữ liệu:

- **Dữ liệu điện năng:** file `energy_dataset.csv` (nguồn dữ liệu UCI theo thông tin project cung cấp).
- **Dữ liệu thời tiết:** file `weather_features.csv` từ một nguồn thời tiết riêng.

Hai file raw cần được đặt tại:

```text
datasets/raw/energy_dataset.csv
datasets/raw/weather_features.csv
```

Trong script hiện tại, dữ liệu thời tiết được lọc cho thành phố **Madrid**. Nguồn/link tải chính xác, phiên bản dataset và giấy phép sử dụng chưa được ghi trong thông tin hiện có; nên bổ sung khi hoàn thiện hồ sơ project.

### 3.2. Các cột được sử dụng

**Energy – `energy_dataset.csv`**

| Cột gốc | Xử lý | Cột sau xử lý |
|---|---|---|
| `time` | Chuyển sang datetime UTC, sắp xếp tăng dần | `time` |
| `total load actual` | Đổi tên thành `load`; nội suy tuyến tính trong script | `load` |

**Weather – `weather_features.csv`**

| Cột gốc | Xử lý | Cột sau xử lý |
|---|---|---|
| `dt_iso` | Chuyển sang datetime UTC | `time` |
| `city_name` | Xóa khoảng trắng đầu/cuối và lọc `Madrid` | Dùng để lọc, không đưa vào processed dataset |
| `temp` | Tính trung bình theo timestamp; trừ 273.15 để đổi Kelvin sang Celsius | `temperature` |
| `humidity` | Tính trung bình theo timestamp | `humidity` |
| `wind_speed` | Tính trung bình theo timestamp | `wind_speed` |

### 3.3. Quy trình tạo processed dataset

Script `src/build_dataset.py` cung cấp hàm `build_electricity_weather_dataset()` và hàm `main()` để thực hiện các bước:

1. Đọc `energy_dataset.csv`, chỉ lấy `time` và `total load actual`; đổi tên cột phụ tải thành `load`, chuyển `time` sang UTC và sắp xếp theo thời gian.
2. Nội suy tuyến tính cột `load` bằng `interpolate(method="linear", limit_direction="both")`.
3. Đọc các cột thời tiết `dt_iso`, `city_name`, `temp`, `humidity`, `wind_speed`; lọc thành phố `Madrid` (hoặc tất cả thành phố nếu gọi hàm với `city="all").
4. Chuyển `dt_iso` sang `time` theo UTC; gộp các bản ghi thời tiết trùng timestamp bằng trung bình cộng.
5. Đổi `temp` từ Kelvin sang Celsius khi `convert_kelvin_to_celsius=True` (giá trị mặc định trong script).
6. Ghép energy và weather bằng `inner join` theo timestamp UTC.
7. Đặt `time` làm index, sắp xếp thời gian, cố định tần suất `1h` bằng `asfreq("1h")` và nội suy tuyến tính hai chiều cho các giá trị thiếu.
8. Tạo thư mục processed nếu chưa có và lưu thành `datasets/processed/electricity_load_weather_hourly.csv`.

Processed dataset có các cột `time`, `load`, `temperature`, `humidity`, `wind_speed` (trong CSV, `time` được lưu làm index bởi `to_csv()` sau khi `set_index`). Notebook đọc file này để thực hiện EDA và modeling.

### 3.4. Chạy script tạo dataset

Từ thư mục gốc `Practice_4/`, chạy:

```bash
python src/build_dataset.py
```

Script hiện thiết lập `city="Madrid"` và `convert_kelvin_to_celsius=True` trực tiếp trong hàm `main()`; chưa định nghĩa command-line arguments. Có thể thay đổi hai giá trị này trong `main()` nếu cần tạo dataset cho cấu hình khác.

### 3.5. Lưu ý về nội suy và tính hợp lệ theo thời gian

Trong phiên bản `build_dataset.py` được cung cấp, nội suy được thực hiện trên chuỗi trước khi chia Train/Validation/Test và dùng `limit_direction="both"`. Với các khoảng thiếu, nội suy tuyến tính hai chiều có thể sử dụng giá trị nằm sau thời điểm đang được điền; do đó có khả năng đưa thông tin tương lai vào dữ liệu lịch sử. Điều này đặc biệt đáng lưu ý với `load`, vì đây là biến mục tiêu.

Vì vậy, nếu yêu cầu đánh giá nghiêm ngặt theo thời gian, cần rà soát lại chiến lược xử lý missing values: xác định khoảng thiếu trước, chia theo thời gian, và lựa chọn cách impute chỉ sử dụng thông tin khả dụng tại thời điểm dự báo (hoặc fit quy tắc imputation trên Train rồi áp dụng phù hợp cho các tập sau). Không nên mặc định rằng nội suy hai chiều trước khi split là hoàn toàn không gây leakage.

Ngoài ra, `inner join` chỉ giữ các timestamp có mặt ở cả hai nguồn trước khi áp dụng `asfreq("1h")`; các mốc không khớp bị loại trong bước ghép, còn các khoảng trống theo giờ phát sinh sau đó mới được tạo lại và nội suy. Cần kiểm tra số lượng timestamp bị mất sau join khi cập nhật dataset.

## 4. Quy trình thực nghiệm

### 4.1. Data Understanding

Notebook thực hiện các hoạt động khám phá dữ liệu:

- Kiểm tra khoảng thời gian, số dòng, tần suất timestamp và thống kê mô tả.
- Kiểm tra missing values, dòng trùng và timestamp trùng.
- Kiểm tra dấu hiệu bất thường cảm biến, ví dụ `temperature` và `humidity` đồng thời bằng 0.
- Phát hiện outliers bằng quy tắc IQR và trực quan hóa bằng boxplot.
- Phân tích phân phối theo giờ, thứ trong tuần và tháng bằng temporal boxplots.
- Trực quan hóa `load` theo thời gian, `load` so với `temperature` và correlation matrix.

Các phân tích EDA dùng để định hướng mô hình nên được thực hiện trên Train. Những kiểm tra toàn vẹn dữ liệu theo quy tắc xác định trước (ví dụ kiểm tra schema hoặc timestamp trùng) có thể áp dụng cho file nguồn, nhưng không dùng thống kê từ Validation/Test để chọn đặc trưng hoặc điều chỉnh mô hình.

Việc phát hiện outlier hoặc điểm nghi ngờ lỗi cảm biến không đồng nghĩa các quan sát sẽ tự động bị xóa/thay thế; cách xử lý cần được quyết định và ghi nhận riêng.

### 4.2. Chia Train/Validation/Test theo thời gian

Dữ liệu được sắp xếp tăng dần theo timestamp và chia tuần tự, không shuffle:

| Tập | Tỷ lệ | Số quan sát ở dataset 35.064 dòng |
|---|---:|---:|
| Train | 70% | 24.544 |
| Validation | 15% | 5.260 |
| Test | 15% | 5.260 |
| **Tổng** | **100%** | **35.064** |

Train dùng để fit mô hình và tham số preprocessing. Validation dùng để lựa chọn cấu hình/early stopping. Test được giữ lại cho đánh giá cuối cùng.

### 4.3. Preprocessing

- Sử dụng `StandardScaler` cho bốn biến số.
- Chỉ gọi `fit` trên Train.
- Dùng scaler đã fit để `transform` Validation và Test.
- Khi tính metric cho `load`, đưa dự báo và giá trị thực về đơn vị ban đầu bằng inverse scaling.

### 4.4. Feature Engineering

Cửa sổ lịch sử được đặt là 24 giờ.

- **XGBoost:** 96 lag features (4 biến × 24 giờ) và 3 rolling features, tổng cộng 99 đặc trưng: rolling mean 6 giờ, rolling standard deviation 24 giờ và load trend 24 giờ.
- **LSTM:** dữ liệu đầu vào dạng tensor 3 chiều `(samples, 24, 4)`.
- Các lag/rolling features tại thời điểm dự báo chỉ được sử dụng những quan sát đã có trước thời điểm đó.

### 4.5. Các mô hình

#### VAR – Statistical Baseline

- Kiểm định tính dừng từng biến bằng Augmented Dickey-Fuller (ADF) trên Train.
- Sai phân các biến không dừng nếu cần và kiểm tra lại tính dừng.
- Chọn bậc trễ dựa trên AIC hoặc BIC trong phạm vi tìm kiếm được cấu hình trong notebook.
- VAR mô hình hóa vector gồm `load`, `temperature`, `humidity`, `wind_speed`; khi đánh giá chỉ lấy dự báo `load`.

#### XGBoost – Machine Learning

- Sử dụng 99 lag/rolling features.
- Điều chỉnh `max_depth` và `n_estimators` bằng Validation.
- Sử dụng Early Stopping dựa trên Validation.
- Chọn cấu hình theo metric Validation đã quy định trong notebook (hiện dùng RMSE trong phần tuning).

#### LSTM – Deep Learning

- Kiến trúc: `LSTM(64) → LSTM(32) → Dense(1)`.
- Loss: Mean Squared Error (MSE).
- Optimizer: Adam.
- Theo dõi Validation Loss và sử dụng cơ chế dừng sớm nếu được cấu hình trong notebook.

### 4.6. Backtesting và đánh giá

Notebook sử dụng *rolling one-step-ahead backtesting*: dùng lịch sử để dự báo giờ kế tiếp; sau khi quan sát được giá trị thực tế tại thời điểm đó, cập nhật lịch sử bằng quan sát thực tế rồi dự báo bước kế tiếp.

Ba mô hình được so sánh bằng:

- **RMSE** – Root Mean Squared Error.
- **MAE** – Mean Absolute Error.
- **MAPE** – Mean Absolute Percentage Error.

Các metric được tính trên thang đo `load` ban đầu sau inverse scaling. Validation phục vụ lựa chọn cấu hình; Test phục vụ đánh giá cuối cùng.

> Chiến lược one-step-ahead có cập nhật quan sát thực tế sau mỗi bước khác với dự báo nhiều giờ liên tiếp từ một mốc cố định mà không nhận thêm dữ liệu mới.

## 5. Môi trường và thư viện

Project sử dụng Python và Jupyter Notebook. Các thư viện chính:

- `numpy`, `pandas`
- `matplotlib`, `seaborn`
- `scikit-learn`
- `statsmodels`
- `xgboost`
- `torch` (PyTorch)
- `openpyxl` (nếu xuất bảng đánh giá sang Excel)

Cài đặt trong đúng môi trường Python/Conda mà Jupyter kernel sử dụng:

```bash
python -m pip install numpy pandas matplotlib seaborn scikit-learn statsmodels xgboost torch jupyter openpyxl
```

Kiểm tra môi trường:

```bash
python --version
python -m pip show numpy pandas scikit-learn statsmodels xgboost torch openpyxl
```

Trong Jupyter có thể cài gói còn thiếu bằng `%pip install <package>`. Nếu kernel chưa nhận package sau khi cài, restart kernel và chạy lại notebook.

## 6. Cách chạy project

### Bước 1 – Chuẩn bị raw data

Đặt hai file sau vào `datasets/raw/`:

```text
datasets/raw/energy_dataset.csv
datasets/raw/weather_features.csv
```

### Bước 2 – Tạo processed dataset

Từ thư mục gốc project:

```bash
python src/build_dataset.py
```

Kiểm tra file được tạo tại:

```text
datasets/processed/electricity_load_weather_hourly.csv
```

### Bước 3 – Mở Jupyter Notebook

Trên Windows, mở Anaconda Prompt và chuyển đến thư mục `notebooks/`:

```bat
cd /d <duong_dan_den_Practice_4>\notebooks
jupyter notebook
```

Mở notebook Practice 4 mới nhất trong thư mục. Tên file có thể thay đổi theo phiên bản.

### Bước 4 – Chạy notebook

- Chọn kernel Python đã cài đầy đủ thư viện.
- Chạy các cell theo thứ tự từ đầu đến cuối để đảm bảo các biến và mô hình được khởi tạo đúng.
- Không chạy riêng cell đánh giá, backtesting hoặc Model Summary khi các model/result đầu vào chưa tồn tại.
- Kiểm tra log và các file đầu ra sau khi notebook hoàn tất.

## 7. Đầu ra và nơi lưu kết quả

### 7.1. Model Evaluation

Bảng tổng hợp các chỉ số RMSE, MAE, MAPE cho VAR, XGBoost và LSTM trên Validation/Test được lưu dưới dạng:

```text
results/
├── model_evaluation.csv
├── model_evaluation.xlsx
├── validation_ranking.csv
└── test_ranking.csv
```

Các file này được tạo khi chạy cell export Model Evaluation trong notebook. File Excel gồm các sheet tổng hợp và xếp hạng theo tập dữ liệu nếu cell export được cấu hình theo hướng dẫn trong notebook.

### 7.2. Model Summaries

Sau khi chạy các cell Model Summary, các báo cáo được ghi vào `results/model_summaries/`:

| File | Nội dung |
|---|---|
| `VAR_summary.txt` | ADF, differencing, lag order, AIC/BIC/HQIC và thống kê mô hình VAR. |
| `XGBoost_summary.txt` | Cấu hình tốt nhất, best iteration, thông tin huấn luyện, Validation metrics và feature importance. |
| `XGBoost_feature_importance.csv` | Mức độ quan trọng của các feature XGBoost. |
| `XGBoost_tuning_results.csv` | Kết quả các cấu hình XGBoost đã thử nghiệm. |
| `LSTM_summary.txt` | Kiến trúc, số lượng tham số, optimizer, learning rate, epoch và loss. |
| `LSTM_training_history.csv` | Train Loss và Validation Loss theo epoch. |

### 7.3. Logs, figures và experiment runs

- **Logs:** `docs/logs/practice4.log` – ghi lại thông tin và trạng thái thực thi notebook/script.
- **Figures:** `outputs/figures/` – vị trí lưu biểu đồ được export. Biểu đồ chỉ xuất hiện trong output notebook nếu chưa gọi `savefig()`.
- **Runs:** `runs/` – lưu kết quả theo từng lần chạy thực nghiệm. Nên giữ các kết quả của mỗi lần chạy riêng biệt để có thể đối chiếu cấu hình, metric và báo cáo tương ứng. Quy ước đặt tên thư mục run cụ thể có thể được bổ sung sau.

## 8. Nguyên tắc tránh data leakage

- Chia dữ liệu theo thứ tự thời gian, không shuffle.
- EDA định hướng mô hình và lựa chọn đặc trưng chỉ sử dụng Train.
- Fit `StandardScaler` trên Train; chỉ transform Validation/Test.
- Không dùng Validation/Test để tính ngưỡng outlier, lựa chọn feature hoặc điều chỉnh preprocessing.
- Chọn hyperparameters và theo dõi early stopping bằng Validation.
- Không dùng Test để lựa chọn mô hình hoặc điều chỉnh cấu hình.
- Chỉ báo cáo kết quả Test sau khi quy trình/mô hình đã được chốt.
- Lag và rolling features tại thời điểm dự báo chỉ được sử dụng dữ liệu lịch sử khả dụng.
- Rà soát bước nội suy trong `build_dataset.py` trước khi khẳng định quy trình hoàn toàn không có look-ahead leakage; xem mục 3.5.

## 9. Khả năng tái lập thực nghiệm

Khi lưu mỗi lần chạy vào `runs/`, nên ghi nhận:

- Ngày/giờ chạy và mã định danh run.
- Phiên bản raw/processed dataset hoặc checksum của file dữ liệu.
- Phiên bản Python và các thư viện.
- Cấu hình mô hình, hyperparameters và random seed.
- Metrics trên Validation/Test.
- Model Summary, tuning results và training history tương ứng.

Notebook có thể đặt random seed cho các thành phần có hỗ trợ (ví dụ `random_state` của XGBoost và seed của PyTorch). Kết quả vẫn có thể khác nhau theo phiên bản thư viện, phần cứng và backend.

## 10. Thông tin project cần bổ sung (nếu muốn công bố/chia sẻ)

Các nội dung dưới đây chưa được cung cấp hoặc chưa thể xác nhận từ file hiện có:

1. **Link nguồn dữ liệu:** URL chính thức/đường dẫn tải cụ thể và phiên bản của `energy_dataset.csv` (UCI) và `weather_features.csv` (nguồn thời tiết riêng).
2. **Thông tin học thuật:** tên môn học, trường/lớp, giảng viên, nhóm thực hiện và tác giả (nếu muốn ghi trong README).
3. **Repository:** URL GitHub/GitLab nếu project được quản lý bằng Git.
4. **Quy ước `runs/`:** tên thư mục theo timestamp, run ID hay experiment name; những artifact chính xác được lưu trong mỗi run.
5. **Chính sách lưu hình:** xác nhận có tự động export toàn bộ figure sang `outputs/figures/` hay chỉ lưu một số hình được chọn.

---

**Project:** Practice 4 – Multivariate Time Series Forecasting (Electricity Load + Weather)  
**Ngôn ngữ:** Python  
**Môi trường thực thi:** Jupyter Notebook / Visual Studio Code
