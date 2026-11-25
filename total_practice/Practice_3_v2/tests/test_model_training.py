from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3_v2.analysis.model_training import (
    PROJECT_ROOT,
    append_run_log,
    atomic_write_json,
    dependency_smoke_test,
    evaluate_baseline_candidate,
    initialize_run,
    load_phase_06_inputs,
    run_preflight,
    sample_tuning_parameters,
    select_candidate,
    validate_model_training_contract,
    validate_resume_identity,
)
from practice_3_v2.data.data_preparation import load_json_contract
from practice_3_v2.data.supervised_dataset import (
    SupervisedFold,
    SupervisedPartition,
)


TRAINING_CONTRACT = load_json_contract(PROJECT_ROOT / "config/model_training.json")


def synthetic_partition(start: str, rows: int) -> SupervisedPartition:
    index = pd.date_range(start, periods=rows, freq="h", name="target_timestamp")
    values = np.arange(rows, dtype="float64") + 100.0
    X = pd.DataFrame(
        {"lag_1h": values - 1.0, "lag_24h": values - 24.0},
        index=index,
    )
    y = pd.Series(values, index=index, name="AEP_MW")
    metadata = pd.DataFrame(
        {
            "target_timestamp": index,
            "forecast_origin": index - pd.Timedelta(hours=1),
        },
        index=index,
    )
    return SupervisedPartition(X=X, y=y, metadata=metadata)


def synthetic_folds() -> list[SupervisedFold]:
    folds: list[SupervisedFold] = []
    for fold_index in range(1, 6):
        validation = synthetic_partition(f"202{fold_index}-01-01", 5)
        train = synthetic_partition("2020-01-01", 10 + fold_index)
        folds.append(
            SupervisedFold(
                fold=fold_index,
                validation_start=validation.X.index.min(),
                validation_end_exclusive=validation.X.index.max()
                + pd.Timedelta(hours=1),
                train=train,
                validation=validation,
            )
        )
    return folds


def test_contract_matches_approved_training_scope() -> None:
    validate_model_training_contract(TRAINING_CONTRACT)
    assert TRAINING_CONTRACT["execution"]["executor"] == "human_terminal_only"
    assert TRAINING_CONTRACT["scope"]["holdout_access_allowed"] is False
    assert TRAINING_CONTRACT["execution"]["binary_model_persisted"] is False


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("status",), "DRAFT", "approved"),
        (("upstream", "eligible_samples"), 10, "upstream"),
        (("comparison", "shuffle"), True, "Fair-comparison"),
        (("metrics", "standard_deviation_ddof"), 1, "Metric"),
        (("tuning", "parameter_candidates"), 23, "24"),
        (("execution", "executor"), "ai", "Human-executed"),
        (("scope", "holdout_access_allowed"), True, "scope"),
    ],
)
def test_invalid_contract_changes_are_rejected(
    path: tuple[str, ...],
    value: object,
    message: str,
) -> None:
    changed = deepcopy(TRAINING_CONTRACT)
    cursor = changed
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises(ValueError, match=message):
        validate_model_training_contract(changed)


def test_dependency_import_and_synthetic_fit_predict() -> None:
    result = dependency_smoke_test()
    assert result["synthetic_fit_predict"] == "PASS"
    assert result["versions"]["scikit-learn"]
    assert result["versions"]["xgboost"]


def test_tuning_parameter_sampling_is_deterministic_and_complete() -> None:
    first = sample_tuning_parameters(TRAINING_CONTRACT)
    second = sample_tuning_parameters(TRAINING_CONTRACT)
    assert first == second
    assert len(first) == 24
    assert len({record["parameter_identity"] for record in first}) == 24
    assert [record["candidate_index"] for record in first] == list(range(1, 25))
    for record in first:
        assert record["parameters"]["random_state"] == 42
        assert record["parameters"]["objective"] == "reg:squarederror"


def test_phase_06_inputs_match_phase_05_population() -> None:
    contract, folds, evidence = load_phase_06_inputs()
    assert contract == TRAINING_CONTRACT
    assert evidence["eligible_samples"] == 108_083
    assert len(evidence["feature_order"]) == 22
    assert [(len(fold.train.X), len(fold.validation.X)) for fold in folds] == [
        (65_670, 8_253),
        (73_923, 8_363),
        (82_286, 8_591),
        (90_877, 8_615),
        (99_492, 8_591),
    ]
    reference_validation_indices = [fold.validation.X.index for fold in folds]
    for fold, reference in zip(folds, reference_validation_indices, strict=True):
        assert fold.validation.X.index.equals(reference)
    assert evidence["holdout_evaluated"] is False
    assert evidence["holdout_features_materialized"] is False


