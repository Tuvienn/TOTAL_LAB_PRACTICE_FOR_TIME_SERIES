# Practice 4

Trạng thái kỹ thuật: `COMPLETED` — Phase 0–10 artifacts và notebook đã được tạo; xem `docs/status/current_status.md` để biết run IDs, bằng chứng và giới hạn.

## Lịch sử kế hoạch

Các ghi chú và phase draft bên dưới phản ánh trạng thái tại thời điểm chúng được tạo; trạng thái bàn giao hiện tại ở trên và trong `docs/status/current_status.md`.

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
- `docs/plans/file_map.csv`: inventory và ownership của artifacts.
- `docs/phase_details/phase_00.md`: specification và plan Phase 0 đã duyệt.
- `docs/logs/A01_20261117_document_review.md`: evidence và giới hạn của A01.
- `docs/results/problem_definition.md`: problem definition A02 được Human chấp nhận.
- `docs/logs/A02_20261117_document_review.md`: evidence và giới hạn của A02.
- `docs/phase_details/phase_01.md`: Phase 1 specification và plan đã duyệt.
- `docs/plans/b01_core_environment.md`: đề xuất environment B01 đang chuẩn bị.
- `docs/results/data_audit.md`: B01 audit và policy B02 đề xuất.
- `docs/results/data_contract.md`: B02 canonical contract đã được Human chấp nhận.
- `docs/phase_details/phase_02.md`: Phase 2 specification draft chờ Human review.
- `docs/status/current_status.md`: trạng thái thực tế hiện tại.


## Bàn giao cuối cùng

- [Báo cáo cuối](docs/results/final_report.md)
- [Notebook end-to-end](notebooks/practice_4_end_to_end.ipynb)
- [So sánh và phân tích lỗi test](docs/results/model_comparison.md)
- [Hướng dẫn tái lập offline](docs/logs/reproduction.md)
- [Trạng thái và run evidence](docs/status/current_status.md)
