# Phase 0 — Specification và before-process plan

Trạng thái: **COMPLETED — Human đã đóng A01 và A02**.
Ngày chuẩn bị và duyệt: 2026-11-17. Người duyệt: Human; tham chiếu:
tin nhắn `APPROVED` ngay sau đề nghị duyệt Phase 0 specification/before-process
plan trong cuộc hội thoại hiện tại. Approval này không tự phê duyệt roadmap,
kiến trúc hay việc chuyển sang A02.

## Mục tiêu và nguồn

Phase 0 xác định phạm vi bài toán dự báo điện năng đa biến và ownership;
không xử lý dữ liệu. Nguồn là [đề Practice 4](../../../../references/practice%204.pdf),
[roadmap](../plans/plan_overview.md), [file map](../plans/file_map.csv),
[project overview](../plans/PROJECT_OVERVIEW.md) và các quy tắc repository.
Roadmap và project overview hiện vẫn ghi là draft.

Đề yêu cầu dùng lịch sử 24 giờ của load, temperature, humidity và wind speed
để dự báo load bước tiếp theo; so sánh VAR, XGBoost và LSTM bằng RMSE, MAE,
MAPE. R01–R09 và ownership chi tiết được liệt kê trong roadmap mục 1.2.
Project overview ghi Human đã chọn nguồn Spain thay nguồn UCI nêu trong đề;
chọn nguồn không phê duyệt schema, đơn vị hoặc xử lý dữ liệu.

## Phạm vi và ranh giới

- A01: rà soát scope, dataset source, R01–R09, file map và module owners;
  sửa mô tả hiện trạng sai; trình Human duyệt kiến trúc và kết quả.
- A02: sau khi A01 được chấp nhận, viết `docs/results/problem_definition.md`
  gồm 5W1H, I/O và forecast origin tạm thời, success criteria, risks và
  decision register; trình Human review. Không coi đề xuất là contract đã khóa.
- Ngoài Phase 0: tải hoặc checksum dataset, cài dependencies, xử lý/split dữ liệu,
  viết pipeline/tests, fit model, traffic forecasting và deployment.
- Nguồn Spain và các lựa chọn downstream vẫn cần kiểm chứng, thiết kế và duyệt
  ở phase sở hữu; không sao chép preliminary inspection thành execution evidence.

## Ownership đề xuất để duyệt tại A01

`data/` sở hữu ingestion, integration, splitting, preprocessing và features;
`analysis/` sở hữu EDA, metrics, baselines, models, walk-forward và error analysis;
`visualization/` vẽ từ artifacts được phép; `pipeline.py` chỉ điều phối stage và
gates. `config/`, `datasets/`, `runs/`, `outputs/`, `docs/` và `notebooks/` có
ranh giới như roadmap mục 2. Chi tiết file, dependencies và validation nằm trong
file map; đây là thiết kế, không khẳng định các file planned đã tồn tại.

## Before-process plan: A01

1. Đối chiếu đề, rules, overview và map với checkout; ghi khác biệt và giữ nguyên
   các quyết định chưa được duyệt. Rà soát paths, ownership và dependencies.
2. Sửa drift tại `docs/plans/PROJECT_OVERVIEW.md` và
   `docs/status/current_status.md`: không khẳng định UCI raw file đang tồn tại;
   ghi notebook template đã có nhưng chưa executable/final. Cập nhật `README.md`
   và status theo thực trạng, không tuyên bố A01 đã được Human chấp nhận.
3. Cập nhật inventory/map khi có file thực tế mới; ghi execution evidence của
   stage trong `docs/logs/` theo roadmap. Không thay đổi code, dữ liệu, notebook,
   dependencies hoặc các phase sau. Nếu map/roadmap cần thay đổi substantive,
   ghi rõ ảnh hưởng đến review trước đó và không tự tuyên bố được duyệt.
4. Kiểm tra CSV parse, path tương đối duy nhất, đối chiếu files hiện có với map,
   links nội bộ liên quan, UTF-8 và `git diff --check`; kiểm tra diff đúng scope.
   Ghi commands, kết quả, giới hạn và approval reference thực tế trong log.
5. Trình Human review scope, nguồn, R01–R09, map và architecture; chỉ khi được
   chấp nhận mới đánh dấu A01 đạt gate và bắt đầu A02.

Ảnh hưởng dự kiến chỉ ở tài liệu/metadata. Rủi ro chính là nhầm historical
inspection thành bằng chứng tái lập hoặc nhầm kế hoạch draft thành quyết định
được duyệt; mọi trạng thái phải ghi rõ. Có thể giữ nguyên mô tả cũ, nhưng điều
đó duy trì khẳng định sai về checkout và không đáp ứng acceptance A01.

## Before-process plan: A02

Sau gate A01, tạo `docs/results/problem_definition.md` từ đề, overview và quyết
định thực tế. Phân biệt yêu cầu, quyết định Human, đề xuất và việc cần đo; nêu
5W1H, I/O/origin dự kiến, scope, tiêu chí thành công, giới hạn và các quyết định
còn mở. Rà soát links, consistency với A01 và `git diff --check`, ghi log và
trình Human review. Không thực hiện công việc Phase 1.

## Gate và điều kiện dừng

Approval cần ghi người duyệt, ngày và tham chiếu message/record thật. Dừng khi
có conflict giữa nguồn/rules, scope phải mở rộng, thiếu approval, inventory hoặc
validation có sai lệch chưa giải thích. A01 hoàn tất chỉ sau validation và Human
duyệt scope, source, R01–R09, map và architecture; A02 chỉ hoàn tất sau Human
duyệt problem definition. Chuyển Phase 1 cần review Phase 0 và thiết kế/approval
Phase 1 riêng.

## Evidence chuẩn bị, chưa phải validation hoàn tất A01

- 2026-11-17: kiểm tra `datasets/raw/` chỉ thấy README; không tìm thấy
  `LD2011_2014.txt` tại đó. Không suy diễn nguyên nhân.
- Notebook `notebooks/practice_4.ipynb` có 12 Markdown cells, 0 code cells.
- Inventory trước khi tạo tài liệu này: 25 files, map có 91 entries; các FILE
  đánh dấu EXISTING khớp các file hiện có. Cần kiểm tra lại sau thay đổi.
- PDF trích xuất bằng `pypdf` có cảnh báo object offsets; nội dung ba trang đọc
  được, nhưng đây chưa phải kiểm tra trực quan bản PDF.

## Approval record

- Phase 0 specification/before-process plan: **Human duyệt 2026-11-17**, tin nhắn
  `APPROVED` trong cuộc hội thoại hiện tại, trả lời đề nghị duyệt tài liệu này.
- A01 scope, source, R01–R09, map và architecture: **Human chấp nhận và đóng
  gate ngày 2026-11-17**, tin nhắn `Close Gate A01 & Execute Phase 0 — Stage A02`
  trong cuộc hội thoại hiện tại, trả lời đề nghị review A01.
- A02 problem definition / Phase 0 acceptance: **Human chấp nhận và đóng ngày
  2026-11-17**, tin nhắn `Close Phase 0 (Gate A02) & Draft Phase 1 Specification`
  trong cuộc hội thoại hiện tại, trả lời đề nghị review A02.
