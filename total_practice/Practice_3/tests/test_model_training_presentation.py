from pathlib import Path

from practice_3.analysis.model_training_presentation import (
    build_training_diagnostics,
    run,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_training_diagnostics_match_model_lock() -> None:
    diagnostics = build_training_diagnostics(PROJECT_ROOT)
    assert diagnostics["status"] == "PASS"
    assert diagnostics["scope"]["holdout_evaluated"] is False
    assert diagnostics["training_summary"]["tuning_candidates"] == 24
    assert diagnostics["training_summary"]["folds_per_candidate"] == 5
    assert diagnostics["training_summary"]["completed_tuning_fits"] == 120
    assert diagnostics["training_summary"]["per_boosting_round_metrics_available"] is False
    assert diagnostics["selected_candidate"]["model"] == "xgboost_tuned"
    assert diagnostics["selected_candidate"]["tuning_candidate_index"] == 22
    assert len(diagnostics["selected_candidate"]["fold_metrics"]) == 5


def test_training_diagnostic_bundle_is_complete(tmp_path: Path) -> None:
    output_path = tmp_path / "phase_06_training_diagnostics.json"
    tuning_figure = tmp_path / "phase_06_tuning_candidates.png"
    fold_figure = tmp_path / "phase_06_selected_candidate_folds.png"
    diagnostics = run(
        PROJECT_ROOT,
        output_path=output_path,
        tuning_figure_path=tuning_figure,
        fold_figure_path=fold_figure,
    )
    assert output_path.is_file()
    assert tuning_figure.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert fold_figure.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(diagnostics["figures"]) == 2
    assert all(figure["bytes"] > 0 for figure in diagnostics["figures"])
