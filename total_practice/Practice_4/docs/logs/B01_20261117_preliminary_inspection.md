# B01 — Preliminary inspection evidence

Ngày: 2026-11-17. Human cho biết đã cung cấp hai CSV và yêu cầu dùng môi trường
có sẵn, Python 3.12 recommended. Đây là inspection read-only, không phải run
manifest/approval hay acceptance của B01.

Environment đã chạy: Windows 11 AMD64, Python 3.12.10, pandas 2.3.3,
NumPy 2.5.4. `pytest` và `setuptools` không importable; pip 25.0.1 hiện có.
Không cài package. `python` trên PATH là Python 3.12.10; `py -0p` cũng liệt kê
3.12, 3.13 và 3.14; các version khác chưa được kiểm tra dependencies.

Command từ repository root: PowerShell truyền đoạn Python sau qua stdin tới
`python -` (đoạn này chỉ đọc raw files; không tạo hoặc sửa dataset):

```python
from pathlib import Path
import hashlib, json, pandas as pd
p = Path('total_practice/Practice_4/datasets/raw')
for name in ['energy_dataset.csv', 'weather_features.csv']:
    f = p / name
    before = hashlib.sha256(f.read_bytes()).hexdigest()
    d = pd.read_csv(f)
    print(name, before, len(d), len(d.columns), list(d.columns))
    print('missing', json.dumps(d.isna().sum().to_dict()))
    print('duplicate_rows', int(d.duplicated().sum()))
    col = 'time' if 'time' in d else d.columns[0]
    t = pd.to_datetime(d[col], utc=True, errors='coerce', format='mixed')
    print('time', col, int(t.isna().sum()), t.min(), t.max(),
          bool(t.is_monotonic_increasing), int(t.duplicated().sum()))
    if name.startswith('energy'):
        s = pd.DatetimeIndex(t.dropna().unique()).sort_values()
        print('unique_times', len(s), 'missing_hours',
              len(pd.date_range(s.min(), s.max(), freq='h')) - len(s))
    else:
        print('city_counts', d['city_name'].value_counts(dropna=False).to_dict())
        print('city_time_duplicate_extra',
              int(pd.DataFrame({'t': t, 'city': d['city_name']}).duplicated().sum()))
    print('raw_hash_unchanged', before == hashlib.sha256(f.read_bytes()).hexdigest())
```

Thực tế đã chạy đoạn tương đương, exit 0; kết quả chính, hashes và giới hạn
được ghi tại [data audit](../results/data_audit.md). Hai raw hashes trước/sau
đều khớp. Lệnh trên tái hiện các phép tính đã dùng; format in khác nhẹ, không
phải log output từng dòng. Chưa có reproducible pipeline/config hay formal run
manifest; không tự ghi approval hoặc khẳng định B01 pass.

## Kiểm tra bổ sung 2026-11-18

System Python 3.12.10 hiện import được pandas 2.3.3, numpy 2.5.5, pytest 9.2.0
và setuptools 84.2.1. Các versions này là environment quan sát tại thời điểm
kiểm tra; so với inspection trước, pytest/setuptools đã xuất hiện và NumPy đã
thay đổi. Không có bằng chứng ai đã thay đổi environment và không khẳng định nó
là lock hoặc clean install. Chưa có B01 test suite để chạy.

Python/pandas kiểm tra read-only group theo `city_name` nguyên gốc và timestamp
UTC parse được: 2.798 duplicate groups, 3.076 extra rows; `nunique(dropna=False)`
trên `temp`, `humidity`, `wind_speed` cho 0 conflicting groups. Mỗi city có
35.064 timestamps duy nhất, sai khác tập timestamp với energy bằng 0. Đây là
inspection trên các timestamps parse được, không phê duyệt dedup hoặc proxy.
Chi tiết counts và min/max tại data audit.

Trang nguồn Kaggle và hai metadata API endpoints đã thử mở nhưng không trả body
metadata đọc được; không thể xác minh units độc lập từ các kết quả đó. Source
version/license/date là theo xác nhận Human, như source manifest ghi rõ.
