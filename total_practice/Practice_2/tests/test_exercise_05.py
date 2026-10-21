from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_2.analysis.forecasting import (
    build_forecast_table,
    calculate_forecast_metrics,
    compute_residual_diagnostics,
    fit_arima_candidates,
    forecast_arima_candidates,
    largest_forecast_errors,
    seasonal_naive_forecast,
)
from practice_2.data.time_series_data import chronological_split, load_monthly_retail_sales


ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def e05_run():
    series = load_monthly_retail_sales(ROOT / "datasets" / "raw" / "a10.csv")
    train, test = chronological_split(series)
    candidates = pd.read_csv(ROOT / "outputs" / "results" / "arima_candidates.csv")
    fitted, fit_summary = fit_arima_candidates(train, candidates)
    residuals, diagnostics = compute_residual_diagnostics(fitted, lags=(12, 24))
    forecasts = forecast_arima_candidates(fitted, test.index)
    forecasts["Seasonal naive (12)"] = seasonal_naive_forecast(train, test.index, 12)
    forecast_table = build_forecast_table(test, forecasts)
    metrics = calculate_forecast_metrics(forecast_table)
    largest = largest_forecast_errors(forecast_table)
    return {
        "train": train,
        "test": test,
        "candidates": candidates,
        "fitted": fitted,
        "fit_summary": fit_summary,
        "residuals": residuals,
        "diagnostics": diagnostics,
        "forecasts": forecasts,
        "forecast_table": forecast_table,
        "metrics": metrics,
        "largest": largest,
    }


def test_e05_uses_e01_split_and_e04_candidates(e05_run):
    assert len(e05_run["train"]) == 163
    assert len(e05_run["test"]) == 41
    assert e05_run["train"].index.max() < e05_run["test"].index.min()
    assert e05_run["candidates"]["candidate"].tolist() == [
        "ARIMA(1,1,1)",
        "ARIMA(2,1,1)",
    ]
    assert (e05_run["candidates"]["d"] == 1).all()


def test_e05_fits_log_training_levels_without_double_differencing(e05_run):
    summary = e05_run["fit_summary"]
    assert (summary["n_train"] == 163).all()
    assert (summary["analysis_scale"] == "natural_log").all()
    assert (summary["d"] == 1).all()
    assert (summary["trend"] == "n").all()
    assert not summary["drift_included"].any()
    assert summary["converged"].all()
    assert (summary["warnings"] == "none").all()
    assert all(model.model.trend == "n" for model in e05_run["fitted"].values())
    assert all(int(model.nobs) == 163 for model in e05_run["fitted"].values())


def test_e05_residual_diagnostics_use_post_burn_in_values(e05_run):
    diagnostics = e05_run["diagnostics"]
    assert set(diagnostics["lag"]) == {12, 24}
    assert (diagnostics["burn_in"] == 1).all()
    assert (diagnostics["residual_observations"] == 162).all()
    assert (diagnostics["model_df"] == pd.Series([2, 2, 3, 3])).all()
    assert diagnostics["reject_no_autocorrelation"].all()
    assert not diagnostics["white_noise_supported"].any()


def test_e05_seasonal_naive_uses_training_history_only(e05_run):
    baseline = e05_run["forecasts"]["Seasonal naive (12)"]
    expected = np.resize(e05_run["train"].iloc[-12:].to_numpy(), len(e05_run["test"]))
    np.testing.assert_allclose(baseline.to_numpy(), expected)
    assert baseline.index.equals(e05_run["test"].index)


def test_e05_forecasts_align_with_full_test_horizon(e05_run):
    assert set(e05_run["forecasts"]) == {
        "ARIMA(1,1,1)",
        "ARIMA(2,1,1)",
        "Seasonal naive (12)",
    }
    assert all(len(forecast) == 41 for forecast in e05_run["forecasts"].values())
    assert all(
        forecast.index.equals(e05_run["test"].index)
        for forecast in e05_run["forecasts"].values()
    )
    assert len(e05_run["forecast_table"]) == 3 * 41


def test_e05_metrics_and_largest_errors_are_derived_from_aligned_table(e05_run):
    metrics = e05_run["metrics"]
    largest = e05_run["largest"]
    assert set(metrics["model"]) == set(e05_run["forecasts"])
    assert set(largest["model"]) == set(e05_run["forecasts"])
    assert (metrics[["mae", "rmse", "mape_percent"]] > 0).all().all()
    assert (largest["absolute_error"] > 0).all()


def test_e05_rejects_misaligned_forecast_index():
    actual_index = pd.date_range("2020-01-01", periods=3, freq="MS")
    forecast_index = pd.date_range("2020-02-01", periods=3, freq="MS")
    actual = pd.Series([1.0, 2.0, 3.0], index=actual_index)
    forecast = pd.Series([1.0, 2.0, 3.0], index=forecast_index)
    with pytest.raises(ValueError, match="does not match"):
        build_forecast_table(actual, {"model": forecast})


def test_e05_rejects_zero_actual_for_mape():
    forecast_table = pd.DataFrame(
        {
            "model": ["model"],
            "timestamp": [pd.Timestamp("2020-01-01")],
            "actual": [0.0],
            "forecast": [1.0],
            "error": [-1.0],
            "absolute_error": [1.0],
        }
    )
    with pytest.raises(ValueError, match="MAPE"):
        calculate_forecast_metrics(forecast_table)
