# Báo cáo thực hành phân tích chuỗi thời gian

**Chủ đề:** EDA, kiểm định ADF, sai phân và dự báo bằng ARIMA/SARIMA
**Nguồn kết quả:** các output hiện được lưu trong [Practice_2_present.ipynb](../notebooks/Practice_2_present.ipynb). Các nhận xét dưới đây phân biệt kết quả đã quan sát với kết luận còn chờ rà soát; không thay thế việc chạy lại notebook trong kernel sạch.

## Tổng quan dữ liệu

| Dataset | Quan sát | Khoảng thời gian | Tần suất | Phân tích |
|---|---:|---|---|---|
| `a10.csv` | 204 | 1991-07 đến 2008-06 | Hàng tháng (`MS`) | Bài 1–5, ARIMA |
| `airline-passengers.csv` | 144 | 1949-01 đến 1960-12 | Hàng tháng | Bài nâng cao, ARIMA và SARIMA |

---

## Phần I — Dataset 1: `a10.csv`

### Bài 1 — Khám phá dữ liệu

Chuỗi tháng có xu hướng tăng dài hạn và biến động theo mùa vụ năm (chu kỳ 12 tháng). Biên độ dao động tăng cùng với mức chuỗi; do đó phương sai trên thang gốc không ổn định. Điều này ủng hộ việc dùng logarit khi phân tích và mô hình hóa.

Dữ liệu có 204 quan sát, không có giá trị thiếu, timestamp trùng lặp hoặc khoảng tháng bị thiếu. Phép chia theo thời gian giữ nguyên thứ tự:

| Tập | Số quan sát | Khoảng thời gian |
|---|---:|---|
| Train | 163 | 1991-07 đến 2005-01 |
| Test | 41 | 2005-02 đến 2008-06 |

**Trả lời:** Chuỗi có xu hướng tăng và mùa vụ hàng năm rõ rệt. Trên thang gốc, chuỗi không có vẻ dừng vì mức trung bình và độ biến động thay đổi theo thời gian.

### Bài 2 — ADF trên chuỗi gốc

ADF được tính trên phần train, không dùng tập test:

| Chuỗi | ADF statistic | p-value | Lag dùng | Số quan sát trong hồi quy ADF | Quyết định ở mức 0.05 |
|---|---:|---:|---:|---:|---|
| Chuỗi gốc | 2.230893 | 0.998907 | 14 | 148 | Không bác bỏ H₀ |

- **H₀:** chuỗi có nghiệm đơn vị, tức chưa có bằng chứng chuỗi dừng.
- **p-value:** mức độ tương thích của kết quả kiểm định với H₀; p-value nhỏ hơn 0.05 dẫn đến bác bỏ H₀ theo ngưỡng đã chọn. Không bác bỏ H₀ không đồng nghĩa với việc chứng minh H₀ đúng.
- **Kết luận:** p-value 0.998907 lớn hơn 0.05, nên chưa có bằng chứng chuỗi gốc dừng.

### Bài 3 — Sai phân và kiểm định lại

Kết quả so sánh hai cách xử lý trên train:

| Biến đổi | ADF statistic | p-value | Kết luận ở mức 0.05 |
|---|---:|---:|---|
| Sai phân bậc 1 trên thang gốc | -1.706074 | 0.427986 | Không bác bỏ H₀ |
| Log rồi sai phân bậc 1 | -3.659486 | 0.004720 | Bác bỏ H₀ |

Sai phân bậc 1 trên giá trị gốc chưa đủ bằng chứng để kết luận dừng. Trên chuỗi log, sai phân bậc 1 dao động quanh mức ổn định hơn và ADF bác bỏ H₀. Vì vậy, chuỗi được chọn cho các bước sau là **log(train) với d = 1**. `d = 1` chỉ số lần sai phân thường; log là phép biến đổi thang đo, không phải một bậc sai phân.

**Trả lời:** Sai phân thô đơn thuần chưa đạt kết quả dừng theo ADF; log-sai phân bậc 1 đạt kết quả này trong mẫu train. Bậc sai phân thường được chọn là **d = 1**.

### Bài 4 — ACF/PACF và đề xuất bậc

