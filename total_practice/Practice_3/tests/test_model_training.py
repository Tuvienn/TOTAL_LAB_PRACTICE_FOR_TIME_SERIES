from copy import deepcopy
from dataclasses import fields
from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from practice_3.analysis.model_training import (
    APPROVED_MODEL_TRAINING_CONFIG,
    Phase05EntryState,
    TrainingDataset,
    build_baseline_predictions,
    build_execution_identity,
    build_model_comparison,
    calculate_regression_metrics,
    collect_runtime_versions,
    create_screening_manifest,
    create_random_forest_manifest,
    create_model_lock_manifest,
    create_tuning_manifest,
    create_xgboost_randomized_search,
    evaluate_forecasting_baselines,
    evaluate_xgboost_configuration,
    file_sha256,
    initialize_screening_run,
    load_json_result,
    load_resumable_run,
    load_screening_result,
    load_model_training_config,
    main,
    run_phase_05_screening,
    run_phase_05_random_forest,
    run_phase_05_model_lock,
    run_phase_05_tuning,
    screen_feature_configurations,
    select_feature_configuration,
    select_model_candidate,
    summarize_fold_metrics,
    validate_model_training_config,
    validate_phase_05_entry,
)
from practice_3.data.temporal_split import (
    CVFoldIndices,
    EXPECTED_CONFIGURATION_NAMES,
    EXPECTED_CV_FOLDS,
    EXPECTED_TOP_LEVEL,
)
from practice_3.visualization.training_progress import (
    render_screening_progress,
)


MODEL_CONFIG_PATH = Path("config/model_training.json")


@pytest.fixture(scope="module")
def model_config():
    return load_model_training_config(MODEL_CONFIG_PATH)


@pytest.fixture(scope="module")
def phase_05_entry_state():
    return validate_phase_05_entry(model_config_path=MODEL_CONFIG_PATH)


@pytest.fixture(scope="module")
def baseline_results(phase_05_entry_state):
    return evaluate_forecasting_baselines(phase_05_entry_state)


def test_model_training_config_matches_approved_contract(model_config):
    assert MODEL_CONFIG_PATH.exists()
    assert model_config == APPROVED_MODEL_TRAINING_CONFIG
    assert validate_model_training_config(model_config) == {
        "approved_contract": True,
        "status": "PASS",
    }


@pytest.mark.parametrize(
    ("section", "key", "invalid_value"),
    [
        ("forecast_protocol", "mode", "recursive"),
        ("metrics", "primary", "rmse"),
        ("tuning", "n_iter", 12),
        ("tuning", "early_stopping", True),
        ("policies", "final_test_sealed", False),
        ("policies", "materialize_final_test_in_training", True),
    ],
)
def test_model_training_config_rejects_unapproved_changes(
    model_config,
    section,
    key,
    invalid_value,
):
    invalid_config = deepcopy(model_config)
    invalid_config[section][key] = invalid_value

    with pytest.raises(ValueError, match="approved contract"):
        validate_model_training_config(invalid_config)


def test_phase_05_entry_gate_passes_without_training(phase_05_entry_state):
    audit = phase_05_entry_state.audit

    assert audit["phase"] == "phase_05_entry_gate"
    assert audit["upstream"]["status"] == "PASS"
    assert audit["model_training_config"]["status"] == "PASS"
    assert audit["training_executed"] is False
    assert audit["baseline_evaluation_executed"] is False
    assert audit["status"] == "PASS"


def test_training_population_is_shared_and_finite(phase_05_entry_state):
    training_datasets = phase_05_entry_state.training_datasets

    assert tuple(training_datasets) == EXPECTED_CONFIGURATION_NAMES
    reference_index = training_datasets[
        EXPECTED_CONFIGURATION_NAMES[0]
    ].timestamp_index
    assert len(reference_index) == EXPECTED_TOP_LEVEL["train_rows"]
    assert str(reference_index[0]) == EXPECTED_TOP_LEVEL["train_start"]
    assert str(reference_index[-1]) == EXPECTED_TOP_LEVEL["train_end"]

    for name, dataset in training_datasets.items():
        assert len(dataset.X) == EXPECTED_TOP_LEVEL["train_rows"]
        assert dataset.X.index.equals(dataset.y.index)
        assert dataset.X.index.equals(dataset.timestamp_index)
        assert dataset.timestamp_index.equals(reference_index)
        assert tuple(dataset.X.columns) == dataset.feature_names
        assert "AEP_MW" not in dataset.X.columns
        assert np.isfinite(dataset.X.to_numpy()).all(), name
        assert np.isfinite(dataset.y.to_numpy()).all(), name


def test_cv_fold_identity_matches_phase_04(phase_05_entry_state):
    folds = phase_05_entry_state.cv_fold_indices

    assert len(folds) == len(EXPECTED_CV_FOLDS)
    for fold, expected in zip(folds, EXPECTED_CV_FOLDS):
        assert fold.fold == expected["fold"]
        assert len(fold.train_indices) == expected["train_samples"]
        assert len(fold.validation_indices) == expected[
            "validation_samples"
        ]
        assert fold.train_indices[-1] < fold.validation_indices[0]


