# Practice 4 — Tổng quan dự án dự báo chuỗi thời gian đa biến

> **Trạng thái tài liệu:** BẢN NHÁP ĐÃ CẬP NHẬT THEO KIẾN TRÚC PHASE 0–10 ĐƯỢC HUMAN THỐNG NHẤT — Chờ phê duyệt làm cơ sở thiết kế Phase 0
> **Dự án:** Time Series / Practice 4
> **Mục đích:** Xác định bài toán, phạm vi và các quyết định cần có trước khi triển khai.
> **Căn cứ thực hiện:** Đề bài quy định mục tiêu học tập; các quy tắc quản trị kho mã nguồn và quyết định được người dùng phê duyệt quy định việc triển khai.
> **Tài liệu đi kèm:** `plan_overview.md`

## 1. Quản lý tài liệu và trạng thái quyết định

Đây là **bản nháp phục vụ lập kế hoạch**, không phải văn bản cho phép triển khai. Mọi nhận định và quyết định cần được phân biệt theo các trạng thái sau:

- **ĐÃ XÁC NHẬN (THEO ĐỀ):** Yêu cầu được nêu rõ trong `references/practice 4.pdf`.
- **ĐÃ ĐƯỢC HUMAN CHỌN:** Quyết định phạm vi do Human phê duyệt trong quá trình thảo luận.
- **ĐỀ XUẤT:** Lựa chọn được khuyến nghị nhưng phải được người dùng xem xét.
- **CHỜ QUYẾT ĐỊNH:** Vấn đề chỉ có thể kết luận sau khi kiểm tra dữ liệu thực tế, đối chiếu quy tắc kho mã nguồn hoặc nhận phê duyệt từ người dùng/giảng viên.
- **ĐÃ KIỂM CHỨNG:** Có bằng chứng kiểm tra hoặc kết quả thử nghiệm được ghi nhận; không sử dụng trạng thái này khi chưa thực hiện kiểm chứng.
- **ĐÃ KIỂM TRA SƠ BỘ:** Có kết quả read-only inspection nhưng chưa thay thế bằng chứng có thể tái lập và approval gate của Phase 1.

**Tình trạng đối chiếu quản trị:** `AGENTS.md`, `working_rule.md`, `.agents/RULES_INDEX.md`, các shared rules, canonical workflow và cấu trúc Practice 4 đã được đọc trực tiếp ngày 2026-11-13. Chưa có Practice 4-specific normative rule ngoài các shared rules được router chỉ định. Mọi implementation vẫn phải có phase specification, before-process plan và Human approval theo workflow hiện hành.

## 2. Bài toán theo yêu cầu đề bài (ĐÃ XÁC NHẬN)

Xây dựng và so sánh các mô hình **dự báo điện năng sử dụng đầu vào chuỗi thời gian đa biến**. Dùng lịch sử quan sát trong **24 giờ gần nhất** để dự báo giá trị điện năng ở **bước thời gian tiếp theo**, ký hiệu `load(t+1)`.

