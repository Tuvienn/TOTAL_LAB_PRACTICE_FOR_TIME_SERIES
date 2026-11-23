from __future__ import annotations

import json

import numpy as np
import pandas as pd
import xgboost as xgb

from practice_4.data.features import XGB_FULL_FEATURES
from practice_4.runtime import PRACTICE_ROOT, read_file_map


def test_s6_xgboost_gpu_artifacts_ablation_and_shap():
    metrics_path = PRACTICE_ROOT / "runs/v2/s6_xgb/artifacts/xgb_metrics.json"
    ablation_path = PRACTICE_ROOT / "runs/v2/s6_xgb/artifacts/ablation_summary.csv"
    shap_csv = PRACTICE_ROOT / "runs/v2/s6_xgb/artifacts/shap_importance.csv"
    assert metrics_path.exists() and ablation_path.exists() and shap_csv.exists()

    res = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert res["device"] == "cuda"
    assert res["shap_additivity_max_err"] < 5.0

    ab = pd.read_csv(ablation_path)
    assert set(ab["subset"]) == {"XGB_load_only", "XGB_load_weather", "XGB_load_calendar", "XGB_full"}
    assert (ab["reload_max_diff"] < 1e-2).all()

    base = json.loads((PRACTICE_ROOT / "runs/v2/s5_var/artifacts/baseline_metrics.json").read_text(encoding="utf-8"))
    best_rmse = float(ab["rmse_mw"].min())
    assert best_rmse < base["persistence"]["validation"]["rmse_mw"]
    assert best_rmse < base["seasonal168"]["validation"]["rmse_mw"]

    best_subset = res["best_subset"]
    booster_path = PRACTICE_ROOT / "runs/v2/s6_xgb/artifacts" / f"{best_subset}.json"
    assert booster_path.exists()
    booster = xgb.Booster()
    booster.load_model(booster_path)
    assert len(booster.feature_names) > 0

    for fig in ("xgb_shap_summary.png", "xgb_shap_dependence_temp.png"):
        p = PRACTICE_ROOT / "outputs/figures" / fig
        assert p.exists() and p.stat().st_size > 5000

    fmap = {r["path"]: r for r in read_file_map()}
    assert fmap["docs/results/xgboost_findings.md"]["existence"] == "EXISTING"
