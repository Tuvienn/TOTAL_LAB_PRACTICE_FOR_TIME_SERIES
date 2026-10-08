from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd


EXPECTED_COLUMNS = ["rownames", "time", "value"]
EXPECTED_ROWS = 144
EXPECTED_START = "1949-01-01"
EXPECTED_END = "1960-12-01"
EXPECTED_FREQUENCY = "MS"


def calculate_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def load_air_passengers(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    if raw.columns.tolist() != EXPECTED_COLUMNS:
        raise ValueError(f"Unexpected columns: {raw.columns.tolist()}")
    if len(raw) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} rows, found {len(raw)}")
    if raw["rownames"].tolist() != list(range(1, EXPECTED_ROWS + 1)):
        raise ValueError("Source row identifiers are not sequential from 1 to 144")
    expected_time = 1949 + np.arange(EXPECTED_ROWS) / 12
    if not np.allclose(raw["time"].to_numpy(dtype=float), expected_time, atol=1e-10):
        raise ValueError("Fractional-year values do not match the documented monthly progression")
    values = pd.to_numeric(raw["value"], errors="raise").astype(float)
    index = pd.date_range(EXPECTED_START, periods=EXPECTED_ROWS, freq=EXPECTED_FREQUENCY)
    if index[-1] != pd.Timestamp(EXPECTED_END):
        raise ValueError("Constructed monthly index does not end at the expected date")
    frame = pd.DataFrame({"passengers_thousands": values.to_numpy()}, index=index)
    frame.index.name = "date"
    if frame.index.has_duplicates:
        raise ValueError("Duplicate timestamps detected")
    if not frame.index.is_monotonic_increasing:
        raise ValueError("Timestamps are not chronological")
    if frame.isna().any().any():
        raise ValueError("Unexpected missing values detected")
    if not frame["passengers_thousands"].gt(0).all():
        raise ValueError("Passenger values must be positive")
    return frame

