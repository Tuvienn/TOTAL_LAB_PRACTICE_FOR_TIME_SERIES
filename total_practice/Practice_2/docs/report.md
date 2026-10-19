# BÁO CÁO THỰC HÀNH PHÂN TÍCH CHUỖI THỜI GIAN
**Chủ đề:** Kiểm định tính dừng (ADF) & Xây dựng mô hình dự báo ARIMA / SARIMA

---

## 1. MỤC TIÊU & TỔNG QUAN DỮ LIỆU

### 1.1. Mục tiêu bài thực hành
1. Nhận diện đặc trưng chuỗi thời gian (xu hướng, mùa vụ, tính dừng) thông qua khám phá dữ liệu trực quan (EDA).
2. Thực hiện và diễn giải kết quả kiểm định nghiệm đơn vị **ADF (Augmented Dickey-Fuller)**.
3. Ứng dụng phép lấy sai phân (Differencing) kết hợp biểu đồ **ACF / PACF** để xác định bộ tham số tối ưu cho mô hình.
4. Thiết lập quy trình huấn luyện, chẩn đoán phần dư (Residual Diagnostics) và đánh giá dự báo giữa **ARIMA** và **SARIMA**.

### 1.2. Bộ dữ liệu sử dụng
| Tên Dataset | Mô tả dữ liệu | Tần suất | Chu kỳ mùa vụ ($s$) | Mục tiêu áp dụng |
| :--- | :--- | :---: | :---: | :--- |
| **Dataset 1 (`a10.csv`)** | Doanh số bán lẻ theo tháng tại Mỹ (1991 – 2008) | Monthly (`MS`) | $s = 12$ | Thực hành cơ bản (Bài 1 $\rightarrow$ Bài 5) |
| **Dataset 2 (`airline-passengers.csv`)** | Số lượng hành khách hàng không (1949 – 1960, 144 quan sát) | Monthly (`MS`) | $s = 12$ | Bài tập nâng cao (So sánh ARIMA & SARIMA) |

---

## PHẦN I: THỰC HÀNH MÔ HÌNH ARIMA (DATASET 1 - `a10.csv`)

### Bài 1: Khám phá dữ liệu (Exploratory Data Analysis - EDA)

#### Bước 1.1: Thiết lập đường dẫn và nạp dữ liệu chuỗi thời gian
Dữ liệu được nạp từ file `a10.csv`, chuyển đổi cột `date` sang định dạng `datetime`, sắp xếp theo trình tự thời gian và cố định tần suất theo đầu tháng (`MS` - Month Start).

```python
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path.cwd().resolve().parent
RAW_PATH = PROJECT_ROOT / "datasets" / "raw" / "a10.csv"
print(RAW_PATH)

df = pd.read_csv(RAW_PATH)
df["date"] = pd.to_datetime(df["date"], errors="raise")
df = df.set_index("date").sort_index()
df = df.asfreq("MS")

print(df.head())
```

**Kết quả xuất ra (Output):**
```text
D:\TimeSeries_Data\total_practice\Practice_2\datasets\raw\a10.csv
               value
date                
1991-07-01  3.526591
1991-08-01  3.180891
1991-09-01  3.252221
1991-10-01  3.611003
1991-11-01  3.565869
```

#### Bước 1.2: Trực quan hóa chuỗi thời gian gốc
```python
plt.figure(figsize=(12, 5))
plt.plot(df.index, df['value'])
plt.title("Monthly Retail Sales (Dataset 1)")
plt.xlabel("Date")
plt.ylabel("Value")
plt.grid(True)
plt.show()
```

