# Phase 3 — Training-only exploratory data analysis (D01)

Trạng thái: **DRAFT — PENDING HUMAN REVIEW / APPROVAL**, 2026-11-18. Human đã
duyệt C02 run `20261118_system312_c02_01`, evaluation contract và đóng Phase 2;
yêu cầu `Close Phase 2 (Gate C02) & Draft Phase 3 Specification` chỉ cho phép
soạn tài liệu này. D01 chưa được duyệt hoặc thực thi.

Nguồn: [roadmap Cụm D và mục 7](../plans/plan_overview.md),
[file map](../plans/file_map.csv), [Phase 2](phase_02.md),
[evaluation contract](../results/evaluation_contract.md),
[data contract](../results/data_contract.md),
[C02 run manifest](../../runs/20261118_system312_c02_01/manifest.json) và
[split manifest](../../datasets/processed/split_manifest.json).

## 1. Mục tiêu, phạm vi và gate

D01 đáp ứng R02 bằng EDA **chỉ trên train**: missing/gaps, outliers, daily/weekly
seasonality, quan hệ load–temperature, correlation và temporal dependence. Mục 7
roadmap giao D01 cung cấp evidence ban đầu về liên hệ weather/load và profiles
ngày/tuần; evidence này không chứng minh weather nào dự báo tốt nhất hoặc LSTM đã
học tuần. Các câu hỏi đó còn cần validation ablation/model evaluation ở stage sở hữu.

Không làm D02 treatment, scaler fit, window/tensor materialization, model fit,
validation/test EDA hoặc scoring. Findings chỉ mô tả association, không suy luận
causality, không chọn treatment hoặc xác nhận sensor error chỉ từ giá trị cực trị.
Phase 3 approval và D01 gate là hai quyết định Human riêng; D02 cần D01 acceptance
và Phase 4 specification/before-process plan được duyệt riêng.

## 2. Input và train-only boundary bắt buộc

- Input canonical là `datasets/processed/canonical_hourly.csv` được B02 chấp nhận;
  split là `datasets/processed/split_manifest.json` được C01 chấp nhận. Trước run
  kiểm Phase 2 acceptance, C02 predecessor, canonical byte SHA256 theo lineage
  C02, split byte SHA256 và canonical `split_sha256` theo quy tắc Phase 2. Kiểm
  hashes raw/canonical/split trước và sau run. Chỉ đọc byte stream để checksum là
  integrity check, không parse hay phân tích held-out rows.
- Chỉ parse các data rows zero-based **0..24543 inclusive**, 24.544 rows, từ
  `2014-12-31T23:00:00+00:00` đến `2017-10-19T14:00:00+00:00`, theo train entry
  đã chấp nhận. Loader phải dừng ở đúng số row train; không load toàn CSV rồi
  slice, không parse/đọc record validation hoặc test. Mọi statistics, missing
  profiles, correlations và figures chỉ nhận frame đã bị chặn tại boundary.
- Trước bất kỳ phân tích, validate schema, count, UTC-aware timestamps, strictly
  increasing/unique/contiguous hourly và hai inclusive endpoints của train; reject
  frame có bất kỳ row ngoài train, sai thứ tự hoặc thiếu dòng. Không sửa, sort,
  drop, fill hoặc silently repair input. Synthetic tests phải chứng minh loader
  không yêu cầu record đầu tiên sau train và consumer reject out-of-range data.
- Giữ UTC làm index; chỉ tạo local-time labels bằng `Europe/Madrid` cho daily/
  weekly profiles. Kiểm timezone database và DST; giữ cả hai giờ local lặp lại
  như hai UTC observations khác nhau, không tạo giờ bị thiếu khi spring-forward.
  Báo count cho từng hour/weekday và biên train không đủ chu kỳ; không giả mọi
  local day có 24 observations.

## 3. D01 analyses và evidence yêu cầu

1. **Missing/gaps:** kiểm consistency `load_observed` và raw load; báo số/tỷ lệ
   missing, observed và contiguous missing-run lengths theo giờ, frequency và
   các UTC boundaries trong train. Gaps chạm đầu/cuối train được đánh dấu censored;
   không suy luận length ngoài train. Weather missing và schema bất thường phải
   được báo; không impute hay thay observed truth.
