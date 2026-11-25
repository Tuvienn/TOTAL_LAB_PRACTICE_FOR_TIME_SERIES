from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3_v2.analysis import supplemental_experiments as supplemental
from practice_3_v2.analysis.supplemental_experiments import (
    EXPECTED_P_VALUES,
    build_common_lag_folds,
    build_consecutive_lag_frame,
    fit_linear_fold,
    initialize_run,
    load_supplemental_inputs,
    natural_eligibility_counts,
    promote_official_bundle,
    run_preflight,
    validate_resume_identity,
    validate_supplemental_contract,
)
from practice_3_v2.data.data_preparation import calculate_sha256, load_json_contract
from practice_3_v2.data.supervised_dataset import (
    PROJECT_ROOT,
    SupervisedFold,
    SupervisedPartition,
)
from practice_3_v2.visualization.supplemental_experiments import (
    save_lag_sensitivity_figure,
    save_model_comparison_figure,
)


CONTRACT = load_json_contract(PROJECT_ROOT / "config/supplemental_experiments.json")


@pytest.fixture(scope="module")
def official_inputs() -> tuple:
    return load_supplemental_inputs()


def synthetic_partition(
    start: str,
    rows: int,
    feature_count: int = 2,
) -> SupervisedPartition:
    index = pd.date_range(start, periods=rows, freq="h", name="target_timestamp")
    base = np.arange(rows, dtype="float64")
    X = pd.DataFrame(
        {f"feature_{column}": base + column for column in range(feature_count)},
        index=index,
    )
    y = pd.Series(3.0 * base + 7.0, index=index, name="AEP_MW")
    metadata = pd.DataFrame(
        {
            "target_timestamp": index,
            "forecast_origin": index - pd.Timedelta(hours=1),
        },
        index=index,
    )
    return SupervisedPartition(X=X, y=y, metadata=metadata)


def test_contract_matches_approved_supplemental_scope() -> None:
    validate_supplemental_contract(CONTRACT)
    assert CONTRACT["lag_sensitivity"]["p_values"] == EXPECTED_P_VALUES
    assert CONTRACT["execution"]["project_data_fits"] == 35
    assert CONTRACT["scope"]["selection_authority"] == "none"
    assert CONTRACT["scope"]["holdout_access_allowed"] is False


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("status",), "DRAFT", "approved"),
        (("evidence_label",), "selection_evidence", "label"),
        (("upstream", "folds"), 4, "upstream"),
        (("linear_regression", "tuning"), True, "Linear Regression"),
        (("lag_sensitivity", "p_values"), [1, 24], "lag-p"),
        (("lag_sensitivity", "rolling_features_included"), True, "Lag-sensitivity"),
        (("execution", "project_data_fits"), 34, "execution"),
        (("scope", "holdout_access_allowed"), True, "scope"),
    ],
)
def test_contract_mutations_are_rejected(
    path: tuple[str, ...],
    value: object,
    message: str,
) -> None:
    changed = deepcopy(CONTRACT)
    cursor = changed
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises(ValueError, match=message):
        validate_supplemental_contract(changed)


def test_official_inputs_lock_features_folds_parameters_and_holdout(
    official_inputs: tuple,
) -> None:
    contract, folds, lag_folds, official_xgboost, evidence = official_inputs
    assert contract == CONTRACT
    assert len(folds) == 5
    assert len(folds[0].train.X.columns) == 22
    assert official_xgboost["parameters"] == contract["lag_sensitivity"]["parameters"]
    assert official_xgboost["aggregate"]["validation_samples"] == 42_413
    assert evidence["holdout_accessed"] is False
    assert evidence["holdout_features_materialized"] is False
    assert evidence["holdout_evaluated"] is False
    assert sorted(lag_folds) == EXPECTED_P_VALUES
    assert [(len(fold.train.X), len(fold.validation.X)) for fold in folds] == [
        (65_670, 8_253),
        (73_923, 8_363),
        (82_286, 8_591),
        (90_877, 8_615),
        (99_492, 8_591),
    ]


