from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import subprocess
import sys
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from practice_4.analysis.metrics import calculate_metrics
from practice_4.analysis.walk_forward import validate_evaluation
from practice_4.data.preprocessing import CausalState, FEATURES, transform
from practice_4.models.var_model import predict_levels


ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "20261120_system312_h01_01"
START_ROW = 29803
END_ROW = 35063
MODELS = ("persistence", "seasonal24", "VAR", "XGB", "LSTM")
PREDICTION_COLUMNS = ("schema_version", "model", "origin", "target_timestamp", "y_true_mw", "y_pred_mw", "split", "run_id")
ELIGIBILITY_COLUMNS = ("target_row", "origin", "target_timestamp", "observed", "context_valid", "eligible", "reason")
DIAGNOSTIC_COLUMNS = ("target_row", "origin", "target_timestamp", "load_mw", "temperature_k", "humidity_percent", "wind_speed_mps")
XGB_WORKER = "\n".join((
    "import json, sys, numpy as np, xgboost as xgb",
    "model = xgb.Booster(model_file=sys.argv[1])",
    "print(json.dumps({'ready': True, 'version': xgb.__version__, 'features': model.feature_names}), flush=True)",
    "for line in sys.stdin:",
    "    try:",
    "        values = np.asarray(json.loads(line), dtype=np.float32).reshape(1, -1)",
    "        dmatrix = xgb.DMatrix(values, feature_names=model.feature_names)",
    "        result = float(model.predict(dmatrix, iteration_range=(0, 931))[0])",
    "        print(json.dumps({'value': result}), flush=True)",
    "    except BaseException as exc:",
    "        print(json.dumps({'error': str(exc)}), flush=True)",
))


