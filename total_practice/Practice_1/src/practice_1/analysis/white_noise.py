import numpy as np
import pandas as pd


def generate_white_noise(
    size: int = 1000,
    seed: int = 42,
    mean: float = 0.0,
    standard_deviation: float = 1.0,
) -> pd.Series:
    if isinstance(size, bool) or not isinstance(size, (int, np.integer)):
        raise TypeError("size must be an integer")
    if size <= 0:
        raise ValueError("size must be positive")
    if not np.isfinite(mean):
        raise ValueError("mean must be finite")
    if not np.isfinite(standard_deviation) or standard_deviation <= 0:
        raise ValueError("standard_deviation must be finite and positive")

    rng = np.random.default_rng(seed)
    values = rng.normal(
        loc=float(mean),
        scale=float(standard_deviation),
        size=int(size),
    )
    return pd.Series(values, name="white_noise", dtype=float)
