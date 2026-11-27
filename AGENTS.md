# Repository Instructions

Đây là entry point chung cho toàn bộ repository và bốn Practice trong
`total_practice/`. Trước khi làm việc, agent phải đọc các nguồn governance và
route tới tài liệu scoped tương ứng; không tự tạo một bộ rule riêng cho từng
Practice nếu chưa có yêu cầu rõ ràng.

## 1. Startup và rule precedence

Trước khi làm việc trong repository:

1. Đọc `working_rule.md` hoàn toàn như Human–AI governance charter.
2. Đọc `.agents/RULES_INDEX.md` hoàn toàn.
3. Đọc mọi active rule, workflow và scoped source mà `.agents/RULES_INDEX.md`
   route cho task hiện tại.

Nếu có conflict giữa các rule, phải dừng, nêu rõ nguồn xung đột và tác động,
không triển khai phần đang tranh chấp cho tới khi Human xác nhận.

## 2. Routing theo Practice

Khi làm việc dưới một Practice, phải đọc README của Practice đó, các rule scoped
nếu tồn tại, exercise specification liên quan và before-process plan đã được
xác nhận khi task yêu cầu implementation.

### Practice 1

- README: `total_practice/Practice_1/README.md`
- Notebook canonical: `notebooks/practice_1_present.ipynb`
- Scoped rules:
  - `docs/rules/architecture_rule.md`
  - `docs/rules/rule_code.md`
- Kết quả chính: E1–E5; E6 là báo cáo Word ngoài repository.

### Practice 2

- README: `total_practice/Practice_2/README.md`
- Core notebook: `notebooks/Practice_2_Exercise.ipynb`
- Exploratory extension: `notebooks/Practice_2_Advanced.ipynb`
- Scoped rules:
  - `docs/rules/architecture_rule.md`
  - `docs/rules/rule_code.md`
- Core protocol: E01–E05; E06 là SARIMA exploratory extension.

### Practice 3

- README: `total_practice/Practice_3/README.md`
- Notebook canonical: `notebooks/Practice_3_present.ipynb`
- Scoped rules:
  - `docs/rules/architecture_rule.md`
  - `docs/rules/rule_code.md`
  - `docs/rules/workflow_rule.md`
- Kết quả phải được đối chiếu với phase details, results, logs và current status.

### Practice 4

- README: `total_practice/Practice_4/README.md`
- Notebook canonical duy nhất: `notebooks/practice4.ipynb`
- Không thêm hoặc khôi phục `notebooks/Practice_4_Manual.ipynb` thành notebook
  canonical thứ hai.
- Practice 4 không có thư mục `docs/rules/` riêng; dùng README, plans, status,
  results và governance rules được route từ `.agents/RULES_INDEX.md`.

## 3. Quy tắc chung cho bốn Practice

- Giữ raw dataset bất biến; mọi transformation hoặc missing-value experiment
  phải chạy trên working object hoặc processed artifact đã được ghi nhận.
- Giữ provenance, checksum, outputs, logs, current status và README nhất quán
  với lần chạy thực tế.
- Không ghi nhận experiment, metric hoặc conclusion chưa chạy là kết quả hoàn tất.
- Không commit `.venv/`, `.ipynb_checkpoints/`, Python cache hoặc local metadata.
- Không phụ thuộc vào thư mục khởi chạy notebook; path phải được resolve từ
  project root hoặc package contract của Practice.
- Không thay đổi notebook canonical, dataset hoặc kết quả đã xác nhận nếu task
  không yêu cầu và chưa có phạm vi rõ ràng.
- Khi sửa code hoặc protocol, phải cập nhật execution evidence và kiểm tra liên
  quan trong cùng phạm vi.

## 4. Tài liệu lịch sử

Historical acknowledgements chỉ là provenance, không phải startup instruction và
không cần agent/session ký lại hoặc cập nhật trong workflow thông thường.
