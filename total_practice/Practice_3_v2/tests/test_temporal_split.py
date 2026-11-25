from copy import deepcopy
import json
from pathlib import Path

import pandas as pd
import pytest

from practice_3_v2.data.data_preparation import load_json_contract
from practice_3_v2.data.temporal_split import (
    PROJECT_ROOT,
    build_development_holdout_masks,
    build_expanding_window_folds,
    load_phase_02_inputs,
    run_phase_02,
    validate_contract_alignment,
    validate_prepared_input,
    validate_temporal_split,
)


DATA_CONTRACT = load_json_contract(PROJECT_ROOT / "config/data_contract.json")
PREPARATION_CONTRACT = load_json_contract(
    PROJECT_ROOT / "config/data_preparation.json"
)
SPLIT_CONTRACT = load_json_contract(PROJECT_ROOT / "config/temporal_split.json")
PREPARED_PATH = PROJECT_ROOT / SPLIT_CONTRACT["prepared_input"]
with (PROJECT_ROOT / PREPARATION_CONTRACT["outputs"]["audit"]).open(
    encoding="utf-8"
) as file:
    PHASE_01_AUDIT = json.load(file)


@pytest.fixture(scope="module")
def split_bundle():
    prepared_data, prepared_sha256 = validate_prepared_input(
        PREPARED_PATH,
        DATA_CONTRACT,
        PREPARATION_CONTRACT,
        SPLIT_CONTRACT,
        PHASE_01_AUDIT,
    )
    development_mask, holdout_mask = build_development_holdout_masks(
        prepared_data,
        DATA_CONTRACT,
        SPLIT_CONTRACT,
    )
    folds = build_expanding_window_folds(
        prepared_data,
        DATA_CONTRACT,
        SPLIT_CONTRACT,
    )
    return (
        prepared_data,
        prepared_sha256,
        development_mask,
        holdout_mask,
        folds,
    )


def test_phase_02_inputs_are_approved_and_consistent() -> None:
    _, _, forecasting_contract, split_contract = load_phase_02_inputs()
    temporal_design = forecasting_contract["temporal_design"]
    assert split_contract["status"] == "APPROVED"
    assert split_contract["timestamp_semantics"]["split_key"] == (
        "target_timestamp"
    )
    assert temporal_design["development_end_exclusive"] == (
        split_contract["development"]["end_exclusive"]
    )
    assert temporal_design["holdout_start"] == (
        split_contract["holdout"]["start_inclusive"]
    )
    validate_contract_alignment(forecasting_contract, split_contract)


def test_cross_contract_conflict_is_rejected() -> None:
    _, _, forecasting_contract, split_contract = load_phase_02_inputs()
    invalid_contract = deepcopy(split_contract)
    invalid_contract["cross_validation"]["splits"] = 4
    with pytest.raises(ValueError, match="conflicts with forecasting contract"):
        validate_contract_alignment(forecasting_contract, invalid_contract)


def test_prepared_input_identity_and_structure(split_bundle) -> None:
    prepared_data, prepared_sha256, *_ = split_bundle
    assert prepared_sha256 == SPLIT_CONTRACT["prepared_sha256"]
    assert len(prepared_data) == 121_296
    assert prepared_data["Datetime"].is_monotonic_increasing
    assert prepared_data["Datetime"].is_unique
    assert prepared_data["Datetime"].diff().dropna().eq(
        pd.Timedelta(hours=1)
    ).all()


def test_development_and_holdout_cover_without_overlap(split_bundle) -> None:
    _, _, development_mask, holdout_mask, _ = split_bundle
    assert not (development_mask & holdout_mask).any()
    assert (development_mask | holdout_mask).all()
    assert int(development_mask.sum()) == 112_535
    assert int(holdout_mask.sum()) == 8_761


