from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3.analysis.evaluation import (
    build_multistep_prediction_frame,
    build_one_step_prediction_frame,
    calculate_multistep_metrics,
    calculate_one_step_metrics,
)
from practice_3.visualization.forecast_evaluation import (
    plot_multistep_error_by_horizon,
    plot_one_step_diagnostic_window,
    plot_one_step_full_test,
)


CANDIDATES = ["seasonal_naive_24", "xgboost_tuned"]


def build_one_step_predictions():
    timestamps = pd.date_range("2026-01-01", periods=4, freq="h")
    actual = np.asarray([10.0, 12.0, 14.0, 16.0])
    frames = []
    for candidate_id, prediction in (
        ("seasonal_naive_24", np.asarray([9.0, 11.0, 13.0, 15.0])),
        ("xgboost_tuned", np.asarray([10.0, 11.0, 15.0, 16.0])),
    ):
        frames.append(
            build_one_step_prediction_frame(
                timestamps,
                candidate_id,
                actual,
                prediction,
                "lag_only_p168",
            )
        )
    return pd.concat(frames, ignore_index=True)


def build_multistep_predictions():
    frames = []
    for origin_number, origin in enumerate(
        pd.to_datetime(["2026-01-01 23:00", "2026-01-02 23:00"])
    ):
        index = pd.date_range(
            origin + pd.Timedelta(hours=1),
            periods=3,
            freq="h",
        )
        actual = pd.Series(
            np.asarray([10.0, 20.0, 30.0]) + origin_number,
            index=index,
        )
        for candidate_id, offset in (
            ("seasonal_naive_24", 2.0),
            ("xgboost_tuned", 1.0),
        ):
            prediction = actual - offset * np.arange(1.0, 4.0)
            frames.append(
                build_multistep_prediction_frame(
                    origin,
                    candidate_id,
                    actual,
                    prediction,
                    "lag_only_p168",
                )
            )
    return pd.concat(frames, ignore_index=True)


def test_one_step_metrics_match_independent_calculation():
    predictions = build_one_step_predictions()
    result = calculate_one_step_metrics(predictions, CANDIDATES)

    assert result["population"]["rows_per_candidate"] == 4
    assert result["candidates"]["seasonal_naive_24"]["mae"] == 1.0
    assert result["candidates"]["seasonal_naive_24"]["rmse"] == 1.0
    assert result["candidates"]["xgboost_tuned"]["mae"] == 0.5
    assert result["candidates"]["xgboost_tuned"]["rmse"] == pytest.approx(
        np.sqrt(0.5)
    )


def test_one_step_rejects_candidate_population_mismatch():
    predictions = build_one_step_predictions()
    predictions = predictions.drop(predictions.index[-1])

    with pytest.raises(ValueError, match="timestamps differ"):
        calculate_one_step_metrics(predictions, CANDIDATES)


def test_multistep_metrics_include_per_horizon_and_pooled_values():
    predictions = build_multistep_predictions()
    result = calculate_multistep_metrics(
        predictions,
        CANDIDATES,
        horizon=3,
    )

    tuned = result["candidates"]["xgboost_tuned"]
    assert result["population"]["origin_count"] == 2
    assert tuned["n_predictions"] == 6
    assert [item["mae"] for item in tuned["per_horizon"]] == [
        1.0,
        2.0,
        3.0,
    ]
    assert tuned["pooled_mae"] == 2.0
    assert tuned["pooled_rmse"] == pytest.approx(np.sqrt(14.0 / 3.0))
    assert tuned["pooled_rmse"] != pytest.approx(
        np.mean([1.0, 2.0, 3.0])
    )


def test_multistep_rejects_incomplete_horizon():
    predictions = build_multistep_predictions()
    predictions = predictions.drop(predictions.index[-1])

    with pytest.raises(ValueError, match="incomplete horizon"):
        calculate_multistep_metrics(predictions, CANDIDATES, horizon=3)


def test_fixed_visualizations_are_created(tmp_path):
    one_step = build_one_step_predictions()
    multi_step = build_multistep_predictions()
    multi_metrics = calculate_multistep_metrics(
        multi_step,
        CANDIDATES,
        horizon=3,
    )
    full_path = tmp_path / "full.png"
    diagnostic_path = tmp_path / "diagnostic.png"
    horizon_path = tmp_path / "horizon.png"

    plot_one_step_full_test(one_step, "xgboost_tuned", full_path)
    plot_one_step_diagnostic_window(
        one_step,
        CANDIDATES,
        pd.Timestamp("2026-01-01 00:00"),
        pd.Timestamp("2026-01-01 03:00"),
        diagnostic_path,
    )
    plot_multistep_error_by_horizon(
        multi_metrics,
        CANDIDATES,
        horizon_path,
    )

    for path in (full_path, diagnostic_path, horizon_path):
        assert path.exists()
        assert path.stat().st_size > 0
