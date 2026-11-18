# Phase 8 - LSTM sequence model (G02)

Status **APPROVED / COMPLETED**. Human accepted G02, the LSTM model lock and Phase 8 completion on 2026-11-18 via Director review.

G02 addresses R07, Q09 and analytical questions 4, 5 and 6 under the [roadmap, cluster G and sections 4.3 and 7](../plans/plan_overview.md), [C02 contract](../results/evaluation_contract.md), [feature dictionary](../results/feature_dictionary.md) and [file map](../plans/file_map.csv).

## 1. Inputs and chronology

Verify accepted E02 model inputs and origins, the D02 scaler, F01/F02/G01 validation evidence and approved model locks by SHA256 and lineage. For reports carrying subsequent approval edits, distinguish the run-time hash from the approved report hash. Use only the E02 train/validation arrays. Join by sample_index and verify target rows, splits, exact observed MW labels and consecutive UTC origin/target hours. Compare validation keys and truths with predecessor predictions. Reject any target row at or above 29803. Apply C02 predict-score-reveal with fixed model state and observed causal history. Earlier history may cross split boundaries. Target-hour observations and forecast feedback are prohibited.

Input x_lstm has shape (N, 24, 4), time order t-23..t oldest to newest, and exact variable order ["load_input_scaled", "temp_scaled", "humidity_scaled", "wind_speed_scaled"]. The target is observed load(t+1). Apply the common 25-hour eligibility context. The first 25 rows are warm-up. Train has 24,519 candidates, 32 missing truths, 52 invalid contexts and 24,435 eligible samples. Validation has 5,259 candidates, two missing truths, zero invalid contexts and 5,257 eligible samples.

Optimize MSE on (y_true_mw - mean[0]) / scale[0] using fixed D02 train-fitted parameters with finite mean and positive finite scale. Convert scaled validation predictions to float64, multiply by scale[0] and add mean[0]. Score against original observed truths in MW.

## 2. R07 architecture and proposed Q09 budget

