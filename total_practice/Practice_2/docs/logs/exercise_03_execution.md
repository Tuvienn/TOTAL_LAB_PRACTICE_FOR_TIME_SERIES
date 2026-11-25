# Exercise 03 — Execution Evidence

## Run context

- Source: `notebooks/Practice_2_Exercise.ipynb`
- Input: original training series only (`n=163`)
- Test values used: false
- Status: validated with approved log transformation

## Transformation and ADF result

| Item | Value |
|---|---|
| Transformation | Natural logarithm |
| Regular differencing | First difference |
| Selected `d` | `1` |
| Transformed observations | `162` |
| ADF statistic | `-3.659486` |
| p-value | `0.004720` |
| Used lag | `13` |
| ADF observations | `148` |
| Decision | Reject H0 |

The official E03 conclusion is `natural log + first difference`, with `d=1`.
The second-difference cell is retained only as a historical comparison and is
not used for the official handoff.
