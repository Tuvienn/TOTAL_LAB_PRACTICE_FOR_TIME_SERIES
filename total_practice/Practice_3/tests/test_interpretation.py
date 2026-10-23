from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_3.analysis.interpretation import (
    EXPECTED_CANDIDATES,
    SELECTED_CANDIDATE,
    SELECTED_FEATURE_CONFIGURATION,
    build_comparison_summary,
    build_feature_importance,
    build_lag_p_analysis,
    build_rolling_analysis,
    classify_rolling_contribution,
    create_phase_07_manifest,
    interpret_feature,
    relative_improvement_percent,
    run_phase_07,
    validate_phase_07_entry,
)
from practice_3.analysis.model_training import TrainingDataset
from practice_3.visualization.interpretation_plots import (
    plot_top_feature_importance,
)


class FakeBooster:
    def __init__(self, score):
        self.score = score

    def get_score(self, importance_type):
        assert importance_type == "gain"
        return self.score


class FakeEstimator:
    def __init__(self, score, **parameters):
        self.score = score
        self.parameters = parameters
        self.fitted = False

    def fit(self, X, y):
        assert X.index.equals(y.index)
        self.fitted = True
        return self

    def get_booster(self):
        assert self.fitted
        return FakeBooster(self.score)


def test_phase_07_entry_gate_validates_official_evidence():
    state = validate_phase_07_entry()

    assert state.selected_feature_configuration == (
        SELECTED_FEATURE_CONFIGURATION
    )
    assert state.cv_selected_candidate == SELECTED_CANDIDATE
    assert state.artifacts["phase_06_audit"]["status"] == "PASS"
    assert list(
        state.artifacts["one_step_metrics"]["candidates"]
    ) == EXPECTED_CANDIDATES


def test_phase_07_manifest_requires_human_execution():
    manifest = create_phase_07_manifest(validate_phase_07_entry())

    assert manifest["status"] == "READY"
    assert manifest["requires_human_execution"] is True
    assert manifest["final_test_refit"] is False
    assert manifest["new_model_selection"] is False


def test_feature_importance_includes_zero_gain_and_is_deterministic():
    estimator = FakeEstimator(
        {"lag_2": 1.0, "lag_1": 2.0}
    )
    X = pd.DataFrame({"lag_1": [1.0], "lag_2": [2.0], "lag_3": [3.0]})
    estimator.fit(X, pd.Series([1.0], index=X.index))

    result = build_feature_importance(
        estimator,
        ("lag_1", "lag_2", "lag_3"),
    )

    assert result["feature"].tolist() == ["lag_1", "lag_2", "lag_3"]
    assert result["gain"].tolist() == [2.0, 1.0, 0.0]
    assert result["rank"].tolist() == [1, 2, 3]
    assert np.isclose(result["normalized_gain"].sum(), 1.0)


def test_feature_importance_rejects_unknown_or_zero_total_gain():
    unknown = FakeEstimator({"unexpected": 1.0})
    zero = FakeEstimator({})
    X = pd.DataFrame({"lag_1": [1.0]})
    y = pd.Series([1.0], index=X.index)
    unknown.fit(X, y)
    zero.fit(X, y)

    with pytest.raises(ValueError, match="unknown feature"):
        build_feature_importance(unknown, ("lag_1",))
    with pytest.raises(ValueError, match="positive"):
        build_feature_importance(zero, ("lag_1",))


def test_feature_group_and_interpretation_are_explicit():
    estimator = FakeEstimator({"unknown_feature": 1.0})
    X = pd.DataFrame({"unknown_feature": [1.0]})
    estimator.fit(X, pd.Series([1.0], index=X.index))

    with pytest.raises(ValueError, match="Unknown feature group"):
        build_feature_importance(estimator, ("unknown_feature",))
    assert "daily recurrence" in interpret_feature("lag_24")[
        "possible_interpretation"
    ]
    assert "does not prove" in interpret_feature("lag_168")["limitation"]


def test_relative_improvement_and_rolling_classification():
    assert relative_improvement_percent(100.0, 90.0) == pytest.approx(10.0)
    assert classify_rolling_contribution(1.01) == "HELPFUL"
    assert classify_rolling_contribution(1.0) == "NEUTRAL"
    assert classify_rolling_contribution(-1.0) == "NEUTRAL"
    assert classify_rolling_contribution(-1.01) == "HARMFUL"


def test_rolling_and_lag_p_analysis_use_phase_05_cv_only():
    state = validate_phase_07_entry()
    rolling = build_rolling_analysis(state.artifacts["screening"])
    lag_p = build_lag_p_analysis(state.artifacts["screening"])

    assert [item["p"] for item in rolling] == [24, 72, 168]
    assert all(item["evidence_scope"] == "TRAIN_ONLY_CV" for item in rolling)
    assert all(item["classification"] == "NEUTRAL" for item in rolling)
    assert lag_p["lag_only"]["best_configuration_by_mean_mae"] == (
        "lag_only_p168"
    )
    assert lag_p["lag_rolling"]["best_configuration_by_mean_mae"] == (
        "lag_rolling_p168"
    )


def test_comparison_summary_keeps_protocols_separate():
    result = build_comparison_summary(validate_phase_07_entry())

    assert len(result) == 21
    assert set(result["evidence_scope"]) == {"TRAIN_ONLY_CV", "FINAL_TEST"}
    assert set(result["forecast_protocol"]) == {
        "one_step",
        "one_step_rolling_observed_history",
        "recursive_24_hour",
    }
    final = result.loc[result["evidence_scope"] == "FINAL_TEST"]
    assert len(final) == 10


def test_top20_plot_is_created(tmp_path):
    frame = pd.DataFrame(
        {
            "feature": [f"lag_{index}" for index in range(1, 21)],
            "normalized_gain": np.linspace(0.1, 0.01, 20),
            "rank": np.arange(1, 21),
        }
    )
    output = tmp_path / "top20.png"

    plot_top_feature_importance(frame, output)

    assert output.exists()
    assert output.stat().st_size > 0


def test_phase_07_run_with_fake_estimator_creates_complete_outputs(tmp_path):
    feature_names = tuple(f"lag_{index}" for index in range(1, 169))
    index = pd.date_range("2020-01-01", periods=12, freq="h")
    X = pd.DataFrame(
        np.arange(12 * 168, dtype=float).reshape(12, 168),
        index=index,
        columns=feature_names,
    )
    y = pd.Series(np.arange(12, dtype=float), index=index, name="AEP_MW")
    dataset = TrainingDataset(
        X=X,
        y=y,
        timestamp_index=index,
        feature_names=feature_names,
    )
    score = {name: float(169 - position) for position, name in enumerate(feature_names, 1)}

    def factory(**parameters):
        return FakeEstimator(score, **parameters)

    result = run_phase_07(
        entry_state=validate_phase_07_entry(),
        training_dataset=dataset,
        estimator_factory=factory,
        results_dir=tmp_path / "results",
        figures_dir=tmp_path / "figures",
    )

    assert result["status"] == "PASS"
    assert result["top_feature"] == "lag_1"
    assert len(result["outputs"]) == 5
    for artifact in result["outputs"].values():
        assert Path(artifact["path"]).exists()
    final_text = (tmp_path / "results" / "phase_07_final_analysis.md").read_text(
        encoding="utf-8"
    )
    assert "THEORETICAL COMPARISON ONLY" in final_text
    assert "ARIMA chưa được train" in final_text
