import math
import pytest
from practice_4.analysis.metrics import calculate_metrics, select_validation


def test_metrics_and_counts():
    m = calculate_metrics([1, 2], [2, 0], 2, 3)
    assert m["mae_mw"] == 1.5 and m["rmse_mw"] == pytest.approx(math.sqrt(2.5)) and m["mape_percent"] == 100
    assert (m["n_considered"], m["n_missing_excluded"], m["n_input_excluded"], m["n_scored"]) == (7, 2, 3, 2)
    assert calculate_metrics([0, 2], [1, 0])["n_zero_excluded"] == 1
    zero = calculate_metrics([0], [1])
    assert zero["mape_percent"] is None and zero["mape_null_reason"]
    for y, p in [([], []), ([1], [float('nan')]), ([1], [])]:
        with pytest.raises(ValueError): calculate_metrics(y, p)


def test_selection_uses_global_minimum_and_ties():
    def c(model, rmse, mae, complexity, trial_id):
        return dict(model=model, rmse_mw=rmse, mae_mw=mae, complexity=complexity, trial_id=trial_id)
    choices = [c('LSTM', 1, 1, 3, 'c'), c('VAR', 1.0000008, 0.5, 9, 'b'), c('persistence', 1.0000015, 0, 1, 'a')]
    assert select_validation(choices)['model'] == 'VAR'
    choices = [c('VAR', 1, 1, 1, 'x'), c('persistence', 1, 1, 5, 'b'), c('persistence', 1, 1, 2, 'b'), c('persistence', 1, 1, 2, 'a')]
    assert select_validation(choices)['trial_id'] == 'a'
