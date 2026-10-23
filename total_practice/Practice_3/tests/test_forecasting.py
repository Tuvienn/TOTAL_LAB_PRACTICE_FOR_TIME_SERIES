from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from practice_3.analysis.forecasting import (
    APPROVED_FORECASTING_CONFIG,
    build_complete_hourly_target_grid,
    build_eligible_origins,
    build_lag_feature_frame,
    create_phase_06_manifest,
    initialize_phase_06_run,
    load_completed_unit_frame,
    load_forecasting_config,
    load_resumable_phase_06_run,
    migrate_failed_run_after_approved_fix,
    predict_one_step_baseline,
    predict_one_step_model,
    predict_recursive_model,
    predict_recursive_persistence,
    predict_recursive_seasonal_naive,
    promote_phase_06_artifacts,
    record_final_test_opening,
    update_phase_06_unit,
    validate_forecasting_config,
    validate_phase_06_entry,
)


CONFIG_PATH = Path("config/forecasting.json")


def test_forecasting_config_matches_approved_contract():
    config = load_forecasting_config(CONFIG_PATH)

    assert config == APPROVED_FORECASTING_CONFIG
    assert validate_forecasting_config(config) == {
        "approved_contract": True,
        "status": "PASS",
    }


def test_forecasting_config_rejects_protocol_change():
    config = deepcopy(APPROVED_FORECASTING_CONFIG)
    config["multi_step"]["horizon"] = 48

    with pytest.raises(ValueError, match="approved contract"):
        validate_forecasting_config(config)


def test_phase_06_entry_gate_keeps_final_test_sealed():
    entry_state = validate_phase_06_entry()

    assert entry_state.audit["status"] == "PASS"
    assert entry_state.audit["final_test_state"] == "SEALED"
    assert entry_state.audit["target_values_accessed"] is False
    assert entry_state.audit["metrics_computed"] is False
    assert entry_state.audit["candidate_order"] == (
        APPROVED_FORECASTING_CONFIG["candidate_order"]
    )


