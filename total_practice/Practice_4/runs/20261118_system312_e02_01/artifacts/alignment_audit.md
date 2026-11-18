# E02 Alignment Audit

Run `20261118_system312_e02_01` · **PENDING HUMAN REVIEW**

`py -3.12 -m practice_4.pipeline --stage E02 --config config/practice_4.json --run-id 20261118_system312_e02_01` completed successfully. The [execution log](../logs/E02_20261118_system312_e02_01.md) links the separate pytest evidence.

## Scope and conservation

The validated D02 train/validation prefix contains 29,803 UTC rows.
Warm-up excludes target rows 0–24 (25 rows). The candidate manifest contains 29,778 rows and the supervised arrays contain 29,692 eligible samples.
Raw share below uses the full canonical row count from split metadata as the denominator. Dataset records were parsed only from the prepared prefix.

| Target split | Raw rows | Raw share | Start UTC | End UTC | Candidates | Missing truth | Invalid context | Eligible |
|---|---:|---:|---|---|---:|---:|---:|---:|
| train | 24,544 | 69.9977% | 2014-12-31T23:00:00+00:00 | 2017-10-19T14:00:00+00:00 | 24,519 | 32 | 52 | 24,435 |
| validation | 5,259 | 14.9983% | 2017-10-19T15:00:00+00:00 | 2018-05-26T17:00:00+00:00 | 5,259 | 2 | 0 | 5,257 |

Each split passed candidate = missing truth + invalid context + eligible.
The first validation target is row 24,544 at `2017-10-19T15:00:00+00:00`. Its origin is the last train row 24,543 at `2017-10-19T14:00:00+00:00`.
Every target uses exactly the previous 25 hours for eligibility. Each lag and statistic ends at or before the origin. Missing truth takes precedence over nonfinite context.

## RV2 schema v1 round-trip checks

UTF-8 origin CSV used the exact ordered header below. The reload checked all candidate IDs, timestamps, splits, mask and context flags, exclusion reasons, raw values and consecutive eligible sample indices against the prepared source.

```text
schema_version,origin_row,target_row,context_start_row,origin_timestamp_utc,target_timestamp_utc,split,load_observed,context_finite,eligible,exclusion_reason,y_true_mw,sample_index
```

The NPZ ZIP member list, keys, dtypes and shapes passed validation with `allow_pickle=False`. Each eligible sample matched the source by target row, including raw MW truth, 24-hour sequence, time-major flat view and all three XGBoost statistics. Floating-point arrays were finite.

| NPZ key | dtype | Shape |
|---|---|---|
| `schema_version` | `uint8` | `()` |
| `target_row` | `int64` | `(29692,)` |
| `x_lstm` | `float64` | `(29692, 24, 4)` |
| `x_flat` | `float64` | `(29692, 96)` |
| `x_xgb` | `float64` | `(29692, 99)` |
| `y_true_mw` | `float64` | `(29692,)` |
| `var_row` | `int64` | `(9271,)` |
| `var_train_levels` | `float64` | `(9271, 4)` |

The LSTM and VAR variable axes use `load_input_scaled`, `temp_scaled`, `humidity_scaled`, `wind_speed_scaled` in that order.
The XGBoost order runs from `lag23_load` through `lag00_wind_speed`, followed by `mean6h`, `std24h` and `trend24h`. See the [feature dictionary](feature_dictionary.md) for each column.

## VAR block

Rows 15,273–24,543, from `2016-09-28T08:00:00+00:00` through `2017-10-19T14:00:00+00:00` inclusive, were checked for hourly continuity, observed raw load, working/raw equality and finite scaled levels.
The separate VAR axis excludes 15,241 earlier observed hours. The retained block may underrepresent earlier training regimes. Model fitting has its own gate.

## SHA256 provenance

Split semantic SHA256 `37a84f769f4f8e2a8180641c4ef68bb5309c88d02eb73c932d93d84c20f898b5` matched D02 scaler lineage. Protected inputs matched D02 before and after staging.
Raw and canonical files were hashed as opaque bytes. The E01 manifest preserves the original Phase 5 and dictionary digests from before the approval edits.