> **Phân tích & Trả lời câu hỏi Bài 1:**
> * **Chuỗi có xu hướng (Trend) không?** **Có.** Đồ thị thể hiện xu hướng tăng trưởng dài hạn rất rõ rệt từ năm 1991 đến năm 2008.
> * **Có dấu hiệu mùa vụ (Seasonality) không?** **Có.** Xuất hiện các đỉnh cao điểm và đáy thấp điểm lặp lại đều đặn theo chu kỳ hàng năm ($s = 12$ tháng), đồng thời biên độ dao động mùa vụ ngày càng mở rộng theo thời gian.
> * **Chuỗi có khả năng dừng (Stationary) không?** **Không dừng.** Do kỳ vọng (trung bình trượt tăng dần theo xu hướng) và phương sai (độ rộng biên độ dao động phình to dần) đều biến đổi theo thời gian.

---

### Bài 2: Kiểm định tính dừng ADF trên chuỗi gốc

#### Bước 2.1: Thực thi kiểm định Augmented Dickey-Fuller (ADF)
```python
from statsmodels.tsa.stattools import adfuller

result = adfuller(df['value'])
print(f"ADF Statistic: {result[0]:.4f}")
print(f"p-value: {result[1]:.4f}")
```

**Kết quả kiểm định:**
| Chỉ số thống kê | Giá trị thực nghiệm | Ngưỡng ý nghĩa ($\alpha$) |
| :--- | :---: | :---: |
| **ADF Statistic** | `3.1452` | — |
| **p-value** | `1.0000` | `0.05` (5%) |

> **Phân tích & Trả lời câu hỏi Bài 2:**
> * **Giả thuyết $H_0$ của kiểm định ADF là gì?** Giả thuyết $H_0$ phát biểu rằng chuỗi thời gian có nghiệm đơn vị (Unit Root), đồng nghĩa với việc **chuỗi KHÔNG dừng**. Giả thuyết đối $H_1$ là chuỗi dừng.
> * **Ý nghĩa của `p-value`:** Đại diện cho mức xác suất quan sát được giá trị thống kê hiện tại nếu $H_0$ đúng. Nếu $\text{p-value} < 0.05$, ta bác bỏ $H_0$ (chuỗi dừng); ngược lại nếu $\text{p-value} \ge 0.05$, ta chưa đủ cơ sở bác bỏ $H_0$.
> * **Kết luận:** Với chuỗi gốc của `a10.csv`, $\text{p-value} = 1.0000 > 0.05$, nên kết luận **chuỗi gốc KHÔNG dừng**.

---

### Bài 3: Phép lấy sai phân & Kiểm định lại tính dừng

#### Bước 3.1: Lấy sai phân bậc 1 ($\Delta Y_t = Y_t - Y_{t-1}$) và kiểm định ADF lần 2
```python
df_diff1 = df['value'].diff().dropna()

plt.figure(figsize=(12, 5))
plt.plot(df_diff1)
plt.title("Chuỗi sau sai phân bậc 1")
plt.show()

res_diff1 = adfuller(df_diff1)
print(f"ADF Statistic (Diff 1): {res_diff1[0]:.4f}")
print(f"p-value (Diff 1): {res_diff1[1]:.6f}")
```

**So sánh kết quả ADF trước và sau sai phân bậc 1:**
| Trạng thái chuỗi | ADF Statistic | p-value | Đánh giá xu hướng (Trend) |
| :--- | :---: | :---: | :--- |
| **Chuỗi gốc (`df['value']`)** | `3.1452` | `1.000000` | Tăng mạnh theo thời gian |
| **Sai phân bậc 1 (`df_diff1`)** | `-2.4952` | `0.116653` | Đã triệt tiêu xu hướng, dao động quanh trục `0` |

> **Phân tích & Trả lời câu hỏi Bài 3:**
> * **Sau sai phân, chuỗi đã dừng chưa?** Về mặt trung bình, chuỗi đã loại bỏ hoàn toàn xu hướng tăng tuyến tính và dao động ổn định quanh mức `0` (thống kê ADF giảm mạnh từ `3.1452` xuống `-2.4952`). Tuy nhiên, do phương sai ở nửa cuối chuỗi vẫn phình to theo mùa vụ nên `p-value` đạt `0.116653`.
> * **Giá trị $d$ trong ARIMA là bao nhiêu?** Chọn bậc sai phân thường là **$d = 1$** để loại bỏ thành phần xu hướng (Trend) trước khi đưa vào phân tích tương quan.

