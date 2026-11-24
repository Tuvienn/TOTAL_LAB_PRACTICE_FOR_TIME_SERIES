from __future__ import annotations

import json

import numpy as np
import pandas as pd
import torch

from practice_4.models.lstm_model import (
    MultivariateLSTM,
    count_trainable_parameters,
    predict_single_window,
)
from practice_4.runtime import PRACTICE_ROOT, read_file_map


def test_s7_core_architecture_parameter_count_and_single_inference():
    model = MultivariateLSTM(input_size=4, hidden1=64, hidden2=32, dropout=0.0, future_cal_dim=0).cuda()
    expected_pytorch_params = 4 * 64 * (4 + 64 + 2) + 4 * 32 * (64 + 32 + 2) + 32 + 1
    assert count_trainable_parameters(model) == expected_pytorch_params == 30497
    w = np.zeros((24, 4), dtype=np.float32)
    val = predict_single_window(model, w, torch.device("cuda"))
    assert np.isfinite(val)

    cal_model = MultivariateLSTM(input_size=13, hidden1=64, hidden2=32, dropout=0.1, future_cal_dim=9).cuda()
    expected_cal_params = 4 * 64 * (13 + 64 + 2) + 4 * 32 * (64 + 32 + 2) + (32 + 9) + 1
    assert count_trainable_parameters(cal_model) == expected_cal_params == 32810
    w_cal = np.zeros((24, 13), dtype=np.float32)
    f_cal = np.zeros((9,), dtype=np.float32)
    val_cal = predict_single_window(cal_model, w_cal, torch.device("cuda"), future_cal=f_cal)
    assert np.isfinite(val_cal)


def test_s7_real_lstm_gpu_artifacts_and_reload_parity():
    metrics_path = PRACTICE_ROOT / "runs/v2/s7_lstm/artifacts/lstm_metrics.json"
    trials_path = PRACTICE_ROOT / "runs/v2/s7_lstm/artifacts/trials.csv"
    ckpt_best = PRACTICE_ROOT / "runs/v2/s7_lstm/artifacts/lstm_best.pt"
    ckpt_core = PRACTICE_ROOT / "runs/v2/s7_lstm/artifacts/lstm_core.pt"
    assert metrics_path.exists() and trials_path.exists() and ckpt_best.exists() and ckpt_core.exists()

    trials_df = pd.read_csv(trials_path)
    counts = trials_df.groupby("variant").size().to_dict()
    assert counts == {
        "LSTM_24h_load_only": 4,
        "LSTM_24h_core": 4,
        "LSTM_24h_cal": 4,
        "LSTM_168h_diag": 4,
    }, f"Unbalanced LSTM tuning budget across variants: {counts}"

    res = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "cuda" in res["device"].lower()
    assert len(res["variants_summary"]) == 4
    assert len(res["seed_stability"]) == 3

    for key in ("lstm_best", "lstm_core"):
        assert res["checkpoints"][key]["reload_batch_max_diff"] < 1e-2
        assert res["checkpoints"][key]["reload_single_diff"] < 1e-2

    base = json.loads((PRACTICE_ROOT / "runs/v2/s5_var/artifacts/baseline_metrics.json").read_text(encoding="utf-8"))
    best_rmse = min(r["rmse_kw"] for r in res["variants_summary"])
    assert best_rmse < base["persistence"]["validation"]["rmse_kw"]

    fig = PRACTICE_ROOT / "outputs/figures/lstm_learning_curves.png"
    assert fig.exists() and fig.stat().st_size > 5000

    fmap = {r["path"]: r for r in read_file_map()}
    assert fmap["docs/results/lstm_findings.md"]["existence"] == "EXISTING"
