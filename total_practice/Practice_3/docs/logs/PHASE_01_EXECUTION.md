# PHASE 01 — EXECUTION LOG

## 1. Trạng thái

```text
Phase: 01 — Data Preparation
Execution date: 2026-10-19
Result: PASS
```

## 2. Môi trường đã dùng

```text
Python: 3.14.3
pandas: 3.0.6
pytest: 9.1.1
Notebook kernel: practice3-timeseries
```

## 3. Thành phần đã chạy

1. Chạy pipeline chính thức bằng `python -m practice_3.data.data_preparation`.
2. Đọc lại và validate processed CSV sau khi serialize.
3. Chạy `pytest tests/test_data_preparation.py -v`.
4. Chạy toàn bộ `notebooks/Practice_3_present.ipynb` từ đầu bằng `nbconvert`.
5. Kiểm tra compile cho source và tests.

## 4. Kết quả dữ liệu

| Chỉ số | Kết quả |
|---|---:|
| Raw rows | 121.273 |
| Raw missing target | 0 |
| Raw non-positive target | 0 |
| Duplicate rows trước xử lý | 8 |
| Duplicate timestamps trước xử lý | 4 |
| Missing hourly timestamps trước reindex | 27 |
| Prepared rows | 121.296 |
| Duplicate timestamps sau xử lý | 0 |
| Missing `AEP_MW` sau reindex | 27 |
| `source_count = 0 / 1 / 2` | 27 / 121.265 / 4 |
| Tổng `source_count` | 121.273 |
| Timeline liên tục theo giờ | PASS |
| Timezone policy | timezone-naive |

Raw SHA-256 trước và sau execution đều là:

```text
109d122f7b485555c609eecdec2cd5a03172e0a08acd358d863acc93eb452585
```

## 5. Kết quả validation

```text
Pytest: 14 passed
Source/tests compile: PASS
Notebook: 6/6 code cells executed
Notebook errors: 0
Notebook validation gate: PASS
```

Bộ test bao phủ schema, timeline, missing timestamp, duplicate aggregation bằng trung bình, source conservation, audit trước/sau, stop conditions và việc tạo/đọc lại artifacts.

## 6. Artifacts bàn giao

- Processed dataset: `datasets/processed/aep_hourly_prepared.csv`
- Machine-readable audit: `outputs/results/phase_01_data_quality.json`
- Presentation notebook: `notebooks/Practice_3_present.ipynb`
- Source implementation: `src/practice_3/data/data_preparation.py`
- Automated tests: `tests/test_data_preparation.py`

## 7. Giới hạn được giữ lại

- Raw source không có timezone hoặc UTC offset; không tự gán timezone.
- Bốn timestamp trùng được lấy trung bình theo contract, nên không khôi phục được hai giờ vật lý có thể liên quan DST.
- Hai mươi bảy target thiếu vẫn là `NaN`; Phase 1 không interpolation, forward-fill hoặc tạo target giả.
- Không xóa hoặc clip outlier trong Phase 1.

## 8. Kết luận

```text
PHASE 01: PASS
HANDOFF TO PHASE 02: READY
```

Phase 2 phải tiếp tục giữ metadata chất lượng và không đưa hàng có target `NaN` vào model training.
