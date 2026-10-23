from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


ONE_STEP_COLUMNS = (
    "timestamp",
    "candidate_id",
    "actual",
    "prediction",
    "error",
    "absolute_error",
    "squared_error",
    "forecast_protocol",
    "feature_configuration",
)

MULTI_STEP_COLUMNS = (
    "forecast_origin",
    "horizon",
    "target_timestamp",
    "candidate_id",
    "actual",
    "prediction",
    "error",
    "absolute_error",
    "squared_error",
    "forecast_protocol",
    "feature_configuration",
)


def calculate_error_columns(
    actual: np.ndarray,
    prediction: np.ndarray,
) -> dict[str, np.ndarray]:
    actual = np.asarray(actual, dtype=np.float64)
    prediction = np.asarray(prediction, dtype=np.float64)
    if actual.ndim != 1 or prediction.ndim != 1:
        raise ValueError("Actual and prediction must be one-dimensional.")
    if len(actual) != len(prediction):
        raise ValueError("Actual and prediction lengths differ.")
    if not np.isfinite(actual).all() or not np.isfinite(prediction).all():
        raise ValueError("Actual or prediction contains non-finite values.")
    error = actual - prediction
    return {
        "error": error,
        "absolute_error": np.abs(error),
        "squared_error": np.square(error),
    }


def build_one_step_prediction_frame(
    timestamps: pd.DatetimeIndex,
    candidate_id: str,
    actual: np.ndarray,
    prediction: np.ndarray,
    feature_configuration: str,
) -> pd.DataFrame:
    errors = calculate_error_columns(actual, prediction)
    if len(timestamps) != len(actual):
        raise ValueError("One-step timestamp and value lengths differ.")
    if not timestamps.is_unique or not timestamps.is_monotonic_increasing:
        raise ValueError("One-step timestamps are invalid.")
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "candidate_id": candidate_id,
            "actual": np.asarray(actual, dtype=np.float64),
            "prediction": np.asarray(prediction, dtype=np.float64),
            **errors,
            "forecast_protocol": "one_step_rolling_observed_history",
            "feature_configuration": feature_configuration,
        }
    )
    return frame.loc[:, ONE_STEP_COLUMNS]


def build_multistep_prediction_frame(
    forecast_origin: pd.Timestamp,
    candidate_id: str,
    actual: pd.Series,
    prediction: pd.Series,
    feature_configuration: str,
) -> pd.DataFrame:
    if not actual.index.equals(prediction.index):
        raise ValueError("Multi-step actual/prediction indices differ.")
    if len(actual) == 0:
        raise ValueError("Multi-step prediction block is empty.")
    expected_index = pd.date_range(
        forecast_origin + pd.Timedelta(hours=1),
        periods=len(actual),
        freq="h",
    )
    if not actual.index.equals(expected_index):
        raise ValueError("Multi-step target timestamps are not contiguous.")
    errors = calculate_error_columns(
        actual.to_numpy(),
        prediction.to_numpy(),
    )
    frame = pd.DataFrame(
        {
            "forecast_origin": forecast_origin,
            "horizon": np.arange(1, len(actual) + 1, dtype=np.int64),
            "target_timestamp": actual.index,
            "candidate_id": candidate_id,
            "actual": actual.to_numpy(dtype=np.float64),
            "prediction": prediction.to_numpy(dtype=np.float64),
            **errors,
            "forecast_protocol": "recursive_24_hour",
            "feature_configuration": feature_configuration,
        }
    )
    return frame.loc[:, MULTI_STEP_COLUMNS]


def validate_error_columns(frame: pd.DataFrame) -> None:
    expected = calculate_error_columns(
        frame["actual"].to_numpy(),
        frame["prediction"].to_numpy(),
    )
    for column, values in expected.items():
        if not np.allclose(frame[column].to_numpy(), values):
            raise ValueError(f"Stored {column} values are inconsistent.")


def validate_shared_one_step_population(
    predictions: pd.DataFrame,
    candidate_order: Sequence[str],
) -> dict:
    if tuple(predictions.columns) != ONE_STEP_COLUMNS:
        raise ValueError("One-step prediction schema is invalid.")
    reference_timestamps = None
    reference_actual = None
    rows_per_candidate = None
    for candidate_id in candidate_order:
        candidate = predictions.loc[
            predictions["candidate_id"] == candidate_id
        ].reset_index(drop=True)
        if candidate.empty:
            raise ValueError(f"Missing one-step candidate: {candidate_id}")
        validate_error_columns(candidate)
        timestamps = pd.DatetimeIndex(candidate["timestamp"])
        actual = candidate["actual"].to_numpy(dtype=np.float64)
        if reference_timestamps is None:
            reference_timestamps = timestamps
            reference_actual = actual
            rows_per_candidate = len(candidate)
        elif not timestamps.equals(reference_timestamps):
            raise ValueError("One-step candidate timestamps differ.")
        elif not np.array_equal(actual, reference_actual):
            raise ValueError("One-step candidate actual values differ.")
    if set(predictions["candidate_id"].unique()) != set(candidate_order):
        raise ValueError("One-step predictions contain an unknown candidate.")
    return {
        "candidate_count": len(candidate_order),
        "rows_per_candidate": rows_per_candidate,
        "shared_timestamps": True,
        "shared_actual": True,
        "status": "PASS",
    }


