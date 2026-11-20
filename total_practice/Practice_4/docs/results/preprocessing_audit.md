# D02 ? Causal preprocessing audit

Status: **APPROVED / COMPLETED**. Human accepted D02 run `20261118_system312_d02_01`, the prepared data, this audit and Phase 4 completion on 2026-11-18 via Director review.

## Method and limits

Train rows 0?24543; validation rows 24544?29802. Only these 29,803 records are parsed, in UTC chronological order. Full input files were hashed as bytes only. Streaming LOCF-1 fills the first missing hour from the preceding observation and leaves subsequent consecutive missing hours and leading missing hours empty; state crosses the split. Raw truth and mask remain unchanged. No clipping, label imputation, windows or models. Remaining NaN context will be excluded after missing-truth exclusion by E02; no real origin counts are computed here.

Physical flags use raw load and weather; percentile flags use available raw train observations for each variable and strict comparisons. Percentiles: 0.5 and 99.5, NumPy `linear` interpolation. Flags do not establish errors. Unexpected invalid or missing weather stops processing. `StandardScaler` is fit on complete finite working-feature train rows; population standard deviation, fixed transform, sklearn zero/near-constant scale behavior.

UTF-8 CSV, empty field means missing, numeric float format `%.17g`; timestamps ISO-8601 UTC, flags and mask boolean. Scaler SHA256 `ebfa412b7bce9ac077776b416df1083eaff32b08c48c28dc5d2e7e06b2757b11`; prepared SHA256 `fbe9ff6f95757caf53482cb522c4e06007840fc7775a145530b89fbb789a415c`. Reloaded inverse maximum error on finite prepared load levels: `0.0` MW.

## Schema and measured results

```json
{
  "schema": [
    {
      "name": "timestamp_utc",
      "dtype": "datetime64[ns, UTC]"
    },
    {
      "name": "load",
      "dtype": "float64"
    },
    {
      "name": "temp",
      "dtype": "float64"
    },
    {
      "name": "humidity",
      "dtype": "float64"
    },
    {
      "name": "wind_speed",
      "dtype": "float64"
    },
    {
      "name": "load_observed",
      "dtype": "bool"
    },
    {
      "name": "load_input",
      "dtype": "float64"
    },
    {
      "name": "load_physical_invalid",
      "dtype": "bool"
    },
    {
      "name": "temp_physical_invalid",
      "dtype": "bool"
    },
    {
      "name": "humidity_physical_invalid",
      "dtype": "bool"
    },
    {
      "name": "wind_speed_physical_invalid",
      "dtype": "bool"
    },
    {
      "name": "load_statistical_extreme",
      "dtype": "bool"
    },
    {
      "name": "temp_statistical_extreme",
      "dtype": "bool"
    },
    {
      "name": "humidity_statistical_extreme",
      "dtype": "bool"
    },
    {
      "name": "wind_speed_statistical_extreme",
      "dtype": "bool"
    },
    {
      "name": "load_input_scaled",
      "dtype": "float64"
    },
    {
      "name": "temp_scaled",
      "dtype": "float64"
    },
    {
      "name": "humidity_scaled",
      "dtype": "float64"
    },
    {
      "name": "wind_speed_scaled",
      "dtype": "float64"
    }
  ],
  "counts": {
    "train": {
      "rows": 24544,
      "missing_truth": 32,
      "missing_working_load": 14,
      "locf_filled": 18,
      "flags": {
        "load_physical_invalid": 0,
        "temp_physical_invalid": 0,
        "humidity_physical_invalid": 0,
        "wind_speed_physical_invalid": 0,
        "load_statistical_extreme": 245,
        "temp_statistical_extreme": 246,
        "humidity_statistical_extreme": 238,
        "wind_speed_statistical_extreme": 148
      }
    },
    "validation": {
      "rows": 5259,
      "missing_truth": 2,
      "missing_working_load": 0,
      "locf_filled": 2,
      "flags": {
        "load_physical_invalid": 0,
        "temp_physical_invalid": 0,
        "humidity_physical_invalid": 0,
        "wind_speed_physical_invalid": 0,
        "load_statistical_extreme": 40,
        "temp_statistical_extreme": 86,
        "humidity_statistical_extreme": 33,
        "wind_speed_statistical_extreme": 66
      }
    }
  },
  "missing_gap_lengths": [
    6,
    1,
    3,
    8,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1
  ],
  "scaler": {
    "schema_version": "1",
    "feature_order": [
      "load_input",
      "temp",
      "humidity",
      "wind_speed"
    ],
    "mean": [
      28552.109702405218,
      290.26302578806514,
      67.47501834488384,
      2.4490827558091985
    ],
    "std": [
      4536.503215172632,
      7.204975167486003,
      14.843465870743465,
      1.3747929371868104
    ],
    "scale": [
      4536.503215172632,
      7.204975167486003,
      14.843465870743465,
      1.3747929371868104
    ],
    "variance": [
      20579861.421271626,
      51.911667164089955,
      220.32847905592604,
      1.8900556201387373
    ],
    "fit_count": 24530,
    "fit_start_row": 0,
    "fit_end_row": 24543,
    "percentiles": [
      0.5,
      99.5
    ],
    "percentile_method": "linear",
    "bounds": {
      "load": {
        "lower": 19605.11,
        "upper": 38758.0,
        "count": 24512
      },
      "temp": {
        "lower": 274.89040300000005,
        "upper": 306.28171000000003,
        "count": 24544
      },
      "humidity": {
        "lower": 33.4,
        "upper": 95.6,
        "count": 24544
      },
      "wind_speed": {
        "lower": 0.4,
        "upper": 7.4,
        "count": 24544
      }
    },
    "locf_max_gap": 1,
    "scikit_learn_version": "1.9.1",
    "numpy_version": "2.5.5",
    "pandas_version": "2.3.3",
    "provenance": {
      "datasets/raw/energy_dataset.csv": "14cd13e020d87af0ab49db8e0f1e4d308320ec5b8d2dec23bab4d27c75c7733a",
      "datasets/raw/weather_features.csv": "3566c3c21179d4fc6691eec6d37a6cfe8fe6a4d9e097f95e4fda4a29dc683b18",
      "datasets/processed/canonical_hourly.csv": "7122e873708d3297e38316a5d29a08236c516fcdf20327e7724edc1d31a83045",
      "datasets/processed/split_manifest.json": "d21e718e1b3661186df9f0848e7bd341b5760a6d29fdd3f48dc51102cd0f307d",
      "split_semantic_sha256": "37a84f769f4f8e2a8180641c4ef68bb5309c88d02eb73c932d93d84c20f898b5"
    }
  },
  "final_stream_state": {
    "last_load": 25194.0,
    "missing_run": 0,
    "last_timestamp": "2018-05-26T17:00:00+00:00"
  }
}
```

## VAR domain and limitations

Observed contiguous train block 2016-09-28T08:00:00+00:00 through 2017-10-19T14:00:00+00:00 has 9,271 hours; 15,241 earlier observed train hours are excluded. The block may not represent the full training history. Extreme values are retained and can affect modeling. Five-city weather is a limited proxy. Source 133 m/s raw wind membership remains unverified. Float64 cannot guarantee 1e-9 MW absolute roundtrip for arbitrarily large values; the actual finite train/validation levels were checked. System Python environment, not a clean-environment reproduction.
