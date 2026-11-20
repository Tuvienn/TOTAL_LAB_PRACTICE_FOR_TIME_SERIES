from __future__ import annotations

import csv
from contextlib import contextmanager
from io import BytesIO, StringIO
from types import SimpleNamespace
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest

from practice_4.data import features
from practice_4.data.features import (
    FLAT_FEATURE_NAMES,
    PREPARED_COLUMNS,
    SCALED_COLUMNS,
    XGB_FEATURE_NAMES,
    classify_origin,
    extract_var_train_levels,
    feature_views,
    load_prepared_prefix,
)


@pytest.fixture
def ramp():
    levels = np.arange(30, dtype=np.float64)[:, None] + [0, 100, 200, 300]
    raw = levels[:, 0].copy()
    raw[25] = 12345
    return levels, raw


def test_ramp_order_statistics_and_raw_label(ramp):
    levels, raw = ramp
    origin = classify_origin(levels, 25, raw[25], True)
    sequences, flat, xgb = feature_views(levels, [25, 26])
    expected = np.arange(1, 25)[:, None] + [0, 100, 200, 300]

    assert origin.eligible
    assert (origin.target_row, origin.origin_row, origin.context_start_row) == (25, 24, 0)
    assert origin.y_true_mw == 12345 and origin.y_true_mw != levels[25, 0]
    assert SCALED_COLUMNS == ("load_input_scaled", "temp_scaled", "humidity_scaled", "wind_speed_scaled")
    assert FLAT_FEATURE_NAMES == tuple(
        f"lag{lag:02d}_{variable}"
        for lag in range(23, -1, -1)
        for variable in ("load", "temperature", "humidity", "wind_speed")
    )
    assert XGB_FEATURE_NAMES == (*FLAT_FEATURE_NAMES, "mean6h", "std24h", "trend24h")
    assert (sequences.shape, flat.shape, xgb.shape) == ((2, 24, 4), (2, 96), (2, 99))
    assert all(view.dtype == np.float64 for view in (sequences, flat, xgb))
    np.testing.assert_array_equal(sequences[0], expected)
    np.testing.assert_array_equal(sequences[1], expected + 1)
    np.testing.assert_array_equal(flat[0], expected.ravel())
    np.testing.assert_array_equal(xgb[:, :96], flat)
    np.testing.assert_allclose(xgb[0, 96:], [21.5, np.sqrt(575 / 12), 24], rtol=1e-14, atol=0)


def test_target_weather_and_future_perturbations(ramp):
    levels, raw = ramp
    changed = levels.copy()
    changed[25, 1:] = [np.nan, np.inf, -100_000]
    changed[26:] = np.nan

    assert classify_origin(changed, 25, raw[25], True) == classify_origin(levels, 25, raw[25], True)
    for actual, expected in zip(feature_views(changed, [25]), feature_views(levels, [25])):
        np.testing.assert_array_equal(actual, expected)


def test_warmup_and_target_split_boundaries():
    levels = np.repeat(np.arange(29_804, dtype=np.float64)[:, None], 4, axis=1)
    for target in (0, 24, 29_803):
        with pytest.raises(ValueError, match="outside"):
            classify_origin(levels, target, 1.0, True)
        with pytest.raises(ValueError, match="outside"):
            feature_views(levels, [target])

    assert classify_origin(levels, 25, 1.0, True).split == "train"
    assert classify_origin(levels, 24_543, 1.0, True).split == "train"
    first_validation = classify_origin(levels, 24_544, 1.0, True)
    assert (first_validation.split, first_validation.origin_row, first_validation.context_start_row) == (
        "validation", 24_543, 24_519,
    )
    assert classify_origin(levels, 29_802, 1.0, True).split == "validation"
    sequences, _, xgb = feature_views(levels, [24_544, 24_545])
    np.testing.assert_array_equal(sequences[0, :, 0], np.arange(24_520, 24_544))
    assert sequences[1, -1, 0] == 24_544
    assert xgb[0, -1] == 24