Không có kết luận “ACF cắt sau lag 1” hoặc “PACF cắt chính xác sau lag 4” đủ tin cậy để ghi là kết quả cuối cùng cho chuỗi mô hình hóa. Các giá trị lag mùa vụ đang được lưu trong notebook thuộc phần phân tích sai phân thô: ACF tại lag 12/24/36 lần lượt là 0.8444/0.7044/0.6052; PACF tương ứng là 0.5121/-0.0571/-0.0273. Đây là dấu hiệu phụ thuộc mùa vụ, nhưng không phải bằng chứng cho một điểm cắt ngắn hạn rõ ràng trên chuỗi log-sai phân đã chọn ở Bài 3.

Bảng candidate hiện có ghi `ARIMA(1,1,1)`, `ARIMA(2,1,1)` và `ARIMA(4,1,1)` ở trạng thái provisional. Trong E05, hai mô hình được fit thực tế là **ARIMA(1,1,1)** và **ARIMA(2,1,1)**; `ARIMA(4,1,1)` không nằm trong bảng kết quả fit. Do đó, kết quả E04 nên được hiểu là gợi ý thăm dò, không phải quyết định cuối cùng về cutoff hoặc order.

**Trả lời:**

- **ACF cắt cụt ở lag nào?** Output lưu hiện tại cho thấy tương quan giảm dần qua các lag mùa vụ, không xác nhận một cutoff ngắn hạn rõ ràng trên chuỗi log-sai phân.
- **PACF cắt cụt ở lag nào?** Các lag có ý nghĩa không tạo thành một cutoff duy nhất có thể khẳng định từ bằng chứng hiện có.
- **Gợi ý ARIMA(p,d,q)?** Hai candidate được đưa sang bước fit là `(1,1,1)` và `(2,1,1)`, với `d=1`. Cần đọc/ghi nhận ACF-PACF trên đúng chuỗi log-sai phân train trước khi coi các bậc `p,q` là kết luận chính thức.

> **Trạng thái bằng chứng:** current status vẫn ghi nhận discrepancy ở E04 handoff. Vì vậy báo cáo không biến các candidate provisional thành lựa chọn đã được phê duyệt; xem [current_status.md](./status/current_status.md).

### Bài 5 — Fit, chẩn đoán residual, forecast và đánh giá

Hai candidate được fit trên log của tập train; forecast được đưa về thang đo gốc để so sánh với test. Cả hai mô hình hội tụ, không ghi nhận warning trong output:

| Mô hình | Hội tụ | AIC | BIC |
|---|---|---:|---:|
| ARIMA(1,1,1) | Có | -131.048881 | -121.786092 |
| ARIMA(2,1,1) | Có | -129.532608 | -117.182223 |

Theo AIC/BIC, ARIMA(1,1,1) được ưu tiên hơn trong hai candidate. `p` là bậc AR, `d` là bậc sai phân thường và `q` là bậc MA. Chẳng hạn, `(1,1,1)` dùng một bậc AR, sai phân một lần và một bậc MA; các bậc này không chứng minh rằng cấu trúc mùa vụ đã được xử lý.

#### Chẩn đoán residual

| Mô hình | Trung bình residual | Ljung–Box p-value (lag 12) | Ljung–Box p-value (lag 24) |
|---|---:|---:|---:|
| ARIMA(1,1,1) | 0.044193 | 5.97 × 10⁻¹⁴ | 1.22 × 10⁻²⁰ |
| ARIMA(2,1,1) | 0.044555 | 2.96 × 10⁻¹⁴ | 1.12 × 10⁻²⁰ |

Residual mean gần 0 nhưng không đủ để kết luận white noise. Các p-value Ljung–Box rất nhỏ ở cả hai lag cho thấy bác bỏ giả thuyết không có tự tương quan đến lag đang kiểm tra; residuals còn cấu trúc chưa được mô hình giải thích.

**Nếu residuals còn tự tương quan:** xem ACF residual để nhận biết lag còn sót, rồi cân nhắc điều chỉnh `p`/`q` hoặc, nếu được duyệt và có bằng chứng mùa vụ, thử mô hình mùa vụ. Fit lại trên train và kiểm tra residuals sau điều chỉnh; không tăng sai phân chỉ để làm một p-value giảm.

#### Forecast ngoài mẫu

| Mô hình | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| ARIMA(1,1,1) | 3.833290 | 4.865821 | 18.493973% |
| ARIMA(2,1,1) | 3.806130 | 4.834506 | 18.357607% |
| Seasonal naive (12) | 4.256436 | 5.186466 | 20.097262% |