def test_holdout_end_is_inclusive(split_bundle) -> None:
    prepared_data, _, _, holdout_mask, _ = split_bundle
    holdout = prepared_data.loc[holdout_mask]
    assert holdout["Datetime"].min() == pd.Timestamp("2017-08-03 00:00:00")
    assert holdout["Datetime"].max() == pd.Timestamp("2018-08-03 00:00:00")
    assert holdout["AEP_MW"].notna().sum() == 8_760
    assert holdout["AEP_MW"].isna().sum() == 1


def test_five_expanding_folds_have_approved_counts(split_bundle) -> None:
    prepared_data, _, development_mask, _, folds = split_bundle
    assert len(folds) == 5
    prior_train_count = 0
    prior_validation_end = None
    for fold in folds:
        train_mask = fold["train_mask"]
        validation_mask = fold["validation_mask"]
        contract = fold["contract"]
        assert not (train_mask & validation_mask).any()
        assert not (validation_mask & ~development_mask).any()
        assert int(train_mask.sum()) == contract["expected_train_rows"]
        assert int(validation_mask.sum()) == contract[
            "expected_validation_rows"
        ]
        assert int(train_mask.sum()) > prior_train_count
        if prior_validation_end is not None:
            assert fold["validation_start"] == prior_validation_end
        prior_train_count = int(train_mask.sum())
        prior_validation_end = fold["validation_end_exclusive"]
    assert prior_validation_end == pd.Timestamp("2017-08-03 00:00:00")
    assert int(folds[3]["validation_mask"].sum()) == 8_784


def test_missing_targets_remain_in_timeline_but_are_not_eligible_labels(
    split_bundle,
) -> None:
    prepared_data, _, development_mask, holdout_mask, _ = split_bundle
    assert prepared_data["AEP_MW"].isna().sum() == 27
    assert prepared_data.loc[development_mask, "AEP_MW"].isna().sum() == 26
    assert prepared_data.loc[holdout_mask, "AEP_MW"].isna().sum() == 1
    policy = SPLIT_CONTRACT["missing_target_policy"]
    assert policy == {
        "retain_timeline_rows": True,
        "imputation": "none",
        "training_label_eligible": False,
        "metric_eligible": False,
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("shuffle", True, "cannot shuffle"),
        ("gap_hours", 24, "gap must be zero"),
        ("method", "random_kfold", "must be expanding_window"),
    ],
)
def test_invalid_cv_policy_is_rejected(
    split_bundle,
    field: str,
    value: object,
    message: str,
) -> None:
    prepared_data, _, development_mask, holdout_mask, folds = split_bundle
    invalid_contract = deepcopy(SPLIT_CONTRACT)
    invalid_contract["cross_validation"][field] = value
    with pytest.raises(ValueError, match=message):
        validate_temporal_split(
            prepared_data,
            DATA_CONTRACT,
            invalid_contract,
            development_mask,
            holdout_mask,
            folds,
        )


def test_invalid_boundary_is_rejected(split_bundle) -> None:
    prepared_data, *_ = split_bundle
    invalid_contract = deepcopy(SPLIT_CONTRACT)
    invalid_contract["holdout"]["start_inclusive"] = (
        "2017-08-03 01:00:00"
    )
    with pytest.raises(ValueError, match="not contiguous"):
        build_development_holdout_masks(
            prepared_data,
            DATA_CONTRACT,
            invalid_contract,
        )


def test_phase_02_artifact_is_deterministic(tmp_path: Path) -> None:
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first = run_phase_02(PROJECT_ROOT, first_path)
    second = run_phase_02(PROJECT_ROOT, second_path)
    assert first == second
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["status"] == "PASS"
    assert first["checks"]["development_holdout_overlap"] == 0
    assert first["checks"]["holdout_target_values_inspected"] is False


def test_pipeline_source_does_not_import_legacy_package() -> None:
    source_path = PROJECT_ROOT / "src/practice_3_v2/data/temporal_split.py"
    source = source_path.read_text(encoding="utf-8")
    assert "from practice_3 " not in source
    assert "import practice_3" not in source
