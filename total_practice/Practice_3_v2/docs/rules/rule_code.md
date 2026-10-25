# QUY TẮC CODE — PRACTICE 3 V2

## 1. Ngôn ngữ

- Source code, identifier, exception và test name dùng tiếng Anh.
- Tài liệu Markdown và nội dung giải thích cho Human dùng tiếng Việt; thuật ngữ chuyên ngành có thể giữ tiếng Anh.

## 2. Source ownership

- Logic được tái sử dụng hoặc ảnh hưởng correctness phải có một owner trong `src/practice_3_v2/`.
- Notebook không được chứa bản sao của data repair, split, feature engineering, training, forecasting hoặc metric logic.
- Không import package legacy `practice_3` khi chạy official v2 pipeline.

## 3. Đường dẫn và configuration

- Không hard-code absolute path theo máy cá nhân.
- Đường dẫn phải được resolve từ project root hoặc configuration.
- Tham số ảnh hưởng kết quả phải được ghi trong configuration hoặc official artifact.

## 4. Time-series safety

- Không shuffle dữ liệu time series.
- Không dùng future target để tạo feature hiện tại.
- Rolling feature phải loại target hiện tại khi dự báo target đó.
- Không fit transformation trên validation hoặc holdout.
- Mọi split phải kiểm tra chronology và overlap.

## 5. Kiểm thử

Mỗi phase phải có focused tests tương ứng với rủi ro của phase. Trước khi bàn giao phase phải chạy focused tests, full regression suite hiện có và `git diff --check`.

## 6. Error handling

Lỗi implementation có ảnh hưởng scientific validity phải dừng phase, ghi error analysis và xin Human duyệt fix plan trước khi sửa. Không xem metric thấp là implementation bug.
