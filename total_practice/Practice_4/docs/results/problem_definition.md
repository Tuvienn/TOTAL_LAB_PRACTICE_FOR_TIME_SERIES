# Practice 4 — Problem Definition

Trạng thái: **A02 — CHỜ HUMAN REVIEW**, ngày 2026-11-17. Tài liệu này đề xuất
định nghĩa bài toán; không thay thế data contract, evaluation contract hoặc
approval của phase sở hữu. Human đã đóng A01 và yêu cầu thực hiện A02 bằng tin
nhắn `Close Gate A01 & Execute Phase 0 — Stage A02` trong cuộc hội thoại hiện tại.

Nguồn: [đề bài, trang 1–3](../../../../references/practice%204.pdf),
[roadmap và R01–R09](../plans/plan_overview.md),
[project overview](../plans/PROJECT_OVERVIEW.md),
[Phase 0 plan và approval](../phase_details/phase_00.md),
[file map](../plans/file_map.csv) và
[Time Series rules](../../../../.agents/rules/TIME_SERIES_RULES.md).

## 1. 5W1H

| Câu hỏi | Định nghĩa |
|---|---|
| What | Bài thực hành dự báo chuỗi thời gian đa biến: so sánh VAR, XGBoost và LSTM khi dự báo load một bước tiếp theo. |
| Why | Khảo sát dự báo điện năng và thông tin thời tiết, so sánh nhóm statistical, ML, DL và trả lời sáu câu hỏi của đề bằng evidence. |
| Who | Người học Practice 4 thực hiện; Human review các quyết định và kết quả. Đây là bài lab, chưa xác định người dùng vận hành thực tế. |
| Where | Nguồn chính được Human chọn là Spain energy consumption và weather; artifacts theo ownership của Practice 4. Source version và license chờ xác minh. |
| When | Đề yêu cầu lịch sử 24 giờ và dự báo bước tiếp theo. Theo hourly setup dự kiến, forecast origin là cuối giờ `t`, target ở `t+1`; availability thực tế cần kiểm chứng. |
| How | Theo trình tự data audit, split theo thời gian, train-only EDA, preprocessing, features, baselines, ba model, walk-forward và báo cáo; từng phase có approval và validation riêng. |

## 2. Yêu cầu và quyết định đã xác nhận

- **Theo đề:** bốn biến load, temperature, humidity, wind speed; lịch sử 24 giờ;
  dự báo load bước kế tiếp; VAR, XGBoost, LSTM; RMSE, MAE, MAPE; chronological
  split 70/15/15 không shuffle. StandardScaler, ADF/differencing/AIC hoặc BIC,
  feature engineering và kiến trúc LSTM theo R01–R08 trong roadmap.
- **Theo đề:** kiểm tra missing/outliers, seasonality ngày/tuần và biểu đồ quan
  hệ; trả lời sáu câu hỏi về weather, VAR, XGBoost, LSTM và ML/DL (R02, R09).
- **Human chọn:** thay nguồn UCI nêu trong đề bằng Spain energy/weather làm
  nguồn chính; A01 đã chấp nhận scope, source, R01–R09, map và architecture.
  Không suy ra rằng dữ liệu thực tế hay các downstream contracts đã được duyệt.
- **Repository rules:** bảo toàn raw, ngăn leakage, giữ chronology, có baseline,
  evidence thực tế và Human review tại các gate. Không dùng test để chọn model.

## 3. Input, output và forecast origin dự kiến

| Thành phần | Đề xuất hoặc trạng thái kiểm chứng |
|---|---|
| Nguồn input | Hai CSV energy và city weather thuộc nguồn Spain đã chọn; tên cột `total load actual`, `temp`, `humidity`, `wind_speed` chỉ mới có historical preliminary inspection, cần B01 xác minh. |
| Granularity | Theo giờ là setup dự kiến; timezone, DST, tần suất, đơn vị và schema cần kiểm chứng trước data contract B02. |
| Observation | `X(t) = [load(t), temperature(t), humidity(t), wind_speed(t)]`; weather proxy đại diện national load chưa khóa. |
| Origin và horizon | **Đề xuất:** tại cuối giờ `t`, sau khi có các giá trị đến `t`, dự báo `load(t+1)`. Availability cuối giờ là giả định lab cần được đánh giá, không chứng minh khả dụng production. |
| Window | **Đề xuất:** `[X(t-23), …, X(t)]` gồm 24 hourly observations; exact alignment và split membership chờ C/E. XGBoost trend `load(t)-load(t-24)` cần thêm observation: khác context LSTM 24 bước, phải công bố. |
| Output | Forecast load một bước trên thang đo/đơn vị gốc đã xác minh; so sánh forecast và metrics cùng origins/truth hợp lệ; report evidence và limitations. Không giả định metric hay model thắng trước khi chạy. |

