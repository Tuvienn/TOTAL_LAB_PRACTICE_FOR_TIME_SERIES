# Phase 5 — Feature engineering and aligned model inputs (E01–E02)

Status: **SPECIFICATION DRAFT — PENDING HUMAN REVIEW**. Phase 5 drafting is **IN_PROGRESS**. Human authorized documentation only on 2026-11-18 via Director review.

Sources: [roadmap, Cụm E and §4.1](../plans/plan_overview.md), [file map](../plans/file_map.csv), [C02 evaluation contract](../results/evaluation_contract.md), [split manifest](../../datasets/processed/split_manifest.json), [Phase 4 approval](phase_04.md), [D02 audit](../results/preprocessing_audit.md), and [accepted D02 run manifest](../../runs/20261118_system312_d02_01/manifest.json).

## 1. Scope and input contract

Use the approved D02 prepared prefix of 29,803 hourly UTC records, with train rows 0–24,543 and validation rows 24,544–29,802. Row IDs are zero based. Verify the prepared CSV and scaler SHA256 against the D02 manifest and the split file and semantic hashes against D02 lineage. Validate the prepared schema, chronological hourly index, endpoints, mask/truth agreement and expected counts. Reject malformed or extra records without parsing beyond the permitted prefix. Use the fixed D02 scaler and Streaming LOCF-1 results. E01/E02 do not refit, clip, fill or repair data. Future test streaming belongs to H01 under separate authorization.

## 2. E01 — Feature dictionary (R01, R04, Q07)

Origin `t` is the end of the last revealed hour. Predict raw `load(t+1)` in MW. In this lab all four input measurements are assumed available by the end of their hour. Form the vector `X(s)` from D02 columns `load_input_scaled`, `temp_scaled`, `humidity_scaled`, `wind_speed_scaled`, in that order, corresponding to load, temperature, humidity and wind speed. The label is the original observed load, independent of the working load used as input.

| Feature or view | Definition and order |
|---|---|
| LSTM | `[X(t-23), ..., X(t)]` with shape `(N, 24, 4)`, oldest first. |
| Flat lags | The same 24 × 4 window, time-major, with zero-based column `4*j+k` for hour `t-23+j` and variable `k`. Name columns `lag{h:02d}_{variable}`, ordered by `h=23,...,0` and then by `load,temperature,humidity,wind_speed`. Total 96. |
| XGBoost | Append `mean6h`, `std24h`, `trend24h` in that order to the flat lags. All derive from the fixed train-scaled working load. `mean6h` uses `t-5..t` inclusive, `std24h` uses `t-23..t` inclusive with population `ddof=0`, and `trend24h = load_input_scaled(t) - load_input_scaled(t-24)`. Total 99. |

The latest feature source is `t`. Future weather at `t+1` is prohibited. Both views share origin eligibility, while XGBoost uses one older load observation for the trend. The dictionary must record exact names, order, units, source columns, and offsets.

In `tests/test_features.py`, hand-check a synthetic ramp with row `i` equal to `[i, 100+i, 200+i, 300+i]`. For origin row 24, the sequence starts at `[1,101,201,301]` and ends at `[24,124,224,324]`. The flat view starts and ends with the same blocks, derived values are `21.5`, `sqrt(575/12)`, and `24`, and the target must come from row 25's distinct raw load. Perturb target-hour weather and future rows and verify inputs at that origin remain identical. Test the eligibility and split boundaries in §3 with synthetic fixtures.

For F02, extract a separate `(9271, 4)` matrix of scaled levels in the same variable order from the inclusive observed train block `2016-09-28T08:00:00+00:00` through `2017-10-19T14:00:00+00:00` (prepared rows 15,273–24,543). Verify hourly continuity, observed raw load, equality of working and raw load, and finite scaled levels throughout. Preserve the approved block as a single segment. Document the 15,241 earlier observed hours excluded and the resulting representativeness limitation. VAR fitting and adequacy belong to F02. This training matrix is separate from the common supervised sample axis.

## 3. E02 — Common origins and aligned arrays

