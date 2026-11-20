# Phase 9 - Test opening, walk-forward evaluation and error analysis (H01-H02)

Status: executed under the user's explicit 2026-11-20 delegation to complete Practice 4. H01/H02 runs and post-run review evidence are linked in `docs/status/current_status.md`; the original pre-run gate requirements below are retained as design history.

## 1. Scope and upstream decisions

H01 addresses Q10 and R08. H02 addresses R09. The design follows [roadmap cluster H, sections 4.2-4.4 and section 7](../plans/plan_overview.md), the [approved C02/RV2 v1 contract](../results/evaluation_contract.md), the [E01 feature dictionary](../results/feature_dictionary.md), the [D02 audit](../results/preprocessing_audit.md) and the [file map](../plans/file_map.csv). G02 and Phase 8 were accepted on 2026-11-18. Drafting authority ends at documentation. H01 requires both Human approval of this specification/before-process plan and explicit authorization to open test rows. H02 requires Human acceptance of the H01 evidence and authorization to analyze it.

Preserve the validation-selected configurations and report test rankings as descriptive results. The chronological target assignment, observation availability assumption, model-specific input representations, original MW units and missing-data policy carry forward from the accepted contracts.

## 2. H01 - Pre-opening verification (Q10)

Bind the following exact locks. Baseline digests identify the canonical JSON configuration/version per model in the F01 config. Check the F01 source and scaler bindings as well as the individual hashes.

| Lock / RV2 ID | Accepted artifact | SHA256 |
|---|---|---|
| D02 scaler | `runs/20261118_system312_d02_01/artifacts/scaler.json` | `ebfa412b7bce9ac077776b416df1083eaff32b08c48c28dc5d2e7e06b2757b11` |
| persistence | `runs/20261118_system312_f01_01/config.json`, key `persistence` | `f0bce270c71b033af288c8f2b43ab05a66730d98aaa00ba0694c70fd24925d63` |
| seasonal24 | Same F01 file, key `seasonal24` | `2c8b93b4f663e69f6ef62229ab8c3df79d4f3959a5cb803ec9521682aac7dce3` |
| VAR(24) / VAR | `runs/20261118_system312_f02_02/artifacts/model.npz` | `0b3820731f3369f57699adaa64a7b1f4a5cbbf659c48331fc5721335572d3e26` |
| XGB_full / XGB | `runs/20261118_system312_g01_01/artifacts/XGB_full.json` | `e7386e8cfc38d51d6abc51abad383fb2c9d6360c9c955c6fe3ddb33883aec8ae` |
| LSTM weights | `runs/20261118_system312_g02_01/artifacts/lstm.weights.h5` | `512715c5249f35bcfe46d1ecdbfc4413dbb1d3f263fe73f41dc9845fe5a69a1c` |
| LSTM architecture | `runs/20261118_system312_g02_01/artifacts/lstm_architecture.json` | `c858df9f6417ac508d9b4d2195ce0b29a539ab89d4bb5d10950ac12f6d7af807` |

Before parsing any test row, verify the Human gate references, canonical byte SHA256 `7122e873708d3297e38316a5d29a08236c516fcdf20327e7724edc1d31a83045`, split file SHA256 `d21e718e1b3661186df9f0848e7bd341b5760a6d29fdd3f48dc51102cd0f307d`, split semantic digest, raw byte hashes and accepted B02/C01/D02/E02/F01/F02/G01/G02 lineage. Record exact manifest, code, metadata, config and preprocessor digests. Keep historical run-time report hashes distinct from post-approval report hashes. D02 prepared rows and the scaler must match their manifests. Verify F02 feature order and scaler lineage through its accepted sidecar/config and manifest, with the approved direct-embedding limitation disclosed. Check XGB_full and LSTM embedded feature order/scaler digest, model shape, state reload and accepted validation parity. Never import a model through a training entry point for these checks.

