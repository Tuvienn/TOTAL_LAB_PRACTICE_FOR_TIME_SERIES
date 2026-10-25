import numpy as np
import pytest

from practice_3_v2.analysis.metrics import (
    aggregate_fold_metrics,
    mean_absolute_error,
    regression_metrics,
    root_mean_squared_error,
)


def test_known_regression_metrics() -> None:
    actual = np.array([1.0, 2.0, 3.0])
    predicted = np.array([1.0, 4.0, 2.0])
    assert mean_absolute_error(actual, predicted) == pytest.approx(1.0)
    assert root_mean_squared_error(actual, predicted) == pytest.approx(
        np.sqrt(5.0 / 3.0)
    )
    assert regression_metrics(actual, predicted) == {
        "mae": pytest.approx(1.0),
        "rmse": pytest.approx(np.sqrt(5.0 / 3.0)),
        "samples": 3,
    }


@pytest.mark.parametrize(
    ("actual", "predicted", "message"),
    [
        ([], [], "non-zero"),
        ([1.0], [1.0, 2.0], "same non-zero"),
        ([1.0, np.nan], [1.0, 2.0], "Actual"),
        ([1.0, 2.0], [1.0, np.inf], "Predictions"),
        ([[1.0]], [[1.0]], "one-dimensional"),
    ],
)
def test_invalid_metric_inputs_are_rejected(
    actual: object,
    predicted: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        regression_metrics(actual, predicted)


def test_fold_aggregation_uses_population_standard_deviation() -> None:
    records = [
        {"fold": index, "mae": float(index), "rmse": float(index + 1), "samples": 10}
        for index in range(1, 6)
    ]
    aggregate = aggregate_fold_metrics(records)
    assert aggregate["mean_cv_mae"] == pytest.approx(3.0)
    assert aggregate["mean_cv_rmse"] == pytest.approx(4.0)
    assert aggregate["cv_mae_standard_deviation"] == pytest.approx(
        np.std([1, 2, 3, 4, 5], ddof=0)
    )
    assert aggregate["standard_deviation_ddof"] == 0
    assert aggregate["validation_samples"] == 50


def test_incomplete_or_duplicate_fold_evidence_is_rejected() -> None:
    incomplete = [
        {"fold": index, "mae": 1.0, "rmse": 2.0, "samples": 10}
        for index in range(1, 5)
    ]
    with pytest.raises(ValueError, match="Expected 5"):
        aggregate_fold_metrics(incomplete)
    duplicate = [
        {"fold": index, "mae": 1.0, "rmse": 2.0, "samples": 10}
        for index in [1, 2, 3, 4, 4]
    ]
    with pytest.raises(ValueError, match="each approved fold"):
        aggregate_fold_metrics(duplicate)
