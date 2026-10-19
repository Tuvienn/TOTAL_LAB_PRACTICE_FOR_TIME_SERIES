from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# Phase 1 input contract
EXPECTED_ROWS = 121_296
EXPECTED_MISSING_TARGETS = 27

EXPECTED_COLUMNS = [
    "Datetime",
    "AEP_MW",
    "source_count",
    "quality_flag",
]

EXPECTED_SOURCE_COUNT_DISTRIBUTION = {
    0: 27,
    1: 121_265,
    2: 4,
}

EXPECTED_QUALITY_FLAG_DISTRIBUTION = {
    "observed": 121_265,
    "missing_timestamp": 27,
    "duplicate_aggregated": 4,
}

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

APPROVED_FEATURE_CONFIG = {
    "phase": "phase_02_feature_engineering",
    "input": {
        "path": "datasets/processed/aep_hourly_prepared.csv",
        "timestamp_column": "Datetime",
        "target_column": "AEP_MW",
        "metadata_columns": ["source_count", "quality_flag"],
        "frequency": "h",
    },
    "lag_features": {
        "small_p": 24,
        "medium_p": 72,
        "large_p": 168,
        "max_lag": 168,
    },
    "rolling_features": {
        "windows": [24, 168],
        "min_periods": "window",
        "ddof": 0,
        "center": False,
        "shift_before_rolling": 1,
    },
    "policies": {
        "fill_missing_values": False,
        "drop_samples": False,
        "persist_full_feature_table": False,
        "include_metadata_as_model_features": False,
    },
}


def validate_feature_config(config: dict) -> dict:
    """Validate the complete approved Phase 2 configuration contract."""
    if config != APPROVED_FEATURE_CONFIG:
        raise ValueError(
            "Phase 2 configuration does not match the approved contract.\n"
            f"Expected: {APPROVED_FEATURE_CONFIG}\n"
            f"Actual:   {config}"
        )

    return {
        "approved_contract": True,
        "status": "PASS",
    }


def load_feature_config(
    config_path: Path = Path("config/feature_engineering.json"),
) -> dict:
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Phase 2 configuration file not found: {config_path}"
        )

    with config_path.open(
        "r", encoding="utf-8",
    ) as file:
        config = json.load(file)

    validate_feature_config(config)

    return config


def load_prepared_data(
    input_path: Path,
) -> pd.DataFrame:
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Processed data not found: {input_path}"
        )

    df = pd.read_csv(input_path)

    if "Datetime" not in df.columns:
        raise ValueError("Input dataset does not contain the 'Datetime' column.")

    df["Datetime"] = pd.to_datetime(
        df["Datetime"],
        format=DATETIME_FORMAT,
        errors="raise",
    ).astype("datetime64[ns]")

    return df


