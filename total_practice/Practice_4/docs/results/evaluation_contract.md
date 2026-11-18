# Phase 2 evaluation contract — Q04, Q05, RV2

Status: **APPROVED / COMPLETED**. Human approved C02 run `20261118_system312_c02_01`, this contract, RV2 closure and Phase 2 completion on 2026-11-18 via Director review. This approval does not authorize fitting or test opening.

## Q04: origins and eligibility

The target timestamp `t+1` determines split membership. The common warm-up is 25 raw hourly rows ending at origin `t`, including `t-24` and `t`; LSTM uses 24 rows. Historical context may cross a split boundary only when its timestamps are at or before `t`. Train-fitted transformations and weights remain fixed; no train-plus-validation refit before test.

Eligible scoring requires an observed raw target and valid causal input context. Count missing truth first; among observed targets count invalid context; score the remaining origins. The D02 treatment, maximum gap and valid-context policy remain subject to their own approval. E02 may materialize train/validation eligibility after D02; H01 authorization is required before test origins, tensors or predictions are materialized. Source observations at the end of hour `t` are a lab availability assumption, not a production guarantee.

## Q05: walk-forward, metrics and selection

In chronological order predict using revealed history, score if truth is observed and context valid, then reveal the raw truth or missing marker. Never insert a forecast as observed truth. Invalid context and missing truth are exclusions; model errors and nonfinite forecasts fail the run. Fixed model and transformation state must not change. The controller requires a caller-supplied complete state snapshot for mutation detection; future model integrations must establish that this snapshot covers all fitted state and verify their own chronology and input access. The synthetic controller is not a security boundary for arbitrary callbacks.

On the same eligible pairs and original MW scale: MAE = mean absolute error; RMSE = square root of mean squared error; MAPE = 100 times mean absolute percentage error for nonzero truths only. No epsilon is used. If all scored truths are zero, MAPE is null with a reason. Report near-zero sensitivity without a post-test threshold change. `n_considered = n_missing_excluded + n_input_excluded + n_scored`; `n_zero_excluded` is a subset of `n_scored`. Zero scored points fail.

Select on validation only: candidates within `1e-6` MW of the global minimum RMSE, then lowest MAE, then model order persistence, seasonal24, VAR, XGB, LSTM, then lower parameter/tree/epoch count, then trial ID. The meaning and comparability of the count for each model and the model budgets must be approved before fit. Test ranking is descriptive and cannot change the configuration.

## RV2: evaluation artifacts v1

H01 owns actual artifacts. UTF-8 CSV `outputs/results/predictions.csv` has exactly `schema_version,model,origin,target_timestamp,y_true_mw,y_pred_mw,split,run_id`; version `1`, `split=test`, finite numeric MW, UTC ISO 8601 `Z` or `+00:00`, target one hour after origin. `(model, origin, target_timestamp)` is unique; each required model has the same origin/target set and observed truth. Empty output, duplicate headers or rows, missing fields and nonfinite values fail. Excluded origins are not prediction rows and need separate eligibility evidence.

UTF-8 JSON `outputs/results/evaluation_manifest.json` has exactly `schema_version`, `run_id`, `stage_id`, `prediction_file`, `input_hashes`, `model_hashes`, `approval_refs`, `counts`, `metrics`, `protocol`, `created_at_utc`, `limitations`. Version is `1`, stage is `H01`; duplicate keys and unknown fields fail. `prediction_file` has relative `path` and byte `sha256`. `input_hashes` has `canonical_sha256`, `split_sha256`, `config_sha256`, `preprocessor_sha256`, `eligibility_sha256`, `source_manifest_sha256`. `model_hashes` has one lowercase SHA256 per required model, including a baseline version/config hash. `approval_refs` has nonempty `evaluation_contract`, `model_locks`, `test_opening` references; independent test opening authorization is required. Counts use the invariants above. Per-model `metrics` contains finite nonnegative `mae_mw`, `rmse_mw`, and `mape_percent` or null only when all truths are zero; `mape_null_reason` is nonempty exactly in that case. `protocol` records horizon 1, fixed weights, train-fitted fixed transformations and `predict_score_reveal`. `created_at_utc` is ISO UTC; `limitations` is an array of strings.

The validator checks prediction bytes against the recorded checksum, model and origin/truth agreement, count conservation and MAPE null semantics. H01 must additionally verify referenced artifact bytes, approvals, eligibility evidence and independently recompute reported metrics before publication. RV2 was accepted by Human on 2026-11-18.
