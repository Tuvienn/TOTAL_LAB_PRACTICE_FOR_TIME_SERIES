# EXERCISE 04 — EXECUTION EVIDENCE LOG

## Record Status

```text
record type: retrospective record of persisted notebook output
execution owner: Human-reported notebook run
execution timestamp: not available in the persisted evidence reviewed
assistant rerun in this documentation task: no
formal E04 completion: not established
E04-to-E05 handoff: remains open pending reconciliation
```

This log records evidence available in `notebooks/Practice_2_present.ipynb`. It does
not claim that E04 was run from a clean kernel or that its formal approval and
completion gates were met. The E04 specification and before-process plan remain
drafts; see `docs/status/current_status.md`.

## Scope

ACF/PACF and provisional ARIMA candidate evidence for Dataset 1, Monthly Retail
Sales (`a10.csv`). E04 does not fit models, calculate AIC/BIC, diagnose model
residuals, forecast, or open the test set.

## Expected Input and Evidence Limitations

```text
expected input: E03 log_first_differenced_training
expected transformation: natural_log
expected regular differencing order: d = 1
expected observations: 162
expected missing values: 0
test set: 41 observations, must remain excluded
```

The persisted notebook candidate table labels its analysis scale as
`natural_log`, but the reviewed outputs do not establish that every ACF/PACF
diagnostic was computed from the exact E03 `log_first_differenced_training`
series. The input identity, timestamp boundary, and test-set exclusion therefore
remain unverified for E04.

## Persisted Notebook Results

The candidate table contains three provisional entries:

| Candidate | Order | Persisted rationale summary | Status |
|---|---|---|---|
| ARIMA(1,1,1) | (1,1,1) | ACF described as cutting after lag 1; PACF has a strong lag-1 spike | Provisional |
| ARIMA(2,1,1) | (2,1,1) | ACF described as cutting after lag 1; PACF lags 1–2 cited | Provisional |
| ARIMA(4,1,1) | (4,1,1) | PACF signal through lag 4 cited | Provisional |

The current E04 specification permits one or two candidates, so the recorded
three-row table does not satisfy that candidate-count requirement.

A separate persisted seasonal-reference output reports:

| Lag | ACF | ACF significant | PACF | PACF significant |
|---:|---:|---|---:|---|
| 12 | 0.8444 | Yes | 0.5121 | Yes |
| 24 | 0.7044 | Yes | -0.0571 | No |
| 36 | 0.6052 | Yes | -0.0273 | No |

The saved printout does not establish that this seasonal-reference result came
from the required log first-differenced training input. Treat it as recorded
notebook output, not as validated evidence for the E04 handoff.

## Outputs

Notebook plots and tables are present as persisted cell outputs. At the time of
this record, no dedicated E04 ACF/PACF figure or result CSV was present in
`outputs/figures/` or `outputs/results/`.

## Validation and Decision

```text
E03 input identity reproduced: not verified
162-observation / no-missing input contract: not verified for ACF/PACF execution
test-set exclusion: not independently verified
ACF/PACF configuration and confidence level: not fully traceable from saved evidence
candidate count within 1–2: no, three candidates recorded
candidate rationale traceable to approved input: not established
clean-kernel notebook run: not performed
targeted E04 tests: not run
```

The notebook output is useful as exploratory evidence, but does not establish a
validated E04 handoff. The formal E04 handoff remains open. Do not treat these
candidates as approved inputs to a formally completed E05 without reconciling
the input provenance, candidate count, approval state, and current status.
