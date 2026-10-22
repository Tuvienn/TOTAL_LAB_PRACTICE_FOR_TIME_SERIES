from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf


ACF_TABLE_COLUMNS = {"lag", "acf", "lower_ci", "upper_ci"}
DECOMPOSITION_COLUMNS = {
    "observed_log",
    "trend_log",
    "seasonal_log",
    "residual_log",
}
ROLLING_STATISTICS_COLUMNS = {
    "observed_value",
    "rolling_mean_12",
    "rolling_std_12",
}
SEASONAL_DATA_COLUMNS = {
    "timestamp",
    "year",
    "month",
    "observed_value",
}


def _save_figure(figure: plt.Figure, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def plot_time_series(frame: pd.DataFrame, output_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(frame.index, frame["passengers_thousands"], color="#1769aa", linewidth=1.8)
    min_val = frame["passengers_thousands"].min()
    max_val = frame["passengers_thousands"].max()
    axis.axhline(
        max_val,
        color="#85db87",
        linestyle="--",
        linewidth=1.125,
        label=f"Max ({int(max_val)})",
    )  
    yearly_avg = frame["passengers_thousands"].resample("YE").mean()
    axis.plot(
        yearly_avg.index,
        yearly_avg.values,
        color="#f59e0b",
        linestyle="--",
        linewidth=1.3,
        marker="o",
        markersize=5,
        label="Annual Average",
    )
    axis.axhline(
        min_val,
        color="#d32f2f",
        linestyle="--",
        linewidth=1.125,
        label=f"Min ({int(min_val)})",
    )
    axis.set_title("Monthly International Airline Passengers (1949–1960)")
    axis.set_xlabel("Date")
    axis.set_ylabel("Passengers (thousands)")
    axis.grid(alpha=0.25)
    axis.legend(loc="upper left")
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


def plot_white_noise_series(series: pd.Series, output_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(series.index, series.to_numpy(dtype=float), color="#1769aa", linewidth=0.9)
    axis.set_title("White Noise — Normal(0, 1), n=1000, seed=42")
    axis.set_xlabel("Observation")
    axis.set_ylabel("Value")
    axis.grid(alpha=0.25)
    _save_figure(figure, output_path)


def _validate_acf_table(table: pd.DataFrame) -> None:
    missing_columns = ACF_TABLE_COLUMNS.difference(table.columns)
    if missing_columns:
        raise ValueError(f"ACF table is missing columns: {sorted(missing_columns)}")
    if table.empty:
        raise ValueError("ACF table must not be empty")
    if table["lag"].duplicated().any():
        raise ValueError("ACF table contains duplicate lags")
    if not table["lag"].is_monotonic_increasing:
        raise ValueError("ACF table lags must be in increasing order")
    if table[list(ACF_TABLE_COLUMNS)].isna().any().any():
        raise ValueError("ACF table contains missing values")


def _draw_acf_table(
    axis: plt.Axes,
    table: pd.DataFrame,
    title: str,
    x_label: str,
) -> None:
    _validate_acf_table(table)
    lags = table["lag"].to_numpy(dtype=int)
    values = table["acf"].to_numpy(dtype=float)
    lower_zero_bound = table["lower_ci"].to_numpy(dtype=float) - values
    upper_zero_bound = table["upper_ci"].to_numpy(dtype=float) - values

    axis.stem(lags, values)
    if len(lags) > 1:
        axis.fill_between(
            lags[1:],
            lower_zero_bound[1:],
            upper_zero_bound[1:],
            color="#1769aa",
            alpha=0.18,
            label="95% confidence interval",
        )
    axis.axhline(0.0, color="black", linewidth=0.8)
    axis.set_title(title)
    axis.set_xlabel(x_label)
    axis.set_ylabel("Autocorrelation")
    axis.set_xticks(range(0, int(lags.max()) + 1, 5))
    axis.grid(alpha=0.25)
    axis.legend(loc="upper right")


def plot_acf_table(
    table: pd.DataFrame,
    output_path: Path,
    title: str,
    x_label: str = "Lag (observations)",
) -> None:
    figure, axis = plt.subplots(figsize=(11, 5))
    _draw_acf_table(axis, table, title, x_label)
    axis.set_ylim(-0.2, 1.05)
    _save_figure(figure, output_path)


def plot_acf_comparison(
    white_noise_table: pd.DataFrame,
    air_passengers_table: pd.DataFrame,
    output_path: Path,
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(15, 5), sharey=True)
    _draw_acf_table(
        axes[0],
        white_noise_table,
        "White Noise ACF",
        "Lag (observations)",
    )
    _draw_acf_table(
        axes[1],
        air_passengers_table,
        "AirPassengers ACF",
        "Lag (months)",
    )
    axes[0].set_ylim(-0.2, 1.05)
    figure.suptitle("ACF Comparison — White Noise vs AirPassengers")
    figure.tight_layout()
    _save_figure(figure, output_path)


def plot_log_transformed_series(series: pd.Series, output_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(12, 5))
    axis.plot(series.index, series.to_numpy(dtype=float), color="#1769aa", linewidth=1.8)
    axis.set_title("AirPassengers — Natural-Log Transformed Series")
    axis.set_xlabel("Date")
    axis.set_ylabel("Natural log of passengers (thousands)")
    axis.grid(alpha=0.25)
    _save_figure(figure, output_path)


def _validate_decomposition_components(components: pd.DataFrame) -> None:
    missing_columns = DECOMPOSITION_COLUMNS.difference(components.columns)
    if missing_columns:
        raise ValueError(
            f"Decomposition components are missing columns: {sorted(missing_columns)}"
        )
    if components.empty:
        raise ValueError("Decomposition components must not be empty")
    if components[list(DECOMPOSITION_COLUMNS)].isna().any().any():
        raise ValueError("Decomposition components contain missing values")


def plot_stl_decomposition(
    components: pd.DataFrame,
    output_path: Path,
) -> None:
    _validate_decomposition_components(components)
    figure, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    plot_details = (
        ("observed_log", "Observed — natural-log scale", "Log observed"),
        ("trend_log", "Trend — natural-log scale", "Log trend"),
        ("seasonal_log", "Seasonal — natural-log scale", "Log seasonal effect"),
        ("residual_log", "Residual — natural-log scale", "Log residual"),
    )
    for axis, (column, title, y_label) in zip(axes, plot_details, strict=True):
        axis.plot(components.index, components[column], linewidth=1.4)
        axis.set_title(title)
        axis.set_ylabel(y_label)
        axis.grid(alpha=0.25)
    axes[-1].set_xlabel("Date")
    figure.suptitle("AirPassengers Log-STL Decomposition — period=12, robust=True")
    figure.tight_layout()
    _save_figure(figure, output_path)


def plot_decomposition_residual_diagnostics(
    residual: pd.Series,
    acf_table: pd.DataFrame,
    output_path: Path,
) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(12, 9))
    axes[0].plot(
        residual.index,
        residual.to_numpy(dtype=float),
        color="#1769aa",
        linewidth=1.2,
    )
    axes[0].axhline(0.0, color="black", linewidth=0.8)
    axes[0].set_title("Log-STL Residual over Time")
    axes[0].set_xlabel("Date")
    axes[0].set_ylabel("Residual (natural-log scale)")
    axes[0].grid(alpha=0.25)

    _draw_acf_table(
        axes[1],
        acf_table,
        "Log-STL Residual ACF — 40 Lags, 95% Confidence Interval",
        "Lag (months)",
    )
    axes[1].set_ylim(-0.3, 1.05)
    figure.tight_layout()
    _save_figure(figure, output_path)


def plot_missing_values_simulation(
    original: pd.Series,
    masked: pd.Series,
    masked_timestamps: pd.DatetimeIndex,
    output_path: Path,
) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    axes[0].plot(original.index, original, color="#1769aa", linewidth=1.5)
    axes[0].scatter(
        masked_timestamps,
        original.loc[masked_timestamps],
        color="#d32f2f",
        marker="x",
        s=65,
        label="Values selected for masking",
        zorder=3,
    )
    axes[0].set_title("Original AirPassengers and Locked Masking Positions")
    axes[0].set_ylabel("Passengers (thousands)")
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    axes[1].plot(masked.index, masked, color="#1769aa", linewidth=1.5)
    axes[1].scatter(
        masked_timestamps,
        [original.min()] * len(masked_timestamps),
        color="#d32f2f",
        marker="x",
        s=65,
        label="Simulated missing timestamps",
        zorder=3,
    )
    axes[1].set_title("Working Copy with Six Simulated Missing Values")
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Passengers (thousands)")
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    figure.tight_layout()
    _save_figure(figure, output_path)


def plot_missing_treatment_comparison(
    original: pd.Series,
    masked: pd.Series,
    forward_fill: pd.Series,
    interpolation: pd.Series,
    comparison: pd.DataFrame,
    output_path: Path,
) -> None:
    timestamps = pd.DatetimeIndex(comparison["timestamp"])
    figure, axes = plt.subplots(2, 1, figsize=(13, 9))
    axes[0].plot(original.index, original, color="black", linewidth=1.4, label="Original")
    axes[0].plot(masked.index, masked, color="#757575", alpha=0.6, label="With missing")
    axes[0].plot(forward_fill.index, forward_fill, color="#ef6c00", alpha=0.8, label="Forward-fill")
    axes[0].plot(interpolation.index, interpolation, color="#2e7d32", alpha=0.8, label="Time interpolation")
    axes[0].set_title("Missing-Value Treatments in Full-Series Context")
    axes[0].set_ylabel("Passengers (thousands)")
    axes[0].legend(ncol=2)
    axes[0].grid(alpha=0.25)

    positions = range(len(comparison))
    axes[1].plot(positions, comparison["true_value"], marker="o", label="True value")
    axes[1].plot(positions, comparison["forward_fill_value"], marker="o", label="Forward-fill")
    axes[1].plot(positions, comparison["interpolation_value"], marker="o", label="Time interpolation")
    axes[1].set_xticks(list(positions), timestamps.strftime("%Y-%m"), rotation=30)
    axes[1].set_title("Reconstruction at the Six Masked Timestamps")
    axes[1].set_xlabel("Masked timestamp")
    axes[1].set_ylabel("Passengers (thousands)")
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    figure.tight_layout()
    _save_figure(figure, output_path)


def plot_residual_outlier_analysis(
    original: pd.Series,
    residual_log: pd.Series,
    candidates: pd.DataFrame,
    lower_fence: float,
    upper_fence: float,
    output_path: Path,
) -> None:
    candidate_timestamps = pd.DatetimeIndex(candidates["timestamp"])
    figure, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
    axes[0].plot(original.index, original, color="#1769aa", linewidth=1.5)
    axes[0].scatter(
        candidate_timestamps,
        original.loc[candidate_timestamps],
        color="#d32f2f",
        s=38,
        label="Potential outlier candidate",
        zorder=3,
    )
    axes[0].set_title("Potential Outliers in Original-Series Context")
    axes[0].set_ylabel("Passengers (thousands)")
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    axes[1].plot(residual_log.index, residual_log, color="#1769aa", linewidth=1.2)
    axes[1].axhline(lower_fence, color="#d32f2f", linestyle="--", label="IQR fences")
    axes[1].axhline(upper_fence, color="#d32f2f", linestyle="--")
    axes[1].scatter(
        candidate_timestamps,
        residual_log.loc[candidate_timestamps],
        color="#d32f2f",
        s=38,
        label="Flagged residual",
        zorder=3,
    )
    axes[1].set_title("IQR 1.5 Flags on Natural-Log STL Residual")
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Residual (natural-log scale)")
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    figure.tight_layout()
    _save_figure(figure, output_path)


def plot_rolling_statistics(
    rolling_statistics: pd.DataFrame,
    output_path: Path,
) -> None:
    missing_columns = ROLLING_STATISTICS_COLUMNS.difference(
        rolling_statistics.columns
    )
    if missing_columns:
        raise ValueError(
            f"rolling statistics are missing columns: {sorted(missing_columns)}"
        )
    if not isinstance(rolling_statistics.index, pd.DatetimeIndex):
        raise TypeError("rolling statistics index must be a pandas DatetimeIndex")

    figure, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
    axes[0].plot(
        rolling_statistics.index,
        rolling_statistics["observed_value"],
        color="#90caf9",
        linewidth=1.3,
        label="Observed",
    )
    axes[0].plot(
        rolling_statistics.index,
        rolling_statistics["rolling_mean_12"],
        color="#ef6c00",
        linewidth=2.0,
        label="Trailing rolling mean (12 months)",
    )
    axes[0].set_title("AirPassengers and 12-Month Trailing Rolling Mean")
    axes[0].set_ylabel("Passengers (thousands)")
    axes[0].legend()
    axes[0].grid(alpha=0.25)

    axes[1].plot(
        rolling_statistics.index,
        rolling_statistics["rolling_std_12"],
        color="#6a1b9a",
        linewidth=1.8,
        label="Trailing rolling std (12 months, ddof=1)",
    )
    axes[1].set_title("AirPassengers 12-Month Trailing Rolling Standard Deviation")
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Standard deviation (thousands)")
    axes[1].legend()
    axes[1].grid(alpha=0.25)
    figure.tight_layout()
    _save_figure(figure, output_path)


def plot_monthly_seasonal_pattern(
    seasonal_data: pd.DataFrame,
    output_path: Path,
) -> None:
    missing_columns = SEASONAL_DATA_COLUMNS.difference(seasonal_data.columns)
    if missing_columns:
        raise ValueError(
            f"seasonal data are missing columns: {sorted(missing_columns)}"
        )
    if seasonal_data.duplicated(subset=["year", "month"]).any():
        raise ValueError("seasonal data contain duplicate month-year observations")

    years = sorted(seasonal_data["year"].unique().tolist())
    colors = plt.colormaps["viridis"].resampled(len(years))
    figure, axis = plt.subplots(figsize=(13, 7))
    for position, year in enumerate(years):
        yearly = seasonal_data.loc[seasonal_data["year"].eq(year)].sort_values(
            "month"
        )
        if yearly["month"].tolist() != list(range(1, 13)):
            raise ValueError(f"year {year} does not contain months 1 through 12")
        axis.plot(
            yearly["month"],
            yearly["observed_value"],
            color=colors(position),
            marker="o",
            linewidth=1.5,
            markersize=4,
            label=str(year),
        )
    axis.set_title("AirPassengers Monthly Seasonal Pattern by Year")
    axis.set_xlabel("Month")
    axis.set_ylabel("Passengers (thousands)")
    axis.set_xticks(
        range(1, 13),
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    )
    axis.legend(title="Year", bbox_to_anchor=(1.01, 1), loc="upper left")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    _save_figure(figure, output_path)


def plot_month_year_heatmap(
    month_year_matrix: pd.DataFrame,
    output_path: Path,
) -> None:
    if month_year_matrix.shape != (12, 12):
        raise ValueError("month-year matrix must have shape (12, 12)")
    if month_year_matrix.index.tolist() != list(range(1, 13)):
        raise ValueError("month-year matrix rows must be months 1 through 12")
    if month_year_matrix.isna().any().any():
        raise ValueError("month-year matrix must not contain missing cells")

    values = month_year_matrix.to_numpy(dtype=float)
    minimum = float(values.min())
    maximum = float(values.max())
    figure, axis = plt.subplots(figsize=(14, 7))
    image = axis.imshow(values, aspect="auto", cmap="YlOrRd")
    axis.set_title("AirPassengers Month-Year Heatmap")
    axis.set_xlabel("Year")
    axis.set_ylabel("Month")
    axis.set_xticks(range(len(month_year_matrix.columns)))
    axis.set_xticklabels(month_year_matrix.columns.astype(str))
    axis.set_yticks(range(12))
    axis.set_yticklabels(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    )
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            normalized = (values[row, column] - minimum) / (maximum - minimum)
            axis.text(
                column,
                row,
                f"{values[row, column]:.0f}",
                ha="center",
                va="center",
                color="white" if normalized > 0.58 else "#212121",
                fontsize=8,
            )
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label("Passengers (thousands)")
    figure.tight_layout()
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
