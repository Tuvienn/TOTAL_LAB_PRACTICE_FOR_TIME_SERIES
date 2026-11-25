# Exercise 01 — Execution Evidence

## Run context

- Source: `notebooks/Practice_2_Exercise.ipynb`
- Run type: clean-kernel reconciliation run
- Dataset: `datasets/raw/a10.csv`
- Status: validated

## Data contract

| Check | Result |
|---|---:|
| Observations | 204 |
| Train observations | 163 |
| Test observations | 41 |
| Frequency | Monthly start (`MS`) |
| Missing values | 0 |
| Duplicate timestamps | 0 |
| Missing intervals | 0 |
| Shuffle | false |

Train ends at `2005-01`; test starts at `2005-02`. The test partition is sealed
until E05.

## Output

The validated series and chronological boundary are used by E02–E05. Raw data
is not modified.
