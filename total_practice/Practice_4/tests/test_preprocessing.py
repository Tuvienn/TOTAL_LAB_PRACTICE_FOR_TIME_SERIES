import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from practice_4.data.preprocessing import COLUMNS, CausalState, causal_load, fit_state, inverse_load, load_prefix, physical_flags, transform, verify_var_block


def frame(loads):
    n = len(loads)
    return pd.DataFrame({'timestamp_utc': pd.date_range('2020-01-01', periods=n, freq='h', tz='UTC'), 'load': loads, 'temp': np.arange(n) + 280., 'humidity': np.arange(n) + 40., 'wind_speed': np.arange(n) + 1., 'load_observed': pd.Series(loads).notna()})


def test_locf_leading_single_multigap_and_cross_split():
    state = CausalState()
    a = causal_load([np.nan, 10, np.nan, 20, np.nan], state)
    b = causal_load([np.nan, np.nan, 30], state)
    np.testing.assert_equal(np.r_[a, b], [np.nan, 10, 10, 20, 20, np.nan, np.nan, 30])


def test_causality_truth_and_streaming():
    f = frame([2., np.nan, np.nan, 4., 5., 6., 7., 8.])
    original = f.copy(deep=True)
    fitted = fit_state(f, 4, {})
    state = CausalState()
    first = transform(f.iloc[:4], fitted, state)
    later = transform(f.iloc[4:], fitted, state)
    changed = f.copy()
    changed.loc[6:, 'load'] = 1e9
    result = transform(changed, fitted, CausalState())
    pd.testing.assert_frame_equal(first, result.iloc[:4])
    pd.testing.assert_frame_equal(f, original)
    pd.testing.assert_series_equal(pd.concat([first, later]).load, f.load)
    pd.testing.assert_series_equal(pd.concat([first, later]).load_observed, f.load_observed)
    assert np.isnan(first.load_input_scaled.iloc[2])
    with pytest.raises(ValueError):
        transform(f.iloc[5:], fitted, state)


def test_fit_train_only_nonclipping_serialization_and_inverse():
    f = frame([10., 11., 12., 13., 14., 15., 16., 17.])
    state = fit_state(f, 5, {'canonical_sha256': 'a' * 64})
    changed = f.copy()
    changed.loc[5:, ['load', 'temp']] = 50000.
    assert fit_state(changed, 5, {'canonical_sha256': 'a' * 64}) == state
    reloaded = json.loads(json.dumps(state, allow_nan=False))
    result = transform(changed, reloaded, CausalState())
    assert result.load.iloc[-1] == 50000. and result.load_statistical_extreme.iloc[-1]
    assert np.max(np.abs(inverse_load(result.load_input_scaled, reloaded) - result.load_input)) <= 1e-9
    assert state['fit_count'] == 5 and state['fit_end_row'] == 4


def test_zero_scale_and_strict_bounds_and_physical_flags():
    f = frame([10.] * 8)
    f[['temp', 'humidity', 'wind_speed']] = [290., 50., 3.]
    state = fit_state(f, 5, {})
    assert state['scale'] == [1., 1., 1., 1.]
    result = transform(f, state, CausalState())
    assert not result.filter(like='statistical_extreme').to_numpy().any()
    f.loc[7, 'load'] = 11.
    assert transform(f, state, CausalState()).load_statistical_extreme.iloc[7]
    f.loc[0, ['load', 'temp', 'humidity', 'wind_speed']] = [-1., 0., 101., -1.]
    assert physical_flags(f).iloc[0].all()
    with pytest.raises(ValueError):
        transform(f, state, CausalState())


def test_prefix_does_not_read_following_record(monkeypatch):
    f = frame([1., 2., 3.])
    csv_text = f.to_csv(index=False).encode() + b'FORBIDDEN TEST ROW\n'
    class Guard(io.BytesIO):
        def readline(self, *args):
            if self.tell() >= len(csv_text) - len(b'FORBIDDEN TEST ROW\n'):
                raise AssertionError('test row accessed')
            return super().readline(*args)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    monkeypatch.setattr(Path, 'open', lambda *args, **kwargs: Guard(csv_text))
    result = load_prefix(Path('x'), 3, f.timestamp_utc.iloc[0].isoformat(), f.timestamp_utc.iloc[-1].isoformat())
    assert len(result) == 3


def test_prefix_rejects_schema_and_timeline(monkeypatch):
    f = frame([1., 2., 3.])
    class Context(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *args): return False
    bad = f.copy()
    bad.loc[1, 'timestamp_utc'] = bad.loc[0, 'timestamp_utc']
    monkeypatch.setattr(Path, 'open', lambda *args, **kwargs: Context(bad.to_csv(index=False).encode()))
    with pytest.raises(ValueError):
        load_prefix(Path('x'), 3, f.timestamp_utc.iloc[0].isoformat(), f.timestamp_utc.iloc[-1].isoformat())
    monkeypatch.setattr(Path, 'open', lambda *args, **kwargs: Context(b'bad,header\n'))
    with pytest.raises(ValueError):
        load_prefix(Path('x'), 3, f.timestamp_utc.iloc[0].isoformat(), f.timestamp_utc.iloc[-1].isoformat())


def test_window_exclusion_precedence():
    inputs = [1., np.nan, 2., 3., 4.]
    targets = [np.nan, 3., 4.]
    missing = invalid = scored = 0
    for i, target in enumerate(targets):
        if np.isnan(target): missing += 1
        elif not np.isfinite(inputs[i:i + 2]).all(): invalid += 1
        else: scored += 1
    assert (missing, invalid, scored) == (1, 1, 1)


def test_real_cutoff_guard(monkeypatch):
    n = 29803
    f = pd.DataFrame({'timestamp_utc': pd.date_range('2014-12-31 23:00', periods=n, freq='h', tz='UTC'), 'load': 10., 'temp': 290., 'humidity': 50., 'wind_speed': 3., 'load_observed': True})
    prefix = f.to_csv(index=False).encode()
    class Guard(io.BytesIO):
        def readline(self, *args):
            if self.tell() >= len(prefix):
                raise AssertionError('row 29803 accessed')
            return super().readline(*args)
        def __enter__(self): return self
        def __exit__(self, *args): return False
    monkeypatch.setattr(Path, 'open', lambda *args, **kwargs: Guard(prefix + b'test row forbidden\n'))
    out = load_prefix(Path('x'), n, f.timestamp_utc.iloc[0].isoformat(), f.timestamp_utc.iloc[-1].isoformat())
    assert len(out) == n


def test_var_block_boundaries_and_exclusion_count():
    n = 24544
    f = pd.DataFrame({'timestamp_utc': pd.date_range('2014-12-31 23:00', periods=n, freq='h', tz='UTC'), 'load_observed': np.ones(n, dtype=bool)})
    f.loc[:31, 'load_observed'] = False
    block = {'start_utc': '2016-09-28T08:00:00+00:00', 'end_utc': '2017-10-19T14:00:00+00:00', 'rows': 9271, 'earlier_observed_excluded': 15241}
    verify_var_block(f, block)
    f.loc[n - 1, 'load_observed'] = False
    with pytest.raises(ValueError):
        verify_var_block(f, block)
