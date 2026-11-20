from __future__ import annotations

import csv
import copy
import hashlib
import io
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from practice_4.analysis.metrics import calculate_metrics


MODELS = {"persistence", "seasonal24", "VAR", "XGB", "LSTM"}
COLUMNS = {"schema_version", "model", "origin", "target_timestamp", "y_true_mw", "y_pred_mw", "split", "run_id"}
HASH_RE = re.compile(r"^[a-f0-9]{64}$")


def utc(value):
    if not isinstance(value, str) or not (value.endswith("Z") or value.endswith("+00:00")):
        raise ValueError("UTC timestamp required")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid timestamp") from exc
    if result.utcoffset() != timedelta(0):
        raise ValueError("UTC timestamp required")
    return result


def walk_forward(initial_history, targets, predict, context_valid, fixed_state):
    locked_state = copy.deepcopy(fixed_state())
    history = list(initial_history)
    scored_truth, scored_forecast, predictions = [], [], []
    missing = invalid = 0
    for reveal in targets:
        valid = bool(context_valid(tuple(history)))
        prediction = None
        if valid:
            prediction = float(predict(tuple(history)))
            if fixed_state() != locked_state:
                raise ValueError("Fixed model or transformation state changed")
            if not math.isfinite(prediction):
                raise ValueError("Non-finite forecast")
        truth = reveal()
        if truth is None:
            missing += 1
        else:
            truth = float(truth)
            if not math.isfinite(truth):
                raise ValueError("Non-finite truth")
            if not valid:
                invalid += 1
            else:
                scored_truth.append(truth)
                scored_forecast.append(prediction)
                predictions.append(prediction)
        history.append(truth)
    return {"metrics": calculate_metrics(scored_truth, scored_forecast, missing, invalid), "predictions": predictions, "history": history}


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def exact(obj, keys):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ValueError("Missing or unknown fields")


def string(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Nonempty string required")


def hash_value(value):
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise ValueError("Invalid SHA256")


def validate_predictions(data: bytes, run_id: str):
    reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""))
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or set(reader.fieldnames) != COLUMNS:
        raise ValueError("Invalid CSV header")
    seen, by_model = set(), {}
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("Invalid CSV row")
        if row["schema_version"] != "1" or row["model"] not in MODELS or row["split"] != "test" or row["run_id"] != run_id:
            raise ValueError("Invalid prediction identity")
        origin, target = utc(row["origin"]), utc(row["target_timestamp"])
        if target != origin + timedelta(hours=1):
            raise ValueError("Invalid horizon")
        key = (row["model"], origin, target)
        if key in seen:
            raise ValueError("Duplicate prediction")
        seen.add(key)
        try:
            truth, pred = float(row["y_true_mw"]), float(row["y_pred_mw"])
        except ValueError as exc:
            raise ValueError("Invalid numeric prediction") from exc
        if not math.isfinite(truth) or not math.isfinite(pred):
            raise ValueError("Non-finite prediction")
        by_model.setdefault(row["model"], {})[(origin, target)] = truth
    if not by_model:
        raise ValueError("No predictions")
    first = next(iter(by_model.values()))
    if any(values != first for values in by_model.values()):
        raise ValueError("Mismatched origins or truths")
    return by_model


def validate_evaluation(manifest_bytes: bytes, prediction_bytes: bytes, test_opening_approved: bool):
    if test_opening_approved is not True:
        raise ValueError("Test opening approval required")
    m = json.loads(manifest_bytes.decode("utf-8"), object_pairs_hook=no_duplicates, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Non-finite JSON")))
    exact(m, {"schema_version", "run_id", "stage_id", "prediction_file", "input_hashes", "model_hashes", "approval_refs", "counts", "metrics", "protocol", "created_at_utc", "limitations"})
    if m["schema_version"] != "1" or m["stage_id"] != "H01":
        raise ValueError("Unknown schema or stage")
    string(m["run_id"]); utc(m["created_at_utc"])
    exact(m["prediction_file"], {"path", "sha256"})
    path = m["prediction_file"]["path"]
    string(path)
    if Path(path).is_absolute() or ".." in Path(path).parts or "\\" in path or ":" in path:
        raise ValueError("Unsafe prediction path")
    hash_value(m["prediction_file"]["sha256"])
    if hashlib.sha256(prediction_bytes).hexdigest() != m["prediction_file"]["sha256"]:
        raise ValueError("Prediction hash mismatch")
    exact(m["input_hashes"], {"canonical_sha256", "split_sha256", "config_sha256", "preprocessor_sha256", "eligibility_sha256", "source_manifest_sha256"})
    for v in m["input_hashes"].values(): hash_value(v)
    exact(m["model_hashes"], MODELS)
    for v in m["model_hashes"].values(): hash_value(v)
    exact(m["approval_refs"], {"evaluation_contract", "model_locks", "test_opening"})
    for v in m["approval_refs"].values(): string(v)
    exact(m["counts"], {"n_considered", "n_scored", "n_zero_excluded", "n_missing_excluded", "n_input_excluded"})
    c = m["counts"]
    if any(type(v) is not int or v < 0 for v in c.values()) or not c["n_scored"] or c["n_zero_excluded"] > c["n_scored"] or c["n_considered"] != c["n_scored"] + c["n_missing_excluded"] + c["n_input_excluded"]:
        raise ValueError("Invalid counts")
    if m["protocol"] != {"forecast_horizon_hours": 1, "weights": "fixed", "transformations": "train_fitted_fixed", "update_order": "predict_score_reveal"}:
        raise ValueError("Invalid protocol")
    if not isinstance(m["limitations"], list) or any(not isinstance(v, str) for v in m["limitations"]):
        raise ValueError("Invalid limitations")
    predictions = validate_predictions(prediction_bytes, m["run_id"])
    if set(predictions) != MODELS or any(len(v) != c["n_scored"] for v in predictions.values()):
        raise ValueError("Model set or scored count mismatch")
    truths = next(iter(predictions.values())).values()
    zeros = sum(v == 0 for v in truths)
    if zeros != c["n_zero_excluded"]:
        raise ValueError("Zero count mismatch")
    exact(m["metrics"], MODELS)
    for value in m["metrics"].values():
        exact(value, {"mae_mw", "rmse_mw", "mape_percent", "mape_null_reason"})
        for k in ("mae_mw", "rmse_mw"):
            if type(value[k]) not in (int, float) or not math.isfinite(value[k]) or value[k] < 0: raise ValueError("Invalid metric")
        mp = value["mape_percent"]
        if zeros == c["n_scored"]:
            if mp is not None: raise ValueError("MAPE must be null")
            string(value["mape_null_reason"])
        elif type(mp) not in (int, float) or not math.isfinite(mp) or mp < 0 or value["mape_null_reason"] is not None:
            raise ValueError("Invalid MAPE")
    return m
