from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf


def save_series_plot(series: pd.Series, output_path: Path, title: str, ylabel: str) -> None:
    """Save a labelled time-series plot."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(series.index, series)
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def save_acf_pacf_plot(
    series: pd.Series,
    output_path: Path,
    nlags: int = 36,
    pacf_method: str = "ywm",
) -> None:
    """Save ACF and PACF panels for one validated analysis series."""
    _validate_plot_series(series, "Correlation input")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 4))
    plot_acf(series, lags=nlags, zero=False, ax=axes[0])
    plot_pacf(series, lags=nlags, zero=False, method=pacf_method, ax=axes[1])
    axes[0].set_title("ACF")
    axes[1].set_title("PACF")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def save_residual_diagnostics_plot(residuals: pd.Series, output_path: Path, nlags: int = 36) -> None:
    """Save a residual time plot and residual ACF panel."""
    _validate_plot_series(residuals, "Residual series")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    axes[0].plot(residuals.index, residuals)
    axes[0].axhline(0, color="red", linestyle="--")
    axes[0].set_title("Residuals")
    axes[0].set_xlabel("Date")
    axes[0].set_ylabel("Residual")
    axes[0].grid(alpha=0.25)
    plot_acf(residuals, lags=nlags, zero=False, ax=axes[1])
    axes[1].set_title("Residual ACF")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def save_forecast_comparison_plot(
    train: pd.Series,
    actual: pd.Series,
    forecasts: dict[str, pd.Series],
    output_path: Path,
    title: str,
    ylabel: str,
) -> None:
    """Save aligned train, test, and forecast series in one figure."""
    _validate_plot_series(train, "Training series")
    _validate_plot_series(actual, "Actual series")
    if not forecasts:
        raise ValueError("forecasts must not be empty")
    if any(not actual.index.equals(forecast.index) for forecast in forecasts.values()):
        raise ValueError("All forecast indices must match the actual series index")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(train.index, train, label="Train")
    ax.plot(actual.index, actual, label="Test actual")
    for name, forecast in forecasts.items():
        ax.plot(forecast.index, forecast, linestyle="--", label=name)
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def _validate_plot_series(series: pd.Series, name: str) -> None:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series")
    if series.empty or series.isna().any():
        raise ValueError(f"{name} must be non-empty and contain no missing values")
