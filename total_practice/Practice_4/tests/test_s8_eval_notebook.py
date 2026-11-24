from __future__ import annotations

import json

import pandas as pd

from practice_4.runtime import PRACTICE_ROOT, read_file_map


def test_s8_walk_forward_metrics_dm_and_executed_notebook():
    metrics_path = PRACTICE_ROOT / "outputs/tables/test_metrics.csv"
    preds_path = PRACTICE_ROOT / "outputs/predictions/test_predictions.csv"
    dm_path = PRACTICE_ROOT / "outputs/tables/dm_test.csv"
    manifest_path = PRACTICE_ROOT / "runs/v2/s8_eval/artifacts/evaluation_manifest.json"
    nb_path = PRACTICE_ROOT / "notebooks/practice_4.ipynb"

    for p in (metrics_path, preds_path, dm_path, manifest_path, nb_path):
        assert p.exists(), f"Missing S8 artifact: {p}"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    c = manifest["counts"]
    assert c["n_considered"] == c["n_scored"] + c["n_missing_excluded"] + c["n_input_excluded"]
    assert c["n_scored"] > 3500

    preds = pd.read_csv(preds_path)
    counts_by_model = preds.groupby("model").size()
    assert counts_by_model.eq(c["n_scored"]).all()
    first_model = counts_by_model.index[0]
    ref_keys = preds.loc[preds["model"] == first_model, ["origin", "target_timestamp", "y_true"]].reset_index(drop=True)
    for m in counts_by_model.index[1:]:
        cur = preds.loc[preds["model"] == m, ["origin", "target_timestamp", "y_true"]].reset_index(drop=True)
        pd.testing.assert_frame_equal(ref_keys, cur)

    tm = pd.read_csv(metrics_path).set_index("model")
    assert tm.loc["XGB_best", "rmse_kw"] < tm.loc["persistence", "rmse_kw"]
    assert tm.loc["LSTM_best", "rmse_kw"] < tm.loc["persistence", "rmse_kw"]
    assert tm.loc["VAR", "rmse_kw"] < tm.loc["persistence", "rmse_kw"]

    dm = pd.read_csv(dm_path)
    assert len(dm) >= 4
    assert dm["p_value"].between(0.0, 1.0).all()

    for fig in ("actual_vs_predicted.png", "residual_distributions.png", "grouped_error_profiles.png"):
        assert (PRACTICE_ROOT / "outputs/figures" / fig).exists()

    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    code_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "code"]
    assert len(code_cells) >= 6
    for cell in code_cells:
        assert cell.get("execution_count") is not None, f"Un-executed code cell: {cell.get('id')}"
        for out in cell.get("outputs", []):
            assert out.get("output_type") != "error", f"Notebook execution error in cell {cell.get('id')}: {out}"

    assert not (PRACTICE_ROOT / "notebooks/practice_4_end_to_end.ipynb").exists()
    fmap = {r["path"]: r for r in read_file_map()}
    assert fmap["notebooks/practice_4.ipynb"]["existence"] == "EXISTING"
    assert fmap["docs/results/final_report.md"]["existence"] == "EXISTING"
