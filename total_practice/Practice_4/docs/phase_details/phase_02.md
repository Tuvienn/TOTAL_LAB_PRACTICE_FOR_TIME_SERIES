# Phase 2 — Temporal Split và Evaluation Contract

Trạng thái: **APPROVED / COMPLETED**, 2026-11-18. Human duyệt C02, evaluation
contract và đóng Phase 2 qua Director review.

Nguồn: [Phase 1 approval](phase_01.md), [data contract](../results/data_contract.md),
[roadmap mục 3–4](../plans/plan_overview.md), [file map](../plans/file_map.csv),
[review finding RV2](../plans/plan_review.md),
[Time Series rules](../../../../.agents/rules/TIME_SERIES_RULES.md) và
[workflow](../../../../.agents/workflows/WORKFLOW.md).

## 1. Scope, ownership và gates

- C01: định nghĩa và kiểm tra chronological membership trên row timeline
  canonical; tạo split manifest, không tạo model windows hoặc xử lý values.
- C02: định nghĩa/kiểm thử evaluation protocol, metrics và schema; trình Human
  duyệt evaluation contract trước modeling. Synthetic fixtures không dùng
  target test thật. C02 không mở test scoring hoặc materialize test origins.
- Bên ngoài Phase 2: EDA quan hệ, causal treatment, scaler fit, model-ready
  arrays, fit/model selection và test scoring. Không sửa raw hoặc canonical.
- Mỗi stage phải có predecessor acceptance, hash/approval check, focused tests,
  run manifest/log và Human review. C02 bắt đầu sau khi C01 đạt gate; Phase 3
  cần Phase 2 acceptance và Phase 3 specification/approval riêng.

| Stage | Files dự kiến / owner | Mục đích |
|---|---|---|
| C01 | `src/practice_4/data/splitting.py`, `tests/test_splitting.py` | Timestamp-only partition, rounding, ordering và boundary fixtures. |
| C01 | `datasets/processed/split_manifest.json` | Counts, inclusive UTC boundaries, canonical hash và split hash. |
| C02 | `src/practice_4/analysis/metrics.py`, `tests/test_metrics.py` | Original-scale metrics, eligibility accounting, hand-calculated fixtures. |
| C02 | `src/practice_4/analysis/walk_forward.py`, `tests/test_walk_forward.py` | Predict-before-reveal control, synthetic streaming/causality fixtures. |
| C02 | `docs/results/evaluation_contract.md` | Protocol và artifact schemas được Human khóa trước modeling. |
| C01–C02 | `config/practice_4.json`, `src/practice_4/pipeline.py` | Chỉ section/schema/gate và dispatcher cần thiết; giữ B01/B02 behavior. |
| C01–C02 | `runs/<run_id>/`, `docs/logs/<stage_id>_<run_id>.md`, `docs/status/current_status.md`, `docs/plans/file_map.csv` | Snapshots, hashes, actual checks, approval references và inventory. |

`outputs/results/predictions.csv` và `outputs/results/evaluation_manifest.json`
thuộc **H01**, không tạo tại C02. C02 chỉ soạn/kiểm schema bằng synthetic data.

## 2. C01 — Temporal partition (Q04)

Input: canonical đã được Human chấp nhận, 35.064 UTC hourly rows;
SHA256 tại lúc soạn `7122e873708d3297e38316a5d29a08236c516fcdf20327e7724edc1d31a83045`.
Phải đối chiếu lại với accepted B02 manifest và bytes hiện có tại execution;
hash drift → dừng. Dùng **chỉ timestamp/counts**, không quan sát phân phối
held-out target để chọn split. Chia row timeline trước windowing hoặc drop rows:

| Split | Count | Inclusive UTC start | Inclusive UTC end |
|---|---:|---|---|
| train | floor(0,70 × 35.064) = 24.544 | 2014-12-31 23:00:00+00:00 | 2017-10-19 14:00:00+00:00 |
| validation | floor(0,15 × 35.064) = 5.259 | 2017-10-19 15:00:00+00:00 | 2018-05-26 17:00:00+00:00 |
| test | N − train − validation = 5.261 | 2018-05-26 18:00:00+00:00 | 2018-12-31 22:00:00+00:00 |

