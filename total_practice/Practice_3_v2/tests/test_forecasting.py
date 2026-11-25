from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3_v2.analysis.forecasting import (
    EXPECTED_CANDIDATES,
    PROJECT_ROOT,
    build_recursive_predictions,
    eligible_recursive_origins,
    initialize_run,
    load_phase_07_preflight_inputs,
    run_preflight,
    scheduled_recursive_origins,
    seasonal_naive_24_values,
    validate_final_evaluation_contract,
    validate_resume_identity,
)
from practice_3_v2.data.data_preparation import load_json_contract


FINAL_CONTRACT = load_json_contract(PROJECT_ROOT / "config/final_evaluation.json")
FEATURE_CONTRACT = load_json_contract(PROJECT_ROOT / "config/features.json")


class DeterministicEstimator:
    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return frame["lag_1h"].to_numpy(dtype="float64") + 1.0


def synthetic_prepared() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-01 00:00:00", periods=400, freq="h")
    return pd.DataFrame(
        {
            "Datetime": timestamps,
            "AEP_MW": np.arange(400, dtype="float64") + 1000.0,
            "source_count": 1,
            "quality_flag": "observed",
        }
    )


def test_contract_matches_approved_phase_07_scope() -> None:
    validate_final_evaluation_contract(FINAL_CONTRACT)
    assert FINAL_CONTRACT["candidate_registry"] == EXPECTED_CANDIDATES
    assert FINAL_CONTRACT["execution"]["executor"] == "human_terminal_only"
    assert FINAL_CONTRACT["execution"]["binary_model_persisted"] is False
    assert FINAL_CONTRACT["scope"]["holdout_is_claimed_unseen"] is False


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("status",), "DRAFT", "approved"),
        (("candidate_registry",), ["xgboost_tuned"], "registry"),
        (("one_step", "expected_common_eligible_rows"), 10, "One-step"),
        (("recursive", "origin_hour"), 0, "Recursive"),
        (("execution", "executor"), "ai", "execution"),
        (("scope", "holdout_is_claimed_unseen"), True, "claim"),
        (("outputs", "evaluation_audit"), "other.json", "output"),
    ],
)
def test_contract_changes_are_rejected(
    path: tuple[str, ...], value: object, message: str
) -> None:
    changed = deepcopy(FINAL_CONTRACT)
    cursor = changed
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises(ValueError, match=message):
        validate_final_evaluation_contract(changed)


def test_preflight_links_model_lock_without_opening_holdout() -> None:
    contract, cv_results, model_lock, evidence = load_phase_07_preflight_inputs()
    assert contract == FINAL_CONTRACT
    assert cv_results["selected_candidate"] == "xgboost_tuned"
    assert model_lock["selected_candidate"] == "xgboost_tuned"
    assert evidence["development_eligible_samples"] == 108_083
    assert evidence["holdout_opened"] is False
    result = run_preflight()
    assert result["status"] == "PASS"
    assert result["holdout_opened"] is False
    assert result["evaluation_started"] is False


def test_fixed_recursive_schedule_is_daily_at_23_and_non_overlapping() -> None:
    split_contract = load_json_contract(PROJECT_ROOT / "config/temporal_split.json")
    origins = scheduled_recursive_origins(split_contract)
    assert len(origins) > 0
    assert (origins.hour == 23).all()
    assert origins.to_series().diff().dropna().eq(pd.Timedelta(hours=24)).all()
    prior_ends = origins[:-1] + pd.Timedelta(hours=24)
    next_starts = origins[1:] + pd.Timedelta(hours=1)
    assert (prior_ends < next_starts).all()


def test_recursive_predictions_do_not_use_actual_future_values() -> None:
    prepared = synthetic_prepared()
    origin = pd.Timestamp("2024-01-10 23:00:00")
    origins = pd.DatetimeIndex([origin])
    data_contract = {"timestamp_column": "Datetime", "target_column": "AEP_MW"}
    target = prepared.set_index("Datetime")["AEP_MW"]
    assert eligible_recursive_origins(
        target, origins, FEATURE_CONTRACT
    ).equals(origins)
    first = build_recursive_predictions(
        DeterministicEstimator(),
        prepared,
        origins,
        data_contract,
        FEATURE_CONTRACT,
        EXPECTED_CANDIDATES,
    )
    changed = prepared.copy()
    future_mask = changed["Datetime"].gt(origin)
    changed.loc[future_mask, "AEP_MW"] += 100_000.0
    second = build_recursive_predictions(
        DeterministicEstimator(),
        changed,
        origins,
        data_contract,
        FEATURE_CONTRACT,
        EXPECTED_CANDIDATES,
    )
    first_predictions = first[["candidate", "horizon", "prediction"]]
    second_predictions = second[["candidate", "horizon", "prediction"]]
    pd.testing.assert_frame_equal(first_predictions, second_predictions)
    assert not first["actual"].equals(second["actual"])


