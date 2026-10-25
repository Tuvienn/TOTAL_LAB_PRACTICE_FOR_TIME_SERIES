from typing import Optional, Tuple
import numpy as np
import pandas as pd


def temporal_train_test_split(
    df: pd.DataFrame,
    test_ratio: float = 0.2,
    timestamp_col: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Chia dữ liệu theo mốc thời gian (Temporal Split) bảo toàn nguyên vẹn thứ tự thời gian.
    
    Toàn bộ quan sát quá khứ nằm ở tập Train và quan sát tương lai nằm ở tập Test.
    
    Args:
        df: DataFrame đầu vào.
        test_ratio: Tỷ lệ tập test (mặc định 0.2).
        timestamp_col: Cột thời gian dùng để sắp xếp/xác nhận thứ tự.
        
    Returns:
        Tuple gồm (train_df, test_df).
    """
    if not 0.0 < test_ratio < 1.0:
        raise ValueError(f"test_ratio must be strictly between 0 and 1, got {test_ratio}")

    sorted_df = df.copy()
    if timestamp_col is not None and timestamp_col in sorted_df.columns:
        sorted_df = sorted_df.sort_values(by=timestamp_col)
    elif isinstance(sorted_df.index, pd.DatetimeIndex):
        sorted_df = sorted_df.sort_index()

    n = len(sorted_df)
    split_idx = int(n * (1.0 - test_ratio))
    if split_idx <= 0 or split_idx >= n:
        raise ValueError(f"Invalid split index {split_idx} for dataset length {n}")

    train_df = sorted_df.iloc[:split_idx].copy()
    test_df = sorted_df.iloc[split_idx:].copy()
    return train_df, test_df


def random_train_test_split(
    df: pd.DataFrame,
    test_ratio: float = 0.2,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Chia dữ liệu ngẫu nhiên (Random Split - SAI LẦM trong Time Series) dùng để minh họa rủi ro rò rỉ.
    
    Args:
        df: DataFrame đầu vào.
        test_ratio: Tỷ lệ tập test.
        random_state: Seed để tái lập kết quả xáo trộn ngẫu nhiên.
        
    Returns:
        Tuple gồm (train_df, test_df) bị xáo trộn vị trí thời gian.
    """
    if not 0.0 < test_ratio < 1.0:
        raise ValueError(f"test_ratio must be strictly between 0 and 1, got {test_ratio}")

    rng = np.random.RandomState(random_state)
    n = len(df)
    perm = rng.permutation(n)
    split_idx = int(n * (1.0 - test_ratio))

    train_indices = perm[:split_idx]
    test_indices = perm[split_idx:]

    train_df = df.iloc[train_indices].copy()
    test_df = df.iloc[test_indices].copy()
    return train_df, test_df
