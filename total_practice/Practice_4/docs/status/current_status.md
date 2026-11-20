# Current Status — Practice 4

Technical work for Phases 0–10 is complete. The user explicitly delegated completion of Practice 4 and authorized proceeding through the remaining work on 2026-11-20. Phase 8.5 replay, Phase 9 H01/H02 and Phase 10 I01/I02 evidence are recorded below and in their run logs. No claim is made that the user separately reviewed the final reports after their creation.

## Historical progress notes (superseded by the completion record above)

The following notes preserve the state recorded during earlier phases; they are not the current status.

The system Python 3.12 probe raised `ModuleNotFoundError: No module named 'tensorflow'`; `pip show tensorflow keras` found neither package, while `pip check` reported no broken requirements. Installation requires separate Human approval. No G02 training code or configuration was written and no test records were accessed.

Human approved `tensorflow==2.20.0` and `keras==3.11.3` on 2026-11-18 via Director review and manually installed them. The follow-up probe confirmed those versions, TensorFlow backend, CPU visibility and a clean `pip check`. Existing lock versions matched and the initial dependency block was resolved.

The synthetic EarlyStopping and `.keras` save/load smoke did not complete after more than one minute and was interrupted. A partial checkpoint appeared, but save/load parity was not established. The script and partial file remain under `runs/g02_smoke_20261118/` for inspection. No pre-fit configuration or G02 trial was created.

