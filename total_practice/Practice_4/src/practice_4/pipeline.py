from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import jsonschema

from practice_4.data.ingestion import sha256_file, summarize


HASH = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
FILE = {"type": "object", "required": ["path", "sha256"], "properties": {"path": {"type": "string", "minLength": 1}, "sha256": HASH}, "additionalProperties": False}
MANIFEST_SCHEMA = {"type": "object", "required": ["schema_version", "run_id", "stage_id", "status", "started_at_utc", "finished_at_utc", "approval_refs", "inputs", "config_sha256", "environment", "outputs", "checks", "limitations"], "properties": {"schema_version": {"const": "1"}, "run_id": {"type": "string", "minLength": 1}, "stage_id": {"enum": ["B01", "B02", "C01", "C02", "D01", "D02", "E01", "E02"]}, "status": {"enum": ["running", "completed", "failed"]}, "started_at_utc": {"type": "string"}, "finished_at_utc": {"type": ["string", "null"]}, "approval_refs": {"type": "object", "minProperties": 1}, "inputs": {"type": "array", "items": FILE}, "config_sha256": HASH, "environment": {"type": "object", "minProperties": 1}, "outputs": {"type": "array", "items": FILE}, "checks": {"type": "array", "items": {"type": "object", "required": ["name", "status", "evidence"]}}, "limitations": {"type": "array", "items": {"type": "string"}}}, "additionalProperties": False}


def validate_manifest(manifest: dict) -> None:
    jsonschema.validate(manifest, MANIFEST_SCHEMA)


