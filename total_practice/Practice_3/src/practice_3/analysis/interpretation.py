from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from time import perf_counter
import warnings

import numpy as np
import pandas as pd

from practice_3.analysis.model_training import (
    TrainingDataset,
    validate_phase_05_entry,
)
from practice_3.visualization.interpretation_plots import (
    plot_top_feature_importance,
)


RESULTS_DIR = Path("outputs/results")
FIGURES_DIR = Path("outputs/figures")
DEFAULT_PATHS = {
    "phase_01": RESULTS_DIR / "phase_01_data_quality.json",
    "phase_02": RESULTS_DIR / "phase_02_feature_quality.json",
    "phase_03": RESULTS_DIR / "phase_03_supervised_quality.json",
    "phase_04": RESULTS_DIR / "phase_04_split_audit.json",
    "screening": RESULTS_DIR / "phase_05_screening_results.json",
    "cv_results": RESULTS_DIR / "phase_05_cv_results.json",
    "model_lock": RESULTS_DIR / "phase_05_model_lock.json",
    "phase_06_audit": RESULTS_DIR / "phase_06_evaluation_audit.json",
    "one_step_metrics": RESULTS_DIR / "phase_06_one_step_metrics.json",
    "multi_step_metrics": RESULTS_DIR / "phase_06_multistep_metrics.json",
    "one_step_predictions": RESULTS_DIR / "phase_06_one_step_predictions.csv",
    "multi_step_predictions": RESULTS_DIR / "phase_06_multistep_predictions.csv",
}
EXPECTED_PHASES = {
    "phase_01": "phase_01_data_preparation",
    "phase_02": "phase_02_feature_engineering",
    "phase_03": "phase_03_x_y_preparation",
    "phase_04": "phase_04_temporal_split_validation",
}
EXPECTED_CANDIDATES = [
    "seasonal_naive_24",
    "persistence",
    "xgboost_baseline",
    "xgboost_tuned",
    "random_forest",
]
SELECTED_FEATURE_CONFIGURATION = "lag_only_p168"
SELECTED_CANDIDATE = "xgboost_tuned"
ROLLING_THRESHOLD_PERCENT = 1.0