2. **Extremes/physical sanity:** thống kê và plot train load (MW), temperature
   (K), humidity (%) và wind_speed (m/s); báo extrema/timestamps, missing counts,
   kiểm sanity có giải thích, tách flagged value với lỗi sensor được xác nhận.
   B02 ghi raw wind speed 133 m/s trên toàn nguồn, nhưng canonical wind là mean
   năm city: không giả canonical có 133 hoặc giá trị raw đó thuộc train. Xác định
   raw record có thuộc train bằng evidence provenance đã có mà không đọc held-out
   records; nếu có timestamp train đã xác minh, chỉ inspect raw record thuộc train
   và phân biệt raw city value với canonical proxy cùng giờ. Nếu không xác định
   được train membership mà không parse held-out records, không mở raw rows để
   tìm: ghi limitation, dừng phần truy vết này và trình Human hướng xử lý trước
   khi tuyên bố hoàn tất yêu cầu đó. Không xóa, clip hay sửa giá trị.
3. **Time series/profiles:** đồ thị load theo UTC và mean/median profile theo
   hour-of-day và weekday `Europe/Madrid`; show số observed/missing và coverage.
   Báo DST và partial-period limitations, không đưa missing thành zero.
4. **Relationships:** scatter hoặc binned summary load–temperature cùng counts
   và units; kiểm bằng evidence xem U-shape heating/cooling có được hỗ trợ không,
   không giả định tồn tại. Báo pairwise complete counts và correlation matrix bốn
   biến; correlation chỉ phản ánh association, không chứng minh quan hệ nhân quả
   hay dự báo. Báo weather là proxy mean không trọng số của năm thành phố.
5. **ACF/PACF:** train-only load temporal diagnostics, ghi method, lag range,
   sample domain/counts, confidence convention và missing treatment. Không drop
   interior missing rồi xem các hàng còn lại là contiguous hourly; không fill chỉ
   để vẽ. Đề xuất dùng contiguous observed train block, báo rõ cách chọn, endpoints,
   lost observations và khả năng bias; chỉ tính nếu sample đủ cho method/lags.
   Nếu nhiều block, rule chọn và max lag phải được chốt trong approved config
   trước khi xem kết quả; không chọn block/lag theo hình đẹp. Không suy luận
   stationarity hay model specification chỉ từ đồ thị này.

`docs/results/eda_findings.md` phải liên kết từng claim với figure/table, train
range, counts, phương pháp, timezone, config và run hash. Báo giá trị hoặc câu hỏi
chưa đủ evidence; không hứa U-shape hay seasonality. Trên evidence train, đề xuất
cụ thể để Human xem xét tại Phase 4: causal missing-load handling và max-gap
threshold có lý do/counts; cách flag/handle sensor anomalies mà không sửa raw
truth; contiguous hourly domain cho VAR, endpoints/coverage và alternatives khi
không đủ domain. Các đề xuất chưa phải approved policy; không dùng held-out data
để chọn hoặc đánh giá threshold.

## 4. Dự kiến artifacts, ownership và dependencies

| Path | Trách nhiệm sau khi được duyệt |
|---|---|
| `src/practice_4/analysis/eda.py` | Train-boundary loader/validation và analyses; không consume held-out values. |
| `src/practice_4/visualization/plots.py` | Vẽ từ train-only data/summary đã validate, không tự load canonical hay fit. |
| `tests/test_eda.py` | Synthetic boundary/loader access, DST local profiles, gap lengths/censored edges và deterministic figures. |
| `config/practice_4.json`, `src/practice_4/pipeline.py` | D01 config/approval checks, hashes, dispatcher và run orchestration; không đổi behavior stages cũ. |
| `runs/<run_id>/` | Config/environment snapshots, manifest, tables và figures staging; unique run ID, không overwrite evidence. |
| `outputs/figures/*.png` | Official figures chỉ promote sau validation và Human review theo roadmap; ghi source run/hash, không overwrite ngầm. |
| `docs/results/eda_findings.md` | Findings và D02 proposals với provenance; pending Human review. |
| `docs/logs/D01_<run_id>.md`, `docs/status/current_status.md`, `docs/plans/file_map.csv` | Run evidence, stage state và inventory. |

