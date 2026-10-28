from pathlib import Path

from practice_3_v2.analysis.feature_presentation import (
    build_correlation_evidence,
    run,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_feature_correlation_is_development_only() -> None:
    correlation, valid_pairs, evidence = build_correlation_evidence(PROJECT_ROOT)
    assert correlation.shape == (13, 13)
    assert valid_pairs.shape == (13, 13)
    assert evidence["status"] == "PASS"
    assert evidence["scope"]["rows"] == 112535
    assert evidence["scope"]["holdout_target_values_inspected"] is False
    assert correlation.loc["AEP_MW (target)", "lag_1h"] > 0.97


def test_feature_correlation_bundle_is_complete(tmp_path: Path) -> None:
    output_path = tmp_path / "phase_04_feature_presentation.json"
    figure_path = tmp_path / "phase_04_temporal_feature_correlation.png"
    evidence = run(PROJECT_ROOT, output_path, figure_path)
    assert output_path.is_file()
    assert figure_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert evidence["figure"]["bytes"] > 0
    assert len(evidence["correlation_matrix"]) == 13
