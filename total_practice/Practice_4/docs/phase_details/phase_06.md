# Phase 6 — Baselines and VAR/VECM statistical models (F01–F02)

Status **SPECIFICATION APPROVED**, F01 **APPROVED / COMPLETED**, and F02 and Phase 6 **APPROVED / COMPLETED**. Human approved F02 and its VAR(24) model lock on 2026-11-18 via Director review.

The forecast target is the observed raw load at hour `t+1` in MW. F01 establishes two zero-parameter reference forecasts. F02 evaluates a four-variable statistical model against them using the same eligible validation origins and truths.

Sources for scope, chronology and decision gates are the [roadmap, Cụm F and §§4.2–5](../plans/plan_overview.md), [C02 evaluation contract](../results/evaluation_contract.md), [file map](../plans/file_map.csv), [Phase 5 approval and RV2 schema](phase_05.md), and [E02 alignment audit](../results/alignment_audit.md).

## 1. Inputs, chronology and shared scoring

- Verify the approved [E02 run manifest](../../runs/20261118_system312_e02_01/manifest.json), [origin manifest](../../datasets/processed/origin_manifest.csv), [model inputs](../../datasets/processed/model_inputs.npz), and [D02 scaler](../../runs/20261118_system312_d02_01/artifacts/scaler.json) against the accepted run lineage and artifact SHA256 values. E02 manifest hashes for the Phase 5 specification and audit describe their run-time revisions. Use the current approval records for authorization.
- Join eligible CSV rows to the supervised NPZ axis by `sample_index` and check `target_row`, origin and target UTC keys, split and exact `y_true_mw`. Target hour determines split. The common context is `t-24..t` inclusive. The first validation target is row 24,544 and may use the last train hour as origin.
- Phase 6 access ends at prepared row 29,802. H01 owns the separate test opening gate for rows `>= 29803`. Read only the approved scoped inputs. F02 may read [prepared levels](../../datasets/processed/prepared_hourly.csv) through the preceding hour for the extra context row and must verify that prefix against E02 lineage. No changes to the D02 scaler, treatment state, E02 masks or artifacts.
- Preserve chronological predict–score–reveal semantics. Use only working load and weather revealed by the end of `t`, which is the lab's availability assumption. A missing raw target remains a missing observation and any subsequent working input follows the fixed D02 treatment. Forecasts never enter the observed history. An excluded origin does not prevent subsequent hours from becoming available as context. Check complete fitted-state snapshots before and after validation.
- Reuse the C02 metrics owner. Calculate MAE and RMSE in MW on every eligible pair. Calculate MAPE as a percentage on nonzero truths with no epsilon. Report `n_zero_excluded` as a subset of `n_scored` and use null with a reason if all scored truths are zero. Use the approved scaler's stored `mean[0]` and `scale[0]` to restore load as `scaled_load * scale[0] + mean[0]`. Keep finite predictions on their restored scale without clipping.
- Report candidate, missing-truth, invalid-context and scored counts plus the separate 25-row warm-up. Train counts are 24,519 = 32 + 52 + 24,435. Validation counts are 5,259 = 2 + 0 + 5,257. Forecast errors and nonfinite values fail the run. Comparisons use all 5,257 eligible validation keys and identical truths.
- Use the C02 selection order downstream. Take candidates within `1e-6` MW of minimum validation RMSE, then lowest MAE, then model order `persistence`, `seasonal24`, `VAR`, `XGB`, `LSTM`, then lower complexity, then trial ID. The F02 artifact records its VAR or VECM form under the C02 `VAR` model family. The F02 lag and form decisions use train evidence only.

## 2. F01 — Persistence and Seasonal-24 baselines

| Model ID | One-hour-ahead MW forecast | Approved feature |
|---|---|---|
| `persistence` | `load_input(t)` | Inverse-scale `lag00_load` / `x_lstm[:, -1, 0]`. |
| `seasonal24` | `load_input(t-23)`, 24 hours before the target | Inverse-scale `lag23_load` / `x_lstm[:, 0, 0]`. |