---

### Bài 4: Phân tích biểu đồ ACF & PACF

#### Bước 4.1: Trực quan hóa hàm Tự tương quan (ACF) và Tự tương quan riêng phần (PACF)
```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

fig, axes = plt.subplots(1, 2, figsize=(14, 4))
plot_acf(df_diff1, lags=36, ax=axes[0])
plot_pacf(df_diff1, lags=36, ax=axes[1], method='ywm')
plt.show()
```

> **Phân tích & Trả lời câu hỏi Bài 4:**
> * **ACF cắt cụt ở lag nào?**
>   * Biểu đồ **ACF** bị cắt cụt ngay sau **Lag 1** (trong ngắn hạn từ Lag 2 đến Lag 10 đều nằm gọn trong dải tin cậy) $\rightarrow$ Xác định bậc trung bình trượt **$q = 1$** (đồng thời ghi nhận các spike mùa vụ rất cao tại Lag 12, 24, 36).
> * **PACF cắt cụt ở lag nào?**
>   * Biểu đồ **PACF** cắt cụt sau **Lag 4** $\rightarrow p = 4$ (trong đó spike tương quan mạnh và rõ rệt nhất nằm ở **Lag 1** $\rightarrow$ ưu tiên xét **$p = 1$** hoặc **$p = 2$** để giữ mô hình tinh gọn, tránh quá khớp).
> * **Gợi ý mô hình $\text{ARIMA}(p,d,q)$?**
>   * Kết hợp với sai phân bậc 1 ($d = 1$), đề xuất thử nghiệm các cấu hình: **`ARIMA(4, 1, 1)`**, **`ARIMA(1, 1, 1)`** hoặc **`ARIMA(2, 1, 1)`**. Đồng thời, do chuỗi có các spike mùa vụ rất mạnh tại chu kỳ $s = 12$, đề xuất mở rộng sang mô hình **`SARIMA(1, 1, 1)(0, 1, 1, 12)`**.

---

### Bài 5: Thiết lập mô hình ARIMA – Dự báo – Đánh giá

#### Bước 5.1: Phân chia tập dữ liệu Train (80%) và Test (20%)
```python
# 1. Chia Train (80%) - Test (20%) theo đúng thứ tự thời gian
train_size = int(len(df) * 0.8)
train, test = df['value'].iloc[:train_size], df['value'].iloc[train_size:]
```

> **Câu hỏi 1: Vì sao không được shuffle dữ liệu chuỗi thời gian? Test set dùng để làm gì?**
> * **Không được shuffle (xáo trộn) vì:** Dữ liệu chuỗi thời gian có tính phụ thuộc chặt chẽ vào trình tự thời gian trước - sau (quá khứ quyết định hiện tại, hiện tại quyết định tương lai). Việc shuffle sẽ làm đứt gãy cấu trúc tự tương quan ở các độ trễ (lags) và gây ra hiện tượng **rò rỉ dữ liệu từ tương lai về quá khứ (Data Leakage)** trong quá trình huấn luyện.
> * **Vai trò của Test set:** Tập Test (20% dữ liệu cuối từ năm 2005 đến 2008) đóng vai trò là dữ liệu tương lai chưa từng được nhìn thấy, dùng để kiểm tra và đánh giá khách quan khả năng dự báo thực tế (khả năng tổng quát hóa) của mô hình.

---

#### Bước 5.2: Huấn luyện mô hình & Lựa chọn tham số qua AIC / BIC
```python
from statsmodels.tsa.arima.model import ARIMA

# 2. Huấn luyện mô hình ARIMA(1,1,1) và ARIMA(2,1,1)
model1 = ARIMA(train, order=(1, 1, 1))
fitted_model1 = model1.fit()
print(f"ARIMA(1,1,1) - AIC: {fitted_model1.aic:.2f} | BIC: {fitted_model1.bic:.2f}")

model2 = ARIMA(train, order=(2, 1, 1))
fitted_model2 = model2.fit()
print(f"ARIMA(2,1,1) - AIC: {fitted_model2.aic:.2f} | BIC: {fitted_model2.bic:.2f}")
```

