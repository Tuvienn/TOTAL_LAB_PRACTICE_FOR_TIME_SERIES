from copy import deepcopy
import json
from pathlib import Path
import re

import pytest

from practice_3_v2.analysis.final_conclusion import (
    atomic_write_json,
    build_final_conclusion,
    load_phase_09_inputs,
    run_preflight,
    validate_evidence_consistency,
    validate_final_conclusion_contract,
)
from practice_3_v2.data.data_preparation import calculate_sha256, load_json_contract
from practice_3_v2.data.supervised_dataset import PROJECT_ROOT


CONTRACT = load_json_contract(PROJECT_ROOT / "config/final_conclusion.json")


@pytest.fixture(scope="module")
def inputs() -> tuple:
    return load_phase_09_inputs()


def test_contract_matches_approved_phase_09_scope() -> None:
    validate_final_conclusion_contract(CONTRACT)
    assert len(CONTRACT["upstream"]) == 15
    assert CONTRACT["scope"]["training_allowed"] is False
    assert CONTRACT["scope"]["prediction_allowed"] is False
    assert CONTRACT["scope"]["model_selection_allowed"] is False
    assert CONTRACT["scope"]["arima_empirically_benchmarked"] is False


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("status",), "DRAFT", "approved"),
        (("expected", "selected_candidate"), "linear_regression", "expected"),
        (("expected", "cv_folds"), 4, "expected"),
        (("expected", "lag_p_values"), [1, 24], "expected"),
        (("scope", "training_allowed"), True, "scope"),
        (("scope", "holdout_re_evaluation_allowed"), True, "scope"),
        (("scope", "arima_empirically_benchmarked"), True, "scope"),
        (("outputs", "final_conclusion"), "wrong.json", "output"),
    ],
)
def test_contract_mutations_are_rejected(
    path: tuple[str, ...], value: object, message: str
) -> None:
    changed = deepcopy(CONTRACT)
    cursor = changed
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    with pytest.raises(ValueError, match=message):
        validate_final_conclusion_contract(changed)


def test_all_upstream_identities_and_statuses_are_locked(inputs: tuple) -> None:
    contract, documents, hashes = inputs
    assert contract == CONTRACT
    assert hashes == {
        name: record["sha256"] for name, record in CONTRACT["upstream"].items()
    }
    assert len(documents) == 14
    assert all(document["status"] == "PASS" for document in documents.values())


def test_cross_phase_evidence_is_consistent(inputs: tuple) -> None:
    contract, documents, _hashes = inputs
    validate_evidence_consistency(contract, documents)
    assert documents["phase_06_model_lock"]["selected_candidate"] == "xgboost_tuned"
    assert documents["phase_05_supervised"]["development"]["eligible_rows"] == 108083
    assert documents["phase_07_one_step"]["holdout_label"] == (
        "historical_re_evaluation_holdout"
    )


def test_changed_model_lock_or_population_is_rejected(inputs: tuple) -> None:
    contract, documents, _hashes = inputs
    changed = deepcopy(documents)
    changed["phase_06_model_lock"]["selected_candidate"] = "persistence"
    with pytest.raises(ValueError, match="Selected candidate"):
        validate_evidence_consistency(contract, changed)
    changed = deepcopy(documents)
    changed["phase_07_one_step"]["candidate_metrics"][2]["n_observations"] = 1
    with pytest.raises(ValueError, match="One-step"):
        validate_evidence_consistency(contract, changed)


def test_final_conclusion_is_deterministic(inputs: tuple) -> None:
    contract, documents, hashes = inputs
    first = build_final_conclusion(contract, documents, hashes)
    second = build_final_conclusion(contract, documents, hashes)
    assert first == second
    assert "generated_at" not in first
    assert first["status"] == "PASS"


def test_assignment_answer_metrics_and_formulas(inputs: tuple) -> None:
    contract, documents, hashes = inputs
    result = build_final_conclusion(contract, documents, hashes)
    comparison = result["assignment_answers"]["xgboost_vs_linear_regression"]
    linear_mae = comparison["linear_regression"]["mean_cv_mae"]
    xgboost_mae = comparison["xgboost_tuned"]["mean_cv_mae"]
    expected = (linear_mae - xgboost_mae) / linear_mae * 100.0
    assert comparison["xgboost_mae_improvement_percent"] == pytest.approx(expected)
    assert comparison["validation_samples"] == 42413
    assert comparison["same_validation_population"] is True
    assert comparison["universal_superiority_claim_allowed"] is False


