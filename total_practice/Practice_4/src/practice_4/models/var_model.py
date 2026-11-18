from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels
from statsmodels.tsa.api import VAR

from practice_4.analysis.metrics import calculate_metrics
from practice_4.models.baselines import ROOT, INPUTS, SCALER, align, canonical, sha, verify_lineage

CONFIG_HASH = "2f6bedf20bbc34a5bde0e2ae15eb8fb0b9b5266d91ba22d82e9b19dddea85b60"
F01 = "20261118_system312_f01_01"
DIAGNOSTICS = ROOT / "runs/20261118_system312_f02_01/stationarity.json"


def select_lag(levels):
    if levels.shape != (9271, 4) or not np.isfinite(levels).all():
        raise ValueError("Invalid approved train block")
    trials = []
    for p in range(1, 25):
        fitted = VAR(levels[25 - p:]).fit(p, trend="c")
        bic = float(fitted.bic)
        if fitted.nobs != 9246 or not np.isfinite(bic):
            raise ValueError(f"Invalid candidate p={p}")
        trials.append((p, bic))
    return min(trials, key=lambda entry: (entry[1], entry[0]))[0], trials


def predict_levels(history, coefficients, intercept):
    p = len(coefficients)
    if history.shape != (p, 4) or p < 1 or p > 24:
        raise ValueError("Invalid causal context")
    return intercept + np.einsum("kij,kj->i", coefficients, history[::-1])


def validate_stability(coefficients):
    p = len(coefficients)
    companion = np.zeros((4 * p, 4 * p))
    companion[:4, :] = np.concatenate(coefficients, axis=1)
    if p > 1:
        companion[4:, :-4] = np.eye(4 * (p - 1))
    eigenvalues = np.linalg.eigvals(companion)
    if not np.isfinite(eigenvalues).all() or np.max(np.abs(eigenvalues)) >= 1:
        raise ValueError("VAR companion matrix is unstable")
    return eigenvalues