Các con số trên là tính toán thiết kế từ N/start đã chấp nhận, **không phải
split đã chạy**. Khi execution phải validate sorted, unique, contiguous hourly,
counts cộng N, adjacent boundaries và không overlap/gap; mismatch → dừng.
Target timestamp `t+1` quyết định membership; input history `<= t` có thể qua
boundary một cách causal, không dùng target tương lai hoặc learned statistics
fit ngoài training. Tỷ lệ row khác sample counts sau warm-up/masks; báo cả hai
khi samples được tạo ở phase sở hữu.

### Split manifest v1 — đề xuất để khóa tại C01

JSON UTF-8, required keys, không thêm semantics ngầm:

| Key | Type và invariant |
|---|---|
| `schema_version` | string `"1"` |
| `canonical_path`, `canonical_sha256` | relative string path và lowercase SHA256 của canonical bytes đã kiểm |
| `total_rows`, `frequency`, `timezone` | integer 35064, string `"1h"`, string `"UTC"` |
| `splits` | object bắt buộc `train`, `validation`, `test`; mỗi object có integer `row_count`, `start_row`, `end_row` zero-based inclusive, string `start_utc`, `end_utc` ISO 8601 UTC inclusive |
| `split_sha256` | lowercase SHA256 của canonical JSON UTF-8 cho toàn object **không có `split_sha256`**, `sort_keys=True`, `separators=(',', ':')`, `ensure_ascii=False`, không newline |

All keys bắt buộc, không null; rows contiguous, `end_row-start_row+1=row_count`,
counts cộng total và timestamp boundaries khớp input. Dùng `split_sha256` như
hash semantic split; file SHA256 riêng được run manifest ghi theo bytes thực tế.
Không tự đưa hash của object chứa chính hash vào phép tính.

## 3. C02 — Eligibility, walk-forward và metrics (Q04/Q05)

### Origin và common mask

Đề xuất warm-up chung **25 raw hourly rows** kết thúc ở origin `t` (bao gồm
`t-24` và `t`), cho trend lag24 và VAR `d<=1,p<=24`; LSTM vẫn nhận 24 rows.
Target là `t+1`; không giả exact feature parity giữa models. Nếu F02 chứng minh
cần history khác, dừng và xin duyệt contract/manifest rebuild trước model fit.
Historic context có thể qua split boundary nếu mọi source timestamp `<=t`.

Common eligible scoring origin = target raw `load_observed == True` tại `t+1`
**và** đủ valid causal input context theo policy được duyệt tại D02. Missing
truth và invalid context có reason, không biến imputed input thành truth. Rule
mask được xác định trước scoring, không theo model errors; model failure hoặc
non-finite forecast trên origin hợp lệ → **fail run**, không silently drop hay
đổi mask. Zero eligible points → fail. D02 chưa khóa max-gap/treatment nên
eligibility ở đây là contract dự kiến; E02 materialize train/validation origins
sau D02, test origin list chỉ sau H01 authorization.

### Walk-forward

Fixed model weights và fixed train-fitted transforms; không refit train+val trước
test. Với mỗi origin theo thứ tự: lấy history đã reveal, **predict → score nếu
raw target observed → reveal ground truth** cho bước tiếp theo. Nếu target
missing, không score và reveal missing theo causal policy; không đưa forecast
thành observed truth. Context không hợp lệ theo policy → ghi input exclusion;
không dùng giá trị tương lai để sửa. Weather/load cuối giờ `t` available là giả
định lab cần báo, không phải production guarantee. Validation dùng cùng history
semantics; không tạo test predictions/tensors/origin list trước H01.

### Metrics và selection

Trên cùng scored pairs, original MW scale: `MAE = mean(abs(y-yhat))`;
`RMSE = sqrt(mean((y-yhat)^2))`; `MAPE = 100*mean(abs((y-yhat)/y))` chỉ với
`y != 0`. Không hidden epsilon; nếu mọi scored `y=0` thì MAPE = null/NA kèm lý
do. MAE/RMSE/MAPE không tính imputed truth; report sensitivity gần zero mà
không đổi threshold sau test.

