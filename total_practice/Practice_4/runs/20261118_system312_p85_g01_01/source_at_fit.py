from __future__ import annotations

import argparse
import csv
import json
import platform
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

from practice_4.analysis.metrics import calculate_metrics, select_validation
from practice_4.data.features import XGB_FEATURE_NAMES
from practice_4.models.baselines import ROOT, INPUTS, SCALER, align, canonical, sha, verify_lineage

CONFIG_HASH = "16d91759d81efb3af5394b7dace9cecafd915badee0e489b27043b9aaa9ee6fd"
RUN_ID = "20261118_system312_g01_01"


def feature_indices(names, selected):
    if len(names) != len(set(names)) or len(selected) != len(set(selected)):
        raise ValueError("Duplicate feature names")
    return [names.index(name) for name in selected]


def prediction(model, features, best_iteration):
    if best_iteration < 0:
        raise ValueError("Invalid best iteration")
    return model.predict(features, iteration_range=(0, best_iteration + 1))


def metadata(subset, names, scaler_hash, booster_hash, config_hash, best_iteration, versions, lineage):
    return {"model": subset, "feature_order": names, "scaler_sha256": scaler_hash,
            "booster_sha256": booster_hash, "config_sha256": config_hash,
            "best_iteration": best_iteration, "tree_count": best_iteration + 1,
            "library_versions": versions, "input_lineage": lineage, "model_version": "1"}


def verify(config):
    for name, expected in config["upstream_sha256"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"Upstream hash mismatch: {name}")
    verify_lineage(ROOT)
    if (xgb.__version__, np.__version__, pd.__version__) != ("3.4.1", "2.5.5", "2.3.3"):
        raise ValueError("Version mismatch")


