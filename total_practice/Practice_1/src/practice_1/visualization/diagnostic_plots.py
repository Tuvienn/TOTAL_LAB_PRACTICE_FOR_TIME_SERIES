from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf


def _save_figure(figure: plt.Figure, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def plot_time_series(frame: pd.DataFrame, output_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(frame.index, frame["passengers_thousands"], color="#1769aa", linewidth=1.8)
    axis.set_title("AirPassengers Monthly International Airline Passengers")
    axis.set_xlabel("Date")
    axis.set_ylabel("Passengers (thousands)")
    axis.grid(alpha=0.25)
    _save_figure(figure, output_path)


def plot_acf_diagnostic(
    series: pd.Series,
    output_path: Path,
    max_lag: int = 40,
    alpha: float = 0.05,
) -> None:
    figure, axis = plt.subplots(figsize=(11, 5))
    plot_acf(series, lags=max_lag, alpha=alpha, ax=axis, zero=True)
    axis.set_title("AirPassengers ACF — 40 Lags, 95% Confidence Interval")
    axis.set_xlabel("Lag (months)")
    axis.set_ylabel("Autocorrelation")
    axis.set_xticks(range(0, max_lag + 1, 5))
    axis.tick_params(axis="x", labelbottom=True)
    _save_figure(figure, output_path)


def plot_pacf_diagnostic(
    series: pd.Series,
    output_path: Path,
    max_lag: int = 40,
    alpha: float = 0.05,
    method: str = "ywm",
) -> None:
    figure, axis = plt.subplots(figsize=(11, 5))
    plot_pacf(series, lags=max_lag, alpha=alpha, method=method, ax=axis, zero=True)
    axis.set_title("AirPassengers PACF — 40 Lags, 95% Confidence Interval")
    axis.set_xlabel("Lag (months)")
    axis.set_ylabel("Partial autocorrelation")
    axis.set_xticks(range(0, max_lag + 1, 5))
    axis.tick_params(axis="x", labelbottom=True)
    _save_figure(figure, output_path)
