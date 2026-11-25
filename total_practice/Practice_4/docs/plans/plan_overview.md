# Practice 4 — Kế hoạch tổng quan

> **Trạng thái tài liệu:** BẢN NHÁP ĐÃ CẬP NHẬT THEO KIẾN TRÚC PHASE 0–10 — Làm cơ sở thiết kế Phase 0
> **Mức độ lập kế hoạch:** Chỉ mô tả tổng quan các giai đoạn; chưa phải kế hoạch triển khai chi tiết.
> **Tài liệu đi kèm:** `PROJECT_OVERVIEW.md`
> **Phạm vi xác nhận:** Việc thiết kế và triển khai từng giai đoạn phải được xác nhận theo quy tắc quản trị áp dụng cho kho mã nguồn.

## 1. Mục đích

Hoàn thành Practice 4 theo trình tự: định nghĩa bài toán, chuẩn bị dữ liệu, khóa temporal split, thực hiện training-only EDA, preprocessing, feature engineering, modeling, final evaluation và cuối cùng tổng hợp notebook/report. Không tạo trước toàn bộ tài liệu chi tiết cho các phase và không triển khai phase tiếp theo khi phase hiện tại chưa được kiểm tra.

Kế hoạch này bám các yêu cầu của đề: bốn biến đầu vào, lịch sử 24 giờ, dự báo điện năng ở bước tiếp theo, ba mô hình VAR/XGBoost/LSTM, chia dữ liệu theo thời gian 70/15/15, đánh giá bằng RMSE/MAE/MAPE và kiểm định dự báo tiến dần theo thời gian. **Hourly energy demand, generation and weather** được chọn làm dataset chính. Quyết định nguồn dữ liệu không tự khóa data contract, weather aggregation, preprocessing hoặc evaluation protocol.

## 2. Điều kiện tiên quyết và thẩm quyền

1. **Đọc trước:** Toàn bộ nội dung thực tế của `AGENTS.md`, `working_rule.md`, `.agents/RULES_INDEX.md`, các quy tắc có hiệu lực theo phạm vi và tệp PDF đề bài.
2. **Kiểm tra trước khi sửa:** Xem cấu trúc thư mục Practice 4, các tài liệu dự án đã có, quyết định được xác nhận và trạng thái kho mã nguồn; bảo toàn kết quả cũ, chỉ thay đổi phần cần thiết.
3. **Xử lý xung đột:** Khi hướng dẫn mâu thuẫn với quy tắc quản trị hoặc đặc tả đã xác nhận, phải báo cáo xung đột và dừng phần việc có tranh chấp cho đến khi người dùng quyết định.
4. **Giới hạn phạm vi:** Chỉ sửa tệp trong phạm vi Practice 4 đã được chấp thuận; phải xin phép trước khi đổi quy tắc chung hoặc động đến những bài thực hành khác.
5. **Phân biệt trạng thái:** Không đánh đồng **ĐÃ XÁC NHẬN**, **ĐỀ XUẤT**, **CẦN XÁC ĐỊNH** và **ĐÃ KIỂM CHỨNG**.
6. **Nguyên tắc xác nhận:** Không tự nâng một bản nháp thành yêu cầu đã xác nhận hoặc chuyển sang giai đoạn tiếp theo khi chưa có quyết định rõ ràng.

**Tình trạng kiểm tra:** Các governance files, shared rules, cấu trúc Practice 4 và hai archive CSV công khai đã được kiểm tra read-only ở mức sơ bộ ngày 2026-11-13. Kết quả sơ bộ chỉ cung cấp context cho thiết kế; Phase 1 phải tái lập kiểm tra từ source version đã khóa, lưu checksum/provenance và tạo execution evidence theo kế hoạch được xác nhận.

## 3. Chu trình thực hiện

1. Kiểm tra quy tắc quản trị và các tệp đang có.
2. Soạn `PROJECT_OVERVIEW.md` và `plan_overview.md`.
3. Kiểm tra cơ sở lập kế hoạch.
4. Chỉ thiết kế chi tiết **Phase 0 — Problem Definition** rồi xin xác nhận.
5. Triển khai Phase 0 trong phạm vi tài liệu, validation và kiểm tra; không xử lý dữ liệu.
6. Chỉ thiết kế **Phase 1 — Data Preparation** sau khi Phase 0 hoàn thành.
7. Thực hiện tuần tự từng phase theo chu trình: thiết kế → phase gate → triển khai → validation → kiểm tra.
8. Chỉ tạo end-to-end notebook và final report ở Phase 10 sau khi Phase 0–9 có artifacts đã xác nhận.

