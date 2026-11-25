from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3_v2.analysis.interpretation import (
    EXPECTED_CANDIDATES,
    PROJECT_ROOT,
    _promote_phase_08_outputs,
    attach_error_regimes,
    build_exact_lag_residual_acf,
    build_largest_error_records,
    build_recursive_interpretation,
    build_regime_metrics,
    build_residual_summary,
    initialize_run,
    normalize_gain_importance,
    run_preflight,
    validate_error_analysis_contract,
)
from practice_3_v2.data.data_preparation import calculate_sha256, load_json_contract


ERROR_CONTRACT = load_json_contract(PROJECT_ROOT / "config/error_analysis.json")


def synthetic_one_step() -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-01 00:00:00", periods=8, freq="h")
    actual = np.arange(8, dtype="float64") + 100.0
    records: list[dict[str, object]] = []
    offsets = {
        "persistence": -2.0,
        "seasonal_naive_24": 3.0,
        "xgboost_tuned": 1.0,
    }
    for candidate in EXPECTED_CANDIDATES:
        prediction = actual + offsets[candidate]
        for timestamp, observed, forecast in zip(
            timestamps, actual, prediction, strict=True
        ):
            error = float(forecast - observed)
            records.append(
                {
                    "timestamp": timestamp,
                    "candidate": candidate,
                    "actual": float(observed),
                    "prediction": float(forecast),
                    "error": error,
                    "absolute_error": abs(error),
                    "squared_error": error**2,
                    "forecast_protocol": "one_step_rolling_observed_history",
                }
            )
    return pd.DataFrame.from_records(records)


def synthetic_recursive_metrics() -> dict[str, object]:
    records = []
    for candidate_index, candidate in enumerate(EXPECTED_CANDIDATES, start=1):
        per_horizon = [
            {
                "horizon": horizon,
                "mae": float(candidate_index * 10 + horizon),
                "rmse": float(candidate_index * 20 + horizon),
                "n_origins": 5,
            }
            for horizon in range(1, 25)
        ]
        records.append(
            {
                "candidate": candidate,
                "origins": 5,
                "per_horizon": per_horizon,
                "pooled": {
                    "pooled_mae": 1.0,
                    "pooled_rmse": 2.0,
                    "n_predictions": 120,
                    "n_origins": 5,
                },
            }
        )
    return {
        "protocol": "recursive_24_hour",
        "candidate_metrics": records,
        "status": "PASS",
    }


def test_contract_matches_approved_phase_08_scope() -> None:
    validate_error_analysis_contract(ERROR_CONTRACT)
    assert ERROR_CONTRACT["execution"]["executor"] == "human_terminal_only"
    assert ERROR_CONTRACT["scope"]["post_hoc_analysis_only"] is True
    assert ERROR_CONTRACT["scope"]["new_model_selection_allowed"] is False
    assert ERROR_CONTRACT["feature_importance"]["holdout_used_for_importance"] is False


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("status",), "DRAFT", "approved"),
        (("one_step", "summary_statistics"), [], "one-step"),
        (("regimes", "post_hoc_only"), False, "regime"),
        (("recursive", "analysis"), [], "recursive"),
        (("feature_importance", "feature_groups"), {}, "feature-importance"),
        (("execution", "executor"), "ai", "execution"),
        (("scope", "new_model_selection_allowed"), True, "post-hoc"),
        (("outputs", "error_analysis"), "other.json", "output"),
    ],
)
def test_contract_changes_are_rejected(
    path: tuple[str, ...], value: object, message: str
) -> None:
    changed = deepcopy(ERROR_CONTRACT)
    cursor = changed
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises(ValueError, match=message):
        validate_error_analysis_contract(changed)


def test_residual_summary_uses_prediction_minus_actual() -> None:
    summary = build_residual_summary(synthetic_one_step(), EXPECTED_CANDIDATES)
    records = {record["candidate"]: record for record in summary}
    assert records["persistence"]["mean_error"] == pytest.approx(-2.0)
    assert records["seasonal_naive_24"]["mean_error"] == pytest.approx(3.0)
    assert records["xgboost_tuned"]["mae"] == pytest.approx(1.0)
    assert records["xgboost_tuned"]["rmse"] == pytest.approx(1.0)
    assert records["xgboost_tuned"]["over_forecast_rate"] == pytest.approx(1.0)