For target row `k`, origin is row `k-1` and common context is rows `k-25..k-1` inclusive. Targets 0–24 are initial warm-up and are reported separately from candidate exclusions. Emit one origin record for each candidate target 25–29,802 (24,519 train candidates and 5,259 validation candidates before masks). Split membership follows the target timestamp. The first validation target uses the previous train hour as its origin, and any validation history admitted into context must already be revealed at that origin.

Apply a single eligibility rule across baseline, VAR, XGBoost and LSTM comparisons. First classify a missing raw target (`load_observed=False`) as `missing_truth`. Among observed targets, classify any nonfinite value in the 25 × 4 scaled context as `invalid_context`, even in row `t-24`. All remaining targets are `eligible`. An observed target with nonfinite truth or a mask/truth mismatch is a contract error. Physical and percentile flags do not change this rule. Preserve raw truth in MW. The same eligible origin set applies across models even if a model consumes fewer rows. Per split, `n_considered = n_missing_excluded + n_input_excluded + n_eligible`; downstream scoring accounts for eligible origins under C02.

### Phase 5 RV2 schema v1 — `datasets/processed/origin_manifest.csv`

UTF-8, with this exact ordered header and one record per candidate, ordered by increasing `target_row`.

| Column | Type and constraint |
|---|---|
| `schema_version` | Literal `1` on each row. |
| `origin_row`, `target_row`, `context_start_row` | Nonnegative decimal integers. `target_row=origin_row+1`, `context_start_row=origin_row-24`. |
| `origin_timestamp_utc`, `target_timestamp_utc` | ISO 8601 UTC, `YYYY-MM-DDTHH:MM:SS+00:00`, sourced from prepared rows. Exactly one hour apart. |
| `split` | `train` or `validation`, determined by target. |
| `load_observed`, `context_finite`, `eligible` | Boolean literals `True` or `False`. Context finiteness is recorded even for missing truth. |
| `exclusion_reason` | Empty for eligible rows, otherwise `missing_truth` or `invalid_context` in that priority order. |
| `y_true_mw` | Round-trip float64 in original MW when observed, including invalid-context rows. Empty for missing truth. |
| `sample_index` | Zero-based consecutive integer for eligible rows only. Empty for exclusions. |

Reject missing, reordered, duplicate or unknown columns, duplicate row/timestamp keys, missing candidates, inconsistent masks or sample indices, a test split or a target beyond row 29,802. No warm-up rows appear in the CSV.

### Phase 5 RV2 schema v1 — `datasets/processed/model_inputs.npz`

Use the exact keys below. Arrays must load with `allow_pickle=False`, use the stated dtype and shape, and contain finite values for floating-point keys. `N` is the sum of eligible train and validation rows. Index `i` identifies CSV `sample_index=i` across all supervised arrays.

| Key | dtype | Shape | Contract |
|---|---|---|---|
| `schema_version` | `uint8` | scalar | Value 1. |
| `target_row` | `int64` | `(N,)` | Strictly increasing prepared target row IDs. Join to CSV for split and UTC timestamps. |
| `x_lstm` | `float64` | `(N,24,4)` | Sequence order from §2. |
| `x_flat` | `float64` | `(N,96)` | Exact time-major reshape of `x_lstm`. |
| `x_xgb` | `float64` | `(N,99)` | First 96 columns match `x_flat`; remaining three follow §2. |
| `y_true_mw` | `float64` | `(N,)` | Exact observed raw truth, identical to CSV and source. |
| `var_row` | `int64` | `(9271,)` | Consecutive prepared row IDs for the approved VAR block. |
| `var_train_levels` | `float64` | `(9271,4)` | Observed train block from §2; independently indexed by `var_row`. |

Reject object arrays, extra or duplicate keys, dtype/shape mismatches, nonfinite data, empty eligible splits and any alignment failure. Validate every target-to-sample mapping and source lineage before promotion. This schema addresses RV2 for E02 origin/input artifacts subject to Human approval. The accepted C02 prediction and evaluation manifest contract still governs H01.

