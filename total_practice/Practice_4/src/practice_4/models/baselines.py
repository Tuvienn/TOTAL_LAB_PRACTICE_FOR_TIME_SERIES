from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from practice_4.analysis.metrics import calculate_metrics


def compute_baselines(
    prepared_df: pd.DataFrame,
    origin_df: pd.DataFrame,
) -> tuple[dict[str, dict[str, Any]], pd.DataFrame]:
    eligible = origin_df[origin_df["eligible"]].reset_index(drop=True)
    work_load = prepared_df["load_input"].to_numpy(dtype=np.float64)
    target_rows = eligible["target_row"].to_numpy(dtype=np.int64)
    y_true = eligible["y_true"].to_numpy(dtype=np.float64)

    preds = {
        "persistence": work_load[target_rows - 1],
        "seasonal24": work_load[target_rows - 24],
        "seasonal168": work_load[target_rows - 168],
    }

    metrics: dict[str, dict[str, Any]] = {}
    pred_rows = []
    for name, arr in preds.items():
        if not np.isfinite(arr).all():
            raise ValueError(f"Non-finite baseline forecast for {name}")
        metrics[name] = {}
        for split_name in ("train", "validation"):
            mask = (eligible["split"] == split_name).to_numpy()
            part_all = origin_df[origin_df["split"] == split_name]
            missing = int((part_all["exclusion_reason"] == "missing_truth").sum())
            invalid = int((part_all["exclusion_reason"] == "invalid_context").sum())
            metrics[name][split_name] = calculate_metrics(y_true[mask], arr[mask], missing, invalid)

        val_mask = (eligible["split"] == "validation").to_numpy()
        val_df = eligible.loc[val_mask, ["target_row", "origin_timestamp_utc", "target_timestamp_utc", "y_true"]].copy()
        val_df["model"] = name
        val_df["y_pred"] = arr[val_mask]
        pred_rows.append(val_df)

    return metrics, pd.concat(pred_rows, ignore_index=True)


def format_baseline_markdown(metrics: dict[str, dict[str, Any]], unit: str = "kW") -> str:
    lines = [
        "# Stage S5 — Baseline Results (Persistence, Seasonal-24, Seasonal-168)",
        "",
        f"Metrics reported in original load unit (`{unit}`) on identical eligible origins.",
        "",
        f"| Model | Split | Scored | MAE ({unit}) | RMSE ({unit}) | MAPE (%) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for model_name in ("persistence", "seasonal24", "seasonal168"):
        for split_name in ("train", "validation"):
            m = metrics[model_name][split_name]
            lines.append(
                f"| `{model_name}` | {split_name} | {m['n_scored']:,} | "
                f"{m['mae_kw']:,.2f} | {m['rmse_kw']:,.2f} | {m['mape_percent']:.4f} |"
            )
    lines.append("")
    return "\n".join(lines)
