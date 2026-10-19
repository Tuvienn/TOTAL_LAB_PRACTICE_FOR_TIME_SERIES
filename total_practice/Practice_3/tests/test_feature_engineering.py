from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3.analysis.feature_engineering import (
    load_feature_config,
    load_prepared_data,
    validate_feature_config,
    validate_input_contract,
    validate_phase_02_entry,
    create_lag_features,
    validate_lag_alignment,
    create_rolling_features,
    validate_rolling_features,
    generate_feature_table,
    validate_feature_integrity,
    validate_no_input_mutation,
    validate_deterministic_generation,
    run_phase_02,
)


CONFIG_PATH = Path(
    "config/feature_engineering.json"
)


@pytest.fixture(scope="module")
def config():
    return load_feature_config(
        CONFIG_PATH
    )


@pytest.fixture(scope="module")
def source_df(config):
    input_path = Path(
        config["input"]["path"]
    )

    return load_prepared_data(
        input_path
    )


@pytest.fixture(scope="module")
def feature_df(source_df, config):
    return generate_feature_table(
        source_df,
        config,
    )


def test_feature_config_exists():
    assert CONFIG_PATH.exists()


def test_feature_config_matches_approved_contract(config):
    audit = validate_feature_config(config)

    assert audit == {
        "approved_contract": True,
        "status": "PASS",
    }


@pytest.mark.parametrize(
    ("section", "key", "invalid_value"),
    [
        ("lag_features", "small_p", 12),
        ("rolling_features", "center", True),
        ("policies", "fill_missing_values", True),
    ],
)
def test_feature_config_rejects_unapproved_changes(
    config,
    source_df,
    section,
    key,
    invalid_value,
):
    invalid_config = deepcopy(config)
    invalid_config[section][key] = invalid_value

    with pytest.raises(ValueError, match="approved contract"):
        validate_feature_config(invalid_config)

    with pytest.raises(ValueError, match="approved contract"):
        generate_feature_table(source_df, invalid_config)


def test_phase_02_input_contract(source_df):
    audit = validate_input_contract(
        source_df
    )

    assert audit["rows"] == 121_296
    assert audit["unique_timestamps"] == 121_296
    assert audit["duplicate_timestamps"] == 0
    assert audit["chronologically_sorted"] is True
    assert audit["hourly_continuous"] is True
    assert audit["missing_AEP_MW"] == 27
    assert audit["source_count_distribution"] == {
        "0": 27,
        "1": 121_265,
        "2": 4,
    }
    assert all(audit["row_level_metadata_contracts"].values())
    assert audit["status"] == "PASS"


def test_input_contract_rejects_row_level_metadata_mismatch(source_df):
    corrupted = source_df.copy(deep=True)
    missing_index = corrupted.index[
        corrupted["quality_flag"].eq("missing_timestamp")
    ][0]
    observed_index = corrupted.index[
        corrupted["quality_flag"].eq("observed")
    ][0]

    corrupted.loc[missing_index, "quality_flag"] = "observed"
    corrupted.loc[observed_index, "quality_flag"] = "missing_timestamp"

    with pytest.raises(ValueError, match="row-level metadata contract"):
        validate_input_contract(corrupted)


def test_phase_02_entry_gate():
    df, config, audit = (
        validate_phase_02_entry(
            CONFIG_PATH
        )
    )

    assert len(df) == 121_296
    assert config["lag_features"]["max_lag"] == 168
    assert audit["status"] == "PASS"


def test_lag_feature_generation(source_df, config):
    max_lag = int(
        config["lag_features"]["max_lag"]
    )

    lag_df = create_lag_features(
        source_df,
        max_lag=max_lag,
    )

    assert len(lag_df) == len(source_df)

    assert "lag_1" in lag_df.columns
    assert "lag_24" in lag_df.columns
    assert "lag_72" in lag_df.columns
    assert "lag_168" in lag_df.columns

    assert "lag_0" not in lag_df.columns

    lag_columns = [
        column
        for column in lag_df.columns
        if column.startswith("lag_")
    ]

    assert len(lag_columns) == 168


def test_lag_alignment(source_df, config):
    max_lag = int(
        config["lag_features"]["max_lag"]
    )

    lag_df = create_lag_features(
        source_df,
        max_lag=max_lag,
    )

    alignment = validate_lag_alignment(
        source_df,
        lag_df,
    )

    assert alignment == {
        "lag_1": True,
        "lag_24": True,
        "lag_72": True,
        "lag_168": True,
    }


def test_lag_alignment_at_independent_samples(source_df, feature_df):
    required_lags = (1, 24, 72, 168)
    valid_mask = feature_df[
        [f"lag_{lag}" for lag in required_lags]
    ].notna().all(axis=1)
    normal_position = int(np.flatnonzero(valid_mask.to_numpy())[0])

    for lag in required_lags:
        assert feature_df.iloc[normal_position][f"lag_{lag}"] == (
            source_df.iloc[normal_position - lag]["AEP_MW"]
        )

    missing_position = int(
        np.flatnonzero(source_df["AEP_MW"].isna().to_numpy())[0]
    )
    assert pd.isna(feature_df.iloc[missing_position + 1]["lag_1"])


