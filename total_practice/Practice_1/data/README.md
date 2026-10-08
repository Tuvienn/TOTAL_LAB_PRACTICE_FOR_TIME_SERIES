# AirPassengers Dataset Provenance

```text
Dataset: AirPassengers
Canonical CSV: https://vincentarelbundock.github.io/Rdatasets/csv/datasets/AirPassengers.csv
Documentation: https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/AirPassengers.html
Retrieved at: 2026-10-08T14:07:55+07:00
Raw file: data/raw/air_passengers.csv
SHA-256: bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8
Actual schema: rownames,time,value
Observations: 144
Frequency: monthly
Date range after validated conversion: 1949-01-01 through 1960-12-01
Value unit: thousands of international airline passengers
```

The raw `time` field represents fractional years. After validating its 1/12-year
progression and the documented start and frequency, analysis code constructs a
deterministic month-start index. The `rownames` field is a source row identifier and
is not an analytical variable.

The Rdatasets mirror publishes its code under GPL-3 but does not provide a definitive
standalone license for every underlying dataset. This repository records that
limitation and does not claim that GPL-3 directly licenses the AirPassengers data.

The raw CSV is immutable source evidence. Missing-value simulation, transformation,
interpolation and outlier experiments must use in-memory working copies.