Freeze an immutable pre-opening configuration and a source-reference manifest under the new H01 run ID. Bind approval references, locks, eligibility and scoring versions, runtime pins, deterministic device and inference layouts, numeric tolerance for validation replay checks, and H02 bin definitions. Exercise each adapter on synthetic and authorized validation data using the intended causal inference layout. For LSTM preserve the G02 CPU, dtype, threading, HDF5 and deterministic settings. The proposed per-origin adapter uses one real 24 x 4 sequence in a fixed batch of 64 identical copies of that sequence and returns its first prediction. Check parity against accepted G02 validation outputs under that layout before opening (maximum absolute difference 1e-6 MW, zero relative tolerance). If the proposed layout fails this check, return to Human review before opening test. This preserves the batch width without drawing a second origin from the stream. For all models, capture complete fitted-state fingerprints before and after prediction, including weights/parameters, scaler, inference configuration and any mutable inference state. Rolling history and LOCF state are the only expected data updates.

## 3. H01 - Single-pass causal evaluation (R08)

Test comprises 5,261 consecutive hourly targets, canonical rows 29803..35063 inclusive, from 2018-05-26 18:00 UTC through 2018-12-31 22:00 UTC. Initialize the 25-row ring with the finite D02 prepared validation rows 29778..29802 and verify their exact row indices, order, feature order, and one-hour UTC spacing. Verify D02's end state at row 29802 (2018-05-26 17:00 UTC), `last_load=25194.0` and `missing_run=0`, from accepted D02 evidence and prepared data before any test access.

After both H01 gates and preflight pass, open one sequential canonical record iterator. Validate header and skip the prefix by record count. A controller owns the iterator. Forecast callbacks receive only the ring and expected origin/target timestamps from the split schedule. Forecasts for a finite context are completed before the controller reads the target record. After reading and validating the record, the controller scores or classifies the origin privately, then reveals that observation or missing marker to history and updates fixed-scale working features for the next origin. Buffered operating system I/O does not permit parsing future records or making them available to adapters. Do not preload a test dataframe, precompute test tensors, revisit canonical test rows for analysis, or use target-hour weather. Verify expected UTC and target index before any update.

- The common window is `t-24..t`. Eligibility is observed raw load at `t+1` and all 25 x 4 working inputs finite. Count missing truth first, then invalid context. A valid context requests all five predictions before truth availability is known. An exception, state mutation or nonfinite forecast fails the whole run, including at an origin later excluded for missing truth.
- Use D02 Streaming LOCF-1. An observed load resets the missing run. Carry forward an available prior observation at the first missing hour only. Leading or subsequent consecutive missing hours remain missing. Preserve observed values, raw masks and original labels. Apply fixed D02 means and scales in order `load_input, temp, humidity, wind_speed`. Apply the approved physical and statistical flags without clipping. Unexpected missing or invalid weather stops H01 under the D02 policy.
- Persistence uses the working load at `t` and seasonal24 at `t-23`. Locked VAR(24) consumes the latest 24 scaled level vectors and applies its fixed intercept and coefficients with `d=[0,0,0,0]`. XGB_full uses the ordered 96 lags plus `mean6h`, `std24h` with `ddof=0`, and `trend24h = load(t)-load(t-24)` in scaled working load, exactly as at G01. LSTM consumes the latest ordered 24 x 4 scaled inputs and keeps its stateless forward behavior. Restore baseline, VAR and LSTM scaled load forecasts with D02's load mean and scale. XGB_full already predicts MW.
- Score matching observed MW truth for all five models. Report MAE, RMSE and MAPE as defined in C02 with no epsilon. Exclude zero truths only from MAPE. If all scored truths are zero, record null MAPE and its reason. Require `5261 = n_missing_excluded + n_input_excluded + n_scored`, `n_zero_excluded <= n_scored`, five identical scored key/truth sets, and a nonempty scored set. Score the locked models once, with no refitting, tuning or post-test selection.

## 4. H01 - RV2 outputs and promotion

Stage `test_predictions.csv`, `test_metrics.csv`, `evaluation_manifest.json`, `test_eligibility.csv` and `diagnostic_context.csv` under `runs/<run_id>/artifacts/`. The eligibility file contains every candidate row, UTC origin/target, observed flag, context-valid flag, eligibility and reason. The diagnostic sidecar contains one row per scored UTC key with origin-hour canonical weather proxies and their fixed D02 regime labels. It supports H02 without reopening canonical test records.