def test_lag_missing_value_propagation(
    source_df,
    config,
):
    max_lag = int(
        config["lag_features"]["max_lag"]
    )

    lag_df = create_lag_features(
        source_df,
        max_lag=max_lag,
    )

    assert int(
        lag_df["lag_1"].isna().sum()
    ) == 28

    assert int(
        lag_df["lag_24"].isna().sum()
    ) == 51

    assert int(
        lag_df["lag_72"].isna().sum()
    ) == 99

    assert int(
        lag_df["lag_168"].isna().sum()
    ) == 195


def test_rolling_feature_generation(
    source_df,
    config,
):
    max_lag = int(
        config["lag_features"]["max_lag"]
    )

    windows = [
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

    lag_df = create_lag_features(
        source_df,
        max_lag=max_lag,
    )

    rolling_df = create_rolling_features(
        lag_df,
        windows=windows,
        ddof=ddof,
    )

    expected_columns = [
        "rolling_mean_24",
        "rolling_std_24",
        "rolling_mean_168",
        "rolling_std_168",
    ]

    for column in expected_columns:
        assert column in rolling_df.columns

    assert len(rolling_df) == len(source_df)


def test_rolling_features_are_past_only(
    source_df,
    feature_df,
    config,
):
    windows = [
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

    results = validate_rolling_features(
        source_df,
        feature_df,
        windows=windows,
        ddof=ddof,
    )

    assert results[
        "rolling_mean_24"
    ] is True

    assert results[
        "rolling_std_24"
    ] is True

    assert results[
        "rolling_mean_168"
    ] is True

    assert results[
        "rolling_std_168"
    ] is True


def test_rolling_features_at_independent_samples(source_df, feature_df):
    valid_mask = feature_df[
        [
            "rolling_mean_24",
            "rolling_std_24",
            "rolling_mean_168",
            "rolling_std_168",
        ]
    ].notna().all(axis=1)
    position = int(np.flatnonzero(valid_mask.to_numpy())[0])

    history_24 = source_df["AEP_MW"].iloc[position - 24:position]
    history_168 = source_df["AEP_MW"].iloc[position - 168:position]

    assert feature_df.iloc[position]["rolling_mean_24"] == pytest.approx(
        float(np.mean(history_24.to_numpy()))
    )
    assert feature_df.iloc[position]["rolling_std_24"] == pytest.approx(
        float(np.std(history_24.to_numpy(), ddof=0))
    )
    assert feature_df.iloc[position]["rolling_mean_168"] == pytest.approx(
        float(np.mean(history_168.to_numpy()))
    )
    assert feature_df.iloc[position]["rolling_std_168"] == pytest.approx(
        float(np.std(history_168.to_numpy(), ddof=0))
    )

    missing_position = int(
        np.flatnonzero(source_df["AEP_MW"].isna().to_numpy())[0]
    )
    row_after_missing = missing_position + 1
    assert pd.isna(
        feature_df.iloc[row_after_missing]["rolling_mean_24"]
    )
    assert pd.isna(
        feature_df.iloc[row_after_missing]["rolling_mean_168"]
    )


def test_final_feature_table_contract(
    source_df,
    feature_df,
    config,
):
    audit = validate_feature_integrity(
        source_df,
        feature_df,
        config,
    )

    assert feature_df.shape == (
        121_296,
        176,
    )

    assert audit[
        "rows_preserved"
    ] is True

    assert audit[
        "timestamps_preserved"
    ] is True

    assert audit[
        "target_preserved"
    ] is True

    assert audit[
        "metadata_preserved"
    ] is True

    assert audit[
        "lag_0_present"
    ] is False

    assert audit[
        "negative_lag_present"
    ] is False

    assert audit[
        "target_in_model_features"
    ] is False

    assert audit[
        "metadata_in_model_features"
    ] is False

    assert audit["status"] == "PASS"


def test_feature_generation_does_not_mutate_input(
    source_df,
    config,
):
    audit = validate_no_input_mutation(
        source_df,
        config,
    )

    assert audit[
        "input_mutated"
    ] is False

    assert audit["status"] == "PASS"


def test_feature_generation_is_deterministic(
    source_df,
    config,
):
    audit = validate_deterministic_generation(
        source_df,
        config,
    )

    assert audit[
        "deterministic_generation"
    ] is True

    assert audit["status"] == "PASS"


def test_phase_02_audit_round_trip(tmp_path):
    output_path = tmp_path / "phase_02_feature_quality.json"

    audit = run_phase_02(
        config_path=CONFIG_PATH,
        audit_path=output_path,
    )

    with output_path.open("r", encoding="utf-8") as file:
        saved_audit = json.load(file)

    assert saved_audit == audit
    assert audit["configuration"]["approved_contract"] is True
    assert audit["feature_table"] == {
        "rows": 121_296,
        "columns": 176,
        "lag_feature_count": 168,
        "rolling_feature_count": 4,
    }
    assert audit["feature_experiments"] == {
        "lag_only": [24, 72, 168],
        "lag_plus_rolling": [24, 72, 168],
    }
    assert audit["full_feature_table_persisted"] is False
    assert audit["status"] == "PASS"