- **Biến đầu vào:** `load`, `temperature`, `humidity`, `wind_speed`.
- **Biến cần dự báo:** Chỉ dự báo điện năng tiêu thụ ở bước tiếp theo.
- **Nhóm mô hình:** VAR (thống kê), XGBoost (học máy) và LSTM (học sâu).
- **Chỉ số đánh giá:** RMSE, MAE và MAPE.
- **Chia dữ liệu theo thời gian:** Tập huấn luyện 70%, tập xác thực 15% và tập kiểm tra 15%; giữ nguyên thứ tự thời gian, không xáo trộn.
- **Khám phá dữ liệu:** Giá trị thiếu, giá trị ngoại lai, tính mùa vụ theo ngày và tuần; đồ thị điện năng theo thời gian, điện năng so với nhiệt độ và ma trận tương quan.
- **Tiền xử lý:** Chuẩn hóa bằng `StandardScaler`; cách ước lượng tham số chuẩn hóa phải tránh rò rỉ dữ liệu.
- **Tạo đặc trưng:** Cửa sổ trễ 24 giờ; riêng XGBoost có thêm trung bình trượt 6 giờ, độ lệch chuẩn trượt 24 giờ và đặc trưng xu hướng điện năng.
- **Yêu cầu VAR:** Kiểm tra tính dừng bằng ADF, lấy sai phân khi cần, lựa chọn bậc trễ qua AIC/BIC; VAR dự báo cả véc-tơ biến nhưng chỉ đánh giá biến điện năng.
- **Yêu cầu XGBoost:** Điều chỉnh ít nhất `max_depth` và `n_estimators`; dừng sớm dựa trên tập xác thực.
- **Yêu cầu LSTM:** Đầu vào có kích thước `(số_mẫu, 24, 4)` nếu dữ liệu theo giờ; kiến trúc `LSTM(64) → LSTM(32) → Dense(1)`, hàm mất mát MSE và bộ tối ưu Adam.
- **Kiểm định dự báo theo thời gian:** Đề yêu cầu đánh giá tiến dần theo thời gian, nhưng chưa quy định rõ cách cập nhật dữ liệu và mô hình sau mỗi bước dự báo.
- **Bài nâng cao:** Dự báo giao thông với METR-LA / PEMS-BAY; tách khỏi quy trình chính.

Với chuỗi theo giờ, quy ước cửa sổ quan sát được đề xuất là:

`[X_(t-23), ..., X_t] → load_(t+1)`, trong đó `X_t = [load_t, temperature_t, humidity_t, wind_speed_t]`.

Cách đánh chỉ số trên là **ĐỀ XUẤT** để tránh nhầm lẫn, cần được xác nhận trong tài liệu đặc tả dữ liệu. Một cửa sổ lịch sử 24 giờ phải chứa đúng **24 quan sát theo giờ**.

## 3. Mâu thuẫn dữ liệu trong đề và quyết định nguồn chính

Đề bài nêu bộ **UCI Electricity Load Diagrams 2011–2014** và liệt kê thêm ba biến thời tiết. Tuy nhiên, bộ UCI gốc ghi nhận mức sử dụng điện của **370 khách hàng, với tần suất 15 phút**, và **không chứa** ba biến thời tiết được yêu cầu.

Hệ quả:

1. Không thể tạo đầu vào gồm bốn biến chỉ từ tệp UCI gốc.
2. Với tần suất 15 phút, lịch sử 24 giờ tương đương 96 bước thời gian, không phải 24 bước.
3. Cần xác định rõ cách chọn, tổng hợp và diễn giải biến mục tiêu `load`.

Nguồn: <https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014>

### Quyết định dataset

| Phương án | Mô tả | Trạng thái | Đánh đổi chính |
|---|---|---|---|
| A | Spain Electricity Consumption & Weather (2015–2018), gồm dữ liệu điện theo giờ và weather của năm thành phố | **DATASET CHÍNH — ĐÃ ĐƯỢC HUMAN CHỌN ngày 2026-11-13** | Khớp hourly setup và có chuỗi bốn năm; phải định nghĩa weather proxy cho national load |
| B | UCI Power Consumption of Tetouan City | **Fallback** | Cùng địa điểm và đủ ba biến weather nhưng tần suất 10 phút, chỉ một năm và có ba target zone |
| C | UCI Electricity Load Diagrams 2011–2014 hiện có trong repository | **Source evidence, không dùng làm dataset chính** | Không có weather và có 370 client series ở tần suất 15 phút |

Nguồn phương án A: <https://www.kaggle.com/datasets/nicholasjhana/energy-consumption-generation-prices-and-weather>
Nguồn phương án B: <https://archive.ics.uci.edu/dataset/849/power%2Bconsumption%2Bof%2Bteto>

**Quyết định Human:** Được phép thay dataset ghi trong đề để phù hợp với bài và chọn phương án A làm dataset chính. Quyết định này khóa **nguồn dữ liệu**, không tự phê duyệt data contract, weather aggregation, missing-value treatment hoặc evaluation protocol.

### Kết quả preliminary read-only inspection (ĐÃ KIỂM TRA SƠ BỘ)

