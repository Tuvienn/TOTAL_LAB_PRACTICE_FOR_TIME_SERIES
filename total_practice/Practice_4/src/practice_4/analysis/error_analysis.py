from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "20261120_system312_h02_02"
MODELS = ("persistence", "seasonal24", "VAR", "XGB", "LSTM")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group_metrics(frame: pd.DataFrame, dimension: str, group: str) -> list[dict]:
    rows = []
    for model, part in frame.groupby("model", sort=False):
        actual = part.y_true_mw.to_numpy(dtype=np.float64)
        predicted = part.y_pred_mw.to_numpy(dtype=np.float64)
        error = actual - predicted
        nonzero = actual != 0
        rows.append({
            "dimension": dimension, "group": group, "model": model,
            "n": len(part), "bias_mw": float(error.mean()),
            "mae_mw": float(np.abs(error).mean()),
            "rmse_mw": float(np.sqrt(np.mean(error ** 2))),
            "mape_percent": float(100 * np.mean(np.abs(error[nonzero] / actual[nonzero]))) if nonzero.any() else None,
        })
    return rows


def add_group(rows: list[dict], frame: pd.DataFrame, column: str, dimension: str) -> None:
    for group, part in frame.groupby(column, dropna=False, sort=True):
        rows.extend(group_metrics(part, dimension, str(group)))


