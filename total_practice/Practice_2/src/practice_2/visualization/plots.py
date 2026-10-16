from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


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
