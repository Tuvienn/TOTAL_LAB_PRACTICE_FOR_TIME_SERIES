from __future__ import annotations

import itertools
import time
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb

from practice_4.analysis.metrics import calculate_metrics
from practice_4.data.features import (
    EXTENDED_LOAD_LAGS,
    INTERACTION_FEATURES,
    LAG24_FEATURE_NAMES,
    ROLLING_LOAD_FEATURES,
    TARGET_CALENDAR_FEATURES,
    XGB_FULL_FEATURES,
    feature_subset_indices,
    xgb_ablation_subsets,
)


def _feature_group(name: str) -> str:
    if name in TARGET_CALENDAR_FEATURES:
        return "calendar_dst_holiday"
    if name in INTERACTION_FEATURES:
        return "cross_interactions"
    if name in ROLLING_LOAD_FEATURES or name in EXTENDED_LOAD_LAGS:
        return "load_rolling_weekly"
    if name.endswith("_load"):
        return "load_lags_24h"
    if name.endswith("_temperature"):
        return "temperature_lags"
    if name.endswith("_humidity"):
        return "humidity_lags"
    if name.endswith("_wind_speed"):
        return "wind_speed_lags"
    return "other"


def _predict_booster(model: xgb.XGBRegressor, x_data: np.ndarray, best_iteration: int) -> np.ndarray:
    booster = model.get_booster()
    dmat = xgb.DMatrix(x_data, feature_names=booster.feature_names)
    return booster.predict(dmat, iteration_range=(0, best_iteration + 1)).astype(np.float64)


