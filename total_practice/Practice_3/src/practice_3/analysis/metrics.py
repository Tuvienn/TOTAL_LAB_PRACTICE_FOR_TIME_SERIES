"""Validated regression metrics shared by Practice 3 evaluation phases."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np


def _validated_pair(
    actual: Sequence[float] | np.ndarray,
    predicted: Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return finite, one-dimensional arrays with identical non-zero length."""

    actual_array = np.asarray(actual, dtype="float64")
    predicted_array = np.asarray(predicted, dtype="float64")
    if actual_array.ndim != 1 or predicted_array.ndim != 1:
        raise ValueError("Metric inputs must be one-dimensional.")
    if actual_array.size == 0 or actual_array.size != predicted_array.size:
        raise ValueError("Metric inputs must have the same non-zero length.")
    if not np.isfinite(actual_array).all():
        raise ValueError("Actual values must be finite.")
    if not np.isfinite(predicted_array).all():
        raise ValueError("Predictions must be finite.")
    return actual_array, predicted_array


def mean_absolute_error(
    actual: Sequence[float] | np.ndarray,
    predicted: Sequence[float] | np.ndarray,
) -> float:
    """Compute MAE after strict input validation."""

    actual_array, predicted_array = _validated_pair(actual, predicted)
    return float(np.mean(np.abs(actual_array - predicted_array)))


def root_mean_squared_error(
    actual: Sequence[float] | np.ndarray,
    predicted: Sequence[float] | np.ndarray,
) -> float:
    """Compute RMSE after strict input validation."""

    actual_array, predicted_array = _validated_pair(actual, predicted)
    return float(np.sqrt(np.mean(np.square(actual_array - predicted_array))))


def regression_metrics(
    actual: Sequence[float] | np.ndarray,
    predicted: Sequence[float] | np.ndarray,
) -> dict[str, float | int]:
    """Return the approved fold-level metric record."""

    actual_array, predicted_array = _validated_pair(actual, predicted)
    return {
        "mae": mean_absolute_error(actual_array, predicted_array),
        "rmse": root_mean_squared_error(actual_array, predicted_array),
        "samples": int(actual_array.size),
    }


def aggregate_fold_metrics(
    fold_metrics: Sequence[dict[str, Any]],
    *,
    expected_folds: int = 5,
) -> dict[str, float | int]:
    """Aggregate complete fold evidence with population standard deviation."""

    if len(fold_metrics) != expected_folds:
        raise ValueError(f"Expected {expected_folds} complete fold records.")
    fold_ids = [int(record["fold"]) for record in fold_metrics]
    if sorted(fold_ids) != list(range(1, expected_folds + 1)):
        raise ValueError("Fold records must contain each approved fold once.")
    maes = np.asarray([record["mae"] for record in fold_metrics], dtype="float64")
    rmses = np.asarray([record["rmse"] for record in fold_metrics], dtype="float64")
    if not np.isfinite(maes).all() or not np.isfinite(rmses).all():
        raise ValueError("Fold metrics must be finite.")
    return {
        "folds": expected_folds,
        "validation_samples": int(sum(int(record["samples"]) for record in fold_metrics)),
        "mean_cv_mae": float(np.mean(maes)),
        "mean_cv_rmse": float(np.mean(rmses)),
        "cv_mae_standard_deviation": float(np.std(maes, ddof=0)),
        "cv_rmse_standard_deviation": float(np.std(rmses, ddof=0)),
        "standard_deviation_ddof": 0,
    }