def test_consecutive_lag_alignment_and_no_current_or_future_leakage() -> None:
    timestamps = pd.date_range("2020-01-01", periods=12, freq="h")
    development = pd.DataFrame(
        {"Datetime": timestamps, "AEP_MW": np.arange(12, dtype="float64")}
    )
    data_contract = {"timestamp_column": "Datetime", "target_column": "AEP_MW"}
    original = build_consecutive_lag_frame(development, data_contract, max_p=3)
    assert original.loc[5, "lag_1h"] == 4.0
    assert original.loc[5, "lag_2h"] == 3.0
    assert original.loc[5, "lag_3h"] == 2.0
    changed = development.copy()
    changed.loc[5, "AEP_MW"] = 99_999.0
    mutated = build_consecutive_lag_frame(changed, data_contract, max_p=3)
    pd.testing.assert_series_equal(
        original.loc[5, ["lag_1h", "lag_2h", "lag_3h"]],
        mutated.loc[5, ["lag_1h", "lag_2h", "lag_3h"]],
    )
    assert mutated.loc[6, "lag_1h"] == 99_999.0


def test_missing_values_are_not_imputed_and_natural_eligibility_is_monotonic() -> None:
    timestamps = pd.date_range("2020-01-01", periods=240, freq="h")
    target = np.arange(240, dtype="float64")
    target[100] = np.nan
    development = pd.DataFrame({"Datetime": timestamps, "AEP_MW": target})
    frame = build_consecutive_lag_frame(
        development,
        {"timestamp_column": "Datetime", "target_column": "AEP_MW"},
        max_p=168,
    )
    assert np.isnan(frame.loc[100, "target"])
    assert np.isnan(frame.loc[101, "lag_1h"])
    counts = natural_eligibility_counts(frame)
    values = [counts[p] for p in EXPECTED_P_VALUES]
    assert values == sorted(values, reverse=True)


def test_all_p_values_use_exact_common_p168_fold_timestamps(
    official_inputs: tuple,
) -> None:
    _contract, _folds, lag_folds, _official_xgboost, evidence = official_inputs
    reference = lag_folds[168]
    for p in EXPECTED_P_VALUES:
        for actual, expected in zip(lag_folds[p], reference, strict=True):
            assert actual.train.X.index.equals(expected.train.X.index)
            assert actual.validation.X.index.equals(expected.validation.X.index)
            assert actual.train.X.shape[1] == p
    natural = [evidence["natural_eligibility"][str(p)] for p in EXPECTED_P_VALUES]
    assert natural == [112_482, 112_347, 112_185, 111_861, 111_213, 108_083]


def test_linear_fold_uses_train_only_scaler_and_known_metrics() -> None:
    train = synthetic_partition("2020-01-01", 20)
    validation = synthetic_partition("2021-01-01", 8)
    shifted_validation_X = validation.X + 100.0
    validation = SupervisedPartition(
        X=shifted_validation_X,
        y=pd.Series(
            3.0 * shifted_validation_X["feature_0"].to_numpy() + 7.0,
            index=shifted_validation_X.index,
            name="AEP_MW",
        ),
        metadata=validation.metadata,
    )
    fold = SupervisedFold(
        fold=1,
        validation_start=validation.X.index.min(),
        validation_end_exclusive=validation.X.index.max() + pd.Timedelta(hours=1),
        train=train,
        validation=validation,
    )
    record, scaler = fit_linear_fold(fold)
    assert scaler["mean"] == pytest.approx(train.X.mean().tolist())
    assert scaler["mean"] != pytest.approx(
        pd.concat([train.X, validation.X]).mean().tolist()
    )
    assert record["mae"] == pytest.approx(0.0, abs=1e-10)
    assert record["rmse"] == pytest.approx(0.0, abs=1e-10)


def test_common_fold_builder_rejects_no_chronology_and_aligns_features() -> None:
    timestamps = pd.date_range("2020-01-01", periods=260, freq="h")
    development = pd.DataFrame(
        {"Datetime": timestamps, "AEP_MW": np.arange(260, dtype="float64")}
    )
    frame = build_consecutive_lag_frame(
        development,
        {"timestamp_column": "Datetime", "target_column": "AEP_MW"},
        max_p=168,
    )
    split = {
        "development": {"start_inclusive": "2020-01-01 00:00:00"},
        "cross_validation": {
            "folds": [
                {
                    "fold": 1,
                    "validation_start_inclusive": "2020-01-09 08:00:00",
                    "validation_end_exclusive": "2020-01-11 00:00:00",
                }
            ]
        },
    }
    folds = build_common_lag_folds(frame, split, p_values=[1, 168])
    assert folds[1][0].train.X.index.equals(folds[168][0].train.X.index)
    assert folds[1][0].validation.X.index.equals(folds[168][0].validation.X.index)


def _identity_evidence() -> dict:
    return {
        "verified_upstream_sha256": {"phase_05_audit": "a" * 64},
        "prepared_sha256": "b" * 64,
        "package_versions": {"python": "test"},
        "official_feature_order": ["lag_1h"],
        "official_fold_counts": [],
        "natural_eligibility": {"1": 1},
        "common_lag_fold_counts": [],
        "holdout_accessed": False,
        "holdout_features_materialized": False,
        "holdout_evaluated": False,
    }


