from pathlib import Path

import pandas as pd


def load_monthly_retail_sales(path: Path) -> pd.Series:
    """Load a10.csv as a validated monthly value series."""
    frame = pd.read_csv(path)
    if list(frame.columns) != ["date", "value"]:
        raise ValueError(f"Unexpected schema: {frame.columns.tolist()}")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame = frame.set_index("date")
    if not frame.index.is_monotonic_increasing:
        raise ValueError("Time index is not chronological")
    if frame.index.has_duplicates:
        raise ValueError("Duplicate timestamps detected")
    if frame["value"].isna().any():
        raise ValueError("Missing target values detected")
    expected = pd.date_range(frame.index.min(), frame.index.max(), freq="MS")
    if not frame.index.equals(expected):
        raise ValueError("Monthly time index contains missing or unexpected intervals")
    frame.index = pd.DatetimeIndex(frame.index, freq="MS", name=frame.index.name)
    return frame["value"].astype(float)


def chronological_split(series: pd.Series, train_fraction: float = 0.8):
    """Split a series without shuffling and return independent copies."""
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    cut = int(len(series) * train_fraction)
    return series.iloc[:cut].copy(), series.iloc[cut:].copy()