def test_final_test_remains_metadata_only_and_sealed(phase_05_entry_state):
    metadata = phase_05_entry_state.final_test_metadata
    exposed_fields = {field.name for field in fields(Phase05EntryState)}

    assert metadata == {
        "sealed": True,
        "rows": EXPECTED_TOP_LEVEL["test_rows"],
        "start": EXPECTED_TOP_LEVEL["test_start"],
        "end": EXPECTED_TOP_LEVEL["test_end"],
        "feature_matrices_materialized": False,
        "target_values_accessed": False,
        "metrics_computed": False,
        "status": "PASS",
    }
    assert "X_test" not in exposed_fields
    assert "y_test" not in exposed_fields


def test_phase_05_rejects_failed_phase_04_audit(tmp_path):
    failed_audit_path = tmp_path / "phase_04_failed.json"
    with failed_audit_path.open("w", encoding="utf-8") as file:
        json.dump(
            {
                "phase": "phase_04_temporal_split_validation",
                "status": "FAIL",
            },
            file,
        )

    with pytest.raises(ValueError, match="has not passed"):
        validate_phase_05_entry(
            model_config_path=MODEL_CONFIG_PATH,
            phase_04_audit_path=failed_audit_path,
        )


def test_runtime_dependencies_are_available(phase_05_entry_state):
    runtime = collect_runtime_versions()

    assert runtime == phase_05_entry_state.audit["runtime"]
    assert set(runtime["packages"]) == {
        "matplotlib",
        "numpy",
        "pandas",
        "scikit-learn",
        "xgboost",
        "pytest",
    }
    assert runtime["status"] == "PASS"


def test_entry_input_identities_are_complete(phase_05_entry_state):
    identities = phase_05_entry_state.audit["input_identities"]

    assert set(identities) == {
        "feature_config",
        "validation_config",
        "model_training_config",
        "phase_03_audit",
        "phase_04_audit",
    }
    for identity in identities.values():
        assert Path(identity["path"]).exists()
        assert len(identity["sha256"]) == 64


def test_regression_metrics_match_manual_calculation():
    actual = np.asarray([2.0, 5.0, 9.0])
    predicted = np.asarray([1.0, 7.0, 8.0])
    errors = actual - predicted

    metrics = calculate_regression_metrics(actual, predicted)

    assert metrics["mae"] == pytest.approx(np.abs(errors).mean())
    assert metrics["rmse"] == pytest.approx(
        np.sqrt(np.square(errors).mean())
    )


@pytest.mark.parametrize("lag", [1, 24])
def test_baseline_predictions_use_approved_lag_feature(
    phase_05_entry_state,
    lag,
):
    dataset = phase_05_entry_state.training_datasets["lag_only_p24"]
    fold = phase_05_entry_state.cv_fold_indices[0]

    predictions = build_baseline_predictions(
        dataset,
        fold.validation_indices,
        lag,
    )
    expected = dataset.X.iloc[fold.validation_indices][f"lag_{lag}"]

    assert predictions.index.equals(expected.index)
    assert np.array_equal(predictions.to_numpy(), expected.to_numpy())
    assert predictions.name == "prediction"


def test_fold_summary_uses_approved_population_standard_deviation():
    fold_metrics = [
        {"mae": 1.0, "rmse": 2.0},
        {"mae": 3.0, "rmse": 4.0},
    ]

    summary = summarize_fold_metrics(fold_metrics, ddof=0)

    assert summary["mean_mae"] == pytest.approx(2.0)
    assert summary["std_mae"] == pytest.approx(1.0)
    assert summary["mean_rmse"] == pytest.approx(3.0)
    assert summary["std_rmse"] == pytest.approx(1.0)
    assert summary["standard_deviation_ddof"] == 0


def test_baselines_cover_all_approved_cv_folds(baseline_results):
    assert tuple(baseline_results["baselines"]) == (
        "seasonal_naive_24",
        "persistence",
    )

    for result in baseline_results["baselines"].values():
        assert len(result["fold_metrics"]) == len(EXPECTED_CV_FOLDS)
        for actual, expected in zip(
            result["fold_metrics"],
            EXPECTED_CV_FOLDS,
        ):
            assert actual["fold"] == expected["fold"]
            assert actual["samples"] == expected["validation_samples"]
            assert actual["validation_start"] == expected[
                "validation_start"
            ]
            assert actual["validation_end"] == expected["validation_end"]
            assert np.isfinite(actual["mae"])
            assert np.isfinite(actual["rmse"])
        assert result["aggregate"]["fold_count"] == 5
        assert result["status"] == "PASS"


def test_first_fold_metrics_match_independent_numpy_calculation(
    phase_05_entry_state,
    baseline_results,
):
    dataset = phase_05_entry_state.training_datasets["lag_only_p24"]
    fold = phase_05_entry_state.cv_fold_indices[0]
    actual = dataset.y.iloc[fold.validation_indices].to_numpy()

    for baseline_name, lag in (
        ("seasonal_naive_24", 24),
        ("persistence", 1),
    ):
        predicted = dataset.X.iloc[fold.validation_indices][
            f"lag_{lag}"
        ].to_numpy()
        errors = actual - predicted
        reported = baseline_results["baselines"][baseline_name][
            "fold_metrics"
        ][0]

        assert reported["mae"] == pytest.approx(
            np.mean(np.abs(errors))
        )
        assert reported["rmse"] == pytest.approx(
            np.sqrt(np.mean(np.square(errors)))
        )


