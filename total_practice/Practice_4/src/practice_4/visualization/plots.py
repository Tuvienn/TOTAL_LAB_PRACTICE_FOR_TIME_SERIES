from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def render_eda_figures(
    frame: pd.DataFrame,
    summary: dict[str, Any],
    output_dir: Path,
    dpi: int = 130,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    ts = pd.DatetimeIndex(frame["timestamp_utc"])

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(ts, frame["load"], linewidth=0.5, color="#1f77b4")
    ax.set_title("Train Electricity Load Over Time (UTC)")
    ax.set_xlabel("Timestamp (UTC)")
    ax.set_ylabel("Total Load (kW)")
    fig.tight_layout()
    p1 = output_dir / "eda_load_utc.png"
    fig.savefig(p1, dpi=dpi)
    plt.close(fig)
    paths.append(p1)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    hour_df = pd.DataFrame(summary["profiles"]["hour"])
    axes[0].plot(hour_df["group"], hour_df["mean"], marker="o", ms=3)
    axes[0].set_title(f"Mean Load by Hour ({summary['timezone_local']})")
    axes[0].set_xlabel("Local Hour")
    axes[0].set_ylabel("Load (kW)")

    wd_df = pd.DataFrame(summary["profiles"]["weekday"])
    axes[1].bar(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], wd_df["mean"], color="#2ca02c")
    axes[1].set_title("Mean Load by Weekday")
    axes[1].set_ylabel("Load (kW)")

    mo_df = pd.DataFrame(summary["profiles"]["month"])
    axes[2].plot(mo_df["group"], mo_df["mean"], marker="s", color="#d62728")
    axes[2].set_title("Mean Load by Month (Seasonality)")
    axes[2].set_xlabel("Month")
    axes[2].set_ylabel("Load (kW)")
    fig.tight_layout()
    p2 = output_dir / "eda_seasonality_profiles.png"
    fig.savefig(p2, dpi=dpi)
    plt.close(fig)
    paths.append(p2)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    sample = frame.iloc[::max(1, len(frame) // 4000)]
    axes[0].scatter(sample["temp"], sample["load"], s=4, alpha=0.35, color="#ff7f0e")
    axes[0].set_title("Load vs Temperature (Nonlinear Response)")
    axes[0].set_xlabel("Temperature (°C)")
    axes[0].set_ylabel("Load (kW)")

    vars_order = ["load", "temp", "humidity", "wind_speed"]
    corr = np.array([[summary["pearson"][r][c] for c in vars_order] for r in vars_order])
    im = axes[1].imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    axes[1].set_xticks(range(4))
    axes[1].set_yticks(range(4))
    axes[1].set_xticklabels(vars_order, rotation=20)
    axes[1].set_yticklabels(vars_order)
    for i in range(4):
        for j in range(4):
            axes[1].text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center", fontsize=9)
    axes[1].set_title("Train Pearson Correlation Matrix")
    fig.colorbar(im, ax=axes[1], fraction=0.046)
    fig.tight_layout()
    p3 = output_dir / "eda_relationships.png"
    fig.savefig(p3, dpi=dpi)
    plt.close(fig)
    paths.append(p3)

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    lags = np.arange(len(summary["acf"]))
    conf = 1.96 / np.sqrt(summary["rows"])
    axes[0].vlines(lags, 0, summary["acf"], color="#1f77b4", lw=1.0)
    axes[0].axhline(conf, color="red", ls="--", lw=0.8)
    axes[0].axhline(-conf, color="red", ls="--", lw=0.8)
    axes[0].set_title("Train Load ACF (Lags 0–168h)")
    axes[0].set_ylabel("ACF")

    axes[1].vlines(lags, 0, summary["pacf"], color="#2ca02c", lw=1.0)
    axes[1].axhline(conf, color="red", ls="--", lw=0.8)
    axes[1].axhline(-conf, color="red", ls="--", lw=0.8)
    axes[1].set_title("Train Load PACF (YWM, Lags 0–168h)")
    axes[1].set_xlabel("Lag (hours)")
    axes[1].set_ylabel("PACF")
    fig.tight_layout()
    p4 = output_dir / "eda_acf_pacf.png"
    fig.savefig(p4, dpi=dpi)
    plt.close(fig)
    paths.append(p4)

    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    for ax, col, label in zip(
        axes.ravel(),
        ["load", "temp", "humidity", "wind_speed"],
        ["Load (kW)", "Temperature (°C)", "Humidity (%)", "Wind Speed (m/s)"],
    ):
        ax.hist(frame[col].dropna(), bins=60, color="#4c72b0", alpha=0.8)
        e = summary["extrema"][col]
        ax.axvline(e["p0_5"], color="red", ls="--", lw=1.0, label="P0.5/P99.5")
        ax.axvline(e["p99_5"], color="red", ls="--", lw=1.0)
        ax.set_title(f"Train Distribution: {label}")
        ax.legend(fontsize=8)
    fig.tight_layout()
    p5 = output_dir / "eda_distributions.png"
    fig.savefig(p5, dpi=dpi)
    plt.close(fig)
    paths.append(p5)

    return paths
