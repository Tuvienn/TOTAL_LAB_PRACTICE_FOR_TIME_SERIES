import csv
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import numpy as np
import pytest

from practice_4.models import baselines, lstm_model as lstm


@pytest.fixture(scope="module")
def config():
    return json.loads((lstm.ROOT / "runs" / lstm.RUN_ID / "config.json").read_bytes())


@pytest.fixture(scope="module")
def backend(config):
    return lstm.runtime(config)


def test_exact_r07_architecture(backend, config):
    tf, keras = backend
    model = lstm.build_model(keras, config, 0.001)
    actual = [tuple(layer.output.shape) for layer in model.layers]
    assert actual == [(None, 24, 64), (None, 32), (None, 1)]
    assert [type(layer) for layer in model.layers] == [keras.layers.LSTM, keras.layers.LSTM, keras.layers.Dense]
    assert model.count_params() == sum(np.prod(v.shape) for v in model.trainable_weights) == 30113
    assert model(tf.zeros((2, 24, 4))).dtype == tf.float32
    assert model.jit_compile is False


def test_causal_alignment(monkeypatch):
    monkeypatch.setattr(baselines, "EXPECTED", {"train": (2, 0, 0, 2), "validation": (0, 0, 0, 0)})
    directory = lstm.ROOT / "runs" / f"g02_test_{uuid4().hex}"
    path = directory / "origin.csv"
    directory.mkdir()
    monkeypatch.setattr(lstm, "ROOT", directory)
    monkeypatch.setattr(baselines, "ORIGINS", "origin.csv")
    now = datetime(2015, 1, 1, tzinfo=timezone.utc)
    entries = []
    for i in range(2):
        entries.append(dict(
            target_row=25+i, origin_row=24+i, context_start_row=i, split="train",
            origin_timestamp_utc=(now+timedelta(hours=24+i)).isoformat(),
            target_timestamp_utc=(now+timedelta(hours=25+i)).isoformat(),
            eligible=True, sample_index=i, y_true_mw=float(i), exclusion_reason="",
        ))
    try:
        for valid in (True, False):
            if not valid:
                entries[0]["origin_timestamp_utc"] = entries[0]["target_timestamp_utc"]
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, baselines.ORIGIN_COLUMNS)
                writer.writeheader()
                writer.writerows(entries)
            args = (np.zeros((2, 24, 4)), np.array([25, 26]), np.array([0., 1.]))
            if valid:
                assert len(lstm.align_sequences(*args)[0]) == 2
            else:
                with pytest.raises(ValueError, match="Origin alignment"):
                    lstm.align_sequences(*args)
    finally:
        path.unlink()
        directory.rmdir()


def test_boundary_rejected_before_origin_read():
    with pytest.raises(ValueError, match="Forbidden target row"):
        lstm.align_sequences(np.zeros((1, 24, 4)), np.array([29803]), np.array([1.]))


def test_scaling_and_metrics():
    y = np.array([0., 100., 125.])
    scaled = lstm.scale_truth(y, 100., 25.)
    assert scaled.dtype == np.float32
    np.testing.assert_array_equal(scaled, [-4., 0., 1.])
    yhat = lstm.to_mw(np.array([-3.6, -0.4, 0.6]), 100., 25.)
    assert yhat.dtype == np.float64
    score = lstm.scores(y, yhat, missing=2, invalid=1)
    assert (score["n_considered"], score["n_zero_excluded"]) == (6, 1)
    assert score["mae_mw"] == pytest.approx(10)
    assert score["rmse_mw"] == pytest.approx(10)
    assert score["mape_percent"] == pytest.approx(9)


def test_fit_preserves_chronology(config):
    class Recorder:
        def fit(self, x, y, **kwargs):
            assert x is train_x and y is train_y
            assert kwargs["shuffle"] is False
            assert kwargs["batch_size"] == 64
            assert kwargs["epochs"] == 50
            assert kwargs["validation_data"] == (valid_x, valid_y)
            assert kwargs["callbacks"] == [callback]
            return type("History", (), {"history": {"loss": [1.]}})()

    train_x, train_y, valid_x, valid_y, callback = (object() for _ in range(5))
    assert lstm.fit(Recorder(), callback, config, train_x, train_y, valid_x, valid_y) == {"loss": [1.]}


@pytest.mark.parametrize("end_at_cap", [True, False])
def test_early_stopping_restores_earliest_tie(backend, config, end_at_cap):
    _, keras = backend
    model = lstm.build_model(keras, config, 0.001)
    callback = keras.callbacks.EarlyStopping(**config["early_stopping"])
    callback.set_model(model)
    callback.on_train_begin()
    vals = [3., 1., 1.] if end_at_cap else [3., 1.] + [1.] * 8
    for i, value in enumerate(vals):
        model.set_weights([np.full_like(w, i) for w in model.get_weights()])
        callback.on_epoch_end(i, {"val_loss": value, "loss": 0.})
    assert model.stop_training is (not end_at_cap)
    callback.on_train_end()
    assert lstm.restored_epoch(model, callback, {"loss": [0.] * len(vals), "val_loss": vals}) == 2
    for w in model.get_weights():
        np.testing.assert_array_equal(w, np.ones_like(w))


def test_metadata_and_weight_reload(config, backend):
    tf, keras = backend
    keras.utils.set_random_seed(42)
    model = lstm.build_model(keras, config, 0.001)
    model.optimizer.build(model.trainable_variables)
    directory = lstm.ROOT / "runs" / f"g02_test_{uuid4().hex}"
    directory.mkdir()
    try:
        selected = {"best_epoch": 1, "trial_id": "lstm_lr_001"}
        loaded, metadata = lstm.write_checkpoint(keras, model, directory, config, selected)
        actual = json.loads((directory / "lstm_metadata.json").read_bytes())
        assert actual == metadata
        assert actual["feature_order"] == lstm.FEATURE_ORDER
        assert actual["scaler_sha256"] == lstm.sha(lstm.ROOT / lstm.SCALER)
        assert actual["checkpoint_sha256"] == lstm.sha(directory / "lstm.weights.h5")
        assert actual["architecture_sha256"] == lstm.sha(directory / "lstm_architecture.json")
        x = np.random.default_rng(42).normal(size=(65, 24, 4)).astype(np.float32)
        a, b = [lstm.to_mw(lstm.predict(tf, m, x, 64), 28000., 4500.) for m in (model, loaded)]
        np.testing.assert_allclose(a, b, rtol=0, atol=1e-6)
    finally:
        for file in directory.iterdir():
            file.unlink()
        directory.rmdir()

