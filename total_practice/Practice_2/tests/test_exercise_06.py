from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

from practice_2.analysis.forecasting import compute_residual_diagnostics


ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def e06_diagnostics():
    data = pd.read_csv(ROOT / "datasets" / "raw" / "airline-passengers.csv")
    data["Month"] = pd.to_datetime(data["Month"], format="%Y-%m", errors="raise")
    series = data.set_index("Month")["Passengers"].astype(float)
    series.index = pd.DatetimeIndex(series.index, freq="MS", name="Month")
    train = np.log(series.iloc[: int(len(series) * 0.8)])

    fitted = {
        "ARIMA": ARIMA(train, order=(1, 1, 1), trend="n").fit(),
        "SARIMA": SARIMAX(
            train,
            order=(1, 1, 1),
            seasonal_order=(0, 1, 1, 12),
            trend="n",
        ).fit(disp=False),
    }
    parameters_before = {
        model_name: model.params.copy()
        for model_name, model in fitted.items()
    }
    residuals, diagnostics = compute_residual_diagnostics(
        fitted,
        lags=(12, 24),
        alpha=0.05,
    )
    return fitted, parameters_before, residuals, diagnostics


def test_e06_residual_diagnostics_apply_model_specific_burn_in(e06_diagnostics):
    fitted, _, residuals, diagnostics = e06_diagnostics

    arima_rows = diagnostics.loc[diagnostics["model"] == "ARIMA"]
    sarima_rows = diagnostics.loc[diagnostics["model"] == "SARIMA"]

    assert (arima_rows["burn_in"] == 1).all()
    assert (sarima_rows["burn_in"] == 13).all()
    assert (arima_rows["residual_observations"] == 114).all()
    assert (sarima_rows["residual_observations"] == 102).all()
    assert residuals["ARIMA"].index[0] == fitted["ARIMA"].resid.index[1]
    assert residuals["SARIMA"].index[0] == fitted["SARIMA"].resid.index[13]
    assert np.isclose(residuals["ARIMA"].iloc[0], fitted["ARIMA"].resid.iloc[1])
    assert np.isclose(residuals["SARIMA"].iloc[0], fitted["SARIMA"].resid.iloc[13])


def test_e06_residual_diagnostics_include_seasonal_model_df(e06_diagnostics):
    _, _, _, diagnostics = e06_diagnostics
    arima_rows = diagnostics.loc[diagnostics["model"] == "ARIMA"]
    sarima_rows = diagnostics.loc[diagnostics["model"] == "SARIMA"]

    assert (arima_rows["model_df"] == 2).all()
    assert (sarima_rows["model_df"] == 3).all()
    assert set(diagnostics["lag"]) == {12, 24}
    assert (diagnostics["alpha"] == 0.05).all()


def test_e06_corrected_ljung_box_decisions(e06_diagnostics):
    _, _, _, diagnostics = e06_diagnostics
    arima_rows = diagnostics.loc[diagnostics["model"] == "ARIMA"]
    sarima_rows = diagnostics.loc[diagnostics["model"] == "SARIMA"]

    assert arima_rows["reject_no_autocorrelation"].all()
    assert not arima_rows["white_noise_supported"].any()
    assert not sarima_rows["reject_no_autocorrelation"].any()
    assert sarima_rows["white_noise_supported"].all()
    assert np.all(arima_rows["lb_pvalue"].to_numpy() < 1e-10)
    assert np.all(sarima_rows["lb_pvalue"].to_numpy() > 0.05)


def test_e06_diagnostics_do_not_mutate_fitted_parameters(e06_diagnostics):
    fitted, parameters_before, _, _ = e06_diagnostics

    for model_name, model in fitted.items():
        np.testing.assert_allclose(model.params, parameters_before[model_name])
