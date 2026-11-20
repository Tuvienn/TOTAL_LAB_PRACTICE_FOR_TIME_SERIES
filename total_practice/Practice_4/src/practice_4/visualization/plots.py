from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from practice_4.analysis.eda import VARIABLES


def render(frame, summary: dict, directory: Path, dpi: int = 120) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    with plt.rc_context({"font.family": "DejaVu Sans", "figure.dpi": dpi, "savefig.dpi": dpi}):
        def save(fig, name):
            fig.tight_layout()
            path = directory / name
            fig.savefig(path, metadata={"Software": "matplotlib"})
            plt.close(fig)
            paths.append(path)

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].bar(["observed", "missing"], [summary["observed"], summary["missing"]])
        axes[0].set_title("Train load coverage")
        lengths = [g["length_hours"] for g in summary["gaps"]]
        if lengths:
            unique, counts = np.unique(lengths, return_counts=True)
            axes[1].bar(unique, counts)
        axes[1].set(title="Missing run lengths (hours)", xlabel="hours", ylabel="runs")
        censored = sum(g["left_censored"] or g["right_censored"] for g in summary["gaps"])
        axes[1].text(0.98, 0.98, f"censored runs: {censored}", transform=axes[1].transAxes, ha="right", va="top")
        save(fig, "missing_gaps.png")

        fig, axes = plt.subplots(2, 2, figsize=(10, 7))
        for ax, name in zip(axes.flat, VARIABLES):
            ax.hist(frame[name].dropna(), bins=40)
            ax.set(title=name, ylabel="rows")
        save(fig, "extremes.png")

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(frame["timestamp_utc"], frame["load"], linewidth=0.5)
        ax.set(title="Train load (UTC)", ylabel="MW", xlabel="UTC")
        save(fig, "load_utc.png")

        fig, axes = plt.subplots(2, 2, figsize=(12, 7))
        for column, key in enumerate(("hour", "weekday")):
            rows = summary["profiles"][key]
            x = [r["group"] for r in rows]
            for label in ("mean", "median"):
                axes[0, column].plot(x, [r[label] for r in rows], label=label)
            axes[0, column].set(title=f"Madrid {key}", ylabel="MW")
            axes[0, column].legend()
            axes[1, column].bar(x, [r["count"] for r in rows], label="observed")
            axes[1, column].bar(x, [r["missing"] for r in rows], bottom=[r["count"] for r in rows], label="missing")
            axes[1, column].set(xlabel=key, ylabel="rows")
            axes[1, column].legend()
        save(fig, "local_profiles.png")

        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        axes[0].scatter(frame["temp"], frame["load"], s=2, alpha=0.15)
        axes[0].set(title=f"Load vs temperature (n={summary['pair_counts']['load']['temp']})", xlabel="temperature proxy (K)", ylabel="load (MW)")
        matrix = np.array([[summary["correlations"][a][b] for a in VARIABLES] for b in VARIABLES])
        im = axes[1].imshow(matrix, vmin=-1, vmax=1, cmap="coolwarm")
        axes[1].set_xticks(range(4), VARIABLES, rotation=45, ha="right")
        axes[1].set_yticks(range(4), VARIABLES)
        axes[1].set_title("Train correlation")
        fig.colorbar(im, ax=axes[1])
        save(fig, "relationships.png")

        fig, axes = plt.subplots(2, 1, figsize=(11, 6))
        for ax, key in zip(axes, ("acf", "pacf")):
            ax.vlines(range(len(summary[key])), 0, summary[key], linewidth=0.7)
            ax.axhline(0, color="black", linewidth=0.5)
            ax.set(title=f"{key.upper()} - longest observed train block", xlabel="lag (hours)")
        save(fig, "acf_pacf.png")
    return paths
