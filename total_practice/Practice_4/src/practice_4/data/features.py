from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import islice, zip_longest
from pathlib import Path
from zipfile import ZipFile

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


RV2_VERSION = 1
ORIGIN_COLUMNS = (
    "schema_version", "origin_row", "target_row", "context_start_row",
    "origin_timestamp_utc", "target_timestamp_utc", "split", "load_observed",
    "context_finite", "eligible", "exclusion_reason", "y_true_mw", "sample_index",
)
ARRAY_KEYS = (
    "schema_version", "target_row", "x_lstm", "x_flat", "x_xgb", "y_true_mw",
    "var_row", "var_train_levels",
)


def align_origins(frame: pd.DataFrame) -> tuple[list[Origin], dict[str, dict[str, int]]]:
    if len(frame) != PREFIX_ROWS:
        raise ValueError("E02 requires the exact prepared train and validation prefix")
    levels = frame.loc[:, list(SCALED_COLUMNS)].to_numpy(dtype=np.float64)
    raw = frame.load.to_numpy(dtype=np.float64)
    observed = frame.load_observed.to_numpy(dtype=bool)
    origins = [
        classify_origin(levels, row, raw[row], observed[row])
        for row in range(CONTEXT_HOURS, PREFIX_ROWS)
    ]
    counts = {}
    for name, expected in (("train", TRAIN_ROWS - CONTEXT_HOURS), ("validation", PREFIX_ROWS - TRAIN_ROWS)):
        part = [origin for origin in origins if origin.split == name]
        missing = sum(origin.exclusion_reason == "missing_truth" for origin in part)
        invalid = sum(origin.exclusion_reason == "invalid_context" for origin in part)
        eligible = sum(origin.eligible for origin in part)
        if not eligible or len(part) != expected or missing + invalid + eligible != expected:
            raise ValueError(f"Empty eligible split or candidate count mismatch: {name}")
        counts[name] = {
            "n_considered": expected, "n_missing_excluded": missing,
            "n_input_excluded": invalid, "n_eligible": eligible,
        }
    return origins, counts


def _origin_rows(frame: pd.DataFrame, origins: list[Origin]):
    timestamps = [timestamp.isoformat(timespec="seconds") for timestamp in frame.timestamp_utc]
    sample_index = 0
    for origin in origins:
        yield (
            str(RV2_VERSION), str(origin.origin_row), str(origin.target_row), str(origin.context_start_row),
            timestamps[origin.origin_row], timestamps[origin.target_row], origin.split,
            str(origin.y_true_mw is not None), str(origin.context_finite), str(origin.eligible),
            origin.exclusion_reason or "",
            "" if origin.y_true_mw is None else repr(origin.y_true_mw),
            str(sample_index) if origin.eligible else "",
        )
        sample_index += origin.eligible


def stage_aligned_inputs(
    frame: pd.DataFrame, origins: list[Origin], csv_path: Path, npz_path: Path
) -> None:
    target_rows = np.array([origin.target_row for origin in origins if origin.eligible], dtype=np.int64)
    levels = frame.loc[:, list(SCALED_COLUMNS)].to_numpy(dtype=np.float64)
    sequences, flat, xgb = feature_views(levels, target_rows)
    var_levels = extract_var_train_levels(frame)

    with csv_path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(ORIGIN_COLUMNS)
        writer.writerows(_origin_rows(frame, origins))
    with npz_path.open("xb") as stream:
        np.savez_compressed(
            stream,
            schema_version=np.asarray(RV2_VERSION, dtype=np.uint8),
            target_row=target_rows,
            x_lstm=sequences,
            x_flat=flat,
            x_xgb=xgb,
            y_true_mw=frame.load.to_numpy(dtype=np.float64)[target_rows],
            var_row=np.arange(VAR_START_ROW, VAR_END_ROW + 1, dtype=np.int64),
            var_train_levels=var_levels,
        )


def validate_aligned_inputs(
    frame: pd.DataFrame, csv_path: Path, npz_path: Path
) -> dict[str, tuple[tuple[int, ...], str]]:
    candidates = np.arange(CONTEXT_HOURS, PREFIX_ROWS, dtype=np.int64)
    levels = frame.loc[:, list(SCALED_COLUMNS)].to_numpy(dtype=np.float64)
    context = levels[candidates[:, None] - np.arange(CONTEXT_HOURS, 0, -1)]
    context_finite = np.isfinite(context).all(axis=(1, 2))
    observed = frame.load_observed.to_numpy(dtype=bool)[candidates]
    raw = frame.load.to_numpy(dtype=np.float64)[candidates]
    eligible = observed & context_finite
    reasons = np.where(~observed, "missing_truth", np.where(~context_finite, "invalid_context", None))
    expected_origins = [
        Origin(row, row - 1, row - CONTEXT_HOURS, split, bool(finite), reason, float(truth) if mask else None)
        for row, split, finite, reason, truth, mask in zip(
            candidates, np.where(candidates < TRAIN_ROWS, "train", "validation"),
            context_finite, reasons, raw, observed,
        )
    ]
    with csv_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        if tuple(next(reader, ())) != ORIGIN_COLUMNS:
            raise ValueError("RV2 origin CSV schema mismatch")
        for actual, expected in zip_longest(reader, _origin_rows(frame, expected_origins)):
            if actual is None or expected is None or tuple(actual) != expected:
                raise ValueError("RV2 origin CSV candidate or sample alignment mismatch")

    targets = candidates[eligible]
    context = context[eligible]
    sequences = context[:, 1:, :]
    flat = sequences.reshape(len(targets), len(FLAT_FEATURE_NAMES))
    load = context[:, :, 0]
    xgb_stats = (
        load[:, -6:].mean(axis=1),
        load[:, -24:].std(axis=1, ddof=0),
        load[:, -1] - load[:, 0],
    )
    expected_arrays = {
        "schema_version": np.asarray(RV2_VERSION, dtype=np.uint8),
        "target_row": targets,
        "x_lstm": sequences,
        "x_flat": flat,
        "x_xgb": np.column_stack((flat, *xgb_stats)),
        "y_true_mw": frame.load.to_numpy(dtype=np.float64)[targets],
        "var_row": np.arange(VAR_START_ROW, VAR_END_ROW + 1, dtype=np.int64),
        "var_train_levels": extract_var_train_levels(frame),
    }
    shapes = {}
    with npz_path.open("rb") as stream:
        with ZipFile(stream) as archive:
            if sorted(archive.namelist()) != sorted(f"{key}.npy" for key in ARRAY_KEYS):
                raise ValueError("RV2 NPZ keys are missing, extra or duplicated")
        stream.seek(0)
        with np.load(stream, allow_pickle=False) as archive:
            for key, expected in expected_arrays.items():
                actual = archive[key]
                if actual.dtype != expected.dtype or actual.shape != expected.shape:
                    raise ValueError(f"RV2 NPZ dtype or shape mismatch: {key}")
                if actual.dtype.kind == "f" and not np.isfinite(actual).all():
                    raise ValueError(f"RV2 NPZ nonfinite values: {key}")
                if not np.array_equal(actual, expected):
                    raise ValueError(f"RV2 NPZ source or sample alignment mismatch: {key}")
                shapes[key] = (actual.shape, str(actual.dtype))
    return shapes
