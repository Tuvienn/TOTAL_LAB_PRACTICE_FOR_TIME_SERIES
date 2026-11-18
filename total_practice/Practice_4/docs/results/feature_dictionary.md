# E01 Feature Dictionary

Run `20261118_system312_e01_01` · **PENDING HUMAN REVIEW**

For target row `k`, origin `t` is row `k-1`. The common context is rows `k-25..k-1` inclusive.
Each input is available at the end of its source hour. Target-hour weather and later observations are outside the context.
The fixed D02 working features and their statistics are dimensionless. The label is the observed raw `load` at `t+1` in MW.

LSTM uses a float64 array of shape `(N, 24, 4)`. Its time axis runs oldest to newest from `t-23` through `t`.
Its variable axis is `load_input_scaled`, `temp_scaled`, `humidity_scaled`, `wind_speed_scaled`.
The flat view reshapes these axes in time-major order to `(N, 96)`. XGBoost appends three derived columns for `(N, 99)`.

| 0-based column | Exact name | D02 source | Origin-relative hours | Target-relative hours | Definition |
|---:|---|---|---|---|---|
| 0 | `lag23_load` | `load_input_scaled` | -23 | -24 | Scaled level |
| 1 | `lag23_temperature` | `temp_scaled` | -23 | -24 | Scaled level |
| 2 | `lag23_humidity` | `humidity_scaled` | -23 | -24 | Scaled level |
| 3 | `lag23_wind_speed` | `wind_speed_scaled` | -23 | -24 | Scaled level |
| 4 | `lag22_load` | `load_input_scaled` | -22 | -23 | Scaled level |
| 5 | `lag22_temperature` | `temp_scaled` | -22 | -23 | Scaled level |
| 6 | `lag22_humidity` | `humidity_scaled` | -22 | -23 | Scaled level |
| 7 | `lag22_wind_speed` | `wind_speed_scaled` | -22 | -23 | Scaled level |
| 8 | `lag21_load` | `load_input_scaled` | -21 | -22 | Scaled level |
| 9 | `lag21_temperature` | `temp_scaled` | -21 | -22 | Scaled level |
| 10 | `lag21_humidity` | `humidity_scaled` | -21 | -22 | Scaled level |
| 11 | `lag21_wind_speed` | `wind_speed_scaled` | -21 | -22 | Scaled level |
| 12 | `lag20_load` | `load_input_scaled` | -20 | -21 | Scaled level |
| 13 | `lag20_temperature` | `temp_scaled` | -20 | -21 | Scaled level |
| 14 | `lag20_humidity` | `humidity_scaled` | -20 | -21 | Scaled level |
| 15 | `lag20_wind_speed` | `wind_speed_scaled` | -20 | -21 | Scaled level |
| 16 | `lag19_load` | `load_input_scaled` | -19 | -20 | Scaled level |
| 17 | `lag19_temperature` | `temp_scaled` | -19 | -20 | Scaled level |
| 18 | `lag19_humidity` | `humidity_scaled` | -19 | -20 | Scaled level |
| 19 | `lag19_wind_speed` | `wind_speed_scaled` | -19 | -20 | Scaled level |
| 20 | `lag18_load` | `load_input_scaled` | -18 | -19 | Scaled level |
| 21 | `lag18_temperature` | `temp_scaled` | -18 | -19 | Scaled level |
| 22 | `lag18_humidity` | `humidity_scaled` | -18 | -19 | Scaled level |
| 23 | `lag18_wind_speed` | `wind_speed_scaled` | -18 | -19 | Scaled level |
| 24 | `lag17_load` | `load_input_scaled` | -17 | -18 | Scaled level |
| 25 | `lag17_temperature` | `temp_scaled` | -17 | -18 | Scaled level |
| 26 | `lag17_humidity` | `humidity_scaled` | -17 | -18 | Scaled level |
| 27 | `lag17_wind_speed` | `wind_speed_scaled` | -17 | -18 | Scaled level |
| 28 | `lag16_load` | `load_input_scaled` | -16 | -17 | Scaled level |
| 29 | `lag16_temperature` | `temp_scaled` | -16 | -17 | Scaled level |
| 30 | `lag16_humidity` | `humidity_scaled` | -16 | -17 | Scaled level |
| 31 | `lag16_wind_speed` | `wind_speed_scaled` | -16 | -17 | Scaled level |
| 32 | `lag15_load` | `load_input_scaled` | -15 | -16 | Scaled level |
| 33 | `lag15_temperature` | `temp_scaled` | -15 | -16 | Scaled level |
| 34 | `lag15_humidity` | `humidity_scaled` | -15 | -16 | Scaled level |
| 35 | `lag15_wind_speed` | `wind_speed_scaled` | -15 | -16 | Scaled level |
| 36 | `lag14_load` | `load_input_scaled` | -14 | -15 | Scaled level |
| 37 | `lag14_temperature` | `temp_scaled` | -14 | -15 | Scaled level |
| 38 | `lag14_humidity` | `humidity_scaled` | -14 | -15 | Scaled level |
| 39 | `lag14_wind_speed` | `wind_speed_scaled` | -14 | -15 | Scaled level |
| 40 | `lag13_load` | `load_input_scaled` | -13 | -14 | Scaled level |
| 41 | `lag13_temperature` | `temp_scaled` | -13 | -14 | Scaled level |
| 42 | `lag13_humidity` | `humidity_scaled` | -13 | -14 | Scaled level |
| 43 | `lag13_wind_speed` | `wind_speed_scaled` | -13 | -14 | Scaled level |
| 44 | `lag12_load` | `load_input_scaled` | -12 | -13 | Scaled level |
| 45 | `lag12_temperature` | `temp_scaled` | -12 | -13 | Scaled level |
| 46 | `lag12_humidity` | `humidity_scaled` | -12 | -13 | Scaled level |
| 47 | `lag12_wind_speed` | `wind_speed_scaled` | -12 | -13 | Scaled level |
| 48 | `lag11_load` | `load_input_scaled` | -11 | -12 | Scaled level |
| 49 | `lag11_temperature` | `temp_scaled` | -11 | -12 | Scaled level |
| 50 | `lag11_humidity` | `humidity_scaled` | -11 | -12 | Scaled level |
| 51 | `lag11_wind_speed` | `wind_speed_scaled` | -11 | -12 | Scaled level |
| 52 | `lag10_load` | `load_input_scaled` | -10 | -11 | Scaled level |
| 53 | `lag10_temperature` | `temp_scaled` | -10 | -11 | Scaled level |
| 54 | `lag10_humidity` | `humidity_scaled` | -10 | -11 | Scaled level |
| 55 | `lag10_wind_speed` | `wind_speed_scaled` | -10 | -11 | Scaled level |
| 56 | `lag09_load` | `load_input_scaled` | -9 | -10 | Scaled level |
| 57 | `lag09_temperature` | `temp_scaled` | -9 | -10 | Scaled level |
| 58 | `lag09_humidity` | `humidity_scaled` | -9 | -10 | Scaled level |
| 59 | `lag09_wind_speed` | `wind_speed_scaled` | -9 | -10 | Scaled level |
| 60 | `lag08_load` | `load_input_scaled` | -8 | -9 | Scaled level |
| 61 | `lag08_temperature` | `temp_scaled` | -8 | -9 | Scaled level |
| 62 | `lag08_humidity` | `humidity_scaled` | -8 | -9 | Scaled level |
| 63 | `lag08_wind_speed` | `wind_speed_scaled` | -8 | -9 | Scaled level |
| 64 | `lag07_load` | `load_input_scaled` | -7 | -8 | Scaled level |
| 65 | `lag07_temperature` | `temp_scaled` | -7 | -8 | Scaled level |
| 66 | `lag07_humidity` | `humidity_scaled` | -7 | -8 | Scaled level |
| 67 | `lag07_wind_speed` | `wind_speed_scaled` | -7 | -8 | Scaled level |
| 68 | `lag06_load` | `load_input_scaled` | -6 | -7 | Scaled level |
| 69 | `lag06_temperature` | `temp_scaled` | -6 | -7 | Scaled level |
| 70 | `lag06_humidity` | `humidity_scaled` | -6 | -7 | Scaled level |
| 71 | `lag06_wind_speed` | `wind_speed_scaled` | -6 | -7 | Scaled level |
| 72 | `lag05_load` | `load_input_scaled` | -5 | -6 | Scaled level |
| 73 | `lag05_temperature` | `temp_scaled` | -5 | -6 | Scaled level |
| 74 | `lag05_humidity` | `humidity_scaled` | -5 | -6 | Scaled level |
| 75 | `lag05_wind_speed` | `wind_speed_scaled` | -5 | -6 | Scaled level |
| 76 | `lag04_load` | `load_input_scaled` | -4 | -5 | Scaled level |
| 77 | `lag04_temperature` | `temp_scaled` | -4 | -5 | Scaled level |
| 78 | `lag04_humidity` | `humidity_scaled` | -4 | -5 | Scaled level |
| 79 | `lag04_wind_speed` | `wind_speed_scaled` | -4 | -5 | Scaled level |
| 80 | `lag03_load` | `load_input_scaled` | -3 | -4 | Scaled level |
| 81 | `lag03_temperature` | `temp_scaled` | -3 | -4 | Scaled level |
| 82 | `lag03_humidity` | `humidity_scaled` | -3 | -4 | Scaled level |
| 83 | `lag03_wind_speed` | `wind_speed_scaled` | -3 | -4 | Scaled level |
| 84 | `lag02_load` | `load_input_scaled` | -2 | -3 | Scaled level |
| 85 | `lag02_temperature` | `temp_scaled` | -2 | -3 | Scaled level |
| 86 | `lag02_humidity` | `humidity_scaled` | -2 | -3 | Scaled level |
| 87 | `lag02_wind_speed` | `wind_speed_scaled` | -2 | -3 | Scaled level |
| 88 | `lag01_load` | `load_input_scaled` | -1 | -2 | Scaled level |
| 89 | `lag01_temperature` | `temp_scaled` | -1 | -2 | Scaled level |
| 90 | `lag01_humidity` | `humidity_scaled` | -1 | -2 | Scaled level |
| 91 | `lag01_wind_speed` | `wind_speed_scaled` | -1 | -2 | Scaled level |
| 92 | `lag00_load` | `load_input_scaled` | 0 | -1 | Scaled level |
| 93 | `lag00_temperature` | `temp_scaled` | 0 | -1 | Scaled level |
| 94 | `lag00_humidity` | `humidity_scaled` | 0 | -1 | Scaled level |
| 95 | `lag00_wind_speed` | `wind_speed_scaled` | 0 | -1 | Scaled level |
| 96 | `mean6h` | `load_input_scaled` | -5..0 | -6..-1 | Arithmetic mean of six hourly levels |
| 97 | `std24h` | `load_input_scaled` | -23..0 | -24..-1 | Population standard deviation of 24 hourly levels, `ddof=0` |
| 98 | `trend24h` | `load_input_scaled` | -24, 0 | -25, -1 | Level at `t` minus level at `t-24` |