**Lưu ý:** Kiểm tra hai tài liệu tổng quan chỉ cho phép **thiết kế Phase 0**, không cho phép tự động triển khai Phase 0 hoặc bất kỳ phase nào khác. Phase 0 vẫn cần specification và before-process plan được xác nhận.

## 4. Bản đồ tổng quan các giai đoạn (ĐỀ XUẤT)

| Giai đoạn | Mục tiêu | Kết quả và bằng chứng chính | Điều kiện bắt đầu | Điều kiện hoàn thành |
|---|---|---|---|---|
| **0 — Problem Definition** | Khóa business/scientific objective, forecasting contract dự kiến, scope, constraints và acceptance criteria; không xử lý dữ liệu | Problem Definition được kiểm tra, nêu rõ target, input, horizon, models, metrics và split requirement | Hai tài liệu tổng quan được xác nhận; Phase 0 specification và plan được xác nhận | kiểm tra Problem Definition |
| **1 — Data Preparation** | Kiểm chứng hai raw CSV, chuẩn hóa/deduplicate weather, tạo weather proxy, join và tạo canonical hourly dataset; bảo toàn missing target | Raw provenance/checksum, data-preparation audit, canonical dataset và verified data contract | Phase 0 hoàn thành; Phase 1 specification và plan được xác nhận | xác nhận audit, canonical dataset và data contract |
| **2 — Temporal Split và Validation Design** | Chia 70/15/15 theo thời gian, khóa test set, forecast origins, context-boundary rule và walk-forward contract | Split manifest, validation contract, overlap/leakage checks và test-access policy | Canonical dataset và data contract được xác nhận | xác nhận split và validation design |
| **3 — Exploratory Data Analysis** | Phân tích missing/outlier, distribution, trend, daily/weekly seasonality, load–weather relationship và temporal dependence chỉ trên training set | Reproducible figures, training-only EDA findings và preprocessing proposals | Temporal split được khóa | kiểm tra EDA evidence; validation/test không bị quan sát để ra quyết định |
| **4 — Preprocessing và Scaling** | Giữ missing target trong canonical data; forward-fill `load` past-only cho input; loại target thiếu khỏi metrics; fit scaler chỉ trên train | Processed splits, fitted preprocessing artifacts và leakage audit | Training-only EDA được kiểm tra; preprocessing plan được xác nhận | Data quality, chronology và transform-boundary checks đạt yêu cầu |
| **5 — Feature Engineering và Supervised Conversion** | Tạo window 24 giờ, lag/rolling/trend features và model-ready inputs với cùng forecast origins | Feature dictionary, VAR/XGBoost/LSTM inputs, shape/alignment/leakage audit | Processed splits được xác nhận | kiểm tra model-ready data và alignment evidence |
| **6 — VAR và benchmark tùy chọn** | Thực hiện ADF/differencing, AIC/BIC lag selection, VAR validation và residual diagnostics; Naive/Seasonal Naive chỉ là benchmark bổ sung nếu được chọn | Locked VAR configuration và validation evidence; nếu có benchmark thì lưu thêm baseline metrics | Model-ready data và evaluation protocol được xác nhận | kiểm tra VAR diagnostics; benchmark không phải cổng bắt buộc |
| **7 — XGBoost** | Tune `max_depth`, `n_estimators`, early stopping trên validation và weather contribution analysis | Locked XGBoost configuration, validation metrics và feature-attribution evidence | Phase 5 inputs và comparison rules được xác nhận | kiểm tra XGBoost validation evidence; cấu hình khóa trước test |
| **8 — LSTM** | Huấn luyện kiến trúc theo đề, early stopping, learning curves và overfitting analysis | Locked LSTM configuration, validation metrics và training diagnostics | Phase 5 sequence inputs và training plan được xác nhận | kiểm tra LSTM evidence; cấu hình khóa trước test |
| **9 — Walk-forward Evaluation và Error Analysis** | Mở test sau model lock, recursive append prediction theo PDF, đánh giá cùng forecast origins bằng RMSE/MAE/MAPE và phân tích error/residual regimes; không tuning lại | Official recursive predictions, metrics, comparison và error-analysis evidence | Ba model đã khóa; benchmark nếu có không phải điều kiện mở test | kiểm tra tính công bằng, metric correctness và limitations |
| **10 — End-to-End Notebook và Final Report** | Tổng hợp artifacts đã xác nhận, trả lời sáu câu hỏi và trình bày conclusion; không triển khai lại pipeline | `practice_4_end_to_end.ipynb`, final report và reproducibility references | Phase 0–9 artifacts đã được kiểm tra | kiểm tra hoàn tất notebook và final report |