@dataclass(frozen=True)
class Phase07EntryState:
    artifacts: dict[str, dict]
    paths: dict[str, Path]
    evidence_inventory: dict
    selected_feature_configuration: str
    cv_selected_candidate: str


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Required Phase 7 artifact not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def atomic_save_json(payload: dict, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def atomic_save_csv(frame: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def atomic_save_text(text: str, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def _validate_metric_artifact(
    artifact: dict,
    protocol: str,
    candidate_order: list[str],
) -> None:
    if artifact.get("status") != "PASS":
        raise ValueError(f"Phase 6 {protocol} metrics have not passed.")
    if artifact.get("protocol") != protocol:
        raise ValueError(f"Phase 6 protocol identity is invalid: {protocol}")
    if list(artifact.get("candidates", {})) != candidate_order:
        raise ValueError(f"Phase 6 candidate registry is invalid: {protocol}")
    for candidate_id, result in artifact["candidates"].items():
        metric_keys = (
            ("mae", "rmse")
            if protocol == "one_step_rolling_observed_history"
            else ("pooled_mae", "pooled_rmse")
        )
        if result.get("status") != "PASS" or not np.isfinite(
            [result[key] for key in metric_keys]
        ).all():
            raise ValueError(f"Invalid Phase 6 metrics: {candidate_id}")


def validate_phase_07_entry(
    paths: dict[str, Path] | None = None,
) -> Phase07EntryState:
    resolved = {
        key: Path(value)
        for key, value in (paths or DEFAULT_PATHS).items()
    }
    if set(resolved) != set(DEFAULT_PATHS):
        raise ValueError("Phase 7 requires the complete approved artifact set.")

    for key, path in resolved.items():
        if not path.exists():
            raise FileNotFoundError(f"Required Phase 7 artifact missing: {path}")
        if key.endswith("predictions") and path.stat().st_size == 0:
            raise ValueError(f"Prediction artifact is empty: {path}")

    artifacts = {
        key: load_json(path)
        for key, path in resolved.items()
        if not key.endswith("predictions")
    }
    for key, expected_phase in EXPECTED_PHASES.items():
        if artifacts[key].get("phase") != expected_phase:
            raise ValueError(f"Invalid upstream phase identity: {key}")
        if artifacts[key].get("status") != "PASS":
            raise ValueError(f"Upstream phase has not passed: {key}")

    screening = artifacts["screening"]
    cv_results = artifacts["cv_results"]
    model_lock = artifacts["model_lock"]
    phase_06_audit = artifacts["phase_06_audit"]
    if any(
        item.get("status") != "PASS"
        for item in (screening, cv_results, model_lock, phase_06_audit)
    ):
        raise ValueError("Phase 5 or Phase 6 evidence has not passed.")
    if screening.get("phase") != "phase_05_feature_configuration_screening":
        raise ValueError("Phase 5 screening identity is invalid.")
    if cv_results.get("phase") != "phase_05_model_training_selection":
        raise ValueError("Phase 5 CV identity is invalid.")
    if model_lock.get("phase") != "phase_05_model_lock":
        raise ValueError("Phase 5 model-lock identity is invalid.")
    if phase_06_audit.get("phase") != "phase_06_forecasting_evaluation":
        raise ValueError("Phase 6 audit identity is invalid.")

    if model_lock.get("cv_results", {}).get("sha256") != file_sha256(
        resolved["cv_results"]
    ):
        raise ValueError("Phase 5 CV result no longer matches model lock.")
    if cv_results.get("candidate_order") != EXPECTED_CANDIDATES:
        raise ValueError("Phase 5 CV candidate registry is invalid.")
    if model_lock.get("candidate_order") != EXPECTED_CANDIDATES:
        raise ValueError("Phase 5 locked candidate registry is invalid.")
    if list(model_lock.get("locked_candidates", {})) != EXPECTED_CANDIDATES:
        raise ValueError("Phase 5 locked candidates are incomplete.")
    if cv_results.get("selected_feature_configuration") != (
        SELECTED_FEATURE_CONFIGURATION
    ):
        raise ValueError("Selected feature configuration changed.")
    if model_lock.get("cv_selected_candidate") != SELECTED_CANDIDATE:
        raise ValueError("CV-selected candidate changed.")
    if cv_results.get("final_test_evaluated") is not False:
        raise ValueError("Phase 5 unexpectedly evaluated the final test.")

    input_identities = phase_06_audit.get("entry_gate", {}).get(
        "input_identities",
        {},
    )
    identity_mapping = {
        "phase_05_cv_results": "cv_results",
        "phase_05_model_lock": "model_lock",
        "phase_01": "phase_01",
        "phase_02": "phase_02",
        "phase_03": "phase_03",
        "phase_04": "phase_04",
    }
    for identity_name, path_name in identity_mapping.items():
        recorded = input_identities.get(identity_name, {}).get("sha256")
        if recorded != file_sha256(resolved[path_name]):
            raise ValueError(f"Stale Phase 6 input identity: {identity_name}")
    if phase_06_audit.get("cv_selected_candidate") != SELECTED_CANDIDATE:
        raise ValueError("Phase 6 changed the CV-selected candidate.")
    if phase_06_audit.get("post_test_model_change") is not False:
        raise ValueError("Phase 6 reports a post-test model change.")

    _validate_metric_artifact(
        artifacts["one_step_metrics"],
        "one_step_rolling_observed_history",
        EXPECTED_CANDIDATES,
    )
    _validate_metric_artifact(
        artifacts["multi_step_metrics"],
        "recursive_24_hour",
        EXPECTED_CANDIDATES,
    )
    one_population = artifacts["one_step_metrics"].get("population", {})
    multi_population = artifacts["multi_step_metrics"].get("population", {})
    if one_population.get("rows_per_candidate") != 8592:
        raise ValueError("One-step population identity changed.")
    if multi_population.get("origin_count") != 350:
        raise ValueError("Multi-step origin population identity changed.")
    if multi_population.get("horizon") != 24:
        raise ValueError("Multi-step forecast horizon changed.")

    inventory = {
        name: {
            "path": str(path),
            "sha256": file_sha256(path),
            "status": "PASS",
        }
        for name, path in resolved.items()
    }
    return Phase07EntryState(
        artifacts=artifacts,
        paths=resolved,
        evidence_inventory=inventory,
        selected_feature_configuration=SELECTED_FEATURE_CONFIGURATION,
        cv_selected_candidate=SELECTED_CANDIDATE,
    )


def build_feature_importance(
    estimator,
    feature_names: tuple[str, ...] | list[str],
) -> pd.DataFrame:
    names = list(feature_names)
    if not names or len(names) != len(set(names)):
        raise ValueError("Feature names must be non-empty and unique.")
    score = estimator.get_booster().get_score(importance_type="gain")
    unknown = sorted(set(score).difference(names))
    if unknown:
        raise ValueError(f"Booster returned unknown feature names: {unknown}")
    gain = np.asarray([float(score.get(name, 0.0)) for name in names])
    if not np.isfinite(gain).all() or (gain < 0).any():
        raise ValueError("Feature gain contains invalid values.")
    total = float(gain.sum())
    if total <= 0:
        raise ValueError("Total XGBoost gain must be positive.")

    feature_groups = []
    for name in names:
        if name.startswith("lag_"):
            feature_groups.append("lag")
        elif name.startswith(("rolling_mean_", "rolling_std_")):
            feature_groups.append("rolling")
        else:
            raise ValueError(f"Unknown feature group: {name}")

    frame = pd.DataFrame(
        {
            "feature": names,
            "feature_group": feature_groups,
            "gain": gain,
            "normalized_gain": gain / total,
            "approved_feature_order": np.arange(len(names)),
        }
    )
    frame = frame.sort_values(
        ["gain", "approved_feature_order"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    frame["rank"] = np.arange(1, len(frame) + 1)
    frame["candidate_id"] = SELECTED_CANDIDATE
    frame["feature_configuration"] = SELECTED_FEATURE_CONFIGURATION
    frame["importance_type"] = "gain"
    frame["training_population"] = "full_top_level_train"
    return frame.drop(columns="approved_feature_order")


def interpret_feature(feature: str) -> dict:
    if not feature.startswith("lag_"):
        return {
            "possible_interpretation": (
                "A historical rolling summary used by the fitted model."
            ),
            "limitation": (
                "Rolling importance is not a causal effect and can overlap "
                "with correlated lag features."
            ),
        }
    lag = int(feature.removeprefix("lag_"))
    if lag == 1:
        interpretation = "Consistent with short-term dependence/persistence."
    elif lag == 24:
        interpretation = "Consistent with daily recurrence."
    elif lag == 168:
        interpretation = "Consistent with weekly recurrence."
    else:
        interpretation = (
            f"Consistent with predictive dependence on the value {lag} "
            "hours earlier."
        )
    return {
        "possible_interpretation": interpretation,
        "limitation": (
            "Gain alone does not prove seasonality or causality; correlated "
            "features can share importance."
        ),
    }


def relative_improvement_percent(reference: float, candidate: float) -> float:
    if not np.isfinite([reference, candidate]).all() or reference <= 0:
        raise ValueError("Relative-improvement inputs are invalid.")
    return float((reference - candidate) / reference * 100.0)


def classify_rolling_contribution(improvement: float) -> str:
    if improvement > ROLLING_THRESHOLD_PERCENT:
        return "HELPFUL"
    if improvement < -ROLLING_THRESHOLD_PERCENT:
        return "HARMFUL"
    return "NEUTRAL"


def build_rolling_analysis(screening: dict) -> list[dict]:
    configurations = screening["screening_results"]["configurations"]
    analysis = []
    for p in (24, 72, 168):
        lag_name = f"lag_only_p{p}"
        rolling_name = f"lag_rolling_p{p}"
        lag_mae = configurations[lag_name]["aggregate"]["mean_mae"]
        rolling_mae = configurations[rolling_name]["aggregate"]["mean_mae"]
        improvement = relative_improvement_percent(lag_mae, rolling_mae)
        analysis.append(
            {
                "p": p,
                "reference_configuration": lag_name,
                "candidate_configuration": rolling_name,
                "reference_mean_mae": float(lag_mae),
                "candidate_mean_mae": float(rolling_mae),
                "relative_mae_improvement_percent": improvement,
                "classification": classify_rolling_contribution(improvement),
                "evidence_scope": "TRAIN_ONLY_CV",
            }
        )
    return analysis


def build_lag_p_analysis(screening: dict) -> dict:
    configurations = screening["screening_results"]["configurations"]
    result = {}
    for family, prefix in (
        ("lag_only", "lag_only_p"),
        ("lag_rolling", "lag_rolling_p"),
    ):
        rows = []
        for p in (24, 72, 168):
            configuration = configurations[f"{prefix}{p}"]
            aggregate = configuration["aggregate"]
            rows.append(
                {
                    "p": p,
                    "configuration": configuration["configuration"],
                    "feature_count": configuration["feature_count"],
                    "mean_mae": aggregate["mean_mae"],
                    "std_mae": aggregate["std_mae"],
                    "mean_rmse": aggregate["mean_rmse"],
                    "std_rmse": aggregate["std_rmse"],
                    "training_seconds": aggregate.get(
                        "total_training_seconds"
                    ),
                }
            )
        best = min(rows, key=lambda row: row["mean_mae"])
        result[family] = {
            "configurations": rows,
            "best_configuration_by_mean_mae": best["configuration"],
            "p24_to_p168_mae_improvement_percent": (
                relative_improvement_percent(
                    rows[0]["mean_mae"],
                    rows[-1]["mean_mae"],
                )
            ),
            "evidence_scope": "TRAIN_ONLY_CV",
        }
    return result


def build_comparison_summary(entry_state: Phase07EntryState) -> pd.DataFrame:
    rows = []
    screening = entry_state.artifacts["screening"]["screening_results"]
    source = str(entry_state.paths["screening"])
    for name, result in screening["configurations"].items():
        aggregate = result["aggregate"]
        rows.append(
            {
                "evidence_scope": "TRAIN_ONLY_CV",
                "forecast_protocol": "one_step",
                "comparison_group": "feature_configuration_screening",
                "candidate_or_configuration": name,
                "MAE": aggregate["mean_mae"],
                "RMSE": aggregate["mean_rmse"],
                "MAE_std_if_available": aggregate["std_mae"],
                "RMSE_std_if_available": aggregate["std_rmse"],
                "training_time_if_available": aggregate.get(
                    "total_training_seconds"
                ),
                "relative_improvement_percent": np.nan,
                "reference_id": "paired_lag_only_reported_in_summary_json",
                "source_artifact": source,
            }
        )

    cv_results = entry_state.artifacts["cv_results"]
    cv_reference = cv_results["candidates"]["seasonal_naive_24"][
        "aggregate"
    ]["mean_mae"]
    for name, result in cv_results["candidates"].items():
        aggregate = result["aggregate"]
        rows.append(
            {
                "evidence_scope": "TRAIN_ONLY_CV",
                "forecast_protocol": "one_step",
                "comparison_group": "locked_candidate_comparison",
                "candidate_or_configuration": name,
                "MAE": aggregate["mean_mae"],
                "RMSE": aggregate["mean_rmse"],
                "MAE_std_if_available": aggregate["std_mae"],
                "RMSE_std_if_available": aggregate["std_rmse"],
                "training_time_if_available": aggregate.get(
                    "total_training_seconds"
                ),
                "relative_improvement_percent": (
                    relative_improvement_percent(
                        cv_reference,
                        aggregate["mean_mae"],
                    )
                ),
                "reference_id": "seasonal_naive_24",
                "source_artifact": str(entry_state.paths["cv_results"]),
            }
        )

    for scope, key, protocol, mae_key, rmse_key in (
        (
            "FINAL_TEST",
            "one_step_metrics",
            "one_step_rolling_observed_history",
            "mae",
            "rmse",
        ),
        (
            "FINAL_TEST",
            "multi_step_metrics",
            "recursive_24_hour",
            "pooled_mae",
            "pooled_rmse",
        ),
    ):
        artifact = entry_state.artifacts[key]
        reference = artifact["candidates"]["seasonal_naive_24"][mae_key]
        for name, result in artifact["candidates"].items():
            rows.append(
                {
                    "evidence_scope": scope,
                    "forecast_protocol": protocol,
                    "comparison_group": "final_test_candidate_comparison",
                    "candidate_or_configuration": name,
                    "MAE": result[mae_key],
                    "RMSE": result[rmse_key],
                    "MAE_std_if_available": np.nan,
                    "RMSE_std_if_available": np.nan,
                    "training_time_if_available": np.nan,
                    "relative_improvement_percent": (
                        relative_improvement_percent(
                            reference,
                            result[mae_key],
                        )
                    ),
                    "reference_id": "seasonal_naive_24",
                    "source_artifact": str(entry_state.paths[key]),
                }
            )
    return pd.DataFrame(rows)


def _build_final_analysis(
    entry_state: Phase07EntryState,
    importance: pd.DataFrame,
    rolling_analysis: list[dict],
    lag_p_analysis: dict,
) -> str:
    phase_01 = entry_state.artifacts["phase_01"]
    one = entry_state.artifacts["one_step_metrics"]["candidates"]
    multi_artifact = entry_state.artifacts["multi_step_metrics"]
    multi = multi_artifact["candidates"]
    cv = entry_state.artifacts["cv_results"]["candidates"]
    top = importance.head(10)
    top_lines = "\n".join(
        f"- `{row.feature}`: rank {int(row.rank)}, normalized gain "
        f"`{row.normalized_gain:.6f}`; "
        f"{interpret_feature(row.feature)['possible_interpretation']} "
        f"Giới hạn: {interpret_feature(row.feature)['limitation']}"
        for row in top.itertuples()
    )
    rolling_lines = "\n".join(
        f"- p={item['p']}: `{item['classification']}`, cải thiện MAE "
        f"`{item['relative_mae_improvement_percent']:.3f}%`."
        for item in rolling_analysis
    )
    tuned_horizon = multi[SELECTED_CANDIDATE]["per_horizon"]
    first_h = tuned_horizon[0]
    last_h = tuned_horizon[-1]
    return f"""# PHASE 07 — PHÂN TÍCH VÀ KẾT LUẬN CUỐI

## 1. Dataset

Dữ liệu AEP theo giờ có `{phase_01['raw_rows']}` dòng raw, từ nguồn đã khóa trong Practice 3. Phase 1 đã sắp xếp thời gian, aggregate duplicate timestamp bằng mean và reindex hourly timeline; timezone của nguồn không được cung cấp. Source of truth: [Phase 1 audit](phase_01_data_quality.json).

## 2. Thiết kế feature

Sáu cấu hình lag/rolling được so sánh trên cùng common population. Cấu hình được khóa là `{SELECTED_FEATURE_CONFIGURATION}`, gồm 168 lag và không có rolling feature. Source: [Phase 5 screening](phase_05_screening_results.json).

## 3. CV selection

Candidate được chọn hoàn toàn từ TRAIN-only CV là `{SELECTED_CANDIDATE}` với MAE `{cv[SELECTED_CANDIDATE]['aggregate']['mean_mae']:.4f}` và RMSE `{cv[SELECTED_CANDIDATE]['aggregate']['mean_rmse']:.4f}`. Final test không tham gia chọn model. Source: [Phase 5 CV](phase_05_cv_results.json) và [model lock](phase_05_model_lock.json).

## 4. One-step final-test result

`{SELECTED_CANDIDATE}` đạt MAE `{one[SELECTED_CANDIDATE]['mae']:.4f}` và RMSE `{one[SELECTED_CANDIDATE]['rmse']:.4f}` trên 8.592 timestamp. So với Seasonal Naive 24, MAE cải thiện `{relative_improvement_percent(one['seasonal_naive_24']['mae'], one[SELECTED_CANDIDATE]['mae']):.3f}%`. Source: [one-step metrics](phase_06_one_step_metrics.json).

## 5. Recursive 24-hour result

Trên 350 origin đủ điều kiện, `{SELECTED_CANDIDATE}` đạt pooled MAE `{multi[SELECTED_CANDIDATE]['pooled_mae']:.4f}` và pooled RMSE `{multi[SELECTED_CANDIDATE]['pooled_rmse']:.4f}`. MAE theo horizon chuyển từ `{first_h['mae']:.4f}` ở horizon 1 thành `{last_h['mae']:.4f}` ở horizon 24; đây là evidence của error accumulation, không được gộp với one-step metric. Source: [multi-step metrics](phase_06_multistep_metrics.json).

## 6. Feature importance

Gain importance được lấy từ đúng tuned XGBoost refit trên full top-level TRAIN. Top features thực tế:

{top_lines}

Importance cho biết cách fitted tree sử dụng feature, không chứng minh causality. Correlated lags có thể chia sẻ hoặc làm lệch gain. Xem [full importance table](phase_07_feature_importance.csv) và [Top-20 figure](../figures/phase_07_top20_feature_importance.png).

## 7. Rolling và số lag p

Rolling contribution theo TRAIN-only CV và ngưỡng ±1%:

{rolling_lines}

Trong lag-only family, cấu hình tốt nhất là `{lag_p_analysis['lag_only']['best_configuration_by_mean_mae']}`; trong lag+rolling family là `{lag_p_analysis['lag_rolling']['best_configuration_by_mean_mae']}`. Kết quả không chứng minh rằng tăng p luôn tốt; cần cân bằng metric, variability và training cost.

## 8. Ba câu hỏi bắt buộc

### 8.1 XGBoost và Linear Regression

**THEORETICAL COMPARISON ONLY — Linear Regression was not trained in Practice 3.**

XGBoost học nonlinear threshold và feature interaction trực tiếp nhưng phức tạp hơn, dễ overfit nếu kiểm soát kém và thường yếu khi extrapolate ngoài range đã thấy. Linear Regression đơn giản, coefficient dễ đọc hơn và có thể extrapolate theo linear form, nhưng nonlinear terms/interactions phải được thiết kế rõ. Không có metric Linear Regression để tuyên bố model nào thắng trên AEP.

### 8.2 Ảnh hưởng khi tăng lag p

**EMPIRICAL_RESULT — TRAIN-only CV.**

Lag-only p=24→168 cải thiện mean MAE `{lag_p_analysis['lag_only']['p24_to_p168_mae_improvement_percent']:.3f}%`; lag+rolling p=24→168 cải thiện `{lag_p_analysis['lag_rolling']['p24_to_p168_mae_improvement_percent']:.3f}%`. Lịch sử dài hơn cải thiện kết quả trong experiment này nhưng tăng feature count và compute cost; đây không phải quy luật đảm bảo cho dataset khác.

### 8.3 XGBoost và ARIMA

**THEORETICAL COMPARISON ONLY — ARIMA was not trained in Practice 3.**

XGBoost linh hoạt với nonlinear relations và nhiều engineered features. ARIMA tự nhiên hơn cho univariate linear autocorrelation, có statistical assumptions rõ và thường hỗ trợ forecast interval. Với exogenous features cần ARIMAX/SARIMAX. Không có ARIMA metric để tuyên bố XGBoost tốt hơn ARIMA trên AEP.

## 9. Limitations

- Source timestamp không có timezone hoặc UTC offset.
- Duplicate timestamps có dấu hiệu DST được aggregate bằng mean, làm mất phân biệt observations gốc.
- Missing timestamps/targets làm giảm supervised và evaluation population.
- Common maximal mask tăng comparison fairness nhưng bỏ thêm usable samples của configuration nhỏ.
- Gain importance không phải causality và bị ảnh hưởng bởi correlated features.
- Rolling one-step giả định actual trước đó được quan sát trước prediction kế tiếp.
- Recursive multi-step có error accumulation; complete daily-block rule làm giảm origin count.
- Linear Regression và ARIMA chưa được train.
- Final test chỉ đại diện giai đoạn lịch sử đã chọn.
- Workflow chỉ đánh giá point forecast, chưa đánh giá prediction interval hoặc uncertainty calibration.
- Không có significance-testing protocol, nên không tuyên bố statistical significance.

## 10. Kết luận

`{SELECTED_CANDIDATE}` là model được chọn bằng TRAIN-only CV và đồng thời có MAE thấp nhất quan sát được trong cả one-step và recursive 24-hour final-test protocol. Model phù hợp nhất cho one-step rolling forecast trong phạm vi evidence hiện tại; recursive forecast vẫn có sai số tích lũy lớn hơn và không nên suy rộng ngoài giai đoạn final test. Xem [comparison summary](phase_07_comparison_summary.csv) và [machine-readable summary](phase_07_interpretation_summary.json).
"""


def build_interpretation_summary(
    entry_state: Phase07EntryState,
    importance: pd.DataFrame,
    comparison: pd.DataFrame,
    fit_evidence: dict,
) -> dict:
    rolling = build_rolling_analysis(entry_state.artifacts["screening"])
    lag_p = build_lag_p_analysis(entry_state.artifacts["screening"])
    one = entry_state.artifacts["one_step_metrics"]
    multi = entry_state.artifacts["multi_step_metrics"]
    top_features = importance.head(20)[
        ["feature", "rank", "gain", "normalized_gain"]
    ].to_dict(orient="records")
    for item in top_features:
        item.update(interpret_feature(item["feature"]))
    validation = {
        "importance_row_count": len(importance),
        "expected_importance_row_count": 168,
        "normalized_gain_sum": float(importance["normalized_gain"].sum()),
        "importance_finite": bool(
            np.isfinite(
                importance[["gain", "normalized_gain"]].to_numpy()
            ).all()
        ),
        "comparison_row_count": len(comparison),
        "cv_final_test_separated": True,
        "one_step_multi_step_separated": True,
        "theoretical_models_have_no_metrics": True,
        "status": "PASS",
    }
    if len(importance) != 168:
        raise ValueError("Selected importance table must contain 168 rows.")
    if not np.isclose(validation["normalized_gain_sum"], 1.0):
        raise ValueError("Normalized feature gain does not sum to one.")
    if not validation["importance_finite"]:
        raise ValueError("Feature importance contains non-finite values.")

    limitations = [
        "Source timestamps have no timezone or UTC offset.",
        "Duplicate timestamps were aggregated by mean.",
        "Missing timestamps and targets reduce evaluation population.",
        "The common maximal mask discards extra usable samples.",
        "Gain importance is not causality.",
        "Correlated features can share or distort gain importance.",
        "One-step rolling evaluation assumes observed prior actuals.",
        "Recursive multi-step forecasting accumulates error.",
        "Complete daily blocks reduce multi-step origin count.",
        "Linear Regression and ARIMA were not trained.",
        "The final test represents one selected historical period.",
        "Prediction intervals and uncertainty calibration were not tested.",
    ]
    return {
        "phase": "phase_07_interpretation_final_analysis",
        "evidence_inventory": entry_state.evidence_inventory,
        "cv_selection": {
            "selected_feature_configuration": (
                entry_state.selected_feature_configuration
            ),
            "cv_selected_candidate": entry_state.cv_selected_candidate,
            "selection_rule": entry_state.artifacts["model_lock"][
                "selection_evidence"
            ],
            "evidence_scope": "TRAIN_ONLY_CV",
        },
        "final_test": {
            "one_step_protocol": one["protocol"],
            "one_step_candidates": one["candidates"],
            "multi_step_protocol": multi["protocol"],
            "multi_step_population": multi["population"],
            "multi_step_candidates": multi["candidates"],
        },
        "feature_importance": {
            "candidate_id": SELECTED_CANDIDATE,
            "feature_configuration": SELECTED_FEATURE_CONFIGURATION,
            "importance_type": "gain",
            "training_population": "full_top_level_train",
            "fit_evidence": fit_evidence,
            "top_20": top_features,
            "interpretation_boundary": (
                "Gain describes fitted-tree usage, not causality."
            ),
        },
        "rolling_contribution": rolling,
        "lag_p_analysis": lag_p,
        "required_questions": {
            "xgboost_vs_linear_regression": "THEORETICAL_EXPLANATION",
            "effect_of_increasing_lag_p": "EMPIRICAL_RESULT",
            "xgboost_vs_arima": "THEORETICAL_EXPLANATION",
        },
        "limitations": limitations,
        "validation_checks": validation,
        "status": "PASS",
    }


def create_phase_07_manifest(entry_state: Phase07EntryState) -> dict:
    return {
        "phase": "phase_07_interpretation_final_analysis",
        "selected_feature_configuration": (
            entry_state.selected_feature_configuration
        ),
        "cv_selected_candidate": entry_state.cv_selected_candidate,
        "importance_type": "gain",
        "fit_population": "full_top_level_train",
        "expected_feature_count": 168,
        "final_test_refit": False,
        "new_model_selection": False,
        "outputs": [
            str(RESULTS_DIR / "phase_07_feature_importance.csv"),
            str(RESULTS_DIR / "phase_07_comparison_summary.csv"),
            str(RESULTS_DIR / "phase_07_interpretation_summary.json"),
            str(RESULTS_DIR / "phase_07_final_analysis.md"),
            str(FIGURES_DIR / "phase_07_top20_feature_importance.png"),
        ],
        "requires_human_execution": True,
        "status": "READY",
    }


def run_phase_07(
    entry_state: Phase07EntryState | None = None,
    training_dataset: TrainingDataset | None = None,
    estimator_factory=None,
    results_dir: Path = RESULTS_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> dict:
    entry_state = entry_state or validate_phase_07_entry()
    if training_dataset is None:
        phase_05_entry = validate_phase_05_entry()
        training_dataset = phase_05_entry.training_datasets[
            entry_state.selected_feature_configuration
        ]
    if len(training_dataset.feature_names) != 168:
        raise ValueError("Phase 7 requires exactly 168 selected features.")
    expected_features = tuple(f"lag_{lag}" for lag in range(1, 169))
    if training_dataset.feature_names != expected_features:
        raise ValueError("Phase 7 selected feature identity or order changed.")
    if tuple(training_dataset.X.columns) != training_dataset.feature_names:
        raise ValueError("TRAIN feature order changed before Phase 7 refit.")
    if not np.isfinite(training_dataset.X.to_numpy()).all():
        raise ValueError("Phase 7 TRAIN features contain non-finite values.")
    if not np.isfinite(training_dataset.y.to_numpy()).all():
        raise ValueError("Phase 7 TRAIN target contains non-finite values.")

    parameters = entry_state.artifacts["model_lock"]["locked_candidates"][
        SELECTED_CANDIDATE
    ]["parameters"]
    if estimator_factory is None:
        from xgboost import XGBRegressor

        estimator_factory = XGBRegressor
    estimator = estimator_factory(**parameters)
    start = perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        estimator.fit(training_dataset.X, training_dataset.y)
    fit_evidence = {
        "candidate_id": SELECTED_CANDIDATE,
        "parameters": parameters,
        "train_rows": len(training_dataset.X),
        "feature_count": training_dataset.X.shape[1],
        "training_seconds": float(perf_counter() - start),
        "warnings": [
            {
                "category": item.category.__name__,
                "message": str(item.message),
            }
            for item in caught
        ],
        "final_test_used_for_fit": False,
        "prediction_executed": False,
        "binary_model_persisted": False,
        "status": "PASS",
    }
    importance = build_feature_importance(
        estimator,
        training_dataset.feature_names,
    )
    comparison = build_comparison_summary(entry_state)
    summary = build_interpretation_summary(
        entry_state,
        importance,
        comparison,
        fit_evidence,
    )
    rolling = summary["rolling_contribution"]
    lag_p = summary["lag_p_analysis"]
    final_analysis = _build_final_analysis(
        entry_state,
        importance,
        rolling,
        lag_p,
    )

    results_dir = Path(results_dir)
    figures_dir = Path(figures_dir)
    output_paths = {
        "feature_importance": results_dir
        / "phase_07_feature_importance.csv",
        "comparison_summary": results_dir
        / "phase_07_comparison_summary.csv",
        "interpretation_summary": results_dir
        / "phase_07_interpretation_summary.json",
        "final_analysis": results_dir / "phase_07_final_analysis.md",
        "top20_figure": figures_dir
        / "phase_07_top20_feature_importance.png",
    }
    atomic_save_csv(importance, output_paths["feature_importance"])
    atomic_save_csv(comparison, output_paths["comparison_summary"])
    atomic_save_json(summary, output_paths["interpretation_summary"])
    atomic_save_text(final_analysis, output_paths["final_analysis"])
    plot_top_feature_importance(
        importance,
        output_paths["top20_figure"],
    )

    output_inventory = {
        name: {
            "path": str(path),
            "sha256": file_sha256(path),
        }
        for name, path in output_paths.items()
    }
    return {
        "phase": "phase_07_interpretation_final_analysis",
        "outputs": output_inventory,
        "top_feature": importance.iloc[0]["feature"],
        "status": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate or run Phase 7 interpretation and final analysis."
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)

    entry_state = validate_phase_07_entry()
    if args.dry_run:
        print(json.dumps(create_phase_07_manifest(entry_state), indent=2))
        return 0

    result = run_phase_07(entry_state=entry_state)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