Predictions use exactly the RV2 v1 columns `schema_version,model,origin,target_timestamp,y_true_mw,y_pred_mw,split,run_id`. Use UTF-8, UTC ISO 8601, model IDs `persistence,seasonal24,VAR,XGB,LSTM` and `split=test`, with finite round-trip MW values. Metrics CSV has one row per model with `schema_version,run_id,model,split,mae_mw,rmse_mw,mape_percent,mape_null_reason,n_considered,n_scored,n_zero_excluded,n_missing_excluded,n_input_excluded`. Check it against independent scoring from the serialized predictions and eligibility, using a relative numerical tolerance of `1e-12` (absolute floor `1e-12`) for finite metrics and exact counts/null semantics.

Use the strict C02 manifest schema and existing RV2 validator. Keep one digest per model ID. `model_hashes.LSTM` references the weights SHA256 and the hashed `source_manifest.json` binds the architecture, metadata and G02 run manifest as well. Map `prediction_file.path` to the Practice 4-relative official path. Record the canonical, split, locked config, preprocessor, eligibility and source manifest digests in `input_hashes`. Bind metrics, diagnostic context and staged/promoted byte identity in the outer run `manifest.json`, with exact approval refs and test-open record. Keep RV2 keys unchanged.

Proposed location amendment for this phase: publish `outputs/predictions/test_predictions.csv` and `outputs/tables/test_metrics.csv`, and retain the authoritative RV2 `evaluation_manifest.json` under the H01 run artifacts. This supersedes the earlier planned `outputs/results/` locations upon Human approval. Use the accepted H01 manifest to resolve paths, avoid duplicate official copies, and verify that H02/I01 references agree before opening test. Require collision-free destinations and complete staged verification before promotion. Promote verified bytes with exclusive publication and an accepted manifest reference as the downstream gate. Verify the post-promotion hashes. Any incomplete promotion invalidates the candidate and requires quarantine.

## 5. H02 - Diagnostics and cross-model comparison (R09)

Consume only the accepted H01 predictions, metrics, manifest and diagnostic context plus accepted train/validation evidence. Verify hashes, align on UTC keys, and keep the same five-model scored sample. Residual is observed minus forecast in MW. Report grouped counts, bias, MAE, RMSE and MAPE with the same zero rule. Keep empty or sparse groups explicit and avoid unsupported rankings. Analyze the complete test window, identify large residual periods with evidence, and distinguish actual validation/test comparisons from explanations.

| Group | Predeclared definition |
|---|---|
| Local hour and weekday | Target UTC converted to `Europe/Madrid`, with hour 0..23 and Monday=0. Keep UTC as join key and include both repeated DST observations. |
| Month and season | Target local YYYY-MM, and meteorological DJF, MAM, JJA, SON. Report coverage for partial months/seasons. |
| Load regime | Scored raw target load relative to D02 train-only load bounds 19,605.11 and 38,758 MW. Strictly below lower, within inclusive bounds, strictly above upper. These are retrospective labels. |
| Weather proxy regimes | Group independently by origin-hour canonical temperature, humidity and wind-speed proxies. Use each variable's exact D02 0.5th and 99.5th percentile values, strict tails and inclusive middle. Freeze the exact scaler numbers before test. Report joint effects only as limitations, without creating additional bins from test. |

For section 7's questions, use D01 and G01 to discuss weather relationships and the validation ablation. Test proxy strata describe association. Use F02 and matched baseline errors to discuss VAR failure regimes. Use G02 curves and restored-state train/validation loss for overfitting; use local hour/weekday profiles and exact UTC residual lags 24 and 168 for daily/weekly evidence, with pair counts and no claim of learned weekly structure without support. Compare ML/DL using MW metrics, information sets, compute, budgets and interpretability. Explain any differences between MAE and RMSE rankings. Preserve the validation-selected winner and all locked configurations.

Stage `actual_vs_predicted.png`, `residual_distributions.png`, `grouped_error_profiles.png`, `grouped_errors.csv` and `model_comparison.md` under the H02 run artifacts. Inspect figure labels, coverage, units and timezone, check group and residual calculations, and bind all staged files and official copies to the H02 manifest. Promote the figures to `outputs/figures/` and report to `docs/results/model_comparison.md` after verification. Keep the grouped table as run evidence.

