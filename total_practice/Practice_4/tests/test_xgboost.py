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


def test_train_monitoring_preserves_validation_early_stopping():
    rng = np.random.default_rng(42)
    x = rng.normal(size=(128, 5))
    y = 3 * x[:, 0] + x[:, 1] + rng.normal(size=128)
    train_x, valid_x = x[:96], x[96:]
    train_y, valid_y = y[:96], y[96:]
    params = dict(n_estimators=100, max_depth=3, learning_rate=0.1,
                  early_stopping_rounds=8, random_state=42, n_jobs=1,
                  eval_metric="rmse")
    validation_only = xgb.XGBRegressor(**params)
    both = xgb.XGBRegressor(**params)
    validation_only.fit(train_x, train_y, eval_set=[(valid_x, valid_y)], verbose=False)
    both.fit(train_x, train_y, eval_set=[(train_x, train_y), (valid_x, valid_y)], verbose=False)
    assert validation_only.best_iteration == both.best_iteration
    np.testing.assert_array_equal(validation_only.predict(valid_x), both.predict(valid_x))
    np.testing.assert_array_equal(validation_only.evals_result()["validation_0"]["rmse"],
                                  both.evals_result()["validation_1"]["rmse"])

def test_replay_rejects_collision_before_reading_config():
    import pytest
    from practice_4.models.xgboost_model import run
    with pytest.raises(FileExistsError):
        run("20261118_system312_g01_01", "missing.json", replay=True)


def test_replay_rejects_wrong_locked_config():
    import pytest
    from practice_4.models.xgboost_model import ROOT, run
    with pytest.raises(ValueError, match="config mismatch"):
        run("p85_invalid_config_xgb", ROOT / "runs/20261118_system312_f02_02/config.json", replay=True)
