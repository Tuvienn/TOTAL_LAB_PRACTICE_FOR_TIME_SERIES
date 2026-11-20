import copy
import json
from pathlib import Path

import pandas as pd
import pytest

from practice_4.data.integration import CITIES, integrate
from practice_4.pipeline import bootstrap_b02


def fixture_frames():
    times = ["2018-10-28T02:00:00+02:00", "2018-10-28T02:00:00+01:00"]
    index = pd.date_range("2018-10-28T00:00:00Z", periods=2, freq="h")
    energy = pd.DataFrame({"time": times, "total load actual": [100.0, None]})
    rows = [{"dt_iso": t, "city_name": " Barcelona " if city == "Barcelona" else city, "temp": 280, "humidity": 70, "wind_speed": 133 if city == "Madrid" else 3} for t in times for city in sorted(CITIES)]
    return energy, pd.DataFrame(rows), index


def test_normalization_dedup_dst_join_mask_and_extreme():
    energy, weather, index = fixture_frames()
    weather = pd.concat([weather, weather.iloc[[0]]], ignore_index=True)
    result, details = integrate(energy, weather, index, expected_missing=1)
    assert len(result) == 2 and details["weather_duplicate_rows_removed"] == 1
    assert list(result["timestamp_utc"]) == list(index)
    assert list(result["load_observed"]) == [True, False]
    assert pd.isna(result.loc[1, "load"])
    assert result.loc[0, "wind_speed"] == (133 + 4 * 3) / 5
    assert details["raw_wind_speed_max"] == 133


def test_conflicting_duplicates_and_city_set_fail():
    energy, weather, index = fixture_frames()
    extra = weather.iloc[[0]].copy()
    extra.loc[:, "temp"] = 281
    with pytest.raises(ValueError, match="Conflicting"):
        integrate(energy, pd.concat([weather, extra], ignore_index=True), index)
    with pytest.raises(ValueError, match="city set"):
        integrate(energy, weather[weather["city_name"] != "Madrid"], index)


def test_duplicate_energy_and_incomplete_weather_fail():
    energy, weather, index = fixture_frames()
    with pytest.raises(ValueError, match="Duplicate energy"):
        integrate(pd.concat([energy, energy.iloc[[0]]], ignore_index=True), weather, index)
    with pytest.raises(ValueError, match="coverage"):
        integrate(energy, weather.iloc[1:], index)


def test_rejects_missing_offsets_and_missing_count():
    energy, weather, index = fixture_frames()
    energy.loc[0, "time"] = "2018-10-28 02:00:00"
    with pytest.raises(ValueError, match="explicit UTC offset"):
        integrate(energy, weather, index)
    energy, weather, index = fixture_frames()
    with pytest.raises(ValueError, match="missing load count"):
        integrate(energy, weather, index, expected_missing=0)


def test_b02_bootstrap_checks_approval_and_source_hash():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "config/practice_4.json").read_text(encoding="utf-8"))
    assert len(bootstrap_b02(root, config)) == 5
    modified = copy.deepcopy(config)
    modified["b02"]["inputs"]["datasets/raw/source_manifest.json"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        bootstrap_b02(root, modified)
    modified = copy.deepcopy(config)
    modified["b02"]["approval_reference"] = ""
    with pytest.raises(ValueError, match="approval"):
        bootstrap_b02(root, modified)
