# Phase 7 - XGBoost and weather ablation (G01)

Status **APPROVED / COMPLETED**. Human approved F02, the VAR(24) lock and Phase 6 completion on 2026-11-18 via Director review, and authorized preparation of this specification and before-process plan.

The objective is one-step observed load prediction in MW and a validation comparison of load-only inputs with load plus weather. This document records the approved execution protocol.

Sources are the [roadmap, cluster G and sections 4.3 and 7](../plans/plan_overview.md), [evaluation contract](../results/evaluation_contract.md), [feature dictionary](../results/feature_dictionary.md), [file map](../plans/file_map.csv), [Phase 6 approval](phase_06.md) and [F02 report](../results/var_results.md).

## 1. Inputs, eligibility and chronology

Verify the accepted E02, F01 and F02 run manifests and relevant artifact SHA256 values, including the locked VAR model, model inputs, origin manifest and D02 scaler. The F02 report approval header was edited after its run. Preserve its historical manifest and verify the run-time hash against its recorded evidence.

Use the approved E02 `x_xgb`, `target_row`, `y_true_mw` and `origin_manifest.csv`. Join by `sample_index`, checking chronological target/origin UTC timestamps, target row, split and exact raw truth. The 25-hour common eligibility context is fixed. Train has 24,519 candidates, 32 missing truths, 52 invalid contexts and 24,435 eligible samples. Validation has 5,259 candidates, 2 missing truths, 0 invalid contexts and 5,257 eligible samples. The 25 initial warm-up target rows are reported separately.

Forecast `load(t+1)` from information available by origin `t`. Preserve chronological ordering with no shuffle, fixed D02 transformations and the C02 predict-score-reveal protocol. A forecast never becomes an observed input. No training or feature may use target-hour weather. Never parse or materialize test records `>= 29803`. H01 has an independent test-opening gate.

Score raw observed labels in MW. Fit boosters directly to `y_true_mw`, so predictions and early-stopping RMSE are in MW. Input features remain in the D02 train-scaled representation. Do not inverse-scale labels or predictions. Use the existing C02 metrics owner for MAE, RMSE and MAPE. Exclude zero truths only from MAPE, without epsilon. If all scored truths are zero, report null and a reason. Report candidate, missing, invalid, scored and zero-excluded counts.

## 2. Locked trial budget and feature subsets

Before any fit, serialize and hash a run configuration containing the exact grid, feature indices and names, seed, version, input and scaler hashes, scoring and stopping protocol. Human approval of this document and G01 execution is required.

| Parameter | Proposed values |
|---|---|
| max_depth | 3, 5, 7 |
| n_estimators | 300, 600, 1000 |
| learning_rate | 0.05 |
| subsample | 0.8 |
| colsample_bytree | 0.8 |
| random_state | 42 |
| objective | reg:squarederror |
| eval_metric | rmse |
| early_stopping_rounds | 30 |

The nine combinations run once per subset, yielding **18 trials** and at most 11,400 requested boosting rounds if every trial reaches its cap. Fix all remaining estimator and backend parameters explicitly in the pre-fit config after checking the installed version and approving its compatibility. No unlisted tuning, seeds, training-set reshuffle or test-based decisions. Early stopping uses the 5,257 eligible validation samples in chronological order with raw MW labels. The validation set is used for both early stopping and selection, so the ablation comparison is a model-selection estimate with optimism risk.

| Subset | Exact ordered input |
|---|---|
| `XGB_full` | All 99 columns of `x_xgb`, matching the E01 feature dictionary and E02 array order. |
| `XGB_load_only` | The 24 load columns `lag23_load` through `lag00_load`, oldest first, followed by `mean6h`, `std24h`, `trend24h`, for 27 columns. |

Resolve indices from approved feature names and assert uniqueness and order. Each trial uses the same 24,435 eligible train keys, 5,257 validation keys, labels, seed and corresponding grid combination. The only difference between paired ablation trials is the feature subset. Record config, trial ID, status, elapsed time, validation metrics, best iteration, best tree count, warnings and artifact references. A failed trial fails the stage and is documented for Human review instead of being silently skipped.

## 3. Model selection and interpretation

For every trial evaluate MAE, RMSE and MAPE on the common validation set at the selected early-stopping iteration. Explicitly use the first `best_iteration + 1` boosting rounds for prediction and serialization or inference. When a trial reaches its cap without triggering early stopping, use its best iteration as reported by the configured API. Reject missing or invalid best-iteration state.

For C02 tie-breaking, `complexity = best_iteration + 1`, the count of boosted trees used for prediction. The objective has one output and one tree per boosting round. Within each subset, select candidates within `1e-6` MW of that subset's minimum validation RMSE, then lowest MAE, then lower complexity, then lexicographically smaller stable trial ID. Compare each subset's selected validation metrics and report full minus load-only RMSE, MAE and MAPE. The production candidate is the selected `XGB_full` model under the roadmap's full-feature model contract. Feed its validation metrics and complexity to C02 cross-model selection under model ID `XGB`. Do not use test rankings for selection.

Extract train-fitted `gain` importance from the selected full model using only the trees used by its predictions. Enumerate all 99 feature names, assign zero to unused features, and report individual lags and aggregates by load, temperature, humidity, wind speed and derived load features. Define gain as the model's mean split gain for each used feature and state how any group aggregate is calculated. Gain ranking and ablation describe predictive association, subject to correlated predictors, weather proxy construction, shared validation selection and the effects of the fixed model budget. They do not establish causal effects or isolate a unique weather variable's contribution.

