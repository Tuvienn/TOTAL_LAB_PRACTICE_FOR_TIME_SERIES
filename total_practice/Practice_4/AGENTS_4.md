# Practice 4 Instructions

These instructions apply only to `total_practice/Practice_4/`.

## Scope

- Keep changes scoped to Practice 4 unless the Human explicitly authorizes edits to shared repository instructions or another practice.
- The canonical notebook is `notebooks/practice4.ipynb`.
- Do not add or restore `Practice_4_Manual.ipynb` as a second canonical notebook.

## Reproducibility

- Use the Practice 4 virtual environment and the pinned dependencies in `requirements.txt`.
- Resolve project paths from the project root; do not depend on the notebook's launch directory.
- Keep raw data, processed data, runtime logs, model summaries, and evaluation tables under their existing Practice 4 directories.
- Do not commit `.venv/` or `.ipynb_checkpoints/`.

## Analysis protocol

- Preserve chronological train/validation/test splits and the recursive walk-forward evaluation protocol documented in the notebook.
- Prevent leakage: fit preprocessing objects on training data only and use past-only treatment for missing load targets.
- Treat `practice4.log` and the files under `results/` as outputs of the current notebook run; update them together when the protocol changes.
- Keep conclusions tied to the selected dataset and the recorded metrics; do not claim weekly seasonality or causal weather effects without supporting evidence.

## Documentation

- Keep the notebook, README, phase result notes, current status, and saved artifacts consistent.
- Do not describe unrun experiments or pending human decisions as completed results.