Quy tắc counts để tránh double counting: `n_missing_excluded` đếm target raw
thiếu trước; trong các target observed, `n_input_excluded` đếm context invalid;
`n_scored` đếm target observed và context valid; `n_zero_excluded` là **subset
của n_scored** loại khỏi mẫu MAPE, không cộng lại thành tổng origin. Báo thêm
`n_considered = n_missing_excluded + n_input_excluded + n_scored`; model errors
trên eligible origin gây fail, không tăng exclusion. Counts dùng chung giữa
models; no eligible points → fail.

Selection chỉ trên validation: primary RMSE; chọn nhóm candidates có
`RMSE - min(RMSE) <= 1e-6 MW`, sau đó MAE nhỏ nhất; nếu vẫn hòa, model order
`persistence → seasonal24 → VAR → XGB → LSTM`; trials cùng model hòa ưu tiên
ít parameters/trees/epochs hơn rồi `trial_id` nhỏ hơn. Việc so với minimum
RMSE tránh tie chain phụ thuộc thứ tự duyệt. Báo test ranking mô tả, không dùng
test để đổi configuration. Ties, model budget và trial-count definition cần
được Human duyệt trong evaluation contract trước fit.

## 4. Evaluation artifact schema v1 — RV2 proposal

Schema này đã được Human duyệt tại gate C02; RV2 đóng ngày 2026-11-18.
H01 mới được tạo artifacts thật. UTC timestamps có offset `Z`
hoặc `+00:00`; numeric metrics/predictions phải finite, units MW. Schema validators
phải reject unknown schema versions, missing required fields và duplicate keys.

### `outputs/results/predictions.csv`

Mỗi row là forecast hợp lệ của một model cho một origin/target; required header
và types:

| Column | Type / null semantics |
|---|---|
| `schema_version` | string `1`, non-null |
| `model` | non-empty string, non-null; tên theo locked model registry |
| `origin`, `target_timestamp` | ISO 8601 UTC timestamps, non-null; target = origin + 1h |
| `y_true_mw`, `y_pred_mw` | finite float, non-null; truth là raw observed; prediction không finite → fail |
| `split` | string `test` cho H01 official output; non-null |
| `run_id` | non-empty string, non-null, tham chiếu evaluation manifest |

Unique key `(model, origin, target_timestamp)`; mỗi model có cùng origin/target
set và truth. CSV **không chứa excluded origins**; chúng được đếm trong manifest
và lưu origin/eligibility evidence riêng theo contract E02/H01. Không dùng null
forecast để biểu diễn lỗi. Header-only/zero scored → fail.

### `outputs/results/evaluation_manifest.json`

JSON object, required keys và types; unknown keys chỉ cho phép nếu schema version
được cập nhật trước execution:

| Key | Type / null semantics |
|---|---|
| `schema_version`, `run_id`, `stage_id` | strings; lần lượt `"1"`, non-empty, `"H01"`; non-null |
| `prediction_file` | object `{path, sha256}`: relative path và lowercase SHA256 của CSV bytes; non-null |
| `input_hashes` | object non-null chứa `canonical_sha256`, `split_sha256`, `config_sha256`, `preprocessor_sha256`, `eligibility_sha256`, `source_manifest_sha256`; mỗi value lowercase SHA256 |
| `model_hashes` | object non-null; mỗi required model có artifact hash lowercase SHA256; baselines không có artifact thì khóa version/config hash, không dùng null |
| `approval_refs` | object non-null: `evaluation_contract`, `model_locks`, `test_opening`; non-empty references thật |
| `counts` | object non-null integer >=0: `n_considered`, `n_scored`, `n_zero_excluded`, `n_missing_excluded`, `n_input_excluded`; tuân invariant mục 3 |
| `metrics` | object theo model với non-null finite `mae_mw`, `rmse_mw`; `mape_percent` finite hoặc null **chỉ** khi mọi scored truth bằng zero; `mape_null_reason` null khi MAPE finite, non-empty string khi null |
| `protocol` | object non-null `forecast_horizon_hours: 1`, `weights: "fixed"`, `transformations: "train_fitted_fixed"`, `update_order: "predict_score_reveal"` |
| `created_at_utc`, `limitations` | ISO UTC timestamp non-null; array strings, có thể rỗng nếu không còn limitation được xác định |

