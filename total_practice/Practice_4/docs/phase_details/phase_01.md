# Phase 1 — Data Preparation: specification và before-process plan

Trạng thái: **COMPLETED — Human đã duyệt B02 và Phase 1 ngày 2026-11-18**.
Người duyệt: Human; approval reference: tin nhắn `APPROVED` trong cuộc hội thoại
hiện tại, trả lời bản Phase 1 specification. Human đã đóng Phase 0 qua
tin nhắn `Close Phase 0 (Gate A02) & Draft Phase 1 Specification` trong cuộc hội
thoại hiện tại; tin nhắn đó chỉ yêu cầu soạn draft, không duyệt triển khai B01
hoặc B02. Kế hoạch, schema và commands dưới đây đều là đề xuất để review.

Nguồn: [Problem Definition đã chấp nhận](../results/problem_definition.md),
[Phase 0 approval](phase_00.md), [roadmap](../plans/plan_overview.md),
[file map](../plans/file_map.csv), [review findings RV1–RV3](../plans/plan_review.md),
[Time Series rules](../../../../.agents/rules/TIME_SERIES_RULES.md),
[code rules](../../../../.agents/rules/CODE_RULES.md) và
[workflow](../../../../.agents/workflows/WORKFLOW.md).

## 1. Mục tiêu, đầu vào và ranh giới

Phase 1 xác minh provenance, schema và chất lượng raw của nguồn Spain được Human
chọn (B01), sau đó xây dựng canonical hourly data trên bản derived theo policy
được Human duyệt từ audit (B02). Output là raw source evidence bất biến, audit,
canonical dataset và data contract có lineage. Đây không phải EDA quan hệ hay
forecasting: không split, fit scaler, xử lý missing/anomaly, feature engineering,
training, tuning hoặc mở test. Không sửa raw hay tự chuyển nguồn.

| Input | Trạng thái hiện tại |
|---|---|
| Problem definition, A01/A02 approval | Đã được Human chấp nhận; bootstrap bằng hash tài liệu và approval record. |
| Hai CSV từ nguồn Spain | Human đã đặt trong `datasets/raw/`; hash và audit sơ bộ đã ghi, archive/version, quyền sử dụng, units và timestamp semantics nguồn chưa xác minh. |
| Counts và schema preliminary | Chỉ là historical inspection; không dùng làm evidence mới hoặc giả định bất biến. |
| Environment/CLI/ingestion | Chưa có; versions, compatibility và core dependency lock phải được review trước cài đặt. |

## 2. Quy trình và gates

1. **Phase 1 design gate:** Human review scope, ownership, commands, bootstrap,
   manifest schema, dependency setup và stop conditions trong bản này. Trước
   khi cài dependency, cần proposal cụ thể gồm Python, direct/transitive versions,
   platform compatibility, lock strategy và impact, được Human duyệt; không
   coi việc duyệt bản draft này là duyệt các version chưa được nêu.
2. **B01 — raw provenance và audit:** sau các approval tương ứng, lấy archive
   từ nguồn đã chọn theo điều khoản truy cập thực tế; lưu nguyên hai CSV, ghi
   nguồn/version/retrieval/license/checksums, kiểm schema, units/time semantics,
   timestamp, missing và duplicate/coverage. Báo evidence, gaps và lựa chọn
   B02; không tự sửa hoặc treat raw. B01 acceptance cần tests, audit và Human review.
3. **B02 policy gate:** sau B01 audit, đề xuất dedup/city normalization, proxy,
   timezone/DST, hourly join, missing coverage và data contract dựa trên evidence;
   Human duyệt policy cụ thể trước tạo canonical. Mean không trọng số và UTC là
   đề xuất, không phải quyết định. Nếu audit thiếu chứng cứ cần thiết thì dừng.
4. **B02 — canonical:** triển khai policy đã duyệt trên derived copy, validate
   invariants và raw hashes, trình contract/artifacts và limitations để Human
   chấp nhận. Cần Phase 1 acceptance và Phase 2 design/approval riêng trước C01.

