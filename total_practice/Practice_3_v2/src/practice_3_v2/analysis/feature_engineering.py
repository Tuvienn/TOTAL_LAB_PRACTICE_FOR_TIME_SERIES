"""Leakage-safe feature engineering for Practice 3 v2."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import os
import tempfile
from typing import Any

import numpy as np
import pandas as pd

from practice_3_v2.analysis.eda import (
    extract_development_data,
    load_phase_03_inputs,
    validate_development_data,
)
from practice_3_v2.data.data_preparation import (
    calculate_sha256,
    load_json_contract,
)
from practice_3_v2.data.temporal_split import validate_prepared_input


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _expected_feature_order(contract: dict[str, Any]) -> list[str]:
    """Derive the exact feature order from the feature policies."""

    lag_features = [f"lag_{lag}h" for lag in contract["lag_hours"]]
    rolling_features = [
        f"rolling_{statistic}_{window}h"
        for window in contract["rolling"]["windows_hours"]
        for statistic in contract["rolling"]["statistics"]
    ]
    calendar = contract["calendar"]
    return (
        lag_features
        + rolling_features
        + calendar["integer_features"]
        + calendar["cyclical_features"]
    )


def validate_feature_contract(contract: dict[str, Any]) -> None:
    """Reject any contract that weakens the approved leakage controls."""

    expected_lags = [1, 2, 3, 23, 24, 25, 48, 168]
    expected_windows = [24, 168]
    expected_statistics = ["mean", "std"]
    semantics = contract["time_semantics"]
    rolling = contract["rolling"]
    missing = contract["missing_policy"]
    if contract["lag_hours"] != expected_lags:
        raise ValueError("Feature lag contract does not match the approved design.")
    if rolling["windows_hours"] != expected_windows:
        raise ValueError("Rolling windows do not match the approved design.")
    if rolling["statistics"] != expected_statistics:
        raise ValueError("Rolling statistics do not match the approved design.")
    if (
        rolling["shift_before_rolling_hours"] != 1
        or rolling["min_periods_equals_window"] is not True
        or rolling["std_ddof"] != 1
        or rolling["centered"] is not False
    ):
        raise ValueError("Rolling features must use shifted trailing windows.")
    if semantics != {
        "feature_timestamp": "target_timestamp",
        "forecast_origin_offset_hours": 1,
        "available_target_history": "through_target_minus_1_hour",
    }:
        raise ValueError("Feature time semantics do not match the approved design.")
    if missing != {
        "imputation": "none",
        "drop_rows": False,
        "eligibility_owner": "phase_05",
    }:
        raise ValueError("Missing-feature ownership must remain with Phase 5.")
    if contract["feature_order"] != _expected_feature_order(contract):
        raise ValueError("Feature order does not match the configured policies.")
    if len(contract["feature_order"]) != 22:
        raise ValueError("The approved core schema must contain 22 features.")
    if len(set(contract["feature_order"])) != 22:
        raise ValueError("Feature names must be unique.")


def load_phase_04_inputs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    """Load approved contracts and verify all upstream identities."""

    project_root = Path(project_root).resolve()
    (
        data_contract,
        preparation_contract,
        split_contract,
        eda_contract,
        phase_01_audit,
        phase_02_audit,
    ) = load_phase_03_inputs(project_root)
    feature_contract = load_json_contract(project_root / "config/features.json")
    validate_feature_contract(feature_contract)

    if feature_contract["prepared_sha256"] != eda_contract["prepared_sha256"]:
        raise ValueError("Prepared identity conflicts with the EDA contract.")
    if feature_contract["split_audit"] != eda_contract["split_audit"]:
        raise ValueError("Split audit identity conflicts with the EDA contract.")

    eda_audit_path = project_root / feature_contract["eda_audit"]
    if not eda_audit_path.is_file():
        raise FileNotFoundError(f"Phase 3 audit not found: {eda_audit_path}")
    actual_eda_sha256 = calculate_sha256(eda_audit_path)
    if actual_eda_sha256 != feature_contract["eda_audit_sha256"]:
        raise ValueError("Phase 3 audit SHA-256 does not match feature contract.")
    with eda_audit_path.open(encoding="utf-8") as file:
        phase_03_audit = json.load(file)
    if phase_03_audit.get("status") != "PASS":
        raise ValueError("Phase 3 audit status must be PASS.")
    if phase_03_audit.get("prepared_sha256") != feature_contract[
        "prepared_sha256"
    ]:
        raise ValueError("Phase 3 prepared identity conflicts with Phase 4.")
    return (
        data_contract,
        preparation_contract,
        split_contract,
        feature_contract,
        phase_01_audit,
        phase_02_audit,
        phase_03_audit,
    )


def build_calendar_features(
    timestamps: pd.Series | pd.DatetimeIndex,
) -> pd.DataFrame:
    """Build deterministic calendar features for target timestamps."""

    index = timestamps.index if isinstance(timestamps, pd.Series) else None
    values = pd.DatetimeIndex(timestamps)
    hour = values.hour
    day_of_week = values.day_of_week
    month = values.month
    result = pd.DataFrame(
        {
            "hour": hour,
            "day_of_week": day_of_week,
            "month": month,
            "is_weekend": (day_of_week >= 5).astype("int64"),
            "hour_sin": np.sin(2 * np.pi * hour / 24),
            "hour_cos": np.cos(2 * np.pi * hour / 24),
            "day_of_week_sin": np.sin(2 * np.pi * day_of_week / 7),
            "day_of_week_cos": np.cos(2 * np.pi * day_of_week / 7),
            "month_sin": np.sin(2 * np.pi * (month - 1) / 12),
            "month_cos": np.cos(2 * np.pi * (month - 1) / 12),
        },
        index=index,
    )
    return result


def build_time_safe_features(
    data: pd.DataFrame,
    data_contract: dict[str, Any],
    feature_contract: dict[str, Any],
) -> pd.DataFrame:
    """Build batch features using only target history available at the origin."""

    validate_feature_contract(feature_contract)
    timestamp_column = data_contract["timestamp_column"]
    target_column = data_contract["target_column"]
    required = [timestamp_column, target_column]
    if any(column not in data.columns for column in required):
        raise ValueError("Feature input is missing a required column.")
    timestamps = data[timestamp_column]
    if not pd.api.types.is_datetime64_any_dtype(timestamps):
        raise ValueError("Feature timestamps must use a datetime dtype.")
    if not timestamps.is_unique or not timestamps.is_monotonic_increasing:
        raise ValueError("Feature timestamps must be unique and increasing.")
    if not timestamps.diff().dropna().eq(pd.Timedelta(hours=1)).all():
        raise ValueError("Feature input must use a complete hourly timeline.")

    target = data[target_column].astype("float64")
    features = pd.DataFrame(index=data.index)
    for lag in feature_contract["lag_hours"]:
        features[f"lag_{lag}h"] = target.shift(lag)
    shifted = target.shift(feature_contract["rolling"]["shift_before_rolling_hours"])
    for window in feature_contract["rolling"]["windows_hours"]:
        rolling = shifted.rolling(window=window, min_periods=window, center=False)
        features[f"rolling_mean_{window}h"] = rolling.mean()
        features[f"rolling_std_{window}h"] = rolling.std(
            ddof=feature_contract["rolling"]["std_ddof"]
        )
    calendar = build_calendar_features(timestamps)
    for column in calendar.columns:
        features[column] = calendar[column]
    return features.loc[:, feature_contract["feature_order"]]


def _history_value(history: pd.Series, timestamp: pd.Timestamp) -> float:
    """Return one exact hourly history value or NaN if it is missing."""

    if timestamp not in history.index:
        return float("nan")
    value = history.loc[timestamp]
    if isinstance(value, pd.Series):
        raise ValueError("Recursive history timestamps must be unique.")
    return float(value)


def build_feature_row_from_history(
    history: pd.Series,
    target_timestamp: pd.Timestamp | str,
    feature_contract: dict[str, Any],
) -> pd.Series:
    """Build one recursive-safe feature row from history ending at the origin."""

    validate_feature_contract(feature_contract)
    target_timestamp = pd.Timestamp(target_timestamp)
    if not isinstance(history.index, pd.DatetimeIndex):
        raise ValueError("Recursive history must use a DatetimeIndex.")
    if not history.index.is_unique or not history.index.is_monotonic_increasing:
        raise ValueError("Recursive history timestamps must be unique and increasing.")
    if history.empty:
        raise ValueError("Recursive history cannot be empty.")
    expected_origin = target_timestamp - pd.Timedelta(hours=1)
    if history.index.max() != expected_origin:
        raise ValueError("Recursive history must end exactly at the forecast origin.")
    if (history.index >= target_timestamp).any():
        raise ValueError("Recursive history cannot contain target or future values.")

    values: dict[str, float | int] = {}
    for lag in feature_contract["lag_hours"]:
        values[f"lag_{lag}h"] = _history_value(
            history,
            target_timestamp - pd.Timedelta(hours=lag),
        )
    for window in feature_contract["rolling"]["windows_hours"]:
        window_index = pd.date_range(
            end=expected_origin,
            periods=window,
            freq="h",
        )
        window_values = history.reindex(window_index).astype("float64")
        if window_values.notna().sum() != window:
            values[f"rolling_mean_{window}h"] = float("nan")
            values[f"rolling_std_{window}h"] = float("nan")
        else:
            values[f"rolling_mean_{window}h"] = float(window_values.mean())
            values[f"rolling_std_{window}h"] = float(
                window_values.std(ddof=feature_contract["rolling"]["std_ddof"])
            )
    calendar = build_calendar_features(pd.DatetimeIndex([target_timestamp])).iloc[0]
    values.update(calendar.to_dict())
    return pd.Series(values).loc[feature_contract["feature_order"]]


def validate_feature_frame(
    features: pd.DataFrame,
    source: pd.DataFrame,
    data_contract: dict[str, Any],
    feature_contract: dict[str, Any],
) -> None:
    """Validate exact schema, alignment, ranges, and finite observed values."""

    if features.columns.tolist() != feature_contract["feature_order"]:
        raise ValueError("Feature frame does not use the approved exact order.")
    if len(features) != len(source) or not features.index.equals(source.index):
        raise ValueError("Feature frame is not row-aligned with its source.")
    if np.isinf(features.select_dtypes(include=[np.number]).to_numpy()).any():
        raise ValueError("Feature frame contains infinite values.")
    for column, minimum, maximum in (
        ("hour", 0, 23),
        ("day_of_week", 0, 6),
        ("month", 1, 12),
        ("is_weekend", 0, 1),
    ):
        if not features[column].between(minimum, maximum).all():
            raise ValueError(f"Calendar feature is out of range: {column}")
    cyclical = feature_contract["calendar"]["cyclical_features"]
    if not features[cyclical].ge(-1.0 - 1e-12).all().all():
        raise ValueError("A cyclical feature is below -1.")
    if not features[cyclical].le(1.0 + 1e-12).all().all():
        raise ValueError("A cyclical feature is above 1.")

    target = source[data_contract["target_column"]].astype("float64")
    for lag in feature_contract["lag_hours"]:
        pd.testing.assert_series_equal(
            features[f"lag_{lag}h"],
            target.shift(lag),
            check_names=False,
        )


def build_phase_04_audit(
    development_data: pd.DataFrame,
    features: pd.DataFrame,
    prepared_sha256: str,
    phase_02_audit_sha256: str,
    phase_03_audit_sha256: str,
    data_contract: dict[str, Any],
    feature_contract: dict[str, Any],
) -> dict[str, Any]:
    """Build the deterministic development-only feature validation audit."""

    timestamp_column = data_contract["timestamp_column"]
    complete = features.notna().all(axis=1)
    first_complete_index = complete[complete].index.min()
    first_complete = development_data.loc[first_complete_index, timestamp_column]
    return {
        "phase": feature_contract["phase"],
        "contract_version": feature_contract["contract_version"],
        "prepared_input": feature_contract["prepared_input"],
        "prepared_sha256": prepared_sha256,
        "split_audit": feature_contract["split_audit"],
        "split_audit_sha256": phase_02_audit_sha256,
        "eda_audit": feature_contract["eda_audit"],
        "eda_audit_sha256": phase_03_audit_sha256,
        "development": {
            "start_inclusive": development_data[timestamp_column].min().strftime(
                DATETIME_FORMAT
            ),
            "end_inclusive": development_data[timestamp_column].max().strftime(
                DATETIME_FORMAT
            ),
            "rows": int(len(development_data)),
            "holdout_rows_used_for_feature_calculation": 0,
        },
        "time_semantics": deepcopy(feature_contract["time_semantics"]),
        "feature_count": len(feature_contract["feature_order"]),
        "feature_order": deepcopy(feature_contract["feature_order"]),
        "feature_groups": {
            "lags": [f"lag_{lag}h" for lag in feature_contract["lag_hours"]],
            "rolling": [
                name
                for name in feature_contract["feature_order"]
                if name.startswith("rolling_")
            ],
            "calendar": (
                feature_contract["calendar"]["integer_features"]
                + feature_contract["calendar"]["cyclical_features"]
            ),
        },
        "formulas": {
            "lag": "lag_kh(T) = y(T-k)",
            "rolling": "target.shift(1).rolling(window, min_periods=window)",
            "rolling_std_ddof": feature_contract["rolling"]["std_ddof"],
            "calendar_timestamp": "target_timestamp",
        },
        "null_counts": {
            column: int(features[column].isna().sum())
            for column in feature_contract["feature_order"]
        },
        "non_null_counts": {
            column: int(features[column].notna().sum())
            for column in feature_contract["feature_order"]
        },
        "rows_with_all_features": int(complete.sum()),
        "first_fully_available_timestamp": first_complete.strftime(
            DATETIME_FORMAT
        ),
        "missing_policy": deepcopy(feature_contract["missing_policy"]),
        "checks": {
            "development_only": True,
            "holdout_target_values_used_for_feature_calculation": False,
            "holdout_derived_feature_statistics": False,
            "exact_ordered_schema": True,
            "current_target_excluded": True,
            "future_target_excluded": True,
            "rolling_shifted_by_one_hour": True,
            "centered_rolling_used": False,
            "feature_imputation_applied": False,
            "rows_dropped": False,
            "target_time_metadata_used": False,
            "anomaly_flag_used": False,
            "recursive_row_builder_available": True,
            "calendar_ranges_valid": True,
            "infinite_values_present": False,
        },
        "status": "PASS",
    }


def save_phase_04_artifact(audit: dict[str, Any], output_path: Path) -> None:
    """Validate a staged JSON file before atomically promoting it."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            dir=output_path.parent,
            delete=False,
        ) as temporary:
            json.dump(audit, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        with temporary_path.open(encoding="utf-8") as file:
            reloaded = json.load(file)
        if reloaded != audit or reloaded.get("status") != "PASS":
            raise ValueError("Serialized Phase 4 audit validation failed.")
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def run_phase_04(
    project_root: Path = PROJECT_ROOT,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Run official development-only feature validation."""

    project_root = Path(project_root).resolve()
    (
        data_contract,
        preparation_contract,
        split_contract,
        feature_contract,
        phase_01_audit,
        _phase_02_audit,
        _phase_03_audit,
    ) = load_phase_04_inputs(project_root)
    prepared, prepared_sha256 = validate_prepared_input(
        project_root / feature_contract["prepared_input"],
        data_contract,
        preparation_contract,
        split_contract,
        phase_01_audit,
    )
    development = extract_development_data(prepared, data_contract, split_contract)
    validate_development_data(development, data_contract, {
        "development": split_contract["development"]
    })
    source_before = development.copy(deep=True)
    features = build_time_safe_features(
        development,
        data_contract,
        feature_contract,
    )
    validate_feature_frame(
        features,
        development,
        data_contract,
        feature_contract,
    )
    pd.testing.assert_frame_equal(development, source_before)
    phase_02_path = project_root / feature_contract["split_audit"]
    phase_03_path = project_root / feature_contract["eda_audit"]
    audit = build_phase_04_audit(
        development,
        features,
        prepared_sha256,
        calculate_sha256(phase_02_path),
        calculate_sha256(phase_03_path),
        data_contract,
        feature_contract,
    )
    destination = output_path or (
        project_root / feature_contract["outputs"]["audit"]
    )
    save_phase_04_artifact(audit, destination)
    return audit


def main() -> int:
    """Run Phase 4 from the command line."""

    audit = run_phase_04()
    print(json.dumps({
        "phase": audit["phase"],
        "features": audit["feature_count"],
        "rows_with_all_features": audit["rows_with_all_features"],
        "first_fully_available_timestamp": audit[
            "first_fully_available_timestamp"
        ],
        "status": audit["status"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
