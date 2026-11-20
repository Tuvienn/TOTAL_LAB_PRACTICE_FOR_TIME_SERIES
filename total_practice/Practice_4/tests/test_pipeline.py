import copy
from pathlib import Path

import jsonschema
import pytest

from practice_4.data.ingestion import sha256_file
from practice_4.pipeline import bootstrap, validate_manifest


def test_bootstrap_checks_approvals_and_input_hashes(monkeypatch) -> None:
    paths = ["docs/phase_details/phase_00.md", "docs/phase_details/phase_01.md", "docs/results/problem_definition.md", "datasets/raw/energy_dataset.csv", "datasets/raw/weather_features.csv"]
    monkeypatch.setattr("practice_4.pipeline.sha256_file", lambda path: "a" * 64)
    monkeypatch.setattr(Path, "read_text", lambda *args, **kwargs: "Human duyệt Unblock & Complete Stage B01")
    config = {"stage": "B01", "approval_references": {"phase_0": "Human message", "b01": "Human message"}, "inputs": {name: "a" * 64 for name in paths}}
    assert len(bootstrap(Path("."), config)) == 5
    config["inputs"][paths[0]] = "b" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        bootstrap(Path("."), config)
    config["approval_references"] = {}
    with pytest.raises(ValueError, match="approval"):
        bootstrap(Path("."), config)


def test_manifest_schema_rejects_missing_field_and_invalid_hash() -> None:
    valid = {"schema_version": "1", "run_id": "test", "stage_id": "B01", "status": "completed", "started_at_utc": "2026-11-18T00:00:00Z", "finished_at_utc": "2026-11-18T00:00:01Z", "approval_refs": {"phase_0": "Human"}, "inputs": [{"path": "data.csv", "sha256": "a" * 64}], "config_sha256": "b" * 64, "environment": {"python": "3.12"}, "outputs": [], "checks": [], "limitations": []}
    validate_manifest(valid)
    missing = copy.deepcopy(valid)
    del missing["schema_version"]
    with pytest.raises(jsonschema.ValidationError):
        validate_manifest(missing)
    invalid = copy.deepcopy(valid)
    invalid["inputs"][0]["sha256"] = "bad"
    with pytest.raises(jsonschema.ValidationError):
        validate_manifest(invalid)
