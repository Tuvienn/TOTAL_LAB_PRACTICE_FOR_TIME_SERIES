import json
from pathlib import Path

import pandas as pd

from practice_1.data.air_passengers import calculate_sha256, load_air_passengers


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "datasets" / "raw" / "air_passengers.csv"
CONFIG_PATH = PROJECT_ROOT / "config" / "practice_1.json"


def test_raw_dataset_matches_approved_contract() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    before = RAW_PATH.read_bytes()
    frame = load_air_passengers(RAW_PATH)
    after = RAW_PATH.read_bytes()
    assert before == after
    assert calculate_sha256(RAW_PATH) == config["dataset"]["sha256"]
    assert len(frame) == 144
    assert frame.index[0] == pd.Timestamp("1949-01-01")
    assert frame.index[-1] == pd.Timestamp("1960-12-01")
    assert frame.index.freqstr == "MS"
    assert frame.index.is_monotonic_increasing
    assert not frame.index.has_duplicates
    assert frame.isna().sum().sum() == 0
    assert frame.columns.tolist() == ["passengers_thousands"]
