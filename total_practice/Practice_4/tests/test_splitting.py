import copy
import hashlib
import json

import pandas as pd
import pytest

from practice_4.data.splitting import partition, split_hash


def make(n):
    return partition(pd.date_range("2020-01-01", periods=n, freq="h", tz="UTC"), "canonical.csv", "a" * 64)


def test_floor_rounding_and_inclusive_boundaries():
    result = make(19)
    splits = result["splits"]
    assert [splits[k]["row_count"] for k in splits] == [13, 2, 4]
    assert [(splits[k]["start_row"], splits[k]["end_row"]) for k in splits] == [(0, 12), (13, 14), (15, 18)]
    assert splits["validation"]["start_utc"] == "2020-01-01T13:00:00+00:00"
    assert splits["test"]["end_utc"] == "2020-01-01T18:00:00+00:00"


def test_tiny_timeline_rejects_empty_splits():
    for n in range(7):
        with pytest.raises(ValueError):
            make(n)
    assert [s["row_count"] for s in make(7)["splits"].values()] == [4, 1, 2]


@pytest.mark.parametrize("values", [[], ["bad"], ["2020-01-01"], ["2020-01-01T00:00:00+01:00"], ["2020-01-01T00:00:00Z", "2020-01-01T00:00:00Z"], ["2020-01-01T00:00:00Z", "2020-01-01T02:00:00Z"], ["2020-01-01T01:00:00Z", "2020-01-01T00:00:00Z"]])
def test_invalid_timeline(values):
    with pytest.raises(ValueError):
        partition(values, "canonical.csv", "a" * 64)


def test_target_membership_and_causal_history_across_boundary():
    result = make(20)
    timeline = pd.date_range("2020-01-01", periods=20, freq="h", tz="UTC")
    for name in ("validation", "test"):
        start = result["splits"][name]["start_row"]
        origin = timeline[start - 1]
        target = origin + pd.Timedelta(hours=1)
        assert target.isoformat() == result["splits"][name]["start_utc"]
        assert all(t <= origin for t in timeline[start - 3:start])
        assert timeline[start - 1] < target


def test_self_hash_excludes_hash_and_detects_mutation():
    result = make(20)
    payload = {k: v for k, v in result.items() if k != "split_sha256"}
    expected = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    assert result["split_sha256"] == expected == split_hash(result)
    changed = copy.deepcopy(result)
    changed["splits"]["train"]["row_count"] += 1
    assert split_hash(changed) != expected
