# Phase 8.5 - Scientific replay and model training evidence

Status **PENDING HUMAN REVIEW**. The four replays completed. Human authorized this out-of-plan replay and implementation to collect model-specific logs. Review and acceptance remain **PENDING HUMAN REVIEW**. Phase 9 test opening remains gated.

## Objective and boundaries

Reproduce the accepted F01, F02, G01 and G02 train/validation protocols with new run IDs and capture separate evidence for persistence, seasonal24, VAR(24), XGB_full, XGB_load_only and both LSTM trials. Treat replay results as evidence only. Preserve accepted artifacts, reports and Phase 9 model locks. Do not parse or materialize test rows at or above 29803. Use the accepted E02 inputs, chronological splits, D02 scaler, original config bytes, seed where applicable, hyperparameters, budgets and selection rules. Hash raw and canonical data as opaque bytes only.

## Implementation plan

1. Record pre-run input, accepted-run and report hashes, config identities, environment and approvals. Register this plan and evidence directory in the file map.
2. Update the existing baseline, VAR, XGBoost and LSTM runners and focused tests to accept collision-safe replay IDs and route replay reports inside the new runs. Keep accepted-run behavior and model locks intact. Each run retains config, manifest, structured outputs, full console output and partial failure evidence.
3. Record model-specific logs in a unique batch under `docs/logs/training_evidence/`. Baselines log formula and scores, VAR logs diagnostics and lag selection with provenance, XGBoost logs all 18 trials and per-round validation metrics, and LSTM logs each epoch of both trials. Monitor train RMSE in XGBoost only after a synthetic check confirms the original validation early stopping remains unchanged.
4. Run targeted tests before replay. Execute the four model-family replays in dependency order with the accepted configurations. Compare validation keys, truths, MAE, RMSE, MAPE and relevant model hashes to accepted runs, reporting actual differences.
5. Write an evidence index with run IDs, commands, environment, log and manifest hashes, warnings, parity and limitations. Recheck all pre-run hashes, update status and file map, run `git diff --check` and present results for Human review.

## Planned paths

- `src/practice_4/models/{baselines,var_model,xgboost_model,lstm_model}.py` own replay behavior.
- `tests/test_baselines.py`, `tests/test_var.py`, `tests/test_xgboost.py`, `tests/test_lstm.py` and focused replay tests verify behavior.
- `runs/<unique_replay_run_id>/` contains each replay's isolated evidence.
- `docs/logs/training_evidence/<batch_id>/` contains model-named logs and README.
- `docs/plans/file_map.csv` and `docs/status/current_status.md` record scope and state.

## Stop conditions

Stop on config or input drift, output collision, test boundary access, unexpected dependency change, failed test, invalid numerical output, changed early-stopping semantics, unexpected training failure or incomplete integrity checks. Keep failure evidence. Do not retune, expand budgets, replace locks or silently retry.

## Authorization

Human approved this specification and authorized full Phase 8.5 implementation, tests and replay on 2026-11-18. Acceptance remains **PENDING HUMAN REVIEW**.

- Replays completed in batch `20261118_system312_p85_batch_01`. [Evidence index](../logs/training_evidence/20261118_system312_p85_batch_01/README.md). Human acceptance remains **PENDING HUMAN REVIEW**.
