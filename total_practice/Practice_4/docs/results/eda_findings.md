# D01 — Training-only EDA findings

**APPROVED / PHASE 3 COMPLETED** by Human on 2026-11-18 via Director review, run `20261118_system312_d01_01`. Scope: 24,544
canonical train rows, UTC 2014-12-31 23:00 through 2017-10-19 14:00 inclusive.
[Summary table](../../runs/20261118_system312_d01_01/summary.json),
[config](../../runs/20261118_system312_d01_01/config.json) and
[run manifest](../../runs/20261118_system312_d01_01/manifest.json) contain
counts, UTC extrema, parameters and hashes. Figures were promoted from the accepted run; the original run evidence remains unchanged.

The raw city-level 133 m/s wind-speed extreme recorded in B01/B02 has **unverified
train-split membership**. Human authorized proceeding without searching held-out
records; canonical wind is the unweighted five-city mean, not the raw city value.

## Missing and physical sanity

Train has 24,512 observed load hours and 32 missing (0.130%); 18 missing runs:
15 of one hour and one each of 3, 6 and 8 hours. No observed run touches a train
boundary. Weather proxy fields have no missing train values. See summary `gaps`
and [missing/gaps figure](../../runs/20261118_system312_d01_01/figures/missing_gaps.png).

Canonical train extrema, with first UTC occurrence when tied:

| Variable | Minimum | UTC | Maximum | UTC |
|---|---:|---|---:|---|
| Load (MW) | 18041 | 2015-12-25T04:00:00+00:00 | 41015 | 2017-01-18T19:00:00+00:00 |
| Temperature proxy (K) | 271.9418625 | 2015-02-08T05:00:00+00:00 | 309.094 | 2016-09-06T14:00:00+00:00 |
| Humidity proxy (%) | 26.4 | 2015-03-05T13:00:00+00:00 | 100 | 2017-02-24T08:00:00+00:00 |
| Wind proxy (m/s) | 0 | 2017-08-25T10:00:00+00:00 | 29.8 | 2017-05-11T10:00:00+00:00 |

These train extrema pass the basic checks load/wind nonnegative, temperature
positive Kelvin and humidity 0–100%; this does not establish sensor validity.
The wind extreme warrants review but is not proven erroneous. See summary
`extrema` and [distributions](../../runs/20261118_system312_d01_01/figures/extremes.png).

## Time and relationships

[UTC overview](../../runs/20261118_system312_d01_01/figures/load_utc.png) and
[Madrid profiles](../../runs/20261118_system312_d01_01/figures/local_profiles.png)
show recurring hourly and weekday variation: train mean load is about 22,635 MW
at local hour 04 versus 32,007 MW at 13; Sunday mean is about 26,307 MW versus
29,506 MW Wednesday. Counts and medians are in summary `profiles`. UTC remains
the index; Madrid local aggregation counts repeated DST hours separately and
contains partial boundary days. These are descriptive associations, not proof of
future performance or what LSTM learns.

[Load–temperature scatter and correlations](../../runs/20261118_system312_d01_01/figures/relationships.png)
use 24,512 observed load/temperature pairs. The scatter suggests a nonlinear
pattern with considerable spread; it does not establish a stable U-shape or a
heating/cooling causal response. Train Pearson load correlations: temperature
0.236, humidity -0.367, wind 0.209; pair counts and full matrix are in summary.
These associations do not establish the best predictive variable or causality.

[ACF/PACF](../../runs/20261118_system312_d01_01/figures/acf_pacf.png) use the
longest contiguous observed block: 9,271 hours from 2016-09-28T08:00:00+00:00
through 2017-10-19T14:00:00+00:00; 15,241 other observed hours are outside that
block. ACF at lags 1, 24 and 168 is approximately 0.952, 0.706 and 0.654.
ACF uses FFT and PACF Yule–Walker modified (`ywm`), lags 0–168; no confidence
intervals are plotted. This selected block can bias interpretation and neither
plot alone establishes stationarity or a model order.

## D02 proposals and subsequent Human decision

Human approved the max-gap, anomaly and VAR domain policy decisions on 2026-11-18 via Director review. The causal interpretation of multi-hour gaps requires resolution in the Phase 4 draft.

- **Missing load:** propose causal last-observation carry-forward for at most one
  consecutive missing hour in working inputs only. Train contains 15 one-hour
  gaps; its 3-, 6- and 8-hour gaps exceed this proposal. Beyond one hour mark
  context invalid until observed recovery. Keep raw truth and observed mask intact;
  never score imputed labels. This conservative candidate is not a measured optimal
  threshold and needs D02 approval and causal tests.
- **Anomalies:** propose flagging invalid physical values (load/wind < 0,
  temperature <= 0 K, humidity outside 0–100%) and flagging values outside
  train-fitted 0.5th–99.5th percentiles for review. For a proposed working-input
  sensitivity variant only, cap to those fixed train percentiles; preserve raw
  truth and flags, never fit limits on later periods. Percentile limits may cap
  genuine peaks; require Human approval, counts and sensitivity comparison before
  use, and do not call the wind proxy maximum a confirmed sensor error.
- **VAR domain:** propose the observed 9,271-hour block above for a no-fill
  contiguous baseline. This excludes 15,241 other observed train hours and may
  change the fit population; report that limitation. If inadequate after model
  requirements are set, present alternative causal-fill or contiguous-block
  policies for separate approval instead of silently dropping interior gaps.

## Promoted figure provenance

Human authorized promotion on 2026-11-18. Source run: `20261118_system312_d01_01`; SHA256 is identical for the source and promoted bytes. Historical manifest hashes for this findings document and Phase 3 reflect their state at run time, before approval updates.

| Promoted figure | SHA256 |
|---|---|
| [ missing_gaps.png ](../../outputs/figures/missing_gaps.png) | `c3fbb03a6c2404ad8fa7f78023671b654701fb197625a5efffe524a442f943e6` |
| [ extremes.png ](../../outputs/figures/extremes.png) | `8cbf8c92a546884e07d883c678471e814f374f5eb386f57234456b7870471ded` |
| [ load_utc.png ](../../outputs/figures/load_utc.png) | `856c58eaf431debf8d53c2c5bb9bb37a1fbd6af91c366473d0724c8843c2cafd` |
| [ local_profiles.png ](../../outputs/figures/local_profiles.png) | `4400341b9d5862b58cc2abb57ec8f40ad3ef08e261caaeeddff1ce60caf2ac33` |
| [ relationships.png ](../../outputs/figures/relationships.png) | `898327cbe3745e76b8210d9a7107e9a5606ce69539832058709c0baa84e3af21` |
| [ acf_pacf.png ](../../outputs/figures/acf_pacf.png) | `c4253384ab367fac8e22318ce7f3ba296c4dc682abd09900a28eec88fbbbb4ef` |
