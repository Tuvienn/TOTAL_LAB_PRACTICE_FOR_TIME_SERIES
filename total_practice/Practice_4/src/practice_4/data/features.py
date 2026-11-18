from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import islice
from pathlib import Path

import numpy as np
import pandas as pd

from practice_4.data.preprocessing import COLUMNS, FEATURES, VARIABLES

SEQUENCE_HOURS = 24
CONTEXT_HOURS = SEQUENCE_HOURS + 1
TRAIN_ROWS = 24_544
PREFIX_ROWS = 29_803
VARIABLE_NAMES = ("load", "temperature", "humidity", "wind_speed")
SCALED_COLUMNS = tuple(f"{name}_scaled" for name in FEATURES)
FLAT_FEATURE_NAMES = tuple(
    f"lag{lag:02d}_{name}"
    for lag in range(SEQUENCE_HOURS - 1, -1, -1)
    for name in VARIABLE_NAMES
)
XGB_FEATURE_NAMES = (*FLAT_FEATURE_NAMES, "mean6h", "std24h", "trend24h")
FLAG_COLUMNS = tuple(
    f"{variable}_{suffix}"
    for suffix in ("physical_invalid", "statistical_extreme")
    for variable in VARIABLES
)
PREPARED_COLUMNS = (*COLUMNS, "load_input", *FLAG_COLUMNS, *SCALED_COLUMNS)
VAR_START_ROW = 15_273
VAR_END_ROW = TRAIN_ROWS - 1
VAR_START_UTC = "2016-09-28T08:00:00+00:00"
VAR_END_UTC = "2017-10-19T14:00:00+00:00"
VAR_EARLIER_OBSERVED = 15_241


@dataclass(frozen=True)
class Origin:
    target_row: int
    origin_row: int
    context_start_row: int
    split: str
    context_finite: bool
    exclusion_reason: str | None
    y_true_mw: float | None

    @property
    def eligible(self) -> bool:
        return self.exclusion_reason is None


def _causal_context(levels: np.ndarray, target_row: int) -> np.ndarray:
    if levels.ndim != 2 or levels.shape[1] != len(SCALED_COLUMNS):
        raise ValueError("Expected four scaled columns in D02 order")
    if not CONTEXT_HOURS <= target_row < min(len(levels), PREFIX_ROWS):
        raise ValueError("Target outside the train/validation candidate rows")
    return levels[target_row - CONTEXT_HOURS:target_row]


def classify_origin(
    levels: np.ndarray, target_row: int, raw_load: float, observed: bool
) -> Origin:
    context = _causal_context(levels, target_row)
    if (observed and not np.isfinite(raw_load)) or (not observed and not np.isnan(raw_load)):
        raise ValueError("Raw target and observed mask disagree")
    context_finite = bool(np.isfinite(context).all())
    reason = None
    if not observed:
        reason = "missing_truth"
    elif not context_finite:
        reason = "invalid_context"
    return Origin(
        target_row, target_row - 1, target_row - CONTEXT_HOURS,
        "train" if target_row < TRAIN_ROWS else "validation",
        context_finite, reason, float(raw_load) if observed else None,
    )