def test_lag_p_answer_preserves_registry_and_claim_boundary(inputs: tuple) -> None:
    contract, documents, hashes = inputs
    result = build_final_conclusion(contract, documents, hashes)
    lag_answer = result["assignment_answers"]["lag_p_sensitivity"]
    assert [record["p"] for record in lag_answer["results"]] == [1, 6, 12, 24, 48, 168]
    assert lag_answer["best_observed_p_by_mean_cv_mae"] == 48
    assert lag_answer["global_optimum_claim_allowed"] is False
    assert lag_answer["official_feature_schema_changed"] is False
    maes = {record["p"]: record["mean_cv_mae"] for record in lag_answer["results"]}
    assert maes[48] < maes[24]
    assert maes[168] > maes[48]


def test_arima_answer_is_explicitly_conceptual(inputs: tuple) -> None:
    contract, documents, hashes = inputs
    answer = build_final_conclusion(contract, documents, hashes)["assignment_answers"][
        "xgboost_vs_arima"
    ]
    assert answer["evidence_type"] == "conceptual_only"
    assert answer["arima_empirically_benchmarked"] is False
    assert answer["head_to_head_superiority_claim_allowed"] is False
    assert "no empirical evidence" in answer["conclusion"]


def test_one_step_and_recursive_protocols_remain_separate(inputs: tuple) -> None:
    contract, documents, hashes = inputs
    evaluation = build_final_conclusion(contract, documents, hashes)["final_evaluation"]
    assert evaluation["one_step"]["xgboost_conclusion"]["mae"] == pytest.approx(
        102.84078405511667
    )
    assert evaluation["recursive_24h"]["xgboost_conclusion"][
        "pooled_mae"
    ] == pytest.approx(509.6515496660904)
    assert evaluation["recursive_24h"]["xgboost_conclusion"][
        "hardest_horizon_by_mae"
    ] == 19


def test_limitations_and_handoff_do_not_overclaim(inputs: tuple) -> None:
    contract, documents, hashes = inputs
    result = build_final_conclusion(contract, documents, hashes)
    assert len(result["scientific_limitations"]) == 9
    boundary = result["claim_boundary"]
    assert boundary["production_readiness_claimed"] is False
    assert boundary["external_generalization_claimed"] is False
    assert boundary["arima_superiority_claimed"] is False
    assert boundary["causal_interpretation_claimed"] is False
    readiness = result["handoff_readiness"]
    assert readiness["training_performed_in_phase_09"] is False
    assert readiness["prediction_performed_in_phase_09"] is False
    assert readiness["holdout_re_evaluated_in_phase_09"] is False


def test_preflight_is_read_only_and_passes() -> None:
    output_path = PROJECT_ROOT / CONTRACT["outputs"]["final_conclusion"]
    existed_before = output_path.exists()
    checksum_before = calculate_sha256(output_path) if existed_before else None
    result = run_preflight()
    assert result["status"] == "PASS"
    assert result["verified_upstream_artifacts"] == 15
    assert result["training_started"] is False
    assert result["prediction_started"] is False
    assert result["holdout_re_evaluated"] is False
    assert output_path.exists() is existed_before
    if existed_before:
        assert calculate_sha256(output_path) == checksum_before


def test_atomic_json_round_trip(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    payload = {"phase": "phase_09", "status": "PASS"}
    atomic_write_json(payload, output)
    assert json.loads(output.read_text(encoding="utf-8")) == payload


def test_official_artifact_matches_deterministic_build(inputs: tuple) -> None:
    contract, documents, hashes = inputs
    expected = build_final_conclusion(contract, documents, hashes)
    output_path = PROJECT_ROOT / contract["outputs"]["final_conclusion"]
    actual = json.loads(output_path.read_text(encoding="utf-8"))
    assert actual == expected
    assert actual["status"] == "PASS"


def test_readme_local_links_exist() -> None:
    readme_path = PROJECT_ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme)
    local_links = [
        link
        for link in links
        if not link.startswith(("http://", "https://", "#"))
    ]
    assert local_links
    assert all((PROJECT_ROOT / link).exists() for link in local_links)


def test_source_and_notebook_respect_phase_09_boundaries() -> None:
    source = (
        PROJECT_ROOT / "src/practice_3_v2/analysis/final_conclusion.py"
    ).read_text(encoding="utf-8")
    assert ".fit(" not in source
    assert ".predict(" not in source
    assert "GridSearchCV" not in source
    assert "RandomizedSearchCV" not in source
    assert "from practice_3 " not in source
    assert "import practice_3" not in source
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
    assert "practice_3_v2.analysis.final_conclusion" not in code
    assert "outputs/results/phase_09_final_conclusion.json" in code
    assert ".fit(" not in code
    assert ".predict(" not in code