Use an input of shape (24, 4) and exactly LSTM(64, return_sequences=True) -> LSTM(32) -> Dense(1). Intermediate shapes are (N, 24, 64) and (N, 32), followed by a linear (N, 1) output. Use stateless forward LSTMs, tanh state activation, sigmoid recurrent activation, bias with unit forget bias, Glorot-uniform input kernels, orthogonal recurrent kernels and zero dropout and recurrent dropout. Use MSE and Adam with beta_1=0.9, beta_2=0.999, epsilon=1e-7, amsgrad=False, and no schedule, weight decay or gradient clipping. [Keras LSTM API](https://keras.io/api/layers/recurrent_layers/lstm/)

| Trial ID | Adam learning rate | Seed | Epoch cap | Batch size |
|---|---:|---:|---:|---:|
| lstm_lr_001 | 0.001 | 42 | 50 | 64 |
| lstm_lr_0005 | 0.0005 | 42 | 50 | 64 |

Run exactly two trials, with at most 100 epochs combined. Initialize a fresh model and optimizer and reset Python, NumPy and backend seeds to 42 per trial. Set shuffle=False and provide the explicit chronological validation set. Retain final partial batches. Propose float32 model computation, deterministic TensorFlow CPU execution and JIT disabled. Freeze exact backend versions, device, dtype, thread settings and effective training options in the pre-fit config. Use EarlyStopping(monitor="val_loss", mode="min", min_delta=0, patience=8, restore_best_weights=True, start_from_epoch=0) with no baseline. Verify that restored weights correspond to the earliest epoch attaining minimum validation loss, including when training reaches its cap. [Keras EarlyStopping API](https://keras.io/api/callbacks/early_stopping/)

C02 complexity counts trainable scalar parameters. Each LSTM with input width d and u units contributes 4u(d + u + 1). The total is 4*64*(4+64+1) + 4*32*(64+32+1) + 32 + 1 = **30,113**. Verify against the trainable tensor shapes.

## 3. Scoring and analytical evidence

Use C02 MAE, RMSE and MAPE on the same eligible original-scale pairs. Report candidate, missing, invalid, scored and zero-excluded counts. Exclude zero truths only from MAPE and record null with a reason if all truths are zero. Among trials within 1e-6 MW of minimum validation RMSE, select lowest MAE, then lowest complexity, then lexicographically smallest trial ID. Enter the selected candidate as LSTM for cross-model selection using C02 order persistence, seasonal24, VAR, XGB, LSTM.

| Question | Evidence |
|---|---|
| 4. Daily and weekly learning | Compare D01 training profiles to chronological validation traces and error summaries by local hour and weekday, with counts. Use Europe/Madrid labels while retaining UTC keys and both repeated DST hours. Compare persistence and seasonal24 on matching keys. Compute residual autocorrelation at exact UTC lags of 24 and 168 hours using available pairs. The 24-hour input has no explicit lag-168 observation. Weekly learning remains inconclusive if these diagnostics cannot support it. |
| 5. Overfitting | Plot train and validation scaled MSE by epoch. Record best and stopping epochs, epochs after the best, and validation minus train loss per epoch. Evaluate the restored checkpoint on both splits in inference mode for a comparable gap. Discuss divergence, temporal error regimes and the optimism introduced by shared validation for stopping and selection. |
| 6. ML versus DL | Compare MW metrics with locked XGB_full, VAR(24) and both baselines on common validation keys. Report input structure, wall time, device, trial budgets and interpretability limits. The LSTM uses 24×4 sequences. XGB flattens the lags and adds derived load features including a 25-hour trend context. |

## 4. Dependencies and artifacts

After authorization, probe TensorFlow and Keras imports, versions, active backend and CPU/GPU visibility under system py -3.12. Verify compatibility with existing pins, pip check, device and determinism support, then do a synthetic early-stop and save/load smoke check after recording the approved settings. Stop for Human approval if installation, upgrade, a backend change or a different execution device is required. Record dtype, backend/device versions, threading, seed, inference batch layout and any determinism limits. Hash the immutable config before fitting.

On 2026-11-18, three isolated synthetic probes used `HDF5_USE_FILE_LOCKING=FALSE`, workspace staging and a 15-second timeout per subprocess. ZIP saving timed out both with the original single-thread settings and oneDNN disabled ([log](../../runs/g02_smoke_diag_20261118/zip_exact/probe.log)) and with default threading and oneDNN ([log](../../runs/g02_smoke_diag_20261118/zip_default_threads/probe.log)). Both completed three epochs before stalling in Keras `DiskIOStore` -> `get_temp_dir` -> `tempfile.TemporaryFile` -> `_mkstemp_inner`. Direct HDF5 weights saved in 0.009236 s. Weights reloaded into an architecture reconstructed from JSON, with combined save/load time 0.031979 s and `max_abs_diff=0.0` ([log](../../runs/g02_smoke_diag_20261118/h5_weights/probe.log)). The approved ZIP format remains blocked in the tested environment. The proposed amendment is `.weights.h5` plus architecture JSON, with separate SHA256 values bound in metadata and the run manifest, and the same full validation reload parity requirement. Human approved this amendment on 2026-11-18. Use deterministic CPU with one inter-op and one intra-op thread, oneDNN disabled, and HDF5 file locking disabled as in the passing probe.

| Future path | Responsibility |
|---|---|
| src/practice_4/models/lstm_model.py | Validate lineage and inputs, run trials, score, select and serialize the checkpoint. |
| tests/test_lstm.py | Verify shapes, chronology, scaling, selection, metadata and reload parity. |
| docs/results/lstm_findings.md | Report trial metrics, learning curves, temporal diagnostics, questions 4–6 and proposed lock. |
| runs/<run_id>/ and docs/logs/G02_<run_id>.md | Record pre-fit config, environment, manifest, artifacts and execution evidence. |

Stage trials.csv, training_history.csv, validation_predictions.csv, metrics.json, temporal_errors.csv, diagnostic figures, lstm.weights.h5, lstm_architecture.json and lstm_metadata.json under artifacts/. Save restored weights to lstm.weights.h5 and architecture to lstm_architecture.json. The checkpoint SHA256 denotes the weights file. Load the architecture and weights together for inference. Metadata directly embeds feature_order and scaler_sha256 along with config and checkpoint SHA256, architecture, input shape, seed, best epoch, complexity, device, dtype, model and library versions, selected trial and upstream lineage. Bind weights, architecture and metadata bytes in the manifest. Reopen all three, verify hashes and metadata, and check identical keys and finite MW output for all 5,257 validation samples. Require maximum absolute difference <= 1e-6 MW with zero relative tolerance for float32 or float64 inference on the locked backend, device and batch layout. Check inference state immutability. [Keras saving API](https://keras.io/api/models/model_saving_apis/model_saving_and_loading/)

## 5. Before-process plan

1. Record Human approval of this plan and G02 execution. Verify predecessor hashes and the pinned environment. Serialize and hash the approved configuration, including trials, eligibility, feature order, scaler and scoring protocol.
2. Implement the planned files. Test exact layer shapes and parameter count, causal alignment, rejection beyond the boundary, scaling and metric behavior, no shuffle, validation-only stopping, cap and tie cases, feature/scaler metadata and reload parity. Use in-memory fixtures or dedicated workspace paths under runs/ for serialization.
3. Execute two locked trials. Record status, settings, elapsed time, epochs, warnings and validation metrics. Independently recompute validation metrics and diagnostics, inspect plots, verify reload parity and upstream hashes before and after execution, and verify staged checksums before publication. Present findings and the proposed lock for Human review.

Planned commands from the Practice 4 root after approval.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
py -3.12 -c "import tensorflow as tf, keras; print(tf.__version__, keras.__version__, keras.backend.backend()); print(tf.config.list_physical_devices())"
py -3.12 -m pip check
py -3.12 -m pytest tests/test_lstm.py tests/test_features.py tests/test_metrics.py tests/test_walk_forward.py -q -p no:cacheprovider
py -3.12 -m practice_4.models.lstm_model --run-id <unique_g02_run_id> --config <locked_config>
git status --short
git diff --check
```

## 6. Stop conditions

Stop on missing approval, dependency or device incompatibility, config or upstream drift, output collision, chronology or eligibility mismatch, forbidden target row, nonfinite values, trial failure, invalid best epoch, fitted state mutation, serialization or parity failure, or unapproved budget changes. Record the evidence for Human review before proceeding.

## 7. Approval record

- Human approved G01 run 20261118_system312_g01_01, its findings, the XGB_full lock and Phase 7 completion on 2026-11-18 via Director review. This authorizes Phase 8 drafting. [Phase 7 approval](phase_07.md#7-approval-record)
- Human approved the Phase 8 specification and before-process plan and authorized G02 execution on 2026-11-18 via Director review.
- G02 was initially **BLOCKED** at the dependency probe: system Python 3.12 reports `ModuleNotFoundError: No module named 'tensorflow'`; `pip show tensorflow keras` reports both packages missing. `pip check` reports no broken requirements. No installation is authorized by the G02 execution approval.
- Human approved `tensorflow==2.20.0` and `keras==3.11.3` on 2026-11-18 via Director review and manually installed them. G02 was unblocked and authorized to proceed; the system Python 3.12 probe confirmed both versions, TensorFlow backend and CPU, and `pip check` passed.
- The synthetic EarlyStopping and `.keras` save/load smoke did not complete after more than one minute and was interrupted. A partial `runs/g02_smoke_20261118/smoke.keras` appeared, but save/load parity was not established. G02 was blocked during this verification failure.
- Dependency changes and H01 test opening require their respective Human authorizations.

- Human approved the checkpoint format amendment and continuation of G02 on 2026-11-18.
- Human **APPROVED / COMPLETED** G02 run `20261118_system312_g02_01`, its [findings](../results/lstm_findings.md), the LSTM lock (weights SHA256 `512715c5249f35bcfe46d1ecdbfc4413dbb1d3f263fe73f41dc9845fe5a69a1c`, architecture SHA256 `c858df9f6417ac508d9b4d2195ce0b29a539ab89d4bb5d10950ac12f6d7af807`, complexity 30,113) and Phase 8 on 2026-11-18 via Director review. The [run manifest](../../runs/20261118_system312_g02_01/manifest.json) retains the findings hash from before this approval edit. Human authorized [Phase 9 specification drafting](phase_09.md). H01 test opening requires separate authorization.