def bootstrap(root: Path, config: dict) -> list[dict]:
    if config.get("stage") != "B01" or not config.get("approval_references"):
        raise ValueError("B01 and approval references required")
    result = []
    for name, expected in config["inputs"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe input path")
        actual = sha256_file(root / relative)
        if actual != expected:
            raise ValueError(f"Input hash mismatch: {name}")
        result.append({"path": relative.as_posix(), "sha256": actual})
    approval = (root / "docs/phase_details/phase_01.md").read_text(encoding="utf-8")
    if "Unblock & Complete Stage B01" not in approval or "Human duyệt" not in approval:
        raise ValueError("B01 approval record missing")
    required = {"docs/phase_details/phase_00.md", "docs/phase_details/phase_01.md", "docs/results/problem_definition.md", "datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv"}
    if set(config["inputs"]) != required:
        raise ValueError("Unexpected bootstrap input set")
    return result


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audit_markdown(summary: dict, run_id: str) -> str:
    e, w = summary["energy"], summary["weather"]
    lines = ["# B01 — Raw provenance và data audit", "", f"Run: `{run_id}`. Trạng thái: **PENDING HUMAN REVIEW**.", "", "Nguồn, version 1, CC0, ngày tải 2026-11-17, units và timestamp semantics do Human xác nhận; Kaggle page/API metadata không đọc được trong môi trường này. Không khẳng định đã xác minh độc lập archive. Nguồn upstream theo Human: ENTSO-E Transparency Platform và OpenWeatherMap API.", "", "## Raw quality", "", f"- Energy: {e['rows']} rows, {len(e['columns'])} columns, UTC {e['utc_min']} đến {e['utc_max']}; {e['unique_timestamps']} timestamps duy nhất, {e['missing_hours']} missing hours, {e['duplicate_timestamps']} duplicate timestamps; ordered={e['ordered']}.", f"- Weather: {w['rows']} rows, {len(w['columns'])} columns, UTC {w['utc_min']} đến {w['utc_max']}; {w['duplicate_rows']} duplicate full rows, {w['duplicate_city_hour_groups']} duplicate city-hour groups, {w['extra_city_hour_rows']} extra rows, {w['conflicting_required_weather_groups']} groups xung đột trong ba weather variables.", f"- Missing: `total load actual` {e['missing']['total load actual']}; temp {w['missing']['temp']}, humidity {w['missing']['humidity']}, wind_speed {w['missing']['wind_speed']}.", "", "| Trường | Min | Max | Unit Human xác nhận | Basic range check |", "|---|---:|---:|---|---|"]
    for name, result in summary["ranges"].items():
        lines.append(f"| {name} | {result['min']} | {result['max']} | {result['unit']} | {result['basic_range_pass']} |")
    lines += ["", "Basic checks chỉ kiểm load/wind không âm, Kelvin dương và humidity 0–100; không chứng minh đơn vị hoặc xác nhận outlier. Nhiệt độ tối đa 315,6 K cao hơn mốc xấp xỉ 315 trong yêu cầu; wind speed tối đa cần review vì nonnegative không chứng minh hợp lý.", "", "## City coverage", "", "| City label gốc | Rows | Unique timestamps | Thiếu so với energy | Thừa so với energy |", "|---|---:|---:|---:|---:|"]
    for city, c in w["city_coverage"].items():
        lines.append(f"| `{city}` | {c['rows']} | {c['unique_timestamps']} | {c['missing_energy_timestamps']} | {c['extra_timestamps']} |")
    lines += ["", "## B02 policy proposals — CHỜ HUMAN DUYỆT", "", "- Strip whitespace city names trên derived copy; kiểm tra va chạm tên.", "- Deduplicate city-hour chỉ sau khi xác nhận các biến bắt buộc nhất quán; dừng nếu có conflict, không tự chọn first row khi conflict.", "- Unweighted mean của năm city làm national weather proxy; nêu giới hạn đại diện.", "- Parse explicit offsets sang UTC và align hourly bằng join đã kiểm cardinality/coverage.", "- Giữ nguyên missing `total load actual` và observed mask; không impute truth.", "", "Chưa thực hiện B02, tạo canonical hoặc phê duyệt policy. Counts, columns, missing và hashes đầy đủ trong run artifacts. UTC parsing không tự chứng minh timezone nguồn; semantics do Human xác nhận."]
    return "\n".join(lines) + "\n"


def run(root: Path, config_path: Path, run_id: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = bootstrap(root, config)
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    env = {"python": platform.python_version(), "platform": platform.platform(), "packages": {name: metadata.version(name) for name in ["pandas", "numpy", "pytest", "setuptools", "wheel", "jsonschema"]}}
    manifest = {"schema_version": "1", "run_id": run_id, "stage_id": "B01", "status": "running", "started_at_utc": now(), "finished_at_utc": None, "approval_refs": config["approval_references"], "inputs": inputs, "config_sha256": sha256_file(config_path), "environment": env, "outputs": [], "checks": [], "limitations": ["Source units/time semantics and license/version supplied by Human; Kaggle page/API not independently accessible.", "System Python used; clean-environment reproduction not verified."]}
    (run_dir / "config.json").write_bytes(config_path.read_bytes())
    write_json(run_dir / "environment.json", env)
    try:
        summary = summarize(root / "datasets/raw/energy_dataset.csv", root / "datasets/raw/weather_features.csv")
        if not all(x["basic_range_pass"] for x in summary["ranges"].values()):
            raise ValueError("Basic physical range check failed")
        bootstrap(root, config)
        write_json(run_dir / "audit_summary.json", summary)
        source_path = root / "datasets/raw/source_manifest.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        source["schema_version"] = "1"
        source["status"] = "human_confirmed_pending_review"
        source["source"]["provenance"] = "Kaggle dataset nicholasjhana/energy-consumption-generation-prices-and-weather (downloaded 2026-11-17 by Human); Kaggle page/API metadata unreachable from offline/headless environment, upstream sources ENTSO-E Transparency Platform & OpenWeatherMap"
        source["source"]["metadata_basis"] = "Human confirmation 2026-11-18; not independently verified"
        source["units"] = {name: result["unit"] for name, result in summary["ranges"].items()}
        source["time_semantics"] = {"basis": "Human confirmation", "raw": "ISO-8601 offsets +01:00 and +02:00, CET/CEST", "audit_index": "UTC", "start": summary["energy"]["utc_min"], "end": summary["energy"]["utc_max"]}
        source["unresolved"] = ["Independent archive checksum, source metadata verification and exact retrieval time", "B02 dedup, proxy, timezone policy and contract await Human approval"]
        write_json(source_path, source)
        report = root / "docs/results/data_audit.md"
        report.write_text(audit_markdown(summary, run_id), encoding="utf-8")
        log = root / "docs/logs" / f"B01_{run_id}.md"
        if log.exists():
            raise FileExistsError(log)
        log.write_text(f"# B01 — {run_id}\n\nStatus: PENDING HUMAN REVIEW. Command: `python -m practice_4.pipeline --stage B01 --config config/practice_4.json --run-id {run_id}`.\n\nRaw SHA256 checked before and after audit; basic ranges passed. Full results: `runs/{run_id}/audit_summary.json`. Source metadata and physical units are Human-confirmed; no B02 execution.\n", encoding="utf-8")
        paths = [source_path, report, log, run_dir / "config.json", run_dir / "environment.json", run_dir / "audit_summary.json"]
        manifest["outputs"] = [{"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p)} for p in paths]
        manifest["checks"] = [{"name": "raw_hashes_and_bootstrap", "status": "pass", "evidence": "input hashes verified before and after audit"}, {"name": "basic_physical_ranges", "status": "pass", "evidence": f"runs/{run_id}/audit_summary.json"}]
        manifest["status"] = "completed"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["limitations"].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest["finished_at_utc"] = now()
        validate_manifest(manifest)
        write_json(run_dir / "manifest.json", manifest)


def bootstrap_b02(root: Path, config: dict) -> list[dict]:
    policy = config.get("b02", {})
    if not policy.get("approval_reference") or policy.get("predecessor_run") != "20261118_system312_01":
        raise ValueError("B01 acceptance and B02 policy approval required")
    approval = (root / "docs/phase_details/phase_01.md").read_text(encoding="utf-8")
    if "B01 run `20261118_system312_01`: **Human APPROVED" not in approval or "B02 policy: **Human APPROVED" not in approval:
        raise ValueError("Approval record missing")
    required = {"docs/phase_details/phase_01.md", "runs/20261118_system312_01/manifest.json", "datasets/raw/source_manifest.json", "datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv"}
    if set(policy.get("inputs", {})) != required:
        raise ValueError("Unexpected B02 input set")
    inputs = []
    for name, expected in policy["inputs"].items():
        actual = sha256_file(root / name)
        if actual != expected:
            raise ValueError(f"B02 input hash mismatch: {name}")
        inputs.append({"path": name, "sha256": actual})
    predecessor = json.loads((root / "runs/20261118_system312_01/manifest.json").read_text(encoding="utf-8"))
    validate_manifest(predecessor)
    if predecessor["stage_id"] != "B01" or predecessor["status"] != "completed" or predecessor["run_id"] != policy["predecessor_run"]:
        raise ValueError("Invalid B01 predecessor")
    for item in predecessor["inputs"] + predecessor["outputs"]:
        if item["path"] in {"datasets/raw/source_manifest.json", "datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv"}:
            if sha256_file(root / item["path"]) != item["sha256"]:
                raise ValueError(f"B01 source/input hash drift: {item['path']}")
    expected = {x["path"] for x in predecessor["inputs"] + predecessor["outputs"]}
    if not {"datasets/raw/source_manifest.json", "datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv"}.issubset(expected):
        raise ValueError("B01 predecessor missing source provenance")
    return inputs


def contract_markdown(details: dict, run_id: str, raw_hashes: dict[str, str]) -> str:
    return f'''# Phase 1 — Canonical data contract

Trạng thái: **PENDING HUMAN REVIEW**, B02 run `{run_id}`. Human duyệt B01
`20261118_system312_01` và B02 policy ngày 2026-11-18; Phase 1 chưa được ký duyệt.

## Nguồn và lineage

Human cung cấp dataset Kaggle version 1, ngày tải 2026-11-17, CC0; upstream
được Human xác nhận là ENTSO-E Transparency Platform và OpenWeatherMap. Metadata
Kaggle và archive hash chưa kiểm chứng độc lập. Hash raw SHA256: energy
`{raw_hashes['datasets/raw/energy_dataset.csv']}`, weather
`{raw_hashes['datasets/raw/weather_features.csv']}`. Tất cả raw CSV bất biến.
Source manifest và B01 manifest được xác thực hash trước B02; run manifest B02
ghi config, inputs, outputs và hashes. Giá trị đầu vào đo được và artifacts này
không phải evidence cho model hoặc kết luận nhân quả.

## Schema và timestamp

CSV `datasets/processed/canonical_hourly.csv` có {details['canonical_rows']} rows,
được sắp tăng, unique, liên tục 1 giờ UTC từ 2014-12-31 23:00:00+00:00 tới
2018-12-31 22:00:00+00:00. Timestamps nguồn có explicit offset; parse về UTC
trước join. Source timezone/DST và units theo xác nhận Human.

| Column | Ý nghĩa | Unit / kiểu |
|---|---|---|
| `timestamp_utc` | Thời điểm quan sát theo offset UTC | ISO 8601 UTC |
| `load` | `total load actual` gốc | MW; numeric hoặc missing |
| `temp` | Mean unweighted của 5 city | K; numeric |
| `humidity` | Mean unweighted của 5 city | %; numeric |
| `wind_speed` | Mean unweighted của 5 city | m/s; numeric |
| `load_observed` | `load` có quan sát | Boolean `True`/`False` |

`load` có {details['missing_load']} missing values, CSV biểu diễn bằng empty field;
mask là False đúng tại các hàng này. Không impute, filter, clip hay scale.

## Policy và kiểm tra

City labels được strip leading/trailing whitespace trên derived copy; exact set
là Madrid, Barcelona, Valencia, Seville, Bilbao. Mỗi city-hour chỉ deduplicate
sau kiểm tra temp/humidity/wind_speed đồng nhất, fail nếu conflict; đã bỏ
{details['weather_duplicate_rows_removed']} duplicate rows khỏi bản làm việc.
Sau kiểm coverage 5 city mỗi giờ, tính mean không trọng số và 1:1 join với
{details['energy_rows']} energy rows; output {details['canonical_rows']} rows.
Source weather có {details['weather_rows']} rows.

Unweighted mean không đại diện chính xác phân bố dân số, phụ tải hay địa lý
toàn quốc; cần diễn giải như weather proxy, không suy luận quan hệ nhân quả.
Raw wind_speed max {details['raw_wind_speed_max']} m/s và temp max
{details['raw_temp_max']} K được giữ nguyên trong input và phép mean; wind_speed
133 m/s là raw extreme cần D01 training-only EDA và D02 causal anomaly policy,
không tự xác định là lỗi. Một raw extreme có thể không xuất hiện nguyên giá trị
trong proxy vì proxy là mean. Không có split, scaling, imputation hoặc clipping.
'''


def run_b02(root: Path, config_path: Path, run_id: str) -> None:
    import pandas as pd
    from practice_4.data.integration import integrate

    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = bootstrap_b02(root, config)
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    env = {"python": platform.python_version(), "platform": platform.platform(), "packages": {name: metadata.version(name) for name in ["pandas", "numpy", "pytest", "setuptools", "wheel", "jsonschema"]}}
    manifest = {"schema_version": "1", "run_id": run_id, "stage_id": "B02", "status": "running", "started_at_utc": now(), "finished_at_utc": None, "approval_refs": {"b01_acceptance_and_b02_policy": config["b02"]["approval_reference"]}, "inputs": inputs, "config_sha256": sha256_file(config_path), "environment": env, "outputs": [], "checks": [], "limitations": ["Units, source timezone, source license/version and upstream provenance are Human-confirmed; Kaggle metadata not independently verified.", "Five-city unweighted mean is a limited proxy for national weather.", "B02/Phase 1 acceptance pending Human review."]}
    (run_dir / "config.json").write_bytes(config_path.read_bytes())
    write_json(run_dir / "environment.json", env)
    try:
        canonical = root / "datasets/processed/canonical_hourly.csv"
        contract = root / "docs/results/data_contract.md"
        log = root / "docs/logs" / f"B02_{run_id}.md"
        if any(p.exists() for p in [canonical, contract, log]):
            raise FileExistsError("B02 output exists; refusing to overwrite")
        energy = pd.read_csv(root / "datasets/raw/energy_dataset.csv")
        weather = pd.read_csv(root / "datasets/raw/weather_features.csv")
        timeline = pd.date_range("2014-12-31T23:00:00Z", periods=35064, freq="h")
        data, details = integrate(energy, weather, timeline, expected_missing=36)
        bootstrap_b02(root, config)
        raw_hashes = {x["path"]: x["sha256"] for x in inputs if x["path"].startswith("datasets/raw/")}
        data.to_csv(canonical, index=False)
        contract.write_text(contract_markdown(details, run_id, raw_hashes), encoding="utf-8")
        write_json(run_dir / "integration_summary.json", details)
        log.write_text(f"# B02 — {run_id}\n\nStatus: PENDING HUMAN REVIEW. Command: `python -m practice_4.pipeline --stage B02 --config config/practice_4.json --run-id {run_id}`.\n\nB01 acceptance, approved policy, predecessor and raw/source hashes checked. {details['canonical_rows']} rows, {details['missing_load']} missing load; raw wind speed maximum {details['raw_wind_speed_max']} m/s retained in proxy input. See `integration_summary.json` and `data_contract.md`. No split, scaling, imputation or clipping.\n", encoding="utf-8")
        bootstrap_b02(root, config)
        paths = [canonical, contract, log, run_dir / "config.json", run_dir / "environment.json", run_dir / "integration_summary.json"]
        manifest["outputs"] = [{"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p)} for p in paths]
        manifest["checks"] = [{"name": "approval_and_input_hashes", "status": "pass", "evidence": "B01 source/raw hashes verified before and after integration"}, {"name": "integration_invariants", "status": "pass", "evidence": f"runs/{run_id}/integration_summary.json"}]
        manifest["status"] = "completed"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["limitations"].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest["finished_at_utc"] = now()
        validate_manifest(manifest)
        write_json(run_dir / "manifest.json", manifest)


def bootstrap_c01(root: Path, config: dict) -> list[dict]:
    policy = config.get("c01", {})
    if policy.get("schema_version") != "1" or policy.get("predecessor_run") != "20261118_system312_b02_01" or not policy.get("approval_reference") or not policy.get("b02_acceptance"):
        raise ValueError("C01 approval and B02 acceptance required")
    phase = (root / "docs/phase_details/phase_02.md").read_text(encoding="utf-8")
    if "Human APPROVED 2026-11-18 via Director review" not in phase or "Human APPROVED 2026-11-18" not in phase:
        raise ValueError("Approval record missing")
    predecessor_path = root / "runs/20261118_system312_b02_01/manifest.json"
    if sha256_file(predecessor_path) != policy.get("predecessor_manifest_sha256"):
        raise ValueError("B02 manifest hash mismatch")
    predecessor = json.loads(predecessor_path.read_text(encoding="utf-8"))
    validate_manifest(predecessor)
    if predecessor["stage_id"] != "B02" or predecessor["status"] != "completed" or predecessor["run_id"] != policy["predecessor_run"]:
        raise ValueError("Invalid B02 predecessor")
    names = {"datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv", "datasets/processed/canonical_hourly.csv"}
    entries = [x for x in predecessor["inputs"] + predecessor["outputs"] if x["path"] in names]
    if len(entries) != 3 or {x["path"] for x in entries} != names:
        raise ValueError("Missing B02 data hashes")
    for item in entries:
        if sha256_file(root / item["path"]) != item["sha256"]:
            raise ValueError(f"B02 data hash mismatch: {item['path']}")
    return [{"path": predecessor_path.relative_to(root).as_posix(), "sha256": policy["predecessor_manifest_sha256"]}, {"path": "docs/phase_details/phase_02.md", "sha256": sha256_file(root / "docs/phase_details/phase_02.md")}, *entries]


def run_c01(root: Path, config_path: Path, run_id: str) -> None:
    import pandas as pd
    from practice_4.data.splitting import partition, split_hash

    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = bootstrap_c01(root, config)
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    env = {"python": platform.python_version(), "platform": platform.platform(), "packages": {name: metadata.version(name) for name in ["pandas", "numpy", "pytest", "setuptools", "wheel", "jsonschema"]}}
    manifest = {"schema_version": "1", "run_id": run_id, "stage_id": "C01", "status": "running", "started_at_utc": now(), "finished_at_utc": None, "approval_refs": {"phase_2": config["c01"]["approval_reference"], "b02": config["c01"]["b02_acceptance"]}, "inputs": inputs, "config_sha256": sha256_file(config_path), "environment": env, "outputs": [], "checks": [], "limitations": ["C01 acceptance and C02 contract approval pending Human review.", "No windows, model inputs, or target-value analysis performed."]}
    (run_dir / "config.json").write_bytes(config_path.read_bytes())
    write_json(run_dir / "environment.json", env)
    try:
        output = root / "datasets/processed/split_manifest.json"
        log = root / "docs/logs" / f"C01_{run_id}.md"
        if output.exists() or log.exists():
            raise FileExistsError("C01 output exists; refusing to overwrite")
        canonical = next(x for x in inputs if x["path"] == "datasets/processed/canonical_hourly.csv")
        timestamps = pd.read_csv(root / canonical["path"], usecols=["timestamp_utc"])["timestamp_utc"]
        result = partition(timestamps, canonical["path"], canonical["sha256"])
        expected = [(24544, "2014-12-31T23:00:00+00:00", "2017-10-19T14:00:00+00:00"), (5259, "2017-10-19T15:00:00+00:00", "2018-05-26T17:00:00+00:00"), (5261, "2018-05-26T18:00:00+00:00", "2018-12-31T22:00:00+00:00")]
        actual = [(x["row_count"], x["start_utc"], x["end_utc"]) for x in result["splits"].values()]
        if result["total_rows"] != 35064 or actual != expected or split_hash(result) != result["split_sha256"]:
            raise ValueError("Split mismatch")
        bootstrap_c01(root, config)
        write_json(output, result)
        log.write_text(f"# C01 ? {run_id}\n\nStatus: PENDING HUMAN REVIEW. Command: `python -m practice_4.pipeline --stage C01 --config config/practice_4.json --run-id {run_id}`.\n\nB02 acceptance and data hashes verified before and after timestamp-only partition. Counts and boundaries match Phase 2 plan. Split semantic hash: `{result['split_sha256']}`. No windows or target-value inspection. See run manifest for inputs, outputs, environment and approval references.\n", encoding="utf-8")
        paths = [output, log, run_dir / "config.json", run_dir / "environment.json"]
        manifest["outputs"] = [{"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p)} for p in paths]
        manifest["checks"] = [{"name": "approval_and_data_hashes", "status": "pass", "evidence": "B02 manifest and raw/canonical hashes verified before and after partition"}, {"name": "timeline_and_split", "status": "pass", "evidence": "Sorted unique contiguous UTC hourly timeline and approved counts/boundaries verified"}, {"name": "split_self_hash", "status": "pass", "evidence": result["split_sha256"]}]
        manifest["status"] = "completed"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["limitations"].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest["finished_at_utc"] = now()
        validate_manifest(manifest)
        write_json(run_dir / "manifest.json", manifest)


def bootstrap_c02(root: Path, config: dict) -> list[dict]:
    from practice_4.data.splitting import split_hash

    policy = config.get("c02", {})
    if policy.get("schema_version") != "1" or policy.get("predecessor_run") != "20261118_system312_c01_01" or not policy.get("approval_reference"):
        raise ValueError("C01 approval required")
    phase_path = root / "docs/phase_details/phase_02.md"
    if "C01 run `20261118_system312_c01_01`" not in phase_path.read_text(encoding="utf-8") or "Human APPROVED 2026-11-18 via Director review" not in phase_path.read_text(encoding="utf-8"):
        raise ValueError("C01 acceptance missing")
    previous_path = root / "runs/20261118_system312_c01_01/manifest.json"
    if sha256_file(previous_path) != policy.get("predecessor_manifest_sha256"):
        raise ValueError("C01 manifest hash mismatch")
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    validate_manifest(previous)
    if previous["run_id"] != policy["predecessor_run"] or previous["stage_id"] != "C01" or previous["status"] != "completed":
        raise ValueError("Invalid C01 predecessor")
    names = {"datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv", "datasets/processed/canonical_hourly.csv", "datasets/processed/split_manifest.json"}
    entries = [item for item in previous["inputs"] + previous["outputs"] if item["path"] in names]
    if len(entries) != 4 or {x["path"] for x in entries} != names:
        raise ValueError("C01 data lineage missing")
    for item in entries:
        if sha256_file(root / item["path"]) != item["sha256"]:
            raise ValueError(f"C01 data hash mismatch: {item['path']}")
    split = json.loads((root / "datasets/processed/split_manifest.json").read_text(encoding="utf-8"))
    if split.get("schema_version") != "1" or split_hash(split) != split.get("split_sha256") or split.get("canonical_sha256") != next(x["sha256"] for x in entries if x["path"] == "datasets/processed/canonical_hourly.csv"):
        raise ValueError("Split semantic hash mismatch")
    return [{"path": previous_path.relative_to(root).as_posix(), "sha256": sha256_file(previous_path)}, {"path": phase_path.relative_to(root).as_posix(), "sha256": sha256_file(phase_path)}, *entries]


def run_c02(root: Path, config_path: Path, run_id: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = bootstrap_c02(root, config)
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    env = {"python": platform.python_version(), "platform": platform.platform(), "packages": {name: metadata.version(name) for name in ["pandas", "numpy", "pytest", "setuptools", "wheel", "jsonschema"]}}
    manifest = {"schema_version": "1", "run_id": run_id, "stage_id": "C02", "status": "running", "started_at_utc": now(), "finished_at_utc": None, "approval_refs": {"c01": config["c02"]["approval_reference"]}, "inputs": inputs, "config_sha256": sha256_file(config_path), "environment": env, "outputs": [], "checks": [], "limitations": ["C02 contract and Phase 2 acceptance pending Human review.", "C02 uses synthetic fixtures only; no real test origins or model fitting.", "D02 context eligibility policy and model-specific trial budgets remain pending."]}
    (run_dir / "config.json").write_bytes(config_path.read_bytes())
    write_json(run_dir / "environment.json", env)
    try:
        contract = root / "docs/results/evaluation_contract.md"
        log = root / "docs/logs" / f"C02_{run_id}.md"
        if not contract.exists() or log.exists():
            raise ValueError("Contract missing or log already exists")
        bootstrap_c02(root, config)
        log.write_text(f"# C02 - {run_id}\n\nStatus: PENDING HUMAN REVIEW. Command: `py -3.12 -m practice_4.pipeline --stage C02 --config config/practice_4.json --run-id {run_id}`.\n\nC01 approval, predecessor manifest, split byte and semantic hashes, and raw/canonical hashes verified before and after C02. Contract is pending Human review. No real test origins, tensors, predictions, EDA, or model fitting.\n", encoding="utf-8")
        paths = [contract, log, run_dir / "config.json", run_dir / "environment.json"]
        manifest["outputs"] = [{"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p)} for p in paths]
        manifest["checks"] = [{"name": "c01_acceptance_and_hashes", "status": "pass", "evidence": "C01 manifest, split semantic and file hashes and raw/canonical hashes verified before and after"}]
        manifest["status"] = "completed"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["limitations"].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest["finished_at_utc"] = now()
        validate_manifest(manifest)
        write_json(run_dir / "manifest.json", manifest)


def bootstrap_d01(root: Path, config: dict) -> list[dict]:
    from practice_4.data.splitting import split_hash

    policy = config["d01"]
    if policy.get("predecessor_run") != "20261118_system312_c02_01" or not policy.get("approval_reference"):
        raise ValueError("D01 approval missing")
    phase = (root / "docs/phase_details/phase_03.md").read_text(encoding="utf-8")
    if "Human APPROVED 2026-11-18 via Director review" not in phase or "Human resolution 2026-11-18" not in phase:
        raise ValueError("Phase 3 approval or resolution missing")
    predecessor = root / "runs/20261118_system312_c02_01/manifest.json"
    if sha256_file(predecessor) != policy["predecessor_manifest_sha256"]:
        raise ValueError("C02 manifest hash drift")
    old = json.loads(predecessor.read_text(encoding="utf-8"))
    validate_manifest(old)
    if old["run_id"] != policy["predecessor_run"] or old["stage_id"] != "C02" or old["status"] != "completed":
        raise ValueError("C02 predecessor invalid")
    if "APPROVED / COMPLETED" not in (root / "docs/results/evaluation_contract.md").read_text(encoding="utf-8"):
        raise ValueError("C02 acceptance missing")
    names = {"datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv", "datasets/processed/canonical_hourly.csv", "datasets/processed/split_manifest.json"}
    entries = [item for item in old["inputs"] if item["path"] in names]
    if len(entries) != 4 or {item["path"] for item in entries} != names:
        raise ValueError("C02 data lineage missing")
    for item in entries:
        if sha256_file(root / item["path"]) != item["sha256"]:
            raise ValueError(f"Input drift: {item['path']}")
    split = json.loads((root / "datasets/processed/split_manifest.json").read_text(encoding="utf-8"))
    if split_hash(split) != split["split_sha256"] or split["canonical_sha256"] != next(x["sha256"] for x in entries if x["path"].endswith("canonical_hourly.csv")):
        raise ValueError("Split semantic hash drift")
    expected = {"row_count":24544,"start_row":0,"end_row":24543,"start_utc":"2014-12-31T23:00:00+00:00","end_utc":"2017-10-19T14:00:00+00:00"}
    if split["splits"]["train"] != expected:
        raise ValueError("Train boundary drift")
    if policy["max_acf_lag"] != 168 or policy["pacf_method"] != "ywm" or policy["acf_contiguous_block_rule"] != "longest_observed_train_block" or policy["block_tie_break"] != "earliest_timestamp" or policy["figure_dpi"] != 120:
        raise ValueError("D01 config drift")
    return [{"path": predecessor.relative_to(root).as_posix(), "sha256": sha256_file(predecessor)}, {"path": "docs/phase_details/phase_03.md", "sha256": sha256_file(root / "docs/phase_details/phase_03.md")}, *entries]


def run_d01(root: Path, config_path: Path, run_id: str) -> None:
    from practice_4.analysis.eda import load_train, summarize
    from practice_4.visualization.plots import render
    import matplotlib

    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = bootstrap_d01(root, config)
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    env = {"python": platform.python_version(), "platform": platform.platform(), "packages": {name: metadata.version(name) for name in ["pandas", "numpy", "pytest", "jsonschema", "matplotlib", "statsmodels", "tzdata"]}, "matplotlib_backend": matplotlib.get_backend(), "font": "DejaVu Sans"}
    manifest = {"schema_version":"1","run_id":run_id,"stage_id":"D01","status":"running","started_at_utc":now(),"finished_at_utc":None,"approval_refs":{"phase_3":config["d01"]["approval_reference"]},"inputs":inputs,"config_sha256":sha256_file(config_path),"environment":env,"outputs":[],"checks":[],"limitations":["Raw city-level 133 m/s train membership unverified to preserve strict train-only isolation; Human approved proceeding.","D01 and D02 proposals pending Human review; figures staged, not promoted."]}
    (run_dir / "config.json").write_bytes(config_path.read_bytes())
    write_json(run_dir / "environment.json", env)
    try:
        split = json.loads((root / "datasets/processed/split_manifest.json").read_text(encoding="utf-8"))
        frame = load_train(root / "datasets/processed/canonical_hourly.csv", split["splits"]["train"])
        result = summarize(frame, split["splits"]["train"], 168, "ywm")
        summary = run_dir / "summary.json"
        write_json(summary, result)
        figures = render(frame, result, run_dir / "figures", 120)
        bootstrap_d01(root, config)
        paths = [summary, *figures, run_dir / "config.json", run_dir / "environment.json"]
        manifest["outputs"] = [{"path":p.relative_to(root).as_posix(),"sha256":sha256_file(p)} for p in paths]
        manifest["checks"] = [{"name":"lineage_and_unchanged_hashes","status":"pass","evidence":"C02 manifest and raw/canonical/split bytes verified before and after"},{"name":"train_only","status":"pass","evidence":"24544 records parsed; UTC timeline and train boundaries validated"}]
        manifest["status"] = "completed"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["limitations"].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest["finished_at_utc"] = now()
        validate_manifest(manifest)
        write_json(run_dir / "manifest.json", manifest)


def bootstrap_d02(root: Path, config: dict) -> list[dict]:
    from practice_4.data.splitting import split_hash

    policy = config["d02"]
    if policy != {"approval_reference": "Human: Phase 4 approved and Streaming LOCF-1 selected, 2026-11-18 via Director review", "predecessor_run": "20261118_system312_d01_01", "locf_max_gap": 1, "percentiles": [0.5, 99.5], "percentile_method": "linear", "csv_na_rep": "", "csv_float_format": "%.17g", "var_block": {"start_utc": "2016-09-28T08:00:00+00:00", "end_utc": "2017-10-19T14:00:00+00:00", "rows": 9271, "earlier_observed_excluded": 15241}}:
        raise ValueError("D02 policy drift")
    phase = root / "docs/phase_details/phase_04.md"
    contents = phase.read_text(encoding="utf-8")
    if "Human APPROVED 2026-11-18 via Director review" not in contents or "Streaming LOCF-1" not in contents or "D01, findings and Phase 3: **Human APPROVED / COMPLETED" not in contents:
        raise ValueError("Phase 4 approval or D01 acceptance missing")
    previous = root / "runs/20261118_system312_d01_01/manifest.json"
    if sha256_file(previous) != "c545170a0fad75b27a66f7fa9eceef0f60e5ef106f6fb9d640e29d109fe12062":
        raise ValueError("D01 manifest hash drift")
    predecessor = json.loads(previous.read_text(encoding="utf-8"))
    validate_manifest(predecessor)
    if predecessor["stage_id"] != "D01" or predecessor["status"] != "completed" or predecessor["run_id"] != policy["predecessor_run"]:
        raise ValueError("Invalid D01 predecessor")
    names = {"datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv", "datasets/processed/canonical_hourly.csv", "datasets/processed/split_manifest.json"}
    entries = [item for item in predecessor["inputs"] if item["path"] in names]
    if len(entries) != 4 or {item["path"] for item in entries} != names:
        raise ValueError("Missing D01 data lineage")
    for item in entries:
        if sha256_file(root / item["path"]) != item["sha256"]:
            raise ValueError(f"Input hash drift: {item['path']}")
    split = json.loads((root / "datasets/processed/split_manifest.json").read_text(encoding="utf-8"))
    if split_hash(split) != split["split_sha256"] or split["canonical_sha256"] != next(x["sha256"] for x in entries if x["path"].endswith("canonical_hourly.csv")):
        raise ValueError("Split lineage mismatch")
    train, val = split["splits"]["train"], split["splits"]["validation"]
    if (train["start_row"], train["end_row"], train["row_count"], val["start_row"], val["end_row"], val["row_count"]) != (0, 24543, 24544, 24544, 29802, 5259):
        raise ValueError("Split boundary mismatch")
    return [{"path": previous.relative_to(root).as_posix(), "sha256": sha256_file(previous)}, {"path": phase.relative_to(root).as_posix(), "sha256": sha256_file(phase)}, *entries]


def run_d02(root: Path, config_path: Path, run_id: str) -> None:
    import itertools
    import numpy as np
    import pandas as pd
    from practice_4.data.preprocessing import CausalState, FEATURES, VARIABLES, fit_state, inverse_load, load_prefix, transform, verify_var_block

    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = bootstrap_d02(root, config)
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    artifact_dir = run_dir / "artifacts"
    artifact_dir.mkdir()
    env = {"python": platform.python_version(), "platform": platform.platform(), "packages": {name: metadata.version(name) for name in ["pandas", "numpy", "scikit-learn", "pytest", "jsonschema"]}}
    manifest = {"schema_version": "1", "run_id": run_id, "stage_id": "D02", "status": "running", "started_at_utc": now(), "finished_at_utc": None, "approval_refs": {"phase_4": config["d02"]["approval_reference"]}, "inputs": inputs, "config_sha256": sha256_file(config_path), "environment": env, "outputs": [], "checks": [], "limitations": ["D02 gate and Phase 4 completion pending Human review.", "No test records parsed; full input files hashed as bytes for integrity.", "Full absolute inverse error guarantee is limited by float64 precision; verified for observed train and validation levels.", "VAR block omits earlier observations and may not represent all training regimes."]}
    (run_dir / "config.json").write_bytes(config_path.read_bytes())
    write_json(run_dir / "environment.json", env)
    try:
        target = root / "datasets/processed/prepared_hourly.csv"
        audit = root / "docs/results/preprocessing_audit.md"
        log = root / "docs/logs" / f"D02_{run_id}.md"
        if any(p.exists() for p in [target, audit, log]):
            raise FileExistsError("D02 output collision")
        split = json.loads((root / "datasets/processed/split_manifest.json").read_text(encoding="utf-8"))
        train, val = split["splits"]["train"], split["splits"]["validation"]
        frame = load_prefix(root / "datasets/processed/canonical_hourly.csv", 29803, train["start_utc"], val["end_utc"])
        if frame.timestamp_utc.iloc[24543].isoformat() != train["end_utc"] or frame.timestamp_utc.iloc[24544].isoformat() != val["start_utc"]:
            raise ValueError("Split timestamp mismatch")
        verify_var_block(frame, config["d02"]["var_block"])
        provenance = {item["path"]: item["sha256"] for item in inputs if item["path"].startswith("datasets/")}
        provenance["split_semantic_sha256"] = split["split_sha256"]
        fitted = fit_state(frame, 24544, provenance)
        scaler_path = artifact_dir / "scaler.json"
        write_json(scaler_path, fitted)
        reloaded = json.loads(scaler_path.read_text(encoding="utf-8"))
        if fitted != reloaded:
            raise ValueError("Scaler reload mismatch")
        stream_state = CausalState()
        prepared = pd.concat([transform(frame.iloc[:24544], reloaded, stream_state), transform(frame.iloc[24544:], reloaded, stream_state)], ignore_index=True)
        for name in ["load", "load_observed", "temp", "humidity", "wind_speed"]:
            if not prepared[name].equals(frame[name]):
                raise ValueError(f"Source data mutation: {name}")
        delta = np.abs(inverse_load(prepared.load_input_scaled, reloaded) - prepared.load_input)
        inverse_error = float(delta.max())
        if not np.isfinite(inverse_error) or inverse_error > 1e-9:
            raise ValueError(f"Inverse tolerance failed: {inverse_error}")
        staged = artifact_dir / "prepared_hourly.csv"
        prepared.to_csv(staged, index=False, na_rep=config["d02"]["csv_na_rep"], float_format=config["d02"]["csv_float_format"])
        gap_lengths = [sum(1 for _ in g) for missing, g in itertools.groupby(~frame.load_observed) if missing]
        columns = [{"name": name, "dtype": str(prepared[name].dtype)} for name in prepared.columns]
        flag_columns = [x for x in prepared.columns if x.endswith("_invalid") or x.endswith("_extreme")]
        counts = {}
        for name, part in [("train", prepared.iloc[:24544]), ("validation", prepared.iloc[24544:])]:
            counts[name] = {"rows": len(part), "missing_truth": int(part.load.isna().sum()), "missing_working_load": int(part.load_input.isna().sum()), "locf_filled": int((part.load.isna() & part.load_input.notna()).sum()), "flags": {col: int(part[col].sum()) for col in flag_columns}}
        summary = {"columns": columns, "counts": counts, "gap_lengths": gap_lengths, "inverse_max_error_mw": inverse_error, "scaler_sha256": sha256_file(scaler_path), "prepared_sha256": sha256_file(staged), "input_hashes": provenance, "final_stream_state": {"last_load": stream_state.last_load, "missing_run": stream_state.missing_run, "last_timestamp": stream_state.last_timestamp}}
        write_json(artifact_dir / "summary.json", summary)
        report = "# D02 ? Causal preprocessing audit\n\n" + f"Status: **PENDING HUMAN REVIEW**. Run `{run_id}`. Phase 4 specification approved 2026-11-18; D02 and Phase 4 completion are not approved.\n\n"
        report += "## Method and limits\n\nTrain rows 0?24543; validation rows 24544?29802. Only these 29,803 records are parsed, in UTC chronological order. Full input files were hashed as bytes only. Streaming LOCF-1 fills the first missing hour from the preceding observation and leaves subsequent consecutive missing hours and leading missing hours empty; state crosses the split. Raw truth and mask remain unchanged. No clipping, label imputation, windows or models. Remaining NaN context will be excluded after missing-truth exclusion by E02; no real origin counts are computed here.\n\n"
        report += "Physical flags use raw load and weather; percentile flags use available raw train observations for each variable and strict comparisons. Percentiles: 0.5 and 99.5, NumPy `linear` interpolation. Flags do not establish errors. Unexpected invalid or missing weather stops processing. `StandardScaler` is fit on complete finite working-feature train rows; population standard deviation, fixed transform, sklearn zero/near-constant scale behavior.\n\n"
        report += f"UTF-8 CSV, empty field means missing, numeric float format `%.17g`; timestamps ISO-8601 UTC, flags and mask boolean. Scaler SHA256 `{summary['scaler_sha256']}`; prepared SHA256 `{summary['prepared_sha256']}`. Reloaded inverse maximum error on finite prepared load levels: `{inverse_error}` MW.\n\n"
        report += "## Schema and measured results\n\n```json\n" + json.dumps({"schema": columns, "counts": counts, "missing_gap_lengths": gap_lengths, "scaler": reloaded, "final_stream_state": summary["final_stream_state"]}, indent=2, ensure_ascii=False) + "\n```\n\n"
        report += "## VAR domain and limitations\n\nObserved contiguous train block 2016-09-28T08:00:00+00:00 through 2017-10-19T14:00:00+00:00 has 9,271 hours; 15,241 earlier observed train hours are excluded. The block may not represent the full training history. Extreme values are retained and can affect modeling. Five-city weather is a limited proxy. Source 133 m/s raw wind membership remains unverified. Float64 cannot guarantee 1e-9 MW absolute roundtrip for arbitrarily large values; the actual finite train/validation levels were checked. System Python environment, not a clean-environment reproduction.\n"
        staged_audit = artifact_dir / "preprocessing_audit.md"
        staged_audit.write_text(report, encoding="utf-8")
        if bootstrap_d02(root, config) != inputs:
            raise ValueError("Input drift during D02")
        target.write_bytes(staged.read_bytes())
        audit.write_bytes(staged_audit.read_bytes())
        log.write_text(f"# D02 ? {run_id}\n\nStatus: PENDING HUMAN REVIEW.\n\nCommands: `py -3.12 -m pytest tests/test_preprocessing.py`; `py -3.12 -m pytest tests/test_splitting.py tests/test_walk_forward.py tests/test_metrics.py`; `py -3.12 -m practice_4.pipeline --stage D02 --config config/practice_4.json --run-id {run_id}`. See final status for test results.\n\nInitial synthetic test failed for artificial 100,000,000 MW level: float64 roundtrip error 1.4901161193847656e-08 MW. Fixture updated to representative 50,000 MW; limitation is recorded in audit. No test record was parsed. Raw, canonical and split bytes checked against D01 before and after processing.\n", encoding="utf-8")
        paths = [target, audit, log, scaler_path, artifact_dir / "summary.json", staged, staged_audit, run_dir / "config.json", run_dir / "environment.json"]
        manifest["outputs"] = [{"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p)} for p in paths]
        manifest["checks"] = [{"name": "lineage_and_hashes", "status": "pass", "evidence": "D01 data hashes verified before and after processing"}, {"name": "bounded_prefix", "status": "pass", "evidence": "29803 records, train and validation only; chronological split endpoints checked"}, {"name": "state_and_inverse", "status": "pass", "evidence": f"Reloaded scaler; max inverse error {inverse_error} MW; VAR block validated"}]
        manifest["status"] = "completed"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["limitations"].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest["finished_at_utc"] = now()
        validate_manifest(manifest)
        write_json(run_dir / "manifest.json", manifest)


def _e01_inputs(root: Path, policy: dict) -> tuple[list[dict], dict, dict]:
    from practice_4.data.features import PREFIX_ROWS, TRAIN_ROWS
    from practice_4.data.preprocessing import FEATURES
    from practice_4.data.splitting import split_hash

    phase_4 = "docs/phase_details/phase_04.md"
    phase_5 = "docs/phase_details/phase_05.md"
    run_id = "20261118_system312_d02_01"
    acceptance = (
        f"D02 run `{run_id}`, prepared data, preprocessing audit and Phase 4 completion: "
        "**Human APPROVED / COMPLETED, 2026-11-18 via Director review**."
    )
    approval = "Human: Phase 5 specification and before-process plan APPROVED 2026-11-18 via Director review; E01 only"
    phase_5_record = (root / phase_5).read_text(encoding="utf-8")
    if (
        policy["approval_reference"] != approval
        or policy["predecessor_run"] != run_id
        or acceptance not in (root / phase_4).read_text(encoding="utf-8")
        or "Phase 5 specification and before-process plan: **Human APPROVED 2026-11-18 via Director review**." not in phase_5_record
        or "Stage E01 only: **Human authorized execution 2026-11-18 via Director review**." not in phase_5_record
    ):
        raise ValueError("Phase 5/E01 approval or D02 acceptance missing")

    previous_path = f"runs/{run_id}/manifest.json"
    predecessor_hash = sha256_file(root / previous_path)
    if predecessor_hash != policy["predecessor_manifest_sha256"]:
        raise ValueError("D02 manifest hash drift")
    previous = json.loads((root / previous_path).read_text(encoding="utf-8"))
    validate_manifest(previous)
    if (previous["stage_id"], previous["run_id"], previous["status"]) != ("D02", run_id, "completed"):
        raise ValueError("Invalid D02 predecessor")

    split_path = "datasets/processed/split_manifest.json"
    canonical_path = "datasets/processed/canonical_hourly.csv"
    prepared_path = "datasets/processed/prepared_hourly.csv"
    scaler_path = f"runs/{run_id}/artifacts/scaler.json"
    summary_path = f"runs/{run_id}/artifacts/summary.json"
    immutable_inputs = (
        "datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv", canonical_path, split_path,
    )
    data_entries = []
    for records, paths in (
        (previous["inputs"], immutable_inputs),
        (previous["outputs"], (prepared_path, scaler_path, summary_path)),
    ):
        for path in paths:
            matches = [entry for entry in records if entry["path"] == path]
            if len(matches) != 1 or sha256_file(root / path) != matches[0]["sha256"]:
                raise ValueError(f"Missing or changed D02 lineage: {path}")
            data_entries.append(matches[0])

    hashes = {entry["path"]: entry["sha256"] for entry in data_entries}
    split = json.loads((root / split_path).read_text(encoding="utf-8"))
    scaler = json.loads((root / scaler_path).read_text(encoding="utf-8"))
    summary = json.loads((root / summary_path).read_text(encoding="utf-8"))
    semantic_hash = split_hash(split)
    provenance = {path: hashes[path] for path in immutable_inputs}
    provenance["split_semantic_sha256"] = semantic_hash
    if (
        split["split_sha256"] != semantic_hash
        or split["canonical_path"] != canonical_path
        or split["canonical_sha256"] != hashes[canonical_path]
        or scaler["provenance"] != provenance
        or scaler["feature_order"] != FEATURES
        or (scaler["fit_start_row"], scaler["fit_end_row"]) != (0, TRAIN_ROWS - 1)
        or summary["input_hashes"] != provenance
        or summary["scaler_sha256"] != hashes[scaler_path]
        or summary["prepared_sha256"] != hashes[prepared_path]
    ):
        raise ValueError("D02 split or scaler provenance mismatch")
    for name, start, stop in (("train", 0, TRAIN_ROWS), ("validation", TRAIN_ROWS, PREFIX_ROWS)):
        part = split["splits"][name]
        if (part["start_row"], part["end_row"], part["row_count"]) != (start, stop - 1, stop - start):
            raise ValueError(f"E01 split boundary mismatch: {name}")

    inputs = [
        {"path": previous_path, "sha256": predecessor_hash},
        *({"path": path, "sha256": sha256_file(root / path)} for path in (phase_4, phase_5)),
        *data_entries,
    ]
    return inputs, split["splits"], summary["counts"]


def _feature_dictionary(run_id: str, var_shape: tuple[int, int]) -> str:
    import numpy as np
    from practice_4.data.features import (
        FLAT_FEATURE_NAMES, SCALED_COLUMNS, SEQUENCE_HOURS, VAR_EARLIER_OBSERVED,
        VAR_END_ROW, VAR_END_UTC, VAR_START_ROW, VAR_START_UTC, XGB_FEATURE_NAMES,
        classify_origin, feature_views,
    )

    ramp = np.arange(26, dtype=np.float64)[:, None] + np.array([0, 100, 200, 300])
    raw_load = ramp[:, 0].copy()
    raw_load[25] = 12345.0
    origin = classify_origin(ramp, 25, raw_load[25], True)
    sequence, flat, xgb = feature_views(ramp, [origin.target_row])
    expected_sequence = np.arange(1, 25)[:, None] + np.array([0, 100, 200, 300])
    if not origin.eligible or origin.y_true_mw != 12345.0:
        raise ValueError("E01 ramp label mismatch")
    np.testing.assert_array_equal(sequence[0], expected_sequence)
    np.testing.assert_array_equal(flat[0], expected_sequence.ravel())
    np.testing.assert_array_equal(xgb[0, :96], flat[0])
    np.testing.assert_allclose(xgb[0, 96:], [21.5, np.sqrt(575 / 12), 24], rtol=1e-14, atol=0)

    lines = [
        "# E01 Feature Dictionary", "",
        f"Run `{run_id}` · **PENDING HUMAN REVIEW**", "",
        "For target row `k`, origin `t` is row `k-1`. The common context is rows `k-25..k-1` inclusive.",
        "Each input is available at the end of its source hour. Target-hour weather and later observations are outside the context.",
        "The fixed D02 working features and their statistics are dimensionless. The label is the observed raw `load` at `t+1` in MW.", "",
        "LSTM uses a float64 array of shape `(N, 24, 4)`. Its time axis runs oldest to newest from `t-23` through `t`.",
        f"Its variable axis is {', '.join(f'`{name}`' for name in SCALED_COLUMNS)}.",
        "The flat view reshapes these axes in time-major order to `(N, 96)`. XGBoost appends three derived columns for `(N, 99)`.", "",
        "| 0-based column | Exact name | D02 source | Origin-relative hours | Target-relative hours | Definition |",
        "|---:|---|---|---|---|---|",
    ]
    for column, feature in enumerate(FLAT_FEATURE_NAMES):
        hour, variable = divmod(column, len(SCALED_COLUMNS))
        offset = hour - (SEQUENCE_HOURS - 1)
        source = SCALED_COLUMNS[variable]
        lines.append(f"| {column} | `{feature}` | `{source}` | {offset} | {offset - 1} | Scaled level |")
    derived = (
        ("-5..0", "-6..-1", "Arithmetic mean of six hourly levels"),
        ("-23..0", "-24..-1", "Population standard deviation of 24 hourly levels, `ddof=0`"),
        ("-24, 0", "-25, -1", "Level at `t` minus level at `t-24`"),
    )
    for column, (feature, definition) in enumerate(zip(XGB_FEATURE_NAMES[96:], derived), start=96):
        offset, target_offset, formula = definition
        lines.append(f"| {column} | `{feature}` | `{SCALED_COLUMNS[0]}` | {offset} | {target_offset} | {formula} |")
    lines.extend([
        "", "## Ramp hand check", "",
        "Synthetic row `i` contains `[i, 100+i, 200+i, 300+i]`. Origin 24 uses context 0–24 and target 25.",
        f"- Sequence and flat lag blocks start at `{sequence[0, 0].astype(int).tolist()}` and end at `{sequence[0, -1].astype(int).tolist()}`.",
        "- `mean6h = (19 + 20 + 21 + 22 + 23 + 24) / 6 = 21.5`.",
        f"- `std24h = sqrt(575/12) = {xgb[0, 97]:.15g}` from the population variance of integers 1–24.",
        "- `trend24h = 24 - 0 = 24`.",
        f"- The label is row 25's synthetic raw value, `{origin.y_true_mw:g} MW`.",
        "", "## Candidate eligibility", "",
        "Rows 0–24 are warm-up. Candidate split follows the target timestamp. The first validation target uses the last training hour as its origin.",
        "A missing raw label takes precedence as `missing_truth`. An observed target with a nonfinite value anywhere in its 25 × 4 scaled context is `invalid_context`.",
        "A finite observed truth and finite context are eligible. A raw truth and mask mismatch raises a contract error. Physical and statistical flags leave eligibility unchanged.",
        "", "## VAR training block", "",
        f"E01 verified a contiguous float64 matrix of shape `{var_shape}`, using the same four scaled columns.",
        f"Prepared rows {VAR_START_ROW:,}–{VAR_END_ROW:,} span `{VAR_START_UTC}` through `{VAR_END_UTC}`, inclusive.",
        "All block hours are observed, have equal raw and working load, and have finite scaled levels.",
        f"The fixed block excludes {VAR_EARLIER_OBSERVED:,} earlier observed train hours and may underrepresent earlier regimes.",
        "The block has its own row axis. F02 owns VAR fitting and adequacy checks.",
        "",
    ])
    return "\n".join(lines)


def run_e01(root: Path, config_path: Path, run_id: str) -> None:
    from practice_4.data.features import extract_var_train_levels, load_prepared_prefix

    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    policy = config["e01"]
    inputs, splits, counts = _e01_inputs(root, policy)
    dictionary = root / "docs/results/feature_dictionary.md"
    log = root / "docs/logs" / f"E01_{run_id}.md"
    if dictionary.exists() or log.exists():
        raise FileExistsError("E01 output collision")
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    packages = ("pandas", "numpy", "scikit-learn", "pytest", "jsonschema")
    env = {
        "python": platform.python_version(), "platform": platform.platform(),
        "packages": {name: metadata.version(name) for name in packages},
    }
    manifest = {
        "schema_version": "1", "run_id": run_id, "stage_id": "E01", "status": "running",
        "started_at_utc": now(), "finished_at_utc": None,
        "approval_refs": {"phase_5": policy["approval_reference"], "d02": policy["predecessor_run"]},
        "inputs": inputs, "config_sha256": sha256_file(config_path), "environment": env,
        "outputs": [], "checks": [],
        "limitations": [
            "E01 gate acceptance and E02 execution approval remain pending Human review.",
            "Raw and canonical CSVs were hashed as opaque bytes. Data parsing was restricted to D02 train and validation.",
            "The fixed VAR block omits earlier observed train hours and may underrepresent earlier regimes.",
        ],
    }
    try:
        prepared = load_prepared_prefix(root / "datasets/processed/prepared_hourly.csv", splits, counts)
        var = extract_var_train_levels(prepared)
        report = _feature_dictionary(run_id, var.shape)
        after, _, _ = _e01_inputs(root, policy)
        if inputs != after:
            raise ValueError("Input drift during E01")

        snapshot = run_dir / "config.json"
        environment = run_dir / "environment.json"
        snapshot.write_bytes(config_path.read_bytes())
        write_json(environment, env)
        if sha256_file(snapshot) != manifest["config_sha256"]:
            raise ValueError("Config drift during E01")
        manifest["checks"] = [
            {"name": "lineage_and_hashes", "status": "pass", "evidence": "D02 acceptance, manifest SHA256 and split file/semantic lineage verified. Raw, canonical, split, prepared and scaler digests match D02 before and after feature checks."},
            {"name": "prepared_prefix", "status": "pass", "evidence": f"{len(prepared)} UTC hours with the accepted D02 schema, split endpoints, masks and counts."},
            {"name": "ramp", "status": "pass", "evidence": "Synthetic sequence and flat view matched the hand calculation, including all three derived features and row 25 raw truth."},
            {"name": "var", "status": "pass", "evidence": f"{var.shape} finite scaled levels, exact UTC hourly endpoints, observed raw load and working/raw equality."},
        ]
        log_text = "\n".join([
            f"# E01 {run_id}", "",
            "Status **PENDING HUMAN REVIEW**.", "",
            f"Command `py -3.12 -m practice_4.pipeline --stage E01 --config {config_path.relative_to(root).as_posix()} --run-id {run_id}` completed successfully.", "",
            *(f"- {check['evidence']}" for check in manifest["checks"]),
            "", "The [current status](../status/current_status.md) records the separate pytest commands and outcomes.",
            f"See the [run manifest](../../runs/{run_id}/manifest.json) for input and output hashes.",
            "The run publishes the feature dictionary and run evidence. E02 artifacts remain gated.", "",
        ])
        with dictionary.open("x", encoding="utf-8") as stream:
            stream.write(report)
        with log.open("x", encoding="utf-8") as stream:
            stream.write(log_text)
        manifest["outputs"] = [
            {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
            for path in (dictionary, log, snapshot, environment)
        ]
        manifest["status"] = "completed"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["limitations"].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest["finished_at_utc"] = now()
        validate_manifest(manifest)
        write_json(run_dir / "manifest.json", manifest)


def _e02_inputs(root: Path, config: dict) -> tuple[list[dict], dict, dict]:
    policy = config["e02"]
    acceptance = "Human APPROVED / COMPLETED, 2026-11-18 via Director review"
    run_id = "20261118_system312_e01_01"
    phase_record = (root / "docs/phase_details/phase_05.md").read_text(encoding="utf-8")
    dictionary = "docs/results/feature_dictionary.md"
    if (
        policy["predecessor_run"] != run_id
        or policy["approval_reference"]
        != "Human: E01 run and feature dictionary APPROVED 2026-11-18 via Director review. E02 authorized."
        or f"E01 run `{run_id}` and the feature dictionary: **{acceptance}**. Stage E02 execution authorized."
        not in phase_record
        or f"Run `{run_id}` · **{acceptance}**" not in (root / dictionary).read_text(encoding="utf-8")
    ):
        raise ValueError("E01 acceptance or E02 authorization missing")

    previous_path = f"runs/{run_id}/manifest.json"
    previous_hash = sha256_file(root / previous_path)
    dictionary_hash = sha256_file(root / dictionary)
    if previous_hash != policy["predecessor_manifest_sha256"] or dictionary_hash != policy["accepted_dictionary_sha256"]:
        raise ValueError("E01 manifest or accepted dictionary hash drift")
    previous = json.loads((root / previous_path).read_text(encoding="utf-8"))
    validate_manifest(previous)
    if (previous["stage_id"], previous["run_id"], previous["status"]) != ("E01", run_id, "completed"):
        raise ValueError("Invalid E01 predecessor")

    inputs, splits, counts = _e01_inputs(root, config["e01"])
    phase_path = "docs/phase_details/phase_05.md"
    historical = {entry["path"]: entry["sha256"] for entry in previous["inputs"]}
    if any(entry["sha256"] != historical.get(entry["path"]) for entry in inputs if entry["path"] != phase_path):
        raise ValueError("D02 input lineage differs from the accepted E01 run")
    return [
        {"path": previous_path, "sha256": previous_hash},
        {"path": dictionary, "sha256": dictionary_hash},
        *inputs,
    ], splits, counts


def _e02_audit(
    run_id: str, command: str, counts: dict, shapes: dict, split: dict,
    inputs: list[dict], outputs: list[dict],
) -> str:
    from practice_4.data.features import (
        CONTEXT_HOURS, ORIGIN_COLUMNS, SCALED_COLUMNS, VAR_EARLIER_OBSERVED, VAR_END_ROW,
        VAR_END_UTC, VAR_START_ROW, VAR_START_UTC, XGB_FEATURE_NAMES,
    )

    total_rows = split["total_rows"]
    splits = split["splits"]
    candidate_count = sum(values["n_considered"] for values in counts.values())
    n = sum(values["n_eligible"] for values in counts.values())
    train, validation = splits["train"], splits["validation"]
    lines = [
        "# E02 Alignment Audit", "",
        f"Run `{run_id}` · **PENDING HUMAN REVIEW**", "",
        f"`{command}` completed successfully. The [execution log](../logs/E02_{run_id}.md) links the separate pytest evidence.", "",
        "## Scope and conservation", "",
        f"The validated D02 train/validation prefix contains {train['row_count'] + validation['row_count']:,} UTC rows.",
        f"Warm-up excludes target rows 0–{CONTEXT_HOURS - 1} ({CONTEXT_HOURS} rows). The candidate manifest contains {candidate_count:,} rows and the supervised arrays contain {n:,} eligible samples.",
        "Raw share below uses the full canonical row count from split metadata as the denominator. Dataset records were parsed only from the prepared prefix.",
        "", "| Target split | Raw rows | Raw share | Start UTC | End UTC | Candidates | Missing truth | Invalid context | Eligible |",
        "|---|---:|---:|---|---|---:|---:|---:|---:|",
    ]
    for name, values in counts.items():
        part = splits[name]
        raw_rows = part["row_count"]
        lines.append(
            f"| {name} | {raw_rows:,} | {raw_rows / total_rows:.4%} | {part['start_utc']} | {part['end_utc']} | "
            f"{values['n_considered']:,} | {values['n_missing_excluded']:,} | {values['n_input_excluded']:,} | {values['n_eligible']:,} |"
        )
    lines.extend([
        "", "Each split passed candidate = missing truth + invalid context + eligible.",
        f"The first validation target is row {validation['start_row']:,} at `{validation['start_utc']}`. Its origin is the last train row {train['end_row']:,} at `{train['end_utc']}`.",
        "Every target uses exactly the previous 25 hours for eligibility. Each lag and statistic ends at or before the origin. Missing truth takes precedence over nonfinite context.",
        "", "## RV2 schema v1 round-trip checks", "",
        "UTF-8 origin CSV used the exact ordered header below. The reload checked all candidate IDs, timestamps, splits, mask and context flags, exclusion reasons, raw values and consecutive eligible sample indices against the prepared source.", "",
        "```text", ",".join(ORIGIN_COLUMNS), "```", "",
        "The NPZ ZIP member list, keys, dtypes and shapes passed validation with `allow_pickle=False`. Each eligible sample matched the source by target row, including raw MW truth, 24-hour sequence, time-major flat view and all three XGBoost statistics. Floating-point arrays were finite.",
        "", "| NPZ key | dtype | Shape |", "|---|---|---|",
    ])
    for key, (shape, dtype) in shapes.items():
        lines.append(f"| `{key}` | `{dtype}` | `{shape}` |")
    lines.extend([
        "", f"The LSTM and VAR variable axes use {', '.join(f'`{name}`' for name in SCALED_COLUMNS)} in that order.",
        f"The XGBoost order runs from `{XGB_FEATURE_NAMES[0]}` through `{XGB_FEATURE_NAMES[95]}`, followed by `mean6h`, `std24h` and `trend24h`. See the [feature dictionary](feature_dictionary.md) for each column.",
        "", "## VAR block", "",
        f"Rows {VAR_START_ROW:,}–{VAR_END_ROW:,}, from `{VAR_START_UTC}` through `{VAR_END_UTC}` inclusive, were checked for hourly continuity, observed raw load, working/raw equality and finite scaled levels.",
        f"The separate VAR axis excludes {VAR_EARLIER_OBSERVED:,} earlier observed hours. The retained block may underrepresent earlier training regimes. Model fitting has its own gate.",
        "", "## SHA256 provenance", "",
        f"Split semantic SHA256 `{split['split_sha256']}` matched D02 scaler lineage. Protected inputs matched D02 before and after staging.",
        "Raw and canonical files were hashed as opaque bytes. The E01 manifest preserves the original Phase 5 and dictionary digests from before the approval edits.",
        "", "| Role | Path | SHA256 |", "|---|---|---|",
    ])
    for role, entries in (("Input", inputs), ("Output", outputs)):
        for entry in entries:
            lines.append(f"| {role} | `{entry['path']}` | `{entry['sha256']}` |")
    lines.extend([
        "", f"The [run manifest](../../runs/{run_id}/manifest.json) records the SHA256 of this audit and its staged copy. The final manifest digest is recorded in [current status](../status/current_status.md).",
        "", "E02 gate acceptance, Phase 5 RV2 schema acceptance and Phase 5 completion sign-off are **PENDING HUMAN REVIEW**.", "",
    ])
    return "\n".join(lines)


def run_e02(root: Path, config_path: Path, run_id: str) -> None:
    from shutil import copyfileobj

    from practice_4.data.features import align_origins, load_prepared_prefix, stage_aligned_inputs, validate_aligned_inputs

    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid run ID")
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    policy = config["e02"]
    inputs, splits, counts = _e02_inputs(root, config)
    split_path = root / "datasets/processed/split_manifest.json"
    split = json.loads(split_path.read_text(encoding="utf-8"))
    run_dir = root / "runs" / run_id
    artifacts = run_dir / "artifacts"
    targets = [
        root / "datasets/processed/origin_manifest.csv",
        root / "datasets/processed/model_inputs.npz",
        root / "docs/results/alignment_audit.md",
    ]
    log = root / "docs/logs" / f"E02_{run_id}.md"
    if any(path.exists() for path in (*targets, log)):
        raise FileExistsError("E02 output collision")
    run_dir.mkdir(parents=True, exist_ok=False)
    artifacts.mkdir()

    packages = ("pandas", "numpy", "scikit-learn", "pytest", "jsonschema")
    env = {
        "python": platform.python_version(), "platform": platform.platform(),
        "packages": {name: metadata.version(name) for name in packages},
    }
    manifest = {
        "schema_version": "1", "run_id": run_id, "stage_id": "E02", "status": "running",
        "started_at_utc": now(), "finished_at_utc": None,
        "approval_refs": {"e02": policy["approval_reference"], "e01": policy["predecessor_run"]},
        "inputs": inputs, "config_sha256": sha256_file(config_path), "environment": env,
        "outputs": [], "checks": [],
        "limitations": [
            "E02 gate acceptance, Phase 5 RV2 schema acceptance and Phase 5 sign-off are pending Human review.",
            "Raw and canonical CSVs were hashed as opaque bytes. Parsed records were restricted to the D02 train/validation prefix.",
            "The fixed VAR block omits earlier observed hours and may underrepresent earlier regimes.",
        ],
    }

    def entry(path: Path, digest: str | None = None) -> dict:
        return {"path": path.relative_to(root).as_posix(), "sha256": digest or sha256_file(path)}

    staged_csv, staged_npz, staged_audit = (artifacts / path.name for path in targets)
    snapshot, environment = run_dir / "config.json", run_dir / "environment.json"
    command = f"py -3.12 -m practice_4.pipeline --stage E02 --config {config_path.relative_to(root).as_posix()} --run-id {run_id}"
    published = []
    try:
        prepared = load_prepared_prefix(root / "datasets/processed/prepared_hourly.csv", splits, counts)
        origins, alignment_counts = align_origins(prepared)
        stage_aligned_inputs(prepared, origins, staged_csv, staged_npz)
        shapes = validate_aligned_inputs(prepared, staged_csv, staged_npz)
        if _e02_inputs(root, config)[0] != inputs or config_path.read_bytes() != config_bytes:
            raise ValueError("Input or config drift during E02")

        manifest["checks"] = [
            {"name": "lineage", "status": "pass", "evidence": "Accepted E01 manifest and dictionary verified. D02 raw, canonical, split, prepared and scaler hashes match before and after staging."},
            {"name": "candidate_conservation", "status": "pass", "evidence": alignment_counts},
            {"name": "roundtrip", "status": "pass", "evidence": f"All {len(origins)} CSV candidates and all eight NPZ arrays reloaded and matched the prepared D02 source. VAR continuity and working/raw equality verified."},
        ]
        snapshot.write_bytes(config_bytes)
        write_json(environment, env)
        if sha256_file(snapshot) != manifest["config_sha256"]:
            raise ValueError("E02 config snapshot hash mismatch")
        log_text = "\n".join([
            f"# E02 {run_id}", "", "Status **PENDING HUMAN REVIEW**.", "",
            f"`{command}` completed successfully.", "",
            f"Verified {len(origins):,} origin records and {shapes['target_row'][0][0]:,} eligible samples. The validated CSV, NPZ and audit were staged before publication.",
            "", f"See the [alignment audit](../results/alignment_audit.md) and [manifest](../../runs/{run_id}/manifest.json). The [current status](../status/current_status.md) records the separate pytest results.", "",
        ])
        log_bytes = log_text.encode("utf-8")
        log_entry = entry(log, hashlib.sha256(log_bytes).hexdigest())
        data_entries = [entry(staged_csv), entry(staged_npz)]
        output_records = [
            *data_entries,
            *(entry(target, source["sha256"]) for target, source in zip(targets[:2], data_entries)),
            entry(snapshot), entry(environment), log_entry,
        ]
        staged_audit.write_text(
            _e02_audit(run_id, command, alignment_counts, shapes, split, inputs, output_records),
            encoding="utf-8",
        )

        for staged, target in zip((staged_csv, staged_npz, staged_audit), targets):
            with staged.open("rb") as source, target.open("xb") as destination:
                published.append(target)
                copyfileobj(source, destination)
            if sha256_file(staged) != sha256_file(target):
                raise ValueError(f"E02 promotion hash mismatch: {target.name}")
        with log.open("xb") as stream:
            published.append(log)
            stream.write(log_bytes)

        if entry(log) != log_entry:
            raise ValueError("E02 log hash mismatch")
        manifest["outputs"] = [*output_records, entry(staged_audit), entry(targets[2])]
        manifest["status"] = "completed"
    except Exception as exc:
        for path in reversed(published):
            path.unlink()
        manifest["status"] = "failed"
        manifest["limitations"].append(f"{type(exc).__name__}: {exc}")
        raise
    finally:
        manifest["finished_at_utc"] = now()
        validate_manifest(manifest)
        write_json(run_dir / "manifest.json", manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=["B01", "B02", "C01", "C02", "D01", "D02", "E01", "E02"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    root = Path.cwd()
    if args.stage == "B01":
        run(root, root / args.config, args.run_id)
    elif args.stage == "B02":
        run_b02(root, root / args.config, args.run_id)
    elif args.stage == "C01":
        run_c01(root, root / args.config, args.run_id)
    elif args.stage == "C02":
        run_c02(root, root / args.config, args.run_id)
    elif args.stage == "D01":
        run_d01(root, root / args.config, args.run_id)
    elif args.stage == "D02":
        run_d02(root, root / args.config, args.run_id)
    elif args.stage == "E01":
        run_e01(root, root / args.config, args.run_id)
    else:
        run_e02(root, root / args.config, args.run_id)


if __name__ == "__main__":
    main()
