from collections.abc import Iterable

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX


def seasonal_naive_forecast(
    train: pd.Series,
    forecast_index: pd.Index,
    seasonal_period: int = 12,
) -> pd.Series:
    """Forecast by repeating the most recent seasonal cycle from available history."""
    _validate_series(train, "Training series")
    if not isinstance(seasonal_period, int) or seasonal_period < 1:
        raise ValueError("seasonal_period must be a positive integer")
    if len(train) < seasonal_period:
        raise ValueError("Training series is shorter than seasonal_period")
    _validate_forecast_index(forecast_index)

    history = train.astype(float).tolist()
    values = []
    for _ in forecast_index:
        value = history[-seasonal_period]
        values.append(value)
        history.append(value)
    return pd.Series(values, index=forecast_index, name="seasonal_naive_forecast")


def fit_arima(series: pd.Series, order: tuple[int, int, int]):
    """Fit one ARIMA candidate without suppressing fitting warnings."""
    _validate_series(series, "ARIMA input")
    _validate_order(order, "order")
    return ARIMA(series.astype(float), order=order).fit()


def fit_sarimax(
    series: pd.Series,
    order: tuple[int, int, int],
    seasonal_order: tuple[int, int, int, int],
    enforce_stationarity: bool = True,
    enforce_invertibility: bool = True,
):
    """Fit one SARIMAX candidate without suppressing fitting warnings."""
    _validate_series(series, "SARIMAX input")
    _validate_order(order, "order")
    _validate_seasonal_order(seasonal_order)
    return SARIMAX(
        series.astype(float),
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=enforce_stationarity,
        enforce_invertibility=enforce_invertibility,
    ).fit(disp=False)


def forecast_model(result, forecast_index: pd.Index, name: str) -> pd.Series:
    """Generate a forecast and assign the approved evaluation index."""
    _validate_forecast_index(forecast_index)
    values = np.asarray(result.forecast(steps=len(forecast_index)), dtype=float)
    if len(values) != len(forecast_index):
        raise ValueError("Model forecast length does not match forecast_index")
    return pd.Series(values, index=forecast_index, name=name)


def inverse_log_forecast(forecast: pd.Series) -> pd.Series:
    """Exponentiate a log-scale forecast without a bias correction."""
    _validate_series(forecast, "Log-scale forecast")
    return pd.Series(np.exp(forecast.to_numpy()), index=forecast.index, name=forecast.name)


def validate_forecast_alignment(actual: pd.Series, forecast: pd.Series) -> None:
    """Raise when forecast and actual values do not share the same complete index."""
    _validate_series(actual, "Actual series")
    _validate_series(forecast, "Forecast series")
    if not actual.index.equals(forecast.index):
        raise ValueError("Actual and forecast indices must match exactly")


def evaluate_forecast(actual: pd.Series, forecast: pd.Series) -> pd.DataFrame:
    """Calculate MAE, RMSE, and MAPE after verifying index alignment."""
    validate_forecast_alignment(actual, forecast)
    actual_values = actual.to_numpy(dtype=float)
    forecast_values = forecast.to_numpy(dtype=float)
    if (actual_values == 0).any():
        raise ValueError("MAPE is undefined when actual values contain zero")
    errors = actual_values - forecast_values
    metrics = {
        "MAE": np.abs(errors).mean(),
        "RMSE": np.sqrt(np.square(errors).mean()),
        "MAPE": (np.abs(errors / actual_values).mean()) * 100,
    }
    return pd.DataFrame({"metric": list(metrics), "value": list(metrics.values())})


def residual_summary(residuals: pd.Series) -> pd.DataFrame:
    """Return basic residual diagnostics that do not require a hypothesis test."""
    _validate_series(residuals, "Residual series")
    return pd.DataFrame(
        {
            "metric": ["residual_mean", "n_observations"],
            "value": [residuals.mean(), len(residuals)],
        }
    )


def residual_diagnostics(
    residuals: pd.Series,
    lags: Iterable[int] = (12, 24),
    model_df: int = 0,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Run Ljung-Box diagnostics with explicit model degrees of freedom."""
    _validate_series(residuals, "Residual series")
    if not isinstance(model_df, int) or model_df < 0:
        raise ValueError("model_df must be a non-negative integer")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    lag_values = list(lags)
    if not lag_values or any(not isinstance(lag, int) or lag <= model_df for lag in lag_values):
        raise ValueError("Each Ljung-Box lag must be an integer greater than model_df")
    if any(lag >= len(residuals) for lag in lag_values):
        raise ValueError("Each Ljung-Box lag must be shorter than the residual series")

    result = acorr_ljungbox(residuals, lags=lag_values, model_df=model_df, return_df=True)
    table = result.reset_index().rename(columns={"index": "lag"})
    table["alpha"] = alpha
    table["decision"] = np.where(table["lb_pvalue"] <= alpha, "reject white noise", "fail to reject white noise")
    return table


def _validate_series(series: pd.Series, name: str) -> None:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series")
    if series.empty or series.isna().any():
        raise ValueError(f"{name} must be non-empty and contain no missing values")
    if series.index.has_duplicates:
        raise ValueError(f"{name} index must not contain duplicates")


def _validate_forecast_index(index: pd.Index) -> None:
    if len(index) == 0:
        raise ValueError("forecast_index must not be empty")
    if index.has_duplicates:
        raise ValueError("forecast_index must not contain duplicates")


def _validate_order(order: tuple[int, int, int], name: str) -> None:
    if len(order) != 3 or any(not isinstance(value, int) or value < 0 for value in order):
        raise ValueError(f"{name} must contain three non-negative integers")


def _validate_seasonal_order(seasonal_order: tuple[int, int, int, int]) -> None:
    if len(seasonal_order) != 4:
        raise ValueError("seasonal_order must contain four integers")
    p, d, q, period = seasonal_order
    if any(not isinstance(value, int) or value < 0 for value in (p, d, q)) or period < 1:
        raise ValueError("seasonal_order must contain non-negative orders and a positive period")
