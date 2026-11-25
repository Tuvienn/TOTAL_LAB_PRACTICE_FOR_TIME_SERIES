from pathlib import Path

from practice_3.analysis.eda_presentation import (
    build_presentation_evidence,
    run,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_eda_presentation_uses_development_only() -> None:
    evidence = build_presentation_evidence(PROJECT_ROOT)
    assert evidence["status"] == "PASS"
    assert evidence["scope"]["partition"] == "development_train_validation_only"
    assert evidence["scope"]["holdout_target_values_inspected"] is False
    assert evidence["data_profile"]["rows"] == 112535
    assert len(evidence["top_lag_correlations"]) == 10
    assert len(evidence["top_anomaly_candidates"]) == 10


def test_eda_presentation_bundle_is_complete(tmp_path: Path) -> None:
    output_path = tmp_path / "phase_03_eda_presentation.json"
    figure_path = tmp_path / "phase_03_annual_stability.png"
    evidence = run(PROJECT_ROOT, output_path, figure_path)
    assert figure_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert output_path.is_file()
    assert evidence["figure"]["bytes"] > 0
    assert len(evidence["annual_stability"]) == 14
    assert evidence["annual_stability"][0]["partial_year"] is True
    assert evidence["annual_stability"][-1]["partial_year"] is True
