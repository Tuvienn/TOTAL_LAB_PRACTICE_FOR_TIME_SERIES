import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_CONTRACT_PATH = PROJECT_ROOT / "config/data_contract.json"
FORECASTING_CONTRACT_PATH = PROJECT_ROOT / "config/forecasting_contract.json"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_raw_dataset_matches_approved_contract() -> None:
    contract = load_json(DATA_CONTRACT_PATH)
    raw_path = PROJECT_ROOT / contract["raw_path"]

    assert raw_path.is_file()
    assert calculate_sha256(raw_path) == contract["raw_sha256"]
    assert contract["expected_columns"] == ["Datetime", "AEP_MW"]
    assert contract["raw_data_policy"] == "immutable"
    assert contract["status"] == "APPROVED"


def test_primary_and_secondary_forecasting_tasks_are_explicit() -> None:
    contract = load_json(FORECASTING_CONTRACT_PATH)

    assert contract["primary_task"] == {
        "name": "one_step_hourly_forecasting",
        "horizon": 1,
        "update_cadence": "hourly",
        "selection_role": "primary",
    }
    assert contract["secondary_task"]["name"] == "recursive_24_hour_forecasting"
    assert contract["secondary_task"]["horizon"] == 24
    assert contract["secondary_task"]["future_actual_target_allowed"] is False
    assert contract["secondary_task"]["selection_role"] == "secondary_stress_test"


def test_temporal_and_holdout_claim_boundaries_are_explicit() -> None:
    design = load_json(FORECASTING_CONTRACT_PATH)["temporal_design"]

    assert design["development_end_exclusive"] == design["holdout_start"]
    assert design["holdout_label"] == "historical_re_evaluation_holdout"
    assert design["holdout_is_claimed_unseen"] is False
    assert design["cv_method"] == "expanding_window"
    assert design["cv_splits"] == 5
    assert design["shuffle"] is False


def test_metric_and_selection_contracts_are_locked() -> None:
    contract = load_json(FORECASTING_CONTRACT_PATH)

    assert contract["metrics"]["primary"] == "mae"
    assert contract["metrics"]["secondary"] == "rmse"
    assert contract["selection_policy"]["protocol"] == "one_step_train_only_cv"
    assert contract["selection_policy"][
        "secondary_recursive_result_may_change_locked_model"
    ] is False
    assert contract["eda_policy"]["scope"] == "development_train_only"
    assert contract["eda_policy"]["holdout_target_access_allowed"] is False
