# EXERCISE 03 — KẾ HOẠCH ĐỒNG BỘ NOTEBOOK

## 1. Thông tin kế hoạch

```text
Practice: Practice_1
Exercise: 03 — Time Series Decomposition
Notebook chính: notebooks/practice_1_present.ipynb
Phạm vi cell: 28–31
Mục tiêu: sửa tối thiểu, giữ nguyên các phần E3 đang đúng
Trạng thái kế hoạch: ĐÃ_TRIỂN_KHAI_VÀ_XÁC_MINH
Được phép triển khai: CÓ
```

Tài liệu phân tích:

```text
docs/error_analysis/exercise_03_notebook_alignment_issue.md
```

Kế hoạch này không tự cấp quyền implementation. Chỉ được bắt đầu sửa sau khi Human
phê duyệt rõ ràng.

## 2. Mục tiêu sửa

- dùng validated AirPassengers series từ E1;
- kiểm tra đầy đủ điều kiện natural-log transform;
- phân rã `log(y)` bằng STL với `period=12`, `robust=True`;
- giữ cách trình bày bốn component hiện có nhưng ghi đúng log scale;
- đánh giá residual bằng time plot, ACF 40 lag và Ljung–Box lag 12;
- trả lời đủ mười câu hỏi diễn giải bằng actual results;
- tạo figures, CSV, tests và execution evidence;
- giữ nguyên E1–E2, E4–E5 và raw dataset.

## 3. Nguyên tắc sửa

- không viết lại những phần E3 đang đúng nếu chỉ cần tái sử dụng;
- không thay đổi các scientific parameters đã khóa;
- không đặt reusable analytical hoặc plotting logic làm owner trong notebook;
- không hard-code kết luận thống kê;
- không dùng Ljung–Box như bằng chứng duy nhất;
- không tự động xử lý dữ liệu không dương hoặc missing;
- không thêm cell ngoài phạm vi nếu có thể tái sử dụng bốn cell 28–31;
- không làm thay đổi source/type của cell 0–27 và cell 32 trở đi.

## 4. File được phép tạo hoặc thay đổi sau phê duyệt

```text
notebooks/practice_1_present.ipynb, chỉ cell 28–31 và output tương ứng
src/practice_1/analysis/decomposition.py
src/practice_1/analysis/__init__.py
src/practice_1/visualization/diagnostic_plots.py
src/practice_1/visualization/__init__.py
tests/test_decomposition.py
outputs/figures/07_log_transformed_series.png
outputs/figures/08_stl_decomposition.png
outputs/figures/09_decomposition_residual.png
outputs/results/decomposition_components.csv
outputs/results/residual_diagnostics.csv
docs/logs/exercise_03_execution.md
docs/status/current_status.md
docs/exercise_details/exercise_03_decomposition.md, chỉ trạng thái
docs/plans/exercise_03_before_process.md, chỉ approval/status
docs/error_analysis/exercise_03_notebook_alignment_issue.md, chỉ trạng thái/kết quả
docs/fix_plans/exercise_03_notebook_alignment_fix_plan.md, chỉ approval/kết quả
```

Nếu tên module cần thay đổi để tránh duplicate owner đã tồn tại, phải ghi rõ lý do
trong execution log nhưng không mở rộng phạm vi chức năng.

## 5. File và nội dung không được thay đổi

```text
cell 0–27 của Exercise 1–2
cell 32 trở đi của Exercise 4–5
datasets/raw/
validated Exercise 1 outputs
validated Exercise 2 outputs
config/practice_1.json
pyproject.toml
working_rule.md
approved rule documents
Exercise 4–5 specification và before-process plan
```

Không thêm dependency mới. `numpy`, `pandas`, `matplotlib` và `statsmodels` hiện có
đủ để thực hiện kế hoạch.

## 6. Bản đồ giữ và sửa theo cell

| Cell | Quyết định | Nội dung sau khi được duyệt |
|---:|---|---|
| 28 | Giữ STL và bố cục, sửa input/owner | Thêm heading E3, kiểm tra input, tạo working log series, gọi reusable decomposition, tạo `07` và `08` |
| 29 | Giữ các nhận định đúng, chuyển thành evidence summary | Hiển thị component statistics và các bằng chứng trend, seasonality, amplitude |
| 30 | Giữ ACF 40 lag và Ljung–Box, sửa owner/output | Tạo residual time plot + ACF, lưu `09`, lưu component/diagnostic CSV |
| 31 | Giữ quy tắc p-value, mở rộng diễn giải | Trả lời đủ 10 câu hỏi bằng actual output và nêu Ljung–Box chỉ là supplementary evidence |

Số cell E3 dự kiến vẫn là bốn. Nếu giới hạn kỹ thuật của notebook buộc phải thêm
cell, phải dừng và xin Human duyệt thay đổi ranh giới trước.

## 7. Thiết kế API dự kiến

### 7.1. Analysis owner

Tạo `src/practice_1/analysis/decomposition.py` với các trách nhiệm tập trung:

```text
validate_decomposition_series
log_transform_series
compute_stl_decomposition
compute_residual_diagnostics
```

