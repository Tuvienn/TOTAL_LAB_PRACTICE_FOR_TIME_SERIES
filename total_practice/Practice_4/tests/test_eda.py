import hashlib
import io
from pathlib import Path

import pandas as pd
import pytest

from practice_4.analysis.eda import gap_runs, load_train, profiles, validate_train
from practice_4.visualization.plots import render


def boundary(count, start="2020-01-01T00:00:00+00:00"):
    timestamps = pd.date_range(start, periods=count, freq="h")
    return {"start_row": 0, "end_row": count - 1, "row_count": count, "start_utc": timestamps[0].isoformat(), "end_utc": timestamps[-1].isoformat()}


def test_loader_never_requests_held_out(monkeypatch):
    train = boundary(24544)
    class Sentinel:
        def __enter__(self):
            self.calls = 0
            return self
        def __exit__(self, *args):
            return False
        def __iter__(self):
            return self
        def __next__(self):
            self.calls += 1
            if self.calls == 1:
                return "timestamp_utc,load,temp,humidity,wind_speed,load_observed\n"
            if self.calls > 24545:
                raise AssertionError("held-out row accessed")
            timestamp = pd.Timestamp(train["start_utc"]) + pd.Timedelta(hours=self.calls - 2)
            return f"{timestamp.isoformat()},1,2,3,4,True\n"
    monkeypatch.setattr(Path, "open", lambda *a, **k: Sentinel())
    frame = load_train(Path("synthetic"), train)
    assert len(frame) == 24544 and frame["timestamp_utc"].iloc[-1].isoformat() == train["end_utc"]
    changed = frame.copy()
    changed.loc[24543, "timestamp_utc"] += pd.Timedelta(hours=1)
    with pytest.raises(ValueError): validate_train(changed, train)


def test_dst_profiles_preserve_utc_observations():
    def counts(start, n):
        ts = pd.date_range(start, periods=n, freq="h", tz="UTC")
        frame = pd.DataFrame({"timestamp_utc": ts, "load": range(n)})
        return {row["group"]: row["size"] for row in profiles(frame)["hour"]}
    assert counts("2021-03-28T00:00:00Z", 4)[2] != 1
    assert counts("2021-10-31T00:00:00Z", 4)[2] == 2


def test_gaps_censored_and_missing_not_zero():
    frame = pd.DataFrame({"timestamp_utc": pd.date_range("2020-01-01", periods=6, freq="h", tz="UTC"), "load": [None, None, 3, None, 5, None], "load_observed": [False, False, True, False, True, False]})
    gaps = gap_runs(frame)
    assert [g["length_hours"] for g in gaps] == [2, 1, 1]
    assert gaps[0]["left_censored"] and gaps[-1]["right_censored"]
    assert frame["load"].isna().sum() == 4


def test_figures_deterministic(monkeypatch):
    from matplotlib.figure import Figure

    outputs = []
    original = Figure.savefig
    def capture(fig, path, **kwargs):
        stream = io.BytesIO()
        original(fig, stream, format="png", **kwargs)
        outputs.append(hashlib.sha256(stream.getvalue()).digest())
    monkeypatch.setattr(Figure, "savefig", capture)
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)
    ts = pd.date_range("2020-01-01", periods=48, freq="h", tz="UTC")
    frame = pd.DataFrame({"timestamp_utc": ts, "load": range(48), "temp": range(48), "humidity": range(48), "wind_speed": range(48), "load_observed": [True] * 48})
    variables = ["load", "temp", "humidity", "wind_speed"]
    summary = {"observed": 48, "missing": 0, "gaps": [], "profiles": profiles(frame), "pair_counts": {a: {b: 48 for b in variables} for a in variables}, "correlations": {a: {b: 1.0 for b in variables} for a in variables}, "acf": [1, .5], "pacf": [1, .5]}
    one = render(frame, summary, Path("one"))
    two = render(frame, summary, Path("two"))
    assert len(one) == 6
    assert outputs[:6] == outputs[6:]