Verify that named flat lags equal the corresponding sequence elements. Score each baseline on all 24,435 eligible train targets and all 5,257 eligible validation targets. Train scores describe the reference forecasts over train origins. They involve zero estimated parameters and therefore `complexity = 0` for both models.

Record model ID, stable trial ID, implementation version and a SHA256 of canonical UTF-8 model configuration bytes for each baseline. The model configuration binds the implementation version and source hash, horizon, lag offset, scaler hash and protocol/schema version. Record the resulting baseline version/config digest as its RV2 model hash. Store both splits' predictions with keys, truths, split and run ID under the F01 run. Report each split's counts and metrics in the F01 report. Human acceptance of both baselines precedes F02.

## 3. F02 — VAR / VECM statistical model (Q08)

### 3.1 Fit domain and pre-fit configuration

Use only `var_train_levels` from the approved NPZ for stationarity tests, lag and rank selection, parameter estimation and train residual diagnostics. Verify shape `(9271, 4)`, finite values and `var_row = 15,273..24,543` inclusive. The contiguous UTC block runs from `2016-09-28T08:00:00+00:00` through `2017-10-19T14:00:00+00:00`. Column order is load, temperature, humidity, wind speed. The block excludes 15,241 earlier observed train hours, which limits representativeness. The common train sample set used by F01 is not a fit matrix.

Proposed for Human approval: lock **BIC** in the immutable run config before fitting, with `p = 1..24`, a constant and no trend in the VAR, and the diagnostic settings below. AIC requires an approved config revision before fitting. BIC penalizes increasing lag dimension more strongly and keeps the search bounded. Record the config SHA256 plus exact Python, NumPy, statsmodels and implementation versions. Validation performance does not choose the criterion, `d`, lag, rank or retry policy.

### 3.2 Stationarity, lag and cointegration

Human resolved the conflicting diagnostics on 2026-11-18 via Director review. For this F02 run use ADF at 5% as the primary integration-order rule and set all four entries of the d-map to zero. This decision supersedes the conflicting-evidence stop in step 1 for the recorded diagnostics. Retain KPSS results as diagnostics. Human attributes the weather disagreement to annual seasonal variation and considers differencing potentially excessive. This proposed explanation is not established by the two tests alone.

