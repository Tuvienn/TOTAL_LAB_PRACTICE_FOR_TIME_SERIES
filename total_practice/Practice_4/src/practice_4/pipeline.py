from __future__ import annotations

import argparse
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
MANIFEST_SCHEMA = {"type": "object", "required": ["schema_version", "run_id", "stage_id", "status", "started_at_utc", "finished_at_utc", "approval_refs", "inputs", "config_sha256", "environment", "outputs", "checks", "limitations"], "properties": {"schema_version": {"const": "1"}, "run_id": {"type": "string", "minLength": 1}, "stage_id": {"enum": ["B01", "B02", "C01", "C02", "D01"]}, "status": {"enum": ["running", "completed", "failed"]}, "started_at_utc": {"type": "string"}, "finished_at_utc": {"type": ["string", "null"]}, "approval_refs": {"type": "object", "minProperties": 1}, "inputs": {"type": "array", "items": FILE}, "config_sha256": HASH, "environment": {"type": "object", "minProperties": 1}, "outputs": {"type": "array", "items": FILE}, "checks": {"type": "array", "items": {"type": "object", "required": ["name", "status", "evidence"]}}, "limitations": {"type": "array", "items": {"type": "string"}}}, "additionalProperties": False}


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=["B01", "B02", "C01", "C02", "D01"])
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
    else:
        run_d01(root, root / args.config, args.run_id)


if __name__ == "__main__":
    main()