def test_baseline_results_do_not_evaluate_final_test(baseline_results):
    assert baseline_results["protocol"] == "one_step"
    assert baseline_results["final_test_evaluated"] is False
    assert baseline_results["baseline_evaluation_executed"] is True
    assert baseline_results["training_executed"] is False
    assert baseline_results["status"] == "PASS"
    assert "test_metrics" not in baseline_results


def test_baseline_evaluation_is_deterministic(
    phase_05_entry_state,
    baseline_results,
):
    repeated = evaluate_forecasting_baselines(phase_05_entry_state)

    assert repeated == baseline_results


def build_synthetic_screening_results(
    mean_mae_by_name,
    feature_count_by_name=None,
):
    feature_counts = feature_count_by_name or {
        "lag_only_p24": 24,
        "lag_only_p72": 72,
        "lag_only_p168": 168,
        "lag_rolling_p24": 28,
        "lag_rolling_p72": 76,
        "lag_rolling_p168": 172,
    }
    configurations = {}
    for order, name in enumerate(EXPECTED_CONFIGURATION_NAMES):
        mean_mae = float(mean_mae_by_name[name])
        configurations[name] = {
            "configuration": name,
            "feature_count": feature_counts[name],
            "aggregate": {
                "mean_mae": mean_mae,
                "mean_rmse": mean_mae + 10.0 + order,
                "std_mae": 1.0 + order,
            },
            "status": "PASS",
        }
    return {
        "configurations": configurations,
        "status": "PASS",
    }


def test_screening_manifest_prepares_thirty_train_only_fits(
    phase_05_entry_state,
):
    manifest = create_screening_manifest(phase_05_entry_state)

    assert manifest["configuration_count"] == 6
    assert manifest["cv_fold_count"] == 5
    assert manifest["planned_model_fits"] == 30
    assert manifest["final_test_included"] is False
    assert manifest["requires_human_execution"] is True
    assert manifest["status"] == "READY"
    assert [item["name"] for item in manifest["configurations"]] == list(
        EXPECTED_CONFIGURATION_NAMES
    )


def test_selection_prefers_fewer_features_within_one_percent(model_config):
    mean_mae = {
        "lag_only_p24": 100.5,
        "lag_only_p72": 100.4,
        "lag_only_p168": 100.0,
        "lag_rolling_p24": 103.0,
        "lag_rolling_p72": 104.0,
        "lag_rolling_p168": 105.0,
    }
    screening_results = build_synthetic_screening_results(mean_mae)

    selected, evidence = select_feature_configuration(
        screening_results,
        model_config,
    )

    assert selected == "lag_only_p24"
    assert evidence["tolerance_candidates"] == [
        "lag_only_p24",
        "lag_only_p72",
        "lag_only_p168",
    ]
    assert evidence["fewest_feature_count_in_tolerance"] == 24
    assert evidence["status"] == "PASS"


def test_selection_keeps_best_mae_when_simpler_option_exceeds_tolerance(
    model_config,
):
    mean_mae = {
        "lag_only_p24": 102.0,
        "lag_only_p72": 103.0,
        "lag_only_p168": 100.0,
        "lag_rolling_p24": 104.0,
        "lag_rolling_p72": 105.0,
        "lag_rolling_p168": 106.0,
    }
    screening_results = build_synthetic_screening_results(mean_mae)

    selected, evidence = select_feature_configuration(
        screening_results,
        model_config,
    )

    assert selected == "lag_only_p168"
    assert evidence["tolerance_candidates"] == ["lag_only_p168"]


def test_xgboost_fold_orchestration_with_non_training_test_double(
    phase_05_entry_state,
):
    class ConstantEstimator:
        def __init__(self, **parameters):
            self.parameters = parameters
            self.value = None

        def fit(self, X, y):
            self.value = float(np.mean(y.to_numpy()))
            return self

        def predict(self, X):
            return np.full(len(X), self.value, dtype=np.float64)

    dataset = phase_05_entry_state.training_datasets["lag_only_p24"]
    fold = (phase_05_entry_state.cv_fold_indices[0],)
    parameters = phase_05_entry_state.model_config["screening"][
        "parameters"
    ]

    result = evaluate_xgboost_configuration(
        configuration_name="lag_only_p24",
        dataset=dataset,
        cv_fold_indices=fold,
        parameters=parameters,
        estimator_factory=ConstantEstimator,
    )

    assert result["configuration"] == "lag_only_p24"
    assert len(result["fold_metrics"]) == 1
    assert result["fold_metrics"][0]["train_samples"] == 97_283
    assert result["fold_metrics"][0]["validation_samples"] == 2_160
    assert result["fold_metrics"][0]["warnings"] == []
    assert np.isfinite(result["aggregate"]["mean_mae"])
    assert result["status"] == "PASS"