**Bảng đối chiếu tiêu chuẩn thông tin AIC & BIC:**
| Mô hình thử nghiệm | Chỉ số AIC | Chỉ số BIC | Quyết định lựa chọn |
| :--- | :---: | :---: | :--- |
| **`ARIMA(1, 1, 1)`** | **`582.47`** | **`591.73`** | **Được chọn** (AIC và BIC thấp nhất, cân bằng tốt giữa độ chính xác và độ phức tạp) |
| **`ARIMA(2, 1, 1)`** | `584.46` | `596.81` | Loại (Tăng tham số nhưng không cải thiện chất lượng khớp) |

> **Câu hỏi 2: Ý nghĩa của bộ tham số $(p, d, q)$ đã chọn trong `ARIMA(1, 1, 1)`?**
> * **$p = 1$ ($\text{AR}(1)$ - Tự hồi quy bậc 1):** Giá trị hiện tại của chuỗi (sau sai phân) chịu ảnh hưởng trực tiếp bởi giá trị của chính nó ở **1 tháng ngay trước đó** ($\text{lag} = 1$).
> * **$d = 1$ ($\text{I}(1)$ - Sai phân bậc 1):** Chuỗi gốc được lấy sai phân bậc 1 để loại bỏ xu hướng và đưa chuỗi về trạng thái dừng.
> * **$q = 1$ ($\text{MA}(1)$ - Trung bình trượt bậc 1):** Giá trị hiện tại của chuỗi chịu ảnh hưởng bởi **sai số dự báo (cú sốc ngẫu nhiên) của 1 tháng ngay trước đó** ($\text{lag} = 1$).
>
> **Câu hỏi 3: Mô hình có hội tụ không?**
> * **Có hội tụ.** Quá trình ước lượng hợp lý cực đại (MLE) khi chạy lệnh `.fit()` cho cả hai mô hình `ARIMA(1,1,1)` và `ARIMA(2,1,1)` đã hoàn tất nhanh chóng mà không xuất hiện cảnh báo lỗi không hội tụ (`ConvergenceWarning`), đồng thời tính toán thành công các hệ số và chỉ số AIC, BIC.

---

#### Bước 5.3: Chẩn đoán phần dư (Residual Diagnostics)
```python
# 3. Chẩn đoán phần dư (Residual Diagnostics)
residuals = fitted_model1.resid
fig, ax = plt.subplots(1, 2, figsize=(14, 4))
ax[0].plot(residuals)
ax[0].axhline(0, color='red', linestyle='--')
ax[0].set_title("Residuals theo thời gian")
plot_acf(residuals, lags=24, ax=ax[1])
plt.show()
```

> **Câu hỏi 4: Residuals có phải là nhiễu trắng (White Noise) không?**
> * **Không, Residuals chưa phải là White Noise.** Dù phần dư dao động quanh mức trung bình bằng `0`, nhưng trên biểu đồ ACF của residuals vẫn xuất hiện các đỉnh (spikes) vượt rất cao ra khỏi khoảng tin cậy tại các độ trễ mùa vụ **Lag 12** và **Lag 24**, cho thấy phần dư vẫn còn tự tương quan mạnh theo chu kỳ năm.
>
> **Câu hỏi 5: Nếu residuals còn tự tương quan $\rightarrow$ cần điều chỉnh gì?**
> * Cần điều chỉnh tham số $p$ hoặc $q$, hoặc nâng cấp lên **mô hình SARIMA** (bổ sung sai phân mùa vụ $D=1$ và các bậc $P, Q$ với chu kỳ $s=12$) để mô hình hóa triệt để thành phần mùa vụ còn sót lại.

---

