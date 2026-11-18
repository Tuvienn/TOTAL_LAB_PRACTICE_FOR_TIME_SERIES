# Current Status — Practice 4

Trạng thái dự án: `IN_PROGRESS` — Phase 3 specification APPROVED; Stage D01 `IN_PROGRESS`.

## Đã hoàn thành ở mức lập kế hoạch

- Đã đọc đề bài Practice 4 và các quy tắc repository áp dụng.
- Human đã chọn **Hourly energy demand, generation and weather** làm dataset chính.
- Human đã thống nhất kiến trúc tổng quan gồm Phase 0–10:
  - Phase 0: Problem Definition;
  - Phase 1: Data Preparation;
  - Phase 2: Temporal Split và Validation Design;
  - Phase 3: EDA chỉ trên training set;
  - Phase 4–9: preprocessing, feature engineering, modeling và final evaluation;
  - Phase 10: End-to-End Notebook và Final Report.
- Đã thực hiện preliminary read-only inspection đối với archive công khai:
  - `energy_dataset.csv`: 35.064 dòng, 29 cột, hourly 2015–2018;
  - `weather_features.csv`: 178.396 dòng, 17 cột, weather của năm thành phố;
  - `total load actual` có 36 giá trị thiếu;
  - ba trường `temp`, `humidity`, `wind_speed` không thiếu;
  - có các city-hour bị lặp do nhiều weather descriptions, nhưng ba trường weather
    bắt buộc giống nhau trong các bản lặp đã kiểm tra.
- Roadmap và project overview vẫn là draft. Phase 0 specification/before-process
  plan đã được Human duyệt ngày 2026-11-17; xem `docs/phase_details/phase_00.md`.
- Human đóng gate A01 ngày 2026-11-17 qua tin nhắn `Close Gate A01 & Execute
  Phase 0 — Stage A02`; chi tiết tại `docs/phase_details/phase_00.md`.
- Human đóng gate A02 / Phase 0 ngày 2026-11-17 qua tin nhắn `Close Phase 0
  (Gate A02) & Draft Phase 1 Specification`; đã soạn Phase 1 specification draft.
- Human duyệt Phase 1 specification và yêu cầu B01 dùng system Python 3.12,
  xác nhận metadata nguồn và core dependencies trong yêu cầu ngày 2026-11-18.
- B01 run `20261118_system312_01` đã tạo audit, source manifest, run manifest và
  execution log; targeted tests đạt 5/5. Human duyệt B01 và policy B02 ngày
  2026-11-18 theo yêu cầu `Close Gate B01 & Execute Stage B02`.
- Human duyệt B02 run `20261118_system312_b02_01`, canonical dataset, data
  contract và đóng Phase 1 ngày 2026-11-18 theo yêu cầu `Close Phase 1 (Gate B02)
  & Draft Phase 2 Specification`. Phase 2 specification và before-process plan được
  Human APPROVED ngày 2026-11-18 qua Director review; chỉ C01 được phép thực thi.
- Approval record và contract header được cập nhật sau B02 run: hash hiện tại
  của hai tài liệu khác hash tại thời điểm run trong B02 manifest; manifest được
  giữ nguyên như evidence lịch sử. Raw và canonical data không đổi bởi việc này.
- C01 run `20261118_system312_c01_01` và split manifest được Human APPROVED
  2026-11-18 qua Director review; C02 được phép thực thi.
- C02 run `20261118_system312_c02_01`, evaluation contract và Phase 2 được
  Human APPROVED / COMPLETED ngày 2026-11-18 qua Director review; RV2 đóng.
  Phase 3 specification và before-process plan được Human APPROVED ngày
  2026-11-18 qua Director review; D01 được phép thực thi.
- Header Phase 2 và evaluation contract cập nhật sau C02 approval; hash hiện tại
  khác C02 run manifest lịch sử, manifest được giữ nguyên để bảo toàn provenance.
- D01: Python 3.12 import được matplotlib 3.11.2 với Agg, statsmodels 0.14.6,
  tzdata 2026.5 và pandas 2.3.3; đã ghi versions và khóa config trước EDA.
  Evidence B01/B02 xác nhận một raw 133 m/s record nhưng không ghi timestamp;
  Human cho phép tiếp tục ngày 2026-11-18 qua Director review; train membership
  của raw record được ghi là chưa xác minh, không mở held-out rows để tìm.
- D01 run `20261118_system312_d01_01` đã tạo train-only findings và staged figures;
  D01 acceptance và D02 policy proposals **PENDING HUMAN REVIEW**. Raw 133 m/s
  train membership chưa xác minh; không promote figures.

## Chưa thực hiện

- Human đã đặt hai CSV trong `datasets/raw/`; đã kiểm tra read-only và ghi hash,
  counts cùng limitations trong `docs/results/data_audit.md`.
- Human xác nhận source, version 1, CC0, units và time semantics; Kaggle page/API
  chưa được xác minh độc lập trong môi trường này. Archive hash chưa có.
- Data contract Phase 1 và Phase 2 specification đã được Human chấp nhận.
- D01 acceptance và D02 policy còn PENDING HUMAN REVIEW.
- Chưa khóa missing-value treatment hoặc scaling; walk-forward protocol đã duyệt,
  nhưng D02 context policy và model-specific budgets vẫn chờ approval riêng.
- Editable install vào system Python 3.12 đã chạy; không tạo virtualenv hoặc
  kiểm clean-environment reproduction. B01 đã được Human chấp nhận.
- Đã có B01/B02 pipeline và tests; notebook template có 12 Markdown cells, chưa
  có final executable notebook hoặc model training.

Kiểm tra ngày 2026-11-17 không thấy `LD2011_2014.txt` trong `datasets/raw/`;
không suy diễn nguyên nhân. UCI không phải dataset chính đã chọn.