API có thể được gộp hợp lý nếu giữ rõ các contract sau:

- input là `pandas.Series` có `DatetimeIndex` tháng;
- từ chối Series rỗng, missing, non-finite, không dương hoặc sai chronology;
- không sửa input;
- log transform giữ nguyên index và tên có ý nghĩa;
- STL luôn dùng `period=12`, `robust=True` theo cấu hình được truyền rõ;
- bảng component có đúng 144 dòng và năm cột:

```text
timestamp
observed_log
trend_log
seasonal_log
residual_log
```

- kiểm tra identity trong tolerance:

```text
observed_log ≈ trend_log + seasonal_log + residual_log
```

- residual diagnostics sử dụng ACF đến lag 40, confidence level 95% và
  Ljung–Box lag 12;
- Ljung–Box output chứa lag, statistic và p-value thực tế.

Tái sử dụng `compute_acf_table`; không tạo thuật toán ACF thứ hai.

### 7.2. Visualization owner

Bổ sung các hàm tập trung trong `src/practice_1/visualization/diagnostic_plots.py`:

```text
plot_log_transformed_series
plot_stl_decomposition
plot_decomposition_residual_diagnostics
```

Yêu cầu chung:

- nhận dữ liệu đã tính thay vì tự chạy decomposition;
- dùng `_save_figure` hiện có;
- title và axis label ghi rõ natural-log scale;
- residual diagnostic figure có hai panel: time plot và ACF 40 lag;
- confidence interval 95% phải được hiển thị;
- không đổi hành vi các hàm E1/E2 hiện có.

## 8. Các bước triển khai

### Bước 1 — Ghi nhận baseline

Trước khi sửa, xác minh lại:

```text
notebook checksum
source/type checksum cell 0–27
source/type checksum cell 28–31
source/type checksum cell 32 trở đi
raw dataset checksum
validated E1/E2 output checksum
```

### Bước 2 — Xác minh upstream dependencies

Xác nhận:

- `air_passengers_frame` và `series` từ E1 vẫn tồn tại sau khi chạy sạch;
- E1 đã xác minh 144 tháng, chronology, frequency và missing values;
- E2 evidence có thể được dùng làm conceptual comparison;
- không cần đọc lại raw CSV trực tiếp trong E3.

### Bước 3 — Tạo reusable analysis logic

Tạo module decomposition theo contract ở Mục 7.1. Mọi validation failure phải
raise lỗi rõ ràng; không tự cộng hằng số, nội suy hoặc đổi decomposition method.

### Bước 4 — Bổ sung reusable plotting logic

Tạo ba hàm plot theo Mục 7.2, không làm thay đổi output E1/E2.

### Bước 5 — Thêm kiểm thử tập trung

Tạo `tests/test_decomposition.py` để kiểm tra tối thiểu:

- log transform giữ nguyên index và không sửa input;
- từ chối zero, negative, missing và non-finite values;
- output component có đúng schema, row count và index alignment;
- reconstruction identity đạt tolerance;
- `period=12` và `robust=True` được sử dụng đúng;
- residual ACF có lag 0–40 và confidence interval;
- Ljung–Box output chỉ rõ lag 12, statistic và p-value hữu hạn;
- baseline cốt lõi khớp kết quả được tính lại trong tolerance.

### Bước 6 — Đồng bộ cell 28–31

- Cell 28: thêm heading/mục tiêu E3; import public package API; kiểm tra precondition;
  tạo working log series; lưu và hiển thị `07_log_transformed_series.png`; chạy STL;
  lưu và hiển thị `08_stl_decomposition.png`.
- Cell 29: hiển thị bảng tóm tắt component và evidence cần dùng cho diễn giải;
  không viết kết luận trước actual output.
- Cell 30: lưu `decomposition_components.csv`; tính residual ACF/Ljung–Box;
  lưu `residual_diagnostics.csv`; tạo và hiển thị
  `09_decomposition_residual.png`.
- Cell 31: tạo Markdown động trả lời đủ mười câu hỏi từ actual results, ghi rõ
  component ở log scale và residual chưa chắc là white noise.

### Bước 7 — Thực thi bằng kernel sạch

Khởi động kernel `time-series-practice-1` và chạy tuần tự cell 0–31. Không thực thi
cell 32 trở đi trong validation E3.

### Bước 8 — Kiểm tra trực quan và machine-readable outputs

Kiểm tra thực tế:

```text
07 không bị cắt, có nhãn log scale
08 đủ bốn panel và dùng chung timeline
09 đủ residual time plot và ACF 0–40
confidence interval hiển thị đúng
CSV component có 144 timestamp đúng thứ tự
CSV diagnostic có actual lag 12/statistic/p-value
```

### Bước 9 — Regression validation

Chạy compile và toàn bộ tests E1–E3. Đối chiếu checksum để chứng minh:

```text
raw dataset không đổi
validated E1/E2 outputs không đổi
source/type cell 0–27 không đổi
source/type cell 32 trở đi không đổi
không thêm dependency
```

### Bước 10 — Cập nhật bằng chứng

Chỉ sau khi tất cả validation đạt:

- tạo `docs/logs/exercise_03_execution.md`;
- cập nhật trạng thái E3 trong specification, before-process plan và current status;
- ghi checksum, test result, notebook execution result và actual scientific findings;
- giữ E4 ở trạng thái chưa được phép triển khai.

## 9. Baseline chẩn đoán dự kiến

Baseline chỉ đọc để phát hiện regression:

```text
rows: 144
all values positive: True
log-STL residual mean: khoảng 0.000290
log-STL residual sample standard deviation: khoảng 0.026527
residual ACF lag 1: khoảng 0.374728
residual ACF lag 12: khoảng -0.133553
Ljung–Box lag-12 statistic: khoảng 41.709381
Ljung–Box lag-12 p-value: khoảng 0.000037
significant residual ACF lags trong 1–40: 1 và 2
largest absolute log residual timestamp: 1953-04
```

Các giá trị này không được chép cứng làm output. Test phải dùng tolerance phù hợp và
notebook phải lấy kết quả từ actual execution.

## 10. Validation bắt buộc

```text
JSON notebook hợp lệ
compileall src và tests đạt
toàn bộ tests E1–E3 đạt
cell 0–31 chạy sạch, execution count tuần tự, không có error output
input log transform hợp lệ
STL period = 12
STL robust = True
component reconstruction đạt tolerance
residual ACF đủ lag 0–40 với confidence interval 95%
Ljung–Box lag 12 được lưu và diễn giải như supplementary evidence
ba figure tồn tại, đọc được và đã inspect
hai CSV tồn tại và khớp notebook
mười câu hỏi interpretation được trả lời từ actual results
raw checksum không đổi
E1/E2 source và outputs không đổi
E4/E5 source không đổi
```

## 11. Rủi ro và kiểm soát

### Kết quả khác notebook hiện tại

Chuyển từ original scale sang natural-log scale bắt buộc làm thay đổi component,
residual và diagnostic. Không cố duy trì p-value hoặc outlier timestamp cũ.

### Diễn giải sai scale

Mọi component và residual phải có hậu tố/nhãn `_log` hoặc ghi rõ natural-log scale.
Không gọi residual log là số nghìn hành khách.

### Kết luận white noise quá mức

Kết hợp time plot, ACF và Ljung–Box. Nếu p-value nhỏ hoặc còn significant ACF lag,
phải nói residual chưa giống white noise hoàn toàn.

### Regression E1/E2

Chỉ bổ sung public exports và hàm mới. Không đổi chữ ký hoặc hành vi hàm E1/E2;
chạy lại toàn bộ tests và đối chiếu output checksum.

### Làm thay đổi E4/E5

Giữ đúng bốn cell E3, không sửa cell 32 trở đi và đối chiếu source/type checksum.

### Downstream E4 dùng residual

`decomposition_components.csv` phải có schema, timestamp và log scale rõ ràng để E4
không dùng nhầm residual cũ trên original scale.

## 12. Điều kiện dừng

Phải dừng và báo Human nếu:

```text
phát hiện giá trị không dương, missing hoặc non-finite
frequency/index không khớp validated E1 series
log transform làm thay đổi index hoặc raw data
STL computation fail
component reconstruction không đạt tolerance
cần thay đổi period, robust hoặc decomposition method
cần dependency mới
validated E1/E2 output phải bị ghi đè
cell E4/E5 buộc phải sửa
test E1/E2 bị regression
notebook không chạy sạch đến hết cell 31
```

Không tự chuyển sang classical decomposition, không bỏ log transform và không tự sửa
upstream data.

## 13. Tiêu chí hoàn thành

```text
phần tốt của E3 được giữ theo bản đồ cell
validated AirPassengers series được dùng
log-transform preconditions được kiểm tra
natural-log working series được tạo mà không sửa raw data
STL dùng period=12 và robust=True
đủ Observed, Trend, Seasonal, Residual trên log scale
ba figure và hai CSV được tạo, inspect và đối chiếu
residual được đánh giá bằng plot, ACF và Ljung–Box lag 12
mười câu hỏi được trả lời bằng actual results
tests E1–E3 đạt
cell 0–31 chạy sạch
E1/E2 và E4/E5 không đổi
execution log và current status được cập nhật
```

## 14. Phê duyệt của Human

```text
Human đã xem error analysis: CÓ
Human đã xem fix plan: CÓ
Human phê duyệt phạm vi: CÓ
Cho phép triển khai E3: CÓ
Ngày phê duyệt: 2026-10-12
```

Human đã phê duyệt rõ ràng trong hội thoại ngày 2026-10-12. Agent được phép triển
khai trong đúng phạm vi của kế hoạch này.

## 15. Kết quả triển khai

```text
Triển khai hoàn tất: CÓ
Validation hoàn tất: CÓ
Ngày hoàn tất: 2026-10-12
Notebook chính: notebooks/practice_1_present.ipynb
Nhật ký: docs/logs/exercise_03_execution.md
```

Toàn bộ tiêu chí hoàn thành tại Mục 13 đã đạt. E1–E2 và E4–E5 được bảo vệ bằng
checksum; raw dataset không thay đổi.