def run_xgboost_stage(
    x_xgb: np.ndarray,
    y_true: np.ndarray,
    target_rows: np.ndarray,
    origin_df: pd.DataFrame,
    split_manifest: dict[str, Any],
    config: dict[str, Any],
    artifacts_dir: Path,
    figures_dir: Path,
) -> dict[str, Any]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    xgb_cfg = config["xgboost"]
    seed = int(config["seed"])

    eligible = origin_df[origin_df["eligible"]].reset_index(drop=True)
    train_mask = (eligible["split"] == "train").to_numpy()
    val_mask = (eligible["split"] == "validation").to_numpy()
    val_all = origin_df[origin_df["split"] == "validation"]
    n_missing = int((val_all["exclusion_reason"] == "missing_truth").sum())
    n_invalid = int((val_all["exclusion_reason"] == "invalid_context").sum())

    cv_folds = split_manifest.get("train_expanding_cv_folds", [])
    subsets = xgb_ablation_subsets()
    full_indices = feature_subset_indices(subsets["XGB_full"])

    grid = xgb_cfg["grid"]
    combos = list(
        itertools.product(
            grid["max_depth"],
            grid["learning_rate"],
            grid["min_child_weight"],
            grid["colsample_bytree"],
            grid["reg_lambda"],
        )
    )

    cv_cache_path = artifacts_dir / "cv_trials.csv"
    if cv_cache_path.exists():
        cached_df = pd.read_csv(cv_cache_path)
        if len(cached_df) == len(combos):
            cv_df = cached_df.sort_values("cv_mean_rmse").reset_index(drop=True)
            combos = []

    cv_trials = []
    for idx, (depth, lr, mcw, colsub, reg_lam) in enumerate(combos, start=1):
        started = time.perf_counter()
        fold_rmses = []
        fold_iters = []
        for fold in cv_folds:
            f_tr = (target_rows >= fold["train_start_row"]) & (target_rows <= fold["train_end_row"])
            f_va = (target_rows >= fold["val_start_row"]) & (target_rows <= fold["val_end_row"])
            model = xgb.XGBRegressor(
                n_estimators=xgb_cfg["n_estimators"],
                max_depth=int(depth),
                learning_rate=float(lr),
                min_child_weight=float(mcw),
                subsample=float(xgb_cfg["subsample"]),
                colsample_bytree=float(colsub),
                reg_lambda=float(reg_lam),
                tree_method=xgb_cfg["tree_method"],
                device=xgb_cfg["device"],
                objective=xgb_cfg["objective"],
                eval_metric=xgb_cfg["eval_metric"],
                early_stopping_rounds=int(xgb_cfg["early_stopping_rounds"]),
                random_state=seed,
                verbosity=0,
            )
            model.fit(
                x_xgb[f_tr][:, full_indices],
                y_true[f_tr],
                eval_set=[(x_xgb[f_va][:, full_indices], y_true[f_va])],
                verbose=False,
            )
            best_it = int(model.best_iteration)
            preds = _predict_booster(model, x_xgb[f_va][:, full_indices], best_it)
            rmse = float(np.sqrt(np.mean((y_true[f_va] - preds) ** 2)))
            fold_rmses.append(rmse)
            fold_iters.append(best_it + 1)

        cv_trials.append(
            {
                "trial_id": f"cv_{idx:02d}_d{depth}_lr{lr}_mcw{mcw}_cs{colsub}_l{reg_lam}",
                "max_depth": int(depth),
                "learning_rate": float(lr),
                "min_child_weight": float(mcw),
                "colsample_bytree": float(colsub),
                "reg_lambda": float(reg_lam),
                "cv_mean_rmse": float(np.mean(fold_rmses)),
                "cv_std_rmse": float(np.std(fold_rmses)),
                "cv_median_trees": int(np.median(fold_iters)),
                "elapsed_seconds": float(time.perf_counter() - started),
            }
        )

    if cv_trials:
        cv_df = pd.DataFrame(cv_trials).sort_values("cv_mean_rmse").reset_index(drop=True)
        cv_df.to_csv(cv_cache_path, index=False)
    best_hp = cv_df.iloc[0].to_dict()

    ablation_records = []
    val_preds_map: dict[str, np.ndarray] = {}
    saved_models: dict[str, Path] = {}
    full_model_obj: xgb.XGBRegressor | None = None
    full_best_iter = 0

    for subset_name, feat_names in subsets.items():
        cols = feature_subset_indices(feat_names)
        started = time.perf_counter()
        model = xgb.XGBRegressor(
            n_estimators=xgb_cfg["n_estimators"],
            max_depth=int(best_hp["max_depth"]),
            learning_rate=float(best_hp["learning_rate"]),
            min_child_weight=float(best_hp["min_child_weight"]),
            subsample=float(xgb_cfg["subsample"]),
            colsample_bytree=float(best_hp["colsample_bytree"]),
            reg_lambda=float(best_hp["reg_lambda"]),
            tree_method=xgb_cfg["tree_method"],
            device=xgb_cfg["device"],
            objective=xgb_cfg["objective"],
            eval_metric=xgb_cfg["eval_metric"],
            early_stopping_rounds=int(xgb_cfg["early_stopping_rounds"]),
            random_state=seed,
            verbosity=0,
        )
        x_tr = x_xgb[train_mask][:, cols]
        x_va = x_xgb[val_mask][:, cols]
        model.fit(x_tr, y_true[train_mask], eval_set=[(x_va, y_true[val_mask])], verbose=False)
        best_it = int(model.best_iteration)
        booster = model.get_booster()[: best_it + 1]
        booster.feature_names = feat_names
        model_path = artifacts_dir / f"{subset_name}.json"
        booster.save_model(model_path)
        saved_models[subset_name] = model_path

        reloaded = xgb.Booster()
        reloaded.load_model(model_path)
        reloaded.set_param({"device": xgb_cfg["device"]})
        preds_orig = _predict_booster(model, x_va, best_it)
        preds_reloaded = reloaded.predict(
            xgb.DMatrix(x_va, feature_names=feat_names), iteration_range=(0, best_it + 1)
        ).astype(np.float64)
        reload_diff = float(np.max(np.abs(preds_orig - preds_reloaded)))
        if reload_diff > 1e-2:
            raise ValueError(f"XGBoost reload parity mismatch for {subset_name}: {reload_diff}")

        scores = calculate_metrics(y_true[val_mask], preds_reloaded, n_missing, n_invalid)
        val_preds_map[subset_name] = preds_reloaded
        ablation_records.append(
            {
                "subset": subset_name,
                "n_features": len(feat_names),
                "trees": best_it + 1,
                "elapsed_seconds": float(time.perf_counter() - started),
                "reload_max_diff": reload_diff,
                **scores,
            }
        )
        if subset_name == "XGB_full":
            full_model_obj = model
            full_best_iter = best_it

    ablation_df = pd.DataFrame(ablation_records).sort_values("rmse_kw").reset_index(drop=True)
    ablation_df.to_csv(artifacts_dir / "ablation_summary.csv", index=False)
    best_subset = str(ablation_df.iloc[0]["subset"])

    val_table = eligible.loc[
        val_mask, ["target_row", "origin_timestamp_utc", "target_timestamp_utc", "y_true"]
    ].copy()
    for name, arr in val_preds_map.items():
        val_table[name] = arr
    val_table.to_csv(artifacts_dir / "validation_predictions.csv", index=False)

    assert full_model_obj is not None
    x_va_full = x_xgb[val_mask][:, full_indices]
    sample_n = min(int(xgb_cfg["shap_sample_size"]), len(x_va_full))
    rng = np.random.default_rng(seed)
    sample_idx = np.sort(rng.choice(len(x_va_full), size=sample_n, replace=False))
    x_shap = x_va_full[sample_idx]

    full_booster = xgb.Booster()
    full_booster.load_model(saved_models["XGB_full"])
    explainer = shap.TreeExplainer(full_booster)
    shap_vals = np.asarray(explainer.shap_values(x_shap), dtype=np.float64)
    base_val = float(np.asarray(explainer.expected_value).reshape(-1)[0])
    shap_preds = full_booster.predict(
        xgb.DMatrix(x_shap, feature_names=list(XGB_FULL_FEATURES)),
        iteration_range=(0, full_best_iter + 1),
    ).astype(np.float64)
    shap_additivity_err = float(np.max(np.abs((base_val + shap_vals.sum(axis=1)) - shap_preds)))

    mean_abs_shap = np.abs(shap_vals).mean(axis=0)
    shap_feat_df = pd.DataFrame(
        {
            "feature": list(XGB_FULL_FEATURES),
            "group": [_feature_group(f) for f in XGB_FULL_FEATURES],
            "mean_abs_shap": mean_abs_shap,
        }
    ).sort_values("mean_abs_shap", ascending=False)
    shap_feat_df.to_csv(artifacts_dir / "shap_importance.csv", index=False)
    group_shap = shap_feat_df.groupby("group")["mean_abs_shap"].sum().sort_values(ascending=False).to_dict()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    top20 = shap_feat_df.head(20).iloc[::-1]
    axes[0].barh(top20["feature"], top20["mean_abs_shap"], color="#1f77b4")
    axes[0].set_title("Top 20 Features by Mean |SHAP| (XGB_full)")
    axes[0].set_xlabel("Mean |SHAP value| (kW)")

    g_names = list(group_shap.keys())[::-1]
    g_vals = [group_shap[k] for k in g_names]
    axes[1].barh(g_names, g_vals, color="#ff7f0e")
    axes[1].set_title("Aggregated Mean |SHAP| by Feature Group")
    axes[1].set_xlabel("Sum of Mean |SHAP value| (kW)")
    fig.tight_layout()
    fig.savefig(figures_dir / "xgb_shap_summary.png", dpi=130)
    plt.close(fig)

    temp_idx = list(XGB_FULL_FEATURES).index("lag00_temperature")
    hdd_idx = list(XGB_FULL_FEATURES).index("hdd_proxy")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].scatter(x_shap[:, temp_idx], shap_vals[:, temp_idx], s=10, alpha=0.5, color="#2ca02c")
    axes[0].axhline(0, color="black", lw=0.7)
    axes[0].set_title("SHAP Dependence: lag00_temperature (scaled)")
    axes[0].set_xlabel("lag00_temperature (standardized)")
    axes[0].set_ylabel("SHAP value (kW)")

    axes[1].scatter(x_shap[:, hdd_idx], shap_vals[:, hdd_idx], s=10, alpha=0.5, color="#d62728")
    axes[1].axhline(0, color="black", lw=0.7)
    axes[1].set_title("SHAP Dependence: hdd_proxy (Heating Degree °C)")
    axes[1].set_xlabel("hdd_proxy = max(0, 18 - temp_c)")
    axes[1].set_ylabel("SHAP value (kW)")
    fig.tight_layout()
    fig.savefig(figures_dir / "xgb_shap_dependence_temp.png", dpi=130)
    plt.close(fig)

    return {
        "device": xgb_cfg["device"],
        "best_cv_hyperparams": best_hp,
        "best_subset": best_subset,
        "ablation": ablation_df.to_dict(orient="records"),
        "shap_additivity_max_err": shap_additivity_err,
        "shap_group_totals": {k: float(v) for k, v in group_shap.items()},
        "top10_shap_features": shap_feat_df.head(10).to_dict(orient="records"),
        "saved_models": {k: str(v) for k, v in saved_models.items()},
    }