@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_missing_truth_precedence_and_oldest_context_gate(ramp, bad):
    levels, raw = ramp
    missing = classify_origin(levels, 25, np.nan, False)
    assert (missing.context_finite, missing.eligible, missing.exclusion_reason, missing.y_true_mw) == (
        True, False, "missing_truth", None,
    )
    levels[0, 2] = bad
    missing = classify_origin(levels, 25, np.nan, False)
    assert (missing.context_finite, missing.eligible, missing.exclusion_reason) == (False, False, "missing_truth")
    observed = classify_origin(levels, 25, raw[25], True)
    assert (observed.eligible, observed.exclusion_reason, observed.y_true_mw) == (False, "invalid_context", raw[25])
    with pytest.raises(ValueError, match="finite common context"):
        feature_views(levels, [25])


@pytest.mark.parametrize(("truth", "observed"), [(np.nan, True), (np.inf, True), (150.0, False), (np.inf, False)])
def test_inconsistent_raw_truth_is_a_contract_error(ramp, truth, observed):
    levels, _ = ramp
    with pytest.raises(ValueError, match="mask"):
        classify_origin(levels, 25, truth, observed)


@pytest.fixture
def var_frame():
    row = np.arange(24_545, dtype=np.float64)
    frame = pd.DataFrame({
        "timestamp_utc": pd.date_range("2014-12-31T23:00:00+00:00", periods=len(row), freq="h"),
        "load": row,
        "load_input": row,
        "load_observed": True,
    })
    frame.loc[:31, "load_observed"] = False
    frame.loc[:31, "load"] = np.nan
    for variable, column in enumerate(SCALED_COLUMNS):
        frame[column] = row + variable * 100_000
    frame.loc[24_544, list(SCALED_COLUMNS)] = np.nan
    return frame


def test_extract_exact_var_training_block(var_frame):
    levels = extract_var_train_levels(var_frame)
    assert levels.shape == (9_271, 4)
    assert levels.dtype == np.float64
    assert var_frame.timestamp_utc.iloc[15_273].isoformat() == "2016-09-28T08:00:00+00:00"
    assert var_frame.timestamp_utc.iloc[24_543].isoformat() == "2017-10-19T14:00:00+00:00"
    expected = np.arange(15_273, 24_544)[:, None] + np.arange(4) * 100_000
    np.testing.assert_array_equal(levels, expected)


@pytest.mark.parametrize("defect", ["timeline", "unobserved", "working_load", "nonfinite", "excluded_count"])
def test_reject_invalid_var_block(var_frame, defect):
    if defect == "timeline":
        var_frame.loc[20_000, "timestamp_utc"] = var_frame.loc[20_001, "timestamp_utc"]
    elif defect == "unobserved":
        var_frame.loc[15_273, "load_observed"] = False
    elif defect == "working_load":
        var_frame.loc[24_543, "load_input"] += 1
    elif defect == "nonfinite":
        var_frame.loc[24_543, "wind_speed_scaled"] = np.inf
    else:
        var_frame.loc[32, "load_observed"] = False
    with pytest.raises(ValueError, match="timeline|VAR"):
        extract_var_train_levels(var_frame)


@pytest.fixture
def prepared_fixture(monkeypatch):
    monkeypatch.setattr(features, "TRAIN_ROWS", 2)
    monkeypatch.setattr(features, "PREFIX_ROWS", 4)
    hours = pd.date_range("2017-01-01", periods=4, freq="h", tz="UTC")
    splits = {
        "train": {"start_utc": hours[0].isoformat(), "end_utc": hours[1].isoformat()},
        "validation": {"start_utc": hours[2].isoformat(), "end_utc": hours[3].isoformat()},
    }
    counts = {
        split: {
            "rows": 2, "missing_truth": 0, "missing_working_load": 0, "locf_filled": 0,
            "flags": {name: 0 for name in features.FLAG_COLUMNS},
        }
        for split in splits
    }
    row = ["10000", "280", "90", "2", "True", "10000"] + ["False"] * 8 + ["1", "2", "3", "4"]
    lines = [",".join(PREPARED_COLUMNS), *(",".join([time.isoformat(), *row]) for time in hours)]
    return lines, splits, counts


def _prepared_stream(lines, suffix=b""):
    content = ("\n".join(lines) + "\n").encode("utf-8") + suffix
    return SimpleNamespace(open=lambda *args, **kwargs: BytesIO(content))


