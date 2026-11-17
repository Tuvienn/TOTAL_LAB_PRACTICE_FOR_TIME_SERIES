from pathlib import Path

import pytest
import pandas as pd

from practice_4.data.ingestion import read_raw, sha256_file, summarize


def test_rejects_missing_column_and_bad_timestamp(monkeypatch) -> None:
    path = Path("input.csv")
    monkeypatch.setattr(pd, "read_csv", lambda path: pd.DataFrame({"time": ["invalid"], "value": [1]}))
    with pytest.raises(ValueError, match="Missing required columns"):
        read_raw(path, {"time", "load"}, "time")
    with pytest.raises(ValueError, match="timestamp"):
        read_raw(path, {"time", "value"}, "time")


def test_audit_detects_duplicate_conflict(monkeypatch) -> None:
    energy = pd.DataFrame({"time": ["2020-01-01T00:00:00+01:00", "2020-01-01T01:00:00+01:00"], "total load actual": [100.0, None]})
    weather = pd.DataFrame({"dt_iso": ["2020-01-01T00:00:00+01:00"] * 2, "city_name": ["A", "A"], "temp": [280, 281], "humidity": [80, 80], "wind_speed": [3, 3]})
    monkeypatch.setattr(pd, "read_csv", lambda path: energy.copy() if path.name == "energy.csv" else weather.copy())
    result = summarize(Path("energy.csv"), Path("weather.csv"))
    assert result["energy"]["missing"]["total load actual"] == 1
    assert result["weather"]["conflicting_required_weather_groups"] == 1
    assert result["weather"]["city_coverage"]["A"]["missing_energy_timestamps"] == 1


def test_real_raw_audit_preserves_hashes() -> None:
    root = Path(__file__).resolve().parents[1] / "datasets" / "raw"
    energy, weather = root / "energy_dataset.csv", root / "weather_features.csv"
    before = [sha256_file(path) for path in (energy, weather)]
    result = summarize(energy, weather)
    assert result["energy"]["rows"] > 0
    assert result["weather"]["rows"] > 0
    assert before == [sha256_file(path) for path in (energy, weather)]
