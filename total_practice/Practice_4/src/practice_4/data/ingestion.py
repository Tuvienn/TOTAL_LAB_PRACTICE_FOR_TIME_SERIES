from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_raw(path: Path, required: set[str], timestamp: str) -> tuple[pd.DataFrame, pd.Series]:
    frame = pd.read_csv(path)
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    times = pd.to_datetime(frame[timestamp], utc=True, errors="coerce", format="mixed")
    if times.isna().any():
        raise ValueError(f"Invalid or missing timestamp in {path.name}")
    for column in required - {timestamp, "city_name"}:
        parsed = pd.to_numeric(frame[column], errors="coerce")
        if (parsed.isna() & frame[column].notna()).any():
            raise ValueError(f"Non-numeric values in {column}")
    return frame, times


def summarize(energy_path: Path, weather_path: Path) -> dict:
    energy, et = read_raw(energy_path, {"time", "total load actual"}, "time")
    weather, wt = read_raw(weather_path, {"dt_iso", "city_name", "temp", "humidity", "wind_speed"}, "dt_iso")
    groups = weather.assign(_utc=wt).groupby(["city_name", "_utc"], dropna=False)
    sizes = groups.size()
    duplicated = sizes[sizes > 1]
    conflict = (groups[["temp", "humidity", "wind_speed"]].nunique(dropna=False) > 1).any(axis=1)
    timeline = pd.DatetimeIndex(et.dropna().unique()).sort_values()
    if len(timeline) == 0:
        raise ValueError("Empty energy timeline")
    expected = pd.date_range(timeline.min(), timeline.max(), freq="h")
    ranges = {}
    for name, series, unit in [("total load actual", energy["total load actual"], "MW"), ("temp", weather["temp"], "K"), ("humidity", weather["humidity"], "%"), ("wind_speed", weather["wind_speed"], "m/s")]:
        values = pd.to_numeric(series, errors="raise")
        if values.notna().sum() == 0:
            raise ValueError(f"No observed values for {name}")
        minimum, maximum = float(values.min()), float(values.max())
        ranges[name] = {"min": minimum, "max": maximum, "unit": unit, "missing": int(values.isna().sum())}
    ranges["total load actual"]["basic_range_pass"] = ranges["total load actual"]["min"] >= 0
    ranges["temp"]["basic_range_pass"] = ranges["temp"]["min"] > 0
    ranges["humidity"]["basic_range_pass"] = ranges["humidity"]["min"] >= 0 and ranges["humidity"]["max"] <= 100
    ranges["wind_speed"]["basic_range_pass"] = ranges["wind_speed"]["min"] >= 0
    city_coverage = {}
    for city, group in weather.assign(_utc=wt).groupby("city_name", dropna=False):
        unique = pd.DatetimeIndex(group["_utc"].unique())
        city_coverage[str(city)] = {"rows": len(group), "unique_timestamps": len(unique), "missing_energy_timestamps": len(timeline.difference(unique)), "extra_timestamps": len(unique.difference(timeline))}
    return {"energy": {"rows": len(energy), "columns": list(energy.columns), "missing": {k: int(v) for k, v in energy.isna().sum().items()}, "duplicate_rows": int(energy.duplicated().sum()), "duplicate_timestamps": int(et.duplicated().sum()), "ordered": bool(et.is_monotonic_increasing), "utc_min": str(et.min()), "utc_max": str(et.max()), "unique_timestamps": len(timeline), "missing_hours": len(expected.difference(timeline))}, "weather": {"rows": len(weather), "columns": list(weather.columns), "missing": {k: int(v) for k, v in weather.isna().sum().items()}, "duplicate_rows": int(weather.duplicated().sum()), "ordered": bool(wt.is_monotonic_increasing), "utc_min": str(wt.min()), "utc_max": str(wt.max()), "duplicate_city_hour_groups": len(duplicated), "extra_city_hour_rows": int((duplicated - 1).sum()), "conflicting_required_weather_groups": int(conflict.sum()), "city_coverage": city_coverage}, "ranges": ranges}
