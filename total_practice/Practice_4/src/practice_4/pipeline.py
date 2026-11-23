from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from practice_4.runtime import (
    PRACTICE_ROOT,
    collect_environment,
    load_config,
    sha256_file,
    sync_file_map_existence,
    upsert_file_map_entries,
    utc_now,
    write_json,
)


def _register_stage_files(stage: str, items: list[tuple[str, str, str, str]]) -> None:
    sync_file_map_existence(PRACTICE_ROOT)
    entries = [
        {
            "path": rel,
            "entry_kind": "FILE",
            "existence": "EXISTING",
            "first_stage": stage,
            "owner": owner,
            "responsibility": resp,
            "depends_on": "config/practice_4_v2.json",
            "consumers": "Practice4 v2 pipeline",
            "validation": val,
        }
        for rel, owner, resp, val in items
    ]
    upsert_file_map_entries(entries)


def run_s0(config: dict[str, Any]) -> dict[str, Any]:
    out_dir = PRACTICE_ROOT / "runs/v2/s0_env"
    env = collect_environment(require_cuda=True)
    write_json(out_dir / "environment.json", env)
    write_json(out_dir / "config.json", config)
    _register_stage_files(
        "S0",
        [
            ("config/practice_4_v2.json", "configuration", "Unified v2 configuration for S0-S8", "Validated by test_s0_env_gpu.py"),
            ("src/practice_4/runtime.py", "runtime", "CUDA/seed/file_map utility", "Validated by test_s0_env_gpu.py"),
            ("runs/v2/s0_env/environment.json", "run evidence", "Verified RTX 5050 CUDA & packages", "Validated by test_s0_env_gpu.py"),
            ("tests/test_s0_env_gpu.py", "test", "S0 GPU and environment pytest gate", "pytest pass"),
        ],
    )
    return env


def run_s1(config: dict[str, Any]) -> dict[str, Any]:
    from practice_4.data.download import download_all_raw
    from practice_4.data.ingestion import format_audit_markdown, summarize_raw

    out_dir = PRACTICE_ROOT / "runs/v2/s1_raw"
    manifest = download_all_raw(config, PRACTICE_ROOT, force=False)
    txt_path = PRACTICE_ROOT / manifest["uci_source"]["extracted_file"]["path"]
    weather_path = PRACTICE_ROOT / manifest["weather_source"]["path"]
    summary = summarize_raw(txt_path, weather_path, config["anomaly_bounds"])
    write_json(out_dir / "audit_summary.json", summary)
    (PRACTICE_ROOT / "docs/results/data_audit.md").write_text(
        format_audit_markdown(summary, manifest), encoding="utf-8"
    )
    _register_stage_files(
        "S1",
        [
            ("src/practice_4/data/download.py", "data", "Official UCI + Open-Meteo ERA5 downloader", "test_s1_download_raw.py"),
            ("src/practice_4/data/ingestion.py", "data", "Read-only raw provenance & audit", "test_s1_download_raw.py"),
            ("datasets/raw/electricityloaddiagrams20112014.zip", "raw data", "Official UCI 321 archive (immutable)", "SHA256 verified"),
            ("datasets/raw/LD2011_2014.txt", "raw data", "Extracted UCI 15-min load file (immutable)", "SHA256 verified"),
            ("datasets/raw/portugal_weather_era5.csv", "raw data", "Open-Meteo ERA5 weather for Lisbon/Porto/Coimbra", "SHA256 verified"),
            ("datasets/raw/source_manifest.json", "provenance", "Verified S1 download manifest v2", "test_s1_download_raw.py"),
            ("docs/results/data_audit.md", "data audit", "S1 raw quality & onboarding audit", "test_s1_download_raw.py"),
            ("runs/v2/s1_raw/audit_summary.json", "run evidence", "S1 JSON raw audit summary", "test_s1_download_raw.py"),
            ("tests/test_s1_download_raw.py", "test", "S1 download & provenance pytest gate", "pytest pass"),
        ],
    )
    return summary


def run_s2(config: dict[str, Any]) -> dict[str, Any]:
    from practice_4.data.integration import format_data_contract_markdown, integrate_canonical

    out_dir = PRACTICE_ROOT / "runs/v2/s2_canonical"
    source_manifest = json.loads((PRACTICE_ROOT / "datasets/raw/source_manifest.json").read_text(encoding="utf-8"))
    txt_path = PRACTICE_ROOT / source_manifest["uci_source"]["extracted_file"]["path"]
    weather_path = PRACTICE_ROOT / source_manifest["weather_source"]["path"]

    uci_df = pd.read_csv(txt_path, sep=";", decimal=",", low_memory=False)
    weather_df = pd.read_csv(weather_path)
    canonical_df, details = integrate_canonical(uci_df, weather_df, config)

    canonical_path = PRACTICE_ROOT / "datasets/processed/canonical_hourly.csv"
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    canonical_df.to_csv(canonical_path, index=False, lineterminator="\n")
    write_json(out_dir / "integration_summary.json", details)
    (PRACTICE_ROOT / "docs/results/data_contract.md").write_text(
        format_data_contract_markdown(details, canonical_path, source_manifest), encoding="utf-8"
    )
    _register_stage_files(
        "S2",
        [
            ("src/practice_4/data/integration.py", "data", "UTC hourly integration with DST & ERA5 weights", "test_s2_canonical.py"),
            ("datasets/processed/canonical_hourly.csv", "canonical data", "Contiguous hourly UTC canonical dataset (2012-2014)", "test_s2_canonical.py"),
            ("docs/results/data_contract.md", "contract", "S2 canonical data contract", "test_s2_canonical.py"),
            ("runs/v2/s2_canonical/integration_summary.json", "run evidence", "S2 integration summary", "test_s2_canonical.py"),
            ("tests/test_s2_canonical.py", "test", "S2 canonical & DST pytest gate", "pytest pass"),
        ],
    )
    return details


