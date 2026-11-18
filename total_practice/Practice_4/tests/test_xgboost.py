import numpy as np
import xgboost as xgb

from practice_4.analysis.metrics import select_validation
from practice_4.data.features import XGB_FEATURE_NAMES, _causal_context
from practice_4.models.xgboost_model import feature_indices, metadata, prediction


def test_feature_mapping_and_subsets():
    names = list(XGB_FEATURE_NAMES)
    selected = [f"lag{i:02d}_load" for i in range(23, -1, -1)] + names[-3:]
    indices = feature_indices(names, selected)
    assert len(names) == 99 and len(indices) == 27
    assert indices == list(range(0, 96, 4)) + [96, 97, 98]
    assert np.array_equal(np.arange(99)[indices], indices)


def test_causal_context_excludes_target():
    levels = np.arange(120).reshape(30, 4)
    assert np.array_equal(_causal_context(levels, 25), levels[:25])


def test_selection_ties():
    trials = [{"model":"XGB", "trial_id":name, "complexity":trees, "rmse_mw":rmse, "mae_mw":mae} for name, trees, rmse, mae in [("a", 10, 1.0, 2.0), ("b", 5, 1.0000005, 1.0), ("c", 4, 1.000002, 0.1)]]
    assert select_validation(trials)["trial_id"] == "b"


def test_iteration_metadata_and_reload():
    x = np.arange(100, dtype=float).reshape(-1, 1)
    y = np.sin(x[:, 0])
    model = xgb.XGBRegressor(n_estimators=8, early_stopping_rounds=3, n_jobs=1)
    model.fit(x[:70], y[:70], eval_set=[(x[70:], y[70:])], verbose=False)
    best = model.best_iteration
    expected = prediction(model, x[70:], best)
    booster = model.get_booster()[:best + 1]
    loaded = xgb.Booster()
    loaded.load_model(bytearray(booster.save_raw(raw_format="ubj")))
    actual = loaded.predict(xgb.DMatrix(x[70:]), iteration_range=(0, best + 1))
    assert np.max(np.abs(expected.astype(float) - actual.astype(float))) <= 1e-9
    meta = metadata("XGB_full", ["lag00_load"], "scaler", "booster", "config", best, {}, {})
    assert meta["feature_order"] == ["lag00_load"]
    assert meta["scaler_sha256"] == "scaler"
    assert meta["tree_count"] == best + 1
