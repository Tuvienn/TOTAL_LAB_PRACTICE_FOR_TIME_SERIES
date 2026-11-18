import io

import numpy as np
import pytest

from practice_4.models.var_model import predict_levels, validate_stability


def test_fixed_var_forecast_and_future_invariance():
    coefficients = np.array([np.eye(4) * 0.5, np.eye(4) * 0.2])
    intercept = np.arange(4, dtype=float)
    data = np.arange(12, dtype=float).reshape(3, 4)
    expected = intercept + 0.5 * data[1] + 0.2 * data[0]
    np.testing.assert_allclose(predict_levels(data[:2], coefficients, intercept), expected)
    data[2] *= 1000
    np.testing.assert_allclose(predict_levels(data[:2], coefficients, intercept), expected)


def test_context_bound():
    with pytest.raises(ValueError):
        predict_levels(np.zeros((25, 4)), np.zeros((25, 4, 4)), np.zeros(4))


def test_companion_stability():
    assert np.max(np.abs(validate_stability(np.array([np.eye(4) * 0.5])))) < 1
    with pytest.raises(ValueError):
        validate_stability(np.array([np.eye(4) * 1.01]))


def test_model_roundtrip():
    coefficients = np.array([np.eye(4) * 0.5])
    intercept = np.arange(4, dtype=float)
    stream = io.BytesIO()
    np.savez(stream, coefs=coefficients, intercept=intercept)
    stream.seek(0)
    with np.load(stream, allow_pickle=False) as artifact:
        expected = predict_levels(np.ones((1, 4)), coefficients, intercept)
        np.testing.assert_array_equal(predict_levels(np.ones((1, 4)), artifact["coefs"], artifact["intercept"]), expected)
