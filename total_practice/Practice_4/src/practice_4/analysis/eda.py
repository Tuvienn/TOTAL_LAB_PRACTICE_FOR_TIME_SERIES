from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import acf, pacf


VARIABLES = ["load", "temp", "humidity", "wind_speed"]


def load_train_only(canonical_path: Path, train_split: dict[str, Any]) -> pd.DataFrame:
    count = int(train_split["row_count"])
    frame = pd.read_csv(canonical_path, nrows=count)
    if len(frame) != count:
        raise ValueError("Canonical file shorter than train row count")
    ts = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    if ts.iloc[0].isoformat() != train_split["start_utc"] or ts.iloc[-1].isoformat() != train_split["end_utc"]:
        raise ValueError("Train boundary mismatch or out-of-train access")
    frame["timestamp_utc"] = ts
    return frame


def summarize_train_eda(
    frame: pd.DataFrame,
    train_split: dict[str, Any],
    tz_local: str = "Europe/Lisbon",
    max_lag: int = 168,
) -> dict[str, Any]:
    if len(frame) != int(train_split["row_count"]):
        raise ValueError("EDA frame length does not match train split")
    ts = pd.DatetimeIndex(frame["timestamp_utc"])
    if ts[-1].isoformat() != train_split["end_utc"]:
        raise ValueError("Out-of-train observation detected in EDA frame")

    local = ts.tz_convert(tz_local)
    profiles = {}
    for axis, labels, size in (
        ("hour", local.hour, 24),
        ("weekday", local.dayofweek, 7),
        ("month", local.month, 12),
    ):
        idx = range(1, 13) if axis == "month" else range(size)
        agg = frame.assign(group=labels).groupby("group")["load"].agg(["mean", "median", "std", "count"]).reindex(idx)
        profiles[axis] = agg.reset_index().to_dict(orient="records")

    extrema = {}
    for col in VARIABLES:
        s = frame[col]
        imin, imax = int(s.idxmin()), int(s.idxmax())
        p05, p995 = np.percentile(s.dropna().to_numpy(dtype=np.float64), [0.5, 99.5])
        extrema[col] = {
            "min": float(s.iloc[imin]),
            "min_utc": ts[imin].isoformat(),
            "max": float(s.iloc[imax]),
            "max_utc": ts[imax].isoformat(),
            "mean": float(s.mean()),
            "std": float(s.std()),
            "p0_5": float(p05),
            "p99_5": float(p995),
            "missing": int(s.isna().sum()),
        }

    pearson = frame[VARIABLES].corr(method="pearson").to_dict()
    spearman = frame[VARIABLES].corr(method="spearman").to_dict()

    load_vals = frame["load"].dropna().to_numpy(dtype=np.float64)
    acf_vals = acf(load_vals, nlags=max_lag, fft=True).tolist()
    pacf_vals = pacf(load_vals, nlags=max_lag, method="ywm").tolist()

    return {
        "rows": int(len(frame)),
        "start_utc": ts[0].isoformat(),
        "end_utc": ts[-1].isoformat(),
        "timezone_local": tz_local,
        "missing_load": int(frame["load"].isna().sum()),
        "dst_fallback_split_hours": int(frame["dst_fallback_split"].sum()),
        "weather_physical_anomaly_hours": int(frame["weather_physical_anomaly"].sum()),
        "extrema": extrema,
        "profiles": profiles,
        "pearson": pearson,
        "spearman": spearman,
        "acf": acf_vals,
        "pacf": pacf_vals,
        "max_lag": max_lag,
    }


def format_eda_markdown(summary: dict[str, Any]) -> str:
    ext = summary["extrema"]
    p = summary["pearson"]["load"]
    s = summary["spearman"]["load"]
    lines = [
        "# Stage S3 — Train-Only Exploratory Data Analysis (v2)",
        "",
        f"- **Scope:** Train split only (`{summary['rows']:,}` hours, `{summary['start_utc']}` → `{summary['end_utc']}`). Validation and test were never accessed.",
        f"- **Missing load:** `{summary['missing_load']}` | **DST fall-back split hours:** `{summary['dst_fallback_split_hours']}` | **Weather physical anomalies:** `{summary['weather_physical_anomaly_hours']}`",
        "",
        "## 1. Variable Distributions & Extrema (Train)",
        "",
        "| Variable | Min | Mean | Std | Max | P0.5 | P99.5 | Missing |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for col in VARIABLES:
        e = ext[col]
        lines.append(
            f"| `{col}` | {e['min']:,.2f} | {e['mean']:,.2f} | {e['std']:,.2f} | {e['max']:,.2f} | "
            f"{e['p0_5']:,.2f} | {e['p99_5']:,.2f} | {e['missing']} |"
        )
    lines += [
        "",
        "## 2. Load–Weather Association (Train, Non-Causal)",
        "",
        "| Weather Variable | Pearson r | Spearman ρ |",
        "|---|---:|---:|",
        f"| `temp` | {p['temp']:.4f} | {s['temp']:.4f} |",
        f"| `humidity` | {p['humidity']:.4f} | {s['humidity']:.4f} |",
        f"| `wind_speed` | {p['wind_speed']:.4f} | {s['wind_speed']:.4f} |",
        "",
        "## 3. Temporal Dependence (ACF)",
        "",
        f"- Lag 1h ACF: `{summary['acf'][1]:.4f}`",
        f"- Lag 24h (daily) ACF: `{summary['acf'][24]:.4f}`",
        f"- Lag 168h (weekly) ACF: `{summary['acf'][168]:.4f}`",
        "",
    ]
    return "\n".join(lines)
