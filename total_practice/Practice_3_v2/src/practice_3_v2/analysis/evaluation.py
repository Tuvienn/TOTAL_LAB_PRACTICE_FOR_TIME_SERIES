"""Prediction validation and evaluation artifacts for Practice 3 v2."""

from __future__ import annotations

from pathlib import Path
import os
import tempfile
from typing import Any

import numpy as np
import pandas as pd

from practice_3_v2.analysis.metrics import regression_metrics
ONE_STEP_COLUMNS = [
    "timestamp",
    "candidate",
    "actual",
    "prediction",
    "error",
    "absolute_error",
    "squared_error",
    "forecast_protocol",
]
RECURSIVE_COLUMNS = [
    "forecast_origin",
    "horizon",
    "target_timestamp",
    "candidate",
    "actual",
    "prediction",
    "error",
    "absolute_error",
    "squared_error",
    "forecast_protocol",
]


def attach_error_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach signed, absolute, and squared error columns."""

    result = frame.copy(deep=True)
    actual = result["actual"].to_numpy(dtype="float64")
    prediction = result["prediction"].to_numpy(dtype="float64")
    if not np.isfinite(actual).all() or not np.isfinite(prediction).all():
        raise ValueError("Actual and prediction values must be finite.")
    error = prediction - actual
    result["error"] = error
    result["absolute_error"] = np.abs(error)
    result["squared_error"] = np.square(error)
    return result


def validate_one_step_predictions(
    frame: pd.DataFrame,
    candidate_registry: list[str],
    expected_timestamps: pd.DatetimeIndex,
) -> None:
    """Validate common one-step timestamps and exact prediction schema."""

    if frame.columns.tolist() != ONE_STEP_COLUMNS:
        raise ValueError("One-step prediction schema is invalid.")
    if set(frame["candidate"].unique()) != set(candidate_registry):
        raise ValueError("One-step candidate registry is incomplete.")
    if not frame["timestamp"].map(lambda value: isinstance(value, pd.Timestamp)).all():
        raise ValueError("One-step timestamps must be pandas timestamps.")
    expected = pd.DatetimeIndex(expected_timestamps)
    for candidate in candidate_registry:
        candidate_frame = frame.loc[frame["candidate"].eq(candidate)]
        timestamps = pd.DatetimeIndex(candidate_frame["timestamp"])
        if not timestamps.equals(expected):
            raise ValueError("One-step candidates must use identical timestamps.")
        if candidate_frame["forecast_protocol"].nunique() != 1 or candidate_frame[
            "forecast_protocol"
        ].iloc[0] != "one_step_rolling_observed_history":
            raise ValueError("One-step forecast protocol is invalid.")
    numeric = frame[
        ["actual", "prediction", "error", "absolute_error", "squared_error"]
    ].to_numpy(dtype="float64")
    if not np.isfinite(numeric).all():
        raise ValueError("One-step predictions contain non-finite values.")


def validate_recursive_predictions(
    frame: pd.DataFrame,
    candidate_registry: list[str],
    expected_origins: pd.DatetimeIndex,
    horizon: int = 24,
) -> None:
    """Validate shared origins, complete horizons, and recursive schema."""

    if frame.columns.tolist() != RECURSIVE_COLUMNS:
        raise ValueError("Recursive prediction schema is invalid.")
    if set(frame["candidate"].unique()) != set(candidate_registry):
        raise ValueError("Recursive candidate registry is incomplete.")
    expected_origins = pd.DatetimeIndex(expected_origins)
    expected_horizons = list(range(1, horizon + 1))
    for candidate in candidate_registry:
        candidate_frame = frame.loc[frame["candidate"].eq(candidate)]
        origins = pd.DatetimeIndex(candidate_frame["forecast_origin"].unique())
        if not origins.equals(expected_origins):
            raise ValueError("Recursive candidates must use identical origins.")
        for origin, block in candidate_frame.groupby("forecast_origin", sort=True):
            if block["horizon"].tolist() != expected_horizons:
                raise ValueError("Every recursive origin must contain horizons 1..24.")
            expected_targets = pd.date_range(
                start=pd.Timestamp(origin) + pd.Timedelta(hours=1),
                periods=horizon,
                freq="h",
            )
            if not pd.DatetimeIndex(block["target_timestamp"]).equals(expected_targets):
                raise ValueError("Recursive target timestamps are misaligned.")
        if candidate_frame["forecast_protocol"].nunique() != 1 or candidate_frame[
            "forecast_protocol"
        ].iloc[0] != "recursive_24_hour":
            raise ValueError("Recursive forecast protocol is invalid.")
    numeric = frame[
        ["actual", "prediction", "error", "absolute_error", "squared_error"]
    ].to_numpy(dtype="float64")
    if not np.isfinite(numeric).all():
        raise ValueError("Recursive predictions contain non-finite values.")


def build_one_step_metrics(
    frame: pd.DataFrame,
    candidate_registry: list[str],
) -> dict[str, Any]:
    """Build one-step MAE/RMSE records from validated predictions."""

    records: list[dict[str, Any]] = []
    for candidate in candidate_registry:
        candidate_frame = frame.loc[frame["candidate"].eq(candidate)]
        metrics = regression_metrics(
            candidate_frame["actual"].to_numpy(),
            candidate_frame["prediction"].to_numpy(),
        )
        records.append(
            {
                "candidate": candidate,
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "n_observations": metrics["samples"],
                "evaluation_start": candidate_frame["timestamp"].min().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "evaluation_end": candidate_frame["timestamp"].max().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
    return {
        "protocol": "one_step_rolling_observed_history",
        "candidate_metrics": records,
        "status": "PASS",
    }


def build_recursive_metrics(
    frame: pd.DataFrame,
    candidate_registry: list[str],
) -> dict[str, Any]:
    """Build per-horizon and directly pooled recursive metrics."""

    candidate_records: list[dict[str, Any]] = []
    for candidate in candidate_registry:
        candidate_frame = frame.loc[frame["candidate"].eq(candidate)]
        per_horizon: list[dict[str, Any]] = []
        for horizon, horizon_frame in candidate_frame.groupby("horizon", sort=True):
            metrics = regression_metrics(
                horizon_frame["actual"].to_numpy(),
                horizon_frame["prediction"].to_numpy(),
            )
            per_horizon.append(
                {
                    "horizon": int(horizon),
                    "mae": metrics["mae"],
                    "rmse": metrics["rmse"],
                    "n_origins": metrics["samples"],
                }
            )
        pooled = regression_metrics(
            candidate_frame["actual"].to_numpy(),
            candidate_frame["prediction"].to_numpy(),
        )
        candidate_records.append(
            {
                "candidate": candidate,
                "origins": int(candidate_frame["forecast_origin"].nunique()),
                "per_horizon": per_horizon,
                "pooled": {
                    "pooled_mae": pooled["mae"],
                    "pooled_rmse": pooled["rmse"],
                    "n_predictions": pooled["samples"],
                    "n_origins": int(candidate_frame["forecast_origin"].nunique()),
                },
            }
        )
    return {
        "protocol": "recursive_24_hour",
        "candidate_metrics": candidate_records,
        "status": "PASS",
    }


def atomic_write_csv(frame: pd.DataFrame, output_path: Path) -> None:
    """Atomically write a CSV and verify exact row/column recovery."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".csv",
            dir=output_path.parent,
            delete=False,
        ) as temporary:
            frame.to_csv(temporary, index=False)
            temporary_path = Path(temporary.name)
        reloaded = pd.read_csv(temporary_path)
        if reloaded.columns.tolist() != frame.columns.tolist() or len(reloaded) != len(frame):
            raise ValueError("Serialized CSV validation failed.")
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
