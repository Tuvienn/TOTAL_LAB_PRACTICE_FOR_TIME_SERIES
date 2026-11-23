from __future__ import annotations

import json

import numpy as np
import pandas as pd

from practice_4.models.var_model import companion_max_modulus, predict_var_one_step
from practice_4.runtime import PRACTICE_ROOT, read_file_map


def test_s5_synthetic_var_diff_invertibility_and_stability():
    rng = np.random.default_rng(123)
    coefs = np.array([[[0.5, 0.0, 0.0, 0.0], [0.0, 0.4, 0.0, 0.0], [0.0, 0.0, 0.3, 0.0], [0.0, 0.0, 0.0, 0.2]]])
    intercept = np.array([0.1, 0.0, 0.0, 0.0])
    assert companion_max_modulus(coefs) < 1.0

    hist = np.array([[10.0, 1.0, 2.0, 3.0], [12.0, 1.5, 2.0, 3.0]])
    pred = predict_var_one_step(hist, coefs, intercept, diff_order=1)
    expected_load = 12.0 + (0.1 + 0.5 * (12.0 - 10.0))
    assert np.isclose(pred[0], expected_load, atol=1e-12)


def test_s5_real_baselines_and_var_outputs():
    base_metrics_path = PRACTICE_ROOT / "runs/v2/s5_var/artifacts/baseline_metrics.json"
    var_metrics_path = PRACTICE_ROOT / "runs/v2/s5_var/artifacts/var_metrics.json"
    var_model_path = PRACTICE_ROOT / "runs/v2/s5_var/artifacts/var_model.npz"
    assert base_metrics_path.exists() and var_metrics_path.exists() and var_model_path.exists()

    bm = json.loads(base_metrics_path.read_text(encoding="utf-8"))
    for name in ("persistence", "seasonal24", "seasonal168"):
        assert name in bm
        assert bm[name]["validation"]["rmse_mw"] > 0

    vm = json.loads(var_metrics_path.read_text(encoding="utf-8"))
    sel = vm["selected_tag"]
    sel_info = vm["variants"][sel]
    assert sel_info["stable"] is True
    assert sel_info["max_eigenvalue_modulus"] < 1.0
    assert sel_info["train_rows_used"] > 18000, "VAR must train on full train split, not 38% subset"
    assert sel_info["metrics"]["rmse_mw"] < bm["persistence"]["validation"]["rmse_mw"]

    with np.load(var_model_path, allow_pickle=False) as saved:
        assert int(saved["p"]) == sel_info["p"]
        assert int(saved["diff_order"]) == sel_info["diff_order"]
        assert companion_max_modulus(saved["coefs"]) < 1.0

    fmap = {r["path"]: r for r in read_file_map()}
    assert fmap["docs/results/var_results.md"]["existence"] == "EXISTING"
    assert fmap["docs/results/baseline_results.md"]["existence"] == "EXISTING"