def test_phase_06_entry_gate_rejects_unsealed_model_lock(tmp_path):
    model_lock_path = Path("outputs/results/phase_05_model_lock.json")
    model_lock = json.loads(model_lock_path.read_text(encoding="utf-8"))
    model_lock["final_test"]["sealed"] = False
    changed_path = tmp_path / "phase_05_model_lock.json"
    changed_path.write_text(
        json.dumps(model_lock),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not SEALED"):
        validate_phase_06_entry(model_lock_path=changed_path)


def test_phase_06_manifest_is_ready_but_does_not_open_final_test():
    entry_state = validate_phase_06_entry()
    manifest = create_phase_06_manifest(entry_state)

    assert manifest["status"] == "READY"
    assert manifest["unit_count"] == 10
    assert manifest["final_test_state"] == "SEALED"
    assert manifest["final_test_opened"] is False
    assert manifest["requires_human_execution"] is True


def test_phase_06_run_initialization_and_resume_keep_test_sealed(tmp_path):
    entry_state = validate_phase_06_entry()
    now = datetime(2026, 10, 22, 10, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    run_dir, checkpoint, metadata = initialize_phase_06_run(
        entry_state,
        runs_dir=tmp_path,
        now=now,
    )

    assert checkpoint["status"] == "READY"
    assert checkpoint["opening_event_count"] == 0
    assert checkpoint["final_test_opening_event"] is None
    assert metadata["final_test_state"] == "SEALED"
    resumed_checkpoint, resumed_metadata = load_resumable_phase_06_run(
        entry_state,
        run_dir,
    )
    assert resumed_checkpoint == checkpoint
    assert resumed_metadata == metadata


def test_phase_06_opening_event_is_recorded_only_once(tmp_path):
    entry_state = validate_phase_06_entry()
    now = datetime(2026, 10, 22, 10, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    run_dir, _, _ = initialize_phase_06_run(
        entry_state,
        runs_dir=tmp_path,
        now=now,
    )

    event = record_final_test_opening(run_dir, entry_state, now=now)

    assert event["state_before"] == "SEALED"
    assert event["state_after"] == "OPENED_FOR_FINAL_EVALUATION"
    checkpoint = json.loads(
        (run_dir / "checkpoint.json").read_text(encoding="utf-8")
    )
    assert checkpoint["opening_event_count"] == 1
    with pytest.raises(ValueError, match="already exists"):
        record_final_test_opening(run_dir, entry_state, now=now)


def test_phase_06_resume_rejects_changed_identity(tmp_path):
    entry_state = validate_phase_06_entry()
    run_dir, _, _ = initialize_phase_06_run(
        entry_state,
        runs_dir=tmp_path,
    )
    checkpoint_path = run_dir / "checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    checkpoint["execution_identity"] = "changed"
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")

    with pytest.raises(ValueError, match="execution identity changed"):
        load_resumable_phase_06_run(entry_state, run_dir)


def test_phase_06_unit_requires_opening_and_preserves_result_hash(tmp_path):
    entry_state = validate_phase_06_entry()
    run_dir, _, _ = initialize_phase_06_run(
        entry_state,
        runs_dir=tmp_path,
    )
    result_path = run_dir / "synthetic.csv"
    pd.DataFrame({"value": [1.0]}).to_csv(result_path, index=False)

    with pytest.raises(ValueError, match="before final-test opening"):
        update_phase_06_unit(
            run_dir,
            entry_state,
            "one_step:seasonal_naive_24",
            result_path,
        )

    record_final_test_opening(run_dir, entry_state)
    checkpoint = update_phase_06_unit(
        run_dir,
        entry_state,
        "one_step:seasonal_naive_24",
        result_path,
    )
    unit = checkpoint["units"]["one_step:seasonal_naive_24"]
    assert unit["status"] == "PASS"
    assert load_completed_unit_frame(unit).iloc[0, 0] == 1.0

    result_path.write_text("value\n2.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact changed"):
        load_completed_unit_frame(unit)


def build_ready_promotion_case(tmp_path):
    entry_state = validate_phase_06_entry()
    run_dir, checkpoint, _ = initialize_phase_06_run(
        entry_state,
        runs_dir=tmp_path / "runs",
    )
    record_final_test_opening(run_dir, entry_state)
    for unit_id in checkpoint["units"]:
        result_path = run_dir / f"{unit_id.replace(':', '_')}.csv"
        pd.DataFrame({"value": [1.0]}).to_csv(result_path, index=False)
        update_phase_06_unit(
            run_dir,
            entry_state,
            unit_id,
            result_path,
        )
    figures = {}
    for key in (
        "one_step_full_test",
        "one_step_first_14_days",
        "multi_step_error_by_horizon",
    ):
        official_path = APPROVED_FORECASTING_CONFIG["visualization"][key]
        run_figure = run_dir / f"{key}.png"
        run_figure.write_bytes(key.encode("utf-8"))
        figures[official_path] = run_figure
    return run_dir, figures


def test_phase_06_promotion_completes_as_one_transaction(tmp_path):
    run_dir, figures = build_ready_promotion_case(tmp_path)
    output_root = tmp_path / "official"

    promoted = promote_phase_06_artifacts(
        run_dir=run_dir,
        predictions={
            "one_step": pd.DataFrame({"value": [1.0]}),
            "multi_step": pd.DataFrame({"value": [2.0]}),
        },
        metrics={"one_step": {"status": "PASS"}, "multi_step": {"status": "PASS"}},
        audit={"status": "PASS"},
        figures=figures,
        output_root=output_root,
    )

    assert len(promoted) == 6
    metadata = json.loads(
        (run_dir / "run_metadata.json").read_text(encoding="utf-8")
    )
    checkpoint = json.loads(
        (run_dir / "checkpoint.json").read_text(encoding="utf-8")
    )
    assert metadata["official_outputs_promoted"] is True
    assert metadata["status"] == "COMPLETED"
    assert checkpoint["status"] == "COMPLETED"
    assert len(list((output_root / "outputs").rglob("*.*"))) == 8


def test_phase_06_promotion_rolls_back_partial_replacement(tmp_path):
    run_dir, figures = build_ready_promotion_case(tmp_path)
    output_root = tmp_path / "official"
    original_path = (
        output_root
        / "outputs/results/phase_06_one_step_predictions.csv"
    )
    original_path.parent.mkdir(parents=True, exist_ok=True)
    original_path.write_text("original\n", encoding="utf-8")
    call_count = 0

    def fail_on_second_replacement(source, target):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise OSError("synthetic promotion failure")
        source.replace(target)

    with pytest.raises(OSError, match="synthetic promotion failure"):
        promote_phase_06_artifacts(
            run_dir=run_dir,
            predictions={
                "one_step": pd.DataFrame({"value": [1.0]}),
                "multi_step": pd.DataFrame({"value": [2.0]}),
            },
            metrics={
                "one_step": {"status": "PASS"},
                "multi_step": {"status": "PASS"},
            },
            audit={"status": "PASS"},
            figures=figures,
            output_root=output_root,
            promote_replace=fail_on_second_replacement,
        )

    assert original_path.read_text(encoding="utf-8") == "original\n"
    assert len(list((output_root / "outputs").rglob("*.*"))) == 1
    metadata = json.loads(
        (run_dir / "run_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["status"] == "RUNNING"
    assert metadata["official_outputs_promoted"] is False


def test_lag_feature_frame_uses_only_prior_timestamps():
    index = pd.date_range("2026-01-01", periods=5, freq="h")
    history = pd.Series(np.arange(10.0, 15.0), index=index)
    target_timestamp = index[-1] + pd.Timedelta(hours=1)

    frame = build_lag_feature_frame(
        history,
        target_timestamp,
        ("lag_1", "lag_3", "lag_5"),
    )

    assert frame.index[0] == target_timestamp
    assert frame.iloc[0].to_dict() == {
        "lag_1": 14.0,
        "lag_3": 12.0,
        "lag_5": 10.0,
    }


def test_one_step_predictions_validate_shape_and_baseline():
    X_test = pd.DataFrame(
        {"lag_1": [10.0, 11.0], "lag_24": [3.0, 4.0]}
    )

    class Estimator:
        def predict(self, X):
            return X["lag_1"].to_numpy() + 0.5

    assert np.array_equal(
        predict_one_step_model(Estimator(), X_test),
        np.asarray([10.5, 11.5]),
    )
    assert np.array_equal(
        predict_one_step_baseline(X_test, 24),
        np.asarray([3.0, 4.0]),
    )


def test_recursive_model_uses_previous_predictions():
    index = pd.date_range("2026-01-01", periods=4, freq="h")
    history = pd.Series([1.0, 2.0, 3.0, 4.0], index=index)

    class IncrementEstimator:
        def predict(self, X):
            return X["lag_1"].to_numpy() + 1.0

    predictions = predict_recursive_model(
        IncrementEstimator(),
        history,
        index[-1],
        horizon=3,
        feature_names=("lag_1", "lag_2"),
    )

    assert predictions.to_list() == [5.0, 6.0, 7.0]


def test_recursive_baselines_follow_approved_formulas():
    index = pd.date_range("2026-01-01", periods=48, freq="h")
    history = pd.Series(np.arange(48.0), index=index)
    origin = index[-1]

    persistence = predict_recursive_persistence(history, origin, 24)
    seasonal = predict_recursive_seasonal_naive(history, origin, 24)

    assert (persistence == 47.0).all()
    assert seasonal.iloc[0] == history.loc[origin - pd.Timedelta(hours=23)]
    assert seasonal.iloc[-1] == history.loc[origin]


def test_eligible_origins_require_complete_finite_blocks_and_history():
    index = pd.date_range("2026-01-01", periods=96, freq="h")
    target = pd.Series(np.arange(96.0), index=index)
    test_start = pd.Timestamp("2026-01-03 00:00:00")
    test_end = pd.Timestamp("2026-01-04 23:00:00")

    origins, audit = build_eligible_origins(
        target,
        test_start,
        test_end,
        horizon=24,
        max_lag=24,
        origin_hour=23,
        spacing_hours=24,
    )

    assert origins.to_list() == [
        pd.Timestamp("2026-01-02 23:00:00"),
        pd.Timestamp("2026-01-03 23:00:00"),
    ]
    assert audit["eligible_origins"] == 2
    assert audit["excluded_origins"] == 0

    target.loc["2026-01-04 12:00:00"] = np.nan
    origins, audit = build_eligible_origins(
        target,
        test_start,
        test_end,
        horizon=24,
        max_lag=24,
        origin_hour=23,
        spacing_hours=24,
    )

    assert origins.to_list() == [pd.Timestamp("2026-01-02 23:00:00")]
    assert audit["non_finite_target_block"] == 1


def test_sparse_supervised_target_is_reindexed_without_imputation():
    complete_index = pd.date_range("2026-01-01", periods=72, freq="h")
    sparse_index = complete_index.delete([30, 31])
    sparse = pd.Series(
        np.arange(len(sparse_index), dtype=np.float64),
        index=sparse_index,
    )

    result = build_complete_hourly_target_grid(sparse)

    assert result.index.equals(complete_index)
    assert result.isna().sum() == 2
    assert result.loc[complete_index[30:32]].isna().all()


def test_approved_fix_migration_preserves_opening_and_passed_units(tmp_path):
    entry_state = validate_phase_06_entry()
    run_dir, _, _ = initialize_phase_06_run(
        entry_state,
        runs_dir=tmp_path,
    )
    record_final_test_opening(run_dir, entry_state)
    result_path = run_dir / "one_step.csv"
    pd.DataFrame({"value": [1.0]}).to_csv(result_path, index=False)
    update_phase_06_unit(
        run_dir,
        entry_state,
        "one_step:seasonal_naive_24",
        result_path,
    )
    checkpoint_path = run_dir / "checkpoint.json"
    metadata_path = run_dir / "run_metadata.json"
    manifest_path = run_dir / "evaluation_manifest.json"
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    old_identity = "old-source-identity"
    checkpoint["execution_identity"] = old_identity
    checkpoint["status"] = "FAILED"
    metadata["execution_identity"] = old_identity
    metadata["execution_identity_payload"]["source_sha256"] = {
        "forecasting": "old",
        "evaluation": "old",
        "visualization": "old",
    }
    metadata["status"] = "FAILED"
    manifest["execution_identity"] = old_identity
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    migration = migrate_failed_run_after_approved_fix(
        entry_state,
        run_dir,
        fix_id="synthetic_fix",
    )

    migrated_checkpoint = json.loads(
        checkpoint_path.read_text(encoding="utf-8")
    )
    assert migration["old_execution_identity"] == old_identity
    assert migration["preserved_opening_event_count"] == 1
    assert migration["preserved_passed_units"] == [
        "one_step:seasonal_naive_24"
    ]
    assert migrated_checkpoint["status"] == "INTERRUPTED"
    assert migrated_checkpoint["opening_event_count"] == 1
    assert migrated_checkpoint["completed_unit_count"] == 1
    load_resumable_phase_06_run(entry_state, run_dir)