def test_exact_lag_acf_does_not_compress_timestamp_gaps() -> None:
    timestamps = pd.to_datetime(
        [
            "2024-01-01 00:00:00",
            "2024-01-01 01:00:00",
            "2024-01-01 03:00:00",
            "2024-01-01 04:00:00",
        ]
    )
    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "candidate": "xgboost_tuned",
            "error": [1.0, 2.0, 4.0, 8.0],
        }
    )
    result = build_exact_lag_residual_acf(
        frame, "xgboost_tuned", minimum_lag=1, maximum_lag=1
    )
    assert result.loc[0, "n_pairs"] == 2
    assert result.loc[0, "autocorrelation"] == pytest.approx(1.0)
    assert result.loc[0, "reference_band"] == pytest.approx(1.96 / np.sqrt(2))


def test_largest_errors_have_deterministic_tie_breaking() -> None:
    frame = synthetic_one_step()
    selected = frame["candidate"].eq("xgboost_tuned")
    frame.loc[selected, "absolute_error"] = 5.0
    records = build_largest_error_records(frame, "xgboost_tuned", top_n=3)
    assert [record["rank"] for record in records] == [1, 2, 3]
    assert [record["timestamp"] for record in records] == [
        "2024-01-01 00:00:00",
        "2024-01-01 01:00:00",
        "2024-01-01 02:00:00",
    ]


def test_regimes_share_boundaries_and_conserve_every_candidate() -> None:
    frame, boundaries = attach_error_regimes(
        synthetic_one_step(),
        ERROR_CONTRACT["regimes"]["load_quantiles"],
        ERROR_CONTRACT["regimes"]["load_labels"],
    )
    metrics = build_regime_metrics(
        frame,
        EXPECTED_CANDIDATES,
        ERROR_CONTRACT["regimes"]["dimensions"],
    )
    assert len(boundaries) == 5
    for dimension in ERROR_CONTRACT["regimes"]["dimensions"]:
        for candidate in EXPECTED_CANDIDATES:
            selected = metrics.loc[
                metrics["dimension"].eq(dimension)
                & metrics["candidate"].eq(candidate)
            ]
            assert selected["n_observations"].sum() == 8


def test_regime_assignment_rejects_candidate_actual_disagreement() -> None:
    frame = synthetic_one_step()
    frame.loc[frame.index[-1], "actual"] += 1.0
    with pytest.raises(ValueError, match="disagree"):
        attach_error_regimes(frame, [0.0, 0.25, 0.5, 0.75, 1.0], ["a", "b", "c", "d"])


def test_recursive_interpretation_uses_all_ordered_horizons() -> None:
    result = build_recursive_interpretation(synthetic_recursive_metrics())
    xgboost = result["candidate_horizon_analysis"][2]
    assert xgboost["hardest_horizon_by_mae"] == 24
    assert xgboost["horizons"][0]["mae_growth_from_horizon_1"] == pytest.approx(0.0)
    assert xgboost["horizons"][-1]["mae_growth_from_horizon_1"] == pytest.approx(23.0)
    assert len(result["xgboost_baseline_gaps"]) == 48
    changed = synthetic_recursive_metrics()
    changed["candidate_metrics"][0]["per_horizon"] = changed["candidate_metrics"][0]["per_horizon"][:-1]
    with pytest.raises(ValueError, match="1..24"):
        build_recursive_interpretation(changed)


def test_gain_importance_retains_zero_gain_features_and_normalizes() -> None:
    features = ["lag_1h", "rolling_mean_24h", "hour", "month_cos"]
    result = normalize_gain_importance(
        {"lag_1h": 3.0, "hour": 1.0}, features
    )
    assert set(result["feature"]) == set(features)
    assert result["rank"].tolist() == [1, 2, 3, 4]
    assert result["normalized_gain"].sum() == pytest.approx(1.0)
    assert result.set_index("feature").loc["rolling_mean_24h", "gain"] == 0.0
    assert result.set_index("feature").loc["month_cos", "feature_group"] == "calendar"


def test_preflight_validates_evidence_without_project_refit() -> None:
    result = run_preflight()
    assert result["status"] == "PASS"
    assert result["locked_candidate"] == "xgboost_tuned"
    assert result["one_step_rows_per_candidate"] == 8_592
    assert result["recursive_rows_per_candidate"] == 8_568
    assert result["project_model_refit_started"] is False
    assert result["official_outputs_created"] is True


def test_run_initialization_creates_human_owned_log_and_checkpoint(
    tmp_path: Path,
) -> None:
    evidence = {"phase_07_audit_sha256": "a" * 64}
    run_dir, log_path, checkpoint = initialize_run(
        tmp_path, ERROR_CONTRACT, evidence
    )
    assert run_dir.name.startswith("P8_error_interpretation_")
    assert log_path.name == f"{checkpoint['run_id']}.log"
    assert checkpoint["status"] == "READY"
    assert checkpoint["official_outputs_promoted"] is False
    assert (run_dir / "config_snapshot.json").is_file()
    assert (run_dir / "run_metadata.json").is_file()


