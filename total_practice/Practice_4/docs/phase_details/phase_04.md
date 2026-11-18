# Phase 4 — Causal preprocessing and scaling (D02)

Status: **SPECIFICATION DRAFT — PENDING HUMAN APPROVAL**, 2026-11-18. D01 run `20261118_system312_d01_01`, findings and Phase 3 were accepted by Human via Director review. Human approved the policy decisions below; this draft and its before-process plan do not authorize D02 implementation or execution.

Sources: [Phase 3](phase_03.md), [EDA findings and figure provenance](../results/eda_findings.md), [evaluation contract](../results/evaluation_contract.md), [data contract](../results/data_contract.md), [split manifest](../../datasets/processed/split_manifest.json), [roadmap Cụm D and §4.4](../plans/plan_overview.md), [file map](../plans/file_map.csv), and [D01 manifest](../../runs/20261118_system312_d01_01/manifest.json). D02 addresses R03 and Q06; downstream E01/E02 and test opening remain separate gates.

## 1. Scope and inputs

Use the accepted canonical hourly dataset and locked split manifest. Verify canonical SHA256 `7122e873708d3297e38316a5d29a08236c516fcdf20327e7724edc1d31a83045`, split file SHA256 `d21e718e1b3661186df9f0848e7bd341b5760a6d29fdd3f48dc51102cd0f307d`, lineage, schema, hourly UTC chronology, boundaries and raw hashes. Hashing file bytes for integrity is allowed; parse only train and validation records, stopping before the first test record. Train is rows 0..24543 inclusive; validation 24544..29802; test starts at 29803 and remains unopened for distributions, treatment, prepared rows, origins and scoring until H01 authorization. Validate count and endpoints against the manifest; no sorting, dropping or silent repair.

## 2. Approved policies and unresolved causal interpretation

- Preserve canonical raw load as truth and `load_observed` unchanged, including missing labels. Never impute a scoring label. Construct separate `load_input`, retaining timestamps and weather values. Scan in UTC order, using only already revealed current and past observations; carry state across the train/validation boundary without resetting or consulting future values. No `bfill` or two-sided interpolation.
- Human approved LOCF with `max_gap=1` hour and gaps longer than one hour left `NaN`. **Review issue:** strictly causal processing cannot know at the first missing hour whether a second missing hour will follow. A streaming LOCF-1 rule fills the first missing hour and leaves later hours NaN, whereas leaving *every hour* of a multi-hour gap NaN requires future knowledge or retroactive revision. Neither interpretation is assumed approved. Human must resolve this before D02 implementation; test both a one-hour gap and the first hour of a longer gap against the selected rule. Any retroactive rule would need explicit forecast-time semantics and a compatible causality decision. Windows containing unresolved NaN are invalid context, counted as `n_input_excluded` after missing-truth exclusion under the evaluation contract; E02 owns origin materialization.
- Flag physical invalidity for `load < 0`, `wind_speed < 0`, `temp <= 0`, and `humidity < 0 or > 100`, and statistical extremes strictly outside the train-fitted 0.5th and 99.5th percentiles for each variable. Fit thresholds on available train values only, record method, sample counts and bounds; no clipping or deletion in primary data. Flags are indicators, not proof of sensor error or automatically exclusions. Missing values are not anomalies by comparison. Report any unexpected invalid or missing weather as a stop requiring policy, not an implicit fill.
- VAR primary no-fill domain is the observed contiguous train block `2016-09-28T08:00:00+00:00` through `2017-10-19T14:00:00+00:00`, 9,271 hours. Record the 15,241 earlier observed train hours excluded and resulting representativeness limitation; do not join separated blocks or impute to extend the block. VAR fit and adequacy belong to F02.

## 3. Scaler and output contract

Fit `StandardScaler` on four working levels (load_input, temp, humidity, wind_speed), using only train rows with finite observed or permitted LOCF load and finite weather. Never fit on validation or test. Fix ordering and serialize exact float64 train means, population standard deviations/scales, feature order, fit count, fit row boundary, library version, policy and input/split hashes in `runs/<run_id>/artifacts/scaler.json` or equivalent lossless state; define zero-variance behavior consistently with StandardScaler and audit it. Use those fixed parameters for validation and later streamed test; no refit. Store full precision; verify serialized reload and load inverse transform within **1e-9 MW** on numerical fixtures and representative valid levels. Treat NaNs as invalid input context, not values to replace during scaling.

`datasets/processed/prepared_hourly.csv` contains train and validation only, ordered hourly, with UTC timestamp, original load truth, immutable observed mask, separate working load, unchanged weather, physical and percentile flags, and explicitly named scaled working levels. Record exact column names, data types, missing representation and scaler/state hashes in the audit before promotion. Do not include test rows. Fixed-state causal transformation must support later sequential test use without inspecting test distribution. Preserve unscaled values and flags so peaks remain observable. No windows, model fitting or evaluation in D02.