The [2026-11-18 serialization diagnostic](../phase_details/phase_08.md#4-dependencies-and-artifacts) reproduced the ZIP stall under both CPU thread and oneDNN configurations with `HDF5_USE_FILE_LOCKING=FALSE`. Both subprocesses timed out at 15 seconds inside Python temporary file creation for the Keras asset store. Direct `.weights.h5` save/load passed in 0.031979 seconds with exact synthetic prediction parity. Human approved the weights plus architecture JSON amendment on 2026-11-18 and authorized G02 continuation.

## Đã hoàn thành ở mức lập kế hoạch

- Đã đọc đề bài Practice 4 và các quy tắc repository áp dụng.
- Human đã chọn **Hourly energy demand, generation and weather** làm dataset chính.
- Human đã thống nhất kiến trúc tổng quan gồm Phase 0–10:
  - Phase 0: Problem Definition;
  - Phase 1: Data Preparation;
  - Phase 2: Temporal Split và Validation Design;
  - Phase 3: EDA chỉ trên training set;
  - Phase 4–9: preprocessing, feature engineering, modeling và final evaluation;
  - Phase 10: End-to-End Notebook và Final Report.
- Đã thực hiện preliminary read-only inspection đối với archive công khai:
  - `energy_dataset.csv`: 35.064 dòng, 29 cột, hourly 2015–2018;
  - `weather_features.csv`: 178.396 dòng, 17 cột, weather của năm thành phố;
  - `total load actual` có 36 giá trị thiếu;
  - ba trường `temp`, `humidity`, `wind_speed` không thiếu;
  - có các city-hour bị lặp do nhiều weather descriptions, nhưng ba trường weather
    bắt buộc giống nhau trong các bản lặp đã kiểm tra.
- Roadmap và project overview vẫn là draft. Phase 0 specification/before-process
  plan đã được Human duyệt ngày 2026-11-17; xem `docs/phase_details/phase_00.md`.
- Human đóng gate A01 ngày 2026-11-17 qua tin nhắn `Close Gate A01 & Execute
  Phase 0 — Stage A02`; chi tiết tại `docs/phase_details/phase_00.md`.
- Human đóng gate A02 / Phase 0 ngày 2026-11-17 qua tin nhắn `Close Phase 0
  (Gate A02) & Draft Phase 1 Specification`; đã soạn Phase 1 specification draft.
- Human duyệt Phase 1 specification và yêu cầu B01 dùng system Python 3.12,
  xác nhận metadata nguồn và core dependencies trong yêu cầu ngày 2026-11-18.
- B01 run `20261118_system312_01` đã tạo audit, source manifest, run manifest và
  execution log; targeted tests đạt 5/5. Human duyệt B01 và policy B02 ngày
  2026-11-18 theo yêu cầu `Close Gate B01 & Execute Stage B02`.
- Human duyệt B02 run `20261118_system312_b02_01`, canonical dataset, data
  contract và đóng Phase 1 ngày 2026-11-18 theo yêu cầu `Close Phase 1 (Gate B02)
  & Draft Phase 2 Specification`. Phase 2 specification và before-process plan được
  Human APPROVED ngày 2026-11-18 qua Director review; chỉ C01 được phép thực thi.
- Approval record và contract header được cập nhật sau B02 run: hash hiện tại
  của hai tài liệu khác hash tại thời điểm run trong B02 manifest; manifest được
  giữ nguyên như evidence lịch sử. Raw và canonical data không đổi bởi việc này.
- C01 run `20261118_system312_c01_01` và split manifest được Human APPROVED
  2026-11-18 qua Director review; C02 được phép thực thi.
- C02 run `20261118_system312_c02_01`, evaluation contract và Phase 2 được
  Human APPROVED / COMPLETED ngày 2026-11-18 qua Director review; RV2 đóng.
  Phase 3 specification và before-process plan được Human APPROVED ngày
  2026-11-18 qua Director review; D01 được phép thực thi.
- Header Phase 2 và evaluation contract cập nhật sau C02 approval; hash hiện tại
  khác C02 run manifest lịch sử, manifest được giữ nguyên để bảo toàn provenance.
- D01: Python 3.12 import được matplotlib 3.11.2 với Agg, statsmodels 0.14.6,
  tzdata 2026.5 và pandas 2.3.3; đã ghi versions và khóa config trước EDA.
  Evidence B01/B02 xác nhận một raw 133 m/s record nhưng không ghi timestamp;
  Human cho phép tiếp tục ngày 2026-11-18 qua Director review; train membership
  của raw record được ghi là chưa xác minh, không mở held-out rows để tìm.
- D01 run `20261118_system312_d01_01`, findings and Phase 3: Human APPROVED / COMPLETED on 2026-11-18 via Director review. Six figures were promoted with hashes in findings. Raw 133 m/s train membership remains unverified.

## Chưa thực hiện

- Human đã đặt hai CSV trong `datasets/raw/`; đã kiểm tra read-only và ghi hash,
  counts cùng limitations trong `docs/results/data_audit.md`.
- Human xác nhận source, version 1, CC0, units và time semantics; Kaggle page/API
  chưa được xác minh độc lập trong môi trường này. Archive hash chưa có.
- Data contract Phase 1 và Phase 2 specification đã được Human chấp nhận.
- Editable install vào system Python 3.12 đã chạy; không tạo virtualenv hoặc
  kiểm clean-environment reproduction. B01 đã được Human chấp nhận.
- Đã có B01/B02 pipeline và tests; notebook template có 12 Markdown cells, chưa
  có final executable notebook hoặc model training.

Kiểm tra ngày 2026-11-17 không thấy `LD2011_2014.txt` trong `datasets/raw/`;
không suy diễn nguyên nhân. UCI không phải dataset chính đã chọn.

## Accepted D02 evidence

- Run `20261118_system312_d02_01` processed 24,544 train and 5,259 validation hours; scaler fit count 24,530. Test records were not parsed.
- Preprocessing tests: 9 passed; splitting/walk-forward/metrics regression: 17 passed. Deprecation warnings are recorded in the D02 log.
- Raw, canonical and split hashes matched D01 lineage before and after processing; persisted data and manifest hashes were independently verified. See `docs/results/preprocessing_audit.md` and run manifest.
- Human accepted the D02 run, prepared CSV, preprocessing audit and Phase 4 completion on 2026-11-18 via Director review. The Phase 4 approval record and audit header were updated after the run. The D02 manifest and staged audit retain their run-time hashes and wording.

## Accepted E01 evidence

- Run `20261118_system312_e01_01` completed with exit code 0 on system Python 3.12.10. The [feature dictionary](../results/feature_dictionary.md), [run manifest](../../runs/20261118_system312_e01_01/manifest.json) and [execution log](../logs/E01_20261118_system312_e01_01.md) record the accepted execution.
- `py -3.12 -m pytest tests/test_features.py` passed 23 tests. `py -3.12 -m pytest tests/test_preprocessing.py tests/test_splitting.py tests/test_walk_forward.py tests/test_metrics.py` passed 26 tests with 21 existing NumPy timedelta deprecation warnings. `py -3.12 -m pytest tests/test_pipeline.py` passed 2 tests. Pytest plugin autoload and cache were disabled for these commands.
- The ramp verified the 24 x 4 sequence, 96 flat lags, three appended XGBoost statistics and the distinct raw target. Synthetic tests covered target-hour weather invariance, split carry and exclusion precedence. E01 validated all 29,803 prepared UTC rows and extracted the exact 9,271 x 4 VAR train block in memory. Its exclusion of 15,241 earlier observed hours limits representativeness.
- Independent before/after SHA256 checks matched for both raw CSVs, the canonical CSV, split manifest, prepared CSV and D02 scaler. Raw and canonical CSV access was byte hashing only. Parsed records were restricted to the prepared prefix ending at row 29,802.
- Human approved the E01 run and feature dictionary on 2026-11-18 via Director review and authorized E02 execution. The E01 manifest stays as run-time evidence. Its Phase 5 specification and dictionary hashes precede the approval edits.

## Accepted E02 evidence

- Run `20261118_system312_e02_01` completed with exit code 0 on system Python 3.12.10. The [alignment audit](../results/alignment_audit.md), [execution log](../logs/E02_20261118_system312_e02_01.md) and [manifest](../../runs/20261118_system312_e02_01/manifest.json) document RV2 schema v1 validation. Manifest SHA256 `620c4922f563c2032df14924df221ed3701d49266d1eef37a6c6e59acc8782b5`.
- Warm-up covered 25 rows. Train had 24,519 candidates, 32 missing truths, 52 invalid contexts and 24,435 eligible samples. Validation had 5,259 candidates, 2 missing truths, 0 invalid contexts and 5,257 eligible samples. Both splits passed count conservation.
- The promoted [origin manifest](../../datasets/processed/origin_manifest.csv) contains 29,778 candidates. The promoted [model inputs](../../datasets/processed/model_inputs.npz) contain 29,692 supervised samples and the separate 9,271-row VAR block. Reload verified all CSV records and eight NPZ arrays against the prepared source.
- `py -3.12 -m pytest tests/test_features.py` passed 42 tests. `py -3.12 -m pytest tests/test_preprocessing.py tests/test_splitting.py tests/test_walk_forward.py tests/test_metrics.py` passed 26 tests with 21 existing NumPy timedelta deprecation warnings. `py -3.12 -m pytest tests/test_pipeline.py` passed 2 tests. Pytest plugin autoload and cache were disabled.
- Independent before/after SHA256 checks matched both raw CSVs, canonical CSV, split manifest, prepared CSV and D02 scaler. All 12 manifest input and 9 output SHA256 values were verified after promotion. Raw and canonical access consisted of byte hashing only. Parsed dataset records ended at prepared row 29,802. No test tensors were created and no models were fitted.
- Human approved the run, promoted CSV and NPZ, alignment audit, Phase 5 RV2 schema v1 and Phase 5 completion on 2026-11-18 via Director review. The Phase 5 approval record and audit header were updated after the run. The historical manifest and staged audit retain the run-time hashes and wording.

## Phase 6 approval and F01

- Human approved the [Phase 6 specification and before-process plan](../phase_details/phase_06.md) and authorized F01 execution on 2026-11-18 via Director review. F01 gate acceptance, F02 execution and H01 test opening retain separate approval gates.

## F01 evidence for Human review

- Run `20261118_system312_f01_01` completed. [Baseline report](../results/baseline_results.md), [execution log](../logs/F01_20261118_system312_f01_01.md) and [run manifest](../../runs/20261118_system312_f01_01/manifest.json) record the evidence.
- The targeted pytest command passed 10 tests. Prediction keys matched and metrics were recomputed within relative tolerance 1e-12. Upstream hashes matched before and after the run.
- Human approved the F01 run, baseline report and both RV2 model hashes on 2026-11-18 via Director review and authorized F02. The F01 manifest retains the baseline report hash from before this approval edit.

## F02 stationarity stop

- Run 20261118_system312_f02_01 stopped under the original rule for conflicting ADF/KPSS evidence. [Diagnostics](../../runs/20261118_system312_f02_01/stationarity.json), [locked config](../../runs/20261118_system312_f02_01/config.json), and [log](../logs/F02_20261118_system312_f02_01.md) contain the evidence. Human resolved Q08 by specifying d=[0,0,0,0] on 2026-11-18 via Director review.
- The stop was resolved by Human under Q08. F02 and Phase 6 were subsequently accepted on 2026-11-18 via Director review.

## F02 evidence for Human review

- Run 20261118_system312_f02_02 completed with VAR(24). [Results](../results/var_results.md), [log](../logs/F02_20261118_system312_f02_02.md), and [manifest](../../runs/20261118_system312_f02_02/manifest.json) record results and hashes. Model SHA256 0b3820731f3369f57699adaa64a7b1f4a5cbbf659c48331fc5721335572d3e26.
- Targeted tests passed 14 cases. Forecast keys and truths match F01. Residual whiteness was rejected at 5%. Human approved F02, the VAR(24) model lock and Phase 6 completion on 2026-11-18 via Director review.

## Phase 7 approval and G01 execution

- The 2026-11-18 Director review authorized G01 execution. The required `py -3.12` import probe raised `ModuleNotFoundError: No module named 'xgboost'` under system Python 3.12.10 (Windows x64). Human approved `xgboost==3.4.1` on 2026-11-18 via Director review. The existing installation, core package versions, pip check and early-stopping and model save/load smoke test passed. The stop occurred before configuration lock, implementation, training, or any dataset access. F02 model artifact was accepted as-is, with feature-order and scaler-hash direct embedding recorded as a limitation. The F02 manifest and run-time report hash remain historical evidence.

## G01 acceptance and Phase 7 closure

- Run 20261118_system312_g01_01 completed 18 trials. [Findings](../results/xgboost_findings.md), [manifest](../../runs/20261118_system312_g01_01/manifest.json), and [log](../logs/G01_20261118_system312_g01_01.md) record the results and recovery of manifest creation. Targeted tests passed 14 cases. Human accepted G01, the findings, the XGB_full lock (SHA256 e7386e8cfc38d51d6abc51abad383fb2c9d6360c9c955c6fe3ddb33883aec8ae, complexity 931) and Phase 7 completion on 2026-11-18 via Director review. The run manifest retains the findings hash from before the approval header edit.

## Accepted G02 evidence

- Run `20261118_system312_g02_01` completed the two approved CPU trials. C02 selected `lstm_lr_001` (best epoch 47, 30,113 trainable parameters) with validation MAE 320.692 MW, RMSE 504.751 MW and MAPE 1.1309%. See the [findings](../results/lstm_findings.md), [manifest](../../runs/20261118_system312_g02_01/manifest.json) and [execution log](../logs/G02_20261118_system312_g02_01.md).
- Weights SHA256 `512715c5249f35bcfe46d1ecdbfc4413dbb1d3f263fe73f41dc9845fe5a69a1c`. Architecture SHA256 `c858df9f6417ac508d9b4d2195ce0b29a539ab89d4bb5d10950ac12f6d7af807`. Manifest SHA256 `5baa3e252753d65edefe7e185e57a5e578cac6dea0f639643400ce096853bf47`.
- 56 tests passed. A fresh process reloaded the checkpoint with 0 MW maximum absolute prediction difference across 5,257 rows. Independent checks recomputed the scores and exact UTC lag correlations. All 71 upstream SHA256 values matched. The last validation target row was 29,802. Raw and canonical CSVs were byte hashed only.
- Human approved G02, the LSTM findings and lock, and Phase 8 completion on 2026-11-18 via Director review. The G02 manifest retains the findings hash from before this approval edit.

## Phase 8.5 replay evidence for Human review

- Four isolated replays completed. [Evidence index](../logs/training_evidence/20261118_system312_p85_batch_01/README.md) links seven model-specific logs and records metrics, commands, versions and digests.
- All 26 snapshot hashes matched after replay. All comparisons used 5,257 matching validation keys and truths. Baseline, XGBoost and LSTM metrics matched; VAR differences were at most 1.26e-12 in the reported metrics. Selected XGBoost and LSTM hashes matched. The replay VAR serialized bytes differed with maximum coefficient difference 4.65e-15. Accepted model locks remain authoritative.
- Targeted tests passed 27 cases after final changes, with eight Keras/NumPy deprecation warnings. Baseline and VAR elapsed times were not instrumented. XGBoost per-round logs were saved after each trial during this replay; streaming was enabled afterward.


## Phase 8.5, Phase 9 and Phase 10 completion record

- Phase 8.5: four scientific replays completed; validation keys/truths and selected model locks matched accepted evidence, subject to the recorded floating-point VAR serialization difference. Evidence is indexed at [replay logs](../logs/training_evidence/20261118_system312_p85_batch_01/README.md).
- H01 run `20261120_system312_h01_03` completed on Python 3.12.10. It scored 5,259 common targets from 5,261 candidates (2 missing truths, 0 invalid inputs); test predictions and metrics were promoted. Run evidence and source hashes are in the [H01 log](../logs/H01_20261120_system312_h01_03.md) and manifest. Two failed precursor runs were retained without promotion.
- H02 run `20261120_system312_h02_02` completed from the accepted H01 outputs. It produced 270 grouped model/group rows, three figures and the six-question [comparison report](../results/model_comparison.md). No canonical test rows were reopened.
- Phase 10 run `20261120_system312_i01_01` created the [final report](../results/final_report.md) and [end-to-end notebook](../../notebooks/practice_4_end_to_end.ipynb). All notebook cells executed successfully offline using official artifacts only. The execution record is under `runs/20261120_system312_i01_01/artifacts/`.
- The dedicated Python 3.12.10 environment passed `pip check`; notebook kernel dependencies are pinned separately in `requirements-notebook.lock.txt`. Model and analytical dependencies in `requirements.lock.txt` were not changed.
- Known limitations remain: weather is a five-city proxy, test is a partial-year window, and the walk-forward interpretation assumes the observed target becomes available for the next forecast. Phase 8.5 final Human review of replay evidence is not separately documented as a Director approval.