def test_checkpoint_resume_identity_and_expected_fit_count(tmp_path: Path) -> None:
    evidence = _identity_evidence()
    run_dir, log_path, checkpoint = initialize_run(tmp_path, CONTRACT, evidence)
    assert checkpoint["expected_project_data_fits"] == 35
    assert log_path.name == f"{checkpoint['run_id']}.log"
    restored_log, restored = validate_resume_identity(run_dir, CONTRACT, evidence)
    assert restored_log == log_path
    assert restored["status"] == "READY"
    changed = deepcopy(evidence)
    changed["prepared_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="identity|evidence"):
        validate_resume_identity(run_dir, CONTRACT, changed)


def _dummy_results() -> tuple[dict, dict]:
    fold_metrics = [
        {"fold": fold, "mae": 1.0, "rmse": 2.0, "samples": 2}
        for fold in range(1, 6)
    ]
    aggregate = {
        "folds": 5,
        "validation_samples": 10,
        "mean_cv_mae": 1.0,
        "mean_cv_rmse": 2.0,
        "cv_mae_standard_deviation": 0.0,
        "cv_rmse_standard_deviation": 0.0,
        "standard_deviation_ddof": 0,
    }
    linear = {
        "aggregate": aggregate,
        "official_xgboost_reference": {"aggregate": aggregate},
        "fold_metrics": fold_metrics,
        "status": "PASS",
    }
    lag = {
        "p_results": [
            {
                "p": p,
                "natural_eligible_samples": 100 - index,
                "aggregate": aggregate,
                "fold_metrics": fold_metrics,
            }
            for index, p in enumerate(EXPECTED_P_VALUES)
        ],
        "status": "PASS",
    }
    return linear, lag


def test_supplemental_figures_are_created_from_result_evidence(
    tmp_path: Path,
) -> None:
    linear, lag = _dummy_results()
    model_path = tmp_path / "model.png"
    lag_path = tmp_path / "lag.png"
    save_model_comparison_figure(linear, model_path)
    save_lag_sensitivity_figure(lag, lag_path)
    assert model_path.is_file() and model_path.stat().st_size > 0
    assert lag_path.is_file() and lag_path.stat().st_size > 0


def test_bundle_promotion_writes_audit_last_and_rolls_back_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    run_dir = project / "runs" / "run"
    run_dir.mkdir(parents=True)
    contract = deepcopy(CONTRACT)
    contract["outputs"] = {
        "linear_regression": "outputs/results/linear.json",
        "lag_sensitivity": "outputs/results/lag.json",
        "audit": "outputs/results/audit.json",
        "model_comparison_figure": "outputs/figures/model.png",
        "lag_sensitivity_figure": "outputs/figures/lag.png",
    }
    linear, lag = _dummy_results()

    def fake_figure(_result: dict, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"png")

    monkeypatch.setattr(supplemental, "save_model_comparison_figure", fake_figure)
    monkeypatch.setattr(supplemental, "save_lag_sensitivity_figure", fake_figure)
    real_copy = supplemental.shutil.copy2
    calls = 0

    def failing_copy(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated promotion failure")
        real_copy(source, destination)

    monkeypatch.setattr(supplemental.shutil, "copy2", failing_copy)
    with pytest.raises(OSError, match="simulated"):
        promote_official_bundle(
            project,
            contract,
            _identity_evidence(),
            {"run_id": "run", "execution_identity": "identity"},
            linear,
            lag,
            run_dir,
        )
    assert not any((project / "outputs").rglob("*.json"))
    assert not any((project / "outputs").rglob("*.png"))


def test_preflight_does_not_train_project_data_or_evaluate_holdout() -> None:
    result = run_preflight()
    assert result["status"] == "PASS"
    assert result["training_started"] is False
    assert result["planned_project_data_fits"] == 35
    assert result["holdout_accessed"] is False
    assert result["holdout_evaluated"] is False


def test_official_supplemental_bundle_is_complete_and_hash_linked() -> None:
    outputs = CONTRACT["outputs"]
    audit_path = PROJECT_ROOT / outputs["audit"]
    linear_path = PROJECT_ROOT / outputs["linear_regression"]
    lag_path = PROJECT_ROOT / outputs["lag_sensitivity"]
    model_figure = PROJECT_ROOT / outputs["model_comparison_figure"]
    lag_figure = PROJECT_ROOT / outputs["lag_sensitivity_figure"]
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    linear = json.loads(linear_path.read_text(encoding="utf-8"))
    lag = json.loads(lag_path.read_text(encoding="utf-8"))
    assert audit["status"] == "PASS"
    assert audit["completed_project_data_fits"] == 35
    assert audit["checks"] == {
        "development_only": True,
        "holdout_accessed": False,
        "holdout_evaluated": False,
        "model_lock_changed": False,
        "selection_authority": "none",
        "xgboost_reference_retrained": False,
        "tuning_performed": False,
        "binary_model_persisted": False,
    }
    actual_hashes = {
        "linear_regression": calculate_sha256(linear_path),
        "lag_sensitivity": calculate_sha256(lag_path),
        "model_comparison_figure": calculate_sha256(model_figure),
        "lag_sensitivity_figure": calculate_sha256(lag_figure),
    }
    assert audit["component_sha256"] == actual_hashes
    assert model_figure.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert lag_figure.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    run_dir = PROJECT_ROOT / "runs" / audit["run_id"]
    checkpoint = json.loads(
        (run_dir / "checkpoint.json").read_text(encoding="utf-8")
    )
    assert checkpoint["status"] == "COMPLETED"
    assert checkpoint["official_outputs_promoted"] is True
    assert len(checkpoint["completed_tasks"]) == 35
    assert calculate_sha256(run_dir / "linear_regression_results.json") == actual_hashes[
        "linear_regression"
    ]
    assert calculate_sha256(run_dir / "lag_sensitivity_results.json") == actual_hashes[
        "lag_sensitivity"
    ]
    assert linear["status"] == "PASS"
    assert lag["status"] == "PASS"


def test_official_supplemental_metrics_recompute_and_share_populations() -> None:
    linear = json.loads(
        (PROJECT_ROOT / CONTRACT["outputs"]["linear_regression"]).read_text(
            encoding="utf-8"
        )
    )
    lag = json.loads(
        (PROJECT_ROOT / CONTRACT["outputs"]["lag_sensitivity"]).read_text(
            encoding="utf-8"
        )
    )
    assert supplemental.aggregate_fold_metrics(linear["fold_metrics"]) == pytest.approx(
        linear["aggregate"]
    )
    xgboost = linear["official_xgboost_reference"]
    assert xgboost["retrained"] is False
    assert [item["samples"] for item in linear["fold_metrics"]] == [
        item["samples"] for item in xgboost["fold_metrics"]
    ]
    assert [item["validation_start"] for item in linear["fold_metrics"]] == [
        "2012-08-03 00:00:00",
        "2013-08-03 00:00:00",
        "2014-08-03 00:00:00",
        "2015-08-03 00:00:00",
        "2016-08-03 00:00:00",
    ]
    assert [record["p"] for record in lag["p_results"]] == EXPECTED_P_VALUES
    natural = [record["natural_eligible_samples"] for record in lag["p_results"]]
    assert natural == sorted(natural, reverse=True)
    reference_samples = [
        item["validation_samples"] for item in lag["common_fold_counts"]
    ]
    for record in lag["p_results"]:
        assert supplemental.aggregate_fold_metrics(record["fold_metrics"]) == pytest.approx(
            record["aggregate"]
        )
        assert [item["samples"] for item in record["fold_metrics"]] == reference_samples
        assert record["status"] == "PASS"
    assert lag["parameters"] == CONTRACT["lag_sensitivity"]["parameters"]
    assert lag["tuning"] is False
    assert lag["holdout_evaluated"] is False


def test_model_lock_identity_remains_unchanged_after_supplemental_execution() -> None:
    model_lock = PROJECT_ROOT / CONTRACT["upstream"]["phase_06_model_lock"]
    assert calculate_sha256(model_lock) == CONTRACT["upstream"][
        "phase_06_model_lock_sha256"
    ]


def test_source_and_notebook_respect_supplemental_boundaries() -> None:
    source = (
        PROJECT_ROOT
        / "src/practice_3_v2/analysis/supplemental_experiments.py"
    ).read_text(encoding="utf-8")
    assert "from practice_3 " not in source
    assert "import practice_3" not in source
    assert "GridSearchCV" not in source
    assert "RandomizedSearchCV" not in source
    assert "joblib" not in source
    assert "pickle" not in source
    notebook = json.loads(
        (PROJECT_ROOT / "notebooks/Practice_3_present.ipynb").read_text(
            encoding="utf-8"
        )
    )
    code = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    assert "supplemental_experiments" not in code
    assert ".fit(" not in code
    assert ".predict(" not in code