## 3. File ownership và thay đổi dự kiến

Paths tương đối `Practice_4/`; chi tiết lifecycle tại file map. Chỉ tạo file
khi stage và gate tương ứng được duyệt; log/manifest không hàm ý run đã xảy ra.

| Stage | Files / owner | Trách nhiệm |
|---|---|---|
| B01 | `pyproject.toml`, `requirements.lock.txt`, `config/practice_4.json` | Core Python package, pinned environment và versioned settings được duyệt; không secrets/absolute machine paths. |
| B01 | `src/practice_4/pipeline.py`, `src/practice_4/data/ingestion.py` | Stage dispatcher/gates; read-only raw CSV và reproducible audit riêng. Không import model backend khi audit. |
| B01 | `datasets/raw/energy_dataset.csv`, `datasets/raw/weather_features.csv`, `datasets/raw/source_manifest.json` | Raw bytes bất biến; source/version/retrieval/license/field/unit/timezone evidence và SHA256. Không sửa dữ liệu nguồn để khớp schema. |
| B01 | `docs/results/data_audit.md`, `tests/test_ingestion.py`, `tests/test_pipeline.py` | Counts/coverage/schema và unresolved evidence; fixtures kiểm malformed input, time/hash, gates/bootstrap. |
| B02 | `src/practice_4/data/integration.py`, `tests/test_integration.py` | Normalization, duplicate validation, proxy và join trên derived data theo policy đã duyệt; fixtures conflict/DST/cardinality. |
| B02 | `datasets/processed/canonical_hourly.csv`, `docs/results/data_contract.md` | Canonical lineage, schema, unit, masks, time semantics, coverage, policy và limitations. |
| Cả hai | `runs/<run_id>/manifest.json`, config/environment snapshots, `docs/logs/<stage_id>_<run_id>.md`, status/map | Provenance stage và actual checks; IDs duy nhất, giữ failed run. Không promote official output nếu gate chưa đạt. |

Không thay source/model của các phase khác hoặc notebook; giữ nguyên file ngoài
scope. README ownership có thể cập nhật khi file/command thực sự tồn tại.

## 4. B01 bootstrap, environment và manifest — đề xuất

**RV1:** predecessor của run B01 đầu tiên là Phase 0 acceptance record thật,
hash `docs/results/problem_definition.md` tại thời điểm chạy, Phase 1/B01
approval và config hash đã duyệt. A02 là documentation-only, không có run
manifest; không yêu cầu tạo giả. CLI reject thiếu approval reference, hash
không khớp, unknown stage, predecessor không hợp lệ hoặc input drift. Tests dùng
fixtures cho accepted/rejected bootstrap; không tự ghi `approved=true` để bypass.

**RV2:** schema version `1` đề xuất cho `runs/<run_id>/manifest.json`:

| Key | Kiểu / invariant |
|---|---|
| `schema_version` | string `"1"`; reject version không hỗ trợ. |
| `run_id`, `stage_id`, `status` | non-empty strings; run ID duy nhất, stage `B01` hoặc `B02`; status phản ánh thực tế. |
| `started_at_utc`, `finished_at_utc` | ISO 8601 UTC strings; `finished_at_utc` nullable khi chưa kết thúc. |
| `approval_refs` | object gồm references cho Phase 0, Phase 1 và stage/policy áp dụng; không fabricated. |
| `inputs` | array objects `path`, `sha256`; file có thật tại thời điểm hash; B01 bao gồm problem definition và raw inputs khi có. |
| `config_sha256`, `environment` | config hash; environment object gồm Python/platform và core package versions thực tế; không secrets. |
| `outputs` | array objects `path`, `sha256` cho artifacts đã tạo; empty nếu failure trước output. Manifest không tự hash chính nó. |
| `checks`, `limitations` | array của check name/status/evidence và array strings; failure/unknown được ghi rõ, không suy thành pass. |

