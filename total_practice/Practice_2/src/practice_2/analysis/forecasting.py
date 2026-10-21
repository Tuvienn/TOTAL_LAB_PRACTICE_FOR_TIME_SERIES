from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA

from practice_2.analysis.correlation import validate_arima_candidates


FIT_SUMMARY_COLUMNS = [
    "model",
    "p",
    "d",
    "q",
    "trend",
    "drift_included",
    "analysis_scale",
    "n_train",
    "converged",
    "aic",
    "bic",
    "warnings",
]
RESIDUAL_DIAGNOSTIC_COLUMNS = [
    "model",
    "residual_mean",
    "residual_observations",
    "burn_in",
    "lag",
    "model_df",
    "alpha",
    "lb_stat",
    "lb_pvalue",
    "reject_no_autocorrelation",
    "white_noise_supported",
]
FORECAST_COLUMNS = ["model", "timestamp", "actual", "forecast", "error", "absolute_error"]
METRIC_COLUMNS = ["model", "mae", "rmse", "mape_percent"]
LARGEST_ERROR_COLUMNS = ["model", "timestamp", "actual", "forecast", "absolute_error"]


def _validate_level_series(series: pd.Series, label: str) -> None:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{label} must be a pandas Series")
    if series.empty:
        raise ValueError(f"{label} must be non-empty")
    if series.isna().any():
        raise ValueError(f"{label} must contain no missing values")
    if not pd.api.types.is_numeric_dtype(series):
        raise TypeError(f"{label} must be numeric")
    if (series <= 0).any():
        raise ValueError(f"{label} must contain only positive values")
    if not series.index.is_monotonic_increasing:
        raise ValueError(f"{label} index must be chronological")