def run(run_id, config_path, baseline_run_id):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    if platform.python_version_tuple()[:2] != ("3", "12") or statsmodels.__version__ != "0.14.6" or int(pd.__version__.split(".")[0]) >= 3:
        raise ValueError("Environment mismatch")
    config_path = Path(config_path)
    if sha(config_path) != CONFIG_HASH or baseline_run_id != F01:
        raise ValueError("Locked config or baseline mismatch")
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    if config["d_map"] != dict.fromkeys(("load", "temperature", "humidity", "wind_speed"), 0):
        raise ValueError("Unapproved d map")
    upstream = verify_lineage(ROOT)
    f01_path = ROOT / "runs" / F01 / "manifest.json"
    if sha(f01_path) != "dba8592daaa6971357fe40d1426df31382e189882efc48201ad785e2e520eca1":
        raise ValueError("F01 manifest mismatch")
    f01 = json.loads(f01_path.read_text(encoding="utf-8"))
    for item in f01["outputs"]:
        if item["path"] != "docs/results/baseline_results.md" and sha(ROOT / item["path"]) != item["sha256"]:
            raise ValueError("F01 artifact mismatch")
    if sha(DIAGNOSTICS) != "d54b19f6aea2bc842207b7780cb4084a070eff5ba4f799730386b623f46228e7":
        raise ValueError("Stationarity diagnostics mismatch")
    run_dir = ROOT / "runs" / run_id
    report = ROOT / "docs/results/var_results.md"
    log = ROOT / "docs/logs" / f"F02_{run_id}.md"
    if run_dir.exists() or report.exists() or log.exists():
        raise FileExistsError("F02 output collision")
    with np.load(ROOT / INPUTS, allow_pickle=False) as data:
        levels = data["var_train_levels"].copy()
        if not np.array_equal(data["var_row"], np.arange(15273, 24544)):
            raise ValueError("Wrong train domain")
        targets = data["target_row"].copy()
        truths = data["y_true_mw"].copy()
        sequences = data["x_lstm"].copy()
    rows, counts = align(ROOT, targets, truths)
    artifacts = run_dir / "artifacts"
    artifacts.mkdir(parents=True)
    (run_dir / "config.json").write_bytes(config_bytes)
    p, trials = select_lag(levels)
    with (artifacts / "trials.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["p", "bic", "status", "response_start", "response_end"])
        writer.writerows((lag, repr(bic), "completed", 25, 9270) for lag, bic in trials)
    model = VAR(levels).fit(p, trend="c")
    coefficients = model.coefs.copy()
    intercept = model.intercept.copy()
    try:
        eigenvalues = validate_stability(coefficients)
    except ValueError:
        (run_dir / "failure.json").write_text(json.dumps({"status": "blocked", "reason": "unstable VAR", "p": p}) + "\n", encoding="utf-8")
        raise
    whiteness = model.test_whiteness(nlags=48, adjusted=True, signif=0.05)
    artifact = artifacts / "model.npz"
    with artifact.open("xb") as stream:
        np.savez_compressed(stream, coefs=coefficients, intercept=intercept, sigma_u=model.sigma_u, p=np.array(p), config_sha256=np.array(CONFIG_HASH))
    model_hash = sha(artifact)
    with np.load(artifact, allow_pickle=False) as saved:
        loaded_coefs = saved["coefs"].copy()
        loaded_intercept = saved["intercept"].copy()
        if not np.array_equal(saved["sigma_u"], model.sigma_u) or int(saved["p"]) != p:
            raise ValueError("Model reload mismatch")
    if not np.array_equal(coefficients, loaded_coefs) or not np.array_equal(intercept, loaded_intercept):
        raise ValueError("Model reload parity failure")
    scaler = json.loads((ROOT / SCALER).read_text(encoding="utf-8"))
    val_indices = [i for i, row in enumerate(rows) if row["split"] == "validation"]
    if len(val_indices) != 5257:
        raise ValueError("Validation count mismatch")
    predictions = []
    for i in val_indices:
        history = sequences[i, -p:, :]
        vector = predict_levels(history, loaded_coefs, loaded_intercept)
        reference = model.forecast(history, steps=1)[0]
        if not np.allclose(vector, reference, rtol=1e-12, atol=1e-12):
            raise ValueError("Forecast reload parity mismatch")
        predictions.append(float(vector[0] * scaler["scale"][0] + scaler["mean"][0]))
    if sha(artifact) != model_hash or not np.array_equal(coefficients, loaded_coefs) or not np.array_equal(intercept, loaded_intercept):
        raise ValueError("Fixed state changed")
    actual = truths[val_indices]
    metrics = calculate_metrics(actual, predictions, 2, 0)
    if len(predictions) != 5257:
        raise ValueError("Validation count mismatch")
    with (artifacts / "validation_predictions.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["model", "origin", "target_timestamp", "target_row", "y_true_mw", "y_pred_mw", "split", "run_id"])
        for i, prediction in zip(val_indices, predictions):
            row = rows[i]
            writer.writerow(["VAR", row["origin_timestamp_utc"], row["target_timestamp_utc"], row["target_row"], repr(float(truths[i])), repr(prediction), "validation", run_id])
    (artifacts / "metrics.json").write_bytes(canonical(metrics) + b"\n")
    baseline_metrics = json.loads((ROOT / "runs" / F01 / "artifacts/metrics.json").read_text())
    stationarity = json.loads(DIAGNOSTICS.read_text())
    text = [f"# F02 VAR Results\n\nRun `{run_id}` - **PENDING HUMAN REVIEW**.\n", "## Stationarity\n", "| Variable | ADF statistic | ADF p | KPSS statistic | KPSS p | d |", "|---|---:|---:|---:|---:|---:|"]
    for name, result in stationarity.items():
        text.append(f"| {name} | {result['adf_stat']:.6g} | {result['adf_p']:.6g} | {result['kpss_stat']:.6g} | {result['kpss_p']:.6g} | 0 |")
    text += ["\nKPSS p-values at 0.01 or 0.1 are table bounds. Human selected d=0 using ADF and identified annual weather seasonal drift as a possible explanation of KPSS rejection. These diagnostics alone do not establish the cause. The 9,271-hour block excludes 15,241 earlier observed hours and may not represent earlier regimes.\n", "## Lag selection\n", "| p | BIC |", "|---:|---:|"]
    text += [f"| {lag} | {bic:.8f} |" for lag, bic in trials]
    text += [f"\nSelected VAR({p}), complexity {16*p+14}, model SHA256 `{model_hash}`. Maximum companion eigenvalue modulus {max(abs(eigenvalues)):.10f}.", f"Adjusted Portmanteau lag 48 statistic {whiteness.test_statistic:.6g}, df {whiteness.df}, p-value {whiteness.pvalue:.6g}, reject at 5% {whiteness.pvalue < 0.05}.", "\n## Validation metrics\n", "| Model | MAE MW | RMSE MW | MAPE % |", "|---|---:|---:|---:|"]
    for name, m in [("persistence", baseline_metrics["persistence"]["validation"]), ("seasonal24", baseline_metrics["seasonal24"]["validation"]), ("VAR", metrics)]:
        text.append(f"| {name} | {m['mae_mw']:.6f} | {m['rmse_mw']:.6f} | {m['mape_percent']:.6f} |")
    text.append("\nAll models use 5,257 eligible validation targets. Two missing truths and zero invalid contexts are excluded. Fixed train scaler and coefficients are used throughout.\n")
    if upstream != verify_lineage(ROOT) or config_path.read_bytes() != config_bytes:
        raise ValueError("Upstream drift")
    report.write_text("\n".join(text), encoding="utf-8")
    log.write_text(f"# F02 {run_id}\n\nStatus **PENDING HUMAN REVIEW**. Locked config SHA256 `{CONFIG_HASH}`. Model artifact SHA256 `{model_hash}`. Upstream hashes matched before and after fitting and validation. Forecast reload parity and fixed-state checks passed.\n", encoding="utf-8")
    output = [artifact, artifacts / "trials.csv", artifacts / "validation_predictions.csv", artifacts / "metrics.json", run_dir / "config.json", report, log]
    manifest = {"schema_version":"1","run_id":run_id,"stage_id":"F02","status":"completed","config_sha256":CONFIG_HASH,"model_sha256":model_hash,"p":p,"complexity":16*p+14,"upstream_sha256":upstream,"f01_manifest_sha256":sha(f01_path),"stationarity_sha256":sha(DIAGNOSTICS),"environment":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,"statsmodels":statsmodels.__version__},"outputs":[{"path":str(path.relative_to(ROOT)).replace("\\","/"),"sha256":sha(path)} for path in output],"limitations":["Human-resolved conflicting ADF/KPSS diagnostics","Fixed 9271-hour train block excludes earlier observations","F02 gate and model lock pending Human review"]}
    (run_dir / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    print(json.dumps({"p":p,"model_sha256":model_hash,"metrics":metrics,"max_eigenvalue_modulus":float(max(abs(eigenvalues))),"whiteness_p":float(whiteness.pvalue)}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--baseline-run-id", required=True)
    args = parser.parse_args()
    run(args.run_id, args.config, args.baseline_run_id)


if __name__ == "__main__":
    main()
