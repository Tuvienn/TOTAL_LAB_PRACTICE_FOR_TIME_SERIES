from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from practice_4.data.ingestion import audit_weather_raw
from practice_4.runtime import PRACTICE_ROOT, load_config, read_file_map, sha256_file


def test_s1_raw_files_and_manifest_verified():
    cfg = load_config()
    raw_dir = PRACTICE_ROOT / "datasets/raw"
    manifest_path = raw_dir / "source_manifest.json"
    assert manifest_path.exists(), "source_manifest.json missing"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "2"
    assert manifest["status"] == "verified_official_download"

    archive_path = PRACTICE_ROOT / manifest["uci_source"]["archive_path"]
    txt_path = PRACTICE_ROOT / manifest["uci_source"]["extracted_file"]["path"]
    weather_path = PRACTICE_ROOT / manifest["weather_source"]["path"]

    for p in (archive_path, txt_path, weather_path):
        assert p.exists() and p.stat().st_size > 0, f"Missing or empty raw file: {p}"

    assert sha256_file(archive_path) == manifest["uci_source"]["sha256"]
    assert sha256_file(txt_path) == manifest["uci_source"]["extracted_file"]["sha256"]
    assert sha256_file(weather_path) == manifest["weather_source"]["sha256"]

    w_audit = audit_weather_raw(weather_path, cfg["anomaly_bounds"])
    assert w_audit["duplicate_city_hour"] == 0
    assert set(w_audit["cities"].keys()) == {"Lisbon", "Porto", "Coimbra"}
    for col in ("temp_c", "humidity", "wind_speed"):
        assert w_audit["ranges"][col]["in_bounds"] is True

    audit_md = PRACTICE_ROOT / "docs/results/data_audit.md"
    assert audit_md.exists() and audit_md.stat().st_size > 200


def test_s1_file_map_registered_raw():
    rows = {r["path"]: r for r in read_file_map()}
    for rel in (
        "datasets/raw/electricityloaddiagrams20112014.zip",
        "datasets/raw/LD2011_2014.txt",
        "datasets/raw/portugal_weather_era5.csv",
        "datasets/raw/source_manifest.json",
        "docs/results/data_audit.md",
    ):
        assert rel in rows, f"{rel} not tracked in file_map.csv"
        assert rows[rel]["existence"] == "EXISTING"
