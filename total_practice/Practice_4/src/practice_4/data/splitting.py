from __future__ import annotations

import hashlib
import json

import pandas as pd


def split_hash(manifest: dict) -> str:
    content = {key: value for key, value in manifest.items() if key != "split_sha256"}
    return hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def partition(timestamps, canonical_path: str, canonical_sha256: str) -> dict:
    values = list(timestamps)
    if not values:
        raise ValueError("Empty timeline")
    parsed = []
    for value in values:
        try:
            timestamp = pd.Timestamp(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Invalid timestamp") from exc
        if pd.isna(timestamp) or timestamp.tzinfo is None or timestamp.utcoffset().total_seconds() != 0:
            raise ValueError("Timestamp must be valid UTC")
        parsed.append(timestamp.tz_convert("UTC"))
    index = pd.DatetimeIndex(parsed)
    if not index.is_monotonic_increasing or not index.is_unique:
        raise ValueError("Timeline must be sorted and unique")
    if len(index) > 1 and not ((index[1:] - index[:-1]) == pd.Timedelta(hours=1)).all():
        raise ValueError("Timeline must be contiguous hourly")
    n = len(index)
    counts = [n * 70 // 100, n * 15 // 100]
    counts.append(n - sum(counts))
    if min(counts) == 0:
        raise ValueError("Each split requires at least one row")
    splits = {}
    start = 0
    for name, count in zip(("train", "validation", "test"), counts):
        end = start + count - 1
        splits[name] = {"row_count": count, "start_row": start, "end_row": end, "start_utc": index[start].isoformat(), "end_utc": index[end].isoformat()}
        start = end + 1
    result = {"schema_version": "1", "canonical_path": canonical_path, "canonical_sha256": canonical_sha256, "total_rows": n, "frequency": "1h", "timezone": "UTC", "splits": splits}
    result["split_sha256"] = split_hash(result)
    return result