- `energy_dataset.csv`: 35.064 dòng, 29 cột, timestamp hourly liên tục từ 2015 đến hết 2018 khi chuẩn hóa về UTC; không có timestamp trùng.
- `weather_features.csv`: 178.396 dòng, 17 cột; gồm Barcelona, Bilbao, Madrid, Seville và Valencia.
- Mỗi thành phố có 35.064 city-hour duy nhất và mọi timestamp điện năng đều có weather của đủ năm thành phố.
- Có 3.076 weather rows dư, phân bố trong 2.798 city-hour groups bị lặp do nhiều weather descriptions; `temp`, `humidity`, `wind_speed` giống nhau trong các bản lặp đã kiểm tra.
- `total load actual` có 36 giá trị thiếu; `temp`, `humidity`, `wind_speed` không có giá trị thiếu.
- `city_name` của Barcelona có leading whitespace cần chuẩn hóa.

Các kết quả trên phải được Phase 1 tái lập từ archive đã tải theo quy trình được duyệt, kèm source version, retrieval date, checksum và execution evidence. Chúng chưa phải approval cho data preparation hoặc preprocessing policy cụ thể.

## 4. Định nghĩa bài toán dự kiến — nguồn chính đã chọn, data contract chưa khóa

| Thành phần | Nội dung dự kiến | Trạng thái |
|---|---|---|
| Nhiệm vụ dự báo | Dự báo điện năng trước một bước thời gian | ĐÃ XÁC NHẬN |
| Bộ dữ liệu chính | Spain Electricity Consumption & Weather | ĐÃ ĐƯỢC HUMAN CHỌN |
| Biến mục tiêu điện năng | `total load actual` | Tên cột ĐÃ KIỂM TRA SƠ BỘ; đơn vị và missing-value semantics CHỜ PHASE 1; treatment CHỜ PHASE 4 |
| Biến thời tiết | `temp`, `humidity`, `wind_speed` | Tên cột và coverage ĐÃ KIỂM TRA SƠ BỘ; đơn vị và aggregation CHỜ PHASE 1 |
| Tần suất | Theo giờ | ĐÃ KIỂM TRA SƠ BỘ; timezone/DST contract CHỜ PHASE 1 |
| Độ dài lịch sử | 24 giờ; tương đương 24 quan sát nếu dữ liệu theo giờ | 24 giờ: ĐÃ XÁC NHẬN; cách tạo mẫu: CHỜ QUYẾT ĐỊNH |
| Khoảng dự báo | Giờ tiếp theo | ĐÃ XÁC NHẬN theo cách diễn giải `t+1` trên dữ liệu hourly |
| Đại diện thời tiết | Một national weather proxy từ năm thành phố; unweighted mean là phương án khởi đầu | ĐỀ XUẤT; CHỜ PHASE 1 kiểm chứng và Human phê duyệt |
| Múi giờ | Chuẩn hóa và ghi nhận múi giờ nguồn, cách xử lý đổi giờ mùa hè | CHỜ QUYẾT ĐỊNH |
| Chia dữ liệu | Theo thời gian, tỷ lệ 70/15/15 | ĐÃ XÁC NHẬN |
| Tập kiểm tra cuối cùng | Không sử dụng để chọn mô hình/cấu hình trước khi khóa các lựa chọn | Biện pháp bảo vệ — ĐỀ XUẤT |
| MAPE khi điện năng thực tế bằng 0 | Quy định cách xử lý và báo cáo số điểm chịu ảnh hưởng | CHỜ QUYẾT ĐỊNH |
| Đánh giá tiến dần theo thời gian | Quy định lúc có giá trị thực mới và có huấn luyện lại mô hình hay không | CHỜ QUYẾT ĐỊNH |

**Chưa được quyết định trước** cách điền giá trị thiếu, tổng hợp khi đổi tần suất, chọn thành phố, loại bỏ ngoại lai hoặc biến đổi biến mục tiêu. Các lựa chọn này chỉ được chốt sau khi kiểm tra dữ liệu và ghi nhận ảnh hưởng của chúng.

Dataset UCI `LD2011_2014.txt` hiện có trong `datasets/raw/` phải được giữ nguyên. Việc chọn Spain làm dataset chính không tạo quyền xóa, di chuyển hoặc ghi đè source evidence này.

