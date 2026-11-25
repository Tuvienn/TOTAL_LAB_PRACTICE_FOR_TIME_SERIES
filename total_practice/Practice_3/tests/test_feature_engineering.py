from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3.analysis.eda import extract_development_data
from practice_3.analysis.feature_engineering import (
    PROJECT_ROOT,
    build_calendar_features,
    build_feature_row_from_history,
    build_time_safe_features,
    load_phase_04_inputs,
    run_phase_04,
    validate_feature_contract,
    validate_feature_frame,
)
from practice_3.data.temporal_split import validate_prepared_input


(
    DATA_CONTRACT,
    PREPARATION_CONTRACT,
    SPLIT_CONTRACT,
    FEATURE_CONTRACT,
    PHASE_01_AUDIT,
    PHASE_02_AUDIT,
    PHASE_03_AUDIT,
) = load_phase_04_inputs()


def load_prepared_and_development() -> tuple[pd.DataFrame, pd.DataFrame]:
    prepared, _ = validate_prepared_input(
        PROJECT_ROOT / FEATURE_CONTRACT["prepared_input"],
        DATA_CONTRACT,
        PREPARATION_CONTRACT,
        SPLIT_CONTRACT,
        PHASE_01_AUDIT,
    )
    development = extract_development_data(
        prepared,
        DATA_CONTRACT,
        SPLIT_CONTRACT,
    )
    return prepared, development


def synthetic_data(periods: int = 220) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Datetime": pd.date_range("2020-01-01", periods=periods, freq="h"),
            "AEP_MW": np.arange(1, periods + 1, dtype="float64"),
        }
    )


def test_upstream_identities_are_locked() -> None:
    assert PHASE_02_AUDIT["status"] == "PASS"
    assert PHASE_03_AUDIT["status"] == "PASS"
    assert PHASE_03_AUDIT["prepared_sha256"] == FEATURE_CONTRACT[
        "prepared_sha256"
    ]


def test_contract_has_exact_approved_22_feature_order() -> None:
    validate_feature_contract(FEATURE_CONTRACT)
    assert len(FEATURE_CONTRACT["feature_order"]) == 22
    assert FEATURE_CONTRACT["feature_order"][:8] == [
        "lag_1h",
        "lag_2h",
        "lag_3h",
        "lag_23h",
        "lag_24h",
        "lag_25h",
        "lag_48h",
        "lag_168h",
    ]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"lag_hours": [1, 2]}, "lag"),
        ({"rolling.centered": True}, "Rolling"),
        ({"rolling.shift_before_rolling_hours": 0}, "Rolling"),
    ],
)
def test_invalid_scientific_contract_is_rejected(
    mutation: dict[str, object],
    message: str,
) -> None:
    contract = deepcopy(FEATURE_CONTRACT)
    for key, value in mutation.items():
        if "." in key:
            parent, child = key.split(".")
            contract[parent][child] = value
        else:
            contract[key] = value
    with pytest.raises(ValueError, match=message):
        validate_feature_contract(contract)


def test_batch_lag_and_shifted_rolling_formulas() -> None:
    data = synthetic_data()
    features = build_time_safe_features(data, DATA_CONTRACT, FEATURE_CONTRACT)
    row = features.iloc[168]
    assert row["lag_1h"] == 168.0
    assert row["lag_24h"] == 145.0
    assert row["lag_168h"] == 1.0
    expected_24 = pd.Series(np.arange(145, 169, dtype="float64"))
    expected_168 = pd.Series(np.arange(1, 169, dtype="float64"))
    assert np.isclose(row["rolling_mean_24h"], expected_24.mean())
    assert np.isclose(row["rolling_std_24h"], expected_24.std(ddof=1))
    assert np.isclose(row["rolling_mean_168h"], expected_168.mean())
    assert np.isclose(row["rolling_std_168h"], expected_168.std(ddof=1))


def test_current_and_future_target_mutation_cannot_change_feature_row() -> None:
    data = synthetic_data()
    target_row = 190
    expected = build_time_safe_features(
        data,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
    ).iloc[target_row]
    mutated = data.copy(deep=True)
    mutated.loc[target_row:, "AEP_MW"] = 9_999_999.0
    actual = build_time_safe_features(
        mutated,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
    ).iloc[target_row]
    pd.testing.assert_series_equal(actual, expected)


def test_calendar_features_use_target_timestamp() -> None:
    timestamp = pd.DatetimeIndex(["2024-06-01 06:00:00"])
    calendar = build_calendar_features(timestamp).iloc[0]
    assert calendar["hour"] == 6
    assert calendar["day_of_week"] == 5
    assert calendar["month"] == 6
    assert calendar["is_weekend"] == 1
    assert np.isclose(calendar["hour_sin"], 1.0)
    assert np.isclose(calendar["hour_cos"], 0.0, atol=1e-12)


