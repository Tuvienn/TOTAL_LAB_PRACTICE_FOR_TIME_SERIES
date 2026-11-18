from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from practice_4.analysis.metrics import calculate_metrics, select_validation
from practice_4.models.baselines import INPUTS, ROOT, SCALER, align, canonical, sha, verify_lineage

RUN_ID = "20261118_system312_g02_01"
CONFIG_HASH = "866aa8fb59048789010f09c4355ea7a484c7a5e51d06c655e156575a3d0a87fc"
FEATURE_ORDER = ["load_input_scaled", "temp_scaled", "humidity_scaled", "wind_speed_scaled"]
COMPLEXITY = 30113
KEYS = ["target_row", "origin", "target_timestamp", "y_true_mw"]
PREDECESSORS = {
    "persistence": ("f01_01", "predictions.csv", "y_pred_mw"),
    "seasonal24": ("f01_01", "predictions.csv", "y_pred_mw"),
    "VAR(24)": ("f02_02", "validation_predictions.csv", "y_pred_mw"),
    "XGB_full": ("g01_01", "validation_predictions.csv", "XGB_full"),
}


def verify(config, config_path):
    if sha(config_path) != CONFIG_HASH:
        raise ValueError("Locked config SHA256 mismatch")
    upstream = verify_lineage(ROOT)
    if any(config["upstream_sha256"][key] != value for key, value in upstream.items()):
        raise ValueError("E02 lineage mismatch")
    for name, expected in config["upstream_sha256"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"Upstream SHA256 mismatch: {name}")


def runtime(config):
    os.environ.update(config["environment"])
    import tensorflow as tf
    import keras

    for name, expected in config["versions"].items():
        actual = platform.python_version() if name == "python" else importlib.metadata.version(name)
        if actual != expected:
            raise ValueError(f"Unexpected version for {name}: {actual}")
    if keras.backend.backend() != "tensorflow" or tf.config.list_physical_devices("GPU"):
        raise ValueError("CPU TensorFlow backend required")
    if not tf.config.list_physical_devices("CPU"):
        raise ValueError("No CPU device")
    tf.config.threading.set_inter_op_parallelism_threads(config["threads"]["inter"])
    tf.config.threading.set_intra_op_parallelism_threads(config["threads"]["intra"])
    tf.config.experimental.enable_op_determinism()
    keras.mixed_precision.set_global_policy(config["dtype"])
    return tf, keras


def align_sequences(x, targets, truth):
    if np.any(targets >= 29803):
        raise ValueError("Forbidden target row")
    if x.shape != (len(targets), 24, 4) or truth.shape != targets.shape:
        raise ValueError("Unexpected sequence or target shape")
    if not np.isfinite(x).all() or not np.isfinite(truth).all():
        raise ValueError("Nonfinite sequence or truth")
    return align(ROOT, targets, truth)


def scale_truth(truth, mean, scale):
    if not np.isfinite([mean, scale]).all() or scale <= 0:
        raise ValueError("Invalid D02 load scaler")
    result = ((truth.astype(np.float64) - mean) / scale).astype(np.float32)
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite scaled target")
    return result


def to_mw(values, mean, scale):
    return np.asarray(values, dtype=np.float64) * scale + mean


def build_model(keras, config, lr):
    model = keras.Sequential([
        keras.Input(shape=(24, 4), dtype="float32"),
        keras.layers.LSTM(64, return_sequences=True),
        keras.layers.LSTM(32),
        keras.layers.Dense(1),
    ], name="lstm_r07")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=lr, **config["optimizer"]),
        loss=config["loss"], jit_compile=config["jit_compile"],
    )
    if sum(np.prod(v.shape) for v in model.trainable_weights) != COMPLEXITY:
        raise ValueError("R07 complexity mismatch")
    return model


def fit(model, callback, config, train_x, train_y, valid_x, valid_y):
    kwargs = dict(validation_data=(valid_x, valid_y), epochs=config["epochs"],
                  batch_size=config["batch_size"], shuffle=config["shuffle"],
                  callbacks=[callback], verbose=2)
    return model.fit(train_x, train_y, **kwargs).history