def calculate_one_step_metrics(
    predictions: pd.DataFrame,
    candidate_order: Sequence[str],
) -> dict:
    population = validate_shared_one_step_population(
        predictions,
        candidate_order,
    )
    metrics = {}
    for candidate_id in candidate_order:
        candidate = predictions.loc[
            predictions["candidate_id"] == candidate_id
        ]
        metrics[candidate_id] = {
            "mae": float(candidate["absolute_error"].mean()),
            "rmse": float(np.sqrt(candidate["squared_error"].mean())),
            "n_observations": len(candidate),
            "evaluation_start": str(candidate["timestamp"].iloc[0]),
            "evaluation_end": str(candidate["timestamp"].iloc[-1]),
            "status": "PASS",
        }
    return {
        "protocol": "one_step_rolling_observed_history",
        "population": population,
        "candidates": metrics,
        "status": "PASS",
    }


def validate_shared_multistep_population(
    predictions: pd.DataFrame,
    candidate_order: Sequence[str],
    horizon: int,
) -> dict:
    if tuple(predictions.columns) != MULTI_STEP_COLUMNS:
        raise ValueError("Multi-step prediction schema is invalid.")
    reference_keys = None
    reference_actual = None
    origin_count = None
    for candidate_id in candidate_order:
        candidate = predictions.loc[
            predictions["candidate_id"] == candidate_id
        ].reset_index(drop=True)
        if candidate.empty:
            raise ValueError(f"Missing multi-step candidate: {candidate_id}")
        validate_error_columns(candidate)
        counts = candidate.groupby("forecast_origin")["horizon"].count()
        if not (counts == horizon).all():
            raise ValueError("A multi-step origin has an incomplete horizon.")
        expected_horizons = set(range(1, horizon + 1))
        if any(
            set(group["horizon"]) != expected_horizons
            for _, group in candidate.groupby("forecast_origin")
        ):
            raise ValueError("Multi-step horizon identities are invalid.")
        keys = candidate.loc[
            :, ["forecast_origin", "horizon", "target_timestamp"]
        ]
        actual = candidate["actual"].to_numpy(dtype=np.float64)
        if reference_keys is None:
            reference_keys = keys
            reference_actual = actual
            origin_count = candidate["forecast_origin"].nunique()
        elif not keys.equals(reference_keys):
            raise ValueError("Multi-step candidate populations differ.")
        elif not np.array_equal(actual, reference_actual):
            raise ValueError("Multi-step candidate actual values differ.")
    if set(predictions["candidate_id"].unique()) != set(candidate_order):
        raise ValueError("Multi-step predictions contain an unknown candidate.")
    return {
        "candidate_count": len(candidate_order),
        "origin_count": origin_count,
        "horizon": horizon,
        "predictions_per_candidate": origin_count * horizon,
        "shared_origins": True,
        "shared_actual": True,
        "status": "PASS",
    }


def calculate_multistep_metrics(
    predictions: pd.DataFrame,
    candidate_order: Sequence[str],
    horizon: int,
) -> dict:
    population = validate_shared_multistep_population(
        predictions,
        candidate_order,
        horizon,
    )
    metrics = {}
    for candidate_id in candidate_order:
        candidate = predictions.loc[
            predictions["candidate_id"] == candidate_id
        ]
        per_horizon = []
        for step in range(1, horizon + 1):
            values = candidate.loc[candidate["horizon"] == step]
            per_horizon.append(
                {
                    "horizon": step,
                    "mae": float(values["absolute_error"].mean()),
                    "rmse": float(np.sqrt(values["squared_error"].mean())),
                    "n_origins": len(values),
                }
            )
        metrics[candidate_id] = {
            "per_horizon": per_horizon,
            "pooled_mae": float(candidate["absolute_error"].mean()),
            "pooled_rmse": float(
                np.sqrt(candidate["squared_error"].mean())
            ),
            "n_predictions": len(candidate),
            "status": "PASS",
        }
    return {
        "protocol": "recursive_24_hour",
        "population": population,
        "candidates": metrics,
        "status": "PASS",
    }
