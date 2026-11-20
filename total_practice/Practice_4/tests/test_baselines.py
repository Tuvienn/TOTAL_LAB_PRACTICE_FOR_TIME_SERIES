import hashlib

import numpy as np
import pytest

from practice_4.models.baselines import canonical, forecasts, model_configs, align, ROOT, INPUTS


def test_baseline_endpoints_and_inverse_scale():
    sequence = np.zeros((2, 24, 4))
    sequence[:, 0, 0] = [1, 2]
    sequence[:, -1, 0] = [3, 4]
    flat = sequence.reshape(2, 96).copy()
    result = forecasts(sequence, flat, 100, 10)
    np.testing.assert_array_equal(result["persistence"], [130, 140])
    np.testing.assert_array_equal(result["seasonal24"], [110, 120])
    flat[0, 0] += 1
    with pytest.raises(ValueError):
        forecasts(sequence, flat, 100, 10)


def test_model_identity_deterministic_and_bound():
    configs = model_configs("a" * 64, "b" * 64)
    assert all(config["complexity"] == 0 for config in configs.values())
    digest = lambda value: hashlib.sha256(canonical(value)).hexdigest()
    assert digest(configs["persistence"]) == digest(model_configs("a" * 64, "b" * 64)["persistence"])
    assert digest(configs["persistence"]) != digest(configs["seasonal24"])
    assert digest(configs["persistence"]) != digest(model_configs("c" * 64, "b" * 64)["persistence"])


def test_real_alignment_and_exclusion_counts():
    with np.load(ROOT / INPUTS, allow_pickle=False) as data:
        rows, counts = align(ROOT, data["target_row"], data["y_true_mw"])
    assert counts == {"train": [24519, 32, 52, 24435], "validation": [5259, 2, 0, 5257]}
    assert len(rows) == 29692
    assert len({(row["origin_timestamp_utc"], row["target_timestamp_utc"]) for row in rows}) == len(rows)


def test_target_hour_changes_cannot_change_forecast():
    levels = np.arange(25 * 4, dtype=float).reshape(25, 4)
    history = levels[:24].copy()
    baseline = forecasts(history[None], history.reshape(1, 96), 20, 2)
    levels[24] += 99999
    changed = forecasts(levels[:24][None], levels[:24].reshape(1, 96), 20, 2)
    for name in baseline:
        np.testing.assert_array_equal(baseline[name], changed[name])

def test_replay_rejects_existing_run():
    from practice_4.models.baselines import run
    with pytest.raises(FileExistsError):
        run("20261118_system312_f01_01", replay=True)
