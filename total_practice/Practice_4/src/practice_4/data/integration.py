from __future__ import annotations

import pandas as pd


CITIES = frozenset({"Madrid", "Barcelona", "Valencia", "Seville", "Bilbao"})
WEATHER = ["temp", "humidity", "wind_speed"]


def parse_utc(values: pd.Series) -> pd.Series:
    text = values.astype("string")
    if text.isna().any() or not text.str.contains(r"(?:Z|[+-]\d{2}:\d{2})$", regex=True).all():
        raise ValueError("Every timestamp must include an explicit UTC offset")
    result = pd.to_datetime(text, format="mixed", utc=True, errors="coerce")
    if result.isna().any():
        raise ValueError("Invalid timestamp")
    return result


def integrate(energy: pd.DataFrame, weather: pd.DataFrame, expected_index: pd.DatetimeIndex, expected_missing: int | None = None) -> tuple[pd.DataFrame, dict]:
    if not {"time", "total load actual"}.issubset(energy.columns) or not {"dt_iso", "city_name", *WEATHER}.issubset(weather.columns):
        raise ValueError("Required columns missing")
    if expected_index.tz is None or str(expected_index.tz) != "UTC" or not expected_index.is_unique or not expected_index.is_monotonic_increasing:
        raise ValueError("Expected timeline must be sorted, unique and UTC")
    if len(expected_index) == 0 or not expected_index.equals(pd.date_range(expected_index[0], periods=len(expected_index), freq="h", tz="UTC")):
        raise ValueError("Expected timeline must be contiguous hourly")
    e = pd.DataFrame({"timestamp_utc": parse_utc(energy["time"]), "load": pd.to_numeric(energy["total load actual"], errors="raise")})
    if e["timestamp_utc"].duplicated().any():
        raise ValueError("Duplicate energy timestamps")
    if not pd.DatetimeIndex(e["timestamp_utc"].sort_values()).equals(expected_index):
        raise ValueError("Energy timestamp coverage differs from expected timeline")
    if expected_missing is not None and int(e["load"].isna().sum()) != expected_missing:
        raise ValueError("Unexpected missing load count")
    w = weather.loc[:, ["city_name", *WEATHER]].copy()
    if w["city_name"].isna().any():
        raise ValueError("Missing city name")
    w["city_name"] = w["city_name"].astype("string").str.strip()
    if set(w["city_name"].unique()) != CITIES:
        raise ValueError("Unexpected city set")
    w["timestamp_utc"] = parse_utc(weather["dt_iso"])
    for column in WEATHER:
        w[column] = pd.to_numeric(w[column], errors="raise")
    if w[WEATHER].isna().any().any():
        raise ValueError("Missing weather values")
    grouped = w.groupby(["city_name", "timestamp_utc"], dropna=False)
    if (grouped[WEATHER].nunique(dropna=False) > 1).any(axis=None):
        raise ValueError("Conflicting duplicate weather values")
    dedup = w.drop_duplicates(["city_name", "timestamp_utc"])
    if len(dedup) != len(expected_index) * len(CITIES):
        raise ValueError("Weather city-hour coverage mismatch")
    coverage = dedup.groupby("timestamp_utc")["city_name"].nunique()
    if not pd.DatetimeIndex(coverage.index).equals(expected_index) or not coverage.eq(len(CITIES)).all():
        raise ValueError("Weather timestamps or city coverage mismatch")
    proxy = dedup.groupby("timestamp_utc", as_index=False)[WEATHER].mean()
    result = e.merge(proxy, on="timestamp_utc", how="left", validate="one_to_one", indicator=True)
    if len(result) != len(e) or not result["_merge"].eq("both").all():
        raise ValueError("Weather join coverage/cardinality mismatch")
    result = result.drop(columns="_merge").sort_values("timestamp_utc").reset_index(drop=True)
    result["load_observed"] = result["load"].notna()
    details = {"energy_rows": len(energy), "weather_rows": len(weather), "canonical_rows": len(result), "weather_duplicate_rows_removed": len(w) - len(dedup), "missing_load": int(result["load"].isna().sum()), "raw_wind_speed_max": float(w["wind_speed"].max()), "raw_temp_max": float(w["temp"].max()), "canonical_wind_speed_max": float(result["wind_speed"].max())}
    return result, details