Figure set dự kiến: missing/gap distribution; extremes/sanity; UTC load overview;
local daily và weekly profiles; load–temperature; correlation heatmap; ACF/PACF.
Lưu train counts/summary tables trong run staging, figure filenames/config cố định,
và trực tiếp inspect mọi hình trước review. Determinism phải được test trên cùng
environment/backend, dữ liệu và config; ghi version/backend/font và hash output,
không hứa byte identity xuyên platform. No random sampling trừ khi seed, method
và phạm vi được duyệt trước. Không cài package trong bước draft này.

Hiện project core khai báo pandas/numpy/jsonschema, chưa khai báo plotting hoặc
ACF/PACF dependency. Trước D01 phải kiểm environment, đề xuất cụ thể versions,
compatibility và timezone database; thiếu dependency hoặc cần cài/thay lock →
dừng và xin approval riêng, không tự cài. Lựa chọn lag, PACF method, contiguous
block rule và bất kỳ binning/sampling nào cần được khóa trong config trước run;
không suy diễn rằng approval draft này tự duyệt version chưa xác định.

## 5. Before-process plan và validation sau approval

1. Xác nhận approval Phase 3/D01, dependencies, config choices và accepted
   predecessor; kiểm bytes/hash C02 và split. Approval cập nhật header Phase 2
   và contract **sau C02 run**, nên hash hiện tại của hai tài liệu khác historical
   input/output hashes trong C02 manifest; không sửa historical manifest. Ghi cả
   current approval reference lẫn run-time hashes, so khớp data bytes với C02.
2. Implement train-only loader, analysis và plotting owners theo mục 2–4; test
   synthetic trước chạy data thật. Fixtures kiểm row 24543 so với 24544, sentinel
   held-out loader access, out-of-train rejection, UTC/Madrid DST spring/fall,
   missing runs nội bộ/biên, no zero-fill, và reproducible figures. Kiểm failure
   khi thiếu input/schema/timezone/dependency, sai hash hoặc timeline.
3. Sau focused tests, chạy D01 bằng run ID mới, lưu artifacts staging, tự inspect
   tables/figures và report actual commands, exit codes, hashes, environment,
   exclusions, limitations và failed runs. Kiểm raw/canonical/split hashes sau
   run; trình Human review findings và proposed D02 policy. Chỉ promote figures
   sau Human review và ghi nguồn/checksum.

Commands dự kiến từ Practice_4 root, **chỉ sau approval và khi dependency/config
đã khóa**; chưa chạy, D01 dispatcher chưa tồn tại:

```powershell
py -3.12 -m pytest tests/test_eda.py
py -3.12 -m practice_4.pipeline --stage D01 --config config/practice_4.json --run-id <unique_id>
git diff --check
```

## 6. Stop conditions và risks

Dừng khi thiếu approval/dependency/tzdata, predecessor hay hash drift, split
schema/boundary/timeline mismatch, bất kỳ held-out record được parse, train-only
test thất bại, raw 133 m/s không thể xác minh train membership trong boundary,
missing/invalid values cần policy chưa duyệt, ACF/PACF thiếu contiguous domain,
figure không thể inspect, hoặc scope/semantics cần mở rộng. Giữ failed-run evidence
và báo Human; không tự đổi split, threshold, lag, policy hay dependency.

Rủi ro chính: raw city extreme có thể bị làm mờ trong proxy mean; DST và partial
days gây lệch sample counts; contiguous-block ACF/PACF có selection bias; U-shape
hoặc weekly pattern có thể không rõ. Correlation và observational weather proxy
không chứng minh causality. Findings phải báo những giới hạn thực tế.

## 7. Approval record

- C01, C02, evaluation contract và Phase 2: **Human APPROVED / COMPLETED
  2026-11-18 via Director review**, theo yêu cầu hiện tại.
- Phase 3 specification / before-process plan: **PENDING HUMAN REVIEW / APPROVAL**.
- D01 execution và acceptance, D02 policy và Phase 4: **chưa được duyệt**.