Kiến trúc và thứ tự Phase 0–10 đã được thống nhất ở mức tổng quan. Nội dung chi tiết, file owners, phương pháp và acceptance criteria của từng phase chỉ có hiệu lực triển khai sau khi phase specification và before-process plan tương ứng được kiểm tra.

## 5. Phase 0 — phase duy nhất được thiết kế chi tiết tiếp theo

### 5.1. Mục tiêu

- Định nghĩa bài toán multivariate one-step forecasting.
- Xác định provisional forecasting contract `[X(t-23), …, X(t)] → load(t+1)`.
- Ghi rõ dataset source đã được chọn mà không tuyên bố schema/data contract đã kiểm chứng.
- Khóa target dự kiến, input variables, horizon, model families, metrics, split requirement, scope và constraints.
- Xác định acceptance criteria cho Problem Definition.

### 5.2. Kết quả bắt buộc

- Problem Definition có 5W1H và forecasting objective rõ ràng.
- Provisional input/output contract và terminology nhất quán.
- Danh sách confirmed requirements, proposals và decisions thuộc phase sau.
- Phạm vi trong/ngoài bài và các ambiguity cần chuyển tới đúng phase owner.
- kiểm tra và xác nhận trước khi thiết kế Phase 1.

### 5.3. Ranh giới Phase 0

Phase 0 không tải dữ liệu, không tạo checksum, không đọc hoặc join raw CSV trong execution workflow, không tạo processed dataset, không chia train/validation/test và không huấn luyện model. Preliminary inspection đã có chỉ là context cho planning, không phải output của Phase 0.

### 5.4. Ownership chuyển sang Phase 1

Phase 1 chịu trách nhiệm kiểm chứng `energy_dataset.csv` và `weather_features.csv`, khóa provenance/schema, deduplicate và tổng hợp weather, join theo timestamp, bảo toàn missing target, tạo canonical hourly dataset và trình verified data contract để kiểm tra. Không đưa các trách nhiệm này trở lại Phase 0.

## 6. Các nguyên tắc đánh giá bắt buộc (cần đối chiếu với quy tắc kho mã nguồn)

- Chia dữ liệu theo thứ tự thời gian với tỷ lệ 70/15/15; không xáo trộn.
- Khóa temporal split ở Phase 2 trước Phase 3; EDA chỉ sử dụng training set và không quan sát validation/test để ra quyết định.
- Naive/Persistence và Seasonal Naive lag 24 là benchmark tùy chọn để tăng khả năng diễn giải; chúng không thuộc yêu cầu bắt buộc của PDF và không thay thế ba model VAR/XGBoost/LSTM.
- Chỉ ước lượng bộ chuẩn hóa và bộ điền dữ liệu thiếu từ thông tin huấn luyện được phép; không để thống kê từ tập xác thực/kiểm tra rò rỉ vào huấn luyện.
- Với mỗi dự báo cho thời điểm `t+1`, chỉ sử dụng thông tin đã có khi bắt đầu dự báo. Đặc biệt kiểm tra mốc thời gian của dữ liệu thời tiết và các cửa sổ trượt.
- Duy trì cùng khoảng dự báo, thang đo mục tiêu và các mốc kiểm tra tương đương giữa mô hình. Nếu dữ liệu buộc phải khác nhau, cần công bố sự khác biệt một cách rõ ràng.
- Chỉ điều chỉnh tham số và thực hiện dừng sớm dựa trên tập xác thực; không chọn mô hình dựa trên điểm số của tập kiểm tra cuối cùng.
- Xác định quy trình dự báo tiến dần theo thời gian trước khi báo cáo; phân biệt việc dùng giá trị thực mới quan sát với dùng giá trị dự báo trước đó và nêu rõ có huấn luyện lại hay không.
- Quy định cách tính MAPE khi giá trị điện năng thực tế bằng 0 và báo cáo số điểm bị ảnh hưởng.
- Không kết luận LSTM học chu kỳ tuần chỉ từ training loss hoặc vì dữ liệu có weekly seasonality; cửa sổ 24 giờ không trực tiếp chứa lag 168.
- Giữ nguyên dữ liệu gốc và ghi lại nguồn gốc từng bước tiền xử lý.

