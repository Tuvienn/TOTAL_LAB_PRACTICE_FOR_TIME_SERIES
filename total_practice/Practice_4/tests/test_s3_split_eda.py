from __future__ import annotations

import json

import pandas as pd
import pytest

from practice_4.analysis.eda import load_train_only, summarize_train_eda
from practice_4.data.splitting import partition, split_hash
from practice_4.runtime import PRACTICE_ROOT, read_file_map


def test_s3_synthetic_chronological_partition_and_cv():
    idx = pd.date_range("2012-01-01T00:00:00Z", periods=2000, freq="h")
    manifest = partition(idx, "canonical.csv", "a" * 64, cv_folds=3)
    s = manifest["splits"]
    assert s["train"]["row_count"] + s["validation"]["row_count"] + s["test"]["row_count"] == 2000
    assert s["train"]["end_row"] + 1 == s["validation"]["start_row"]
    assert s["validation"]["end_row"] + 1 == s["test"]["start_row"]
    assert len(manifest["train_expanding_cv_folds"]) == 3
    for fold in manifest["train_expanding_cv_folds"]:
        assert fold["train_end_row"] < fold["val_start_row"]
        assert fold["val_end_row"] <= s["train"]["end_row"]
    assert split_hash(manifest) == manifest["split_sha256"]


def test_s3_eda_rejects_out_of_train_data():
    split = json.loads((PRACTICE_ROOT / "datasets/processed/split_manifest.json").read_text(encoding="utf-8"))
    canonical = PRACTICE_ROOT / "datasets/processed/canonical_hourly.csv"
    df_extra = pd.read_csv(canonical, nrows=split["splits"]["train"]["row_count"] + 5)
    df_extra["timestamp_utc"] = pd.to_datetime(df_extra["timestamp_utc"], utc=True)
    with pytest.raises(ValueError):
        summarize_train_eda(df_extra, split["splits"]["train"])


def test_s3_real_split_and_eda_outputs():
    split_path = PRACTICE_ROOT / "datasets/processed/split_manifest.json"
    assert split_path.exists()
    split = json.loads(split_path.read_text(encoding="utf-8"))
    assert split["schema_version"] == "2"
    assert split["total_rows"] == 26304
    assert split_hash(split) == split["split_sha256"]
    s = split["splits"]
    assert abs(s["train"]["row_count"] / 26304 - 0.70) < 0.001
    assert abs(s["validation"]["row_count"] / 26304 - 0.15) < 0.001
    assert abs(s["test"]["row_count"] / 26304 - 0.15) < 0.001
    assert len(split["train_expanding_cv_folds"]) == 3

    for fig_name in (
        "eda_load_utc.png",
        "eda_seasonality_profiles.png",
        "eda_relationships.png",
        "eda_acf_pacf.png",
        "eda_distributions.png",
    ):
        p = PRACTICE_ROOT / "outputs/figures" / fig_name
        assert p.exists() and p.stat().st_size > 5000

    assert (PRACTICE_ROOT / "docs/results/eda_findings.md").exists()
    fmap = {r["path"]: r for r in read_file_map()}
    assert fmap["datasets/processed/split_manifest.json"]["existence"] == "EXISTING"
    assert fmap["docs/results/eda_findings.md"]["existence"] == "EXISTING"
