from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from practice_4.analysis.metrics import calculate_metrics
from practice_4.data.features import FLAT_FEATURE_NAMES, ORIGIN_COLUMNS

ROOT = Path(__file__).resolve().parents[3]
E02 = "runs/20261118_system312_e02_01/manifest.json"
E02_HASH = "620c4922f563c2032df14924df221ed3701d49266d1eef37a6c6e59acc8782b5"
SCALER = "runs/20261118_system312_d02_01/artifacts/scaler.json"
ORIGINS = "datasets/processed/origin_manifest.csv"
INPUTS = "datasets/processed/model_inputs.npz"
UPSTREAM = (
    "datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv",
    "datasets/processed/canonical_hourly.csv", "datasets/processed/split_manifest.json",
    "datasets/processed/prepared_hourly.csv", SCALER, ORIGINS, INPUTS,
)
EXPECTED = {"train": (24519, 32, 52, 24435), "validation": (5259, 2, 0, 5257)}
VERSION = "1"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def model_configs(scaler_hash, source_hash):
    return {
        name: {
            "model": name, "trial_id": name + "_01", "implementation_version": VERSION,
            "source_sha256": source_hash, "horizon_hours": 1, "lag_offset": offset,
            "scaler_sha256": scaler_hash, "schema_version": "1",
            "protocol_version": "predict_score_reveal_v1", "complexity": 0,
        }
        for name, offset in (("persistence", 0), ("seasonal24", 23))
    }


def forecasts(sequence, flat, mean, scale):
    if sequence.ndim != 3 or sequence.shape[1:] != (24, 4) or flat.shape != (len(sequence), 96):
        raise ValueError("Invalid feature shapes")
    if not np.isfinite(sequence).all() or not np.isfinite(flat).all():
        raise ValueError("Nonfinite feature")
    if not np.isfinite([mean, scale]).all() or scale <= 0:
        raise ValueError("Invalid scaler")
    for offset, index in ((0, -1), (23, 0)):
        column = FLAT_FEATURE_NAMES.index(f"lag{offset:02d}_load")
        if not np.array_equal(flat[:, column], sequence[:, index, 0]):
            raise ValueError("Flat lag and sequence disagree")
    return {
        "persistence": sequence[:, -1, 0] * scale + mean,
        "seasonal24": sequence[:, 0, 0] * scale + mean,
    }