## Ramp hand check

Synthetic row `i` contains `[i, 100+i, 200+i, 300+i]`. Origin 24 uses context 0–24 and target 25.
- Sequence and flat lag blocks start at `[1, 101, 201, 301]` and end at `[24, 124, 224, 324]`.
- `mean6h = (19 + 20 + 21 + 22 + 23 + 24) / 6 = 21.5`.
- `std24h = sqrt(575/12) = 6.92218655243173` from the population variance of integers 1–24.
- `trend24h = 24 - 0 = 24`.
- The label is row 25's synthetic raw value, `12345 MW`.

## Candidate eligibility

Rows 0–24 are warm-up. Candidate split follows the target timestamp. The first validation target uses the last training hour as its origin.
A missing raw label takes precedence as `missing_truth`. An observed target with a nonfinite value anywhere in its 25 × 4 scaled context is `invalid_context`.
A finite observed truth and finite context are eligible. A raw truth and mask mismatch raises a contract error. Physical and statistical flags leave eligibility unchanged.

## VAR training block

E01 verified a contiguous float64 matrix of shape `(9271, 4)`, using the same four scaled columns.
Prepared rows 15,273–24,543 span `2016-09-28T08:00:00+00:00` through `2017-10-19T14:00:00+00:00`, inclusive.
All block hours are observed, have equal raw and working load, and have finite scaled levels.
The fixed block excludes 15,241 earlier observed train hours and may underrepresent earlier regimes.
The block has its own row axis. F02 owns VAR fitting and adequacy checks.