def test_preflight_does_not_start_training_or_evaluate_holdout() -> None:
    result = run_preflight()
    assert result["status"] == "PASS"
    assert result["training_started"] is False
    assert result["holdout_evaluated"] is False
    assert result["tuning_parameter_candidates"] == 24


def test_baseline_formulas_and_checkpointing(tmp_path: Path) -> None:
    folds = synthetic_folds()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    log_path = run_dir / "run.log"
    checkpoint = {
        "completed_tasks": [],
        "status": "READY",
        "official_outputs_promoted": False,
        "holdout_evaluated": False,
    }
    persistence = evaluate_baseline_candidate(
        "persistence", "lag_1h", folds, run_dir, log_path, checkpoint
    )
    seasonal = evaluate_baseline_candidate(
        "seasonal_naive_24", "lag_24h", folds, run_dir, log_path, checkpoint
    )
    assert persistence["aggregate"]["mean_cv_mae"] == pytest.approx(1.0)
    assert seasonal["aggregate"]["mean_cv_mae"] == pytest.approx(24.0)
    assert len(checkpoint["completed_tasks"]) == 10
    assert "persistence fold 1/5 started" in log_path.read_text(encoding="utf-8")


def candidate_record(
    name: str,
    mae: float,
    rmse: float,
    standard_deviation: float,
) -> dict[str, object]:
    return {
        "candidate": name,
        "aggregate": {
            "mean_cv_mae": mae,
            "mean_cv_rmse": rmse,
            "cv_mae_standard_deviation": standard_deviation,
        },
    }


def test_selection_uses_approved_metric_order_and_simplicity() -> None:
    order = TRAINING_CONTRACT["selection"]["simplicity_order"]
    records = [candidate_record(name, 10.0 + index, 20.0, 3.0) for index, name in enumerate(order)]
    assert select_candidate(records, TRAINING_CONTRACT["selection"])["candidate"] == "persistence"
    tied = [candidate_record(name, 10.0, 20.0, 3.0) for name in reversed(order)]
    assert select_candidate(tied, TRAINING_CONTRACT["selection"])["candidate"] == "persistence"
    rmse_break = [candidate_record(name, 10.0, 20.0, 3.0) for name in order]
    rmse_break[3]["aggregate"]["mean_cv_rmse"] = 19.0
    assert select_candidate(rmse_break, TRAINING_CONTRACT["selection"])["candidate"] == "random_forest"


def test_atomic_json_and_run_log_format(tmp_path: Path) -> None:
    output = tmp_path / "record.json"
    atomic_write_json({"status": "PASS"}, output)
    assert json.loads(output.read_text(encoding="utf-8")) == {"status": "PASS"}
    log_path = tmp_path / "example.log"
    append_run_log(log_path, "info", "Test message.")
    line = log_path.read_text(encoding="utf-8").strip()
    assert " | INFO | Test message." in line


def test_checkpoint_resume_rejects_changed_identity(tmp_path: Path) -> None:
    evidence = {
        "phase_05_audit_sha256": "a" * 64,
        "prepared_sha256": "b" * 64,
        "feature_order": ["lag_1h"],
        "fold_counts": [],
        "eligible_samples": 1,
        "holdout_evaluated": False,
        "holdout_features_materialized": False,
    }
    run_dir, log_path, checkpoint = initialize_run(
        tmp_path,
        TRAINING_CONTRACT,
        evidence,
    )
    assert log_path.name == f"{checkpoint['run_id']}.log"
    restored_log, restored_checkpoint = validate_resume_identity(
        run_dir,
        TRAINING_CONTRACT,
        evidence,
    )
    assert restored_log == log_path
    assert restored_checkpoint["official_outputs_promoted"] is False
    changed = deepcopy(evidence)
    changed["prepared_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="identity|evidence"):
        validate_resume_identity(run_dir, TRAINING_CONTRACT, changed)


def test_notebook_and_source_respect_phase_06_boundaries() -> None:
    source = (PROJECT_ROOT / "src/practice_3_v2/analysis/model_training.py").read_text(
        encoding="utf-8"
    )
    assert "from practice_3 " not in source
    assert "import practice_3" not in source
    notebook = json.loads(
        (PROJECT_ROOT / "notebooks/Practice_3_v2_present.ipynb").read_text(
            encoding="utf-8"
        )
    )
    code = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    assert "model_training" not in code
    assert ".fit(" not in code
    assert ".predict(" not in code