def verify_lineage(root):
    manifest_path = root / E02
    if sha(manifest_path) != E02_HASH:
        raise ValueError("E02 manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest["stage_id"], manifest["status"]) != ("E02", "completed"):
        raise ValueError("E02 predecessor invalid")
    recorded = {item["path"]: item["sha256"] for item in manifest["inputs"] + manifest["outputs"]}
    values = {name: sha(root / name) for name in UPSTREAM}
    if any(values[name] != recorded[name] for name in UPSTREAM):
        raise ValueError("E02 upstream hash mismatch")
    return values


def align(root, target_rows, truths):
    eligible = []
    counts = {name: [0, 0, 0, 0] for name in EXPECTED}
    with (root / ORIGINS).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != ORIGIN_COLUMNS:
            raise ValueError("Origin schema mismatch")
        for target, row in enumerate(reader, start=25):
            if target >= 29803 or int(row["target_row"]) != target:
                raise ValueError("Candidate chronology or boundary mismatch")
            split = "train" if target < 24544 else "validation"
            origin_time = datetime.fromisoformat(row["origin_timestamp_utc"])
            target_time = datetime.fromisoformat(row["target_timestamp_utc"])
            if row["split"] != split or int(row["origin_row"]) != target - 1 or int(row["context_start_row"]) != target - 25 or origin_time.utcoffset() != timedelta(0) or target_time != origin_time + timedelta(hours=1):
                raise ValueError("Origin alignment mismatch")
            counts[split][0] += 1
            reason = row["exclusion_reason"]
            if reason == "missing_truth":
                counts[split][1] += 1
            elif reason == "invalid_context":
                counts[split][2] += 1
            elif reason == "":
                index = len(eligible)
                if row["eligible"] != "True" or int(row["sample_index"]) != index or index >= len(target_rows) or int(target_rows[index]) != target or float(row["y_true_mw"]) != truths[index]:
                    raise ValueError("Eligible sample alignment mismatch")
                counts[split][3] += 1
                eligible.append(row)
            else:
                raise ValueError("Unknown exclusion")
    if {name: tuple(value) for name, value in counts.items()} != EXPECTED or len(eligible) != len(target_rows):
        raise ValueError("Eligibility counts mismatch")
    return eligible, counts


def run(run_id, replay=False):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    if replay and (ROOT / "runs" / run_id).exists():
        raise FileExistsError("Replay output collision")
    if platform.python_version_tuple()[:2] != ("3", "12"):
        raise ValueError("Python 3.12 required")
    approval = (ROOT / "docs/phase_details/phase_06.md").read_text(encoding="utf-8")
    if "F01 execution authorized" not in approval or "Human APPROVED" not in approval:
        raise ValueError("F01 approval missing")
    before = verify_lineage(ROOT)
    run_dir = ROOT / "runs" / run_id
    report = run_dir / "artifacts/baseline_results.md" if replay else ROOT / "docs/results/baseline_results.md"
    log = run_dir / "artifacts/execution.md" if replay else ROOT / "docs/logs" / f"F01_{run_id}.md"
    if run_dir.exists() or report.exists() or log.exists():
        raise FileExistsError("Run or output already exists")
    scaler = json.loads((ROOT / SCALER).read_text(encoding="utf-8"))
    with np.load(ROOT / INPUTS, allow_pickle=False) as data:
        if int(data["schema_version"]) != 1:
            raise ValueError("Schema mismatch")
        targets, truths = data["target_row"], data["y_true_mw"]
        predicted = forecasts(data["x_lstm"], data["x_flat"], scaler["mean"][0], scaler["scale"][0])
        rows, counts = align(ROOT, targets, truths)
    if not np.isfinite(truths).all() or any(not np.isfinite(v).all() for v in predicted.values()):
        raise ValueError("Nonfinite truth or prediction")
    configs = json.loads((ROOT / "runs/20261118_system312_f01_01/config.json").read_bytes()) if replay else model_configs(before[SCALER], sha(Path(__file__)))
    hashes = {name: hashlib.sha256(canonical(config)).hexdigest() for name, config in configs.items()}
    metrics = {}
    for name, values in predicted.items():
        metrics[name] = {}
        for split, (_, missing, invalid, _) in EXPECTED.items():
            indices = np.array([i for i, row in enumerate(rows) if row["split"] == split])
            metrics[name][split] = calculate_metrics(truths[indices], values[indices], missing, invalid)
    if before != verify_lineage(ROOT):
        raise ValueError("Upstream hash changed")
    artifacts = run_dir / "artifacts"
    artifacts.mkdir(parents=True)
    prediction_path = artifacts / "predictions.csv"
    with prediction_path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["model", "origin", "target_timestamp", "target_row", "y_true_mw", "y_pred_mw", "split", "run_id"])
        for name, values in predicted.items():
            for row, truth, value in zip(rows, truths, values):
                writer.writerow([name, row["origin_timestamp_utc"], row["target_timestamp_utc"], row["target_row"], repr(float(truth)), repr(float(value)), row["split"], run_id])
    (artifacts / "metrics.json").write_bytes(canonical(metrics) + b"\n")
    (run_dir / "config.json").write_bytes(canonical(configs) + b"\n")
    environment = {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform()}
    (run_dir / "environment.json").write_bytes(canonical(environment) + b"\n")
    lines = ["# F01 Baseline Results", "", f"Run `{run_id}` · **PENDING HUMAN REVIEW**.", "", "Warm-up: 25 target rows. MAPE is a percentage computed from original MW truths.", "", "| Model | Split | Candidates | Missing | Invalid context | Scored | MAE MW | RMSE MW | MAPE % |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name in predicted:
        for split in EXPECTED:
            m = metrics[name][split]
            lines.append(f"| {name} | {split} | {m['n_considered']} | {m['n_missing_excluded']} | {m['n_input_excluded']} | {m['n_scored']} | {m['mae_mw']:.6f} | {m['rmse_mw']:.6f} | {m['mape_percent']:.6f} |")
        lines.append(f"\n{name} complexity 0, RV2 model configuration SHA256 `{hashes[name]}`.")
    lines.extend(["", "Forecasts use fixed D02 scaling and the common E02 eligible origins. The one-step lab protocol assumes input measurements are available at the end of the origin hour.", ""])
    report.write_text("\n".join(lines), encoding="utf-8")
    log.write_text(f"# F01 {run_id}\n\nStatus **PENDING HUMAN REVIEW**.\n\nCommand `py -3.12 -m practice_4.models.baselines --run-id {run_id}` completed. Upstream SHA256 values matched E02 before and after scoring. Raw and canonical CSVs were hashed as opaque bytes.\n", encoding="utf-8")
    output_paths = [prediction_path, artifacts / "metrics.json", run_dir / "config.json", run_dir / "environment.json", report, log]
    manifest = {
        "schema_version": "1", "stage_id": "F01", "run_id": run_id, "status": "completed",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "approval_refs": {"phase_06": "Human approved Phase 6 and authorized F01 on 2026-11-18 via Director review"},
        "inputs": [{"path": key, "sha256": value} for key, value in before.items()],
        "e02_manifest_sha256": E02_HASH, "model_hashes": hashes, "counts": counts,
        "outputs": [{"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)} for path in output_paths],
        "limitations": ["F01 gate and F02 execution await Human review", "Raw and canonical input files were byte-hashed only"],
    }
    (run_dir / "manifest.json").write_bytes(canonical(manifest) + b"\n")
    print(json.dumps({"run_id": run_id, "metrics": metrics, "model_hashes": hashes}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    run(args.run_id, args.replay)


if __name__ == "__main__":
    main()