## 4. Dependencies, artifacts and ownership

Before G01 execution, check whether `xgboost` is importable in system `py -3.12`, record its exact version and check compatibility with the approved Python, NumPy and pandas environment and the configured early-stopping and model persistence APIs. If installation, upgrade or a different backend is required, stop for Human approval of version and environment changes. A package check is part of future stage execution.

| Exact path | Planned ownership |
|---|---|
| `src/practice_4/models/xgboost_model.py` | Aligned feature selection, finite trials, validation, gain extraction, model metadata and run entry point. |
| `tests/test_xgboost.py` | Synthetic indexing, chronology, grid, scoring, early-stopping range, artifact metadata and reload parity checks. |
| `docs/results/xgboost_findings.md` | Trial budget and results, validation ablation, gain interpretation, limitations and evidence. |

Under a fresh `runs/<run_id>/`, save the locked config and environment, trial registry, selected full and load-only boosters, model metadata JSON, validation predictions, metrics and gain table. For each selected booster the JSON metadata must directly embed the exact ordered `feature_order` and D02 `scaler_sha256`, plus model/subset ID, booster byte SHA256, config SHA256, model version, selected iteration, tree count, library version and input lineage. Bind metadata and booster hashes in the run manifest. Reload the serialized booster and metadata in the locked environment, assert feature/scaler agreement and reproduce every selected validation prediction within absolute `1e-9 MW`. A mismatch stops promotion.

The accepted VAR artifact does not directly embed feature order or scaler hash. Its embedded config hash identifies the locked F02 config, which names the F01 baseline run and stationarity run. The F02 manifest separately records the scaler hash among upstream hashes. Human accepted this artifact as-is on 2026-11-18. Phase 7 and the future Phase 8 G02 model metadata must directly embed both `feature_order` and `scaler_sha256`.

H01 owns the eventual published test prediction and evaluation artifacts. Model lock and test opening require their own Human approvals.

## 5. Before-process plan and validation

1. After Human approves this specification and authorizes G01, verify F02 acceptance, model lock, E02 artifacts, scaler and upstream lineage. Check the system environment and stop for approval if an installation or incompatible dependency change is required.
2. Lock the full configuration, 18-trial budget and feature lists before fitting. Implement and test synthetic lag-name mapping, ablation subsets, no future access, target and origin alignment, parameter grid, deterministic ties, zero-target metrics, early-stopping tree range, feature/scaler metadata, artifact hash and reload parity. Keep the two subset runs on identical keys.
3. Run the approved 18 trials with one seed and fixed configuration. Reload selected artifacts, verify parity on all eligible validation samples and independently recompute metrics and gain summary. Stage and verify checksums before promotion. Present both selected configurations, ablation, full-model gain, predictions and model hashes for Human review.

Planned commands from the Practice 4 root after G01 approval. The module CLI and config are proposed interfaces.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
py -3.12 -c "import xgboost; print(xgboost.__version__)"
py -3.12 -m pytest tests/test_xgboost.py tests/test_baselines.py tests/test_metrics.py tests/test_walk_forward.py -q -p no:cacheprovider
py -3.12 -m practice_4.models.xgboost_model --run-id <unique_g01_run_id> --config <approved_locked_config>
git status --short
git diff --check
```

## 6. Stop conditions

Stop for missing Human approval, unapproved or unavailable dependency, version incompatibility, config or lineage drift, output collision, data past the permitted boundary, changed eligibility or mismatched keys/truths, unequal paired budgets, a failed or nonfinite trial, incorrect early-stopping iteration, unapproved grid change, failed state immutability, reload/parity failure or artifact hash mismatch. Record the evidence and request resolution before continuing. Do not replace failed trials or use validation results to expand the grid.

## 7. Approval record

- F02 run `20261118_system312_f02_02`, its report and VAR(24) model lock SHA256 `0b3820731f3369f57699adaa64a7b1f4a5cbbf659c48331fc5721335572d3e26`, and Phase 6 completion were **Human APPROVED / COMPLETED** on 2026-11-18 via Director review.
- Human **APPROVED** the Phase 7 specification and before-process plan on 2026-11-18 via Director review and authorized G01 execution. G01 was blocked at the dependency check. Human approved `xgboost==3.4.1` on 2026-11-18 via Director review and authorized resumption. The installed version, core versions, pip check and API smoke test passed. G01 execution completed 18 trials.
- Human **APPROVED / COMPLETED** G01 run 20261118_system312_g01_01, the [G01 findings](../results/xgboost_findings.md), the XGB_full model lock with SHA256 e7386e8cfc38d51d6abc51abad383fb2c9d6360c9c955c6fe3ddb33883aec8ae and complexity 931, and Phase 7 on 2026-11-18 via Director review. Human authorized [Phase 8 specification drafting](phase_08.md). G02 execution and H01 test opening retain separate approval gates.
- The [G01 run manifest](../../runs/20261118_system312_g01_01/manifest.json) records the findings hash at run time (41adadcbe022a40fac841a8e173314d0c4f5cb4a3678e412fc40f7f475bfecf7). The approved findings header changed the document SHA256 to aa2c8e7787c9e76a419ded671c90a20a3c139bb34cd0206d4049419df376ccbf.