def test_accept_prepared_schema_and_counts(prepared_fixture):
    lines, splits, counts = prepared_fixture
    frame = load_prepared_prefix(_prepared_stream(lines), splits, counts)
    assert tuple(frame.columns) == PREPARED_COLUMNS
    assert frame.timestamp_utc.iloc[2].isoformat() == splits["validation"]["start_utc"]


@pytest.mark.parametrize("defect", ["header", "width", "short", "timestamp", "mask", "counts", "suffix"])
def test_reject_bad_prepared_prefix(prepared_fixture, defect):
    lines, splits, counts = prepared_fixture
    suffix = b""
    if defect == "header":
        lines[0] = lines[0].replace("load_observed", "unknown")
    elif defect == "width":
        lines[1] += ",extra"
    elif defect == "short":
        lines.pop()
    elif defect == "timestamp":
        lines[2] = lines[1]
    elif defect == "mask":
        lines[1] = lines[1].replace("10000,280", ",280")
    elif defect == "counts":
        counts["validation"]["locf_filled"] = 1
    else:
        suffix = b"\xff"
    with pytest.raises(ValueError, match="schema|row count|timeline|mask|count mismatch|after the D02 prepared prefix"):
        load_prepared_prefix(_prepared_stream(lines, suffix), splits, counts)


class MemoryArtifact:
    def __init__(self):
        self.data = b""

    @contextmanager
    def open(self, mode="r", *, encoding="utf-8", newline=None):
        if "b" in mode:
            stream = BytesIO(self.data)
        else:
            stream = StringIO(self.data.decode(encoding), newline=newline)
        yield stream
        self.data = stream.getvalue() if "b" in mode else stream.getvalue().encode(encoding)


@pytest.fixture
def aligned_fixture(monkeypatch):
    row = np.arange(60, dtype=np.float64)
    times = pd.date_range("2017-01-01", periods=len(row), freq="h", tz="UTC")
    monkeypatch.setattr(features, "TRAIN_ROWS", 32)
    monkeypatch.setattr(features, "PREFIX_ROWS", 60)
    monkeypatch.setattr(features, "VAR_START_ROW", 0)
    monkeypatch.setattr(features, "VAR_END_ROW", 4)
    monkeypatch.setattr(features, "VAR_START_UTC", times[0].isoformat())
    monkeypatch.setattr(features, "VAR_END_UTC", times[4].isoformat())
    monkeypatch.setattr(features, "VAR_EARLIER_OBSERVED", 0)

    frame = pd.DataFrame({"timestamp_utc": times, "load": row + 10_000.125, "load_observed": True})
    frame["load_input"] = frame.load
    for index, column in enumerate(SCALED_COLUMNS):
        frame[column] = row + 100 * index
    frame.loc[29, "load"] = np.nan
    frame.loc[29, "load_observed"] = False
    frame.loc[5, SCALED_COLUMNS[0]] = np.nan
    origins, counts = features.align_origins(frame)
    csv_path = MemoryArtifact()
    npz_path = MemoryArtifact()
    features.stage_aligned_inputs(frame, origins, csv_path, npz_path)
    return frame, counts, csv_path, npz_path


def test_rv2_roundtrip_and_boundary_carry(aligned_fixture):
    frame, counts, csv_path, npz_path = aligned_fixture
    assert counts == {
        "train": {"n_considered": 7, "n_missing_excluded": 1, "n_input_excluded": 5, "n_eligible": 1},
        "validation": {"n_considered": 28, "n_missing_excluded": 0, "n_input_excluded": 0, "n_eligible": 28},
    }
    shapes = features.validate_aligned_inputs(frame, csv_path, npz_path)
    assert shapes["x_lstm"] == ((29, 24, 4), "float64")
    assert shapes["x_flat"] == ((29, 96), "float64")
    assert shapes["x_xgb"] == ((29, 99), "float64")
    assert shapes["schema_version"] == ((), "uint8")
    with csv_path.open() as stream:
        reader = csv.DictReader(stream)
        assert tuple(reader.fieldnames) == features.ORIGIN_COLUMNS
        rows = {int(row["target_row"]): row for row in reader}
    assert list(rows) == list(range(25, 60))
    assert (rows[29]["exclusion_reason"], rows[29]["context_finite"], rows[29]["y_true_mw"]) == (
        "missing_truth", "False", "",
    )
    assert (rows[30]["split"], rows[30]["origin_row"], rows[30]["context_start_row"]) == (
        "train", "29", "5",
    )
    assert rows[30]["exclusion_reason"] == "invalid_context"
    assert rows[30]["sample_index"] == ""
    assert float(rows[30]["y_true_mw"]) == frame.load.iloc[30]
    assert rows[31]["sample_index"] == "0"
    assert (rows[32]["split"], rows[32]["origin_row"], rows[32]["context_start_row"], rows[32]["sample_index"]) == (
        "validation", "31", "7", "1",
    )
    with np.load(BytesIO(npz_path.data), allow_pickle=False) as archive:
        np.testing.assert_array_equal(archive["target_row"], np.arange(31, 60))
        np.testing.assert_array_equal(archive["var_row"], np.arange(5))
        np.testing.assert_array_equal(archive["var_train_levels"], frame.loc[:4, list(SCALED_COLUMNS)])
        np.testing.assert_array_equal(archive["x_lstm"][0, :, 0], np.arange(7, 31))
        np.testing.assert_array_equal(archive["y_true_mw"], frame.load.iloc[31:])