def test_cyclical_features_remain_in_unit_interval() -> None:
    data = synthetic_data(periods=24 * 370)
    features = build_time_safe_features(data, DATA_CONTRACT, FEATURE_CONTRACT)
    cyclical = FEATURE_CONTRACT["calendar"]["cyclical_features"]
    assert features[cyclical].ge(-1.0 - 1e-12).all().all()
    assert features[cyclical].le(1.0 + 1e-12).all().all()


def test_missing_history_is_not_imputed() -> None:
    data = synthetic_data()
    data.loc[167, "AEP_MW"] = np.nan
    features = build_time_safe_features(data, DATA_CONTRACT, FEATURE_CONTRACT)
    assert np.isnan(features.loc[168, "lag_1h"])
    assert np.isnan(features.loc[168, "rolling_mean_24h"])
    assert np.isnan(features.loc[168, "rolling_std_168h"])


def test_holdout_mutation_cannot_change_development_features() -> None:
    prepared, expected_development = load_prepared_and_development()
    expected = build_time_safe_features(
        expected_development,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
    )
    mutated = prepared.copy(deep=True)
    holdout = mutated["Datetime"].ge(SPLIT_CONTRACT["holdout"]["start_inclusive"])
    mutated.loc[holdout, "AEP_MW"] = 9_999_999.0
    actual_development = extract_development_data(
        mutated,
        DATA_CONTRACT,
        SPLIT_CONTRACT,
    )
    actual = build_time_safe_features(
        actual_development,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
    )
    pd.testing.assert_frame_equal(actual, expected)


def test_recursive_row_matches_batch_row() -> None:
    data = synthetic_data()
    features = build_time_safe_features(data, DATA_CONTRACT, FEATURE_CONTRACT)
    row_index = 200
    history = data.iloc[:row_index].set_index("Datetime")["AEP_MW"]
    recursive = build_feature_row_from_history(
        history,
        data.loc[row_index, "Datetime"],
        FEATURE_CONTRACT,
    )
    pd.testing.assert_series_equal(
        recursive.astype("float64"),
        features.loc[row_index].astype("float64"),
        check_names=False,
    )


def test_recursive_next_step_uses_appended_prediction() -> None:
    data = synthetic_data(periods=200)
    history = data.set_index("Datetime")["AEP_MW"]
    first_target = history.index.max() + pd.Timedelta(hours=1)
    predicted_value = 12_345.0
    extended = pd.concat(
        [history, pd.Series([predicted_value], index=[first_target])]
    )
    next_row = build_feature_row_from_history(
        extended,
        first_target + pd.Timedelta(hours=1),
        FEATURE_CONTRACT,
    )
    assert next_row["lag_1h"] == predicted_value


def test_recursive_builder_rejects_target_or_future_history() -> None:
    data = synthetic_data(periods=200)
    history = data.set_index("Datetime")["AEP_MW"]
    target = history.index.max()
    with pytest.raises(ValueError, match="forecast origin"):
        build_feature_row_from_history(history, target, FEATURE_CONTRACT)


def test_builders_do_not_modify_inputs() -> None:
    data = synthetic_data()
    before = data.copy(deep=True)
    features = build_time_safe_features(data, DATA_CONTRACT, FEATURE_CONTRACT)
    validate_feature_frame(
        features,
        data,
        DATA_CONTRACT,
        FEATURE_CONTRACT,
    )
    pd.testing.assert_frame_equal(data, before)


def test_phase_04_audit_is_deterministic_and_contains_no_holdout_statistics(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first = run_phase_04(PROJECT_ROOT, first_path)
    second = run_phase_04(PROJECT_ROOT, second_path)
    assert first == second
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["feature_count"] == 22
    assert first["development"][
        "holdout_rows_used_for_feature_calculation"
    ] == 0
    assert first["checks"][
        "holdout_target_values_used_for_feature_calculation"
    ] is False
    assert first["checks"]["holdout_derived_feature_statistics"] is False
    assert first["checks"]["feature_imputation_applied"] is False
    assert first["status"] == "PASS"
    with first_path.open(encoding="utf-8") as file:
        assert json.load(file) == first


def test_pipeline_source_does_not_import_legacy_package() -> None:
    source = (
        PROJECT_ROOT / "src/practice_3/analysis/feature_engineering.py"
    ).read_text(encoding="utf-8")
    assert "from practice_3 " not in source
    assert "import practice_3" not in source
