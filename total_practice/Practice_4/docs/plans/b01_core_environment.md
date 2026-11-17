# B01 — Core environment proposal

Trạng thái: **SYSTEM ENVIRONMENT SNAPSHOT**, cập nhật 2026-11-18. Human yêu cầu
dùng system Python 3.12 không virtualenv, chỉ định core dependencies và cho phép
editable install. `requirements.lock.txt` ghi exact installed core versions;
không chứng minh resolution/clean-environment reproduction trên máy khác.
Phần candidate bên dưới là lịch sử đề xuất trước khi kiểm environment thực tế,
không phải các version đã cài trong run B01.

System Python 3.12.10, Windows 11 AMD64: pandas 2.3.3, numpy 2.5.5,
pytest 9.2.0, setuptools 84.2.1, wheel 0.48.0, jsonschema 4.26.0; các
transitive pins hiện có được ghi trong `requirements.lock.txt`. `pip check` đạt;
editable install dùng `--no-deps --no-build-isolation`, không tạo virtualenv.
Source/version/units/time semantics do Human xác nhận; metadata Kaggle chưa thể
kiểm chứng độc lập. Không có B02 policy approval.

## Target và candidate versions

Target đề xuất: CPython 3.12.10, Windows 11 x86-64, clean virtual environment;
pip 25.0.1 là bootstrap tool. Core chỉ phục vụ B01 ingestion/audit, package và
tests. Các versions dưới đây là candidate exact pins để resolver kiểm tra, chưa
phải dependency closure đã xác nhận.

| Package | Candidate | Vai trò |
|---|---|---|
| pandas | 2.3.3 | CSV và time-index audit |
| numpy | 2.3.4 | pandas dependency |
| pytest | 8.4.2 | fixtures và tests |
| setuptools | 80.9.0 | package build/editable install |
| python-dateutil | 2.9.0.post0 | pandas dependency |
| pytz | 2025.2 | pandas timezone dependency |
| tzdata | 2025.2 | pandas timezone data |
| six | 1.17.0 | python-dateutil dependency |
| iniconfig | 2.1.0 | pytest dependency candidate |
| packaging | 25.0 | pytest dependency candidate |
| pluggy | 1.6.0 | pytest dependency candidate |
| pygments | 2.19.2 | pytest dependency candidate |
| colorama | 0.4.6 | Windows pytest dependency candidate |

Candidate có thể cần thay đổi sau metadata/resolver checks; không khẳng định
đây là tập đầy đủ hoặc các pin đồng thời tương thích. Không bổ sung XGBoost,
TensorFlow/Keras hoặc model dependencies ở B01. Không coi cài đặt sẵn trong
global environment là lock hoặc bằng chứng clean install.

## Evidence hiện có và giới hạn

- Kiểm tra read-only local: Python 3.12.10, pip 25.0.1, Windows 11 AMD64;
  pandas 2.3.3 hiện có. Điều này không xác nhận clean-env compatibility.
- Local pandas metadata yêu cầu numpy >=1.26 với Python >=3.12, python-dateutil
  >=2.8.2, pytz >=2020.1 và tzdata >=2022.7. Điều này không xác nhận toàn bộ
  candidate dependencies.
- [PyPI pandas 2.3.3](https://pypi.org/pypi/pandas/2.3.3/json),
  [numpy 2.3.4](https://pypi.org/pypi/numpy/2.3.4/json) và
  [pytest 8.4.2](https://pypi.org/pypi/pytest/8.4.2/json) liệt kê Python 3.12;
  [setuptools 80.9.0](https://pypi.org/pypi/setuptools/80.9.0/json) là candidate
  build backend. Metadata không thay thế resolver và clean-environment smoke.
- `python -m pip install --dry-run --ignore-installed --only-binary=:all:
  --disable-pip-version-check --retries 0 --timeout 5 pandas==2.3.3 pytest==8.4.2
  setuptools==80.9.0 numpy==2.3.4` không resolve được pandas: pip báo không thấy
  distribution. Chưa xác định được index/network hay nguyên nhân khác; kết quả
  này không chứng minh versions bất khả dụng hoặc tương thích. Không cài package.
- Trang [nguồn Kaggle](https://www.kaggle.com/datasets/nicholasjhana/energy-consumption-generation-prices-and-weather)
  được mở nhưng body không đọc được; license/access/version/units vẫn chưa xác
  minh. Không bypass authentication hoặc suy diễn quyền sử dụng.

## Đường đến approval và validation

1. Kiểm tra index/network và metadata từng candidate; resolve đầy đủ transitive
   pins cho đúng CPython/platform, kiểm tra wheel availability và constraints.
   Ghi index/source, output, versions, platform và mọi thất bại. Không đổi pin
   âm thầm sau Human approval.
2. Trình exact resolved list, compatibility evidence, lock strategy và impact để
   Human duyệt trước cài dependency. Chỉ sau approval mới tạo lock chính thức,
   clean venv và cài; `pip check`, import smoke và tests phải đạt trước audit.
   `--no-build-isolation` hoặc build dependencies được pin cần được xác định rõ
   để editable install không âm thầm lấy backend khác.
3. B01 vẫn cần source license/unit/time evidence và approval references; B02 cần
   policy và acceptance riêng. Chưa tạo code/config/data/lock trong bước này.

Đánh đổi: pins tăng reproducibility nhưng có thể cần rebuild có kiểm soát khi
platform hoặc model groups đổi. Chọn package đang cài trong global environment
không chứng minh được clean reproduction; đó không phải lock strategy.