Hai ARIMA có metric test thấp hơn seasonal-naive baseline trong lần chạy này. ARIMA(2,1,1) nhỉnh hơn một chút về MAE/RMSE/MAPE test, trong khi ARIMA(1,1,1) có AIC/BIC thấp hơn và ít bậc AR hơn. Chênh lệch metric giữa hai candidate nhỏ; không nên suy rộng kết quả holdout này thành bảo đảm hiệu quả ở giai đoạn khác.

Forecast nhiều bước của các ARIMA tiến dần thành đường gần như phẳng và không theo kịp mức tăng/dao động của test. Sai lệch tuyệt đối lớn nhất của cả hai xảy ra vào **2008-01-01**:

| Mô hình | Actual | Forecast | Absolute error |
|---|---:|---:|---:|
| ARIMA(1,1,1) | 29.665356 | 17.032661 | 12.632695 |
| ARIMA(2,1,1) | 29.665356 | 17.073772 | 12.591584 |

**Trả lời các câu hỏi đánh giá:**

1. **Vì sao không shuffle? Test set dùng để làm gì?** Shuffle phá vỡ trật tự quá khứ–tương lai và có thể đưa thông tin tương lai vào huấn luyện. Test là giai đoạn cuối chưa dùng để fit, dùng đánh giá forecast ngoài mẫu.
2. **Ý nghĩa p, d, q?** `p` là bậc tự hồi quy, `d=1` là sai phân thường một lần trên chuỗi log, `q` là bậc trung bình trượt của sai số.
3. **Mô hình có hội tụ không?** Có, cả hai candidate đều có `converged=True`; output không ghi warning.
4. **Residuals có white noise không?** Chưa có bằng chứng như vậy; Ljung–Box bác bỏ giả thuyết không tự tương quan ở lag 12 và 24 cho cả hai mô hình.
5. **Nếu residuals còn tự tương quan?** Kiểm tra ACF residual, điều chỉnh `p`/`q` hoặc xem xét thành phần mùa vụ trong scope được duyệt, sau đó fit và chẩn đoán lại.
6. **Forecast có bám sát xu hướng không?** Chưa tốt ở cuối horizon; đường dự báo phẳng trong khi test tiếp tục có mức cao và dao động.
7. **Sai lệch lớn nhất ở đâu?** Ngày 2008-01-01; các actual, forecast và absolute error được liệt kê trong bảng trên.
8. **Chỉ số nào nhạy với outlier nhất?** RMSE thường nhạy với lỗi lớn hơn MAE vì bình phương sai số. MAPE có thể mất ổn định khi actual bằng hoặc gần 0.
9. **RMSE lớn/nhỏ nói lên điều gì?** RMSE biểu thị độ lớn sai số theo đơn vị target; thấp hơn thường tốt hơn khi so sánh cùng dữ liệu và horizon. Không có ngưỡng “tốt” phổ quát; cần xem thêm MAE, baseline và mục tiêu ứng dụng.

---

## Phần II — Bài nâng cao: Dataset 2 `airline-passengers.csv`

### 1. EDA và scale phân tích

Dataset có 144 quan sát tháng. Đồ thị thể hiện xu hướng tăng cùng mùa vụ hàng năm; biên độ theo mùa tăng theo mức chuỗi. Notebook dùng **log scale** để làm ổn định hơn độ biến động theo mức, sau đó forecast được chuyển về thang passenger để đánh giá. Đây là lựa chọn hợp lý cho cấu trúc biến động tăng theo level, không phải khẳng định log là scale duy nhất có thể dùng.

Train gồm 115 tháng (1949-01 đến 1958-07); test gồm 29 tháng (1958-08 đến 1960-12). Không shuffle dữ liệu.

### 2–3. ADF và sai phân thường/mùa vụ

ADF áp dụng trên log-scale của train. Với chu kỳ mùa vụ `s=12`, kết quả là:

| Chuỗi | Quan sát đầu vào | ADF statistic | p-value | Lag dùng | N quan sát ADF | Quyết định ở mức 0.05 |
|---|---:|---:|---:|---:|---:|---|
| Log chuỗi gốc | 115 | -1.574027 | 0.496626 | 13 | 101 | Không bác bỏ H₀ |
| Sai phân thường `d=1` | 114 | -2.635851 | 0.085812 | 12 | 101 | Không bác bỏ H₀ |
| Sai phân mùa vụ `D=1, s=12` | 103 | -1.991013 | 0.290527 | 12 | 90 | Không bác bỏ H₀ |
| Sai phân kết hợp `d=1, D=1, s=12` | 102 | -3.946340 | 0.001719 | 11 | 90 | Bác bỏ H₀ |

