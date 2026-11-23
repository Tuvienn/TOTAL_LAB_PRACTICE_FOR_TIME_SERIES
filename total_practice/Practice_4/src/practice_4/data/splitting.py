from __future__ import annotations

import hashlib
import json
from typing import Any

import pandas as pd


def split_hash(manifest: dict[str, Any]) -> str:
    content = {key: value for key, value in manifest.items() if key != "split_sha256"}
    return hashlib.sha256(
        json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def build_expanding_cv_folds(train_rows: int, n_folds: int = 3, min_train_frac: float = 0.50) -> list[dict[str, int]]:
    if n_folds < 1:
        raise ValueError("n_folds must be >= 1")
    min_train = int(train_rows * min_train_frac)
    remaining = train_rows - min_train
    val_size = remaining // n_folds
    if val_size < 168:
        raise ValueError("Insufficient training rows for expanding-window CV folds")
    folds = []
    for k in range(n_folds):
        tr_end = min_train + k * val_size - 1
        va_start = tr_end + 1
        va_end = (va_start + val_size - 1) if k < n_folds - 1 else (train_rows - 1)
        folds.append(
            {
                "fold": k + 1,
                "train_start_row": 0,
                "train_end_row": tr_end,
                "val_start_row": va_start,
                "val_end_row": va_end,
                "val_rows": va_end - va_start + 1,
            }
        )
    return folds


def partition(
    timestamps,
    canonical_path: str,
    canonical_sha256: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    cv_folds: int = 3,
) -> dict[str, Any]:
    values = list(timestamps)
    if not values:
        raise ValueError("Empty timeline")
    index = pd.DatetimeIndex(pd.to_datetime(values, utc=True, errors="raise"))
    if not index.is_monotonic_increasing or not index.is_unique:
        raise ValueError("Timeline must be sorted and unique")
    if len(index) > 1 and not ((index[1:] - index[:-1]) == pd.Timedelta(hours=1)).all():
        raise ValueError("Timeline must be contiguous hourly")

    n = len(index)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    n_test = n - n_train - n_val
    if min(n_train, n_val, n_test) <= 0:
        raise ValueError("Each split requires at least one row")

    splits = {}
    start = 0
    for name, count in zip(("train", "validation", "test"), (n_train, n_val, n_test)):
        end = start + count - 1
        splits[name] = {
            "row_count": count,
            "start_row": start,
            "end_row": end,
            "start_utc": index[start].isoformat(),
            "end_utc": index[end].isoformat(),
        }
        start = end + 1

    folds = build_expanding_cv_folds(n_train, n_folds=cv_folds) if n_train >= 1000 else []
    result: dict[str, Any] = {
        "schema_version": "2",
        "canonical_path": canonical_path,
        "canonical_sha256": canonical_sha256,
        "total_rows": n,
        "frequency": "1h",
        "timezone": "UTC",
        "splits": splits,
        "train_expanding_cv_folds": folds,
    }
    result["split_sha256"] = split_hash(result)
    return result