Mean weather của năm thành phố, fixed-weight observed-history walk-forward,
quy tắc common mask, chọn primary metric và MAPE khi target bằng zero là các
**đề xuất hoặc quyết định còn mở**, không phải protocol đã khóa. Không dùng
future observed weather làm input tại origin. Cách cập nhật history/refit cần
C02 phê duyệt; đề bài không quy định đầy đủ.

## 4. Scope và tiêu chí thành công

Trong project scope: xác minh provenance và quality; tạo derived hourly data theo
policy được duyệt; chronological split và train-only EDA; preprocessing và
feature engineering không leakage; persistence và seasonal-naive baselines;
VAR, XGBoost, LSTM; walk-forward, error analysis và report truy vết artifacts.
Phase 0 chỉ xác định bài toán và không thực hiện các bước dữ liệu hoặc model.

Ngoài scope: bài traffic METR-LA/PEMS-BAY, multi-step forecasting, web hoặc
deployment, production service và tự động thu thập dữ liệu trực tiếp. Thay đổi
scope hoặc source cần Human quyết định riêng.

Thành công của **A02** là Human chấp nhận tài liệu này sau khi 5W1H, I/O,
phân loại quyết định, risks và các gate được review. Thành công của **project**
là thực hiện đầy đủ yêu cầu theo contracts đã duyệt, nguyên vẹn raw data và
chronology, các mô hình so sánh trên protocol hợp lệ, metrics và kết luận có
thể truy vết đến artifacts/run; nêu rõ exclusions và limitations. Không bắt
buộc model phức tạp thắng baseline hoặc LSTM chứng minh được chu kỳ tuần.

## 5. Risks và decision register

| ID / owner | Cần evidence hoặc quyết định trước gate | Risk nếu bỏ qua |
|---|---|---|
| Q01 / A01–A02 | Scope/source/map được A01 chấp nhận; problem definition này chờ A02 review. | Lẫn acceptance với approval contracts downstream. |
| Q02 / B01 | Archive version, license, provenance, schema, units, timezone và coverage từ raw thực. | Nguồn không thể tái lập hoặc sai diễn giải. |
| Q03 / B02 | Duplicate, city proxy, DST/join và data contract; Human duyệt sau audit. | Bias proxy, mất quan sát hoặc sai alignment. |
| Q04 / C01–C02 | Split rounding, boundary context, origins và eligibility; synthetic boundary checks. | Leakage hoặc các model dùng sample không tương đương. |
| Q05 / C02 | Information update/refit, metrics, MAPE zero, ties, budgets và test gate. | Chọn protocol sau khi thấy kết quả; so sánh thiếu công bằng. |
| Q06 / D02 | Training-only EDA và policy missing/anomaly/max-gap/contiguous VAR, Human duyệt. | Điền truth giả, dùng future data hoặc phá tính hourly. |
| Q07 / E01 | Window, extra trend context, order, ddof và availability; hand-worked fixture. | Off-by-one, sai information set. |
| Q08 / F02 | ADF options, differencing, lag criterion và finite bounds sau train diagnostics. | VAR không phù hợp hoặc không tái lập. |
| Q09 / G01–G02 | Backend compatibility, candidate budgets, seeds và hyperparameters trước fit. | Tốn tài nguyên, seed cherry-picking, không tái lập. |
| Q10 / H01 | Model/preprocessor/config locks, common eligibility và Human test-opening approval. | Test leakage hoặc mixed artifact versions. |

Weather association/feature importance không chứng minh causality; 24 giờ không
trực tiếp bao gồm lag tuần; chưa có bằng chứng để xác nhận weekly learning.
Preliminary inspection cũ không thay thế audit có provenance và không được coi
là kết quả A02. RV1–RV3 trong [plan review](../plans/plan_review.md) vẫn mở tới
phase owners được phân công.

## 6. Review và gate

Human review mục tiêu, 5W1H, provisional I/O/origin, scope, success criteria,
risks và decision register trước khi chấp nhận A02 / Phase 0. Sau đó Phase 1
cần specification, before-process plan và approval riêng; tài liệu này không
cho phép tải hay xử lý dữ liệu hoặc triển khai Phase 1.