def test_seasonal_naive_24_is_timestamp_aligned_and_origin_safe() -> None:
    timestamps = pd.date_range("2024-01-01 00:00:00", periods=72, freq="h")
    target = pd.Series(np.arange(len(timestamps), dtype="float64"), index=timestamps)
    forecast_timestamps = pd.DatetimeIndex(
        [pd.Timestamp("2024-01-03 00:00:00"), pd.Timestamp("2024-01-03 01:00:00")]
    )
    values = seasonal_naive_24_values(
        target,
        forecast_timestamps,
        forecast_origin=pd.Timestamp("2024-01-02 23:00:00"),
    )
    expected = pd.Series(
        [
            target.loc[pd.Timestamp("2024-01-02 00:00:00")],
            target.loc[pd.Timestamp("2024-01-02 01:00:00")],
        ],
        index=forecast_timestamps - pd.Timedelta(hours=24),
    )
    pd.testing.assert_series_equal(values, expected)
    with pytest.raises(ValueError, match="after the forecast origin"):
        seasonal_naive_24_values(
            target,
            pd.DatetimeIndex([pd.Timestamp("2024-01-03 23:00:00")]),
            forecast_origin=pd.Timestamp("2024-01-02 22:00:00"),
        )


def test_incomplete_recursive_block_is_excluded() -> None:
    prepared = synthetic_prepared()
    origin = pd.Timestamp("2024-01-10 23:00:00")
    target = prepared.set_index("Datetime")["AEP_MW"].copy()
    target.loc[origin + pd.Timedelta(hours=12)] = np.nan
    with pytest.raises(ValueError, match="No complete"):
        eligible_recursive_origins(
            target,
            pd.DatetimeIndex([origin]),
            FEATURE_CONTRACT,
        )


def test_run_resume_rejects_changed_identity(tmp_path: Path) -> None:
    _contract, _cv, _lock, evidence = load_phase_07_preflight_inputs()
    run_dir, log_path, checkpoint = initialize_run(
        tmp_path, FINAL_CONTRACT, evidence
    )
    assert log_path.name == f"{checkpoint['run_id']}.log"
    restored_log, restored_checkpoint = validate_resume_identity(
        run_dir, FINAL_CONTRACT, evidence
    )
    assert restored_log == log_path
    assert restored_checkpoint["official_outputs_promoted"] is False
    changed = deepcopy(evidence)
    changed["prepared_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="identity|evidence"):
        validate_resume_identity(run_dir, FINAL_CONTRACT, changed)


def test_source_has_no_tuning_or_legacy_runtime_import() -> None:
    source = (PROJECT_ROOT / "src/practice_3_v2/analysis/forecasting.py").read_text(
        encoding="utf-8"
    )
    assert "sample_tuning_parameters" not in source
    assert "select_candidate(" not in source
    assert "from practice_3 " not in source
    assert "import practice_3" not in source
    assert "joblib" not in source
    assert "pickle" not in source


def test_human_execution_artifacts_are_promoted_after_completed_run() -> None:
    outputs = FINAL_CONTRACT["outputs"]
    audit = json.loads(
        (PROJECT_ROOT / outputs["evaluation_audit"]).read_text(encoding="utf-8")
    )
    assert audit["status"] == "PASS"
    assert audit["run_id"].startswith("P7_final_evaluation_")
    assert audit["opening_event"]["after_preflight"] is True
    assert audit["checks"]["binary_model_persisted"] is False
    assert (PROJECT_ROOT / outputs["one_step_predictions"]).is_file()
    assert (PROJECT_ROOT / outputs["recursive_predictions"]).is_file()