#### Bước 5.4: Dự báo trên tập Test & Tính toán các chỉ số đánh giá
```python
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 4. Dự báo trên tập Test
forecast = fitted_model1.forecast(steps=len(test))

plt.figure(figsize=(12, 5))
plt.plot(train.index, train, label='Train')
plt.plot(test.index, test, label='Test (Thực tế)')
plt.plot(test.index, forecast, label='Forecast (Dự báo)', color='red')
plt.legend()
plt.show()

# 5. Tính các chỉ số đánh giá MAE, RMSE, MAPE
mae = mean_absolute_error(test, forecast)
rmse = np.sqrt(mean_squared_error(test, forecast))
mape = np.mean(np.abs((test - forecast) / test)) * 100
print(f"MAE: {mae:.3f} | RMSE: {rmse:.3f} | MAPE: {mape:.2f}%")
```

**Kết quả đánh giá sai số của `ARIMA(1, 1, 1)` trên tập Test:**
| Chỉ số đánh giá | Giá trị | Ý nghĩa thực tế |
| :--- | :---: | :--- |
| **MAE** (Mean Absolute Error) | `3.667` | Sai số tuyệt đối trung bình giữa dự báo và thực tế |
| **RMSE** (Root Mean Squared Error) | `4.624` | Độ lệch chuẩn sai số dự báo (phạt nặng các sai số lớn ở đỉnh mùa vụ) |
| **MAPE** (Mean Absolute Percentage Error) | `18.04%` | Tỷ lệ phần trăm sai số trung bình trên tập Test |

> **Phân tích kết quả dự báo (Câu hỏi 6, 7, 8 & 9):**
> * **Câu hỏi 6 – Dự đoán có bám sát xu hướng không?** **Không bám sát.** Quan sát trên đồ thị dự báo, đường Forecast (màu đỏ) chỉ giảm nhẹ ở bước đầu tiên rồi nhanh chóng đi ngang thành một đường thẳng cố định quanh mức giá trị $\approx 17.6$. Mô hình hoàn toàn không bắt được đà tăng trưởng tiếp tục đi lên (Trend) cũng như các nhịp dao động lên xuống theo mùa vụ (Seasonality) của tập Test thực tế (màu cam) trong giai đoạn 2005–2008.
> * **Câu hỏi 7 – Sai lệch lớn nhất xảy ra ở đâu?** Sai lệch lớn nhất xảy ra tại các đỉnh cao điểm mua sắm của tập Test (khoảng cuối năm 2007 – đầu năm 2008), khi giá trị thực tế vọt lên gần **30** nhưng mô hình chỉ dự báo đi ngang quanh mức **17.6 – 18**.
> * **Câu hỏi 8 – Chỉ số nào nhạy với outlier nhất?** **RMSE** nhạy với outlier nhất vì sai số được **bình phương** trước khi lấy trung bình, làm cho các sai số lớn tại các đỉnh mùa vụ có trọng số ảnh hưởng rất mạnh đến kết quả tổng.
> * **Câu hỏi 9 – RMSE lớn hay nhỏ nói lên điều gì?** RMSE càng nhỏ thì dự báo càng gần giá trị thực tế và mô hình càng chính xác; ngược lại RMSE lớn cho thấy sai số dự báo lớn và mô hình mô tả dữ liệu chưa tốt. Với `RMSE = 4.624` (cao hơn hẳn `MAE = 3.667`), mô hình ARIMA thuần túy vẫn còn sai lệch đáng kể so với thực tế có tính mùa vụ.

---

## PHẦN II: BÀI TẬP NÂNG CAO VỚI MÔ HÌNH SARIMA (DATASET 2 - `AirPassengers`)

### Bước 1: Khám phá dữ liệu & Nhận diện tính mùa vụ (`airline-passengers.csv`)
```python
PROJECT_ROOT = Path.cwd().resolve().parent
RAW_PATH2 = PROJECT_ROOT / "datasets" / "raw" / "airline-passengers.csv"
print(RAW_PATH2)

df2 = pd.read_csv(RAW_PATH2, parse_dates=['Month'], index_col='Month')
print(df2.head())

plt.figure(figsize=(12, 4))
plt.plot(df2.index, df2['Passengers'], color='tab:blue')
plt.title("Monthly Airline Passengers (1949 - 1960)")
plt.xlabel("Thời gian")
plt.ylabel("Số lượng hành khách")
plt.grid(True)
plt.show()
```

