# Exercise 04 — Execution Evidence

## Run context

- Source: `notebooks/Practice_2_Exercise.ipynb`
- Input: log-first-difference training series (`n=162`)
- Maximum lag: `36`
- PACF method: `ywm`
- Confidence level: `95%`
- Test values used: false
- Status: confirmed and validated

## Handoff

ACF and PACF were calculated from the transformed training series and made
available as styled tables and a combined figure:

- `outputs/figures/03_acf_pacf_log_first_differenced.png`

The two candidates passed to E05 are `ARIMA(1,1,1)` and
`ARIMA(0,1,1)`, matching the 1–2 ARIMA-candidate scope in the exercise brief.
SARIMA is reserved for the E06 extension. E04 does not choose a final model.
Candidate performance is not treated as final selection evidence until the
formal E04/E05 confirmation state is reconciled.