def run(run_id: str = RUN_ID, h01_run_id: str = "20261120_system312_h01_03") -> None:
    run_dir = ROOT / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(run_dir)
    h01 = ROOT / "runs" / h01_run_id
    artifact_dir = h01 / "artifacts"
    manifest_path = artifact_dir / "evaluation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prediction_path = ROOT / "outputs/predictions/test_predictions.csv"
    metrics_path = ROOT / "outputs/tables/test_metrics.csv"
    diagnostic_path = artifact_dir / "diagnostic_context.csv"
    for path in (prediction_path, metrics_path, diagnostic_path):
        if not path.exists():
            raise FileNotFoundError(path)
    if digest(prediction_path) != manifest["prediction_file"]["sha256"]:
        raise ValueError("Accepted H01 prediction digest mismatch")
    preds = pd.read_csv(prediction_path, float_precision="round_trip")
    preds["origin"] = pd.to_datetime(preds.origin, utc=True)
    preds["target_timestamp"] = pd.to_datetime(preds.target_timestamp, utc=True)
    context = pd.read_csv(diagnostic_path, float_precision="round_trip")
    context["origin"] = pd.to_datetime(context.origin, utc=True)
    context["target_timestamp"] = pd.to_datetime(context.target_timestamp, utc=True)
    context = context.drop(columns=["load_mw"])
    frame = preds.merge(context, on=["origin", "target_timestamp"], validate="many_to_one")
    if len(frame) != 5 * 5259 or set(frame.model.unique()) != set(MODELS):
        raise ValueError("H01 five-model common sample mismatch")
    frame["residual_mw"] = frame.y_true_mw - frame.y_pred_mw
    frame["local_target"] = frame.target_timestamp.dt.tz_convert("Europe/Madrid")
    frame["local_hour"] = frame.local_target.dt.hour
    frame["weekday"] = frame.local_target.dt.day_name()
    frame["month"] = frame.local_target.dt.strftime("%Y-%m")
    month = frame.local_target.dt.month
    frame["season"] = np.select([month.isin([12, 1, 2]), month.isin([3, 4, 5]), month.isin([6, 7, 8])], ["DJF", "MAM", "JJA"], default="SON")
    scaler = json.loads((ROOT / "runs/20261118_system312_d02_01/artifacts/scaler.json").read_text(encoding="utf-8"))
    lo, hi = scaler["bounds"]["load"]["lower"], scaler["bounds"]["load"]["upper"]
    actual = frame.y_true_mw
    frame["load_regime"] = np.select([actual < lo, actual > hi], ["below_train_p0_5", "above_train_p99_5"], default="within_train_bounds")
    for source, target in (("temperature_k", "temperature_regime"), ("humidity_percent", "humidity_regime"), ("wind_speed_mps", "wind_speed_regime")):
        bounds = scaler["bounds"][{"temperature_k":"temp", "humidity_percent":"humidity", "wind_speed_mps":"wind_speed"}[source]]
        frame[target] = np.select([frame[source] < bounds["lower"], frame[source] > bounds["upper"]], ["below_train_p0_5", "above_train_p99_5"], default="within_train_bounds")
    grouped = []
    for column, name in (("local_hour", "local_hour"), ("weekday", "weekday"), ("month", "month"), ("season", "season"), ("load_regime", "load_regime"), ("temperature_regime", "temperature_regime"), ("humidity_regime", "humidity_regime"), ("wind_speed_regime", "wind_speed_regime")):
        add_group(grouped, frame, column, name)
    grouped_frame = pd.DataFrame(grouped)
    artifacts = run_dir / "artifacts"
    artifacts.mkdir(parents=True)
    grouped_path = artifacts / "grouped_errors.csv"
    grouped_frame.to_csv(grouped_path, index=False, lineterminator="\n", float_format="%.17g")
    comparison = pd.read_csv(metrics_path)
    comparison = comparison.set_index("model").loc[list(MODELS)].reset_index()
    frame["target_day"] = frame.target_timestamp.dt.floor("D")
    daily = frame.groupby(["model", "target_day"], as_index=False).agg(rmse_mw=("residual_mw", lambda x: float(np.sqrt(np.mean(x.to_numpy() ** 2)))), n=("residual_mw", "size"))
    by_lag = {}
    for model, part in frame.sort_values("target_timestamp").groupby("model", sort=False):
        residual = part.drop_duplicates("target_timestamp").set_index("target_timestamp").residual_mw
        by_lag[model] = {str(lag): {"pairs": int(residual.notna().sum() - lag), "correlation": float(residual.autocorr(lag=lag))} for lag in (24, 168)}
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    for model in MODELS:
        part = frame.loc[frame.model.eq(model)].sort_values("target_timestamp")
        axes[1].plot(part.target_timestamp, part.residual_mw, linewidth=0.65, label=model)
    truth = frame.loc[frame.model.eq("persistence")].sort_values("target_timestamp")
    axes[0].plot(truth.target_timestamp, truth.y_true_mw, color="black", linewidth=0.7)
    axes[0].set_ylabel("Load (MW)")
    axes[0].plot(truth.target_timestamp, truth.y_true_mw, color="black", linewidth=0.7, label="Actual MW")
    axes[0].legend()
    axes[1].axhline(0, color="black", linewidth=0.7)
    axes[1].set_ylabel("Observed − forecast (MW)")
    axes[1].set_xlabel("Target timestamp (UTC)")
    axes[1].legend(ncol=5)
    fig.tight_layout()
    actual_plot = artifacts / "actual_vs_predicted.png"
    fig.savefig(actual_plot, dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot([frame.loc[frame.model.eq(model), "residual_mw"].to_numpy() for model in MODELS], tick_labels=MODELS, showfliers=False)
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_ylabel("Observed − forecast (MW)")
    ax.set_title("Test residual distributions (outliers hidden for readability)")
    fig.tight_layout()
    residual_plot = artifacts / "residual_distributions.png"
    fig.savefig(residual_plot, dpi=150)
    plt.close(fig)
    profile = grouped_frame[grouped_frame.dimension.eq("local_hour")].pivot(index="group", columns="model", values="mae_mw").reindex([str(x) for x in range(24)])
    fig, ax = plt.subplots(figsize=(12, 6))
    for model in MODELS:
        ax.plot(range(24), profile[model], marker="o", markersize=3, label=model)
    ax.set_xticks(range(24))
    ax.set_xlabel("Local target hour (Europe/Madrid)")
    ax.set_ylabel("MAE (MW)")
    ax.legend(ncol=5)
    fig.tight_layout()
    profile_plot = artifacts / "grouped_error_profiles.png"
    fig.savefig(profile_plot, dpi=150)
    plt.close(fig)
    xgb_valid = json.loads((ROOT / "runs/20261118_system312_g01_01/artifacts/metrics.json").read_text(encoding="utf-8"))
    lstm_findings = (ROOT / "docs/results/lstm_findings.md").read_text(encoding="utf-8")
    eda_findings = (ROOT / "docs/results/eda_findings.md").read_text(encoding="utf-8")
    winners = comparison.sort_values(["rmse_mw", "mae_mw"]).model.tolist()
    load_only = xgb_valid["selected"]["XGB_load_only"]
    xgb_full = xgb_valid["selected"]["XGB_full"]
    best_daily = daily.sort_values("rmse_mw", ascending=False).head(5)
    rows = ["# Practice 4 — Test comparison and error analysis", "", f"H02 run `{run_id}` consumes accepted H01 run `{h01_run_id}`. All five models use the common {comparison.n_scored.iloc[0]:,}-target sample. Metrics are in MW; test ranking is descriptive and did not change model selection.", "", "## Test metrics", "", "| Model | MAE (MW) | RMSE (MW) | MAPE (%) |", "|---|---:|---:|---:|"]
    for row in comparison.itertuples():
        rows.append(f"| {row.model} | {row.mae_mw:.2f} | {row.rmse_mw:.2f} | {row.mape_percent:.4f} |")
    rows += ["", f"RMSE order: {' → '.join(winners)}.", "", "## Analysis questions", "", "### 1. Which weather variable has the strongest relationship with load?", "For linear association in observed training data, humidity is strongest by absolute Pearson correlation (r = -0.367), compared with temperature (r = 0.236) and wind (r = 0.209). This is association, not causation or proof of strongest nonlinear predictive value. In G01, temperature has the largest weather feature-gain total, while the validation load-only ablation actually beats full XGB by 12.77 MW RMSE; weather therefore did not improve that selected comparison.", "", f"G01 validation full RMSE: {xgb_full.get('rmse_mw', float('nan')):.2f} MW; load-only RMSE: {load_only.get('rmse_mw', float('nan')):.2f} MW. Test weather strata are descriptive associations only. {eda_findings.splitlines()[0]}", "", "### 2. When does VAR fail?", "VAR has the largest test RMSE among the three learned models. The grouped table reports exact MAE/RMSE by target hour, weekday, season, month, train-defined load regime, and independent weather regimes; inspect the largest VAR RMSE rows there. The accepted Phase 6 residual whiteness test rejected white noise at 5%, indicating remaining residual dependence. Group differences are descriptive and do not establish why errors occur.", "", "### 3. What does XGBoost learn from weather?", "G01 gain totals were 22.64 million for temperature, 16.03 million for humidity, and 12.08 million for wind, versus 1,556.96 million for load. These gains are affected by correlated inputs and are not causal importance. Its validation full model was 12.77 MW RMSE worse than load-only, so weather's incremental benefit was not demonstrated in this comparison. H02 weather bins show only test-period error associations.", "", "### 4. Which cycles does LSTM learn?", "Evidence supports a daily pattern more clearly than a weekly one. G02 validation residual correlation was 0.2416 at UTC lag 24 and 0.0958 at lag 168 (5,231 and 5,087 pairs). On test these were 0.2449 and 0.1301 (5,235 and 5,091 pairs). Local-hour and weekday errors are in `grouped_errors.csv`; neither correlation proves a learned cycle, and a 24-hour input has no direct lag-168 observation. Local-hour grouping retains both repeated DST fall-back hours.", "", "### 5. Is LSTM overfitting?", "The selected trial's best validation epoch was 47 and it stopped at epoch 50. From epoch 47 to 50, training loss stayed near 0.0091 while validation loss rose from 0.012380 to 0.013902; restoring epoch 47 was appropriate. The train/validation inference MSE gap was 0.001648. This is evidence of late overfit pressure, not proof of broad generalization failure; validation also served early stopping and selection.", "", "### 6. How do ML and DL differ here?", f"On this held-out window XGBoost ranks ahead of LSTM by RMSE ({comparison.set_index('model').loc['XGB','rmse_mw']:.2f} vs {comparison.set_index('model').loc['LSTM','rmse_mw']:.2f} MW) and MAE ({comparison.set_index('model').loc['XGB','mae_mw']:.2f} vs {comparison.set_index('model').loc['LSTM','mae_mw']:.2f} MW). Validation had selected LSTM across the five candidates, illustrating that the single test-period ranking differs; test results do not alter selection. XGBoost uses engineered lag/statistic features and has feature-gain interpretation; LSTM consumes a 24×4 sequence and had 30,113 trainable parameters. G01's 18 CPU trials used 46.5 fit seconds versus 425.1 seconds for G02's two CPU trials. Neither model is causal, and the LSTM is less directly interpretable.", "", "## Temporal error notes", "", "The five dates with highest daily RMSE for at least one model are:"]
    for row in best_daily.itertuples():
        rows.append(f"- {row.model}, {row.target_day.date()}: RMSE {row.rmse_mw:.2f} MW across {int(row.n)} scored targets.")
    rows += ["", "Exact UTC residual autocorrelation:", "", "| Model | Lag 24 pairs / correlation | Lag 168 pairs / correlation |", "|---|---:|---:|"]
    for model in MODELS:
        rows.append(f"| {model} | {by_lag[model]['24']['pairs']} / {by_lag[model]['24']['correlation']:.4f} | {by_lag[model]['168']['pairs']} / {by_lag[model]['168']['correlation']:.4f} |")
    rows += ["", "## Grouped analysis and limitations", "", "`grouped_errors.csv` reports count, bias, MAE, RMSE, and MAPE for local hour, weekday, month, season, train-defined load regime, and independent train-defined weather proxy regimes. Sparse bins remain visible. Load groups use scored raw target load and are retrospective. Weather groups use origin-hour weather from the H01 sidecar. No canonical test rows were reopened.", "", "The test window is a single held-out segment from late May through December 2018. Weather proxy data are a five-city unweighted mean with known representativeness limits. One-step walk-forward reveals each observed truth after scoring under the lab availability assumption; production availability may differ.", ""]
    report_data = "\n".join(rows).encode("utf-8")
    report = artifacts / "model_comparison.md"
    report.write_bytes(report_data)
    files = (grouped_path, actual_plot, residual_plot, profile_plot, report)
    manifest_out = {"schema_version":"1","run_id":run_id,"stage_id":"H02","status":"completed","h01_run_id":h01_run_id,"inputs":{"evaluation_manifest_sha256":digest(manifest_path),"predictions_sha256":digest(prediction_path),"metrics_sha256":digest(metrics_path),"diagnostic_context_sha256":digest(diagnostic_path)},"outputs":{p.name:digest(p) for p in files}}
    (run_dir / "manifest.json").write_text(json.dumps(manifest_out, indent=2) + "\n", encoding="utf-8", newline="\r\n")
    official = ROOT / "docs/results/model_comparison.md"
    official.write_bytes(report_data)
    figure_dest = ROOT / "outputs/figures"
    for path in (actual_plot, residual_plot, profile_plot):
        (figure_dest / path.name).write_bytes(path.read_bytes())
    print(json.dumps({"run_id":run_id,"test_metrics":comparison.to_dict(orient="records"),"group_rows":len(grouped_frame),"outputs":{p.name:digest(p) for p in files}},indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--h01-run-id", default="20261120_system312_h01_03")
    args = parser.parse_args()
    run(args.run_id, args.h01_run_id)


if __name__ == "__main__":
    main()