Đây là các mục tiêu bảo đảm chất lượng kỹ thuật, **không thay thế** quy tắc quản trị đã có trong kho mã nguồn.

## 7. Quy định về tài liệu và phạm vi thay đổi

- **Hiện tại:** kiểm tra đồng thời bản cập nhật `PROJECT_OVERVIEW.md` và `plan_overview.md`; dataset source đã được chọn nhưng data contract chưa được xác nhận.
- **Tiếp theo:** Chỉ soạn **Phase 0 Problem Definition specification** và before-process plan; xin xác nhận trước khi cập nhật phase artifact.
- **Trong Phase 0:** Chỉ định nghĩa bài toán, forecasting contract dự kiến, scope, constraints và acceptance criteria; không xử lý dữ liệu.
- **Sau Phase 0:** Chỉ thiết kế Phase 1 khi Problem Definition đã được kiểm tra.
- **Các phase sau:** Tạo specification gần thời điểm thực hiện từng phase, không tạo sẵn tất cả cùng lúc.

Không tạo tệp trùng nếu đã có tài liệu tương đương. Không tự đổi tên, di chuyển hoặc viết lại kiến trúc thư mục và quy tắc chung khi chưa được phép.

## 8. Danh sách kiểm tra trước xác nhận

- [x] Đã đọc quy tắc quản trị thực tế trong kho mã nguồn; chưa phát hiện xung đột chặn documentation update
- [x] Đã thể hiện đúng các yêu cầu của đề bài và các ambiguity cần giải quyết
- [x] Bộ dữ liệu Spain được ghi rõ là dataset chính đã chọn
- [x] Dataset selection được tách khỏi data contract và preprocessing validation
- [x] Preliminary inspection không được trình bày như Phase 1 verification
- [x] Kiến trúc Phase 0–10 và thứ tự thực hiện đã được thống nhất
- [x] Phase 0 chỉ sở hữu Problem Definition; Phase 1 sở hữu Data Preparation và verified data contract
- [x] Temporal Split là Phase 2 độc lập; EDA là Phase 3 và chỉ dùng training set
- [x] Phase 10 sở hữu end-to-end notebook và final report
- [x] Mỗi phase có bước thiết kế và cổng kiểm tra riêng
- [x] Bản nháp này chưa cho phép lập trình hoặc tạo sẵn tài liệu chi tiết các giai đoạn sau
- [ ] Cặp tài liệu được xác nhận làm **cơ sở lập kế hoạch ban đầu**

## 9. Tình trạng hiện tại

**Lập kế hoạch:** Bản nháp kiến trúc Phase 0–10.
**Chiến lược dữ liệu:** Spain Electricity Consumption & Weather là dataset chính ĐÃ CHỌN; verified data contract CẦN XÁC ĐỊNH Ở PHASE 1.
**Phase 0:** CHƯA BẮT ĐẦU; chỉ sở hữu Problem Definition và chưa có detailed specification.
**Preliminary inspection:** Đã có planning context nhưng không phải output của Phase 0 hoặc Phase 1 evidence.
**Thay đổi trong kho mã nguồn:** Notebook Practice 4 đã được triển khai và chạy kiểm chứng trên môi trường hiện tại; các phase artifact và final report đang được tổng hợp.

**Nguồn tham chiếu:** PDF đề bài Practice 4 trong bộ tài liệu; governance files thực tế; `PROJECT_OVERVIEW.md`; Kaggle dataset page; trang UCI và preliminary inspection của hai CSV công khai. Mọi quyết định ngoài dataset source và phase architecture vẫn là đề xuất hoặc vấn đề cần phase owner kiểm chứng.
