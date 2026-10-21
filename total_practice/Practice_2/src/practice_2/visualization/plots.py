from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf


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
    acf_table: pd.DataFrame,
    pacf_table: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save ACF/PACF panels from the same tables used for interpretation."""
    required = {"lag", "correlation", "ci_lower", "ci_upper"}
    for table_name, table in [("ACF", acf_table), ("PACF", pacf_table)]:
        missing = required.difference(table.columns)
        if missing:
            raise ValueError(f"{table_name} table is missing columns: {sorted(missing)}")
        if table.empty:
            raise ValueError(f"{table_name} table must be non-empty")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5), sharey=True)

    for ax, table, title in [
        (axes[0], acf_table, "ACF — log first-differenced training series"),
        (axes[1], pacf_table, "PACF (ywm) — log first-differenced training series"),
    ]:
        lags = table["lag"].to_numpy()
        correlations = table["correlation"].to_numpy()
        lower_band = table["ci_lower"].to_numpy() - correlations
        upper_band = table["ci_upper"].to_numpy() - correlations

        ax.axhline(0, color="black", linewidth=0.8)
        ax.fill_between(lags, lower_band, upper_band, color="#7aa6d8", alpha=0.28)
        ax.vlines(lags, 0, correlations, color="#265d97", linewidth=1.1)
        ax.plot(lags, correlations, "o", color="#173f6b", markersize=3.4)
        for seasonal_lag in (12, 24, 36):
            if seasonal_lag <= int(np.max(lags)):
                ax.axvline(seasonal_lag, color="#d97706", linestyle="--", alpha=0.45)
        ax.set_title(title)
        ax.set_xlabel("Lag")
        ax.set_xlim(-0.5, float(np.max(lags)) + 0.5)
        ax.grid(axis="y", alpha=0.2)

    axes[0].set_ylabel("Correlation")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def save_residual_diagnostics_plot(
    residuals_by_model: dict[str, pd.Series],
    output_path: Path,
    nlags: int = 36,
    alpha: float = 0.05,
) -> None:
    """Save residual time plots and ACF panels for fitted models."""
    if not residuals_by_model:
        raise ValueError("At least one residual series is required")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(
        len(residuals_by_model),
        2,
        figsize=(14, 4.2 * len(residuals_by_model)),
        squeeze=False,
    )

    for row, (model_name, residuals) in enumerate(residuals_by_model.items()):
        if residuals.empty or residuals.isna().any():
            raise ValueError(f"{model_name} residuals must be non-empty without missing values")
        axes[row, 0].plot(residuals.index, residuals, color="#265d97")
        axes[row, 0].axhline(0, color="black", linewidth=0.8)
        axes[row, 0].set_title(f"{model_name} residuals after burn-in")
        axes[row, 0].set_xlabel("Date")
        axes[row, 0].set_ylabel("Residual (log scale)")
        axes[row, 0].grid(alpha=0.2)
        plot_acf(
            residuals,
            lags=nlags,
            alpha=alpha,
            ax=axes[row, 1],
            title=f"{model_name} residual ACF",
        )
        for seasonal_lag in (12, 24, 36):
            if seasonal_lag <= nlags:
                axes[row, 1].axvline(
                    seasonal_lag,
                    color="#d97706",
                    linestyle="--",
                    linewidth=1.1,
                    alpha=0.65,
                )

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def save_forecast_comparison_plot(
    train: pd.Series,
    test: pd.Series,
    forecasts: dict[str, pd.Series],
    output_path: Path,
) -> None:
    """Save train, test, and aligned forecast series on the original scale."""
    if not forecasts:
        raise ValueError("At least one forecast series is required")
    for model_name, forecast in forecasts.items():
        if not forecast.index.equals(test.index):
            raise ValueError(f"{model_name} forecast index does not match test index")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=False)
    styles = {
        "ARIMA(1,1,1)": {"color": "#9467bd", "linestyle": "-"},
        "ARIMA(2,1,1)": {"color": "#e45756", "linestyle": "-."},
    }

    def draw_panel(ax, train_view: pd.Series, title: str) -> None:
        ax.plot(train_view.index, train_view, label="Train", color="#4c78a8")
        ax.plot(test.index, test, label="Test actual", color="black", linewidth=2)
        for model_name, forecast in forecasts.items():
            style = styles.get(
                model_name,
                {"color": "#2ca02c", "linestyle": "--"},
            )
            ax.plot(
                forecast.index,
                forecast,
                label=model_name,
                linewidth=1.8,
                **style,
            )
        ax.set_title(title)
        ax.set_ylabel("Monthly retail sales")
        ax.grid(alpha=0.25)

    draw_panel(axes[0], train, "Full series: ARIMA forecasts and seasonal-naive baseline")
    zoom_observations = min(36, len(train))
    draw_panel(
        axes[1],
        train.iloc[-zoom_observations:],
        "Test-period detail: final 36 training months and aligned forecasts",
    )
    axes[0].legend(ncol=2)
    axes[1].set_xlabel("Date")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
