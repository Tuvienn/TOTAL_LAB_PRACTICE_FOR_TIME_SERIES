from pathlib import Path

from practice_3_v2.analysis.supervised_presentation import (
    build_supervised_presentation,
    run,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_supervised_presentation_matches_phase_05() -> None:
    evidence = build_supervised_presentation(PROJECT_ROOT)
    assert evidence["status"] == "PASS"
    assert evidence["scope"]["holdout_target_values_inspected"] is False
    assert evidence["scope"]["training_executed"] is False
    assert evidence["feature_groups"] == {
        "lag": 8,
        "rolling": 4,
        "calendar": 10,
        "total": 22,
    }
    assert evidence["matrix_summary"]["x_shape"] == [108083, 22]
    assert evidence["matrix_summary"]["y_shape"] == [108083]
    assert evidence["example_sample"]["target_timestamp"] == "2004-10-08 01:00:00"
    assert evidence["example_sample"]["forecast_origin"] == "2004-10-08 00:00:00"
    assert evidence["example_sample"]["feature_values"]["lag_1h"] == 13271.0
    assert evidence["example_sample"]["target_value"] == 12468.0


def test_supervised_presentation_bundle_is_complete(tmp_path: Path) -> None:
    output_path = tmp_path / "phase_05_supervised_presentation.json"
    figure_path = tmp_path / "phase_05_time_series_to_supervised.png"
    evidence = run(PROJECT_ROOT, output_path, figure_path)
    assert output_path.is_file()
    assert figure_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert evidence["figure"]["bytes"] > 0
