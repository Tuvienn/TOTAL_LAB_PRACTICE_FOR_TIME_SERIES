# Practice 4

Trạng thái hiện tại: `PLANNING`.

Đề bài và quy tắc repository đã được rà soát. Human đã chọn bộ dữ liệu
**Hourly energy demand, generation and weather** làm dataset chính. Kiến trúc
Phase 0–10 đã được Human thống nhất ở mức tổng quan:

- Phase 0 chỉ định nghĩa bài toán.
- Phase 1 chuẩn bị và tích hợp hai raw CSV thành canonical hourly dataset.
- Phase 2 khóa temporal split và validation design.
- Phase 3 thực hiện EDA chỉ trên training set.
- Phase 4–9 xử lý dữ liệu, tạo đặc trưng, xây mô hình và đánh giá cuối cùng.
- Phase 10 tổng hợp approved artifacts thành end-to-end notebook và final report.

Data contract, weather aggregation, missing-value treatment và evaluation protocol
vẫn phải đi qua thiết kế, kiểm chứng và Human approval tại phase sở hữu tương ứng.

Tài liệu điều phối:

- `docs/plans/PROJECT_OVERVIEW.md`: phạm vi, yêu cầu và trạng thái quyết định.
- `docs/plans/plan_overview.md`: bản đồ phase và approval gates.
- `docs/status/current_status.md`: trạng thái thực tế hiện tại.
