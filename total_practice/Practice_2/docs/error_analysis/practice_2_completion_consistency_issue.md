# Error Analysis — Sai lệch trạng thái hoàn thành Practice 2

## 1. Thông tin vấn đề

- **Phạm vi:** Practice 2, Exercise 1–6
- **Loại vấn đề:** Đồng bộ tài liệu, trạng thái notebook và mức độ hoàn thành chính thức
- **Trạng thái:** `RESOLVED_WITH_OPTION_A`
- **Ảnh hưởng đến E1–E5:** Không phát hiện sai số tính toán làm thay đổi kết luận hiện tại
- **Ảnh hưởng đến E6:** Chưa đủ điều kiện đánh dấu hoàn thành chính thức

## 2. Kỳ vọng

Sau khi một Exercise được triển khai và kiểm tra:

1. `README.md`, `docs/report.md` và `docs/status/current_status.md` phải phản ánh cùng một trạng thái.
2. Notebook trình bày phải chạy sạch từ đầu đến cuối và được lưu với execution state nhất quán.
3. Kết quả quan trọng phải có artifact, test và implementation tái sử dụng trong `src/practice_2/` khi specification yêu cầu.
4. Kết luận thống kê phải khớp với số liệu hiện hành.
5. Không được đánh dấu hoàn thành một phạm vi chưa được Human phê duyệt đầy đủ.

## 3. Hiện trạng quan sát được

### 3.1. Tài liệu và trạng thái chưa đồng bộ

- `README.md` vẫn mô tả project ở giai đoạn khởi tạo, dataset chưa chốt và E3 còn bị chặn.
- `docs/status/current_status.md` vừa ghi E5 đã hoàn thành, vừa còn trạng thái chờ Human review; E6 mới được phê duyệt phạm vi residual diagnostics nhưng chưa được phê duyệt toàn bộ workflow.
- `docs/report.md` còn kết quả cũ:
  - còn nhắc đến candidate ARIMA `(4, 1, 1)`;
  - còn dùng residual diagnostics cũ của E5;
  - kết luận E6 bị đảo ngược so với kết quả đã sửa: tài liệu cũ mô tả ARIMA sạch hơn SARIMA, trong khi bằng chứng hiện hành cho thấy điều ngược lại.

### 3.2. Notebook chính có execution state không nhất quán

`notebooks/Practice_2_present.ipynb` có một số code cell chưa có `execution_count`, trong khi các cell khác có số thứ tự không tăng tuần tự. Notebook vẫn chạy sạch trên bản sao tạm, nhưng trạng thái lưu hiện tại chưa phù hợp để bàn giao hoặc trình bày.

### 3.3. E6 chưa hoàn tất formal workflow

- Phạm vi được Human phê duyệt hiện tại chỉ bao phủ residual diagnostics fix.
- Nhiều logic quan trọng vẫn nằm trực tiếp trong notebook: validation, ADF, differencing, ACF/PACF, model fitting, forecasting và metrics.
- Test hiện tại chủ yếu xác nhận residual diagnostics fix, chưa bao phủ toàn bộ E6.
- Chưa có đầy đủ các artifact dự kiến:

  - `figures/06_airpassengers_original_series.png`
  - `figures/06_airpassengers_differencing.png`
  - `figures/06_airpassengers_acf_pacf.png`
  - `figures/06_airpassengers_forecast_comparison.png`
  - `results/06_airpassengers_validation.csv`
  - `results/06_airpassengers_split.csv`
  - `results/06_airpassengers_adf_results.csv`
  - `results/06_airpassengers_model_candidates.csv`
  - `results/06_airpassengers_forecasts.csv`
  - `results/06_airpassengers_metrics.csv`

### 3.4. Thiếu provenance phục vụ trình bày

Hai notebook chưa có phần 5W1H đầy đủ và chưa ghi rõ link nguồn dataset. File `a10.csv` chỉ chứa `date,value`, vì vậy bản thân file raw không đủ để độc lập xác nhận nhãn nghiệp vụ “US Monthly Retail Sales”.

## 4. Bằng chứng kiểm tra

- Test suite: **30 passed**.
- Cả hai notebook đều chạy sạch từ đầu đến cuối trên bản sao tạm.
- Artifact CSV/PNG tạo lại trên bản sao tạm khớp byte-for-byte với artifact hiện có.
- SHA-256 dataset:
  - `a10.csv`: `4baa700091ba43f59d762ed7112e203134467ecde3f7bc88da3b153040d384cb`
  - `AirPassengers.csv`: `8cb51be753a718d9be5d76d7e238cc224792754676adc21faa59e954b0201621`
- E6 sau residual fix:
  - ARIMA: Ljung–Box p-value tại lag 12/24 là `2.944816e-16` / `2.308263e-27` — còn autocorrelation.
  - SARIMA: Ljung–Box p-value tại lag 12/24 là `0.573996` / `0.473545` — chưa phát hiện autocorrelation tại các lag đã kiểm tra.
  - ARIMA MAE/RMSE: `84.254030` / `96.327159`.
  - SARIMA MAE/RMSE: `12.164590` / `14.917399`.

## 5. Nguyên nhân gốc

1. Implementation được thực hiện theo nhiều đợt nhưng tài liệu tổng hợp không được đồng bộ sau từng đợt.
2. E6 chỉ được phê duyệt một fix cục bộ, trong khi notebook đã phát triển thành một workflow rộng hơn.
3. Notebook trình bày đã được chỉnh sửa sau lần execute gần nhất nên execution state bị lệch.
4. Provenance và yêu cầu trình bày 5W1H chưa được đưa vào specification ban đầu.

## 6. Tác động

- E1–E5 vẫn có thể xem là đúng về kết quả tính toán hiện tại.
- Người đọc có thể hiểu sai tiến độ và kết luận model nếu dựa vào `README.md`, `report.md` hoặc `current_status.md`.
- E6 chưa thể đánh dấu `COMPLETED` dù notebook có kết quả chạy được.
- Việc chỉ chỉnh hình thức notebook lúc này có thể che khuất sai lệch trạng thái thay vì giải quyết nó.

## 7. Ranh giới xử lý

- Không thay đổi split, model order, metrics hoặc kết quả khoa học của E1–E5 trong đợt đồng bộ này.
- Không tự ý triển khai toàn bộ E6 trước khi Human chọn phạm vi.
- Không ghi nguồn dataset chưa được xác minh như một dữ kiện chắc chắn.
- Không push lên GitHub khi chưa có yêu cầu riêng từ Human.

## 8. Quyết định Human đã chốt

- **Phương án được chọn:** Phương án A — giữ E6 ở mức exploratory, đồng bộ tài liệu,
  ghi rõ giới hạn và không đánh dấu E6 hoàn thành chính thức.
- Phương án formalize E6 không được triển khai trong phạm vi hiện tại.
