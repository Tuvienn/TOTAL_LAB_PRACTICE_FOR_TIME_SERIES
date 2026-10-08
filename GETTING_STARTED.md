# Hướng dẫn bắt đầu và cộng tác

Tài liệu này dành cho thành viên mới muốn clone, chạy và đóng góp vào repository
`TOTAL_LAB_PRACTICE_FOR_TIME_SERIES`.

## 1. Trạng thái hiện tại

- Practice 1 sử dụng dataset AirPassengers.
- Exercise 1 — ACF/PACF đã được triển khai và kiểm chứng.
- Exercise 2–5 chưa được phép tự động triển khai. Mỗi exercise cần được TuVien duyệt
  specification, before-process plan và authorization riêng.
- Exercise 6 là báo cáo Word do TuVien quản lý ngoài phần AI implementation.

Nguồn trạng thái chính xác nhất là:

```text
total_practice/Practice_1/docs/current_flow/current_status.md
```

## 2. Yêu cầu trước khi clone

Cài đặt:

- Git;
- Python `3.12.x`;
- một terminal;
- VS Code hoặc IDE hỗ trợ Python/Jupyter nếu muốn mở notebook.

Kiểm tra phiên bản:

```bash
git --version
python3.12 --version
```

Nếu máy chỉ có lệnh `python`, cần bảo đảm `python --version` trả về Python 3.12.

## 3. Clone repository

Qua HTTPS:

```bash
git clone https://github.com/Tuvienn/TOTAL_LAB_PRACTICE_FOR_TIME_SERIES-.git
cd TOTAL_LAB_PRACTICE_FOR_TIME_SERIES-
```

Hoặc qua SSH nếu tài khoản GitHub đã cấu hình SSH key:

```bash
git clone git@github.com:Tuvienn/TOTAL_LAB_PRACTICE_FOR_TIME_SERIES-.git
cd TOTAL_LAB_PRACTICE_FOR_TIME_SERIES-
```

Kiểm tra nhánh và remote:

```bash
git status
git remote -v
```

## 4. Những tài liệu phải đọc trước khi làm việc

Mọi thành viên và AI agent phải đọc theo thứ tự:

1. `working_rule.md` — governance giữa Human và AI.
2. `.agents/RULES_INDEX.md` — router đến rules/workflow đang active.
3. Các rule mà `RULES_INDEX.md` áp dụng cho task hiện tại.
4. `total_practice/Practice_1/README.md` khi làm Practice 1.
5. Hai scoped rules của Practice 1:
   - `total_practice/Practice_1/docs/RULE_BASE/architecture_rule.md`;
   - `total_practice/Practice_1/docs/RULE_BASE/rule_code.md`.
6. `total_practice/Practice_1/docs/current_flow/current_status.md`.
7. Specification và before-process plan của exercise định làm.

Không cần đọc hoặc ký `.agents/history/acknowledgements.md`. File đó chỉ lưu lịch sử
provenance và không có normative authority.

Nếu hai instruction mâu thuẫn, phải dừng, chỉ rõ nguồn mâu thuẫn và chờ TuVien quyết
định trước khi sửa code.

## 5. Tạo môi trường cho Practice 1

Di chuyển vào Practice 1:

```bash
cd total_practice/Practice_1
```

### macOS hoặc Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Xác minh đúng interpreter và package:

```bash
python --version
python -c "import practice_1; print(practice_1.__file__)"
```

Không commit `.venv`, cache Python, Jupyter runtime state hoặc `*.egg-info`.

## 6. Chạy kiểm thử trước khi thay đổi code

Từ thư mục `total_practice/Practice_1`:

```bash
python -m pytest
python -m compileall -q src tests
```

Baseline hiện tại phải cho kết quả:

```text
2 passed
```

Nếu baseline thất bại ngay sau khi clone, không sửa kết quả hoặc bỏ test. Ghi lại:

- hệ điều hành;
- phiên bản Python;
- câu lệnh đã chạy;
- toàn bộ error message;
- `git status`;

rồi báo cho TuVien.

## 7. Đăng ký và chạy notebook

Đăng ký kernel một lần cho môi trường local:

```bash
python -m ipykernel install --user --name time-series-practice-1 --display-name "Python (time-series-practice-1)"
```

Mở JupyterLab:

```bash
python -m jupyter lab
```

Sau đó mở:

```text
notebooks/practice_1_analysis.ipynb
```

và chọn kernel `Python (time-series-practice-1)`.

Có thể kiểm chứng notebook không cần giao diện bằng:

```bash
python -m jupyter nbconvert --execute --to notebook --inplace \
  --ExecutePreprocessor.kernel_name=time-series-practice-1 \
  --ExecutePreprocessor.timeout=300 \
  notebooks/practice_1_analysis.ipynb
```

Notebook phải chạy theo thứ tự từ đầu đến cuối. Không chạy ngẫu nhiên các cell rồi commit
trạng thái không tái lập được.

## 8. Cách sử dụng package Practice 1

Ví dụ đọc và kiểm tra dữ liệu:

```python
from pathlib import Path

from practice_1.data import calculate_sha256, load_air_passengers

raw_path = Path("data/raw/air_passengers.csv")
frame = load_air_passengers(raw_path)

print(frame.head())
print(frame.index.min(), frame.index.max())
print(calculate_sha256(raw_path))
```

Ví dụ tính ACF/PACF:

```python
from practice_1.analysis import compute_acf_table, compute_pacf_table

series = frame["passengers_thousands"]
acf_table = compute_acf_table(series, max_lag=40, alpha=0.05)
pacf_table = compute_pacf_table(series, max_lag=40, alpha=0.05)
```

Các artifact đã kiểm chứng của Exercise 1 nằm tại:

```text
outputs/figures/
outputs/results/
docs/logs/exercise_01_execution.md
```

Không chỉnh sửa trực tiếp `data/raw/air_passengers.csv`.

## 9. Thành viên mới nên bắt đầu từ đâu?

### Nếu mục tiêu là học hoặc kiểm chứng Exercise 1

1. Đọc Exercise 1 specification và before-process plan.
2. Tạo môi trường.
3. Chạy tests để xác nhận baseline.
4. Mở notebook và chạy từ đầu đến cuối.
5. Đối chiếu figures, CSV và findings với execution log.
6. Không thay đổi scientific parameters nếu chưa có thảo luận và approval.

Các tài liệu Exercise 1:

```text
docs/plan/exercise_details/exercise_01_acf_pacf.md
docs/plan/before_process/exercise_01_before_process.md
docs/logs/exercise_01_execution.md
```

### Nếu mục tiêu là làm Exercise 2 hoặc exercise tiếp theo

1. Đọc `docs/current_flow/current_status.md`.
2. Đọc specification và before-process plan tương ứng.
3. Review scope, input, output, scientific parameters và acceptance criteria với TuVien.
4. Chờ TuVien ghi nhận approval và implementation authorization.
5. Chỉ sau đó mới tạo branch và triển khai.

Việc một plan đã tồn tại không đồng nghĩa plan đó đã được phép implementation.

## 10. Quy trình Git dành cho thành viên

Không phát triển trực tiếp trên `main`. Trước khi bắt đầu:

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/exercise-02-white-noise
```

Tên branch nên thể hiện đúng phạm vi, ví dụ:

```text
docs/onboarding-guide
feature/exercise-02-white-noise
fix/air-passengers-validation
test/acf-pacf-edge-cases
```

Trong khi làm việc:

```bash
git status
git diff
python -m pytest
```

Sau khi kiểm chứng:

```bash
git add <cac-file-dung-pham-vi>
git diff --cached
git commit -m "type: mo ta ngan gon thay doi"
git push -u origin <ten-branch>
```

Sau đó mở Pull Request trên GitHub. Pull Request phải nêu:

- mục tiêu;
- exercise/plan đã được duyệt;
- file đã thay đổi;
- cách kiểm chứng;
- kết quả tests;
- figures/results mới nếu có;
- giới hạn hoặc vấn đề chưa giải quyết.

Không commit credential, token, `.env`, virtual environment hoặc cache. Không dùng
`git push --force` lên `main`.

## 11. Checklist trước khi gửi Pull Request

```text
[ ] Đã đọc rules và current status
[ ] Task nằm trong phạm vi đã được duyệt
[ ] Không sửa raw data
[ ] Không thay đổi chronology hoặc scientific parameters ngoài approval
[ ] Source logic nằm trong src/practice_1/
[ ] Notebook tái sử dụng package, không chứa sys.path hack
[ ] Tests và compile check đều pass
[ ] Notebook chạy end-to-end nếu task ảnh hưởng analysis
[ ] Outputs có nguồn gốc từ actual execution
[ ] Không có credential hoặc file sinh tự động trong staged changes
[ ] Current status và execution evidence được cập nhật khi cần
```

## 12. Lệnh kiểm tra nhanh hằng ngày

Chạy từ `total_practice/Practice_1`:

```bash
git status
python --version
python -m pytest
python -m compileall -q src tests
```

Nếu tất cả đều đạt và task có approval hợp lệ, thành viên có thể tiếp tục đúng bước đã
ghi trong before-process plan.