Fields bắt buộc trừ `finished_at_utc` nullable như trên; object/array rỗng chỉ
được dùng khi thực sự chưa có dữ liệu và phải có limitation. Cần schema validator,
missing/invalid/hash-drift fixtures và lưu manifest kể cả failed run khi có thể.
Config/environment snapshots phải khớp manifest; atomic creation/unique IDs tránh
ghi đè run. Source manifest cũng cần actual URL, archive/version, retrieval UTC,
license evidence, file hash, schema, units, time semantics và unresolved fields;
không suy đoán license/unit thiếu bằng tên cột.

**RV3:** B01 chỉ đề xuất core dependencies cho ingestion/audit/tests. Trước cài
đặt, lập exact versions/lock và compatibility evidence cho Python, OS và core
packages; Human duyệt proposal đó. XGBoost/LSTM backends là dependency groups
chờ thiết kế và phê duyệt G01/G02, không cài ở B01. Mọi lock revision về sau cần
approval, compatibility smoke và đánh giá invalidation artifacts; không sửa âm
thầm. Không khẳng định version cụ thể đã tương thích khi chưa kiểm.

## 5. B01 — before-process plan và validation

1. Xác nhận approvals, bootstrap hash và permissions truy cập nguồn; đưa proposal
   environment cụ thể để duyệt. Nếu license/access hoặc versions chưa rõ thì
   dừng phần phụ thuộc, ghi evidence và không bypass access control.
2. Sau approval, tạo core environment/config/CLI/ingestion và fixtures theo
   owner; chạy từng kiểm tra và sửa trong scope đã duyệt. Lấy archive đúng nguồn,
   giữ nguyên raw bytes và metadata; không ghi đè raw nếu đã tồn tại khác hash.
3. Audit raw read-only: counts, schema/types, date range, parsing, timezone/DST,
   sort order, gaps/frequency, duplicate timestamps/city-hour, missing/invalid
   values, unit và coverage evidence. Không dựa vào historical counts, không
   phân tích relationships/held-out distributions để chọn treatment.
4. Lưu source manifest, `data_audit.md`, run manifest, config/environment và
   stage log; so sánh hashes raw trước/sau. Báo các vấn đề và alternatives cho
   B02, không chọn policy bằng cách tự repair raw.

Sau khi source/config/tests tồn tại và environment đã duyệt, dự kiến chạy từ
`Practice_4/` trong clean env: `python -m pip install -r requirements.lock.txt`,
`python -m pip install --no-deps -e .`, `python -m pytest tests/test_ingestion.py
tests/test_pipeline.py`, và `python -m practice_4.pipeline --stage B01 --config
config/practice_4.json --run-id <unique_id>`. Đây là proposed interface, chưa
chạy; command acquisition và exact platform/env setup phải được xác định từ
source access và environment proposal. Inspect audit/manifest và exit codes;
schema/unit/license/availability thiếu thì ghi chưa xác minh và chặn B02.

## 6. B02 — before-process plan và validation

Sau accepted B01, trình evidence và alternatives về: city identity/normalization;
weather duplicate groups giống hay xung đột; coverage; timezone/DST parsing;
proxy (unweighted, weighted hoặc city representative) và giới hạn; join keys,
cardinality, missing timestamps/load/weather. Human duyệt policy trước integration.
Không tự chọn first row/mean conflicting duplicates hoặc fill missing.

Sau policy approval, xây dựng derived canonical và data contract. Kiểm fixture
duplicate consistent/conflicting, city-hour join cardinality, DST transitions,
gaps và coverage; kiểm actual output sorted/unique hourly UTC nếu UTC được duyệt,
đếm rows trước/sau join và preserve raw observed load/missing mask. Thiếu một
giờ hoặc coverage không đạt policy thì fail, không tự thêm/fill/drop để pass.
Ghi units, source/canonical hashes, lineage, decisions và limitations; tính raw
hash trước/sau. Dự kiến `python -m pytest tests/test_integration.py` rồi
`python -m practice_4.pipeline --stage B02 --config config/practice_4.json
--run-id <unique_id>` trong environment đã duyệt. Inspect output/contract,
run manifest, log và `git diff --check`; trình Human review.

