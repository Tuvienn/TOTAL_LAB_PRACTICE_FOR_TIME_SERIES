# Phase 10 — Offline reproduction and handoff

The project analysis/model versions are pinned in `requirements.lock.txt`. The notebook kernel add-on is separately pinned in `requirements-notebook.lock.txt`; it does not alter model dependencies. In this workspace the dedicated Python 3.12.10 environment passed `pip check`, and the notebook ran all 30 cells (7 code cells) without errors.

From the `total_practice/Practice_4` directory, install the kernel add-on into the locked environment and register it:

```powershell
$py = 'C:\Users\Daijin_B\anaconda3\envs\practice4-system31210\python.exe'
& $py -m pip install -r requirements-notebook.lock.txt
& $py -m ipykernel install --user --name practice4-system31210 --display-name 'Python 3.12 (Practice 4)'
& $py -m pip check
```

Open `notebooks/practice_4_end_to_end.ipynb`, select kernel **Python 3.12 (Practice 4)** and Run All. Or run from the Practice 4 directory with Anaconda's Jupyter command:

```powershell
jupyter nbconvert --to notebook --execute --ExecutePreprocessor.kernel_name=practice4-system31210 --output practice_4_end_to_end.executed.ipynb --output-dir runs/20261120_system312_i01_01/artifacts notebooks/practice_4_end_to_end.ipynb
```

The notebook reads official H01 predictions and metrics, H02 grouped errors and figures, and accepted phase findings. It does not load raw/canonical data, train/tune a model, or regenerate predictions. Execution produced no cell errors; a Windows ZeroMQ Proactor warning from the base Jupyter launcher did not affect results. H01/H02/I01 manifests and logs preserve provenance.
