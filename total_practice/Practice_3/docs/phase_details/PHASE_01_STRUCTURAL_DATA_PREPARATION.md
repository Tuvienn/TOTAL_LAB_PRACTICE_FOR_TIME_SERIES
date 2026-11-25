# PHASE 01 — STRUCTURAL DATA PREPARATION

## 1. Phase identity

```text
Project: Practice_3
Phase: 1
Name: Structural Data Preparation
Design status: READY_FOR_HUMAN_REVIEW
Implementation authorization: PENDING
```

## 2. Mục tiêu

Tạo một prepared dataset có timeline theo giờ nhất quán, giữ đầy đủ provenance của raw observations và không tạo target giả.

```text
raw CSV
→ contract validation
→ strict normalization
→ stable chronological sort
→ duplicate aggregation
→ complete hourly timeline
→ preserve missing target
→ validate and serialize
```

Phase này chỉ xử lý cấu trúc và chất lượng time index theo policy đã được Human duyệt. Phase này không thực hiện EDA, split, feature engineering, X/y construction, model training hoặc evaluation.

## 3. Input contract

Canonical data contract:

```text
config/data_contract.json
```

Raw input:

```text
datasets/raw/AEP_hourly.csv
```

Expected identity:

```text
Columns: Datetime, AEP_MW
Rows: 121,273
SHA256: 109d122f7b485555c609eecdec2cd5a03172e0a08acd358d863acc93eb452585
Datetime format: %Y-%m-%d %H:%M:%S
Target unit: MW
Expected frequency: hourly
Timezone policy: timezone-naive source without offset
```

Raw file là immutable evidence. Không sort, deduplicate, impute, reindex hoặc ghi đè trực tiếp raw file.

## 4. Known structural findings

Legacy evidence cho biết các expected findings sau; v2 phải tự xác minh lại từ raw input:

| Kiểm tra | Expected finding |
|---|---:|
| Raw rows | 121,273 |
| Raw columns | 2 |
| Raw missing cells | 0 |
| Unparseable timestamps | 0 |
| Non-positive target values | 0 |
| Raw chronology | Chưa tăng dần |
| Duplicate timestamp rows | 8 |
| Duplicate timestamps | 4 |
| Missing hourly timestamps | 27 |
| Fully duplicated rows | 0 |

Nếu v2 quan sát kết quả khác contract hoặc expected findings, pipeline phải dừng để Human review; không tự sửa expected counts.

## 5. Approved processing policy

### 5.1 Load and contract validation

- Đọc `config/data_contract.json`.
- Resolve raw path từ project root, không dùng absolute path theo máy.
- Kiểm tra file tồn tại, SHA256 và exact column order.
- Không tiếp tục nếu contract không hợp lệ.

### 5.2 Strict datetime normalization

Parse `Datetime` bằng format cố định:

```text
%Y-%m-%d %H:%M:%S
```

Policy:

- `errors="raise"`;
- output trong memory là `datetime64[ns]`;
- không cho phép `NaT`;
- giữ timezone-naive;
- không tự suy luận UTC hoặc `America/New_York`.

### 5.3 Target normalization

- Chuyển `AEP_MW` sang numeric bằng strict conversion.
- Dừng nếu có missing, non-finite hoặc non-positive raw target.
- Không scale, difference, clip hoặc transform target.

### 5.4 Stable chronological sort

- Tạo working copy.
- Sort tăng dần theo `Datetime` bằng stable sort.
- Không sửa thứ tự trong raw CSV.

### 5.5 Duplicate timestamp aggregation

Với mỗi duplicate timestamp:

```text
AEP_MW = mean của raw observations cùng timestamp
source_count = số raw observations đóng góp
quality_flag = duplicate_aggregated
```

Timestamp có một raw observation:

```text
source_count = 1
quality_flag = observed
```

Lấy mean là modeling assumption để tạo một giá trị trên mỗi clock-hour; không được mô tả là khôi phục chính xác DST observations.

### 5.6 Complete hourly timeline

Tạo `pd.date_range` từ timestamp nhỏ nhất đến lớn nhất với `freq="h"`, sau đó reindex working dataset.

Timestamp được thêm:

```text
AEP_MW = NaN
source_count = 0
quality_flag = missing_timestamp
```

### 5.7 Missing-target policy

Giữ nguyên missing target. Không:

- interpolate;
- forward-fill;
- backward-fill;
- dùng mean/median;
- dùng future observations;
- tạo target giả bằng model.

### 5.8 Outlier policy

Không xóa, clip hoặc winsorize trong Phase 1. Outlier observations thuộc TRAIN-only EDA ở Phase 3 sau khi temporal boundaries được khóa.

### 5.9 Serialization policy

Processed CSV phải lưu `Datetime` với format:

```text
%Y-%m-%d %H:%M:%S
```

Không thêm timezone hoặc UTC offset không có trong source.

## 6. Expected prepared-data contract

Output path:

```text
datasets/processed/aep_hourly_prepared.csv
```

Schema:

| Field | Contract |
|---|---|
| `Datetime` | `datetime64[ns]` trong memory; timezone-naive; unique; tăng dần |
| `AEP_MW` | Numeric target; `NaN` chỉ tại inserted timestamps |
| `source_count` | Integer thuộc `{0, 1, 2}` |
| `quality_flag` | `observed`, `duplicate_aggregated` hoặc `missing_timestamp` |

Expected results:

```text
prepared rows = 121,296
unique timestamps = 121,296
duplicate timestamps after = 0
missing AEP_MW = 27
source_count_0 = 27
source_count_1 = 121,265
source_count_2 = 4
sum_source_count = 121,273
timeline continuous hourly = true
```