## 4. Deliverables and ownership

| Path | Responsibility |
|---|---|
| `src/practice_4/data/preprocessing.py` | Sequential causal treatment, flags, train-only scaler fit and fixed transform/inverse APIs. |
| `tests/test_preprocessing.py` | Synthetic chronology, missing, flags, scaler and truth invariants. |
| `datasets/processed/prepared_hourly.csv` | Train/validation prepared data with lineage, no test rows. |
| `docs/results/preprocessing_audit.md` | Exact schema, policies, row/gap/flag/fit counts, bounds, scaler parameters, VAR domain, exclusions and limitations; pending D02 acceptance. |
| `runs/<run_id>/artifacts/scaler.json` | Exact fitted state and provenance, checksummed in run manifest. |
| `runs/<run_id>/manifest.json`, config/environment snapshots; `docs/logs/D02_<run_id>.md` | Unique run evidence, input/output hashes, approvals, commands, failures and limitations. |
| `config/practice_4.json`, `src/practice_4/pipeline.py`, status and file map | Only necessary D02 config, gate/orchestration and evidence updates, following existing owners; no unrelated stage changes. |

Do not overwrite raw, canonical, split, existing run evidence or official figures. Verify dependencies before execution: if scikit-learn is absent or its compatible version/lock is not approved, stop for separate dependency approval; do not install implicitly. Run-staged outputs and canonical promotion must follow the approved run/manifest workflow; avoid silently overwriting an existing prepared output.

## 5. Before-process plan and acceptance checks

After Human approves this specification **and resolves §2**, verify predecessors, inputs, dependency and approval references. Implement only D02 owners; use synthetic fixtures before any data run. Record design choices for percentile interpolation and CSV null/precision explicitly before fitting; treat an unresolved choice as a stop rather than choosing from validation results. Run once with a fresh ID, inspect artifacts and audit, compare raw/canonical/split hashes before and after, then present D02 for Human acceptance. Preserve failed-run evidence. Historical D01 manifest hashes describe pre-approval documents; do not rewrite that manifest after document updates.

Required tests: one-hour and multi-hour gaps including the first missing hour, leading missing values and cross-split carry; future perturbation cannot change any already emitted output; no access to test records; mask/truth exact preservation; train cutoff and validation perturbation cannot change scaler or percentile state; physical thresholds and strict percentile boundaries; non-clipping of genuine peaks; NaN propagation; fixed scaler serialization/reload and inverse error <=1e-9 MW; timeline and schema rejection; block endpoints/count and audit lineage. Test exclusion count semantics with synthetic windows; E02 owns actual origin lists and counts. No actual counts are claimed here.

Commands from `total_practice/Practice_4` root, **only after approval, resolution and dependency check** (D02 dispatcher is not yet implemented):

```powershell
py -3.12 -m pytest tests/test_preprocessing.py
py -3.12 -m pytest tests/test_splitting.py tests/test_walk_forward.py tests/test_metrics.py
py -3.12 -m practice_4.pipeline --stage D02 --config config/practice_4.json --run-id <unique_d02_run_id>
git status --short
git diff --check
```

Log exact commands, exit codes and hashes, including any failed attempts. Inspect output row count 29,803, endpoints, all columns, state reload, fit-range counts, flag counts, and no test rows. Audit any train/validation counts actually measured, and the VAR limitation; independently verify artifact hashes.

## 6. Stop conditions, impact and alternatives

Stop for missing specification approval or unresolved causal interpretation, unapproved dependency, missing or changed predecessor/hash, timeline/schema/mask mismatch, inaccessible required inputs, unexpected nonfinite weather, test record access, future leakage, unapproved policy or scope expansion, unexplained failed tests, inverse tolerance failure, output collision, or inability to establish provenance. Do not silently alter policy, split or threshold. Escalate repeated failures per repository rules.

Impact is confined to D02 data and evidence owners; raw truth, existing split and evaluation contract remain authoritative. No clipping avoids suppression of genuine peaks but leaves extreme-value sensitivity; flags permit later approved sensitivity analysis. LOCF can create bias and long gaps reduce usable windows. The fixed VAR block excludes substantial earlier history and is not representative by construction. Alternative future-informed complete-gap classification is incompatible with immediate streaming unless forecast-time behavior is separately defined and approved.

## 7. Approval record

- D01, findings and Phase 3: **Human APPROVED / COMPLETED, 2026-11-18 via Director review**.
- Human approved max-gap, flag/no-clip and VAR block policy decisions on 2026-11-18; §2 identifies a causality ambiguity requiring resolution.
- Phase 4 specification / before-process plan and D02 implementation: **PENDING HUMAN APPROVAL**. No D02 execution is authorized by this draft.
