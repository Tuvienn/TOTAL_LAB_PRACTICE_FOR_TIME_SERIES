import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3.analysis.evaluation import (
    ONE_STEP_COLUMNS,
    RECURSIVE_COLUMNS,
    atomic_write_csv,
    attach_error_columns,
    build_one_step_metrics,
    build_recursive_metrics,
    validate_one_step_predictions,
    validate_recursive_predictions,
)
from practice_3.visualization.forecast_evaluation import (
    _prepare_one_step_plot_data,
)


CANDIDATES = ["persistence", "seasonal_naive_24", "xgboost_tuned"]


def one_step_frame() -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    timestamps = pd.date_range("2024-01-01", periods=3, freq="h")
    records = []
    for offset, candidate in enumerate(CANDIDATES, start=1):
        records.append(
            pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "candidate": candidate,
                    "actual": [10.0, 20.0, 30.0],
                    "prediction": np.asarray([10.0, 20.0, 30.0]) + offset,
                    "forecast_protocol": "one_step_rolling_observed_history",
                }
            )
        )
    frame = attach_error_columns(pd.concat(records, ignore_index=True))
    return frame.loc[:, ONE_STEP_COLUMNS], timestamps


def recursive_frame() -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    origins = pd.date_range("2024-01-01 23:00:00", periods=2, freq="24h")
    records = []
    for candidate_index, candidate in enumerate(CANDIDATES, start=1):
        for origin in origins:
            for horizon in range(1, 25):
                actual = float(100 + horizon)
                records.append(
                    {
                        "forecast_origin": origin,
                        "horizon": horizon,
                        "target_timestamp": origin + pd.Timedelta(hours=horizon),
                        "candidate": candidate,
                        "actual": actual,
                        "prediction": actual + candidate_index * horizon,
                        "forecast_protocol": "recursive_24_hour",
                    }
                )
    frame = attach_error_columns(pd.DataFrame(records))
    return frame.loc[:, RECURSIVE_COLUMNS], origins


def test_one_step_schema_common_timestamps_and_metrics() -> None:
    frame, timestamps = one_step_frame()
    validate_one_step_predictions(frame, CANDIDATES, timestamps)
    metrics = build_one_step_metrics(frame, CANDIDATES)
    assert metrics["status"] == "PASS"
    assert metrics["candidate_metrics"][0]["mae"] == pytest.approx(1.0)
    assert metrics["candidate_metrics"][0]["rmse"] == pytest.approx(1.0)
    assert metrics["candidate_metrics"][0]["n_observations"] == 3


def test_one_step_rejects_candidate_timestamp_mismatch() -> None:
    frame, timestamps = one_step_frame()
    changed = frame.drop(index=frame.index[-1]).reset_index(drop=True)
    with pytest.raises(ValueError, match="identical timestamps"):
        validate_one_step_predictions(changed, CANDIDATES, timestamps)


def test_recursive_schema_complete_horizons_and_direct_pooled_rmse() -> None:
    frame, origins = recursive_frame()
    validate_recursive_predictions(frame, CANDIDATES, origins)
    metrics = build_recursive_metrics(frame, CANDIDATES)
    persistence = metrics["candidate_metrics"][0]
    expected_rmse = float(np.sqrt(np.mean(np.square(np.tile(np.arange(1, 25), 2)))))
    assert len(persistence["per_horizon"]) == 24
    assert persistence["per_horizon"][0]["n_origins"] == 2
    assert persistence["pooled"]["pooled_rmse"] == pytest.approx(expected_rmse)
    assert persistence["pooled"]["n_predictions"] == 48
    assert persistence["pooled"]["n_origins"] == 2


def test_recursive_rejects_partial_origin_block() -> None:
    frame, origins = recursive_frame()
    changed = frame.drop(index=frame.index[23]).reset_index(drop=True)
    with pytest.raises(ValueError, match="horizons 1..24"):
        validate_recursive_predictions(changed, CANDIDATES, origins)


def test_non_finite_predictions_are_rejected() -> None:
    frame, _timestamps = one_step_frame()
    changed = frame.copy()
    changed.loc[0, "prediction"] = np.nan
    with pytest.raises(ValueError, match="finite"):
        attach_error_columns(changed)


def test_atomic_csv_round_trip(tmp_path: Path) -> None:
    frame, _timestamps = one_step_frame()
    output = tmp_path / "predictions.csv"
    atomic_write_csv(frame, output)
    restored = pd.read_csv(output)
    assert restored.columns.tolist() == ONE_STEP_COLUMNS
    assert len(restored) == len(frame)


def test_one_step_plot_preserves_ineligible_timestamp_gaps() -> None:
    frame, timestamps = one_step_frame()
    changed = frame.loc[~frame["timestamp"].eq(timestamps[1])].copy()
    actual, predictions = _prepare_one_step_plot_data(changed)
    assert actual.index.equals(timestamps)
    assert predictions.index.equals(timestamps)
    assert pd.isna(actual.loc[timestamps[1]])
    assert predictions.loc[timestamps[1]].isna().all()


def test_notebook_does_not_execute_phase_07_logic() -> None:
    project_root = Path(__file__).resolve().parents[1]
    notebook = json.loads(
        (project_root / "notebooks/Practice_3_present.ipynb").read_text(
            encoding="utf-8"
        )
    )
    code = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    assert "run_final_evaluation" not in code
    assert ".fit(" not in code
    assert ".predict(" not in code
