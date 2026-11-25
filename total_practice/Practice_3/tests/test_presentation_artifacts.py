from dataclasses import replace

import pytest

from practice_3.visualization.presentation_artifacts import (
    load_presentation_artifacts,
    validate_presentation_artifacts,
)


def test_presentation_artifacts_load_and_validate() -> None:
    artifacts = load_presentation_artifacts()
    assert artifacts.phase_01_audit["status"] == "PASS"
    assert artifacts.phase_03_presentation["status"] == "PASS"
    assert (
        artifacts.phase_03_presentation["scope"][
            "holdout_target_values_inspected"
        ]
        is False
    )
    assert len(artifacts.phase_03_presentation["annual_stability"]) == 14
    assert artifacts.phase_04_presentation["status"] == "PASS"
    assert len(artifacts.phase_04_presentation["variables"]) == 13
    assert (
        artifacts.phase_04_presentation["scope"][
            "holdout_target_values_inspected"
        ]
        is False
    )
    assert artifacts.phase_06_lock["selected_candidate"] == "xgboost_tuned"
    assert artifacts.phase_05_presentation["status"] == "PASS"
    assert artifacts.phase_05_presentation["matrix_summary"]["x_shape"] == [108083, 22]
    assert artifacts.phase_05_conversion_figure_path.is_file()
    assert artifacts.phase_06_training_diagnostics["status"] == "PASS"
    assert (
        artifacts.phase_06_training_diagnostics["training_summary"]
        ["completed_tuning_fits"]
        == 120
    )
    assert artifacts.phase_06_supplemental_audit["completed_project_data_fits"] == 35
    assert len(artifacts.prepared_data) == 121296
    assert artifacts.phase_06_figure_path.is_file()
    assert artifacts.phase_06_tuning_figure_path.is_file()
    assert artifacts.phase_06_fold_figure_path.is_file()
    assert artifacts.phase_06_supplemental_model_figure_path.is_file()
    assert artifacts.phase_06_supplemental_lag_figure_path.is_file()


def test_presentation_artifacts_reject_model_lock_drift() -> None:
    artifacts = load_presentation_artifacts()
    changed_lock = dict(artifacts.phase_06_lock)
    changed_lock["selected_candidate"] = "persistence"
    changed = replace(artifacts, phase_06_lock=changed_lock)
    with pytest.raises(ValueError, match="selected candidate"):
        validate_presentation_artifacts(changed)