**Output dữ liệu mẫu:**
```text
D:\TimeSeries_Data\total_practice\Practice_2\datasets\raw\airline-passengers.csv
            Passengers
Month                 
1949-01-01         112
1949-02-01         118
1949-03-01         132
1949-04-01         129
1949-05-01         121
```
> **Nhận xét:** Chuỗi số lượng hành khách hàng không (1949 – 1960) có xu hướng tăng trưởng dài hạn rất rõ và mang tính mùa vụ lặp lại đều đặn theo chu kỳ $s = 12$ tháng.

---

### Bước 2 & 3: Kiểm định ADF chuỗi gốc & Thực hiện sai phân kép ($d=1, D=1, s=12$)

```python
# 2. Kiểm định ADF trên chuỗi gốc
adf_orig = adfuller(df2['Passengers'])
print(f"ADF Statistic: {adf_orig[0]:.4f} | p-value: {adf_orig[1]:.4f}")
print("-> Kết luận: p-value > 0.05 => Chấp nhận H0, chuỗi gốc KHÔNG DỪNG.\n")

# 3. Sai phân thường (d=1) kết hợp sai phân mùa vụ (D=1, s=12)
df2_diff = df2['Passengers'].diff(1).diff(12).dropna()
print("p-value sau sai phân kép:", adfuller(df2_diff)[1])
```

**Bảng đối chiếu kết quả kiểm định ADF trên Dataset 2:**
| Giai đoạn kiểm định | Tham số sai phân | ADF Statistic | Giá trị p-value | Kết luận tính dừng |
| :--- | :---: | :---: | :---: | :--- |
| **Chuỗi gốc (`Passengers`)** | $d=0, D=0$ | `0.8154` | `0.9919` | **Không dừng** ($\text{p-value} > 0.05$) |
| **Sau sai phân kép (`df2_diff`)** | $d=1, D=1, s=12$ | `-15.5956` | `1.8565e-28` | **Đã dừng hoàn toàn** ($\text{p-value} \ll 0.05$) |

---

### Bước 4: Phân tích biểu đồ ACF / PACF & Xác định tham số $(p, q, P, Q)$
```python
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
plot_acf(df2_diff, lags=36, ax=axes[0], title="4. Autocorrelation (ACF)")
plot_pacf(df2_diff, lags=36, ax=axes[1], method='ywm', title="4. Partial Autocorrelation (PACF)")
plt.tight_layout()
plt.show()
```

> **Phân tích lựa chọn tham số từ biểu đồ:**
> * **Thành phần ngắn hạn $(p, q)$:** Cả hai biểu đồ ACF và PACF đều xuất hiện 1 spike âm vượt ra ngoài vùng tin cậy rõ rệt tại **Lag 1** ($\approx -0.31$) trước khi cắt cụt vào trong dải tin cậy từ Lag 2 $\rightarrow$ Chọn **$p = 1, q = 1$**.
> * **Thành phần mùa vụ $(P, Q)$ với chu kỳ $s = 12$:** Sau khi lấy sai phân mùa vụ $D = 1$, tương quan tại Lag 12 đã giảm mạnh (chỉ còn cột âm nhỏ sát biên dưới). Thiết lập cấu hình **`SARIMA(1, 1, 1)(1, 1, 1, 12)`** để mô hình hấp thụ toàn bộ hiệu ứng trễ mùa vụ.

---

