from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from practice_4.runtime import sha256_file


CANONICAL_COLUMNS = [
    "timestamp_utc",
    "load",
    "temp",
    "humidity",
    "wind_speed",
    "load_observed",
    "dst_fallback_split",
    "weather_physical_anomaly",
]


def uci_local_to_utc_hourly(
    frame: pd.DataFrame,
    tz_local: str = "Europe/Lisbon",
    start_utc: str = "2012-01-01T00:00:00+00:00",
    end_utc: str = "2014-12-31T23:00:00+00:00",
    stable_client_filter: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    ts_col = frame.columns[0]
    raw_ts = pd.to_datetime(frame[ts_col], format="%Y-%m-%d %H:%M:%S", errors="raise")
    hour_start_local = (raw_ts - np.timedelta64(15, "m")).dt.floor("h")

    client_values = frame.iloc[:, 1:].to_numpy(dtype=np.float64)
    client_names = list(frame.columns[1:])

    if stable_client_filter:
        jan_2012_mask = (hour_start_local >= pd.Timestamp("2012-01-01 00:00:00")) & (
            hour_start_local < pd.Timestamp("2012-02-01 00:00:00")
        )
        if jan_2012_mask.any():
            active_jan = (client_values[jan_2012_mask] > 0).sum(axis=0) > 0
            selected_idx = np.where(active_jan)[0]
        else:
            selected_idx = np.arange(client_values.shape[1])
    else:
        selected_idx = np.arange(client_values.shape[1])

    selected_values = client_values[:, selected_idx]
    total_15m_kw = selected_values.sum(axis=1)

    hourly_local = (
        pd.DataFrame({"local_hour": hour_start_local, "kw": total_15m_kw})
        .groupby("local_hour", sort=True)["kw"]
        .mean()
    )

    full_utc = pd.date_range(start_utc, end_utc, freq="h", tz="UTC")
    full_local = full_utc.tz_convert(tz_local)
    local_naive = full_local.tz_localize(None)

    counts_per_local = pd.Series(local_naive).value_counts()
    repeated_local = set(counts_per_local[counts_per_local > 1].index)

    loads = np.empty(len(full_utc), dtype=np.float64)
    dst_flags = np.zeros(len(full_utc), dtype=bool)
    missing_count = 0

    for i, loc_ts in enumerate(local_naive):
        if loc_ts in hourly_local.index:
            val = float(hourly_local.loc[loc_ts])
            if loc_ts in repeated_local:
                val = val / 2.0
                dst_flags[i] = True
            loads[i] = val
        else:
            loads[i] = np.nan
            missing_count += 1

    load_df = pd.DataFrame(
        {
            "timestamp_utc": full_utc,
            "load": loads,
            "load_observed": np.isfinite(loads),
            "dst_fallback_split": dst_flags,
        }
    )

    details = {
        "total_clients_raw": int(len(client_names)),
        "selected_stable_clients": int(len(selected_idx)),
        "start_utc": full_utc[0].isoformat(),
        "end_utc": full_utc[-1].isoformat(),
        "hourly_rows": int(len(load_df)),
        "missing_load_hours": int(missing_count),
        "dst_fallback_split_hours": int(dst_flags.sum()),
        "load_min": float(np.nanmin(loads)),
        "load_max": float(np.nanmax(loads)),
        "load_mean": float(np.nanmean(loads)),
    }
    return load_df, details


def build_weighted_weather(
    weather_df: pd.DataFrame,
    expected_utc: pd.DatetimeIndex,
    bounds: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    w = weather_df.copy()
    w["timestamp_utc"] = pd.to_datetime(w["timestamp_utc"], utc=True, errors="raise")
    w["city_name"] = w["city_name"].astype(str).str.strip()
    if w.duplicated(subset=["city_name", "timestamp_utc"]).any():
        raise ValueError("Duplicate (city_name, timestamp_utc) in weather raw file")

    w["phys_anomaly"] = (
        (w["temp_c"] < bounds["temp_min_c"])
        | (w["temp_c"] > bounds["temp_max_c"])
        | (w["humidity"] < bounds["humidity_min"])
        | (w["humidity"] > bounds["humidity_max"])
        | (w["wind_speed"] < bounds["wind_speed_min"])
        | (w["wind_speed"] > bounds["wind_speed_max"])
        | ((w["humidity"] == 0) & (np.isclose(w["temp_c"], 0.0, atol=1e-6)))
    )

    sub = w[w["timestamp_utc"].isin(expected_utc)].copy()
    city_counts = sub.groupby("timestamp_utc")["city_name"].nunique()
    expected_cities = int(w["city_name"].nunique())
    if len(city_counts) != len(expected_utc) or not city_counts.eq(expected_cities).all():
        raise ValueError("Incomplete city weather coverage over expected UTC timeline")

    weight_sum = sub.groupby("timestamp_utc")["weight"].sum()
    if not np.allclose(weight_sum.to_numpy(), 1.0, atol=1e-6):
        raise ValueError("City weather weights do not sum to 1.0")

    for col in ("temp_c", "humidity", "wind_speed"):
        sub[f"_w_{col}"] = sub[col] * sub["weight"]

    agg = sub.groupby("timestamp_utc", sort=True).agg(
        temp=("_w_temp_c", "sum"),
        humidity=("_w_humidity", "sum"),
        wind_speed=("_w_wind_speed", "sum"),
        weather_physical_anomaly=("phys_anomaly", "any"),
    )
    agg = agg.reindex(expected_utc).reset_index().rename(columns={"index": "timestamp_utc"})
    if agg[["temp", "humidity", "wind_speed"]].isna().any().any():
        raise ValueError("Missing values after weighted weather aggregation")

    details = {
        "cities_count": expected_cities,
        "raw_anomaly_rows": int(sub["phys_anomaly"].sum()),
        "canonical_anomaly_hours": int(agg["weather_physical_anomaly"].sum()),
        "temp_min": float(agg["temp"].min()),
        "temp_max": float(agg["temp"].max()),
        "humidity_min": float(agg["humidity"].min()),
        "humidity_max": float(agg["humidity"].max()),
        "wind_speed_min": float(agg["wind_speed"].min()),
        "wind_speed_max": float(agg["wind_speed"].max()),
    }
    return agg, details


def integrate_canonical(
    uci_frame: pd.DataFrame,
    weather_frame: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    ds = config["dataset"]
    load_df, load_details = uci_local_to_utc_hourly(
        uci_frame,
        tz_local=ds["timezone_local"],
        start_utc=ds["min_active_clients_date"],
        end_utc="2014-12-31T23:00:00+00:00",
        stable_client_filter=True,
    )
    expected_utc = pd.DatetimeIndex(load_df["timestamp_utc"])
    weather_agg, weather_details = build_weighted_weather(
        weather_frame, expected_utc, config["anomaly_bounds"]
    )
    merged = load_df.merge(
        weather_agg,
        on="timestamp_utc",
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != len(load_df):
        raise ValueError("Load-weather join row count mismatch")
    merged = merged[CANONICAL_COLUMNS].sort_values("timestamp_utc").reset_index(drop=True)
    merged["timestamp_utc"] = merged["timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    details = {"load": load_details, "weather": weather_details, "canonical_rows": int(len(merged))}
    return merged, details


def format_data_contract_markdown(
    details: dict[str, Any],
    canonical_path: Path,
    source_manifest: dict[str, Any],
) -> str:
    ld = details["load"]
    wd = details["weather"]
    return "\n".join(
        [
            "# Stage S2 — Canonical Hourly Data Contract (v2)",
            "",
            f"- **Canonical CSV:** `{canonical_path.name}` (SHA256: `{sha256_file(canonical_path)}`)",
            f"- **Source UCI SHA256:** `{source_manifest['uci_source']['extracted_file']['sha256']}`",
            f"- **Source Weather SHA256:** `{source_manifest['weather_source']['sha256']}`",
            f"- **Rows:** **{details['canonical_rows']:,}** contiguous 1-hour UTC steps (`{ld['start_utc']}` → `{ld['end_utc']}`)",
            f"- **Stable Client Cohort:** **{ld['selected_stable_clients']} / {ld['total_clients_raw']}** clients active in Jan 2012 (eliminates 2011 onboarding step-jump).",
            f"- **DST Handling (`Europe/Lisbon`):** Spring-forward non-existent zero-padded local hour excluded naturally upon UTC mapping; Fall-back doubled local hour halved across its two UTC hours (`{ld['dst_fallback_split_hours']}` flagged hours).",
            f"- **Weather Proxy:** Population-weighted ERA5 mean (Lisbon 0.50, Porto 0.35, Coimbra 0.15). Physical anomaly hours: `{wd['canonical_anomaly_hours']}`.",
            "",
            "| Column | Unit / Type | Range / Summary |",
            "|---|---|---|",
            f"| `timestamp_utc` | ISO-8601 UTC (`1h`) | `{ld['start_utc']}` .. `{ld['end_utc']}` |",
            f"| `load` | kW (`float64`) | min `{ld['load_min']:,.2f}`, mean `{ld['load_mean']:,.2f}`, max `{ld['load_max']:,.2f}`, missing `{ld['missing_load_hours']}` |",
            f"| `temp` | °C (`float64`) | `{wd['temp_min']:.2f}` .. `{wd['temp_max']:.2f}` |",
            f"| `humidity` | % (`float64`) | `{wd['humidity_min']:.2f}` .. `{wd['humidity_max']:.2f}` |",
            f"| `wind_speed` | m/s (`float64`) | `{wd['wind_speed_min']:.2f}` .. `{wd['wind_speed_max']:.2f}` |",
            "| `load_observed` | `bool` | Exact mask of observed raw target |",
            "| `dst_fallback_split` | `bool` | Marks October fall-back split hours |",
            "| `weather_physical_anomaly` | `bool` | Marks physical out-of-range weather hours |",
            "",
        ]
    )