## 5. Nguyên tắc bảo đảm tính khoa học và ngăn rò rỉ dữ liệu

1. **Truy xuất nguồn dữ liệu:** Giữ nguyên dữ liệu gốc; ghi lại đường dẫn nguồn, ngày tải, giấy phép/điều khoản liên quan, tên tệp, mã kiểm tra toàn vẹn, cấu trúc cột, khoảng thời gian và giả định về múi giờ.
2. **Đúng thứ tự nhân quả theo thời gian:** Mọi đặc trưng phải có thể quan sát tại thời điểm phát lệnh dự báo. Không sử dụng **dữ liệu thời tiết quan sát trong tương lai**, trừ khi bài toán xác định rõ việc dùng dự báo thời tiết thực sự có sẵn tại thời điểm đó.
3. **Ngăn rò rỉ dữ liệu:** Chỉ ước lượng tham số của bộ chuẩn hóa, bộ điền thiếu, phép biến đổi, bước lựa chọn đặc trưng và tiền xử lý thống kê từ phần dữ liệu huấn luyện được phép sử dụng. Tập xác thực phục vụ lựa chọn; tập kiểm tra cuối cùng không được dùng để lựa chọn.
4. **Ranh giới thời gian:** Quy định cách cửa sổ lịch sử đi qua ranh giới chia tập mà không sử dụng mục tiêu tương lai hay làm rò rỉ thống kê đã học.
5. **So sánh công bằng:** Các mô hình dùng cùng biến mục tiêu, khoảng dự báo, mốc thời gian đánh giá tương đương và phạm vi thông tin đầu vào hợp lệ như nhau. Ghi rõ các bước xử lý riêng của từng mô hình.
6. **Tính đúng đắn của chỉ số:** Báo cáo chỉ số trên thang đo điện năng gốc và quy định MAPE khi giá trị thực bằng 0.
7. **Khả năng tái lập:** Ghi nhận cấu hình, hạt giống ngẫu nhiên khi áp dụng, môi trường phần mềm và nguồn gốc của từng thí nghiệm.
8. **Diễn giải kết quả:** Tương quan hoặc tầm quan trọng đặc trưng đối với dự báo không tự chứng minh quan hệ nhân quả giữa thời tiết và điện năng.
9. **Baseline theo repository rule:** Trước VAR/XGBoost/LSTM phải đánh giá ít nhất Naive/Persistence và Seasonal Naive với lag 24 giờ. Đây là auxiliary quality baselines, không thay thế ba mô hình bắt buộc trong đề.
10. **Giới hạn nhận diện chu kỳ tuần:** Cửa sổ chỉ dài 24 giờ không trực tiếp cung cấp lag 168 hoặc day-of-week. Không kết luận LSTM học chu kỳ tuần nếu không có diagnostic evidence phù hợp hoặc feature được phê duyệt.

Đây là **các biện pháp kỹ thuật được đề xuất**, cần đối chiếu với quy tắc sẵn có trong kho mã nguồn để tránh trùng lặp hoặc mâu thuẫn với quy định cấp cao hơn.

## 6. Phạm vi và nội dung không thực hiện

**Trong phạm vi chính:** Xác minh tính khả thi của dữ liệu, khám phá và chuẩn bị dữ liệu, tạo cửa sổ/đặc trưng không rò rỉ, ba nhóm mô hình trong đề, xác thực theo thời gian, đánh giá dự báo tiến dần theo thời gian, so sánh mô hình và lập báo cáo có bằng chứng.

**Ngoài phạm vi chính:** Dự báo giao thông bằng METR-LA / PEMS-BAY; triển khai hệ thống vận hành thực tế, xây dựng ứng dụng web, tự động thu thập dữ liệu trực tiếp và dự báo nhiều bước khi đề không yêu cầu. Mọi mở rộng trong tương lai cần có quyết định riêng.

## 7. Kiến trúc phase đã được Human thống nhất