def format_xgboost_markdown(res: dict[str, Any], unit: str = "kW") -> str:
    hp = res["best_cv_hyperparams"]
    lines = [
        "# Stage S6 — GPU-Accelerated XGBoost, Ablation & SHAP Findings (v2)",
        "",
        f"- **Device:** NVIDIA RTX 5050 (`device={res['device']}`, `tree_method=hist`)",
        f"- **CV-Selected Hyperparameters (3-fold Expanding CV on Train):** `max_depth={int(hp['max_depth'])}`, `learning_rate={hp['learning_rate']}`, `min_child_weight={hp['min_child_weight']}`, `colsample_bytree={hp['colsample_bytree']}`, `reg_lambda={hp['reg_lambda']}` (CV RMSE `{hp['cv_mean_rmse']:,.2f} ± {hp['cv_std_rmse']:,.2f} {unit}`)",
        f"- **Selected Winning Subset on Validation:** **`{res['best_subset']}`**",
        f"- **SHAP Additivity Max Error:** `{res['shap_additivity_max_err']:.6f} {unit}`",
        "",
        "## 1. Validation Ablation Study",
        "",
        f"| Subset | Features | Trees | Fit (s) | MAE ({unit}) | RMSE ({unit}) | MAPE (%) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in res["ablation"]:
        lines.append(
            f"| `{r['subset']}` | {r['n_features']} | {r['trees']} | {r['elapsed_seconds']:.2f} | "
            f"{r['mae_kw']:,.2f} | {r['rmse_kw']:,.2f} | {r['mape_percent']:.4f} |"
        )
    lines += [
        "",
        "## 2. SHAP Group Attribution (`XGB_full`)",
        "",
        f"| Feature Group | Sum of Mean |SHAP| ({unit}) |",
        "|---|---:|",
    ]
    for grp, val in res["shap_group_totals"].items():
        lines.append(f"| `{grp}` | {val:,.2f} |")
    lines += [
        "",
        "## 3. Top 10 Individual Features by Mean |SHAP|",
        "",
        f"| Feature | Group | Mean |SHAP| ({unit}) |",
        "|---|---|---:|",
    ]
    for item in res["top10_shap_features"]:
        lines.append(f"| `{item['feature']}` | `{item['group']}` | {item['mean_abs_shap']:,.2f} |")
    lines.append("")
    return "\n".join(lines)