H01 cần lưu riêng eligibility/origin evidence với exclusions, nguyên tắc uniqueness
và mask version được C02/E02 chốt; không bịa exclusion details từ CSV prediction.
Manifest hash fields gắn exact accepted artifacts; không trộn versions. Kiểm CSV
uniqueness, same truth/origins, count conservation, checksums và null rules.

## 5. Before-process plan và validation

### C01

1. Kiểm Human approval, accepted B02 manifest/canonical hash, config version;
   chú ý header/approval record thay đổi sau B02 nên hash hai tài liệu hiện tại
   khác hash lịch sử trong B02 manifest. Kiểm canonical bytes theo B02 output
   hash, không âm thầm sửa historical manifest.
2. Tạo `data/splitting.py` và synthetic tests cho rounding (`floor` chính xác),
   tiny timelines, invalid/duplicate/gapped timestamps, target membership,
   inclusive boundaries và cross-boundary history. Không materialize window.
3. Tạo split manifest v1 theo schema, xác minh self-hash convention, timestamp
   boundaries/counts bằng independent inspection, raw/canonical SHA256 trước/sau.
   Ghi actual run/config/environment/approval/log, update status/map; trình
   Human review trước C02.

### C02

1. Sau C01 acceptance, tạo metrics/walk-forward theo approved schema/protocol;
   synthetic hand-check: `y=[1,2]`, `yhat=[2,0]` → MAE 1,5, RMSE sqrt(2,5),
   MAPE 100%; zero truth exclusion, all-zero MAPE null, missing, invalid context,
   count conservation và empty scored fail.
2. Test future mutation không đổi earlier prediction; explicit access gate chứng
   minh prediction xảy ra trước reveal; fixed state không bị refit, missing truth
   và invalid history được tính đúng, nonfinite/model failure fail thay vì drop.
   Test schema: missing fields/types, null semantics, duplicate key, hash drift,
   mismatched model origins/truth, test opening gate và unknown schema version.
3. Viết `evaluation_contract.md` bao gồm Q04/Q05/RV2; Human duyệt trước fit.
   Không materialize real test origins, tensors hoặc predictions tại C02.

Dự kiến từ Practice_4 root, system Python 3.12 đã dùng trong Phase 1, sau khi
source tồn tại và gate được duyệt:

```powershell
python -m pytest tests/test_splitting.py
python -m practice_4.pipeline --stage C01 --config config/practice_4.json --run-id <unique_id>
python -m pytest tests/test_metrics.py tests/test_walk_forward.py
python -m practice_4.pipeline --stage C02 --config config/practice_4.json --run-id <unique_id>
git diff --check
```

Commands chỉ là dự kiến, chưa chạy; C02 commands chỉ sau accepted C01. Ghi
exit codes, actual inputs/output hashes, config, environment, approval reference,
logs và failed runs. Dùng synthetic data cho test fixtures; không đọc test thật
ngoài timestamp/count để C01 xác định row boundaries. Verify raw/canonical hashes
trước/sau, inspect outputs và run manifest, kiểm inventory/map.

## 6. Stop conditions, risks và approval

Dừng khi approval/predecessor thiếu, canonical hash/schema/timeline drift, row
counts/boundaries không khớp, nguồn tương lai xuất hiện trong feature/context,
model failure bị drop, nonfinite forecast, schema/count/hash inconsistency,
unexpected test failure hoặc scope phải mở rộng. Không chọn policy thiếu evidence,
không tự mở test hay thay threshold. Báo risks, alternatives và Human direction.
Baseline-first, raw truth immutability và model-lock/test gate tiếp tục áp dụng.

- Phase 1 / B02 acceptance: **Human APPROVED 2026-11-18**, tin nhắn `Close Phase 1
  (Gate B02) & Draft Phase 2 Specification` trong cuộc hội thoại hiện tại.
- Phase 2 specification / before-process plan: **Human APPROVED 2026-11-18 via Director review**, chỉ C01.
- C01 run `20261118_system312_c01_01` và split manifest: **Human APPROVED 2026-11-18 via Director review**; C01 COMPLETED.
- C02 run `20261118_system312_c02_01`, evaluation contract và Phase 2:
  **Human APPROVED / COMPLETED 2026-11-18 via Director review**; RV2 đóng.