def restored_epoch(model, callback, history):
    validation = np.asarray(history["val_loss"])
    if not np.isfinite([validation, history["loss"]]).all():
        raise ValueError("Nonfinite learning curve")
    first = int(np.argmin(validation))
    if callback.best_epoch != first or callback.best_weights is None:
        raise ValueError("EarlyStopping did not select the earliest minimum")
    for restored, saved in zip(model.get_weights(), callback.best_weights, strict=True):
        np.testing.assert_array_equal(restored, saved)
    return first + 1


def predict(tf, model, x, batch_size):
    before = [v.numpy() for v in model.variables]

    @tf.function(input_signature=[tf.TensorSpec((None, 24, 4), tf.float32)], jit_compile=False)
    def infer(inputs):
        return model(inputs, training=False)

    values = np.concatenate([
        infer(x[start:start + batch_size]).numpy().reshape(-1)
        for start in range(0, len(x), batch_size)
    ])
    for variable, old in zip(model.variables, before, strict=True):
        np.testing.assert_array_equal(variable.numpy(), old)
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite model output")
    return values


def save_json(path, value):
    with path.open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def write_checkpoint(keras, model, artifacts, config, chosen):
    weights = artifacts / "lstm.weights.h5"
    architecture = artifacts / "lstm_architecture.json"
    metadata_path = artifacts / "lstm_metadata.json"
    with architecture.open("x", encoding="utf-8") as stream:
        stream.write(model.to_json())
    model.save_weights(weights)
    metadata = {
        "model": "LSTM", "model_version": "1", "config_sha256": CONFIG_HASH,
        "checkpoint_sha256": sha(weights), "architecture_sha256": sha(architecture),
        "best_epoch": chosen["best_epoch"], "trial_id": chosen["trial_id"],
        "library_versions": config["versions"], "input_lineage": config["upstream_sha256"],
        **{name: config[name] for name in ("feature_order", "scaler_sha256", "architecture",
           "input_shape", "seed", "complexity", "device", "dtype", "batch_size", "checkpoint_format")},
    }
    save_json(metadata_path, metadata)
    saved = json.loads(metadata_path.read_bytes())
    if saved != metadata or sha(weights) != saved["checkpoint_sha256"] or sha(architecture) != saved["architecture_sha256"]:
        raise ValueError("Checkpoint and metadata hash mismatch")
    loaded = keras.models.model_from_json(architecture.read_text(encoding="utf-8"))
    loaded.optimizer.build(loaded.trainable_variables)
    loaded.load_weights(weights)
    return loaded, metadata


def scores(truth, values, missing=0, invalid=0):
    result = calculate_metrics(truth, values, missing, invalid)
    absolute = np.abs(truth - values)
    nonzero = truth != 0
    independent = [absolute.mean(), np.sqrt(np.mean(absolute ** 2))]
    expected = [result["mae_mw"], result["rmse_mw"]]
    if np.any(nonzero):
        independent.append(100 * np.mean(absolute[nonzero] / np.abs(truth[nonzero])))
        expected.append(result["mape_percent"])
    np.testing.assert_allclose(expected, independent, rtol=1e-12, atol=0)
    return result


def predecessor_predictions(expected):
    result = {}
    for name, (run, filename, column) in PREDECESSORS.items():
        path = ROOT / f"runs/20261118_system312_{run}/artifacts/{filename}"
        table = pd.read_csv(path, float_precision="round_trip")
        if (table.target_row >= 29803).any():
            raise ValueError(f"Forbidden predecessor row for {name}")
        if run == "f01_01":
            table = table.loc[(table.model == name) & (table.split == "validation")]
        pd.testing.assert_frame_equal(table[KEYS].reset_index(drop=True), expected[KEYS])
        result[name] = table[column].to_numpy(dtype=np.float64)
    return result