## 7. Acceptance, risks và stop conditions

**B01:** source/version/license/unit/time evidence đủ cho B02, audit có thể tái
lập, raw không đổi, core install/import/test và bootstrap fixtures pass, actual
counts/hash/log/manifest có thật; không tạo canonical hoặc treatment. Nếu không
thể xác minh một điều kiện, báo partial audit và chờ Human, không tuyên bố đạt.

**B02:** policy được duyệt trước build; contract và canonical khớp policy,
time/join/duplicate/coverage/mask tests pass, raw hashes không đổi, output và
lineage được inspect, Human chấp nhận Phase 1. Tính đại diện national weather
proxy vẫn là limitation, không kết luận quan hệ nhân quả.

Dừng khi thiếu approval, license/access/units/time semantics không rõ, hash
drift, schema bất ngờ, duplicate conflict hoặc thiếu coverage chưa có policy,
join nhân dòng, dependency mới chưa duyệt, validation fail chưa giải thích, hay
scope phải mở rộng. Không silently đổi source, treatment hoặc thresholds; giữ
failed evidence, xử lý repeated failures theo repository rules. Nếu không thể
đáp ứng, trình Human phương án và ảnh hưởng trước khi tiếp tục.

## 8. Approval record

- Phase 0 / A02 acceptance: Human, 2026-11-17, tin nhắn `Close Phase 0 (Gate
  A02) & Draft Phase 1 Specification` trong cuộc hội thoại hiện tại.
- Phase 1 specification/B01: **Human duyệt 2026-11-17**, tin nhắn `APPROVED`
  trong cuộc hội thoại hiện tại, trả lời bản specification.
- Human yêu cầu dùng môi trường có sẵn, Python 3.12 recommended, và cho biết đã
  đặt hai CSV trong `datasets/raw/` (tin nhắn hiện tại, 2026-11-17). Không cần
  cài dependency để làm inspection read-only; yêu cầu này không chứng minh clean
  install hoặc các tests đã pass.
- 2026-11-18 Human chỉ định interpreter Python 3.12 và xác nhận nguồn Kaggle,
  version 1, CC0, ngày tải 2026-11-17; xem `datasets/raw/source_manifest.json`.
- 2026-11-18 Human yêu cầu hoàn tất B01 bằng system Python 3.12, không dùng
  virtualenv. Các kiểm tra clean-environment vẫn chưa có bằng chứng và không
  được coi là pass chỉ từ yêu cầu này.
- 2026-11-18 Human yêu cầu `Unblock & Complete Stage B01 (Provenance, Pipeline,
  Tests & Audit)` và xác nhận provenance, units, offsets/DST; chấp thuận core
  dependencies hiện có và editable install system Python. B01 acceptance và B02
  policy vẫn chờ Human review.
- Core environment/dependency proposal: xem [draft](../plans/b01_core_environment.md);
  **chưa giải quyết dependency closure, chưa duyệt**.
- B01 run `20261118_system312_01`: **Human APPROVED 2026-11-18**, theo yêu cầu
  `Close Gate B01 & Execute Stage B02 (Canonical Dataset & Data Contract)`.
- B02 policy: **Human APPROVED 2026-11-18** cùng tin nhắn trên: strip city,
  validate 5-city set, dedup chỉ khi weather fields nhất quán, mean không trọng
  số, UTC hourly 1:1, giữ 36 missing load và raw extremes.
- B02 run `20261118_system312_b02_01`, canonical dataset, data contract và
  Phase 1: **Human APPROVED / COMPLETED 2026-11-18**, theo tin nhắn `Close Phase 1
  (Gate B02) & Draft Phase 2 Specification` trong cuộc hội thoại hiện tại.
- B02 run manifest lưu hash của tài liệu này và data contract tại thời điểm run;
  việc ghi approval sau run làm hai file hiện tại khác hash lịch sử. Không sửa
  manifest để giả rằng approval đã tồn tại lúc run.
