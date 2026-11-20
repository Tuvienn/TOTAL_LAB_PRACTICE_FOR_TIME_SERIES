from __future__ import annotations

import csv
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import acf, pacf


COLUMNS = ["timestamp_utc", "load", "temp", "humidity", "wind_speed", "load_observed"]
VARIABLES = ["load", "temp", "humidity", "wind_speed"]


def load_train(path: Path, train: dict) -> pd.DataFrame:
    if train["start_row"] != 0 or train["end_row"] + 1 != train["row_count"]:
        raise ValueError("Invalid train boundary")
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        if next(reader) != COLUMNS:
            raise ValueError("Unexpected canonical schema")
        rows = list(itertools.islice(reader, train["row_count"]))
    if len(rows) != train["row_count"] or any(len(row) != len(COLUMNS) for row in rows):
        raise ValueError("Incomplete train rows")
    frame = pd.DataFrame(rows, columns=COLUMNS)
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    for name in VARIABLES:
        frame[name] = pd.to_numeric(frame[name], errors="raise")
    if not frame["load_observed"].isin(["True", "False"]).all():
        raise ValueError("Invalid observed mask")
    frame["load_observed"] = frame["load_observed"].eq("True")
    validate_train(frame, train)
    return frame


def validate_train(frame: pd.DataFrame, train: dict) -> None:
    if list(frame.columns) != COLUMNS or len(frame) != train["row_count"]:
        raise ValueError("Invalid train frame")
    ts = pd.DatetimeIndex(frame["timestamp_utc"])
    expected = pd.date_range(train["start_utc"], periods=train["row_count"], freq="h")
    if ts.tz is None or not ts.equals(expected) or ts[-1].isoformat() != train["end_utc"]:
        raise ValueError("Out-of-train or invalid timeline")
    if not frame["load_observed"].equals(frame["load"].notna()):
        raise ValueError("Observed mask mismatch")
    for col in VARIABLES:
        if not np.isfinite(frame[col].dropna()).all():
            raise ValueError("Non-finite values")


def gap_runs(frame: pd.DataFrame) -> list[dict]:
    missing = ~frame["load_observed"].to_numpy()
    result = []
    for state, group in itertools.groupby(enumerate(missing), key=lambda item: item[1]):
        positions = [i for i, _ in group]
        if state:
            start, end = positions[0], positions[-1]
            result.append({"start_utc": frame["timestamp_utc"].iloc[start].isoformat(), "end_utc": frame["timestamp_utc"].iloc[end].isoformat(), "length_hours": len(positions), "left_censored": start == 0, "right_censored": end == len(frame) - 1})
    return result


def profiles(frame: pd.DataFrame) -> dict:
    local = frame["timestamp_utc"].dt.tz_convert("Europe/Madrid")
    output = {}
    for name, values, size in [("hour", local.dt.hour, 24), ("weekday", local.dt.dayofweek, 7)]:
        data = frame.assign(group=values).groupby("group")["load"].agg(["mean", "median", "count", "size"]).reindex(range(size))
        data["missing"] = data["size"] - data["count"]
        output[name] = data.reset_index().to_dict(orient="records")
    return output


def summarize(frame: pd.DataFrame, train: dict, max_lag: int, pacf_method: str) -> dict:
    validate_train(frame, train)
    gaps = gap_runs(frame)
    blocks = []
    for state, group in itertools.groupby(enumerate(frame["load_observed"]), key=lambda item: item[1]):
        positions = [i for i, _ in group]
        if state:
            blocks.append((positions[0], positions[-1]))
    if not blocks:
        raise ValueError("No observed block")
    start, end = min(blocks, key=lambda pair: (-(pair[1] - pair[0] + 1), pair[0]))
    values = frame["load"].iloc[start:end + 1].to_numpy()
    if len(values) <= 2 * max_lag:
        raise ValueError("Observed block too short for PACF")
    extrema = {}
    for name in VARIABLES:
        series = frame[name]
        if series.notna().sum() == 0:
            raise ValueError("Variable has no observations")
        imin, imax = series.idxmin(), series.idxmax()
        extrema[name] = {"min": float(series.loc[imin]), "min_utc": frame.loc[imin, "timestamp_utc"].isoformat(), "max": float(series.loc[imax]), "max_utc": frame.loc[imax, "timestamp_utc"].isoformat(), "missing": int(series.isna().sum())}
    correlation = frame[VARIABLES].corr()
    if not np.isfinite(correlation.to_numpy()).all():
        raise ValueError("Non-finite correlations")
    counts = frame[VARIABLES].notna().astype(int).T.dot(frame[VARIABLES].notna().astype(int))
    acf_values = acf(values, nlags=max_lag, fft=True, missing="raise")
    pacf_values = pacf(values, nlags=max_lag, method=pacf_method)
    if not np.isfinite(acf_values).all() or not np.isfinite(pacf_values).all():
        raise ValueError("Non-finite autocorrelation")
    return {"rows": len(frame), "observed": int(frame["load_observed"].sum()), "missing": int((~frame["load_observed"]).sum()), "gaps": gaps, "extrema": extrema, "profiles": profiles(frame), "correlations": correlation.to_dict(), "pair_counts": counts.to_dict(), "block": {"start_utc": frame["timestamp_utc"].iloc[start].isoformat(), "end_utc": frame["timestamp_utc"].iloc[end].isoformat(), "rows": len(values), "observed_outside": int(frame["load_observed"].sum() - len(values)), "rule": "longest_observed_train_block; earliest tie"}, "acf": acf_values.tolist(), "pacf": pacf_values.tolist(), "max_lag": max_lag, "pacf_method": pacf_method}