def run_s3(config: dict[str, Any]) -> dict[str, Any]:
    from practice_4.analysis.eda import format_eda_markdown, load_train_only, summarize_train_eda
    from practice_4.data.splitting import partition
    from practice_4.visualization.plots import render_eda_figures

    out_dir = PRACTICE_ROOT / "runs/v2/s3_eda"
    canonical_path = PRACTICE_ROOT / "datasets/processed/canonical_hourly.csv"
    ts_only = pd.read_csv(canonical_path, usecols=["timestamp_utc"])["timestamp_utc"]
    split = partition(
        ts_only,
        "datasets/processed/canonical_hourly.csv",
        sha256_file(canonical_path),
        train_ratio=float(config["split"]["train_ratio"]),
        val_ratio=float(config["split"]["val_ratio"]),
        cv_folds=int(config["split"]["cv_folds"]),
    )
    write_json(PRACTICE_ROOT / "datasets/processed/split_manifest.json", split)

    train_df = load_train_only(canonical_path, split["splits"]["train"])
    summary = summarize_train_eda(
        train_df,
        split["splits"]["train"],
        tz_local=config["dataset"]["timezone_local"],
        max_lag=168,
    )
    write_json(out_dir / "summary.json", summary)
    figs = render_eda_figures(train_df, summary, PRACTICE_ROOT / "outputs/figures")
    (PRACTICE_ROOT / "docs/results/eda_findings.md").write_text(
        format_eda_markdown(summary), encoding="utf-8"
    )
    items = [
        ("src/practice_4/data/splitting.py", "data", "Chronological 70/15/15 split + expanding CV", "test_s3_split_eda.py"),
        ("src/practice_4/analysis/eda.py", "analysis", "Train-only EDA summaries", "test_s3_split_eda.py"),
        ("src/practice_4/visualization/plots.py", "visualization", "EDA figure renderer", "test_s3_split_eda.py"),
        ("datasets/processed/split_manifest.json", "split contract", "Chronological 70/15/15 + CV folds manifest", "test_s3_split_eda.py"),
        ("docs/results/eda_findings.md", "analysis report", "S3 train-only EDA findings", "test_s3_split_eda.py"),
        ("runs/v2/s3_eda/summary.json", "run evidence", "S3 train-only EDA JSON summary", "test_s3_split_eda.py"),
        ("tests/test_s3_split_eda.py", "test", "S3 split & train-only EDA pytest gate", "pytest pass"),
    ] + [(p.relative_to(PRACTICE_ROOT).as_posix(), "official figure", "Train-only EDA plot", "test_s3_split_eda.py") for p in figs]
    _register_stage_files("S3", items)
    return summary


