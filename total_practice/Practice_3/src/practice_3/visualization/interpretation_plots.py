from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def plot_top_feature_importance(
    importance: pd.DataFrame,
    output_path: Path,
    top_n: int = 20,
) -> None:
    """Render the approved horizontal gain-importance figure."""
    required = {"feature", "normalized_gain", "rank"}
    if not required.issubset(importance.columns):
        missing = sorted(required.difference(importance.columns))
        raise ValueError(f"Importance table is missing columns: {missing}")
    if top_n <= 0 or len(importance) < top_n:
        raise ValueError("top_n must be positive and available in the table.")

    top = importance.nsmallest(top_n, "rank").sort_values(
        "normalized_gain",
        ascending=True,
    )
    figure, axis = plt.subplots(figsize=(12, 9))
    axis.barh(
        top["feature"],
        top["normalized_gain"],
        color="#2f6f9f",
    )
    axis.set_title(
        "Top 20 Feature Importance — xgboost_tuned, "
        "lag_only_p168, gain"
    )
    axis.set_xlabel("Normalized gain (not a causal effect)")
    axis.set_ylabel("Feature")
    axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f".{output_path.name}.tmp.png")
    figure.savefig(temporary_path, dpi=160, bbox_inches="tight")
    temporary_path.replace(output_path)
    plt.close(figure)