def run(run_id, config_path, replay=False):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    if replay and (ROOT / "runs" / run_id).exists():
        raise FileExistsError("Replay output collision")
    config_path = Path(config_path).resolve()
    if not replay and (run_id != RUN_ID or config_path != ROOT / "runs" / run_id / "config.json"):
        raise ValueError("Unexpected G02 run or config path")
    config = json.loads(config_path.read_bytes())
    verify(config, config_path)
    if config["feature_order"] != FEATURE_ORDER or config["shuffle"] is not False:
        raise ValueError("Feature order or shuffle mismatch")
    run_dir = ROOT / "runs" / run_id
    if replay:
        run_dir.mkdir(exist_ok=False)
        (run_dir / "config.json").write_bytes(config_path.read_bytes())
    tf, keras = runtime(config)
    scaler = json.loads((ROOT / SCALER).read_bytes())
    if [f"{name}_scaled" for name in scaler["feature_order"]] != FEATURE_ORDER:
        raise ValueError("D02 scaler feature order mismatch")
    if sha(ROOT / SCALER) != config["scaler_sha256"]:
        raise ValueError("D02 scaler hash mismatch")
    mean, scale = scaler["mean"][0], scaler["scale"][0]
    with np.load(ROOT / INPUTS, allow_pickle=False) as arrays:
        if int(arrays["schema_version"]) != 1:
            raise ValueError("E02 schema mismatch")
        targets, truth, x = arrays["target_row"], arrays["y_true_mw"], arrays["x_lstm"]
    rows, counts = align_sequences(x, targets, truth)
    if counts != config["eligibility"]:
        raise ValueError("Eligibility gate mismatch")
    train = targets < 24544
    train_x, valid_x = x[train].astype(np.float32), x[~train].astype(np.float32)
    train_y, valid_y = [scale_truth(y, mean, scale) for y in (truth[train], truth[~train])]
    expected = pd.DataFrame([
        (int(row["target_row"]), row["origin_timestamp_utc"], row["target_timestamp_utc"], float(row["y_true_mw"]))
        for row in rows if row["split"] == "validation"
    ], columns=KEYS)
    comparisons = predecessor_predictions(expected)
    artifacts = run_dir / "artifacts"
    report = artifacts / "lstm_findings.md" if replay else ROOT / "docs/results/lstm_findings.md"
    log = artifacts / "execution.md" if replay else ROOT / "docs/logs" / f"G02_{run_id}.md"
    if report.exists() or log.exists():
        raise FileExistsError("G02 report/log collision")
    artifacts.mkdir()
    trials, curves, models, predictions = [], [], {}, {}
    for trial in config["trial_budget"]:
        trial_id = trial["trial_id"]
        print(f"Starting {trial_id}", flush=True)
        keras.utils.set_random_seed(config["seed"])
        model = build_model(keras, config, trial["learning_rate"])
        callback = keras.callbacks.EarlyStopping(**config["early_stopping"])
        started = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            history = fit(model, callback, config, train_x, train_y, valid_x, valid_y)
        elapsed = time.perf_counter() - started
        best, stop = restored_epoch(model, callback, history), len(history["loss"])
        train_scaled = predict(tf, model, train_x, config["batch_size"])
        val_scaled = predict(tf, model, valid_x, config["batch_size"])
        values = to_mw(val_scaled, mean, scale)
        train_mse = float(np.mean((train_scaled.astype(np.float64) - train_y) ** 2))
        val_mse = float(np.mean((val_scaled.astype(np.float64) - valid_y) ** 2))
        trials.append({
            **trial, "model": "LSTM", "complexity": COMPLEXITY, "status": "completed",
            "best_epoch": best, "stopping_epoch": stop, "epochs_after_best": stop - best,
            "elapsed_seconds": elapsed, "restored_train_mse": train_mse, "restored_val_mse": val_mse,
            "warnings": " | ".join(str(w.message) for w in caught),
            **scores(truth[~train], values, 2),
        })
        models[trial_id], predictions[trial_id] = model, values
        table = pd.DataFrame({"trial_id": trial_id, "epoch": range(1, stop + 1),
                              "train_loss": history["loss"], "val_loss": history["val_loss"]})
        table["validation_minus_train"] = table.val_loss - table.train_loss
        curves.append(table)
        pd.DataFrame(trials).to_csv(artifacts / "trials.csv", index=False)
        pd.concat(curves, ignore_index=True).to_csv(artifacts / "training_history.csv", index=False)
    chosen = select_validation(trials)
    trial_id = chosen["trial_id"]
    loaded, metadata = write_checkpoint(keras, models[trial_id], artifacts, config, chosen)
    values = to_mw(predict(tf, loaded, valid_x, config["batch_size"]), mean, scale)
    np.testing.assert_allclose(values, predictions[trial_id], rtol=0, atol=1e-6)
    parity = float(np.max(np.abs(values - predictions[trial_id])))
    comparisons["LSTM"] = values
    results = finish_diagnostics(expected, comparisons, curves, artifacts, trials, chosen, metadata, parity)
    verify(config, config_path)
    write_report(report, results, trials, metadata, run_id)
    with log.open("x", encoding="utf-8") as stream:
        stream.write(
            f"# G02 {run_id}\n\n**PENDING HUMAN REVIEW**\n\n"
            f"Config SHA256 `{CONFIG_HASH}`. Verified all upstream hashes before and after fitting. "
            f"Reloaded architecture and weights across 5,257 validation samples, max difference {parity:.9g} MW. "
            "Trial times and Python warnings are in trials.csv.\n"
        )
    paths = sorted(artifacts.iterdir()) + [config_path, report, log, Path(__file__).resolve()]
    manifest = {
        "stage_id": "G02", "run_id": run_id, "status": "pending_human_review",
        "config_sha256": CONFIG_HASH, "checkpoint_sha256": metadata["checkpoint_sha256"],
        "architecture_sha256": metadata["architecture_sha256"], "upstream_sha256": config["upstream_sha256"],
        "counts": counts, "versions": config["versions"], "reload_max_abs_mw": parity,
        "outputs": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in paths],
    }
    save_json(run_dir / "manifest.json", manifest)
    print(json.dumps({"selected": trial_id, "checkpoint_sha256": metadata["checkpoint_sha256"],
                      "reload_max_abs_mw": parity}, indent=2), flush=True)