def test_screening_orchestration_with_non_training_test_double(
    phase_05_entry_state,
):
    class LastValueEstimator:
        def __init__(self, **parameters):
            self.parameters = parameters
            self.value = None

        def fit(self, X, y):
            self.value = float(y.iloc[-1])
            return self

        def predict(self, X):
            return np.full(len(X), self.value, dtype=np.float64)

    result = screen_feature_configurations(
        phase_05_entry_state,
        estimator_factory=LastValueEstimator,
    )

    assert tuple(result["configurations"]) == EXPECTED_CONFIGURATION_NAMES
    assert result["manifest"]["planned_model_fits"] == 30
    assert result["selected_feature_configuration"] in (
        EXPECTED_CONFIGURATION_NAMES
    )
    assert result["final_test_evaluated"] is False
    assert result["status"] == "PASS"


def test_screening_cli_dry_run_does_not_train(capsys):
    exit_code = main(["--dry-run-screening"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"planned_model_fits": 30' in output
    assert '"requires_human_execution": true' in output


def build_small_entry_state():
    timestamp_index = pd.date_range(
        "2026-01-01 00:00:00",
        periods=12,
        freq="h",
    )
    target = pd.Series(
        np.linspace(100.0, 111.0, 12),
        index=timestamp_index,
        name="AEP_MW",
    )
    features = pd.DataFrame(
        {
            "lag_1": np.linspace(99.0, 110.0, 12),
            "lag_24": np.linspace(90.0, 101.0, 12),
        },
        index=timestamp_index,
    )
    datasets = {
        name: TrainingDataset(
            X=features.copy(),
            y=target.copy(),
            timestamp_index=timestamp_index.copy(),
            feature_names=("lag_1", "lag_24"),
        )
        for name in EXPECTED_CONFIGURATION_NAMES
    }
    folds = (
        CVFoldIndices(
            fold=1,
            train_indices=np.arange(0, 6),
            validation_indices=np.arange(6, 8),
        ),
        CVFoldIndices(
            fold=2,
            train_indices=np.arange(0, 8),
            validation_indices=np.arange(8, 10),
        ),
    )
    input_identities = {
        name: {"path": f"{name}.json", "sha256": character * 64}
        for name, character in (
            ("feature_config", "a"),
            ("validation_config", "b"),
            ("model_training_config", "c"),
            ("phase_03_audit", "d"),
            ("phase_04_audit", "e"),
        )
    }
    final_test_metadata = {
        "sealed": True,
        "rows": 2,
        "start": "2026-01-01 10:00:00",
        "end": "2026-01-01 11:00:00",
        "feature_matrices_materialized": False,
        "target_values_accessed": False,
        "metrics_computed": False,
        "status": "PASS",
    }
    audit = {
        "status": "PASS",
        "runtime": collect_runtime_versions(),
        "input_identities": input_identities,
        "training_population": {
            "configuration_count": 6,
            "train_rows": 12,
            "status": "PASS",
        },
    }
    return Phase05EntryState(
        training_datasets=datasets,
        cv_fold_indices=folds,
        model_config=deepcopy(APPROVED_MODEL_TRAINING_CONFIG),
        final_test_metadata=final_test_metadata,
        audit=audit,
    )


def test_run_initialization_creates_traceable_artifacts(tmp_path):
    entry_state = build_small_entry_state()
    fixed_time = datetime(
        2026,
        10,
        21,
        14,
        30,
        tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"),
    )

    run_dir, checkpoint, metadata = initialize_screening_run(
        entry_state,
        runs_dir=tmp_path / "runs",
        now=fixed_time,
        plot_callback=render_screening_progress,
    )

    assert run_dir.name.startswith("P5_xgb_screening_20261021_143000_")
    assert checkpoint["status"] == "READY"
    assert checkpoint["total_fold_count"] == 12
    assert metadata["execution_identity"] == checkpoint[
        "execution_identity"
    ]
    assert (run_dir / "checkpoint.json").exists()
    assert (run_dir / "run_metadata.json").exists()
    assert (run_dir / "config_snapshot.json").exists()
    assert (run_dir / "training_progress.png").stat().st_size > 0
    assert (run_dir / "fold_duration.png").stat().st_size > 0


def test_interrupted_run_resumes_without_repeating_passed_folds(tmp_path):
    entry_state = build_small_entry_state()

    class InterruptingEstimator:
        fit_calls = 0

        def __init__(self, **parameters):
            self.value = None

        def fit(self, X, y):
            type(self).fit_calls += 1
            if type(self).fit_calls == 3:
                raise KeyboardInterrupt
            self.value = float(y.mean())
            return self

        def predict(self, X):
            return np.full(len(X), self.value, dtype=np.float64)

    official_output = tmp_path / "outputs" / "screening.json"
    interrupted = run_phase_05_screening(
        output_path=official_output,
        runs_dir=tmp_path / "runs",
        entry_state=entry_state,
        estimator_factory=InterruptingEstimator,
        plot_callback=None,
    )

    assert interrupted["status"] == "INTERRUPTED"
    assert interrupted["completed_fold_count"] == 2
    assert not official_output.exists()

    class ConstantEstimator:
        fit_calls = 0

        def __init__(self, **parameters):
            self.value = None

        def fit(self, X, y):
            type(self).fit_calls += 1
            self.value = float(y.mean())
            return self

        def predict(self, X):
            return np.full(len(X), self.value, dtype=np.float64)

    completed = run_phase_05_screening(
        output_path=official_output,
        resume_run_dir=Path(interrupted["run_dir"]),
        entry_state=entry_state,
        estimator_factory=ConstantEstimator,
        plot_callback=None,
    )

    assert completed["status"] == "PASS"
    assert ConstantEstimator.fit_calls == 10
    assert official_output.exists()
    run_dir = Path(completed["run_dir"])
    checkpoint = load_json_result(run_dir / "checkpoint.json")
    assert checkpoint["status"] == "COMPLETED"
    assert checkpoint["completed_fold_count"] == 12
    assert (run_dir / "screening_results.json").exists()
    assert (run_dir / f"{run_dir.name}.log").exists()
    assert not list(run_dir.glob("*.pt"))


def test_resume_rejects_changed_execution_identity(tmp_path):
    entry_state = build_small_entry_state()
    run_dir, _, _ = initialize_screening_run(
        entry_state,
        runs_dir=tmp_path / "runs",
        plot_callback=None,
    )
    changed_entry_state = build_small_entry_state()
    changed_entry_state.audit["input_identities"]["phase_04_audit"][
        "sha256"
    ] = "f" * 64

    original_identity, _ = build_execution_identity(entry_state)
    changed_identity, _ = build_execution_identity(changed_entry_state)

    assert original_identity != changed_identity
    with pytest.raises(ValueError, match="no longer match"):
        load_resumable_run(changed_entry_state, run_dir)


class FakeXGBoostEstimator:
    def __init__(self, **parameters):
        self.parameters = parameters


class FakeRandomizedSearch:
    def __init__(self, **parameters):
        self.parameters = parameters
        self.cv_results_ = None
        self.best_index_ = None
        self.best_params_ = None

    def fit(self, X, y):
        candidate_count = self.parameters["n_iter"]
        folds = self.parameters["cv"]
        search_space = self.parameters["param_distributions"]
        candidates = []
        for candidate_index in range(candidate_count):
            candidates.append(
                {
                    name: values[candidate_index % len(values)]
                    for name, values in search_space.items()
                }
            )

        cv_results = {
            "params": candidates,
            "mean_fit_time": np.linspace(0.1, 0.2, candidate_count),
            "std_fit_time": np.linspace(0.01, 0.02, candidate_count),
            "rank_test_mae": np.arange(1, candidate_count + 1),
        }
        mae_by_candidate = []
        rmse_by_candidate = []
        for fold_index in range(len(folds)):
            mae = np.asarray(
                [
                    100.0 + candidate_index + fold_index * 0.1
                    for candidate_index in range(candidate_count)
                ]
            )
            rmse = mae + 20.0
            cv_results[f"split{fold_index}_test_mae"] = -mae
            cv_results[f"split{fold_index}_test_rmse"] = -rmse
            mae_by_candidate.append(mae)
            rmse_by_candidate.append(rmse)
        cv_results["mean_test_mae"] = -np.mean(
            mae_by_candidate,
            axis=0,
        )
        cv_results["std_test_mae"] = np.std(
            mae_by_candidate,
            axis=0,
        )
        cv_results["mean_test_rmse"] = -np.mean(
            rmse_by_candidate,
            axis=0,
        )
        cv_results["std_test_rmse"] = np.std(
            rmse_by_candidate,
            axis=0,
        )
        self.cv_results_ = cv_results
        self.best_index_ = 0
        self.best_params_ = candidates[0]
        return self


def test_tuning_manifest_locks_screening_winner(phase_05_entry_state):
    screening_result = load_screening_result()

    manifest = create_tuning_manifest(
        phase_05_entry_state,
        screening_result,
    )

    assert manifest["selected_feature_configuration"] == "lag_only_p168"
    assert manifest["candidate_count"] == 24
    assert manifest["cv_fold_count"] == 5
    assert manifest["planned_model_fits"] == 120
    assert manifest["final_test_included"] is False
    assert manifest["requires_human_execution"] is True
    assert manifest["status"] == "READY"


def test_randomized_search_uses_approved_protocol(phase_05_entry_state):
    search = create_xgboost_randomized_search(
        phase_05_entry_state,
        estimator_factory=FakeXGBoostEstimator,
        search_factory=FakeRandomizedSearch,
    )

    assert search.parameters["n_iter"] == 24
    assert search.parameters["scoring"] == {
        "mae": "neg_mean_absolute_error",
        "rmse": "neg_root_mean_squared_error",
    }
    assert search.parameters["refit"] == "mae"
    assert search.parameters["random_state"] == 42
    assert search.parameters["error_score"] == "raise"
    assert len(search.parameters["cv"]) == 5


def test_tuning_orchestration_with_non_training_test_double(
    phase_05_entry_state,
    tmp_path,
):
    result = run_phase_05_tuning(
        runs_dir=tmp_path / "runs",
        entry_state=phase_05_entry_state,
        estimator_factory=FakeXGBoostEstimator,
        search_factory=FakeRandomizedSearch,
    )

    assert result["status"] == "PASS"
    assert result["candidate_count"] == 24
    assert result["selected_feature_configuration"] == "lag_only_p168"
    assert result["selected_candidate"]["candidate_index"] == 0
    assert result["selected_candidate"]["rank_mae"] == 1
    assert result["selected_full_parameters"]["random_state"] == 42
    assert result["selected_full_parameters"]["objective"] == (
        "reg:squarederror"
    )
    assert result["final_test_evaluated"] is False
    assert result["final_test"]["sealed"] is True
    run_dir = Path(result["run_dir"])
    assert (run_dir / "tuning_results.json").exists()
    metadata = load_json_result(run_dir / "run_metadata.json")
    assert metadata["status"] == "COMPLETED"


def test_tuning_interruption_does_not_create_result(
    phase_05_entry_state,
    tmp_path,
):
    class InterruptedSearch(FakeRandomizedSearch):
        def fit(self, X, y):
            raise KeyboardInterrupt

    result = run_phase_05_tuning(
        runs_dir=tmp_path / "runs",
        entry_state=phase_05_entry_state,
        estimator_factory=FakeXGBoostEstimator,
        search_factory=InterruptedSearch,
    )

    assert result["status"] == "INTERRUPTED"
    assert result["final_test_evaluated"] is False
    run_dir = Path(result["run_dir"])
    assert not (run_dir / "tuning_results.json").exists()
    metadata = load_json_result(run_dir / "run_metadata.json")
    assert metadata["status"] == "INTERRUPTED"


def test_tuning_cli_dry_run_does_not_train(capsys):
    exit_code = main(["--dry-run-tuning"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"selected_feature_configuration": "lag_only_p168"' in output
    assert '"planned_model_fits": 120' in output
    assert '"requires_human_execution": true' in output


def write_fake_tuning_result(path, entry_state):
    fold_metrics = [
        {
            "fold": fold.fold,
            "train_samples": len(fold.train_indices),
            "validation_samples": len(fold.validation_indices),
            "mae": 100.0,
            "rmse": 120.0,
        }
        for fold in entry_state.cv_fold_indices
    ]
    result = {
        "phase": "phase_05_xgboost_tuning",
        "run_id": "P5_xgb_tuning_test",
        "selected_feature_configuration": "lag_only_p168",
        "candidate_count": 24,
        "selected_candidate": {
            "candidate_index": 0,
            "rank_mae": 1,
            "aggregate": {
                "mean_mae": 100.0,
                "std_mae": 0.0,
                "mean_rmse": 120.0,
                "std_rmse": 0.0,
                "standard_deviation_ddof": 0,
            },
            "fold_metrics": fold_metrics,
        },
        "selected_full_parameters": {
            **entry_state.model_config["screening"]["parameters"],
            "n_estimators": 800,
            "max_depth": 7,
        },
        "input_identities": entry_state.audit["input_identities"],
        "final_test": entry_state.final_test_metadata,
        "final_test_evaluated": False,
        "status": "PASS",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
    return result


def test_random_forest_manifest_uses_selected_configuration(
    phase_05_entry_state,
):
    tuning_result = {
        "selected_feature_configuration": "lag_only_p168",
        "input_identities": phase_05_entry_state.audit[
            "input_identities"
        ],
    }

    manifest = create_random_forest_manifest(
        phase_05_entry_state,
        tuning_result,
    )

    assert manifest["model"] == "random_forest"
    assert manifest["selected_feature_configuration"] == "lag_only_p168"
    assert manifest["cv_fold_count"] == 5
    assert manifest["planned_model_fits"] == 5
    assert manifest["parameters"] == phase_05_entry_state.model_config[
        "random_forest"
    ]["parameters"]
    assert manifest["checkpoint_unit"] == "cv_fold"
    assert manifest["resume_supported"] is True
    assert manifest["final_test_included"] is False
    assert manifest["requires_human_execution"] is True


def test_random_forest_cli_dry_run_does_not_train(
    phase_05_entry_state,
    tmp_path,
    capsys,
):
    tuning_result_path = tmp_path / "tuning_results.json"
    write_fake_tuning_result(tuning_result_path, phase_05_entry_state)

    exit_code = main(
        [
            "--dry-run-random-forest",
            "--tuning-result",
            str(tuning_result_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"planned_model_fits": 5' in output
    assert '"selected_feature_configuration": "lag_only_p168"' in output
    assert '"requires_human_execution": true' in output


def test_random_forest_orchestration_with_non_training_test_double(
    tmp_path,
):
    entry_state = build_small_entry_state()
    tuning_result_path = tmp_path / "tuning_results.json"
    write_fake_tuning_result(tuning_result_path, entry_state)

    class ConstantRandomForest:
        fit_calls = 0

        def __init__(self, **parameters):
            self.parameters = parameters
            self.value = None

        def fit(self, X, y):
            type(self).fit_calls += 1
            self.value = float(y.mean())
            return self

        def predict(self, X):
            return np.full(len(X), self.value, dtype=np.float64)

    result = run_phase_05_random_forest(
        tuning_result_path=tuning_result_path,
        runs_dir=tmp_path / "runs",
        entry_state=entry_state,
        estimator_factory=ConstantRandomForest,
    )

    assert result["status"] == "PASS"
    assert result["selected_feature_configuration"] == "lag_only_p168"
    assert len(result["fold_metrics"]) == 2
    assert ConstantRandomForest.fit_calls == 2
    assert result["parameters"] == entry_state.model_config[
        "random_forest"
    ]["parameters"]
    assert result["final_test_evaluated"] is False
    assert result["final_test"]["sealed"] is True
    run_dir = Path(result["run_dir"])
    assert (run_dir / "random_forest_results.json").exists()
    assert (run_dir / "checkpoint.json").exists()
    assert not list(run_dir.glob("*.pt"))


def test_random_forest_resume_skips_passed_fold(tmp_path):
    entry_state = build_small_entry_state()
    tuning_result_path = tmp_path / "tuning_results.json"
    write_fake_tuning_result(tuning_result_path, entry_state)

    class InterruptingRandomForest:
        fit_calls = 0

        def __init__(self, **parameters):
            self.value = None

        def fit(self, X, y):
            type(self).fit_calls += 1
            if type(self).fit_calls == 2:
                raise KeyboardInterrupt
            self.value = float(y.mean())
            return self

        def predict(self, X):
            return np.full(len(X), self.value, dtype=np.float64)

    interrupted = run_phase_05_random_forest(
        tuning_result_path=tuning_result_path,
        runs_dir=tmp_path / "runs",
        entry_state=entry_state,
        estimator_factory=InterruptingRandomForest,
    )

    assert interrupted["status"] == "INTERRUPTED"
    assert interrupted["completed_fold_count"] == 1

    class ResumedRandomForest:
        fit_calls = 0

        def __init__(self, **parameters):
            self.value = None

        def fit(self, X, y):
            type(self).fit_calls += 1
            self.value = float(y.mean())
            return self

        def predict(self, X):
            return np.full(len(X), self.value, dtype=np.float64)

    completed = run_phase_05_random_forest(
        tuning_result_path=tuning_result_path,
        resume_run_dir=Path(interrupted["run_dir"]),
        entry_state=entry_state,
        estimator_factory=ResumedRandomForest,
    )

    assert completed["status"] == "PASS"
    assert ResumedRandomForest.fit_calls == 1
    checkpoint = load_json_result(
        Path(completed["run_dir"]) / "checkpoint.json"
    )
    assert checkpoint["status"] == "COMPLETED"
    assert checkpoint["completed_fold_count"] == 2


def write_fake_random_forest_result(
    path,
    entry_state,
    tuning_result_path,
):
    fold_metrics = [
        {
            "fold": fold.fold,
            "train_samples": len(fold.train_indices),
            "validation_samples": len(fold.validation_indices),
            "train_end": str(
                entry_state.training_datasets[
                    "lag_only_p168"
                ].X.index[fold.train_indices[-1]]
            ),
            "validation_start": str(
                entry_state.training_datasets[
                    "lag_only_p168"
                ].X.index[fold.validation_indices[0]]
            ),
            "validation_end": str(
                entry_state.training_datasets[
                    "lag_only_p168"
                ].X.index[fold.validation_indices[-1]]
            ),
            "mae": 130.0,
            "rmse": 170.0,
            "training_seconds": 1.0,
            "warnings": [],
        }
        for fold in entry_state.cv_fold_indices
    ]
    result = {
        "phase": "phase_05_random_forest_comparison",
        "run_id": "P5_random_forest_test",
        "selected_feature_configuration": "lag_only_p168",
        "parameters": entry_state.model_config["random_forest"][
            "parameters"
        ],
        "fold_metrics": fold_metrics,
        "aggregate": {
            "fold_count": len(fold_metrics),
            "mean_mae": 130.0,
            "std_mae": 0.0,
            "mean_rmse": 170.0,
            "std_rmse": 0.0,
            "standard_deviation_ddof": 0,
            "total_training_seconds": float(len(fold_metrics)),
        },
        "tuning_result": {
            "path": str(tuning_result_path),
            "sha256": file_sha256(tuning_result_path),
            "run_id": "P5_xgb_tuning_test",
        },
        "runtime": entry_state.audit["runtime"],
        "input_identities": entry_state.audit["input_identities"],
        "final_test": entry_state.final_test_metadata,
        "final_test_evaluated": False,
        "status": "PASS",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
    return result


def test_model_lock_manifest_selects_tuned_xgboost(
    phase_05_entry_state,
    tmp_path,
):
    screening_result = load_screening_result()
    tuning_result_path = tmp_path / "tuning_results.json"
    tuning_result = write_fake_tuning_result(
        tuning_result_path,
        phase_05_entry_state,
    )
    random_forest_result_path = tmp_path / "random_forest_results.json"
    random_forest_result = write_fake_random_forest_result(
        random_forest_result_path,
        phase_05_entry_state,
        tuning_result_path,
    )

    comparison = build_model_comparison(
        phase_05_entry_state,
        screening_result,
        tuning_result,
        random_forest_result,
    )
    selected, evidence = select_model_candidate(
        comparison,
        phase_05_entry_state.model_config,
    )
    manifest = create_model_lock_manifest(
        phase_05_entry_state,
        comparison,
    )

    assert tuple(comparison["candidates"]) == (
        "seasonal_naive_24",
        "persistence",
        "xgboost_baseline",
        "xgboost_tuned",
        "random_forest",
    )
    assert selected == "xgboost_tuned"
    assert evidence["tolerance_candidates"] == ["xgboost_tuned"]
    assert manifest["cv_selected_candidate"] == "xgboost_tuned"
    assert manifest["full_train_refit_required"] is True
    assert manifest["full_train_rows"] == 108_083
    assert manifest["final_test_included"] is False


def test_model_selection_prefers_simpler_candidate_within_one_percent(
    model_config,
):
    mean_mae = {
        "seasonal_naive_24": 120.0,
        "persistence": 100.5,
        "xgboost_baseline": 110.0,
        "xgboost_tuned": 100.0,
        "random_forest": 105.0,
    }
    candidates = {
        name: {
            "aggregate": {
                "mean_mae": value,
                "mean_rmse": value + 20.0,
                "std_mae": 1.0,
            }
        }
        for name, value in mean_mae.items()
    }

    selected, evidence = select_model_candidate(
        {"candidates": candidates},
        model_config,
    )

    assert evidence["tolerance_candidates"] == [
        "persistence",
        "xgboost_tuned",
    ]
    assert selected == "persistence"


def test_model_lock_orchestration_refits_without_prediction(
    phase_05_entry_state,
    tmp_path,
):
    tuning_result_path = tmp_path / "tuning_results.json"
    write_fake_tuning_result(tuning_result_path, phase_05_entry_state)
    random_forest_result_path = tmp_path / "random_forest_results.json"
    write_fake_random_forest_result(
        random_forest_result_path,
        phase_05_entry_state,
        tuning_result_path,
    )

    class RefitEstimator:
        fit_calls = 0
        predict_calls = 0

        def __init__(self, **parameters):
            self.parameters = parameters

        def fit(self, X, y):
            type(self).fit_calls += 1
            assert len(X) == len(y) == 108_083
            return self

        def predict(self, X):
            type(self).predict_calls += 1
            raise AssertionError("Model-lock refit must not predict.")

    cv_output = tmp_path / "outputs" / "phase_05_cv_results.json"
    lock_output = tmp_path / "outputs" / "phase_05_model_lock.json"
    result = run_phase_05_model_lock(
        screening_result_path=Path(
            "outputs/results/phase_05_screening_results.json"
        ),
        tuning_result_path=tuning_result_path,
        random_forest_result_path=random_forest_result_path,
        cv_result_output_path=cv_output,
        model_lock_output_path=lock_output,
        runs_dir=tmp_path / "runs",
        entry_state=phase_05_entry_state,
        estimator_factories={"xgboost_tuned": RefitEstimator},
    )

    assert result["status"] == "PASS"
    assert RefitEstimator.fit_calls == 1
    assert RefitEstimator.predict_calls == 0
    assert cv_output.exists()
    assert lock_output.exists()
    model_lock = load_json_result(lock_output)
    assert model_lock["cv_selected_candidate"] == "xgboost_tuned"
    assert len(model_lock["locked_candidates"]) == 5
    assert model_lock["selected_candidate_refit"]["status"] == "PASS"
    assert model_lock["final_test_evaluated"] is False
    assert not list((tmp_path / "runs").rglob("*.pt"))


def test_official_phase_05_cv_results_are_complete_and_sealed(
    phase_05_entry_state,
):
    result = load_json_result(
        Path("outputs/results/phase_05_cv_results.json")
    )

    assert result["status"] == "PASS"
    assert result["selected_feature_configuration"] == "lag_only_p168"
    assert tuple(result["candidates"]) == tuple(
        phase_05_entry_state.model_config["model_lock"][
            "candidate_order"
        ]
    )
    assert all(
        len(candidate["fold_metrics"]) == 5
        for candidate in result["candidates"].values()
    )
    assert result["final_test"]["sealed"] is True
    assert result["final_test"]["metrics_computed"] is False
    assert result["final_test_evaluated"] is False


def test_official_phase_05_model_lock_is_reproducible_and_sealed():
    cv_result_path = Path("outputs/results/phase_05_cv_results.json")
    model_lock = load_json_result(
        Path("outputs/results/phase_05_model_lock.json")
    )

    assert model_lock["status"] == "PASS"
    assert model_lock["cv_selected_candidate"] == "xgboost_tuned"
    assert model_lock["selection_evidence"]["tolerance_candidates"] == [
        "xgboost_tuned"
    ]
    assert len(model_lock["locked_candidates"]) == 5
    assert model_lock["selected_candidate_refit"]["status"] == "PASS"
    assert model_lock["selected_candidate_refit"][
        "prediction_executed"
    ] is False
    assert model_lock["selected_candidate_refit"][
        "binary_model_persisted"
    ] is False
    assert model_lock["cv_results"]["sha256"] == file_sha256(
        cv_result_path
    )
    assert model_lock["final_test"]["sealed"] is True
    assert model_lock["final_test_evaluated"] is False