def feature_views(
    levels: np.ndarray, target_rows
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    contexts = np.empty((len(target_rows), CONTEXT_HOURS, len(SCALED_COLUMNS)), dtype=np.float64)
    for index, target_row in enumerate(target_rows):
        contexts[index] = _causal_context(levels, target_row)
    if not np.isfinite(contexts).all():
        raise ValueError("Expected finite common context for feature construction")

    sequences = contexts[:, 1:, :].copy()
    flat = sequences.reshape(len(contexts), len(FLAT_FEATURE_NAMES))
    load = contexts[:, :, 0]
    xgb = np.column_stack((
        flat, load[:, -6:].mean(axis=1), load[:, 1:].std(axis=1, ddof=0),
        load[:, -1] - load[:, 0],
    ))
    return sequences, flat, xgb


def _hourly_index(values, start: str, end: str) -> pd.DatetimeIndex:
    parsed = [pd.Timestamp(value) for value in values]
    if not parsed or any(
        pd.isna(value) or value.tzinfo is None or value.utcoffset().total_seconds() != 0
        for value in parsed
    ):
        raise ValueError("Expected UTC timestamps")
    index = pd.DatetimeIndex(parsed).tz_convert("UTC")
    expected = pd.date_range(start, end, freq="h")
    if not index.equals(expected):
        raise ValueError("Invalid contiguous hourly timeline or endpoints")
    return index


def load_prepared_prefix(path: Path, splits: dict, expected_counts: dict) -> pd.DataFrame:
    train, validation = splits["train"], splits["validation"]
    with path.open("rb", buffering=0) as stream:
        reader = csv.reader((line.decode("utf-8") for line in islice(stream, PREFIX_ROWS + 1)), strict=True)
        if tuple(next(reader, ())) != PREPARED_COLUMNS:
            raise ValueError("Unexpected D02 prepared schema")
        rows = list(reader)
        if len(rows) != PREFIX_ROWS or any(len(row) != len(PREPARED_COLUMNS) for row in rows):
            raise ValueError("Invalid D02 prepared row count or width")
        if stream.read(1):
            raise ValueError("Unexpected bytes after the D02 prepared prefix")

    frame = pd.DataFrame(rows, columns=PREPARED_COLUMNS)
    index = _hourly_index(frame.timestamp_utc, train["start_utc"], validation["end_utc"])
    if index[TRAIN_ROWS - 1].isoformat() != train["end_utc"] or index[TRAIN_ROWS].isoformat() != validation["start_utc"]:
        raise ValueError("D02 prepared split boundary mismatch")
    frame["timestamp_utc"] = index

    for name in ("load_observed", *FLAG_COLUMNS):
        if not frame[name].isin(("True", "False")).all():
            raise ValueError(f"Invalid D02 boolean column: {name}")
        frame[name] = frame[name].eq("True")
    nullable = ("load", "load_input", SCALED_COLUMNS[0])
    for name in (*VARIABLES, "load_input", *SCALED_COLUMNS):
        values = np.array([float(value) if value else np.nan for value in frame[name]])
        allowed_missing = frame[name].eq("").to_numpy() if name in nullable else False
        if not (np.isfinite(values) | allowed_missing).all():
            raise ValueError(f"Invalid D02 numeric column: {name}")
        frame[name] = values
    if not frame.load_observed.equals(frame.load.notna()):
        raise ValueError("D02 raw truth and mask disagree")
    if not frame.load_input.isna().equals(frame[SCALED_COLUMNS[0]].isna()):
        raise ValueError("D02 working load and scaled load missingness disagree")
    if not frame.loc[frame.load_observed, "load"].equals(frame.loc[frame.load_observed, "load_input"]):
        raise ValueError("D02 working load changed an observed value")

    for name, part in (("train", frame.iloc[:TRAIN_ROWS]), ("validation", frame.iloc[TRAIN_ROWS:])):
        counts = {
            "rows": len(part),
            "missing_truth": int(part.load.isna().sum()),
            "missing_working_load": int(part.load_input.isna().sum()),
            "locf_filled": int((part.load.isna() & part.load_input.notna()).sum()),
            "flags": {column: int(part[column].sum()) for column in FLAG_COLUMNS},
        }
        if counts != expected_counts[name]:
            raise ValueError(f"D02 prepared count mismatch: {name}")
    return frame


def extract_var_train_levels(frame: pd.DataFrame) -> np.ndarray:
    block = frame.iloc[VAR_START_ROW:VAR_END_ROW + 1]
    _hourly_index(block.timestamp_utc, VAR_START_UTC, VAR_END_UTC)
    levels = block.loc[:, list(SCALED_COLUMNS)].to_numpy(dtype=np.float64)
    if (
        not block.load_observed.all()
        or not np.isfinite(block.load).all()
        or not block.load_input.eq(block.load).all()
        or not np.isfinite(levels).all()
        or int(frame.load_observed.iloc[:VAR_START_ROW].sum()) != VAR_EARLIER_OBSERVED
    ):
        raise ValueError("D02 VAR observed block, levels or exclusion count mismatch")
    return levels