@pytest.mark.parametrize("defect", ["header", "duplicate", "missing", "sample_index", "timestamp", "test"])
def test_rv2_rejects_malformed_origin_csv(aligned_fixture, defect):
    frame, _, csv_path, npz_path = aligned_fixture
    rows = list(csv.reader(StringIO(csv_path.data.decode("utf-8"))))
    if defect == "header":
        rows[0][1] = rows[0][0]
    elif defect == "duplicate":
        rows.insert(2, rows[1])
    elif defect == "missing":
        rows.pop()
    elif defect == "sample_index":
        rows[-1][-1] = "0"
    elif defect == "timestamp":
        rows[-1][5] = rows[-1][4]
    else:
        rows[-1][6] = "test"
    stream = StringIO()
    csv.writer(stream).writerows(rows)
    csv_path.data = stream.getvalue().encode("utf-8")
    with pytest.raises(ValueError, match="RV2 origin CSV"):
        features.validate_aligned_inputs(frame, csv_path, npz_path)


@pytest.mark.parametrize(
    ("defect", "error"),
    [
        ("extra", "keys"), ("missing", "keys"), ("duplicate", "keys"), ("dtype", "dtype"),
        ("shape", "shape"), ("pickle", "allow_pickle=False"), ("nonfinite", "nonfinite"),
        ("lag", "alignment"), ("stat", "alignment"), ("truth", "alignment"), ("var", "alignment"),
    ],
)
def test_rv2_rejects_malformed_or_misaligned_npz(aligned_fixture, defect, error):
    frame, _, csv_path, npz_path = aligned_fixture
    stream = BytesIO(npz_path.data)
    if defect == "duplicate":
        with ZipFile(stream, "a") as archive, pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("target_row.npy", archive.read("target_row.npy"))
    else:
        with np.load(stream, allow_pickle=False) as archive:
            arrays = {key: archive[key] for key in archive.files}
        if defect == "extra":
            arrays["extra"] = np.array(0)
        elif defect == "missing":
            del arrays["schema_version"]
        elif defect == "dtype":
            arrays["target_row"] = arrays["target_row"].astype(np.int32)
        elif defect == "shape":
            arrays["x_lstm"] = arrays["x_lstm"][:, 1:]
        elif defect == "pickle":
            arrays["y_true_mw"] = arrays["y_true_mw"].astype(object)
        elif defect == "nonfinite":
            arrays["x_xgb"][0, -1] = np.nan
        elif defect == "lag":
            arrays["x_lstm"][0, 0, 0] += 1
        elif defect == "stat":
            arrays["x_xgb"][-1, -1] += 1
        elif defect == "truth":
            arrays["y_true_mw"][-1] += 1
        else:
            arrays["var_train_levels"][0, 0] += 1
        stream = BytesIO()
        np.savez(stream, **arrays)
    npz_path.data = stream.getvalue()
    with pytest.raises(ValueError, match=error):
        features.validate_aligned_inputs(frame, csv_path, npz_path)


def test_e02_rejects_empty_eligible_split(aligned_fixture):
    frame, _, _, _ = aligned_fixture
    frame.loc[30, SCALED_COLUMNS[0]] = np.nan
    with pytest.raises(ValueError, match="Empty eligible split"):
        features.align_origins(frame)