Chỉ chuỗi sau sai phân thường và mùa vụ kết hợp đạt kết quả bác bỏ H₀ ở mức 0.05 trong các phép thử được lưu. Vì vậy cấu hình sử dụng là `d=1`, `D=1`, `s=12`. ADF hỗ trợ quyết định về dừng nhưng không chứng minh chuỗi hoàn toàn không còn cấu trúc hoặc residuals là white noise.

### 4. ACF/PACF và candidate

Trên chuỗi log đã sai phân kết hợp, các lag ACF có ý nghĩa gồm 1 (`-0.320677`), 3 (`-0.232934`) và 12 (`-0.429978`). Các lag PACF có ý nghĩa gồm 1, 3, 12, 23 và 36. Vì vậy đồ thị không cho một cutoff duy nhất, rõ ràng; order được xem là candidate thực nghiệm thay vì suy ra chắc chắn từ một spike.

Seasonal reference cho thấy ACF tại lag 12 có ý nghĩa, trong khi lag 24 và 36 không có ý nghĩa. Candidate đã fit trong notebook là:

- ARIMA baseline: `(1,1,1)`.
- SARIMA: `(1,1,1) × (0,1,1,12)`.

Seasonal MA bậc `Q=1` là candidate phù hợp để thử theo spike ACF tại lag 12; `P=0` là lựa chọn của cấu hình đã chạy, không phải kết luận duy nhất từ PACF. Các bậc nên được đánh giá thêm nếu mở rộng nghiên cứu.

### 5–7. Fit, chẩn đoán, forecast và so sánh

Cả hai mô hình hội tụ và output không ghi warning:

| Mô hình | Order | Seasonal order | AIC | BIC |
|---|---|---|---:|---:|
| ARIMA | (1,1,1) | — | -197.221464 | -189.012869 |
| SARIMA | (1,1,1) | (0,1,1,12) | -369.862160 | -359.362269 |

Residual diagnostics bằng Ljung–Box:

| Mô hình | p-value lag 12 | p-value lag 24 | Diễn giải |
|---|---:|---:|---|
| ARIMA | 0.999957 | 1.000000 | Không bác bỏ giả thuyết không tự tương quan ở các lag đã kiểm tra |
| SARIMA | 0.010010 | 0.408396 | Còn dấu hiệu tự tương quan ở lag 12; không bác bỏ tại lag 24 |

Các p-value không chứng minh residuals hoàn toàn là white noise; riêng SARIMA còn dấu hiệu ở lag 12 và cần được xem xét nếu tiếp tục hiệu chỉnh. Residual mean không được ghi trong bảng output hiện có nên không nêu con số.

Đánh giá trên test, theo đơn vị số hành khách:

| Mô hình | MAE | RMSE |
|---|---:|---:|
| ARIMA(1,1,1) | 84.254386 | 96.327568 |
| SARIMA(1,1,1)(0,1,1,12) | 12.165113 | 14.917604 |

Trong holdout hiện tại, SARIMA có MAE và RMSE thấp hơn đáng kể và forecast bám xu hướng/mùa vụ tốt hơn ARIMA. ARIMA nhiều bước gần như không theo kịp biến động mùa vụ. Sai lệch lớn nhất của ARIMA xảy ra ngày **1958-11-01** (actual 310, forecast 496.108123, absolute error 186.108123); của SARIMA vào **1960-03-01** (actual 419, forecast 452.003028, absolute error 33.003028).

**Kết luận:** Trên đúng lần chia train/test và các candidate đã thử, SARIMA cải thiện rõ MAE/RMSE so với ARIMA. Kết luận này chỉ áp dụng cho holdout hiện tại; không loại bỏ nhu cầu kiểm tra residual mùa vụ còn lại hoặc đánh giá trên giai đoạn khác. Không đưa MAPE vào bảng vì output nâng cao hiện có chỉ yêu cầu và lưu MAE/RMSE.

> **Trạng thái:** số liệu E06 phản ánh lần chạy exploratory trong notebook; chưa được xem là clean-kernel validation hoặc hoàn tất phê duyệt formal. Xem [current_status.md](./status/current_status.md).