| Role | Path | SHA256 |
|---|---|---|
| Input | `runs/20261118_system312_e01_01/manifest.json` | `fbac230318eca7df9b821dfba31a501b449fd1db80ef3aa07c059adac6d6eac9` |
| Input | `docs/results/feature_dictionary.md` | `f6b91409f4d9d4194f3bf6539ffca3e4e9a24419cbeba75575dcdf6074851284` |
| Input | `runs/20261118_system312_d02_01/manifest.json` | `50527847fbbda7dc510806301cf95a368de6f39716577d2ca7813d7bd4c3e3ff` |
| Input | `docs/phase_details/phase_04.md` | `1d0118fced94a5239f478afd556c546a8305cc9bc91e874958b6dfbf972736be` |
| Input | `docs/phase_details/phase_05.md` | `6913fa29c8a07776e75020b788fccbcd645bba6daa4e45c0feb6d0d46e23f739` |
| Input | `datasets/raw/energy_dataset.csv` | `14cd13e020d87af0ab49db8e0f1e4d308320ec5b8d2dec23bab4d27c75c7733a` |
| Input | `datasets/raw/weather_features.csv` | `3566c3c21179d4fc6691eec6d37a6cfe8fe6a4d9e097f95e4fda4a29dc683b18` |
| Input | `datasets/processed/canonical_hourly.csv` | `7122e873708d3297e38316a5d29a08236c516fcdf20327e7724edc1d31a83045` |
| Input | `datasets/processed/split_manifest.json` | `d21e718e1b3661186df9f0848e7bd341b5760a6d29fdd3f48dc51102cd0f307d` |
| Input | `datasets/processed/prepared_hourly.csv` | `fbe9ff6f95757caf53482cb522c4e06007840fc7775a145530b89fbb789a415c` |
| Input | `runs/20261118_system312_d02_01/artifacts/scaler.json` | `ebfa412b7bce9ac077776b416df1083eaff32b08c48c28dc5d2e7e06b2757b11` |
| Input | `runs/20261118_system312_d02_01/artifacts/summary.json` | `8e4a4e3d1cb5f7240bbf876e006aebc63408630ae04e9e37bb41db4a809b0903` |
| Output | `runs/20261118_system312_e02_01/artifacts/origin_manifest.csv` | `2c171663ef57bb883b9f345119ff7751bea182160f7391055d2e99408d47e8f6` |
| Output | `runs/20261118_system312_e02_01/artifacts/model_inputs.npz` | `d6f7d245b188ac34df414d92bac6fc9cd881b36357c7bde5e0e3bc1e19e83814` |
| Output | `datasets/processed/origin_manifest.csv` | `2c171663ef57bb883b9f345119ff7751bea182160f7391055d2e99408d47e8f6` |
| Output | `datasets/processed/model_inputs.npz` | `d6f7d245b188ac34df414d92bac6fc9cd881b36357c7bde5e0e3bc1e19e83814` |
| Output | `runs/20261118_system312_e02_01/config.json` | `ca8724e6c18d038cfcdfec6dc655f769ca1d1d8352a23d4e96be7e5a60494ce1` |
| Output | `runs/20261118_system312_e02_01/environment.json` | `d8d3dc210a8181e95c794d8d58de4ade37dec0c6daeef44b67b7717f5a816492` |
| Output | `docs/logs/E02_20261118_system312_e02_01.md` | `a854b4dcb1e75752293c420bbbc0f432ed2300d7fb4ba0f545f55ba8dd1460dc` |

The [run manifest](../../runs/20261118_system312_e02_01/manifest.json) records the SHA256 of this audit and its staged copy. The final manifest digest is recorded in [current status](../status/current_status.md).

E02 gate acceptance, Phase 5 RV2 schema acceptance and Phase 5 completion sign-off are **PENDING HUMAN REVIEW**.
