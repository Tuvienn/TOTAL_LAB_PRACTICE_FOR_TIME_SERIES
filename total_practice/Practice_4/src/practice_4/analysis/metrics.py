from math import isfinite, sqrt


def calculate_metrics(truth, forecast, missing_excluded=0, input_excluded=0):
    y, pred = list(truth), list(forecast)
    if len(y) != len(pred) or not y:
        raise ValueError("Scored pairs must be nonempty and aligned")
    if any(type(n) is not int or n < 0 for n in (missing_excluded, input_excluded)):
        raise ValueError("Invalid exclusion count")
    if any(not isfinite(v) for v in y + pred):
        raise ValueError("Non-finite scored value")
    errors = [abs(a - b) for a, b in zip(y, pred)]
    nonzero = [e / abs(a) for a, e in zip(y, errors) if a != 0]
    n = len(y)
    result = {
        "mae_kw": sum(errors) / n,
        "rmse_kw": sqrt(sum(e * e for e in errors) / n),
        "mape_percent": 100 * sum(nonzero) / len(nonzero) if nonzero else None,
        "mape_null_reason": None if nonzero else "all scored truths are zero",
        "n_considered": n + missing_excluded + input_excluded,
        "n_scored": n,
        "n_zero_excluded": n - len(nonzero),
        "n_missing_excluded": missing_excluded,
        "n_input_excluded": input_excluded,
    }
    if any(not isfinite(result[k]) for k in ("mae_kw", "rmse_kw")) or (
        result["mape_percent"] is not None and not isfinite(result["mape_percent"])
    ):
        raise ValueError("Non-finite metric")
    return result
