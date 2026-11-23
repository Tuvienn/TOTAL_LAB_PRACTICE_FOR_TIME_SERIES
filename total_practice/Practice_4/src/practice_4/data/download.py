from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from practice_4.runtime import PRACTICE_ROOT, sha256_file, utc_now, write_json


def download_file(url: str, destination: Path, timeout: int = 120) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    with destination.open("wb") as stream:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                stream.write(chunk)
    return {
        "url": url,
        "final_url": response.url,
        "status_code": int(response.status_code),
        "bytes": int(destination.stat().st_size),
        "sha256": sha256_file(destination),
        "retrieved_at_utc": utc_now(),
    }


def extract_uci_member(archive_path: Path, member_name: str, destination: Path) -> dict[str, Any]:
    with zipfile.ZipFile(archive_path, "r") as archive:
        names = archive.namelist()
        if member_name not in names:
            raise ValueError(f"Expected member {member_name} not found in archive: {names}")
        with archive.open(member_name) as src, destination.open("wb") as dst:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                dst.write(chunk)
    return {
        "path": destination.relative_to(PRACTICE_ROOT).as_posix()
        if destination.is_relative_to(PRACTICE_ROOT)
        else str(destination),
        "bytes": int(destination.stat().st_size),
        "sha256": sha256_file(destination),
    }


def fetch_open_meteo_city(
    base_url: str,
    city: dict[str, Any],
    start_date: str,
    end_date: str,
    variables: list[str],
    timeout: int = 60,
) -> pd.DataFrame:
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(variables),
        "wind_speed_unit": "ms",
        "timezone": "UTC",
    }
    response = requests.get(base_url, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    hourly = payload.get("hourly", {})
    if "time" not in hourly:
        raise ValueError(f"Missing hourly time array for {city['name']}")
    frame = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(hourly["time"], utc=True).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "city_name": city["name"],
            "weight": float(city["weight"]),
            "temp_c": pd.to_numeric(hourly["temperature_2m"], errors="raise"),
            "humidity": pd.to_numeric(hourly["relative_humidity_2m"], errors="raise"),
            "wind_speed": pd.to_numeric(hourly["wind_speed_10m"], errors="raise"),
        }
    )
    return frame


def download_all_raw(config: dict[str, Any], root: Path | None = None, force: bool = False) -> dict[str, Any]:
    base = root or PRACTICE_ROOT
    raw_dir = base / "datasets/raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    ds = config["dataset"]

    archive_path = raw_dir / ds["uci_archive_name"]
    txt_path = raw_dir / ds["uci_member_name"]
    weather_path = raw_dir / "portugal_weather_era5.csv"
    manifest_path = raw_dir / "source_manifest.json"

    if force or not archive_path.exists():
        archive_meta = download_file(ds["uci_url"], archive_path)
    else:
        archive_meta = {
            "url": ds["uci_url"],
            "final_url": ds["uci_url"],
            "status_code": 200,
            "bytes": int(archive_path.stat().st_size),
            "sha256": sha256_file(archive_path),
            "retrieved_at_utc": utc_now(),
        }

    if force or not txt_path.exists():
        txt_meta = extract_uci_member(archive_path, ds["uci_member_name"], txt_path)
    else:
        txt_meta = {
            "path": txt_path.relative_to(base).as_posix(),
            "bytes": int(txt_path.stat().st_size),
            "sha256": sha256_file(txt_path),
        }

    if force or not weather_path.exists():
        city_frames = [
            fetch_open_meteo_city(
                ds["open_meteo_url"],
                city,
                ds["start_date"],
                ds["end_date"],
                ds["open_meteo_variables"],
            )
            for city in ds["cities"]
        ]
        weather_df = pd.concat(city_frames, ignore_index=True)
        weather_df.to_csv(weather_path, index=False, lineterminator="\n")

    weather_meta = {
        "path": weather_path.relative_to(base).as_posix(),
        "url": ds["open_meteo_url"],
        "license": ds["open_meteo_license"],
        "bytes": int(weather_path.stat().st_size),
        "sha256": sha256_file(weather_path),
        "cities": ds["cities"],
        "retrieved_at_utc": utc_now(),
    }

    manifest = {
        "schema_version": "2",
        "status": "verified_official_download",
        "dataset_name": ds["name"],
        "uci_source": {
            **archive_meta,
            "archive_path": archive_path.relative_to(base).as_posix(),
            "extracted_file": txt_meta,
            "license": ds["uci_license"],
            "license_url": ds["uci_license_url"],
        },
        "weather_source": weather_meta,
        "units": {
            "load": ds["load_unit"],
            "temp_c": ds["temp_unit"],
            "humidity": ds["humidity_unit"],
            "wind_speed": ds["wind_speed_unit"],
        },
        "time_semantics": {
            "uci_raw": "15-minute intervals in Europe/Lisbon local wall time (March DST=0, Oct DST=combined)",
            "weather_raw": "1-hour intervals in UTC (ERA5 reanalysis via Open-Meteo)",
            "canonical_index": "UTC hourly",
        },
    }
    write_json(manifest_path, manifest)
    return manifest
