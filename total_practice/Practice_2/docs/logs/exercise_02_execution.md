# Exercise 02 — Execution Evidence

## Run context

- Source: `notebooks/Practice_2_Exercise.ipynb`
- Input: original training series only (`n=163`)
- Alpha: `0.05`
- Test values used: false
- Status: validated

## ADF result

| Metric | Value |
|---|---:|
| ADF statistic | `2.230893` |
| p-value | `0.998907` |
| Used lag | `14` |
| ADF observations | `148` |
| Decision | Fail to reject H0 |

The original training series is not supported as stationary at the 5% level.