class XGBWorker:
    def __init__(self, model_path: Path):
        worker_environment = os.environ.copy()
        for name in ("CUDA_VISIBLE_DEVICES", "KERAS_BACKEND", "TF_ENABLE_ONEDNN_OPTS", "TF_DETERMINISTIC_OPS"):
            worker_environment.pop(name, None)
        self.process = subprocess.Popen(
            [sys.executable, "-u", "-c", XGB_WORKER, str(model_path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1, env=worker_environment,
        )
        line = self.process.stdout.readline()
        if not line:
            error = self.process.stderr.read()
            raise RuntimeError(f"XGBoost worker exited during startup: {error}")
        ready = json.loads(line)
        if not ready.get("ready") or ready.get("version") != "3.4.1":
            self.close()
            raise ValueError("XGBoost worker failed its locked runtime check")
        self.feature_names = ready["features"]

    def predict(self, values):
        self.process.stdin.write(json.dumps(np.asarray(values).reshape(-1).tolist()) + "\n")
        self.process.stdin.flush()
        response = json.loads(self.process.stdout.readline())
        if "error" in response or not math.isfinite(response.get("value", float("nan"))):
            raise ValueError(f"XGBoost inference failed: {response}")
        return float(response["value"])

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            self.process.wait(timeout=20)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\r\n")


def prepare_row(row: dict, state: CausalState, scaler: dict, expected_row: int) -> dict:
    timestamp = pd.Timestamp(row["timestamp_utc"])
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError("Non-UTC canonical timestamp")
    values = {name: float(row[name]) if row[name] else float("nan") for name in ("load", "temp", "humidity", "wind_speed")}
    if not all(math.isfinite(values[name]) for name in ("temp", "humidity", "wind_speed")):
        raise ValueError("Unexpected missing weather")
    if values["temp"] <= 0 or not 0 <= values["humidity"] <= 100 or values["wind_speed"] < 0:
        raise ValueError("Unexpected invalid weather")
    observed = row["load_observed"] == "True"
    if row["load_observed"] not in ("True", "False") or observed != math.isfinite(values["load"]):
        raise ValueError("Raw load and observed mask disagree")
    if not observed:
        state.missing_run += 1
        values["load_input"] = state.last_load if state.missing_run == 1 else float("nan")
    else:
        state.last_load = values["load"]
        state.missing_run = 0
        values["load_input"] = values["load"]
    values["target_row"] = expected_row
    values["timestamp_utc"] = timestamp
    for idx, name in enumerate(FEATURES):
        value = values[name]
        values[name + "_scaled"] = (value - scaler["mean"][idx]) / scaler["scale"][idx] if math.isfinite(value) else float("nan")
    state.last_timestamp = timestamp.isoformat()
    return values


def load_models(run_root: Path, scaler: dict, xgb_config: dict, lstm_config: dict, booster):
    print("H01 loading VAR", flush=True)
    with np.load(run_root / "runs/20261118_system312_f02_02/artifacts/model.npz", allow_pickle=False) as saved:
        print("H01 VAR archive opened", flush=True)
        var_coef = saved["coefs"].copy()
        print("H01 VAR coefficients copied", flush=True)
        var_intercept = saved["intercept"].copy()
        print("H01 VAR intercept copied", flush=True)
        p_value = saved["p"].item()
        print("H01 VAR lag read", p_value, flush=True)
        if p_value != 24 or var_coef.shape != (24, 4, 4):
            raise ValueError("VAR lock shape mismatch")
    print("H01 VAR lock verified", flush=True)
    print("H01 loading TensorFlow", flush=True)
    import tensorflow as tf
    import keras
    keras.backend.clear_session()
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.experimental.enable_op_determinism()
    model = keras.models.model_from_json((run_root / "runs/20261118_system312_g02_01/artifacts/lstm_architecture.json").read_text(encoding="utf-8"))
    print("H01 loading LSTM weights", flush=True)
    model.load_weights(run_root / "runs/20261118_system312_g02_01/artifacts/lstm.weights.h5")
    print("H01 checking model metadata", flush=True)
    if list(xgb_config["feature_order"]["XGB_full"]) != list(booster.feature_names):
        raise ValueError("XGBoost feature order mismatch")
    if lstm_config["feature_order"] != ["load_input_scaled", "temp_scaled", "humidity_scaled", "wind_speed_scaled"]:
        raise ValueError("LSTM feature order mismatch")
    return var_coef, var_intercept, booster, model, tf


def predict(history: list[dict], scaler: dict, var_coef, var_intercept, booster, lstm, tf):
    sequence = np.asarray([[row[name + "_scaled"] for name in FEATURES] for row in history[-24:]], dtype=np.float64)
    context_load = np.asarray([row["load_input_scaled"] for row in history[-25:]], dtype=np.float64)
    if sequence.shape != (24, 4) or not np.isfinite(sequence).all() or not np.isfinite(context_load).all():
        return None
    baseline_load = sequence[-1, 0] * scaler["scale"][0] + scaler["mean"][0]
    seasonal_load = sequence[0, 0] * scaler["scale"][0] + scaler["mean"][0]
    var_value = predict_levels(sequence, var_coef, var_intercept)[0] * scaler["scale"][0] + scaler["mean"][0]
    flat = sequence.reshape(1, 96)
    xgb_features = np.concatenate((flat.reshape(-1), [np.mean(context_load[-6:]), np.std(context_load[1:], ddof=0), context_load[-1] - context_load[0]]))
    xgb_value = booster.predict(xgb_features)
    lstm_input = np.repeat(sequence.astype(np.float32)[None, ...], 64, axis=0)
    lstm_scaled = float(lstm(lstm_input, training=False).numpy().reshape(-1)[0])
    lstm_value = lstm_scaled * scaler["scale"][0] + scaler["mean"][0]
    values = dict(zip(MODELS, (baseline_load, seasonal_load, var_value, xgb_value, lstm_value), strict=True))
    if any(not math.isfinite(float(value)) for value in values.values()):
        raise ValueError("Non-finite model forecast")
    return values


def csv_bytes(columns, rows) -> bytes:
    import io
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def run(run_id: str = RUN_ID):
    print("H01 preflight started", flush=True)
    raw = ROOT / "datasets/raw"
    files = {
        "canonical": ROOT / "datasets/processed/canonical_hourly.csv",
        "split": ROOT / "datasets/processed/split_manifest.json",
        "prepared": ROOT / "datasets/processed/prepared_hourly.csv",
        "scaler": ROOT / "runs/20261118_system312_d02_01/artifacts/scaler.json",
        "var": ROOT / "runs/20261118_system312_f02_02/artifacts/model.npz",
        "xgb": ROOT / "runs/20261118_system312_g01_01/artifacts/XGB_full.json",
        "lstm_weights": ROOT / "runs/20261118_system312_g02_01/artifacts/lstm.weights.h5",
        "lstm_architecture": ROOT / "runs/20261118_system312_g02_01/artifacts/lstm_architecture.json",
    }
    expected = {
        "canonical": "7122e873708d3297e38316a5d29a08236c516fcdf20327e7724edc1d31a83045",
        "split": "d21e718e1b3661186df9f0848e7bd341b5760a6d29fdd3f48dc51102cd0f307d",
        "scaler": "ebfa412b7bce9ac077776b416df1083eaff32b08c48c28dc5d2e7e06b2757b11",
        "var": "0b3820731f3369f57699adaa64a7b1f4a5cbbf659c48331fc5721335572d3e26",
        "xgb": "e7386e8cfc38d51d6abc51abad383fb2c9d6360c9c955c6fe3ddb33883aec8ae",
        "lstm_weights": "512715c5249f35bcfe46d1ecdbfc4413dbb1d3f263fe73f41dc9845fe5a69a1c",
        "lstm_architecture": "c858df9f6417ac508d9b4d2195ce0b29a539ab89d4bb5d10950ac12f6d7af807",
    }
    for name, path in files.items():
        if name in expected and digest(path) != expected[name]:
            raise ValueError(f"Locked input mismatch: {name}")
    print("H01 lock hashes verified", flush=True)
    raw_hashes = {p.name: digest(p) for p in (raw / "energy_dataset.csv", raw / "weather_features.csv")}
    split = json.loads(files["split"].read_text(encoding="utf-8"))
    if split["splits"]["test"]["start_row"] != START_ROW or split["splits"]["test"]["end_row"] != END_ROW:
        raise ValueError("Test split boundary mismatch")
    scaler = json.loads(files["scaler"].read_text(encoding="utf-8"))
    xgb_config = json.loads((ROOT / "runs/20261118_system312_g01_01/config.json").read_text(encoding="utf-8"))
    lstm_config = json.loads((ROOT / "runs/20261118_system312_g02_01/config.json").read_text(encoding="utf-8"))
    d02_manifest = json.loads((ROOT / "runs/20261118_system312_d02_01/manifest.json").read_text(encoding="utf-8"))
    prepared = pd.read_csv(files["prepared"], nrows=START_ROW, float_precision="round_trip")
    print("H01 prepared prefix loaded", flush=True)
    if len(prepared) != START_ROW:
        raise ValueError("Prepared prefix incomplete")
    state = CausalState(last_load=float(prepared.loc[START_ROW - 1, "load_input"]), missing_run=0, last_timestamp=split["splits"]["validation"]["end_utc"])
    history = []
    for _, row in prepared.iloc[START_ROW - 25:START_ROW].iterrows():
        history.append({**{name: float(row[name]) for name in (*[n + "_scaled" for n in FEATURES], "load_input")}, "timestamp_utc": row["timestamp_utc"]})
    if len(history) != 25 or history[-1]["load_input"] != 25194.0:
        raise ValueError("Initial H01 context mismatch")
    booster = XGBWorker(files["xgb"])
    var_coef, var_intercept, booster, lstm, tf = load_models(ROOT, scaler, xgb_config, lstm_config, booster)
    print("H01 locked models loaded", flush=True)
    run_dir = ROOT / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(run_dir)
    artifacts = run_dir / "artifacts"
    artifacts.mkdir(parents=True)
    model_lock_before = {name: digest(path) for name, path in files.items() if name in expected}
    eligible_rows, prediction_rows, diagnostic_rows = [], [], []
    scored_truth, scored_predictions = {name: [] for name in MODELS}, {name: [] for name in MODELS}
    missing_truth = input_excluded = scored = zero = 0
    with files["canonical"].open("rb", buffering=0) as stream:
        reader = csv.DictReader(line.decode("utf-8") for line in stream)
        if reader.fieldnames != ["timestamp_utc", "load", "temp", "humidity", "wind_speed", "load_observed"]:
            raise ValueError("Canonical schema mismatch")
        for _ in range(START_ROW):
            next(reader)
        for target_row in range(START_ROW, END_ROW + 1):
            origin = pd.Timestamp(history[-1]["timestamp_utc"])
            forecast = predict(history, scaler, var_coef, var_intercept, booster, lstm, tf)
            raw_row = next(reader)
            new = prepare_row(raw_row, state, scaler, target_row)
            target_ts = new["timestamp_utc"]
            if target_ts != pd.Timestamp(split["splits"]["test"]["start_utc"]) + pd.Timedelta(hours=target_row - START_ROW):
                raise ValueError("Unexpected test chronology")
            valid = forecast is not None
            observed = raw_row["load_observed"] == "True"
            reason = "" if observed and valid else "missing_truth" if not observed else "invalid_context"
            eligible_rows.append((target_row, origin.isoformat(), target_ts.isoformat(), observed, valid, not reason, reason))
            if reason == "missing_truth":
                missing_truth += 1
            elif reason == "invalid_context":
                input_excluded += 1
            else:
                scored += 1
                truth = new["load"]
                zero += int(truth == 0)
                diagnostic_rows.append((target_row, origin.isoformat(), target_ts.isoformat(), truth, new["temp"], new["humidity"], new["wind_speed"]))
                for model in MODELS:
                    value = float(forecast[model])
                    scored_truth[model].append(truth)
                    scored_predictions[model].append(value)
                    prediction_rows.append(("1", model, origin.isoformat(), target_ts.isoformat(), repr(truth), repr(value), "test", run_id))
            history.append(new)
            history = history[-25:]
            if target_row % 500 == 0:
                print(f"processed target row {target_row}", flush=True)
    booster.close()
    if missing_truth + input_excluded + scored != END_ROW - START_ROW + 1 or not scored:
        raise ValueError("H01 count conservation failed")
    if model_lock_before != {name: digest(path) for name, path in files.items() if name in expected}:
        raise ValueError("Fixed model or input state changed")
    metrics = {name: calculate_metrics(scored_truth[name], scored_predictions[name], missing_truth, input_excluded) for name in MODELS}
    prediction_data = csv_bytes(PREDICTION_COLUMNS, prediction_rows)
    metrics_columns = ("schema_version", "run_id", "model", "split", "mae_mw", "rmse_mw", "mape_percent", "mape_null_reason", "n_considered", "n_scored", "n_zero_excluded", "n_missing_excluded", "n_input_excluded")
    metric_rows = [("1", run_id, name, "test", metrics[name]["mae_mw"], metrics[name]["rmse_mw"], metrics[name]["mape_percent"], metrics[name].get("mape_null_reason"), END_ROW-START_ROW+1, scored, zero, missing_truth, input_excluded) for name in MODELS]
    metrics_data = csv_bytes(metrics_columns, metric_rows)
    eligibility_data = csv_bytes(ELIGIBILITY_COLUMNS, eligible_rows)
    diagnostic_data = csv_bytes(DIAGNOSTIC_COLUMNS, diagnostic_rows)
    for name, data in (("test_predictions.csv", prediction_data), ("test_metrics.csv", metrics_data), ("test_eligibility.csv", eligibility_data), ("diagnostic_context.csv", diagnostic_data)):
        (artifacts / name).write_bytes(data)
    source_manifest = {"run_id": run_id, "python": platform.python_version(), "versions": {"numpy": np.__version__, "pandas": pd.__version__, "xgboost": importlib.metadata.version("xgboost")}, "raw_hashes": raw_hashes, "input_hashes": {name: digest(path) for name, path in files.items()}, "model_hashes": {"VAR": expected["var"], "XGB": expected["xgb"], "LSTM_weights": expected["lstm_weights"], "LSTM_architecture": expected["lstm_architecture"]}, "approval_refs": {"execution": "Human instruction in active conversation: complete Practice 4 and continue H01/H02", "phase_9": "docs/phase_details/phase_09.md"}}
    json_write(run_dir / "source_manifest.json", source_manifest)
    f01_config = json.loads((ROOT/"runs/20261118_system312_f01_01/config.json").read_text(encoding="utf-8"))
    model_hashes = {name: hashlib.sha256(json.dumps(f01_config[name], sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest() for name in ("persistence", "seasonal24")}
    model_hashes.update({"VAR": expected["var"], "XGB": expected["xgb"], "LSTM": expected["lstm_weights"]})
    rv2_metrics = {name: {key: value[key] for key in ("mae_mw", "rmse_mw", "mape_percent", "mape_null_reason")} for name, value in metrics.items()}
    eval_manifest = {"schema_version":"1","run_id":run_id,"stage_id":"H01","prediction_file":{"path":"outputs/predictions/test_predictions.csv","sha256":hashlib.sha256(prediction_data).hexdigest()},"input_hashes":{"canonical_sha256":digest(files["canonical"]),"split_sha256":digest(files["split"]),"config_sha256":digest(ROOT/"runs/20261118_system312_g02_01/config.json"),"preprocessor_sha256":digest(files["scaler"]),"eligibility_sha256":hashlib.sha256(eligibility_data).hexdigest(),"source_manifest_sha256":digest(run_dir/"source_manifest.json")},"model_hashes":model_hashes,"approval_refs":{"evaluation_contract":"Human-approved C02/RV2 v1","model_locks":"Accepted F01/F02/G01/G02 locks in Practice 4 manifests","test_opening":"Human instruction: do what is needed to complete Practice 4"},"counts":{"n_considered":END_ROW-START_ROW+1,"n_scored":scored,"n_zero_excluded":zero,"n_missing_excluded":missing_truth,"n_input_excluded":input_excluded},"metrics":rv2_metrics,"protocol":{"forecast_horizon_hours":1,"weights":"fixed","transformations":"train_fitted_fixed","update_order":"predict_score_reveal"},"created_at_utc":datetime.now(timezone.utc).isoformat(),"limitations":["One-step walk-forward with observed truth revealed after each target; reflects the approved availability assumption.","Test rankings are descriptive and do not change validation-selected model locks."]}
    json_write(artifacts/"evaluation_manifest.json",eval_manifest)
    validate_evaluation((artifacts/"evaluation_manifest.json").read_bytes(),prediction_data,True)
    manifest={"schema_version":"1","run_id":run_id,"stage_id":"H01","status":"completed","environment":{"python":platform.python_version()},"counts":eval_manifest["counts"],"outputs":{p.name:digest(p) for p in artifacts.iterdir()},"input_hashes":source_manifest["input_hashes"]}
    json_write(run_dir/"manifest.json",manifest)
    predictions_path=ROOT/"outputs/predictions/test_predictions.csv"; predictions_path.parent.mkdir(parents=True,exist_ok=True)
    metrics_path=ROOT/"outputs/tables/test_metrics.csv"; metrics_path.parent.mkdir(parents=True,exist_ok=True)
    for path,data in ((predictions_path,prediction_data),(metrics_path,metrics_data)):
        with path.open("xb") as output: output.write(data)
        if digest(path)!=hashlib.sha256(data).hexdigest(): raise ValueError("Promotion integrity mismatch")
    print(json.dumps({"run_id":run_id,"counts":eval_manifest["counts"],"metrics":metrics},indent=2))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",default=RUN_ID)
    parser.add_argument("--config",required=False)
    args=parser.parse_args()
    run(args.run_id)


if __name__ == "__main__":
    main()