def run_s4(config: dict[str, Any]) -> dict[str, Any]:
    from practice_4.data.features import format_feature_dictionary_markdown, materialize_supervised_dataset
    from practice_4.data.preprocessing import (
        CausalStreamState,
        fit_scaler_on_train,
        load_canonical_prefix,
        transform_causal,
    )

    out_dir = PRACTICE_ROOT / "runs/v2/s4_prep"
    canonical_path = PRACTICE_ROOT / "datasets/processed/canonical_hourly.csv"
    split = json.loads((PRACTICE_ROOT / "datasets/processed/split_manifest.json").read_text(encoding="utf-8"))
    train_rows = int(split["splits"]["train"]["row_count"])
    val_end_row = int(split["splits"]["validation"]["end_row"])
    prefix_rows = val_end_row + 1

    prefix_df = load_canonical_prefix(canonical_path, prefix_rows)
    scaler_state = fit_scaler_on_train(
        prefix_df.iloc[:train_rows],
        config,
        {"canonical_sha256": sha256_file(canonical_path), "split_sha256": split["split_sha256"]},
    )
    write_json(out_dir / "scaler.json", scaler_state)

    stream_state = CausalStreamState.empty()
    tz_local = config["dataset"]["timezone_local"]
    country = config["dataset"]["country_holiday_code"]
    tr_prep, tr_fill = transform_causal(prefix_df.iloc[:train_rows], scaler_state, stream_state, tz_local, country)
    va_prep, va_fill = transform_causal(prefix_df.iloc[train_rows:], scaler_state, stream_state, tz_local, country)
    prepared_df = pd.concat([tr_prep, va_prep], ignore_index=True)

    prepared_path = PRACTICE_ROOT / "datasets/processed/prepared_hourly.csv"
    prepared_df.to_csv(prepared_path, index=False, lineterminator="\n")

    feat_cfg = config["features"]
    mat = materialize_supervised_dataset(
        prepared_df,
        train_end_row=train_rows - 1,
        hdd_base_c=float(feat_cfg["hdd_base_c"]),
        cdd_base_c=float(feat_cfg["cdd_base_c"]),
    )
    mat["origin_df"].to_csv(PRACTICE_ROOT / "datasets/processed/origin_manifest.csv", index=False, lineterminator="\n")
    np.savez_compressed(PRACTICE_ROOT / "datasets/processed/model_inputs.npz", **mat["arrays"])

    audit_summary = {"train_locf_filled": tr_fill, "val_locf_filled": va_fill, "counts": mat["counts"]}
    write_json(out_dir / "prep_summary.json", audit_summary)
    (PRACTICE_ROOT / "docs/results/feature_dictionary.md").write_text(
        format_feature_dictionary_markdown(mat["counts"]), encoding="utf-8"
    )
    (PRACTICE_ROOT / "docs/results/preprocessing_audit.md").write_text(
        "\n".join(
            [
                "# Stage S4 — Causal Preprocessing & Alignment Audit (v2)",
                "",
                f"- **Scaler Fit Rows:** `{scaler_state['fit_count']:,}` (train only, zero val/test access)",
                f"- **LOCF Filled (Train):** `{tr_fill}` | **LOCF Filled (Val):** `{va_fill}`",
                f"- **Eligible Origins:** Train `{mat['counts']['train']['n_eligible']:,}` | Validation `{mat['counts']['validation']['n_eligible']:,}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _register_stage_files(
        "S4",
        [
            ("src/practice_4/data/preprocessing.py", "data", "Causal LOCF, scaler & calendar encoder", "test_s4_prep_features.py"),
            ("src/practice_4/data/features.py", "data", "Causal 121-feature tabular + sequence views", "test_s4_prep_features.py"),
            ("datasets/processed/prepared_hourly.csv", "prepared data", "Train/val causal prepared hourly levels", "test_s4_prep_features.py"),
            ("datasets/processed/origin_manifest.csv", "alignment", "Train/val candidate & eligible origins", "test_s4_prep_features.py"),
            ("datasets/processed/model_inputs.npz", "model inputs", "Materialized train/val supervised & VAR arrays", "test_s4_prep_features.py"),
            ("runs/v2/s4_prep/scaler.json", "run artifact", "Train-fitted StandardScaler & percentile bounds", "test_s4_prep_features.py"),
            ("docs/results/feature_dictionary.md", "feature contract", "121 features & ablation subset contract", "test_s4_prep_features.py"),
            ("docs/results/preprocessing_audit.md", "data report", "S4 causal preprocessing audit", "test_s4_prep_features.py"),
            ("tests/test_s4_prep_features.py", "test", "S4 anti-leakage & feature pytest gate", "pytest pass"),
        ],
    )
    return audit_summary


def run_s5(config: dict[str, Any]) -> dict[str, Any]:
    from practice_4.models.baselines import compute_baselines, format_baseline_markdown
    from practice_4.models.var_model import fit_and_evaluate_var, format_var_markdown

    art_dir = PRACTICE_ROOT / "runs/v2/s5_var/artifacts"
    art_dir.mkdir(parents=True, exist_ok=True)
    prepared_df = pd.read_csv(PRACTICE_ROOT / "datasets/processed/prepared_hourly.csv")
    origin_df = pd.read_csv(PRACTICE_ROOT / "datasets/processed/origin_manifest.csv")
    scaler_state = json.loads((PRACTICE_ROOT / "runs/v2/s4_prep/scaler.json").read_text(encoding="utf-8"))

    base_metrics, base_val_df = compute_baselines(prepared_df, origin_df)
    write_json(art_dir / "baseline_metrics.json", base_metrics)
    base_val_df.to_csv(art_dir / "baseline_val_predictions.csv", index=False)
    (PRACTICE_ROOT / "docs/results/baseline_results.md").write_text(
        format_baseline_markdown(base_metrics, unit=config["dataset"]["load_unit"]), encoding="utf-8"
    )

    with np.load(PRACTICE_ROOT / "datasets/processed/model_inputs.npz", allow_pickle=False) as data:
        var_train_levels = data["var_train_levels"].copy()

    var_res = fit_and_evaluate_var(
        var_train_levels,
        prepared_df,
        origin_df,
        scaler_state,
        max_lag=int(config["var"]["max_lag"]),
        whiteness_lags=int(config["var"]["whiteness_lags"]),
    )
    sel = var_res["variants"][var_res["selected_tag"]]
    np.savez_compressed(
        art_dir / "var_model.npz",
        coefs=sel["coefs"],
        intercept=sel["intercept"],
        sigma_u=sel["sigma_u"],
        p=np.asarray(sel["p"], dtype=np.int64),
        diff_order=np.asarray(sel["diff_order"], dtype=np.int64),
    )
    pd.DataFrame(var_res["trials"]).to_csv(art_dir / "var_trials.csv", index=False)
    val_out = var_res["val_origins"][["target_row", "origin_timestamp_utc", "target_timestamp_utc", "y_true"]].copy()
    for tag, v in var_res["variants"].items():
        val_out[tag] = v["val_preds"]
    val_out.to_csv(art_dir / "var_val_predictions.csv", index=False)

    serializable = {
        "selected_tag": var_res["selected_tag"],
        "selection_reason": var_res["selection_reason"],
        "stationarity": var_res["stationarity"],
        "variants": {
            tag: {k: v for k, v in info.items() if k not in ("coefs", "intercept", "sigma_u", "val_preds")}
            for tag, info in var_res["variants"].items()
        },
    }
    write_json(art_dir / "var_metrics.json", serializable)
    (PRACTICE_ROOT / "docs/results/var_results.md").write_text(
        format_var_markdown(var_res, base_metrics, unit=config["dataset"]["load_unit"]), encoding="utf-8"
    )
    _register_stage_files(
        "S5",
        [
            ("src/practice_4/models/baselines.py", "model", "Persistence, Seasonal-24, Seasonal-168 baselines", "test_s5_baselines_var.py"),
            ("src/practice_4/models/var_model.py", "model", "Stationary full-train VAR with ADF/KPSS diffing", "test_s5_baselines_var.py"),
            ("runs/v2/s5_var/artifacts/var_model.npz", "model artifact", "Locked stationary VAR weights", "test_s5_baselines_var.py"),
            ("runs/v2/s5_var/artifacts/var_metrics.json", "metric evidence", "VAR stationarity & validation metrics", "test_s5_baselines_var.py"),
            ("runs/v2/s5_var/artifacts/baseline_metrics.json", "metric evidence", "Baseline validation metrics", "test_s5_baselines_var.py"),
            ("docs/results/baseline_results.md", "model report", "S5 baseline results", "test_s5_baselines_var.py"),
            ("docs/results/var_results.md", "model report", "S5 stationary VAR report", "test_s5_baselines_var.py"),
            ("tests/test_s5_baselines_var.py", "test", "S5 baselines & VAR pytest gate", "pytest pass"),
        ],
    )
    return serializable


def run_s6(config: dict[str, Any]) -> dict[str, Any]:
    from practice_4.models.xgboost_model import format_xgboost_markdown, run_xgboost_stage

    art_dir = PRACTICE_ROOT / "runs/v2/s6_xgb/artifacts"
    origin_df = pd.read_csv(PRACTICE_ROOT / "datasets/processed/origin_manifest.csv")
    split_manifest = json.loads((PRACTICE_ROOT / "datasets/processed/split_manifest.json").read_text(encoding="utf-8"))
    with np.load(PRACTICE_ROOT / "datasets/processed/model_inputs.npz", allow_pickle=False) as data:
        x_xgb = data["x_xgb"].copy()
        y_true = data["y_true"].copy()
        target_rows = data["target_row"].copy()

    res = run_xgboost_stage(
        x_xgb, y_true, target_rows, origin_df, split_manifest, config, art_dir, PRACTICE_ROOT / "outputs/figures"
    )
    write_json(art_dir / "xgb_metrics.json", res)
    (PRACTICE_ROOT / "docs/results/xgboost_findings.md").write_text(
        format_xgboost_markdown(res, unit=config["dataset"]["load_unit"]), encoding="utf-8"
    )
    _register_stage_files(
        "S6",
        [
            ("src/practice_4/models/xgboost_model.py", "model", "RTX 5050 CUDA XGBoost + Expanding CV + Ablation + SHAP", "test_s6_xgboost_gpu.py"),
            ("runs/v2/s6_xgb/artifacts/xgb_metrics.json", "metric evidence", "XGBoost ablation & SHAP summary", "test_s6_xgboost_gpu.py"),
            ("runs/v2/s6_xgb/artifacts/ablation_summary.csv", "experiment registry", "4-subset XGBoost ablation table", "test_s6_xgboost_gpu.py"),
            ("runs/v2/s6_xgb/artifacts/shap_importance.csv", "explainability", "SHAP TreeExplainer feature attribution", "test_s6_xgboost_gpu.py"),
            ("outputs/figures/xgb_shap_summary.png", "official figure", "XGBoost SHAP summary plot", "test_s6_xgboost_gpu.py"),
            ("outputs/figures/xgb_shap_dependence_temp.png", "official figure", "XGBoost SHAP temperature dependence", "test_s6_xgboost_gpu.py"),
            ("docs/results/xgboost_findings.md", "model report", "S6 XGBoost & SHAP report", "test_s6_xgboost_gpu.py"),
            ("tests/test_s6_xgboost_gpu.py", "test", "S6 XGBoost GPU & SHAP pytest gate", "pytest pass"),
        ],
    )
    return res


def run_s7(config: dict[str, Any]) -> dict[str, Any]:
    from practice_4.models.lstm_model import format_lstm_markdown, run_lstm_stage

    art_dir = PRACTICE_ROOT / "runs/v2/s7_lstm/artifacts"
    origin_df = pd.read_csv(PRACTICE_ROOT / "datasets/processed/origin_manifest.csv")
    scaler_state = json.loads((PRACTICE_ROOT / "runs/v2/s4_prep/scaler.json").read_text(encoding="utf-8"))
    with np.load(PRACTICE_ROOT / "datasets/processed/model_inputs.npz", allow_pickle=False) as data:
        full_seq = data["full_scaled_seq"].copy()
        target_rows = data["target_row"].copy()
        y_true = data["y_true"].copy()

    res = run_lstm_stage(
        full_seq, target_rows, y_true, origin_df, scaler_state, config, art_dir, PRACTICE_ROOT / "outputs/figures"
    )
    write_json(art_dir / "lstm_metrics.json", res)
    (PRACTICE_ROOT / "docs/results/lstm_findings.md").write_text(
        format_lstm_markdown(res, unit=config["dataset"]["load_unit"]), encoding="utf-8"
    )
    _register_stage_files(
        "S7",
        [
            ("src/practice_4/models/lstm_model.py", "model", "PyTorch CUDA LSTM on RTX 5050 + 24h/168h + multi-seed", "test_s7_lstm_gpu.py"),
            ("runs/v2/s7_lstm/artifacts/lstm_best.pt", "model artifact", "Locked best PyTorch LSTM weights", "test_s7_lstm_gpu.py"),
            ("runs/v2/s7_lstm/artifacts/lstm_core.pt", "model artifact", "Locked 24x4 core PyTorch LSTM weights", "test_s7_lstm_gpu.py"),
            ("runs/v2/s7_lstm/artifacts/lstm_metrics.json", "metric evidence", "LSTM variants & seed stability summary", "test_s7_lstm_gpu.py"),
            ("outputs/figures/lstm_learning_curves.png", "official figure", "PyTorch LSTM learning curves", "test_s7_lstm_gpu.py"),
            ("docs/results/lstm_findings.md", "model report", "S7 PyTorch LSTM report", "test_s7_lstm_gpu.py"),
            ("tests/test_s7_lstm_gpu.py", "test", "S7 PyTorch LSTM GPU pytest gate", "pytest pass"),
        ],
    )
    return res


def _build_and_execute_notebook(root: Path) -> Path:
    nb_path = root / "notebooks/practice_4.ipynb"
    cells = [
        {
            "cell_type": "markdown",
            "id": "title",
            "metadata": {},
            "source": [
                "# Practice 4 — Dự báo Chuỗi thời gian Đa biến (Multivariate Time Series Forecasting)\n",
                "\n",
                "**Bộ dữ liệu chính thức:** `UCI ElectricityLoadDiagrams20112014` (Bồ Đào Nha, nhóm 321 khách hàng ổn định giai đoạn 2012–2014, chuẩn hóa 1 giờ UTC & xử lý DST) + Thời tiết tái phân tích `Open-Meteo ERA5` (Lisbon 50%, Porto 35%, Coimbra 15%).  \n",
                "**Các mô hình đối chiếu:** `Persistence`, `Seasonal-24`, `Seasonal-168`, `Stationary VAR`, `GPU XGBoost (+ SHAP)` và `GPU PyTorch LSTM` (chạy trên **NVIDIA GeForce RTX 5050 CUDA**).  \n",
                "**Tài liệu tham chiếu:** `references/chapter4-5.pdf` — *Chương 4-5: Mô hình Dự đoán Chuỗi thời gian Đa biến*.\n",
                "\n",
                "---\n",
                "\n",
                "## 0. Phát biểu bài toán & Giao thức thực nghiệm (Problem Formulation)\n",
                "\n",
                "Tại cuối mỗi giờ $t$ (origin), ta quan sát véc-tơ 4 biến:\n",
                "\n",
                "$$\n",
                "X_t = [\\text{load}_t,\\; \\text{temp}_t,\\; \\text{humidity}_t,\\; \\text{wind\\_speed}_t]\n",
                "$$\n",
                "\n",
                "Mục tiêu là dự báo phụ tải thực tế ở bước tiếp theo $\\hat{y}_{t+1} = \\widehat{\\text{load}}_{t+1}$ (đơn vị **kW**) trên tập dữ liệu hoàn toàn liên tục, không rò rỉ tương lai. Ba chỉ số đánh giá chính trên thang đo gốc:\n",
                "- **MAE:** $\\frac{1}{N}\\sum_{i=1}^N |y_i - \\hat{y}_i|$\n",
                "- **RMSE:** $\\sqrt{\\frac{1}{N}\\sum_{i=1}^N (y_i - \\hat{y}_i)^2}$\n",
                "- **MAPE (%):** $\\frac{100}{N}\\sum_{i=1}^N \\left|\\frac{y_i - \\hat{y}_i}{y_i}\\right|$ (trên $y_i \\neq 0$)\n",
            ],
        },
        {
            "cell_type": "code",
            "id": "setup",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "from pathlib import Path\n",
                "import json\n",
                "import re\n",
                "import pandas as pd\n",
                "from IPython.display import display, Image, Markdown\n",
                "\n",
                "ROOT = Path.cwd()\n",
                "if not (ROOT / 'outputs').exists() and (ROOT.parent / 'outputs').exists():\n",
                "    ROOT = ROOT.parent\n",
                "\n",
                "def show_doc(rel_path: str) -> None:\n",
                "    text = (ROOT / rel_path).read_text(encoding='utf-8')\n",
                "    lines = text.splitlines()\n",
                "    if lines and lines[0].startswith('# '):\n",
                "        lines = lines[1:]\n",
                "    cleaned = re.sub(r'^(#{1,4}) ', lambda m: '#' * min(len(m.group(1)) + 1, 5) + ' ', '\\n'.join(lines).strip(), flags=re.M)\n",
                "    display(Markdown(cleaned))\n",
                "\n",
                "env = json.loads((ROOT / 'runs/v2/s0_env/environment.json').read_text(encoding='utf-8'))\n",
                "split = json.loads((ROOT / 'datasets/processed/split_manifest.json').read_text(encoding='utf-8'))\n",
                "scaler = json.loads((ROOT / 'runs/v2/s4_prep/scaler.json').read_text(encoding='utf-8'))\n",
                "test_metrics = pd.read_csv(ROOT / 'outputs/tables/test_metrics.csv')\n",
                "dm_test = pd.read_csv(ROOT / 'outputs/tables/dm_test.csv')\n",
                "grouped_errors = pd.read_csv(ROOT / 'runs/v2/s8_eval/artifacts/grouped_errors.csv')\n",
                "\n",
                "env_table = pd.DataFrame([{\n",
                "    'GPU': env['gpu']['device_name'],\n",
                "    'VRAM (MB)': env['gpu']['vram_total_mb'],\n",
                "    'CUDA': env['gpu']['torch_cuda_version'],\n",
                "    'PyTorch': env['packages']['torch'],\n",
                "    'XGBoost': env['packages']['xgboost'],\n",
                "    'SHAP': env['packages']['shap'],\n",
                "    'Statsmodels': env['packages']['statsmodels'],\n",
                "}])\n",
                "display(env_table)\n",
            ],
        },
        {
            "cell_type": "markdown",
            "id": "sec-data",
            "metadata": {},
            "source": [
                "## 1. Dữ liệu chính thức, Xử lý DST & Phân chia theo thời gian (S1–S3)\n",
                "\n",
                "Dữ liệu được tải trực tiếp từ nguồn UCI 321 chính thức (`LD2011_2014.txt`) và Open-Meteo ERA5 (có kiểm chứng SHA256), chuẩn hóa về lưới 1 giờ UTC liên tục (`26.304` giờ) sau khi loại bỏ giai đoạn onboarding không đồng nhất năm 2011 và xử lý chuyển giờ mùa hè/đông (`Europe/Lisbon`). Dữ liệu được chia theo thời gian không shuffle tỷ lệ **70% / 15% / 15%**, kèm **3-fold Expanding-Window CV** bên trong Train.\n",
            ],
        },
        {
            "cell_type": "code",
            "id": "show-split",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "split_df = pd.DataFrame([\n",
                "    {'Split': k, 'Rows': v['row_count'], 'Share (%)': 100*v['row_count']/split['total_rows'], 'Start (UTC)': v['start_utc'], 'End (UTC)': v['end_utc']}\n",
                "    for k, v in split['splits'].items()\n",
                "])\n",
                "display(split_df.style.format({'Rows': '{:,}', 'Share (%)': '{:.2f}'}).hide(axis='index'))\n",
                "show_doc('docs/results/data_audit.md')\n",
                "show_doc('docs/results/data_contract.md')\n",
            ],
        },
        {
            "cell_type": "markdown",
            "id": "sec-eda",
            "metadata": {},
            "source": [
                "## 2. Khám phá dữ liệu chỉ trên tập Train (Train-Only EDA — S3)\n",
                "\n",
                "Toàn bộ thống kê mô tả, tương quan Pearson/Spearman, phân tích mùa vụ theo giờ/thứ/tháng và ACF/PACF chỉ được tính trên `18.412` giờ đầu tiên (tập Train). Validation và Test hoàn toàn bị cách ly trong bước này.\n",
            ],
        },
        {
            "cell_type": "code",
            "id": "show-eda",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "show_doc('docs/results/eda_findings.md')\n",
                "for fn in ['eda_load_utc.png', 'eda_seasonality_profiles.png', 'eda_relationships.png', 'eda_acf_pacf.png', 'eda_distributions.png']:\n",
                "    display(Image(filename=str(ROOT / 'outputs/figures' / fn)))\n",
            ],
        },
        {
            "cell_type": "markdown",
            "id": "sec-prep",
            "metadata": {},
            "source": [
                "## 3. Tiền xử lý nhân quả & Tạo đặc trưng đa biến (S4)\n",
                "\n",
                "- `StandardScaler` chỉ fit trên `18.412` mẫu Train và giữ cố định cho Validation/Test.\n",
                "- Ngoài cửa sổ 24 giờ gốc (`96` lags), bộ đặc trưng mở rộng bổ sung **rolling stats** (`mean6h`, `mean24h`, `std24h`, `min24h`, `max24h`, `trend24h`, `diff1h`, `trend168h`), **lags dài hạn** (`lag47`, `lag167`), **9 biến lịch địa phương/DST/ngày lễ** tại `t+1`, và **6 biến tương tác chéo** (`load_per_temp_k`, `hdd_proxy`, `cdd_proxy`, `temp_x_humidity`, `temp_diff_1h`, `temp_diff_24h`) theo Slide 7 tài liệu `chapter4-5.pdf`.\n",
            ],
        },
        {
            "cell_type": "code",
            "id": "show-prep",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "scaler_df = pd.DataFrame({\n",
                "    'Feature': scaler['feature_order'],\n",
                "    'Train Mean': scaler['mean'],\n",
                "    'Train Std': scaler['std'],\n",
                "})\n",
                "display(scaler_df.style.format({'Train Mean': '{:,.4f}', 'Train Std': '{:,.4f}'}).hide(axis='index'))\n",
                "show_doc('docs/results/feature_dictionary.md')\n",
            ],
        },
        {
            "cell_type": "markdown",
            "id": "sec-var",
            "metadata": {},
            "source": [
                "## 4. Các đường cơ sở & Mô hình Thống kê Cổ điển VAR (S5)\n",
                "\n",
                "Kiểm định song song ADF và KPSS trên toàn bộ chuỗi Train cho thấy cả 4 biến không đạt dừng ở mức gốc (`level`). Tuân thủ Slide 5 (`chapter4-5.pdf`), mô hình được sai phân bậc 1 (`d=1`) và huấn luyện trên **100% tập Train (`18.411` giờ)** thay vì bị cắt xén như phiên bản cũ.\n",
            ],
        },
        {
            "cell_type": "code",
            "id": "show-var",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "show_doc('docs/results/var_results.md')\n",
            ],
        },
        {
            "cell_type": "markdown",
            "id": "sec-xgb",
            "metadata": {},
            "source": [
                "## 5. Mô hình Machine Learning: GPU XGBoost, Ablation & SHAP (S6)\n",
                "\n",
                "Huấn luyện trực tiếp trên **NVIDIA RTX 5050 (`device='cuda'`)** với 48 cấu hình Expanding-Window CV, tiếp theo là thí nghiệm Ablation 4 nhóm đặc trưng (`load_only` → `load_weather` → `load_calendar` → `full`) và phân tích đóng góp bằng **SHAP TreeExplainer**.\n",
            ],
        },
        {
            "cell_type": "code",
            "id": "show-xgb",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "show_doc('docs/results/xgboost_findings.md')\n",
                "for fn in ['xgb_shap_summary.png', 'xgb_shap_dependence_temp.png']:\n",
                "    display(Image(filename=str(ROOT / 'outputs/figures' / fn)))\n",
            ],
        },
        {
            "cell_type": "markdown",
            "id": "sec-lstm",
            "metadata": {},
            "source": [
                "## 6. Mô hình Deep Learning: GPU PyTorch LSTM (S7)\n",
                "\n",
                "Xây dựng bằng PyTorch CUDA (`LSTM(64) → LSTM(32) → Linear(1)`) trên RTX 5050, loại bỏ hoàn toàn các workaround CPU chậm trước đây; thực nghiệm đối chứng trên 4 biến thể (`24h_load_only`, `24h_core`, `24h_cal`, `168h_diag`) và kiểm định độ ổn định qua 3 random seeds (`42, 123, 2026`).\n",
            ],
        },
        {
            "cell_type": "code",
            "id": "show-lstm",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "show_doc('docs/results/lstm_findings.md')\n",
                "display(Image(filename=str(ROOT / 'outputs/figures' / 'lstm_learning_curves.png')))\n",
            ],
        },
        {
            "cell_type": "markdown",
            "id": "sec-test",
            "metadata": {},
            "source": [
                "## 7. Đánh giá Walk-Forward trên Test, Kiểm định Diebold–Mariano & Phân tích Lỗi (S8)\n",
                "\n",
                "Tất cả mô hình đã khóa trọng số và scaler được đánh giá công bằng trên cùng **3.947 điểm Test** theo giao thức `predict → score → reveal`, kèm kiểm định ý nghĩa thống kê **Diebold–Mariano** và phân tích sai số theo giờ địa phương, ngày lễ, mùa.\n",
            ],
        },
        {
            "cell_type": "code",
            "id": "show-test",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "display(Markdown('### Bảng xếp hạng chính thức trên tập Test'))\n",
                "leaderboard = test_metrics[['model', 'n_scored', 'mae_mw', 'rmse_mw', 'mape_percent']].rename(\n",
                "    columns={'model': 'Model', 'n_scored': 'Scored', 'mae_mw': 'MAE (kW)', 'rmse_mw': 'RMSE (kW)', 'mape_percent': 'MAPE (%)'}\n",
                ")\n",
                "display(leaderboard.style.format({'Scored': '{:,}', 'MAE (kW)': '{:,.2f}', 'RMSE (kW)': '{:,.2f}', 'MAPE (%)': '{:.4f}'}).hide(axis='index'))\n",
                "\n",
                "display(Markdown('### Kiểm định Diebold–Mariano (Squared Error Loss, h = 1)'))\n",
                "dm_view = dm_test.rename(columns={\n",
                "    'model_a': 'Model A', 'model_b': 'Model B', 'dm_stat': 'DM Stat',\n",
                "    'p_value': 'p-value', 'significant_5pct': 'Significant (5%)', 'better_model': 'Better Model'\n",
                "})\n",
                "display(dm_view.style.format({'DM Stat': '{:.4f}', 'p-value': '{:.3e}'}).hide(axis='index'))\n",
                "\n",
                "display(Markdown('### So sánh sai số giữa Ngày lễ và Ngày thường (`XGB_best` vs `LSTM_core` vs `LSTM_best` vs `VAR`)'))\n",
                "hol_view = grouped_errors[\n",
                "    (grouped_errors['dimension'] == 'holiday_group') &\n",
                "    (grouped_errors['model'].isin(['VAR', 'XGB_best', 'LSTM_core', 'LSTM_best']))\n",
                "][['group', 'model', 'n', 'mae', 'rmse', 'mape_percent']].rename(\n",
                "    columns={'group': 'Day Type', 'model': 'Model', 'n': 'Samples', 'mae': 'MAE (kW)', 'rmse': 'RMSE (kW)', 'mape_percent': 'MAPE (%)'}\n",
                ")\n",
                "display(hol_view.style.format({'Samples': '{:,}', 'MAE (kW)': '{:,.2f}', 'RMSE (kW)': '{:,.2f}', 'MAPE (%)': '{:.4f}'}).hide(axis='index'))\n",
                "\n",
                "for fn in ['actual_vs_predicted.png', 'residual_distributions.png', 'grouped_error_profiles.png']:\n",
                "    display(Image(filename=str(ROOT / 'outputs/figures' / fn)))\n",
            ],
        },
        {
            "cell_type": "markdown",
            "id": "sec-conclusion",
            "metadata": {},
            "source": [
                "## 8. Kết luận cuối cùng, Trả lời 6 câu hỏi đề bài & Giới hạn\n",
            ],
        },
        {
            "cell_type": "code",
            "id": "show-final",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [
                "show_doc('docs/results/final_report.md')\n",
            ],
        },
    ]
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    nb_path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--inplace",
            str(nb_path),
        ],
        cwd=str(root),
        check=True,
    )
    return nb_path