## 7. Audit contract

Official audit:

```text
outputs/results/phase_01_data_quality.json
```

Audit phải chứa ít nhất:

- phase và contract version;
- input/output relative paths;
- raw SHA256 trước và sau;
- processed artifact SHA256;
- raw và prepared row counts;
- schema identities;
- raw/prepared timestamp range;
- raw chronological status;
- raw missing, non-finite và non-positive target counts;
- duplicate row/timestamp counts;
- danh sách duplicate timestamps;
- missing-hour count;
- danh sách missing timestamps;
- `source_count` distribution;
- `quality_flag` distribution;
- source-conservation result;
- timezone policy;
- duplicate, missing-target và outlier policies;
- final status.

Audit không chứa trend, seasonality, feature recommendation hoặc model metric.

## 8. Atomic-write policy

Official artifacts phải được tạo theo trình tự:

```text
build in memory
→ validate in memory
→ write temporary artifact
→ read temporary artifact back
→ validate serialized artifact
→ calculate processed SHA256
→ promote to official path
```

Nếu một bước thất bại, không promote partial output. Temporary artifact phải nằm trong cùng project và không được xem là official result.

## 9. Determinism

Cùng raw file, contract và source code phải tạo:

- cùng prepared rows;
- cùng timestamps và values;
- cùng processed CSV SHA256;
- cùng scientific audit fields.

Không đưa runtime timestamp ngẫu nhiên vào nội dung quyết định deterministic checksum của processed dataset.

## 10. Proposed source ownership

```text
src/practice_3_v2/data/data_preparation.py
```

Proposed functions:

```text
load_data_contract
calculate_sha256
validate_raw_file
load_raw_data
normalize_raw_data
aggregate_duplicate_timestamps
build_complete_hourly_timeline
validate_prepared_data
build_phase_01_audit
save_prepared_artifacts
run_phase_01
```

Implementation dùng tiếng Anh cho identifier, exception và docstring. Không import runtime code từ package legacy `practice_3`.

## 11. Environment prerequisite

Trước implementation, tạo môi trường riêng:

```text
Practice_3/.venv
```

Dependency tối thiểu của Phase 1:

```text
pandas
numpy
pytest
```

Không cần cài XGBoost hoặc scikit-learn trong Phase 1.

## 12. Test contract

Test owner:

```text
tests/test_data_preparation.py
```

Focused tests phải kiểm tra:

1. Raw file tồn tại.
2. Raw SHA256 khớp contract.
3. Exact raw schema.
4. Strict datetime parsing.
5. Invalid datetime làm pipeline dừng.
6. Non-numeric target làm pipeline dừng.
7. Missing, non-finite hoặc non-positive raw target làm pipeline dừng.
8. Prepared schema và dtypes.
9. Timeline unique, tăng dần và liên tục theo giờ.
10. Đúng 27 inserted timestamps.
11. Missing rows có `AEP_MW = NaN`, `source_count = 0` và đúng flag.
12. Đúng 4 duplicate timestamps được aggregate bằng mean.
13. Source conservation.
14. Exact metadata distributions.
15. Raw checksum không đổi.
16. Serialized CSV đọc lại và validation được.
17. Processed artifact checksum deterministic giữa hai runs.
18. Audit lists khớp dữ liệu thực tế.
19. Pipeline không import package legacy `practice_3`.
20. Official artifact chỉ được promote sau validation.

Module-scoped fixtures được ưu tiên để tránh chạy pipeline lặp lại không cần thiết.

## 13. Validation gate

Phase 1 PASS khi:

- focused tests PASS;
- full v2 regression suite PASS;
- raw checksum trước/sau không đổi;
- prepared artifact khớp contract;
- serialized artifact validation PASS;
- deterministic rerun PASS;
- official audit khớp independent recalculation;
- `git diff --check` PASS;
- execution log được tạo;
- không có processed result hoặc code nào được lấy trực tiếp từ legacy outputs.

## 14. Stop conditions

Dừng và báo Human nếu:

- raw checksum hoặc schema khác contract;
- timestamp không parse được;
- target raw có missing, non-finite hoặc non-positive value;
- duplicate/missing counts khác expected findings;
- xuất hiện timezone metadata mới;
- prepared counts hoặc distributions không khớp;
- serialized artifact không deterministic;
- cần thay duplicate, missing hoặc outlier policy;
- bất kỳ test correctness nào FAIL.

## 15. Execution log

Sau khi triển khai và chạy thành công, tạo:

```text
docs/logs/PHASE_01_EXECUTION.md
```

Log phải ghi command, Python/dependency versions, input/output identities, test result, artifact checksums và status. Không ghi PASS trước khi execution thực sự hoàn thành.

## 16. Downstream handoff

Phase 1 output là input cho Phase 2 — Temporal Split & Validation Design.

Phase 2 phải:

- không âm thầm fill 27 missing targets;
- dùng timestamp boundary đã duyệt trong Phase 0;
- phân biệt development/TRAIN với historical re-evaluation holdout;
- không dùng holdout target trong Phase 3 EDA;
- giữ `source_count` và `quality_flag` để truy vết.

## 17. Completion condition

```text
raw immutable
+ strict schema and datetime validation
+ deterministic structural treatment
+ continuous hourly timeline
+ missing target preserved
+ source provenance preserved
+ atomic official artifacts
+ tests and independent audit PASS
```

Sau khi Human review và duyệt phase detail này mới được tạo môi trường, migrate/viết source và chạy Phase 1.