1. Use ADF with a constant, `maxlag=24`, `autolag=BIC` and KPSS with a constant and `nlags=24`, both at 5%. ADF's null is a unit root. KPSS's null is stationarity around a constant. On each column's levels, accept `d=0` when ADF rejects and KPSS does not reject. If ADF does not reject and KPSS rejects, apply the same checks to the first differences of that column within the block and accept `d=1` only if both support stationarity there. Record statistics, p-values, critical values, chosen lags, sample sizes and warnings, including bounded KPSS p-values. Stop for conflicting, unusable or unresolved evidence. Persist the four-entry `d` map.
2. Search the 24 VAR lag orders on the transformed four-column matrix, aligning all candidate response windows to block-relative index 25 through 9,270 inclusive so every BIC compares the same response hours. Use the same deterministic terms for all candidates. Record the BIC and fit status for each `p`. Choose minimum finite BIC, with smaller `p` for exact ties. No silent candidate drops. A singular or invalid search stops for review.
3. With any `d=0` column, fit the selected VAR on the transformed matrix. When all columns are classified `d=1`, run the Johansen trace rank test at 5% on the original scaled levels in the same block using the selected `p` as the number of lagged differences and a constant specification (`det_order=0`). Rank 0 retains the differenced VAR. Rank 1–3 fits one VECM with `r` equal to the selected rank, `k_ar_diff=p`, a constant outside the cointegration relation (`deterministic="co"`), and no exogenous series. Rank 4 conflicts with the all-`I(1)` decision and stops for review. VECM uses the lag order screened by the train VAR BIC and rank selected by the trace test. Treat this constrained search as a limitation and record rank evidence. [statsmodels VECM specification](https://www.statsmodels.org/stable/generated/statsmodels.tsa.vector_ar.vecm.VECM.html), [Johansen rank test](https://www.statsmodels.org/stable/generated/statsmodels.tsa.vector_ar.vecm.select_coint_rank.html).
4. Estimate the chosen form once on all usable response rows within the approved block, allowing presample rows only inside that block. For VAR with all `d=0`, the causal forecast context is `t-p+1..t`. With any `d=1`, computing `p` differences requires `t-p..t`. VECM likewise uses `p` lagged differences plus the scaled level at `t`. With `p <= 24`, the largest context is exactly 25 rows `t-24..t`, so E02 eligibility suffices without a rebuild.

### 3.3 Diagnostics, validation and model identity

- Report companion-matrix eigenvalues and moduli on the fitted scale. Require all VAR companion moduli below 1. For VECM, identify the expected `4-r` unit eigenvalues at +1 within a proposed absolute tolerance of `1e-8` and require stable remaining modes outside that unit-root tolerance. Stop for an unexpected unit root or instability. Report the adjusted multivariate Portmanteau residual-whiteness result at lag 48 with statistic, degrees of freedom, p-value and 5% decision. Rejection is a diagnostic limitation for Human review and does not trigger automatic retuning. [statsmodels residual whiteness test](https://www.statsmodels.org/stable/generated/statsmodels.tsa.vector_ar.vecm.VECMResults.test_whiteness.html).
- At each of the 5,257 eligible validation origins, use a fixed one-step predictor with observed causal history and frozen parameters. Forecast all four components. For each differenced component, add the forecast difference to its latest revealed scaled level. For VECM use its predicted difference and add the scaled level at `t` exactly once. An undifferenced component is already a scaled level. Inverse-scale the restored load component via the approved `scaler.json` and score against raw MW truth. Read no target-hour weather as forecast input and perform no rolling refit.
- Define C02 `complexity` as the count of free estimated scalar parameters, including intercepts and the unique entries of the symmetric residual covariance. With `K=4`, VAR has `K²p + K + K(K+1)/2 = 16p + 14`. VECM has `K²p + r(2K-r) + K + K(K+1)/2 = 16p + r(8-r) + 14`. The rank term counts the free parameters of the reduced-rank product after identification. Fixed transforms, lag/rank choices and redundant serialized coefficients add zero to the count.
- Serialize the selected form, lag/differencing/rank, coefficients, residual covariance, deterministic terms, feature order and scaler/config references as a versioned, reloadable model artifact. Record relative artifact path and SHA256 of the serialized bytes as the F02 RV2 model hash. Verify reload parity, fixed-state immutability, exact validation keys/truths and independently recomputed metrics. Record fit dates, trials, diagnostics, forecast errors by regime where supported and comparison to both F01 baselines. A model may underperform either baseline while still producing valid evaluation evidence.

## 4. Planned impacted files

The paths below follow the Human's Phase 6 drafting request and the planned file-map entries. The earlier roadmap paths describe the same stage responsibilities.

| Stage | Exact path | Responsibility |
|---|---|---|
| F01 | `src/practice_4/models/baselines.py` | Causal forecasts, F01 run entry point, configuration snapshot and model version hashes. |
| F01 | `tests/test_baselines.py` | Formula, inverse scale, common keys, exclusions and future-perturbation fixtures. |
| F01 | `docs/results/baseline_results.md` | Train/validation counts and MW metrics, config/version hashes and traced evidence. |
| F02 | `src/practice_4/models/var_model.py` | Train-only decision and fit, diagnostics, frozen walk-forward predictor and F02 run entry point. |
| F02 | `tests/test_var.py` | Stationarity/lag/rank decision fixtures, 25-row bound, inverse restoration, leakage and serialized-state checks. |
| F02 | `docs/results/var_results.md` | Train selection and diagnostics, validation evidence, baseline comparison, complexity and artifact hash. |

New per-run artifacts belong under `runs/<run_id>/` per the file map. Record the locked config, environment, input and output checksums, commands and approval references in the run manifest. Store prediction/metric evidence under `artifacts/` and record F02 candidates in `trials.csv`. H01 owns the published test prediction and evaluation artifacts.

## 5. Before-process plan and planned validation

1. After Human approval of this specification and authorization for F01, verify lineage and gates. Implement F01 and run synthetic checks for both lag endpoints, MW restoration, shared scoring and target-hour perturbation. Run F01 on approved train/validation artifacts and present its two model hashes, metrics, prediction keys and report for Human acceptance.
2. After Human accepts F01 and authorizes F02, finalize and hash the Q08 run config before any fit. Verify train-only scope and the frozen dependency versions. Implement and exercise F02 with synthetic fixtures for lag/rank decisions, gap and wrong-lineage rejection, forecast-before-reveal, mixed differencing restoration, VECM integration, 25-row maximum context, stability and serialization. Test that a model or transform mutation fails validation.
3. Run F02 using a fresh ID. Reload the model, check hash and forecast parity, and compare all 5,257 aligned validation predictions with the accepted F01 results. Inspect exclusions, diagnostics and metrics before promotion. Present the results and serialized model hash for Human model-lock and phase review.

Planned commands from the Practice 4 root. The two module entry points are proposed interfaces in the respective model files and require their stage gates. The F02 config is the approved pre-fit snapshot for that run.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
py -3.12 -m pytest tests/test_baselines.py tests/test_metrics.py tests/test_walk_forward.py -q -p no:cacheprovider
py -3.12 -m practice_4.models.baselines --run-id <unique_f01_run_id>
py -3.12 -m pytest tests/test_var.py tests/test_baselines.py tests/test_metrics.py tests/test_walk_forward.py -q -p no:cacheprovider
py -3.12 -m practice_4.models.var_model --run-id <unique_f02_run_id> --config <approved_f02_config> --baseline-run-id <accepted_f01_run_id>
git status --short
git diff --check
```

## 6. Stop conditions

- Stop before execution for missing Human authorization, failed E02/D02 lineage checks, missing F01 acceptance for F02, an unlocked fit config, an environment mismatch or a run-ID collision.
- Stop for any attempt to parse protected test records, use data after an origin, refit on validation, exceed 25 causal rows, rebuild eligibility or change inherited treatment. Any expanded context requires Human review at C02/E02 before dependent work.
- Stop for schema, timestamp, split, eligible-key, count or target mismatch, failed fixtures, nonfinite output, unresolved stationarity or rank, fit failure, instability, state mutation, restoration/reload error or artifact hash mismatch. Report the evidence before changing the protocol or budget.

## 7. Approval record

- E02 run `20261118_system312_e02_01`, Phase 5 RV2 schema v1 and Phase 5 completion were **Human APPROVED / COMPLETED** on 2026-11-18 via Director review.
- Phase 6 specification and before-process plan **Human APPROVED** on 2026-11-18 via Director review. F01 execution authorized.
- F01 run `20261118_system312_f01_01`, baseline report and both RV2 baseline model hashes **Human APPROVED / COMPLETED** on 2026-11-18 via Director review. F02 execution authorized with BIC locked before fitting.
- Q08 conflicting ADF/KPSS results resolved by Human on 2026-11-18 via Director review. The authorized d-map is [0, 0, 0, 0] and F02 resumes under BIC.
- F02 run `20261118_system312_f02_02`, its report, VAR(24) model lock SHA256 `0b3820731f3369f57699adaa64a7b1f4a5cbbf659c48331fc5721335572d3e26` and Phase 6 completion were **Human APPROVED / COMPLETED** on 2026-11-18 via Director review. Human accepted the model artifact as-is. Its feature order and scaler hash are not directly embedded. The F02 run manifest separately records the scaler hash.
- Human authorized preparation of the Phase 7 specification and before-process plan. G01 execution and H01 test opening retain separate gates.