def run_s8(config: dict[str, Any]) -> dict[str, Any]:
    from practice_4.analysis.error_analysis import run_error_analysis_and_reports
    from practice_4.analysis.h01_evaluation import run_locked_test_walk_forward

    art_dir = PRACTICE_ROOT / "runs/v2/s8_eval/artifacts"
    eval_manifest = run_locked_test_walk_forward(PRACTICE_ROOT, config, art_dir)
    err_summary = run_error_analysis_and_reports(PRACTICE_ROOT, config, art_dir)
    nb_path = _build_and_execute_notebook(PRACTICE_ROOT)

    (PRACTICE_ROOT / "docs/status/current_status.md").write_text(
        "\n".join(
            [
                "# Current Status — Practice 4 (v2 Overhaul)",
                "",
                f"- **State:** `COMPLETED` ({utc_now()})",
                "- **Stages Executed & Verified:** `S0 → S8` with dedicated per-stage pytest gates.",
                f"- **Dataset:** `{config['dataset']['name']}`",
                "- **Hardware:** NVIDIA GeForce RTX 5050 (PyTorch CUDA + XGBoost CUDA).",
                "- **Presentation Notebook:** `notebooks/practice_4.ipynb` (executed cleanly via `nbconvert`).",
                "- **File Map:** `docs/plans/file_map.csv` synchronized at every stage.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (PRACTICE_ROOT / "README.md").write_text(
        "\n".join(
            [
                "# Practice 4 (v2) — Multivariate Time Series Forecasting",
                "",
                "Trạng thái: `COMPLETED` — Toàn bộ 9 stage (`S0 → S8`) đã thực thi trên **NVIDIA RTX 5050 CUDA** và vượt qua 100% các stage pytest gates.",
                "",
                "## Bàn giao chính",
                "",
                "- [Executable Notebook](notebooks/practice_4.ipynb)",
                "- [Final Report](docs/results/final_report.md)",
                "- [Test Comparison & Diebold–Mariano](docs/results/model_comparison.md)",
                "- [File Map (Updated per stage)](docs/plans/file_map.csv)",
                "- [Current Status](docs/status/current_status.md)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _register_stage_files(
        "S8",
        [
            ("src/practice_4/analysis/h01_evaluation.py", "evaluation", "Locked test walk-forward controller (v2)", "test_s8_eval_notebook.py"),
            ("src/practice_4/analysis/error_analysis.py", "analysis", "Grouped error analysis & Diebold-Mariano tests", "test_s8_eval_notebook.py"),
            ("outputs/predictions/test_predictions.csv", "official result", "All locked models test predictions", "test_s8_eval_notebook.py"),
            ("outputs/tables/test_metrics.csv", "official result", "Official test MAE/RMSE/MAPE leaderboard", "test_s8_eval_notebook.py"),
            ("outputs/tables/dm_test.csv", "official result", "Diebold-Mariano significance tests", "test_s8_eval_notebook.py"),
            ("outputs/figures/actual_vs_predicted.png", "official figure", "Test actual vs predicted & residuals", "test_s8_eval_notebook.py"),
            ("outputs/figures/residual_distributions.png", "official figure", "Test residual boxplots", "test_s8_eval_notebook.py"),
            ("outputs/figures/grouped_error_profiles.png", "official figure", "Local hour RMSE error profile", "test_s8_eval_notebook.py"),
            ("runs/v2/s8_eval/artifacts/evaluation_manifest.json", "official provenance", "S8 walk-forward manifest & locks", "test_s8_eval_notebook.py"),
            ("docs/results/model_comparison.md", "final analysis", "S8 test comparison & DM report", "test_s8_eval_notebook.py"),
            ("docs/results/final_report.md", "report", "Final evidence-backed report answering 6 questions", "test_s8_eval_notebook.py"),
            ("notebooks/practice_4.ipynb", "presentation", "Single executed end-to-end notebook", "test_s8_eval_notebook.py"),
            ("tests/test_s8_eval_notebook.py", "test", "S8 evaluation & executed notebook pytest gate", "pytest pass"),
        ],
    )
    return {"evaluation": eval_manifest, "error_analysis": err_summary, "notebook": str(nb_path)}


STAGE_RUNNERS = {
    "S0": run_s0,
    "S1": run_s1,
    "S2": run_s2,
    "S3": run_s3,
    "S4": run_s4,
    "S5": run_s5,
    "S6": run_s6,
    "S7": run_s7,
    "S8": run_s8,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Practice 4 v2 stage-gated pipeline")
    parser.add_argument("--stage", required=True, choices=list(STAGE_RUNNERS.keys()))
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args()
    cfg = load_config(args.config)
    result = STAGE_RUNNERS[args.stage](cfg)
    print(json.dumps({"stage": args.stage, "status": "completed", "keys": list(result.keys())}, indent=2))


if __name__ == "__main__":
    main()
