from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from practice_3.analysis.feature_engineering import (
    generate_feature_table,
    validate_feature_config,
    validate_feature_integrity,
    validate_phase_02_entry,
)


EXPECTED_INITIAL_ROWS = 121_296
EXPECTED_USABLE_ROWS = 116_675
EXPECTED_REMOVED_ROWS = 4_621
EXPECTED_FIRST_TIMESTAMP = pd.Timestamp("2004-10-08 01:00:00")
EXPECTED_LAST_TIMESTAMP = pd.Timestamp("2018-08-03 00:00:00")
EXPECTED_LAG_ONLY_COUNTS = {
    "p24": 120_597,
    "p72": 119_267,
    "p168": 116_675,
}
FORBIDDEN_FEATURES = {
    "Datetime",
    "AEP_MW",
    "source_count",
    "quality_flag",
}


@dataclass(frozen=True)
class SupervisedDataset:
    X: pd.DataFrame
    y: pd.Series
    timestamp_index: pd.DatetimeIndex
    feature_names: tuple[str, ...]
    aligned_metadata: pd.DataFrame


def load_pass_audit(path: Path, expected_phase: str) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required phase audit not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        audit = json.load(file)

    if audit.get("phase") != expected_phase:
        raise ValueError(
            f"Unexpected phase audit at {path}: {audit.get('phase')}"
        )
    if audit.get("status") != "PASS":
        raise ValueError(f"Required phase has not passed: {expected_phase}")

    return audit


def validate_phase_03_entry(
    config_path: Path = Path("config/feature_engineering.json"),
    phase_01_audit_path: Path = Path(
        "outputs/results/phase_01_data_quality.json"
    ),
    phase_02_audit_path: Path = Path(
        "outputs/results/phase_02_feature_quality.json"
    ),
) -> tuple[pd.DataFrame, dict, pd.DataFrame, dict]:
    phase_01_audit = load_pass_audit(
        phase_01_audit_path,
        "phase_01_data_preparation",
    )
    phase_02_audit = load_pass_audit(
        phase_02_audit_path,
        "phase_02_feature_engineering",
    )

    source_df, config, input_audit = validate_phase_02_entry(config_path)
    validate_feature_config(config)
    feature_df = generate_feature_table(source_df, config)
    feature_audit = validate_feature_integrity(source_df, feature_df, config)

    return source_df, config, feature_df, {
        "phase_01": phase_01_audit["status"],
        "phase_02": phase_02_audit["status"],
        "input_contract": input_audit["status"],
        "feature_integrity": feature_audit["status"],
        "status": "PASS",
    }


def build_feature_definitions(config: dict) -> dict[str, tuple[str, ...]]:
    validate_feature_config(config)

    p_values = {
        "p24": int(config["lag_features"]["small_p"]),
        "p72": int(config["lag_features"]["medium_p"]),
        "p168": int(config["lag_features"]["large_p"]),
    }
    rolling_features = tuple(
        feature_name
        for window in config["rolling_features"]["windows"]
        for feature_name in (
            f"rolling_mean_{int(window)}",
            f"rolling_std_{int(window)}",
        )
    )

    definitions: dict[str, tuple[str, ...]] = {}
    for label, p_value in p_values.items():
        lag_features = tuple(
            f"lag_{lag}" for lag in range(1, p_value + 1)
        )
        definitions[f"lag_only_{label}"] = lag_features

    for label, p_value in p_values.items():
        lag_features = tuple(
            f"lag_{lag}" for lag in range(1, p_value + 1)
        )
        definitions[f"lag_rolling_{label}"] = (
            lag_features + rolling_features
        )

    return definitions


def validate_feature_table(feature_df: pd.DataFrame, config: dict) -> dict:
    max_lag = int(config["lag_features"]["max_lag"])
    lag_features = [f"lag_{lag}" for lag in range(1, max_lag + 1)]
    rolling_features = [
        feature_name
        for window in config["rolling_features"]["windows"]
        for feature_name in (
            f"rolling_mean_{int(window)}",
            f"rolling_std_{int(window)}",
        )
    ]
    expected_columns = [
        "Datetime",
        "AEP_MW",
        "source_count",
        "quality_flag",
        *lag_features,
        *rolling_features,
    ]

    if list(feature_df.columns) != expected_columns:
        raise ValueError("Phase 3 feature schema or order is invalid.")
    if len(feature_df) != EXPECTED_INITIAL_ROWS:
        raise ValueError(
            "Unexpected Phase 3 input row count: "
            f"expected={EXPECTED_INITIAL_ROWS}, actual={len(feature_df)}"
        )
    if feature_df["Datetime"].duplicated().any():
        raise ValueError("Phase 3 input contains duplicate timestamps.")
    if not feature_df["Datetime"].is_monotonic_increasing:
        raise ValueError("Phase 3 input is not chronologically ordered.")

    return {
        "rows": len(feature_df),
        "columns": len(feature_df.columns),
        "schema_and_order_valid": True,
        "timestamps_unique": True,
        "chronologically_sorted": True,
        "status": "PASS",
    }


