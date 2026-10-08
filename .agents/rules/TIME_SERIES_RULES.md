# TIME SERIES — DATA AND ANALYSIS RULES

## 1. Purpose

These rules apply to Time Series data inspection, preprocessing, exploration, feature engineering, forecasting, validation, evaluation, visualization, and scientific reporting.

They supplement `GENERAL_RULES.md` and `CODE_RULES.md`.

## 2. Raw Data and Provenance

- Treat raw data as immutable source evidence.
- Do not overwrite, silently sort, fill, interpolate, deduplicate, resample, clip, remove outliers, rename fields, or repair timestamps in raw files.
- Store approved derived data separately from raw data.
- Record source, retrieval date, license, checksum, schema, units, frequency, timestamp semantics, and known limitations when required by the scoped project.
- Perform simulated corruption, missing-value experiments, and outlier treatments only on an explicit working copy.

## 3. Time Index Validation

Before analysis or forecasting, validate:

```text
timestamp parsing and type
timezone when applicable
chronological ordering
duplicate timestamps
missing timestamps or intervals
regular versus irregular frequency
date range
sampling granularity
```

Do not silently normalize or repair time-index problems. Report the issue and apply only an approved, documented treatment.

## 4. Data Quality

Check and report:

```text
missing values
duplicate observations
invalid values
outliers
frequency irregularity
unexpected gaps
schema inconsistencies
```

Distinguish clearly between:

```text
observed raw values
simulated corruption
detected issues
proposed treatments
treated working copies
```

Do not automatically delete or replace an outlier. Distinguish seasonal peaks, trend effects, regime changes, data errors, and genuine anomalies when evidence permits.

## 5. Chronology and Information Availability

- Preserve chronological order throughout processing, feature engineering, validation, and reporting.
- Do not shuffle forecasting observations unless an approved task explicitly justifies it.
- Use only information available at the relevant analysis or forecast time.
- Lag features must point backward in time.
- Rolling and expanding features must respect forecast-time availability.
- Do not use centered rolling statistics as forecasting features when they include future observations.
- Do not present backward-fill or two-sided interpolation as real-time forecasting-safe defaults.
- Distinguish historical reconstruction from deployable forecasting-time processing.

## 6. Leakage Prevention

Prevent future-information leakage in:

```text
preprocessing
imputation
scaling
feature engineering
target construction
model selection
validation
evaluation
error analysis
```

Any fitted transformation must use only data available within its training or historical information boundary.

## 7. Analysis Discipline

Before selecting a complex method:

1. Define the problem, target, granularity, horizon, and analysis objective.
2. Inspect the dataset, schema, date range, and time index.
3. Validate data quality.
4. Visualize the series.
5. Analyze trend and seasonality.
6. Inspect temporal dependence using appropriate methods.
7. Check stationarity when required by the intended method.
8. Define validation and metrics.
9. Establish an appropriate baseline.
10. Introduce additional complexity only for a documented reason.

Do not infer a complete model specification solely from one diagnostic such as an ACF or PACF plot on a raw non-stationary series.

## 8. Forecasting Setup

Before model fitting, define:

```text
target
univariate or multivariate setup
forecast origin
forecast horizon
train period
validation period
test period
update or retraining assumptions
evaluation protocol
```

Use chronological holdout, walk-forward validation, or rolling-origin evaluation as appropriate. Do not use random train/test splitting for forecasting unless explicitly approved and scientifically justified.

## 9. Baseline and Metrics

Choose metrics before selecting the final model.

Explain what each metric measures, its limitations, and its relationship to the task objective.

Use an appropriate baseline before a complex model, such as:

```text
naive or persistence
seasonal naive
moving-average baseline
another approved task-appropriate baseline
```

If a model does not beat the baseline, report it honestly and investigate why.

## 10. Statistical and Scientific Evidence

- Record relevant configuration, including random seed, lag limits, confidence levels, seasonal periods, rolling windows, decomposition settings, and evaluation boundaries.
- Use an explicit seed for stochastic experiments.
- Do not conclude white noise from visual inspection alone when a statistical diagnostic is required.
- Explain whether decomposition assumptions are additive, multiplicative, or transformed-additive and identify the analysis scale.
- Ensure residual conclusions are supported by appropriate diagnostics.
- Trace every statistical conclusion to actual configuration and execution evidence.

## 11. Missing-Value Experiments

For simulated missing values:

- Create missingness only on a working copy.
- Preserve true values at masked positions.
- Compare treatment methods on the same positions.
- Use metrics that evaluate only the intended masked observations when appropriate.
- State whether a treatment is intended for historical analysis, offline reconstruction, or forecast-time operation.

## 12. Visualization and Interpretation

- Use plots appropriate to the data granularity and analytical question.
- Inspect plots rather than merely generating them.
- Explain trend, seasonality, variability, temporal dependence, anomalies, and limitations supported by the figure.
- Do not present a plot as evidence for a claim it cannot establish.

## 13. Model Choice and Explainability

Prefer the simplest method that can answer the approved question.

For each proposed model or analytical method, state:

```text
rationale
data requirements
expected trade-offs
failure modes
evaluation plan
```

Use a more complex or less interpretable model only when evidence and the approved objective justify the trade-off.

## 14. Error Analysis and Conclusion

Analyze:

```text
periods with large errors
seasonal or regime-dependent errors
outliers and structural breaks
baseline versus model behavior
residual structure
limitations and unresolved issues
```

Conclusions must state whether the evidence supports forecastability or model improvement without claiming unexecuted performance.

## 15. Completion Standard

Time Series work is not complete until relevant requirements are verified, including:

```text
raw data remained unchanged
time order was preserved
timestamp and frequency issues were assessed
missing values and intervals were assessed
future leakage was prevented
required outputs exist and were inspected
conclusions are traceable to execution evidence
limitations are reported honestly
```