def validate_input_contract(
    df: pd.DataFrame,
) -> dict:
    actual_columns = list(df.columns)

    if actual_columns != EXPECTED_COLUMNS:
        raise ValueError(
            "input schema does not match the expected schema.\n"
            f"Expected: {EXPECTED_COLUMNS}\n"
            f"Actual: {actual_columns}"
        )

    if len(df) != EXPECTED_ROWS:
        raise ValueError(
            "Unexpected row count: "
            f"expected={EXPECTED_ROWS}, actual={len(df)}"
        )

    if df["Datetime"].dtype != "datetime64[ns]":
        raise TypeError("Datetime must have dtype datetime64[ns].")

    duplicate_count = int(
        df["Datetime"].duplicated().sum()
    )

    if duplicate_count != 0:
        raise ValueError(f"Found {duplicate_count} duplicate timestamps.")

    if not df["Datetime"].is_monotonic_increasing:
        raise ValueError("Datetime values are not sorted chronologically.")

    expected_timeline = pd.date_range(
        start=df["Datetime"].iloc[0],
        end=df["Datetime"].iloc[-1],
        freq="h",
    )

    actual_timeline = pd.DatetimeIndex(
        df["Datetime"]
    )

    if not actual_timeline.equals(expected_timeline):
        raise ValueError(
            "Datetime timeline is not continuous at hourly frequency."
        )

    if not pd.api.types.is_numeric_dtype(
        df["AEP_MW"]
    ):
        raise TypeError(
            "AEP_MW must be numeric."
        )

    missing_target_count = int(
        df["AEP_MW"].isna().sum()
    )

    if missing_target_count != EXPECTED_MISSING_TARGETS:
        raise ValueError(
            "Unexpected missing target count: "
            f"expected={EXPECTED_MISSING_TARGETS}, "
            f"actual={missing_target_count}"
        )

    source_count_counts = (
        df["source_count"]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    if (
        source_count_counts
        != EXPECTED_SOURCE_COUNT_DISTRIBUTION
    ):
        raise ValueError(
            "source_count distribution does not match "
            "the Phase 1 contract.\n"
            f"Expected: {EXPECTED_SOURCE_COUNT_DISTRIBUTION}\n"
            f"Actual:   {source_count_counts}"
        )

    quality_flag_distribution = (
        df["quality_flag"]
        .value_counts()
        .to_dict()
    )

    if (
        quality_flag_distribution
        != EXPECTED_QUALITY_FLAG_DISTRIBUTION
    ):
        raise ValueError(
            "quality_flag distribution does not match "
            "the Phase 1 contract.\n"
            f"Expected: {EXPECTED_QUALITY_FLAG_DISTRIBUTION}\n"
            f"Actual:   {quality_flag_distribution}"
        )

    missing_mask = df["quality_flag"].eq("missing_timestamp")
    duplicate_mask = df["quality_flag"].eq("duplicate_aggregated")
    observed_mask = df["quality_flag"].eq("observed")

    row_contracts = {
        "missing_timestamp": bool(
            df.loc[missing_mask, "AEP_MW"].isna().all()
            and df.loc[missing_mask, "source_count"].eq(0).all()
        ),
        "duplicate_aggregated": bool(
            df.loc[duplicate_mask, "AEP_MW"].notna().all()
            and df.loc[duplicate_mask, "source_count"].eq(2).all()
        ),
        "observed": bool(
            df.loc[observed_mask, "AEP_MW"].notna().all()
            and df.loc[observed_mask, "source_count"].eq(1).all()
        ),
    }

    failed_contracts = [
        name for name, passed in row_contracts.items() if not passed
    ]
    if failed_contracts:
        raise ValueError(
            "Phase 1 row-level metadata contract failed for: "
            f"{failed_contracts}"
        )

    source_count_distribution = {
        str(key): int(value)
        for key, value in source_count_counts.items()
    }

    audit = {
        "rows": len(df),
        "unique_timestamps": int(
            df["Datetime"].nunique()
        ),
        "duplicate_timestamps": duplicate_count,
        "chronologically_sorted": bool(
            df["Datetime"].is_monotonic_increasing
        ),
        "hourly_continuous": True,
        "missing_AEP_MW": missing_target_count,
        "source_count_distribution":
            source_count_distribution,
        "quality_flag_distribution":
            quality_flag_distribution,
        "row_level_metadata_contracts": row_contracts,
        "status": "PASS",
    }

    return audit

def validate_phase_02_entry(
    config_path: Path = Path(
        "config/feature_engineering.json"
    ),
) -> tuple[pd.DataFrame, dict, dict]:

    config = load_feature_config(
        config_path
    )

    input_path = Path(
        config["input"]["path"]
    )

    df = load_prepared_data(
        input_path
    )

    audit = validate_input_contract(
        df
    )

    return df, config, audit

def create_lag_features(
    df: pd.DataFrame,
    max_lag: int,
) -> pd.DataFrame:
    if max_lag < 1:
        raise ValueError(
            "max_lag must be greater than or equal to 1."
        )

    feature_df = df.copy(deep=True)

    lag_features = {
        f"lag_{lag}": df["AEP_MW"].shift(lag)
        for lag in range(1, max_lag + 1)
    }

    lag_df = pd.DataFrame(
        lag_features,
        index=df.index,
    )

    feature_df = pd.concat(
        [feature_df, lag_df],
        axis=1,
    )

    return feature_df

def validate_lag_alignment(
    source_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    required_lags: tuple[int, ...] = (
        1,
        24,
        72,
        168,
    ),
) -> dict:

    alignment_results = {}

    for lag in required_lags:
        column_name = f"lag_{lag}"

        if column_name not in feature_df.columns:
            raise ValueError(
                f"Required lag feature is missing: {column_name}"
            )

        expected = source_df["AEP_MW"].shift(lag)
        actual = feature_df[column_name]

        if not actual.equals(expected):
            raise ValueError(
                f"Lag alignment validation failed for {column_name}."
            )

        alignment_results[column_name] = True

    return alignment_results

def build_lag_audit(
    feature_df: pd.DataFrame,
    max_lag: int,
    alignment_results: dict,
) -> dict:

    lag_columns = [
        f"lag_{lag}"
        for lag in range(1, max_lag + 1)
    ]

    missing_counts = {
        column: int(feature_df[column].isna().sum())
        for column in lag_columns
    }

    return {
        "max_lag": max_lag,
        "lag_feature_count": len(lag_columns),
        "first_lag_feature": lag_columns[0],
        "last_lag_feature": lag_columns[-1],
        "rows_after_lag_generation": len(feature_df),
        "lag_alignment": alignment_results,
        "lag_nan_counts": missing_counts,
        "status": "PASS",
    }

def run_lag_feature_step(
    config_path: Path = Path(
        "config/feature_engineering.json"
    ),
) -> tuple[pd.DataFrame, dict]:


    source_df, config, _ = validate_phase_02_entry(
        config_path
    )

    max_lag = int(
        config["lag_features"]["max_lag"]
    )

    feature_df = create_lag_features(
        source_df,
        max_lag=max_lag,
    )

    alignment_results = validate_lag_alignment(
        source_df,
        feature_df,
    )

    lag_audit = build_lag_audit(
        feature_df,
        max_lag=max_lag,
        alignment_results=alignment_results,
    )

    return feature_df, lag_audit

def create_rolling_features(
    feature_df: pd.DataFrame,
    windows: list[int],
    ddof: int,
) -> pd.DataFrame:

    rolling_df = feature_df.copy(deep=True)

    historical_target = rolling_df["AEP_MW"].shift(1)

    for window in windows:
        if window < 1:
            raise ValueError(
                "Rolling window must be greater than or equal to 1."
            )

        rolling_df[f"rolling_mean_{window}"] = (
            historical_target
            .rolling(
                window=window,
                min_periods=window,
                center=False,
            )
            .mean()
        )

        rolling_df[f"rolling_std_{window}"] = (
            historical_target
            .rolling(
                window=window,
                min_periods=window,
                center=False,
            )
            .std(ddof=ddof)
        )

    return rolling_df

def validate_rolling_features(
    source_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    windows: list[int],
    ddof: int,
) -> dict:

    historical_target = source_df["AEP_MW"].shift(1)

    validation_results = {}

    for window in windows:
        mean_column = f"rolling_mean_{window}"
        std_column = f"rolling_std_{window}"

        if mean_column not in feature_df.columns:
            raise ValueError(
                f"Missing rolling feature: {mean_column}"
            )

        if std_column not in feature_df.columns:
            raise ValueError(
                f"Missing rolling feature: {std_column}"
            )

        expected_mean = (
            historical_target
            .rolling(
                window=window,
                min_periods=window,
                center=False,
            )
            .mean()
        )

        expected_std = (
            historical_target
            .rolling(
                window=window,
                min_periods=window,
                center=False,
            )
            .std(ddof=ddof)
        )

        if not feature_df[mean_column].equals(expected_mean):
            raise ValueError(
                f"Rolling mean validation failed: {mean_column}"
            )

        if not feature_df[std_column].equals(expected_std):
            raise ValueError(
                f"Rolling std validation failed: {std_column}"
            )

        validation_results[mean_column] = True
        validation_results[std_column] = True

    return validation_results

def build_rolling_audit(
    feature_df: pd.DataFrame,
    windows: list[int],
    validation_results: dict,
) -> dict:

    rolling_columns = []

    for window in windows:
        rolling_columns.extend(
            [
                f"rolling_mean_{window}",
                f"rolling_std_{window}",
            ]
        )

    missing_counts = {
        column: int(
            feature_df[column].isna().sum()
        )
        for column in rolling_columns
    }

    return {
        "rolling_windows": windows,
        "rolling_feature_count": len(rolling_columns),
        "rolling_features": rolling_columns,
        "rows_after_rolling_generation": len(feature_df),
        "rolling_validation": validation_results,
        "rolling_nan_counts": missing_counts,
        "past_only": True,
        "current_target_used": False,
        "status": "PASS",
    }

def run_rolling_feature_step(
    config_path: Path = Path(
        "config/feature_engineering.json"
    ),
) -> tuple[pd.DataFrame, dict, dict]:

    source_df, config, _ = validate_phase_02_entry(
        config_path
    )

    max_lag = int(
        config["lag_features"]["max_lag"]
    )

    rolling_windows = [
        int(window)
        for window in config[
            "rolling_features"
        ]["windows"]
    ]

    ddof = int(
        config[
            "rolling_features"
        ]["ddof"]
    )

    feature_df = create_lag_features(
        source_df,
        max_lag=max_lag,
    )

    lag_alignment = validate_lag_alignment(
        source_df,
        feature_df,
    )

    lag_audit = build_lag_audit(
        feature_df,
        max_lag=max_lag,
        alignment_results=lag_alignment,
    )

    feature_df = create_rolling_features(
        feature_df,
        windows=rolling_windows,
        ddof=ddof,
    )

    rolling_validation = validate_rolling_features(
        source_df,
        feature_df,
        windows=rolling_windows,
        ddof=ddof,
    )

    rolling_audit = build_rolling_audit(
        feature_df,
        windows=rolling_windows,
        validation_results=rolling_validation,
    )

    return feature_df, lag_audit, rolling_audit

def generate_feature_table(
    source_df: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    validate_feature_config(config)

    max_lag = int(
        config["lag_features"]["max_lag"]
    )

    rolling_windows = [
        int(window)
        for window in config[
            "rolling_features"
        ]["windows"]
    ]

    ddof = int(
        config[
            "rolling_features"
        ]["ddof"]
    )

    feature_df = create_lag_features(
        source_df,
        max_lag=max_lag,
    )

    feature_df = create_rolling_features(
        feature_df,
        windows=rolling_windows,
        ddof=ddof,
    )

    return feature_df

def validate_feature_integrity(
    source_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    config: dict,
) -> dict:
    validate_feature_config(config)

    if len(feature_df) != len(source_df):
        raise ValueError(
            "Feature generation changed the number of rows."
        )

    if not feature_df["Datetime"].equals(
        source_df["Datetime"]
    ):
        raise ValueError(
            "Datetime values changed during feature generation."
        )

    if not feature_df["AEP_MW"].equals(
        source_df["AEP_MW"]
    ):
        raise ValueError(
            "Target values changed during feature generation."
        )

    if not feature_df["source_count"].equals(
        source_df["source_count"]
    ):
        raise ValueError(
            "source_count changed during feature generation."
        )

    if not feature_df["quality_flag"].equals(
        source_df["quality_flag"]
    ):
        raise ValueError(
            "quality_flag changed during feature generation."
        )

    if "lag_0" in feature_df.columns:
        raise ValueError(
            "Forbidden feature detected: lag_0"
        )

    negative_lag_columns = [
        column
        for column in feature_df.columns
        if column.startswith("lag_-")
    ]

    if negative_lag_columns:
        raise ValueError(
            "Negative lag features detected: "
            f"{negative_lag_columns}"
        )

    max_lag = int(
        config["lag_features"]["max_lag"]
    )

    rolling_windows = [
        int(window)
        for window in config[
            "rolling_features"
        ]["windows"]
    ]

    lag_columns = [
        f"lag_{lag}"
        for lag in range(1, max_lag + 1)
    ]

    rolling_columns = []

    for window in rolling_windows:
        rolling_columns.extend(
            [
                f"rolling_mean_{window}",
                f"rolling_std_{window}",
            ]
        )

    model_feature_columns = (
        lag_columns
        + rolling_columns
    )

    forbidden_model_columns = {
        "Datetime",
        "AEP_MW",
        "source_count",
        "quality_flag",
    }

    invalid_model_columns = (
        forbidden_model_columns
        .intersection(model_feature_columns)
    )

    if invalid_model_columns:
        raise ValueError(
            "Forbidden columns detected in model feature list: "
            f"{sorted(invalid_model_columns)}"
        )

    rolling_config = config["rolling_features"]

    if rolling_config["center"] is not False:
        raise ValueError(
            "Rolling configuration must use center=false."
        )

    if int(
        rolling_config["shift_before_rolling"]
    ) != 1:
        raise ValueError(
            "Rolling features must use shift_before_rolling=1."
        )

    if int(
        rolling_config["ddof"]
    ) != 0:
        raise ValueError(
            "Rolling standard deviation must use ddof=0."
        )

    if (
        rolling_config["min_periods"]
        != "window"
    ):
        raise ValueError(
            "Rolling min_periods must equal the window size."
        )

    return {
        "rows_preserved": True,
        "timestamps_preserved": True,
        "target_preserved": True,
        "metadata_preserved": True,
        "lag_0_present": False,
        "negative_lag_present": False,
        "target_in_model_features": False,
        "metadata_in_model_features": False,
        "rolling_centered": False,
        "rolling_shift_before": 1,
        "rolling_ddof": 0,
        "status": "PASS",
    }

def validate_no_input_mutation(
    source_df: pd.DataFrame,
    config: dict,
) -> dict:

    source_snapshot = source_df.copy(deep=True)

    _ = generate_feature_table(
        source_df,
        config,
    )

    if not source_df.equals(source_snapshot):
        raise ValueError(
            "Input dataframe was mutated during feature generation."
        )

    return {
        "input_mutated": False,
        "status": "PASS",
    }

def validate_deterministic_generation(
    source_df: pd.DataFrame,
    config: dict,
) -> dict:

    first_result = generate_feature_table(
        source_df,
        config,
    )

    second_result = generate_feature_table(
        source_df,
        config,
    )

    if not first_result.equals(second_result):
        raise ValueError(
            "Feature generation is not deterministic."
        )

    return {
        "deterministic_generation": True,
        "status": "PASS",
    }

def run_feature_validation_step(
    config_path: Path = Path(
        "config/feature_engineering.json"
    ),
) -> tuple[pd.DataFrame, dict]:

    source_df, config, input_audit = (
        validate_phase_02_entry(
            config_path
        )
    )

    feature_df = generate_feature_table(
        source_df,
        config,
    )

    integrity_audit = validate_feature_integrity(
        source_df,
        feature_df,
        config,
    )

    mutation_audit = validate_no_input_mutation(
        source_df,
        config,
    )

    deterministic_audit = (
        validate_deterministic_generation(
            source_df,
            config,
        )
    )

    audit = {
        "input_contract": input_audit,
        "feature_integrity": integrity_audit,
        "input_mutation": mutation_audit,
        "determinism": deterministic_audit,
        "status": "PASS",
    }

    return feature_df, audit

def build_phase_02_audit(
    source_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    config: dict,
) -> dict:
    config_audit = validate_feature_config(config)

    input_audit = validate_input_contract(
        source_df
    )

    max_lag = int(
        config["lag_features"]["max_lag"]
    )

    rolling_windows = [
        int(window)
        for window in config[
            "rolling_features"
        ]["windows"]
    ]

    ddof = int(
        config[
            "rolling_features"
        ]["ddof"]
    )

    lag_alignment = validate_lag_alignment(
        source_df,
        feature_df,
    )

    lag_audit = build_lag_audit(
        feature_df,
        max_lag=max_lag,
        alignment_results=lag_alignment,
    )

    rolling_validation = validate_rolling_features(
        source_df,
        feature_df,
        windows=rolling_windows,
        ddof=ddof,
    )

    rolling_audit = build_rolling_audit(
        feature_df,
        windows=rolling_windows,
        validation_results=rolling_validation,
    )

    integrity_audit = validate_feature_integrity(
        source_df,
        feature_df,
        config,
    )

    mutation_audit = validate_no_input_mutation(
        source_df,
        config,
    )

    deterministic_audit = (
        validate_deterministic_generation(
            source_df,
            config,
        )
    )

    lag_experiments = [
        int(config["lag_features"][name])
        for name in ("small_p", "medium_p", "large_p")
    ]

    rolling_feature_count = len(rolling_windows) * 2

    return {
        "phase": "phase_02_feature_engineering",
        "configuration": config_audit,
        "input_contract": input_audit,
        "feature_table": {
            "rows": len(feature_df),
            "columns": len(feature_df.columns),
            "lag_feature_count": max_lag,
            "rolling_feature_count": rolling_feature_count,
        },
        "lag_features": lag_audit,
        "rolling_features": rolling_audit,
        "feature_integrity": integrity_audit,
        "input_mutation": mutation_audit,
        "determinism": deterministic_audit,
        "feature_experiments": {
            "lag_only": lag_experiments,
            "lag_plus_rolling": lag_experiments,
        },
        "full_feature_table_persisted": config["policies"][
            "persist_full_feature_table"
        ],
        "status": "PASS",
    }

def save_phase_02_audit(
    audit: dict,
    output_path: Path = Path(
        "outputs/results/phase_02_feature_quality.json"
    ),
) -> None:

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            audit,
            file,
            indent=2,
            ensure_ascii=False,
        )

def run_phase_02(
    config_path: Path = Path(
        "config/feature_engineering.json"
    ),
    audit_path: Path = Path(
        "outputs/results/phase_02_feature_quality.json"
    ),
) -> dict:

    source_df, config, _ = (
        validate_phase_02_entry(
            config_path
        )
    )

    feature_df = generate_feature_table(
        source_df,
        config,
    )

    audit = build_phase_02_audit(
        source_df,
        feature_df,
        config,
    )

    save_phase_02_audit(
        audit,
        audit_path,
    )

    return audit

if __name__ == "__main__":

    audit = run_phase_02()

    print(
        json.dumps(
            audit,
            indent=2,
            ensure_ascii=False,
        )
    )

    print(
        "\nPhase 2 feature engineering: PASS"
    )
