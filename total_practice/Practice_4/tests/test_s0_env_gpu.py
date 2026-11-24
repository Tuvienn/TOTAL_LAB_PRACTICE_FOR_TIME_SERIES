from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
import shap
import torch
import xgboost as xgb

from practice_4.runtime import (
    FILE_MAP_PATH,
    PRACTICE_ROOT,
    collect_environment,
    load_config,
    read_file_map,
    set_deterministic_seed,
)


def test_s0_config_and_file_map_integrity():
    cfg = load_config()
    assert cfg["schema_version"] == "2"
    assert cfg["device"] == "cuda"
    assert cfg["split"]["train_ratio"] + cfg["split"]["val_ratio"] + cfg["split"]["test_ratio"] == pytest.approx(1.0)
    assert sum(c["weight"] for c in cfg["dataset"]["cities"]) == pytest.approx(1.0)

    rows = read_file_map()
    assert len(rows) > 0
    paths = [r["path"] for r in rows]
    assert len(paths) == len(set(paths)), "file_map.csv contains duplicate paths"
    gitignored_raw = {
        "datasets/raw/electricityloaddiagrams20112014.zip",
        "datasets/raw/LD2011_2014.txt",
    }
    for r in rows:
        if r["entry_kind"] == "FILE" and r["existence"] == "EXISTING":
            if r["path"] in gitignored_raw and not (PRACTICE_ROOT / r["path"]).exists():
                continue
            assert (PRACTICE_ROOT / r["path"]).exists(), f"Missing file registered as EXISTING: {r['path']}"


def test_s0_environment_and_rtx_gpu():
    env = collect_environment(require_cuda=True)
    assert env["gpu"]["torch_cuda_available"] is True
    assert env["gpu"]["device_count"] >= 1
    assert "NVIDIA" in (env["gpu"]["device_name"] or "")
    assert env["gpu"]["xgboost_use_cuda"] is True
    for req in ("torch", "xgboost", "shap", "holidays", "statsmodels", "scikit-learn", "pandas", "numpy"):
        assert env["packages"][req] is not None, f"Missing required package: {req}"


def test_s0_pytorch_cuda_lstm_smoke():
    set_deterministic_seed(42)
    device = torch.device("cuda")
    model = torch.nn.Sequential().to(device)

    class TinyLSTM(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.l1 = torch.nn.LSTM(4, 16, batch_first=True)
            self.l2 = torch.nn.LSTM(16, 8, batch_first=True)
            self.fc = torch.nn.Linear(8, 1)

        def forward(self, x):
            out, _ = self.l1(x)
            out, _ = self.l2(out)
            return self.fc(out[:, -1, :]).squeeze(-1)

    net = TinyLSTM().to(device)
    opt = torch.optim.Adam(net.parameters(), lr=1e-2)
    loss_fn = torch.nn.MSELoss()
    x = torch.randn(64, 24, 4, device=device)
    y = x[:, -1, 0] * 2.0 + 0.5
    losses = []
    for _ in range(15):
        opt.zero_grad()
        pred = net(x)
        loss = loss_fn(pred, y)
        assert torch.isfinite(loss)
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    assert losses[-1] < losses[0]


def test_s0_xgboost_cuda_and_shap_additivity():
    rng = np.random.default_rng(42)
    x = rng.normal(size=(256, 8)).astype(np.float32)
    y = (3.0 * x[:, 0] - 1.5 * x[:, 1] + rng.normal(scale=0.1, size=256)).astype(np.float32)

    model = xgb.XGBRegressor(
        n_estimators=20,
        max_depth=3,
        learning_rate=0.1,
        tree_method="hist",
        device="cuda",
        random_state=42,
    )
    model.fit(x, y)
    preds = model.get_booster().predict(xgb.DMatrix(x[:16]))
    assert np.isfinite(preds).all()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "xgb_smoke.json"
        model.get_booster().save_model(path)
        reloaded = xgb.Booster()
        reloaded.load_model(path)
        preds_reloaded = reloaded.predict(xgb.DMatrix(x[:16]))
        assert np.max(np.abs(preds - preds_reloaded)) < 1e-4

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(x[:16])
    assert shap_values.shape == (16, 8)
    expected = float(np.asarray(explainer.expected_value).reshape(-1)[0])
    reconstructed = expected + shap_values.sum(axis=1)
    assert np.max(np.abs(reconstructed - preds)) < 1e-3