def run(run_id, config_path, replay=False):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    if replay and (ROOT / "runs" / run_id).exists():
        raise FileExistsError("Replay output collision")
    config_path = Path(config_path).resolve()
    if (not replay and run_id != RUN_ID) or sha(config_path) != CONFIG_HASH:
        raise ValueError("Run ID or config mismatch")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    verify(config)
    names = list(XGB_FEATURE_NAMES)
    if config["feature_order"]["XGB_full"] != names:
        raise ValueError("Feature order mismatch")
    for subset, features in config["feature_order"].items():
        if feature_indices(names, features) != config["feature_indices"][subset]:
            raise ValueError("Feature indices mismatch")
    with np.load(ROOT / INPUTS, allow_pickle=False) as data:
        targets = data["target_row"]
        truth = data["y_true_mw"]
        features = data["x_xgb"]
    if len(targets) != 29692 or features.shape != (29692, 99) or np.any(targets >= 29803):
        raise ValueError("Invalid feature domain")
    rows, counts = align(ROOT, targets, truth)
    if not np.isfinite(features).all() or not np.isfinite(truth).all():
        raise ValueError("Nonfinite input")
    train = np.array([row["split"] == "train" for row in rows])
    valid = ~train
    if (int(train.sum()), int(valid.sum())) != (24435, 5257):
        raise ValueError("Eligibility mismatch")
    run_dir = ROOT / "runs" / run_id
    if replay:
        run_dir.mkdir(exist_ok=False)
        (run_dir / "config.json").write_bytes(config_path.read_bytes())
    artifacts = run_dir / "artifacts"
    artifacts.mkdir(exist_ok=False)
    trials = []
    models = {}
    for subset in ("XGB_full", "XGB_load_only"):
        selected = features[:, config["feature_indices"][subset]]
        for depth in config["grid"]["max_depth"]:
            for estimators in config["grid"]["n_estimators"]:
                trial_id = f"{subset}_d{depth}_n{estimators:04d}"
                model = xgb.XGBRegressor(max_depth=depth, n_estimators=estimators, **config["parameters"])
                started = time.monotonic()
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    evaluations = [(selected[train], truth[train]), (selected[valid], truth[valid])] if replay else [(selected[valid], truth[valid])]
                    model.fit(selected[train], truth[train], eval_set=evaluations, verbose=False)
                if replay:
                    history = model.evals_result()
                    with (artifacts / f"{trial_id}_rounds.csv").open("x", encoding="utf-8", newline="") as stream:
                        writer = csv.writer(stream, lineterminator="\n")
                        writer.writerow(["round", "train_rmse", "validation_rmse"])
                        writer.writerows((i + 1, a, b) for i, (a, b) in enumerate(zip(history["validation_0"]["rmse"], history["validation_1"]["rmse"], strict=True)))
                best = int(model.best_iteration)
                if best < 0 or best >= estimators:
                    raise ValueError("Invalid early stopping state")
                values = prediction(model, selected[valid], best)
                scores = calculate_metrics(truth[valid], values, 2, 0)
                record = {"model": "XGB", "subset": subset, "trial_id": trial_id, "max_depth": depth,
                          "n_estimators": estimators, "status": "completed", "elapsed_seconds": time.monotonic()-started,
                          "best_iteration": best, "complexity": best+1, "warnings": " | ".join(str(w.message) for w in caught), **scores}
                trials.append(record)
                models[trial_id] = model
                print(trial_id, scores["rmse_mw"], flush=True)
    with (artifacts / "trials.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(trials[0]))
        writer.writeheader()
        writer.writerows(trials)
    selected_records = {}
    predictions = {}
    model_hashes = {}
    for subset in ("XGB_full", "XGB_load_only"):
        chosen = select_validation([trial for trial in trials if trial["subset"] == subset])
        selected_records[subset] = chosen
        model = models[chosen["trial_id"]]
        selected = features[valid][:, config["feature_indices"][subset]]
        reference = prediction(model, selected, chosen["best_iteration"])
        booster = model.get_booster()[:chosen["complexity"]]
        booster.feature_names = config["feature_order"][subset]
        model_path = artifacts / f"{subset}.json"
        booster.save_model(model_path)
        model_hashes[subset] = sha(model_path)
        loaded = xgb.Booster()
        loaded.load_model(model_path)
        actual = loaded.predict(xgb.DMatrix(selected, feature_names=config["feature_order"][subset]), iteration_range=(0, chosen["complexity"]))
        if np.max(np.abs(reference.astype(float) - actual.astype(float))) > 1e-9:
            raise ValueError("Reload parity failure")
        predictions[subset] = actual
        meta = metadata(subset, config["feature_order"][subset], config["scaler_sha256"], model_hashes[subset], CONFIG_HASH, chosen["best_iteration"], config["versions"], config["upstream_sha256"])
        (artifacts / f"{subset}_metadata.json").write_bytes(canonical(meta) + b"\n")
        if subset == "XGB_full":
            gains = loaded.get_score(importance_type="gain")
    with (artifacts / "validation_predictions.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["target_row", "origin", "target_timestamp", "y_true_mw", "XGB_full", "XGB_load_only"])
        for i, row in enumerate([r for r in rows if r["split"] == "validation"]):
            writer.writerow([row["target_row"], row["origin_timestamp_utc"], row["target_timestamp_utc"], row["y_true_mw"], predictions["XGB_full"][i], predictions["XGB_load_only"][i]])
    group = lambda name: "derived_load" if name in ("mean6h", "std24h", "trend24h") else name.split("_", 1)[1]
    with (artifacts / "gain.csv").open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["feature", "group", "mean_split_gain"])
        writer.writerows((name, group(name), gains.get(name, 0.0)) for name in names)
    aggregates = {g: sum(gains.get(n, 0.0) for n in names if group(n) == g) for g in ("load", "temperature", "humidity", "wind_speed", "derived_load")}
    baseline = json.loads((ROOT / "runs/20261118_system312_f01_01/artifacts/metrics.json").read_text())
    var = json.loads((ROOT / "runs/20261118_system312_f02_02/artifacts/metrics.json").read_text())
    results = {"selected": selected_records, "gain_group_sums": aggregates, "baseline": baseline, "VAR": var, "counts": counts, "hashes": model_hashes}
    (artifacts / "metrics.json").write_bytes(canonical(results) + b"\n")
    verify(config)
    if sha(config_path) != CONFIG_HASH:
        raise ValueError("Config changed")
    report = artifacts / "xgboost_findings.md" if replay else ROOT / "docs/results/xgboost_findings.md"
    log = artifacts / "execution.md" if replay else ROOT / "docs/logs" / f"G01_{run_id}.md"
    if report.exists() or log.exists():
        raise FileExistsError("Report collision")
    lines = [f"# G01 XGBoost findings\n\nRun `{run_id}`. **PENDING HUMAN REVIEW**.\n", "## Trials\n", "| Subset | Trial | Trees | MAE MW | RMSE MW | MAPE % |", "|---|---|---:|---:|---:|---:|"]
    for t in trials:
        lines.append(f"| {t['subset']} | {t['trial_id']} | {t['complexity']} | {t['mae_mw']:.6f} | {t['rmse_mw']:.6f} | {t['mape_percent']:.6f} |")
    lines += ["\n## Validation comparison\n", "| Model | MAE MW | RMSE MW | MAPE % |", "|---|---:|---:|---:|"]
    for name, m in [("persistence", baseline["persistence"]["validation"]), ("seasonal24", baseline["seasonal24"]["validation"]), ("VAR(24)", var), *selected_records.items()]:
        lines.append(f"| {name} | {m['mae_mw']:.6f} | {m['rmse_mw']:.6f} | {m['mape_percent']:.6f} |")
    full, load = selected_records["XGB_full"], selected_records["XGB_load_only"]
    lines.append(f"\nFull minus load-only: MAE {full['mae_mw']-load['mae_mw']:.6f} MW, RMSE {full['rmse_mw']-load['rmse_mw']:.6f} MW, MAPE {full['mape_percent']-load['mape_percent']:.6f} percentage points.")
    lines += ["\nValidation has 5259 candidates, 2 missing truths, 0 invalid contexts, and 5257 scored. Train has 24519 candidates, 32 missing truths, 52 invalid contexts, and 24435 scored. Initial warm-up contains 25 target rows. MAPE excludes zero truths.", "\n## Gain importance\n", "Group totals sum each feature's mean split gain. These values describe predictive association and are affected by correlated inputs and weather proxies. The validation set supports early stopping and selection, introducing optimism. Neither gain nor ablation establishes causality."]
    lines += [f"- {name}: {value:.6f}" for name, value in aggregates.items()]
    lines += [f"\n- {name}: `{value}`" for name, value in model_hashes.items()]
    report.write_text("\n".join(lines)+"\n", encoding="utf-8")
    log.write_text(f"# G01 {run_id}\n\nStatus **PENDING HUMAN REVIEW**. Config SHA256 `{CONFIG_HASH}`. Upstream hashes checked before and after fitting. Both selected boosters reloaded with prediction parity <= 1e-9 MW.\n", encoding="utf-8")
    paths = list(artifacts.iterdir()) + [config_path, report, log]
    manifest = {"stage_id":"G01", "run_id":run_id, "status":"pending_human_review", "config_sha256":CONFIG_HASH, "upstream_sha256":config["upstream_sha256"], "model_hashes":model_hashes, "environment":{"python":platform.python_version(), **config["versions"]}, "outputs":[{"path":p.relative_to(ROOT).as_posix(), "sha256":sha(p)} for p in paths]}
    (ROOT / "runs" / run_id / "manifest.json").write_bytes(canonical(manifest)+b"\n")
    print(json.dumps(results, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    run(args.run_id, args.config, args.replay)


if __name__ == "__main__":
    main()