def finish_diagnostics(expected, comparisons, curves, artifacts, trials, chosen, metadata, parity):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    times = pd.DatetimeIndex(pd.to_datetime(expected.target_timestamp, utc=True))
    if times.has_duplicates or not times.is_monotonic_increasing:
        raise ValueError("Validation UTC keys are not unique and increasing")
    local = times.tz_convert("Europe/Madrid")
    truth = expected.y_true_mw.to_numpy()
    d01 = json.loads((ROOT / "runs/20261118_system312_d01_01/summary.json").read_bytes())
    profiles = {axis: {row["group"]: row for row in d01["profiles"][axis]} for axis in ("hour", "weekday")}
    temporal, acf, metrics = [], [], {}
    output = expected.copy()
    output["target_local"] = [stamp.isoformat() for stamp in local]
    for name, estimates in comparisons.items():
        residual = truth - estimates
        output[name] = estimates
        metrics[name] = scores(truth, estimates, 2)
        for lag in (24, 168):
            earlier = times.get_indexer(times - pd.Timedelta(hours=lag))
            exists = earlier >= 0
            corr = float(np.corrcoef(residual[exists], residual[earlier[exists]])[0, 1])
            acf.append({"model": name, "lag_hours_utc": lag, "pairs": int(exists.sum()), "correlation": corr})
        for axis, groups in (("hour", local.hour), ("weekday", local.dayofweek)):
            for label in sorted(set(groups)):
                ix = groups == label
                group_score = scores(truth[ix], estimates[ix])
                train_profile = profiles[axis][label]
                temporal.append({
                    "model": name, "grouping": axis, "group": int(label), "n": int(ix.sum()),
                    "mae_mw": group_score["mae_mw"], "rmse_mw": group_score["rmse_mw"],
                    "mean_residual_mw": float(residual[ix].mean()), "validation_mean_load_mw": float(truth[ix].mean()),
                    "d01_train_mean_load_mw": train_profile["mean"], "d01_train_count": train_profile["count"],
                })
    for key in ("mae_mw", "rmse_mw", "mape_percent"):
        np.testing.assert_allclose(metrics["LSTM"][key], chosen[key], rtol=1e-12, atol=1e-6)
    output["residual_mw"] = truth - comparisons["LSTM"]
    output.to_csv(artifacts / "validation_predictions.csv", index=False)
    pd.DataFrame(temporal).to_csv(artifacts / "temporal_errors.csv", index=False)
    pd.DataFrame(acf).to_csv(artifacts / "residual_autocorrelation.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for ax, curve, trial in zip(axes, curves, trials, strict=True):
        ax.plot(curve.epoch, curve.train_loss, label="Train")
        ax.plot(curve.epoch, curve.val_loss, label="Validation")
        ax.axvline(trial["best_epoch"], color="gray", ls="--", label="Best epoch")
        ax.set(title=trial["trial_id"], xlabel="Epoch", ylabel="Scaled MSE", yscale="log")
        ax.legend()
    fig.savefig(artifacts / "learning_curves.png", dpi=130)
    plt.close(fig)
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), layout="constrained")
    axes[0].plot(times, truth, label="Observed", lw=0.6)
    axes[0].plot(times, comparisons["LSTM"], label="LSTM", lw=0.6, alpha=0.8)
    axes[0].legend()
    axes[0].set(ylabel="Load (MW)")
    axes[1].plot(times, output.residual_mw, lw=0.6, color="tab:orange")
    axes[1].set(xlabel="Target hour (UTC)", ylabel="Observed - forecast (MW)")
    fig.savefig(artifacts / "validation_trace.png", dpi=130)
    plt.close(fig)
    temporal_frame = pd.DataFrame(temporal)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for ax, axis in zip(axes, ("hour", "weekday"), strict=True):
        for name in metrics:
            group = temporal_frame.loc[(temporal_frame.model == name) & (temporal_frame.grouping == axis)]
            ax.plot(group.group, group.mae_mw, marker=".", label=name)
        ax.set(xlabel=f"Europe/Madrid {axis}" + (" (0 = Monday)" if axis == "weekday" else ""), ylabel="MAE (MW)")
        ax.legend()
    fig.savefig(artifacts / "temporal_errors.png", dpi=130)
    plt.close(fig)
    var_manifest = json.loads((ROOT / "runs/20261118_system312_f02_02/manifest.json").read_bytes())
    xgb_metrics = json.loads((ROOT / "runs/20261118_system312_g01_01/artifacts/metrics.json").read_bytes())
    complexities = {"VAR(24)": var_manifest["complexity"],
                    "XGB_full": xgb_metrics["selected"]["XGB_full"]["complexity"],
                    "LSTM": COMPLEXITY}
    validation_candidates = [
        {"model": {"VAR(24)": "VAR", "XGB_full": "XGB"}.get(name, name),
         "trial_id": chosen["trial_id"] if name == "LSTM" else name,
         "complexity": complexities.get(name, 0), **value}
        for name, value in metrics.items()
    ]
    xgb_trials = pd.read_csv(ROOT / "runs/20261118_system312_g01_01/artifacts/trials.csv")
    var_trials = pd.read_csv(ROOT / "runs/20261118_system312_f02_02/artifacts/trials.csv")
    result = {
        "selected_trial": chosen["trial_id"], "metrics": metrics,
        "cross_model_selection": select_validation(validation_candidates),
        "reload_max_abs_mw": parity, "n_reload_checked": len(output),
        "residual_autocorrelation": acf, "temporal_errors": temporal,
        "checkpoint_sha256": metadata["checkpoint_sha256"], "architecture_sha256": metadata["architecture_sha256"],
        "xgb_trials": len(xgb_trials), "xgb_fit_seconds": float(xgb_trials.elapsed_seconds.sum()),
        "var_trials": len(var_trials),
    }
    save_json(artifacts / "metrics.json", result)
    return result


