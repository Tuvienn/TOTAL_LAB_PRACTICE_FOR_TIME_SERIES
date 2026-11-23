from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from practice_4.runtime import sha256_file


def audit_uci_raw(txt_path: Path) -> dict[str, Any]:
    with txt_path.open("r", encoding="utf-8") as stream:
        header = stream.readline().strip().split(";")
    client_cols = [col.strip('"') for col in header[1:]]
    frame = pd.read_csv(
        txt_path,
        sep=";",
        decimal=",",
        low_memory=False,
    )
    ts_col = frame.columns[0]
    ts = pd.to_datetime(frame[ts_col], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    if ts.isna().any():
        raise ValueError("Invalid timestamps in LD2011_2014.txt")

    values = frame.iloc[:, 1:].to_numpy(dtype=np.float64)
    total_kw = values.sum(axis=1)
    active_clients = (values > 0).sum(axis=1)
    years = ts.dt.year
    yearly_active = {
        int(y): {
            "rows": int((years == y).sum()),
            "min_active_clients": int(active_clients[years == y].min()),
            "median_active_clients": float(np.median(active_clients[years == y])),
            "max_active_clients": int(active_clients[years == y].max()),
            "mean_total_kw": float(total_kw[years == y].mean()),
            "zero_total_rows": int((total_kw[years == y] == 0).sum()),
        }
        for y in sorted(years.unique())
    }

    return {
        "path": txt_path.name,
        "sha256": sha256_file(txt_path),
        "rows": int(len(frame)),
        "client_count": int(len(client_cols)),
        "start_local": str(ts.iloc[0]),
        "end_local": str(ts.iloc[-1]),
        "ordered": bool(ts.is_monotonic_increasing),
        "duplicate_timestamps": int(ts.duplicated().sum()),
        "missing_cells": int(np.isnan(values).sum()),
        "negative_cells": int((values < 0).sum()),
        "total_kw_min": float(np.nanmin(total_kw)),
        "total_kw_max": float(np.nanmax(total_kw)),
        "total_kw_mean": float(np.nanmean(total_kw)),
        "yearly_active_summary": yearly_active,
    }


def audit_weather_raw(weather_path: Path, bounds: dict[str, Any]) -> dict[str, Any]:
    frame = pd.read_csv(weather_path)
    required = {"timestamp_utc", "city_name", "weight", "temp_c", "humidity", "wind_speed"}
    missing_cols = required.difference(frame.columns)
    if missing_cols:
        raise ValueError(f"Missing weather columns: {sorted(missing_cols)}")

    ts = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    cities = {}
    for city, group in frame.groupby("city_name"):
        city_ts = pd.to_datetime(group["timestamp_utc"], utc=True)
        cities[str(city)] = {
            "rows": int(len(group)),
            "unique_timestamps": int(city_ts.nunique()),
            "weight": float(group["weight"].iloc[0]),
            "missing_temp": int(group["temp_c"].isna().sum()),
            "missing_humidity": int(group["humidity"].isna().sum()),
            "missing_wind": int(group["wind_speed"].isna().sum()),
        }

    ranges = {
        "temp_c": {
            "min": float(frame["temp_c"].min()),
            "max": float(frame["temp_c"].max()),
            "in_bounds": bool(
                (frame["temp_c"] >= bounds["temp_min_c"]).all()
                and (frame["temp_c"] <= bounds["temp_max_c"]).all()
            ),
        },
        "humidity": {
            "min": float(frame["humidity"].min()),
            "max": float(frame["humidity"].max()),
            "in_bounds": bool(
                (frame["humidity"] >= bounds["humidity_min"]).all()
                and (frame["humidity"] <= bounds["humidity_max"]).all()
            ),
        },
        "wind_speed": {
            "min": float(frame["wind_speed"].min()),
            "max": float(frame["wind_speed"].max()),
            "in_bounds": bool(
                (frame["wind_speed"] >= bounds["wind_speed_min"]).all()
                and (frame["wind_speed"] <= bounds["wind_speed_max"]).all()
            ),
        },
    }

    return {
        "path": weather_path.name,
        "sha256": sha256_file(weather_path),
        "rows": int(len(frame)),
        "utc_min": ts.min().isoformat(),
        "utc_max": ts.max().isoformat(),
        "duplicate_city_hour": int(frame.duplicated(subset=["city_name", "timestamp_utc"]).sum()),
        "cities": cities,
        "ranges": ranges,
    }


def summarize_raw(txt_path: Path, weather_path: Path, bounds: dict[str, Any]) -> dict[str, Any]:
    return {
        "uci": audit_uci_raw(txt_path),
        "weather": audit_weather_raw(weather_path, bounds),
    }


def format_audit_markdown(summary: dict[str, Any], manifest: dict[str, Any]) -> str:
    uci = summary["uci"]
    w = summary["weather"]
    lines = [
        "# Stage S1 — Raw Provenance & Data Quality Audit (v2)",
        "",
        f"- **Dataset:** {manifest['dataset_name']}",
        f"- **UCI URL:** {manifest['uci_source']['url']} (`{manifest['uci_source']['license']}`)",
        f"- **UCI Archive SHA256:** `{manifest['uci_source']['sha256']}`",
        f"- **UCI `LD2011_2014.txt` SHA256:** `{uci['sha256']}`",
        f"- **Weather Source:** Open-Meteo ERA5 Historical Archive (`{manifest['weather_source']['license']}`)",
        f"- **Weather CSV SHA256:** `{w['sha256']}`",
        "",
        "## 1. UCI ElectricityLoadDiagrams20112014 Raw Quality",
        "",
        f"- Rows: **{uci['rows']:,}** (15-min intervals), Clients: **{uci['client_count']}**",
        f"- Local span: `{uci['start_local']}` → `{uci['end_local']}`",
        f"- Ordered: `{uci['ordered']}`, Duplicate timestamps: `{uci['duplicate_timestamps']}`",
        f"- Missing cells: `{uci['missing_cells']}`, Negative cells: `{uci['negative_cells']}`",
        f"- Total active power (kW): min `{uci['total_kw_min']:,.2f}`, mean `{uci['total_kw_mean']:,.2f}`, max `{uci['total_kw_max']:,.2f}`",
        "",
        "### Active Clients by Year (Onboarding Regime Check)",
        "",
        "| Year | 15-min Rows | Min Active | Median Active | Max Active | Mean Total kW | Zero-Total Rows |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for year, info in uci["yearly_active_summary"].items():
        lines.append(
            f"| {year} | {info['rows']:,} | {info['min_active_clients']} | "
            f"{info['median_active_clients']:.1f} | {info['max_active_clients']} | "
            f"{info['mean_total_kw']:,.1f} | {info['zero_total_rows']} |"
        )
    lines += [
        "",
        "## 2. Open-Meteo ERA5 Portugal Weather Raw Quality",
        "",
        f"- Rows: **{w['rows']:,}** (`{w['utc_min']}` → `{w['utc_max']}`), Duplicate city-hour: `{w['duplicate_city_hour']}`",
        "",
        "| Variable | Min | Max | Unit | Physical Bounds Pass |",
        "|---|---:|---:|---|---|",
    ]
    units = {"temp_c": "°C", "humidity": "%", "wind_speed": "m/s"}
    for col, info in w["ranges"].items():
        lines.append(f"| `{col}` | {info['min']:.3f} | {info['max']:.3f} | {units[col]} | `{info['in_bounds']}` |")
    lines += [
        "",
        "| City | Weight | Rows | Unique Timestamps | Missing (T/H/W) |",
        "|---|---:|---:|---:|---|",
    ]
    for city, info in w["cities"].items():
        lines.append(
            f"| {city} | {info['weight']:.2f} | {info['rows']:,} | {info['unique_timestamps']:,} | "
            f"{info['missing_temp']}/{info['missing_humidity']}/{info['missing_wind']} |"
        )
    lines.append("")
    return "\n".join(lines)