def test_bundle_promotion_copies_all_files_with_matching_bytes(
    tmp_path: Path,
) -> None:
    first_source = tmp_path / "first.source"
    second_source = tmp_path / "second.source"
    first_source.write_bytes(b"first")
    second_source.write_bytes(b"second")
    first_output = tmp_path / "official" / "first.output"
    second_output = tmp_path / "official" / "second.output"
    _promote_phase_08_outputs(
        [(first_source, first_output), (second_source, second_output)]
    )
    assert first_output.read_bytes() == first_source.read_bytes()
    assert second_output.read_bytes() == second_source.read_bytes()


def test_failed_bundle_promotion_removes_every_partial_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_source = tmp_path / "first.source"
    second_source = tmp_path / "second.source"
    first_source.write_bytes(b"first")
    second_source.write_bytes(b"second")
    first_output = tmp_path / "official" / "first.output"
    second_output = tmp_path / "official" / "second.output"
    import practice_3_v2.analysis.interpretation as module

    real_replace = module.os.replace
    calls = 0

    def fail_second_replace(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated promotion failure")
        real_replace(source, destination)

    monkeypatch.setattr(module.os, "replace", fail_second_replace)
    with pytest.raises(OSError, match="simulated"):
        _promote_phase_08_outputs(
            [(first_source, first_output), (second_source, second_output)]
        )
    assert not first_output.exists()
    assert not second_output.exists()
    assert not list((tmp_path / "official").glob("*.tmp"))


def test_phase_08_source_has_no_tuning_selection_or_binary_persistence() -> None:
    source = (
        PROJECT_ROOT / "src/practice_3_v2/analysis/interpretation.py"
    ).read_text(encoding="utf-8")
    assert "sample_tuning_parameters" not in source
    assert "select_candidate(" not in source
    assert "joblib" not in source
    assert "pickle" not in source
    assert ".dump(" not in source
    assert "from practice_3." not in source
    assert "import practice_3\n" not in source


def test_notebook_does_not_execute_phase_08_analysis_logic() -> None:
    notebook_path = PROJECT_ROOT / "notebooks/Practice_3_v2_present.ipynb"
    notebook_source = notebook_path.read_text(encoding="utf-8")
    assert "practice_3_v2.analysis.interpretation" not in notebook_source
    assert "run_analysis(" not in notebook_source
    assert "--run" not in notebook_source


def test_human_execution_artifacts_are_complete_and_linked() -> None:
    outputs = ERROR_CONTRACT["outputs"]
    result_path = PROJECT_ROOT / outputs["error_analysis"]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["status"] == "PASS"
    assert result["run_id"].startswith("P8_error_interpretation_")
    assert result["upstream_evidence"]["one_step_rows_per_candidate"] == 8_592
    assert result["upstream_evidence"]["recursive_common_origins"] == 357
    assert result["checks"] == {
        "post_hoc_only": True,
        "model_changed": False,
        "features_changed": False,
        "parameters_changed": False,
        "new_model_selection_performed": False,
        "holdout_used_for_importance": False,
        "binary_model_persisted": False,
        "regime_population_conserved": True,
        "exact_timestamp_acf": True,
    }
    feature_path = PROJECT_ROOT / outputs["feature_importance"]
    feature_importance = pd.read_csv(feature_path)
    assert len(feature_importance) == 22
    assert feature_importance["rank"].tolist() == list(range(1, 23))
    assert feature_importance["normalized_gain"].sum() == pytest.approx(1.0)
    assert result["feature_importance"]["csv_sha256"] == calculate_sha256(
        feature_path
    )
    for figure_record in result["figures"].values():
        figure_path = PROJECT_ROOT / figure_record["path"]
        assert figure_path.is_file()
        assert calculate_sha256(figure_path) == figure_record["sha256"]
    run_dir = PROJECT_ROOT / "runs" / result["run_id"]
    checkpoint = json.loads(
        (run_dir / "checkpoint.json").read_text(encoding="utf-8")
    )
    assert checkpoint["status"] == "COMPLETED"
    assert checkpoint["official_outputs_promoted"] is True
    assert checkpoint["binary_model_persisted"] is False
    assert (run_dir / "error_analysis.json").read_bytes() == result_path.read_bytes()