def write_report(path, result, trials, metadata, run_id):
    chosen = next(t for t in trials if t["trial_id"] == result["selected_trial"])
    groups = pd.DataFrame(result["temporal_errors"])
    lstm_groups = groups.loc[groups.model == "LSTM"]
    days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    lines = [
        "# G02 LSTM findings", "", f"Run `{run_id}`. **PENDING HUMAN REVIEW**.", "",
        "## Trials", "", "| Trial | Best epoch | Stop epoch | CPU fit seconds | MAE MW | RMSE MW | MAPE % |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for t in trials:
        lines.append(f"| {t['trial_id']} | {t['best_epoch']} | {t['stopping_epoch']} | {t['elapsed_seconds']:.2f} | "
                     f"{t['mae_mw']:.3f} | {t['rmse_mw']:.3f} | {t['mape_percent']:.4f} |")
    lines += ["", f"C02 selected **{chosen['trial_id']}**. Both trials used seed 42, chronological batches of 64 and validation-only early stopping.",
              "", "## Q4. Daily and weekly patterns", "",
              f"[Validation trace](../../runs/{run_id}/artifacts/validation_trace.png) and "
              f"[Madrid group errors](../../runs/{run_id}/artifacts/temporal_errors.png) retain UTC alignment. "
              "Repeated local DST hours contribute as separate observations. Residuals are observed minus forecast.", "",
              "| UTC lag (hours) | Available pairs | LSTM | Persistence | Seasonal24 |",
              "|---:|---:|---:|---:|---:|"]
    for lag in (24, 168):
        at_lag = {v["model"]: v for v in result["residual_autocorrelation"] if v["lag_hours_utc"] == lag}
        lines.append(f"| {lag} | {at_lag['LSTM']['pairs']} | {at_lag['LSTM']['correlation']:.4f} | "
                     f"{at_lag['persistence']['correlation']:.4f} | {at_lag['seasonal24']['correlation']:.4f} |")
    lines.append("")
    for axis in ("hour", "weekday"):
        group = lstm_groups.loc[lstm_groups.grouping == axis]
        low, high = group.loc[group.mae_mw.idxmin()], group.loc[group.mae_mw.idxmax()]
        training_low = group.loc[group.d01_train_mean_load_mw.idxmin()]
        training_high = group.loc[group.d01_train_mean_load_mw.idxmax()]
        def label(entry):
            return f"{int(entry.group):02d}:00" if axis == "hour" else days[int(entry.group)]
        lines.append(
            f"By {axis}, D01 training means range from {training_low.d01_train_mean_load_mw:,.0f} MW ({label(training_low)}) "
            f"to {training_high.d01_train_mean_load_mw:,.0f} MW ({label(training_high)}). "
            f"LSTM validation MAE ranges from {low.mae_mw:.1f} MW ({label(low)}, n={low.n}) "
            f"to {high.mae_mw:.1f} MW ({label(high)}, n={high.n})."
        )
    lines += ["", "Daily error variation and the matched baselines describe how predictive accuracy changes across the day. "
              "Weekly learning is inconclusive from group errors and residual correlations. The 24-hour input contains no direct lag-168 observation.",
              "", "## Q5. Overfitting", "",
              f"[Learning curves](../../runs/{run_id}/artifacts/learning_curves.png) show per-epoch train and validation scaled MSE. "
              f"The selected trial ran {chosen['epochs_after_best']} epochs after its earliest best validation epoch. "
              f"Inference MSE with restored weights is {chosen['restored_train_mse']:.6f} (train) and {chosen['restored_val_mse']:.6f} (validation), "
              f"a gap of {chosen['restored_val_mse']-chosen['restored_train_mse']:+.6f}. "
              "The gap reflects generalization across these chronological periods. Using the same validation set for stopping and trial selection can make reported performance optimistic.",
              "", "## Q6. ML versus DL", "",
              "| Model | MAE MW | RMSE MW | MAPE % |", "|---|---:|---:|---:|"]
    for name, score in result["metrics"].items():
        lines.append(f"| {name} | {score['mae_mw']:.3f} | {score['rmse_mw']:.3f} | {score['mape_percent']:.4f} |")
    lines += ["", f"C02 cross-model selection on these five candidates gives **{result['cross_model_selection']['model']}**.",
              f"LSTM uses 24 x 4 sequential inputs with {COMPLEXITY:,} trainable parameters. XGB_full uses flattened lags and derived load features "
              f"including the 25-hour trend context. G01 ran {result['xgb_trials']} CPU trials in {result['xgb_fit_seconds']:.1f} s of fit time. "
              f"G02 ran two CPU trials in {sum(t['elapsed_seconds'] for t in trials):.1f} s of fit time. "
              f"F02 compared {result['var_trials']} lag candidates before its VAR(24) validation forecast. "
              "The baselines have no fitted parameters. VAR coefficients are explicit, XGB gain is associative, and LSTM state is harder to interpret directly.",
              "", "Validation scored 5,257 of 5,259 candidates with two missing truths and zero invalid contexts. "
              "Train scored 24,435 of 24,519 candidates with 32 missing truths and 52 invalid contexts. MAPE excludes zero truths.",
              "", "## Proposed model lock", "",
              f"- Weights SHA256: `{metadata['checkpoint_sha256']}`",
              f"- Architecture SHA256: `{metadata['architecture_sha256']}`",
              f"- Config SHA256: `{CONFIG_HASH}`",
              f"- Reload maximum absolute difference: {result['reload_max_abs_mw']:.9g} MW across {result['n_reload_checked']:,} validation rows.",
              "", "G02 acceptance, LSTM model lock and Phase 8 sign-off are **PENDING HUMAN REVIEW**.", ""]
    with path.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    run(args.run_id, args.config, args.replay)


if __name__ == "__main__":
    main()

