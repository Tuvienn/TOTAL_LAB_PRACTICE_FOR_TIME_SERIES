from pathlib import Path

import numpy as np
from statsmodels.tsa.stattools import pacf

from practice_1.analysis.acf_pacf import compute_acf_table, compute_pacf_table
from practice_1.data.air_passengers import load_air_passengers


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "air_passengers.csv"


def test_acf_and_pacf_cover_lags_zero_through_forty() -> None:
    series = load_air_passengers(RAW_PATH)["passengers_thousands"]
    acf_table = compute_acf_table(series, max_lag=40, alpha=0.05)
    pacf_table = compute_pacf_table(series, max_lag=40, alpha=0.05, method="ywm")
    expected_lags = list(range(41))
    assert acf_table["lag"].tolist() == expected_lags
    assert pacf_table["lag"].tolist() == expected_lags
    assert acf_table.loc[0, "acf"] == 1.0
    assert pacf_table.loc[0, "pacf"] == 1.0
    expected_pacf = pacf(series.to_numpy(), nlags=40, method="ywm")
    assert np.allclose(pacf_table["pacf"].to_numpy(), expected_pacf)
    assert acf_table[["acf", "lower_ci", "upper_ci"]].notna().all().all()
    assert pacf_table[["pacf", "lower_ci", "upper_ci"]].notna().all().all()

