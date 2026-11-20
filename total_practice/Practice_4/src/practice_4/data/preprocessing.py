from __future__ import annotations

import csv
import io
import itertools
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.preprocessing import StandardScaler

COLUMNS = ['timestamp_utc', 'load', 'temp', 'humidity', 'wind_speed', 'load_observed']
VARIABLES = ['load', 'temp', 'humidity', 'wind_speed']
FEATURES = ['load_input', 'temp', 'humidity', 'wind_speed']


def load_prefix(path: Path, count: int, start: str, end: str) -> pd.DataFrame:
    with path.open('rb', buffering=0) as stream:
        def lines():
            for _ in range(count + 1):
                line = stream.readline()
                if not line:
                    break
                yield line.decode('utf-8')
        reader = csv.reader(lines())
        if next(reader, None) != COLUMNS:
            raise ValueError('Unexpected canonical schema')
        rows = list(reader)
    if len(rows) != count or any(len(row) != len(COLUMNS) for row in rows):
        raise ValueError('Incomplete or invalid canonical prefix')
    frame = pd.DataFrame(rows, columns=COLUMNS)
    parsed = [pd.Timestamp(value) for value in frame.timestamp_utc]
    if any(pd.isna(t) or t.tzinfo is None or t.utcoffset().total_seconds() != 0 for t in parsed):
        raise ValueError('Timestamp is not UTC')
    frame['timestamp_utc'] = pd.DatetimeIndex(parsed)
    expected = pd.date_range(start, periods=count, freq='h')
    if not pd.DatetimeIndex(frame.timestamp_utc).equals(expected) or frame.timestamp_utc.iloc[-1].isoformat() != end:
        raise ValueError('Invalid hourly timeline')
    for name in VARIABLES:
        frame[name] = pd.to_numeric(frame[name], errors='raise')
    if not frame.load_observed.isin(['True', 'False']).all():
        raise ValueError('Invalid observed mask')
    frame['load_observed'] = frame.load_observed.eq('True')
    validate_frame(frame)
    return frame


def validate_frame(frame: pd.DataFrame) -> None:
    if list(frame.columns) != COLUMNS or not frame.load_observed.equals(frame.load.notna()):
        raise ValueError('Schema or observed mask mismatch')
    if not np.isfinite(frame[VARIABLES].drop(columns='load').to_numpy()).all():
        raise ValueError('Missing or nonfinite weather')
    if not np.isfinite(frame.load.dropna().to_numpy()).all():
        raise ValueError('Nonfinite load')
    if ((frame.temp <= 0) | (frame.humidity < 0) | (frame.humidity > 100) | (frame.wind_speed < 0)).any():
        raise ValueError('Physically invalid weather requires Human policy')


@dataclass
class CausalState:
    last_load: float = float('nan')
    missing_run: int = 0
    last_timestamp: str | None = None


def physical_flags(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({'load_physical_invalid': frame.load < 0,
                         'temp_physical_invalid': frame.temp <= 0,
                         'humidity_physical_invalid': (frame.humidity < 0) | (frame.humidity > 100),
                         'wind_speed_physical_invalid': frame.wind_speed < 0}, index=frame.index)


def causal_load(values, state: CausalState) -> np.ndarray:
    result = []
    for value in values:
        if pd.isna(value):
            state.missing_run += 1
            result.append(state.last_load if state.missing_run == 1 else np.nan)
        else:
            state.last_load = float(value)
            state.missing_run = 0
            result.append(state.last_load)
    return np.asarray(result, dtype=np.float64)


def fit_state(frame: pd.DataFrame, train_count: int, provenance: dict) -> dict:
    if not 0 < train_count <= len(frame):
        raise ValueError('Invalid train count')
    train = frame.iloc[:train_count].copy()
    train['load_input'] = causal_load(train.load, CausalState())
    values = train[FEATURES].to_numpy(dtype=np.float64)
    valid = np.isfinite(values).all(axis=1)
    if not valid.any():
        raise ValueError('No finite train rows')
    scaler = StandardScaler().fit(values[valid])
    bounds = {}
    for name in VARIABLES:
        sample = train[name].dropna().to_numpy(dtype=np.float64)
        if not len(sample):
            raise ValueError('Empty percentile sample')
        lo, hi = np.percentile(sample, [0.5, 99.5], method='linear')
        bounds[name] = {'lower': float(lo), 'upper': float(hi), 'count': len(sample)}
    return {'schema_version': '1', 'feature_order': FEATURES, 'mean': scaler.mean_.tolist(),
            'std': np.sqrt(scaler.var_).tolist(), 'scale': scaler.scale_.tolist(),
            'variance': scaler.var_.tolist(), 'fit_count': int(valid.sum()),
            'fit_start_row': 0, 'fit_end_row': train_count - 1,
            'percentiles': [0.5, 99.5], 'percentile_method': 'linear', 'bounds': bounds,
            'locf_max_gap': 1, 'scikit_learn_version': sklearn.__version__,
            'numpy_version': np.__version__, 'pandas_version': pd.__version__, 'provenance': provenance}


def transform(frame: pd.DataFrame, fitted: dict, state: CausalState) -> pd.DataFrame:
    validate_frame(frame)
    ts = pd.DatetimeIndex(frame.timestamp_utc)
    if len(ts):
        if ts.tz is None or any(t.utcoffset().total_seconds() != 0 for t in ts):
            raise ValueError('Expected UTC timestamps')
        if len(ts) > 1 and not ((ts[1:] - ts[:-1]) == pd.Timedelta(hours=1)).all():
            raise ValueError('Noncontiguous timestamps')
        if state.last_timestamp is not None and ts[0] != pd.Timestamp(state.last_timestamp) + pd.Timedelta(hours=1):
            raise ValueError('Noncontiguous streaming state')
    result = frame.copy(deep=True)
    result['load_input'] = causal_load(frame.load, state)
    for name, values in physical_flags(frame).items():
        result[name] = values
    for name in VARIABLES:
        bound = fitted['bounds'][name]
        result[name + '_statistical_extreme'] = (frame[name] < bound['lower']) | (frame[name] > bound['upper'])
    values = result[FEATURES].to_numpy(dtype=np.float64)
    scaled = (values - np.asarray(fitted['mean'])) / np.asarray(fitted['scale'])
    for i, name in enumerate(FEATURES):
        result[name + '_scaled'] = scaled[:, i]
    if len(ts):
        state.last_timestamp = ts[-1].isoformat()
    return result


def inverse_load(values, fitted: dict):
    return np.asarray(values, dtype=np.float64) * fitted['scale'][0] + fitted['mean'][0]


def verify_var_block(frame: pd.DataFrame, block: dict) -> None:
    train = frame.iloc[:24544]
    selected = train[(train.timestamp_utc >= pd.Timestamp(block['start_utc'])) & (train.timestamp_utc <= pd.Timestamp(block['end_utc']))]
    earlier = train[train.timestamp_utc < pd.Timestamp(block['start_utc'])]
    if len(selected) != block['rows'] or not selected.load_observed.all() or int(earlier.load_observed.sum()) != block['earlier_observed_excluded']:
        raise ValueError('VAR domain mismatch')