def build_common_validity_mask(
    feature_df: pd.DataFrame,
    config: dict,
) -> tuple[pd.Series, dict]:
    max_lag = int(config["lag_features"]["max_lag"])
    lag_features = [f"lag_{lag}" for lag in range(1, max_lag + 1)]
    rolling_features = [
        feature_name
        for window in config["rolling_features"]["windows"]
        for feature_name in (
            f"rolling_mean_{int(window)}",
            f"rolling_std_{int(window)}",
        )
    ]

    invalid_target = ~np.isfinite(feature_df["AEP_MW"].to_numpy())
    invalid_lag_history = ~np.isfinite(
        feature_df[lag_features].to_numpy()
    ).all(axis=1)
    invalid_rolling_history = ~np.isfinite(
        feature_df[rolling_features].to_numpy()
    ).all(axis=1)
    non_finite_feature = invalid_lag_history | invalid_rolling_history
    invalid_union = invalid_target | non_finite_feature
    common_valid = pd.Series(
        ~invalid_union,
        index=feature_df.index,
        name="common_valid",
    )

    lag_only_counts = {}
    for p_value in (24, 72, 168):
        columns = [f"lag_{lag}" for lag in range(1, p_value + 1)]
        valid = np.isfinite(feature_df["AEP_MW"].to_numpy()) & np.isfinite(
            feature_df[columns].to_numpy()
        ).all(axis=1)
        lag_only_counts[f"p{p_value}"] = int(valid.sum())

    usable_rows = int(common_valid.sum())
    removed_rows = int(invalid_union.sum())
    valid_timestamps = feature_df.loc[common_valid, "Datetime"]

    audit = {
        "initial_rows": len(feature_df),
        "reason_counts": {
            "invalid_target": int(invalid_target.sum()),
            "invalid_lag_history": int(invalid_lag_history.sum()),
            "invalid_rolling_history": int(invalid_rolling_history.sum()),
            "non_finite_feature": int(non_finite_feature.sum()),
        },
        "reason_intersections": {
            "target_and_lag": int(
                (invalid_target & invalid_lag_history).sum()
            ),
            "target_and_rolling": int(
                (invalid_target & invalid_rolling_history).sum()
            ),
            "lag_and_rolling": int(
                (invalid_lag_history & invalid_rolling_history).sum()
            ),
            "target_lag_and_rolling": int(
                (
                    invalid_target
                    & invalid_lag_history
                    & invalid_rolling_history
                ).sum()
            ),
        },
        "lag_only_usable_rows": lag_only_counts,
        "removed_unique_rows": removed_rows,
        "usable_rows": usable_rows,
        "first_usable_timestamp": str(valid_timestamps.iloc[0]),
        "last_usable_timestamp": str(valid_timestamps.iloc[-1]),
        "status": "PASS",
    }

    expected = {
        "initial_rows": EXPECTED_INITIAL_ROWS,
        "usable_rows": EXPECTED_USABLE_ROWS,
        "removed_unique_rows": EXPECTED_REMOVED_ROWS,
        "first_usable_timestamp": str(EXPECTED_FIRST_TIMESTAMP),
        "last_usable_timestamp": str(EXPECTED_LAST_TIMESTAMP),
        "lag_only_usable_rows": EXPECTED_LAG_ONLY_COUNTS,
    }
    actual = {key: audit[key] for key in expected}
    if actual != expected:
        raise ValueError(
            "Phase 3 validity-mask acceptance values changed.\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )

    return common_valid, audit


def build_single_supervised_dataset(
    valid_rows: pd.DataFrame,
    feature_names: tuple[str, ...],
) -> SupervisedDataset:
    timestamp_index = pd.DatetimeIndex(
        valid_rows["Datetime"].to_numpy(copy=True),
        name="Datetime",
    )
    X = valid_rows.loc[:, list(feature_names)].copy()
    y = valid_rows["AEP_MW"].copy()
    metadata = valid_rows[["source_count", "quality_flag"]].copy()

    X.index = timestamp_index
    y.index = timestamp_index
    metadata.index = timestamp_index

    return SupervisedDataset(
        X=X,
        y=y,
        timestamp_index=timestamp_index,
        feature_names=feature_names,
        aligned_metadata=metadata,
    )


def build_supervised_datasets(
    feature_df: pd.DataFrame,
    config: dict,
) -> tuple[dict[str, SupervisedDataset], dict]:
    validate_feature_table(feature_df, config)
    common_valid, row_loss_audit = build_common_validity_mask(
        feature_df,
        config,
    )
    valid_rows = feature_df.loc[common_valid]
    definitions = build_feature_definitions(config)
    datasets = {
        name: build_single_supervised_dataset(valid_rows, feature_names)
        for name, feature_names in definitions.items()
    }

    return datasets, row_loss_audit


def validate_supervised_datasets(
    datasets: dict[str, SupervisedDataset],
    config: dict,
) -> dict:
    definitions = build_feature_definitions(config)
    if list(datasets) != list(definitions):
        raise ValueError("Supervised dataset names or order are invalid.")

    reference_index: pd.DatetimeIndex | None = None
    dataset_audit = {}

    for name, expected_features in definitions.items():
        dataset = datasets[name]
        if tuple(dataset.X.columns) != expected_features:
            raise ValueError(f"Feature order is invalid for {name}.")
        if dataset.feature_names != expected_features:
            raise ValueError(f"feature_names is invalid for {name}.")
        if len(dataset.X) != EXPECTED_USABLE_ROWS:
            raise ValueError(f"Unexpected sample count for {name}.")
        if not dataset.X.index.equals(dataset.y.index):
            raise ValueError(f"X/y index mismatch for {name}.")
        if not dataset.X.index.equals(dataset.aligned_metadata.index):
            raise ValueError(f"X/metadata index mismatch for {name}.")
        if not dataset.X.index.equals(dataset.timestamp_index):
            raise ValueError(f"Timestamp index mismatch for {name}.")
        if FORBIDDEN_FEATURES.intersection(dataset.X.columns):
            raise ValueError(f"Forbidden model feature detected for {name}.")
        if not np.isfinite(dataset.X.to_numpy()).all():
            raise ValueError(f"Invalid numeric feature detected for {name}.")
        if not np.isfinite(dataset.y.to_numpy()).all():
            raise ValueError(f"Invalid target detected for {name}.")
        if not dataset.timestamp_index.is_monotonic_increasing:
            raise ValueError(f"Chronology is invalid for {name}.")

        if reference_index is None:
            reference_index = dataset.timestamp_index
        elif not dataset.timestamp_index.equals(reference_index):
            raise ValueError("Supervised datasets do not share one index.")

        dataset_audit[name] = {
            "samples": len(dataset.X),
            "features": len(dataset.X.columns),
            "first_timestamp": str(dataset.timestamp_index[0]),
            "last_timestamp": str(dataset.timestamp_index[-1]),
            "alignment": "PASS",
            "finite_X_y": True,
            "forbidden_features_present": False,
        }

    return {
        "configuration_count": len(datasets),
        "shared_timestamp_index": True,
        "datasets": dataset_audit,
        "status": "PASS",
    }


def validate_deterministic_construction(
    feature_df: pd.DataFrame,
    config: dict,
    reference_datasets: dict[str, SupervisedDataset],
) -> dict:
    common_valid, _ = build_common_validity_mask(feature_df, config)
    valid_rows = feature_df.loc[common_valid]
    definitions = build_feature_definitions(config)

    for name, feature_names in definitions.items():
        reference = reference_datasets[name]
        repeated = build_single_supervised_dataset(valid_rows, feature_names)
        if not repeated.X.equals(reference.X):
            raise ValueError(f"Non-deterministic X detected for {name}.")
        if not repeated.y.equals(reference.y):
            raise ValueError(f"Non-deterministic y detected for {name}.")
        if not repeated.aligned_metadata.equals(reference.aligned_metadata):
            raise ValueError(f"Non-deterministic metadata detected for {name}.")

    return {
        "deterministic_construction": True,
        "status": "PASS",
    }


def dataframe_fingerprint(df: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    row_hashes = pd.util.hash_pandas_object(df, index=True)
    digest.update(row_hashes.to_numpy().tobytes())
    digest.update(json.dumps(list(df.columns)).encode("utf-8"))
    dtype_names = [str(dtype) for dtype in df.dtypes]
    digest.update(json.dumps(dtype_names).encode("utf-8"))
    return digest.hexdigest()


def save_phase_03_audit(
    audit: dict,
    output_path: Path = Path(
        "outputs/results/phase_03_supervised_quality.json"
    ),
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(audit, file, indent=2, ensure_ascii=False)


def run_phase_03(
    config_path: Path = Path("config/feature_engineering.json"),
    audit_path: Path = Path(
        "outputs/results/phase_03_supervised_quality.json"
    ),
) -> tuple[dict[str, SupervisedDataset], dict]:
    _, config, feature_df, entry_audit = validate_phase_03_entry(
        config_path=config_path
    )
    feature_table_audit = validate_feature_table(feature_df, config)
    input_fingerprint = dataframe_fingerprint(feature_df)
    datasets, row_loss_audit = build_supervised_datasets(feature_df, config)
    supervised_audit = validate_supervised_datasets(datasets, config)
    deterministic_audit = validate_deterministic_construction(
        feature_df,
        config,
        datasets,
    )
    output_fingerprint = dataframe_fingerprint(feature_df)
    if input_fingerprint != output_fingerprint:
        raise ValueError("Phase 3 mutated the input feature table.")

    audit = {
        "phase": "phase_03_x_y_preparation",
        "entry_gate": entry_audit,
        "feature_table": feature_table_audit,
        "row_loss": row_loss_audit,
        "supervised_datasets": supervised_audit,
        "input_mutation": {
            "feature_table_mutated": False,
            "status": "PASS",
        },
        "determinism": deterministic_audit,
        "full_supervised_datasets_persisted": False,
        "status": "PASS",
    }
    save_phase_03_audit(audit, audit_path)

    return datasets, audit


if __name__ == "__main__":
    _, phase_audit = run_phase_03()
    print(json.dumps(phase_audit, indent=2, ensure_ascii=False))
    print("\nPhase 3 X/y preparation: PASS")