1. **Phase 0 — Problem Definition:** Khóa mục tiêu, forecasting contract dự kiến, scope, constraints và acceptance criteria; không xử lý dữ liệu.
2. **Phase 1 — Data Preparation:** Kiểm chứng hai raw CSV, tạo weather proxy, join và tạo canonical hourly dataset; bảo toàn missing target.
3. **Phase 2 — Temporal Split và Validation Design:** Chia 70/15/15 theo thời gian, khóa test set, forecast origins và validation contract.
4. **Phase 3 — Exploratory Data Analysis:** Chỉ phân tích training set; không quan sát validation/test để ra quyết định EDA.
5. **Phase 4 — Preprocessing và Scaling:** Xử lý missing/anomaly theo policy được duyệt; fit transformations chỉ trên train.
6. **Phase 5 — Feature Engineering và Supervised Conversion:** Tạo window, lag/rolling features và model-ready inputs với cùng forecast origins.
7. **Phase 6 — Simple Baselines và VAR:** Đánh giá Naive/Seasonal Naive, ADF/differencing, lag selection và VAR diagnostics.
8. **Phase 7 — XGBoost:** Tuning và early stopping trên validation; khóa cấu hình trước test.
9. **Phase 8 — LSTM:** Huấn luyện kiến trúc theo đề, kiểm tra overfitting và khóa cấu hình trước test.
10. **Phase 9 — Walk-forward Evaluation và Error Analysis:** Mở test sau model lock, đánh giá công bằng và phân tích lỗi; không tuning lại.
11. **Phase 10 — End-to-End Notebook và Final Report:** Tổng hợp approved artifacts, trả lời câu hỏi đề bài và kết luận; không triển khai lại pipeline.

Mỗi phase phải đi qua chu trình thiết kế → Human approval → triển khai → validation → Human review trước khi chuyển phase tiếp theo.

## 8. Các quyết định dữ liệu phải giải quyết trong Phase 1 hoặc phase sở hữu liên quan

1. Archive được tải từ version nào, vào ngày nào, có checksum, license và provenance ra sao?
2. Cách deduplicate weather rows và chuẩn hóa `city_name` nào bảo toàn ba biến bắt buộc?
3. Nên dùng unweighted mean, weighted mean hay một đại diện thành phố để tạo national weather proxy?
4. Đơn vị của target/weather, temperature conversion và timezone/DST contract được xác định thế nào?
5. Phase 4 xử lý 36 giá trị `total load actual` bị thiếu bằng chính sách causal nào sau khi Phase 3 cung cấp training-only evidence?
6. Phase 2 định nghĩa thời điểm bắt đầu dự báo, split boundaries và forecast origins ra sao?
7. Phase 9 dùng giá trị thực vừa quan sát, dự báo trước đó hay quy trình khác trong walk-forward; có refit/retrain không?
8. Phase 9 xử lý MAPE thế nào khi điện năng thực tế bằng 0?
9. Phase 6 chọn VAR lag trong miền `1…24` hay được phép vượt ngoài cửa sổ 24 giờ?
10. Phase 5 cho phép context window đi qua split boundary thế nào để giữ cùng forecast origins giữa các mô hình?
11. Phase 10 cần bằng chứng nào để trả lời sáu câu hỏi phân tích, đặc biệt là weather importance, VAR failure và weekly cycle của LSTM?

## 9. Điều kiện sẵn sàng để thiết kế Phase 0

`PROJECT_OVERVIEW.md` chỉ được đánh dấu **ĐƯỢC DUYỆT ĐỂ THIẾT KẾ PHASE 0** sau khi Human xem xét bản cập nhật này. Phase 0 chỉ tạo Problem Definition; không tải, xử lý hoặc kiểm chứng dữ liệu. Dataset Spain đã được Human chọn, nhưng data contract kiểm chứng, weather aggregation, preprocessing và evaluation protocol phải được giải quyết tại phase sở hữu tương ứng.

**Nguồn tham chiếu:** Tệp `practice 4.pdf` do Human cung cấp; governance files thực tế trong repository; trang UCI; Kaggle dataset page; preliminary read-only inspection của hai CSV công khai. Formal Phase 1 data verification, repository ingestion và reproducible execution evidence chưa được thực hiện.
