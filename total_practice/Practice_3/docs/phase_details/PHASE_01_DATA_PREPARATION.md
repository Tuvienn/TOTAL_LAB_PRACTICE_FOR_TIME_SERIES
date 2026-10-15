# PHASE 01 — DATA PREPARATION

## 1. Phase Identity
**Phase:** 01  
**Name:** Data Preparation  
**Practice:** Practice 3 — Machine Learning Time Series Forecasting  
**Dataset:** `AEP_hourly.csv`  
**Status:** `APPROVED`  
**Implementation authorized:** `YES`  
**Approved by:** `Human`  
**Approval date:** `2026-10-15`

## 2. Objective
Chuẩn bị một working dataset có timeline nhất quán để sử dụng cho Feature Engineering. Phase này không train model và không tạo lag/rolling features.

```text
RAW DATA
    ↓
inspect → parse → sort → resolve timestamp quality issues → hourly working dataset
```

## 3. Input
Raw dataset:
```text
datasets/raw/AEP_hourly.csv
```
Raw file phải được giữ nguyên tuyệt đối, không sửa trực tiếp.

## 4. Current Data Quality Findings
| Kiểm tra | Kết quả |
|---|---:|
| Kích thước | 121,273 dòng, 2 cột |
| Schema | `Datetime`, `AEP_MW` |
| Khoảng thời gian | `2004-10-01 01:00:00` → `2018-08-03 00:00:00` |
| Ô trống | 0 |
| Timestamp không parse được | 0 |
| Giá trị không hợp lệ/không dương | 0 |
| Thứ tự thời gian | Chưa được sắp xếp |
| Timestamp trùng | 4 timestamp, tương ứng 8 dòng |
| Timestamp giờ bị thiếu | 27 giờ |
| Dòng trùng hoàn toàn | 0 |

Trong 27 giờ thiếu:
- 24 giờ có dấu hiệu liên quan DST.
- 3 khoảng thiếu riêng biệt: `2010-12-10 00:00`, `2012-12-06 04:00`, `2014-03-11 14:00`.
- 4 timestamp trùng đều xuất hiện vào tháng 11 và có dấu hiệu liên quan DST.
- CSV không chứa timezone hoặc UTC offset.

Không được tự khẳng định timezone hay tự chuyển sang `America/New_York`.

## 5. Required Tasks
### 5.1 Load Raw Dataset
Đọc raw CSV vào working dataframe.

### 5.2 Parse Datetime
Parse `Datetime` nghiêm ngặt bằng format cố định:

```text
%Y-%m-%d %H:%M:%S
```

Nếu có giá trị không khớp format, quá trình phải dừng thay vì âm thầm chuyển thành `NaT`. Kiểu dữ liệu trong memory là `datetime64[ns]`, timezone-naive.

### 5.3 Convert Target
Chuyển `AEP_MW` sang numeric nếu cần.

### 5.4 Stable Sort
Sắp xếp tăng dần theo `Datetime` bằng stable sort.

### 5.5 Handle Duplicate Timestamps
Với 4 timestamp trùng:
- group theo `Datetime`;
- lấy trung bình `AEP_MW`;
- lưu `source_count`;
- gắn quality flag.

Không dùng `first`/`last` vì lựa chọn đó tùy ý. Lấy trung bình là modeling assumption để tạo một giá trị cho mỗi clock-hour, không phải khôi phục chính xác hai giờ vật lý có thể phát sinh do DST. Cách xử lý này làm mất sự tách biệt giữa hai observation và phải được ghi nhận như một limitation.

### 5.6 Reindex to Complete Hourly Timeline
Tạo hourly index đầy đủ từ timestamp đầu tiên đến cuối cùng.

### 5.7 Preserve Missing Targets
Với timestamp không có quan sát: `AEP_MW = NaN`.

Không interpolation, forward-fill, backward-fill hoặc tạo target giả.

### 5.8 Outlier Policy
Không xóa hoặc clip outlier ở Phase 1.

### 5.9 Timezone Policy
Giữ timestamp timezone-naive và ghi limitation rằng source file không có timezone/offset.

### 5.10 Serialization Policy
Khi lưu processed CSV, `Datetime` phải dùng cùng format:

```text
%Y-%m-%d %H:%M:%S
```

Không thêm `Z`, UTC offset hoặc timezone chưa được source xác nhận.

## 6. Processing Policy
```text
RAW FILE
  ↓ parse Datetime
  ↓ convert AEP_MW
  ↓ stable sort
  ↓ aggregate duplicate timestamps by mean
  ↓ record source_count / quality flag
  ↓ reindex complete hourly timeline
  ↓ keep missing AEP_MW as NaN
WORKING DATAFRAME
```

## 7. Expected Output
### 7.1 Working Dataframe Contract

| Field | Kiểu/giá trị | Ý nghĩa |
|---|---|---|
| `Datetime` | `datetime64[ns]`, timezone-naive | Time index duy nhất, tăng dần trong memory; lưu thành column trong CSV |
| `AEP_MW` | numeric | Target quan sát; `NaN` tại timestamp được thêm khi reindex |
| `source_count` | `0`, `1`, `2` | Số dòng raw đóng góp vào timestamp |
| `quality_flag` | string | Trạng thái nguồn của timestamp |

Quy ước quality flag:

| Trạng thái | `source_count` | `quality_flag` |
|---|---:|---|
| Quan sát bình thường | 1 | `observed` |
| Timestamp trùng đã lấy trung bình | 2 | `duplicate_aggregated` |
| Timestamp được thêm khi reindex | 0 | `missing_timestamp` |

### 7.2 Required Processed Artifact

Processed dataset phải được lưu tại:

```text
datasets/processed/aep_hourly_prepared.csv
```

Kết quả dự kiến:

```text
rows = 121296
unique_timestamps = 121296
duplicate_timestamps = 0
missing_AEP_MW = 27
source_count_0 = 27
source_count_1 = 121265
source_count_2 = 4
sum_source_count = 121273
```

Machine-readable audit được lưu tại:

```text
outputs/results/phase_01_data_quality.json
```

## 8. Validation Criteria
Phase 1 PASS khi:
- `Datetime` parse thành công;
- timeline tăng dần;
- duplicate timestamp = 0;
- hourly timeline liên tục sau reindex;
- missing target được giữ là `NaN`;
- không tạo target giả;
- raw file không bị chỉnh sửa;
- SHA-256 của raw file trước và sau execution đều bằng `109d122f7b485555c609eecdec2cd5a03172e0a08acd358d863acc93eb452585`;
- policy timezone được giữ đúng;
- số lượng duplicate/missing trước và sau xử lý được ghi lại.

## 9. Data Leakage Checks
- không dùng future information để điền missing target;
- không interpolation dựa trên tương lai;
- không thay đổi target để cải thiện model.

## 10. Stop Conditions
STOP nếu:
- timestamp không parse được ngoài dự kiến;
- target có invalid value mới;
- duplicate/missing count khác bất thường;
- xuất hiện timezone metadata mới làm thay đổi interpretation;
- aggregation policy cần thay đổi.

## 11. Implementation Scope

Các owner dự kiến cho implementation sau khi được Human duyệt:

```text
src/practice_3/data/data_preparation.py
tests/test_data_preparation.py
datasets/processed/aep_hourly_prepared.csv
outputs/results/phase_01_data_quality.json
docs/logs/PHASE_01_EXECUTION.md
```

Không thuộc phạm vi Phase 1:

```text
datasets/raw/AEP_hourly.csv
README.md
notebook presentation
lag/rolling feature engineering
train/test split
model training hoặc evaluation
Phase 2–7 implementation
```

## 12. Completion Condition
```text
chronologically ordered
+
hourly aligned
+
duplicate resolved
+
missing preserved
+
raw untouched
```

## 13. Downstream Role
Output là input cho `PHASE 02 — FEATURE ENGINEERING`.

Phase 2 phải tuân thủ handoff contract:

- không âm thầm fill 27 target đang thiếu;
- không đưa hàng có target `NaN` vào model training;
- chốt riêng cách loại các hàng bị ảnh hưởng bởi missing target, lag và rolling;
- giữ `source_count` và `quality_flag` để truy vết chất lượng dữ liệu;
- không xem hourly reindex hoặc duplicate aggregation là bằng chứng đã khôi phục chính xác DST.