## 6. Before-process plan, impacted paths and checks

| Step | Planned file changes and validation |
|---|---|
| H01 implementation and preflight | Extend `src/practice_4/analysis/walk_forward.py` for the gated multi-model controller/CLI and `tests/test_walk_forward.py` for streaming, adversarial chronology, state snapshot coverage, common eligibility and promotion. Reuse existing D02/E01 transformations, metric and RV2 validators, and frozen artifact loaders without changing model training owners. |
| H01 execution and review | Create `runs/<h01_run_id>/config.json`, `source_manifest.json`, `manifest.json` and the five artifacts in section 4, plus `docs/logs/H01_<h01_run_id>.md`. Promote the two CSVs in section 4. Update `docs/status/current_status.md` and `docs/plans/file_map.csv`. Submit diagnostics, hashes and eligibility counts for Human acceptance. |
| H02 implementation and execution | Create `src/practice_4/analysis/error_analysis.py`, `tests/test_error_analysis.py`, `runs/<h02_run_id>/manifest.json` and the five staged files in section 5 plus `docs/logs/H02_<h02_run_id>.md`. Promote `docs/results/model_comparison.md` and the three named figures. Record status and file map, then present Phase 9 and H02 for Human review. |

Planned commands after the respective approvals from the Practice 4 root. The H01/H02 execution entry points will be implemented in their approved stages.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
py -3.12 -m pip check
py -3.12 -m pytest tests/test_walk_forward.py tests/test_metrics.py tests/test_preprocessing.py tests/test_features.py tests/test_lstm.py -q -p no:cacheprovider
py -3.12 -m practice_4.analysis.walk_forward --run-id <h01_run_id> --config runs/<h01_run_id>/config.json
py -3.12 -m pytest tests/test_error_analysis.py tests/test_metrics.py -q -p no:cacheprovider
py -3.12 -m practice_4.analysis.error_analysis --run-id <h02_run_id> --evaluation-manifest runs/<accepted_h01_run_id>/artifacts/evaluation_manifest.json
git status --short
git diff --check
```

Use in-memory fixtures or dedicated workspace staging under `runs/`. Before H01 test with synthetic missing targets, sequential gaps, cross-split seed state, ramp alignment, reordered or mutated future rows, target-iterator access guards, invalid/nonfinite forecasts, mutated state, hash/schema failures, output collisions and all-zero truths. Test that changing an unrevealed observation or its eventual eligibility cannot affect an already issued prediction. Compare the initial origin, shape and inverse transforms to hand fixtures. Before H02 test DST repetition, local month and season boundaries, train-bin edges, zero truths, empty groups and count conservation. Verify raw/canonical/split, model and scaler bytes before and after H01 and accepted H01 artifact hashes before and after H02.

## 7. Stop conditions and approval record

Stop on absent approval, any missing or mismatched lock or version, unresolved output path conflicts, invalid initial state, wrong schema/timezone/endpoints, unexpected missing/invalid weather, access outside the causal boundary, no scored rows, mutation/nonfinite forecast, count or parity failure, output collision, or changed upstream hash. If a bug affects either stage, mark its run invalid, quarantine staged or published files by run ID, retain logs and hashes, document affected consumers, and halt promotion and downstream use. Human must approve the repair scope and any replay after test opening, using a new run ID with the same locked protocol. No silent replacement or selective replay. The single-pass protocol has modest memory use and auditability, with sequential inference cost and sensitivity to bad inputs. The held-out window covers only part of the calendar year.

- Human approved G02 run `20261118_system312_g02_01`, the LSTM findings, the weights and architecture locks, and Phase 8 completion on 2026-11-18 via Director review. This authorizes Phase 9 drafting.
- The user explicitly instructed the agent to complete the remaining Practice 4 work without pausing on 2026-11-20; H01 test opening and subsequent H02 execution proceeded under that delegation. Resulting manifests identify this instruction as authorization. Post-run Human review is not separately recorded.