## 4. Deliverables and ownership

| Stage | Exact path | Planned responsibility |
|---|---|---|
| E01 | `src/practice_4/data/features.py` | Shared causal slicing, derived features and ordered feature names. |
| E01 | `tests/test_features.py` | Ramp, leakage, split, eligibility, schema and VAR fixtures. E02 may extend the same file for round-trip checks. |
| E01 | `docs/results/feature_dictionary.md` | Feature names, order and hand-worked evidence. |
| E02 | `src/practice_4/data/features.py` | Shared origin eligibility, shape checks and alignment logic. |
| E02 | `config/practice_4.json`, `src/practice_4/pipeline.py` | Stage dispatch, approval gates, provenance and output orchestration for E01/E02. E01 wiring may be added when E01 is authorized. |
| E02 | `datasets/processed/origin_manifest.csv`, `datasets/processed/model_inputs.npz` | Validated train and validation artifacts. |
| E02 | `docs/results/alignment_audit.md` | Schema versions, train/validation raw ratios, warm-up and candidate/eligible/excluded counts, exclusions by reason, timestamps, array shapes/dtypes, feature order, VAR endpoints and limitation. Record input/output SHA256, boundary and label checks, commands, results, and pending approval. |
| E01/E02 | `runs/<run_id>/manifest.json`, `runs/<run_id>/config.json`, `runs/<run_id>/environment.json`, `docs/logs/E01_<run_id>.md` or `docs/logs/E02_<run_id>.md` | Fresh run evidence and command outcomes. Stage E01 generates the dictionary for review. Stage E02 stages CSV/NPZ/audit in `runs/<run_id>/artifacts/` before validation and promotion. |
| E01/E02 | `docs/phase_details/phase_05.md`, `docs/plans/file_map.csv`, `docs/status/current_status.md` | Record scope, acceptance, and evidence references. |

## 5. Before-process plan and validation

1. After Human approves this specification and authorizes E01, verify D02 approval, artifact hashes and UTC/schema boundaries. Implement the shared feature owner and dictionary. Run synthetic checks before executing the E01 command. Present the dictionary and fixture evidence for Human review.
2. After Human accepts E01 and authorizes E02, implement alignment and serialization. Verify synthetic fixtures for row-25 warm-up, cross-split carry, target-missing precedence, older context NaNs, wrong timestamp/schema rejection, and VAR block limits.
3. Run E02 with a fresh ID. Reload staged outputs, compare every eligible index, target, lag view and raw label against the permitted source, verify counts and hashes, and only then promote. Present the audit and artifact hashes for Human acceptance before downstream modeling.

Planned commands from the Practice 4 root after the respective gates. The E01/E02 dispatchers and feature tests are future deliverables.

```powershell
py -3.12 -m pytest tests/test_features.py
py -3.12 -m pytest tests/test_preprocessing.py tests/test_splitting.py tests/test_walk_forward.py tests/test_metrics.py
py -3.12 -m practice_4.pipeline --stage E01 --config config/practice_4.json --run-id <unique_e01_run_id>
py -3.12 -m practice_4.pipeline --stage E02 --config config/practice_4.json --run-id <unique_e02_run_id>
git status --short
git diff --check
```

## 6. Stop conditions

Stop for missing stage approval, inaccessible or changed input lineage, unexpected schema/time/row/mask drift, test access, any source timestamp after origin, failed fixture or round-trip, empty eligible split, count mismatch, unapproved policy/dependency change, or output collision. If F02 later needs more than 25 hours of common context, return to C02/E02 for approval and rebuild eligibility before dependent fits.

## 7. Approval record

- D02 run `20261118_system312_d02_01`, prepared data, preprocessing audit and Phase 4 completion: **Human APPROVED / COMPLETED, 2026-11-18 via Director review**.
- Phase 5 specification and before-process plan: **PENDING HUMAN APPROVAL**.
- E01 implementation, E02 implementation and Phase 5 RV2 schema acceptance await explicit Human authorization. H01 test opening remains a separate gate.