def fit_arima_candidates(
    train_levels: pd.Series,
    candidate_table: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Fit validated E04 candidates to natural-log training levels."""
    _validate_level_series(train_levels, "Training levels")
    candidates = validate_arima_candidates(candidate_table)
    train_log = np.log(train_levels.astype(float))

    fitted_models: dict[str, Any] = {}
    summary_rows: list[dict[str, object]] = []

    for row in candidates.itertuples(index=False):
        order = (int(row.p), int(row.d), int(row.q))
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            fitted = ARIMA(train_log, order=order, trend="n").fit()

        warning_text = " | ".join(str(item.message) for item in caught_warnings)
        converged = bool(getattr(fitted, "mle_retvals", {}).get("converged", False))
        fitted_models[row.candidate] = fitted
        summary_rows.append(
            {
                "model": row.candidate,
                "p": order[0],
                "d": order[1],
                "q": order[2],
                "trend": "n",
                "drift_included": False,
                "analysis_scale": row.analysis_scale,
                "n_train": len(train_levels),
                "converged": converged,
                "aic": float(fitted.aic),
                "bic": float(fitted.bic),
                "warnings": warning_text or "none",
            }
        )

    return fitted_models, pd.DataFrame(summary_rows, columns=FIT_SUMMARY_COLUMNS)


def compute_residual_diagnostics(
    fitted_models: Mapping[str, Any],
    lags: Sequence[int] = (12, 24),
    alpha: float = 0.05,
) -> tuple[dict[str, pd.Series], pd.DataFrame]:
    """Compute post-burn-in residual series and Ljung-Box diagnostics."""
    if not fitted_models:
        raise ValueError("At least one fitted model is required")
    if not lags or any(not isinstance(lag, int) or lag < 1 for lag in lags):
        raise ValueError("Ljung-Box lags must be positive integers")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    residuals_by_model: dict[str, pd.Series] = {}
    rows: list[dict[str, object]] = []

    for model_name, fitted in fitted_models.items():
        residuals = fitted.resid
        if not isinstance(residuals, pd.Series):
            row_labels = getattr(fitted.model.data, "row_labels", None)
            residuals = pd.Series(np.asarray(residuals), index=row_labels)
        residuals = residuals.astype(float)

        burn_in = int(getattr(fitted, "loglikelihood_burn", 0))
        residuals = residuals.iloc[burn_in:].dropna()
        if residuals.empty:
            raise ValueError(f"{model_name} has no residuals after burn-in")

        order = tuple(int(value) for value in fitted.model.order)
        seasonal_order = tuple(
            int(value)
            for value in getattr(fitted.model, "seasonal_order", (0, 0, 0, 0))
        )
        model_df = order[0] + order[2] + seasonal_order[0] + seasonal_order[2]
        if any(lag <= model_df for lag in lags):
            raise ValueError("Each Ljung-Box lag must be greater than p + q")
        if max(lags) >= len(residuals):
            raise ValueError("Ljung-Box lag must be smaller than residual length")

        ljung_box = acorr_ljungbox(
            residuals,
            lags=list(lags),
            model_df=model_df,
            return_df=True,
        )
        white_noise_supported = bool((ljung_box["lb_pvalue"] > alpha).all())
        residuals_by_model[model_name] = residuals.rename(model_name)

        for lag in lags:
            rows.append(
                {
                    "model": model_name,
                    "residual_mean": float(residuals.mean()),
                    "residual_observations": len(residuals),
                    "burn_in": burn_in,
                    "lag": lag,
                    "model_df": model_df,
                    "alpha": alpha,
                    "lb_stat": float(ljung_box.loc[lag, "lb_stat"]),
                    "lb_pvalue": float(ljung_box.loc[lag, "lb_pvalue"]),
                    "reject_no_autocorrelation": bool(
                        ljung_box.loc[lag, "lb_pvalue"] <= alpha
                    ),
                    "white_noise_supported": white_noise_supported,
                }
            )

    return residuals_by_model, pd.DataFrame(rows, columns=RESIDUAL_DIAGNOSTIC_COLUMNS)


def forecast_arima_candidates(
    fitted_models: Mapping[str, Any],
    forecast_index: pd.DatetimeIndex,
) -> dict[str, pd.Series]:
    """Forecast on the original scale using exp(log forecast mean)."""
    if not fitted_models:
        raise ValueError("At least one fitted model is required")
    if not isinstance(forecast_index, pd.DatetimeIndex) or forecast_index.empty:
        raise ValueError("forecast_index must be a non-empty DatetimeIndex")
    if not forecast_index.is_monotonic_increasing or forecast_index.has_duplicates:
        raise ValueError("forecast_index must be chronological and unique")

    forecasts: dict[str, pd.Series] = {}
    for model_name, fitted in fitted_models.items():
        log_forecast = fitted.forecast(steps=len(forecast_index))
        forecasts[model_name] = pd.Series(
            np.exp(np.asarray(log_forecast, dtype=float)),
            index=forecast_index,
            name=model_name,
        )
    return forecasts


def seasonal_naive_forecast(
    train_levels: pd.Series,
    forecast_index: pd.DatetimeIndex,
    seasonal_period: int = 12,
) -> pd.Series:
    """Create a fixed-origin seasonal-naive forecast from training history only."""
    _validate_level_series(train_levels, "Training levels")
    if not isinstance(seasonal_period, int) or seasonal_period < 1:
        raise ValueError("seasonal_period must be a positive integer")
    if len(train_levels) < seasonal_period:
        raise ValueError("Training levels are shorter than the seasonal period")
    if not isinstance(forecast_index, pd.DatetimeIndex) or forecast_index.empty:
        raise ValueError("forecast_index must be a non-empty DatetimeIndex")

    seasonal_values = train_levels.iloc[-seasonal_period:].to_numpy(dtype=float)
    values = np.resize(seasonal_values, len(forecast_index))
    return pd.Series(
        values,
        index=forecast_index,
        name=f"Seasonal naive ({seasonal_period})",
    )


def build_forecast_table(
    actual: pd.Series,
    forecasts: Mapping[str, pd.Series],
) -> pd.DataFrame:
    """Create aligned, long-form forecast errors for every evaluated model."""
    _validate_level_series(actual, "Actual test series")
    if not forecasts:
        raise ValueError("At least one forecast is required")

    rows: list[pd.DataFrame] = []
    for model_name, forecast in forecasts.items():
        if not actual.index.equals(forecast.index):
            raise ValueError(f"{model_name} forecast index does not match actual index")
        if forecast.isna().any():
            raise ValueError(f"{model_name} forecast contains missing values")
        error = actual.astype(float) - forecast.astype(float)
        rows.append(
            pd.DataFrame(
                {
                    "model": model_name,
                    "timestamp": actual.index,
                    "actual": actual.to_numpy(dtype=float),
                    "forecast": forecast.to_numpy(dtype=float),
                    "error": error.to_numpy(dtype=float),
                    "absolute_error": error.abs().to_numpy(dtype=float),
                }
            )
        )
    return pd.concat(rows, ignore_index=True).loc[:, FORECAST_COLUMNS]


def calculate_forecast_metrics(forecast_table: pd.DataFrame) -> pd.DataFrame:
    """Calculate MAE, RMSE, and MAPE from an aligned long-form forecast table."""
    missing = set(FORECAST_COLUMNS).difference(forecast_table.columns)
    if missing:
        raise ValueError(f"Forecast table is missing columns: {sorted(missing)}")
    if forecast_table.empty:
        raise ValueError("Forecast table must be non-empty")
    if (forecast_table["actual"] == 0).any():
        raise ValueError("MAPE is undefined when actual contains zero")

    rows: list[dict[str, object]] = []
    for model_name, group in forecast_table.groupby("model", sort=False):
        errors = group["error"].to_numpy(dtype=float)
        actual = group["actual"].to_numpy(dtype=float)
        rows.append(
            {
                "model": model_name,
                "mae": float(np.mean(np.abs(errors))),
                "rmse": float(np.sqrt(np.mean(errors**2))),
                "mape_percent": float(np.mean(np.abs(errors / actual)) * 100),
            }
        )
    return pd.DataFrame(rows, columns=METRIC_COLUMNS)


def largest_forecast_errors(forecast_table: pd.DataFrame) -> pd.DataFrame:
    """Return the maximum absolute-error observation for each model."""
    missing = set(FORECAST_COLUMNS).difference(forecast_table.columns)
    if missing:
        raise ValueError(f"Forecast table is missing columns: {sorted(missing)}")
    if forecast_table.empty:
        raise ValueError("Forecast table must be non-empty")

    indices = forecast_table.groupby("model", sort=False)["absolute_error"].idxmax()
    return (
        forecast_table.loc[indices, LARGEST_ERROR_COLUMNS]
        .reset_index(drop=True)
        .loc[:, LARGEST_ERROR_COLUMNS]
    )