### Bước 5, 6 & 7: Huấn luyện SARIMA, Dự báo và So sánh trực tiếp với ARIMA
```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Chia Train (80%) / Test (20%)
n_train = int(len(df2) * 0.8)
train2, test2 = df2['Passengers'].iloc[:n_train], df2['Passengers'].iloc[n_train:]

# 1. Fit và dự báo với SARIMA(1,1,1)(1,1,1,12) trên Dataset 2
sarima_model = SARIMAX(train2, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
sarima_fit = sarima_model.fit(disp=False)
sarima_pred = sarima_fit.forecast(steps=len(test2))

mae_sarima = mean_absolute_error(test2, sarima_pred)
rmse_sarima = np.sqrt(mean_squared_error(test2, sarima_pred))
mape_sarima = np.mean(np.abs((test2 - sarima_pred) / test2)) * 100

# 2. Fit và dự báo với ARIMA(1,1,1) trên cùng Dataset 2 để so sánh
arima_model2 = ARIMA(train2, order=(1, 1, 1))
arima_fit2 = arima_model2.fit()
arima_pred2 = arima_fit2.forecast(steps=len(test2))

mae_arima2 = mean_absolute_error(test2, arima_pred2)
rmse_arima2 = np.sqrt(mean_squared_error(test2, arima_pred2))
mape_arima2 = np.mean(np.abs((test2 - arima_pred2) / test2)) * 100

print("=== KẾT QUẢ SO SÁNH TRÊN TẬP AIRPASSENGERS (DATASET 2) ===")
print(f"ARIMA(1,1,1)          -> MAE: {mae_arima2:6.2f} | RMSE: {rmse_arima2:6.2f} | MAPE: {mape_arima2:5.2f}%")
print(f"SARIMA(1,1,1)(1,1,1)12 -> MAE: {mae_sarima:6.2f} | RMSE: {rmse_sarima:6.2f} | MAPE: {mape_sarima:5.2f}%")

# Vẽ biểu đồ so sánh trực quan ARIMA vs SARIMA
plt.figure(figsize=(12, 5))
plt.plot(train2.index, train2, label='Train')
plt.plot(test2.index, test2, label='Test (Thực tế)', color='orange')
plt.plot(test2.index, arima_pred2, label='ARIMA Forecast', color='red', linestyle='--')
plt.plot(test2.index, sarima_pred, label='SARIMA Forecast', color='green', linewidth=2)
plt.title("So sánh dự báo: ARIMA vs SARIMA (AirPassengers)")
plt.legend()
plt.grid(True)
plt.show()
```

> **Đánh giá & So sánh tổng kết giữa ARIMA và SARIMA:**
> 1. **Hiệu quả của ARIMA (`đường nét đứt màu đỏ`):** Hoàn toàn thất bại trong việc dự báo chuỗi có chu kỳ mùa vụ. Đường dự báo đi ngang cố định quanh mức $\approx 498$ ngay từ đỉnh cuối của tập Train (giữa năm 1958), gây ra sai số rất lớn ở cả các vùng đáy thấp điểm ($\approx 310$) lẫn các đỉnh mùa hè ($\approx 622$).
> 2. **Sự vượt trội của SARIMA (`đường liền nét màu xanh lá`):** Nhờ kết hợp sai phân mùa vụ ($D = 1, s = 12$) và các tham số $(P, Q)$, đường dự báo của SARIMA uốn lượn bám sát cả **xu hướng tăng trưởng** lẫn **nhịp điệu mùa vụ 12 tháng** của tập dữ liệu Test thực tế, giúp giảm sai số MAE và RMSE xuống gấp nhiều lần so với ARIMA.
> 3. **Hạn chế nhỏ còn tồn đọng:** Tại đỉnh cao nhất vào mùa hè năm 1960, giá trị dự báo của SARIMA ($\approx 548$) hơi thấp hơn so với thực tế ($\approx 622$). Nguyên nhân là do dữ liệu `AirPassengers` có biên độ mùa vụ tăng theo cấp số nhân (phương sai tăng dần), trong khi mô hình SARIMA tiêu chuẩn hoạt động trên thang đo cộng tuyến tính (có thể khắc phục triệt để bằng phép biến đổi Logarit `np.log` trên chuỗi gốc trước khi huấn luyện).