import numpy as np
import pandas as pd
import pytest

from practice_2.analysis import forecasting
from practice_2.analysis import (
    evaluate_forecast,
    forecast_model,
    residual_diagnostics,
    seasonal_naive_forecast,
    validate_forecast_alignment,
)


def test_e05_seasonal_naive_forecast_repeats_available_seasonal_history():
    train = pd.Series(
        np.arange(1, 13, dtype=float),
        index=pd.date_range("2000-01-01", periods=12, freq="MS"),
    )
    forecast_index = pd.date_range("2001-01-01", periods=15, freq="MS")

    forecast = seasonal_naive_forecast(train, forecast_index, seasonal_period=12)

    assert forecast.index.equals(forecast_index)
    assert forecast.tolist() == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 1.0, 2.0, 3.0]


def test_e05_forecast_metrics_require_exact_index_alignment():
    actual = pd.Series([10.0, 20.0], index=pd.date_range("2000-01-01", periods=2, freq="MS"))
    forecast = pd.Series([8.0, 24.0], index=pd.date_range("2000-02-01", periods=2, freq="MS"))

    with pytest.raises(ValueError):
        validate_forecast_alignment(actual, forecast)


def test_e05_forecast_metrics_are_calculated_on_aligned_observations():
    index = pd.date_range("2000-01-01", periods=2, freq="MS")
    actual = pd.Series([10.0, 20.0], index=index)
    forecast = pd.Series([8.0, 24.0], index=index)

    metrics = dict(zip(evaluate_forecast(actual, forecast)["metric"], evaluate_forecast(actual, forecast)["value"]))

    assert metrics["MAE"] == pytest.approx(3.0)
    assert metrics["RMSE"] == pytest.approx(np.sqrt(10))
    assert metrics["MAPE"] == pytest.approx(20.0)


def test_e05_residual_diagnostics_records_requested_lags():
    residuals = pd.Series(np.sin(np.arange(60, dtype=float)))

    diagnostics = residual_diagnostics(residuals, lags=(12, 24), model_df=2)

    assert diagnostics["lag"].tolist() == [12, 24]
    assert {"lb_stat", "lb_pvalue", "alpha", "decision"}.issubset(diagnostics.columns)


def test_e05_forecast_model_uses_requested_evaluation_index():
    class DummyResult:
        def forecast(self, steps):
            return np.arange(steps, dtype=float)

    forecast_index = pd.date_range("2000-01-01", periods=3, freq="MS")

    forecast = forecast_model(DummyResult(), forecast_index, "candidate")

    assert forecast.index.equals(forecast_index)
    assert forecast.name == "candidate"


def test_e05_sarimax_helper_preserves_explicit_fit_constraints(monkeypatch):
    captured = {}

    class DummyModel:
        def fit(self, disp):
            captured["disp"] = disp
            return "fitted"

    def fake_sarimax(series, **kwargs):
        captured["series"] = series
        captured.update(kwargs)
        return DummyModel()

    monkeypatch.setattr(forecasting, "SARIMAX", fake_sarimax)
    series = pd.Series([1.0, 2.0, 3.0], index=pd.date_range("2000-01-01", periods=3, freq="MS"))

    result = forecasting.fit_sarimax(
        series,
        order=(1, 1, 1),
        seasonal_order=(0, 1, 1, 12),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    assert result == "fitted"
    assert captured["enforce_stationarity"] is False
    assert captured["enforce_invertibility"] is False
    assert captured["disp"] is False
