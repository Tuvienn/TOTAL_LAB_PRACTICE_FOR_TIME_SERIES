from typing import Any, List, Tuple
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler


def _get_scaler(scaler_type: str = "standard") -> Any:
    if scaler_type == "standard":
        return StandardScaler()
    elif scaler_type == "minmax":
        return MinMaxScaler()
    else:
        raise ValueError(f"Unsupported scaler_type '{scaler_type}'. Choose 'standard' or 'minmax'.")


def scale_with_leakage(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str],
    scaler_type: str = "standard",
) -> Tuple[pd.DataFrame, pd.DataFrame, Any]:
    """Pipeline A (SAI PHẠM - LEAKAGE): Fit scaler trên toàn bộ dữ liệu trước khi chia hoặc dùng thông tin test."""
    scaler = _get_scaler(scaler_type)
    combined = pd.concat([train_df[feature_cols], test_df[feature_cols]], axis=0)
    scaler.fit(combined)

    train_scaled = train_df.copy()
    test_scaled = test_df.copy()

    train_scaled[feature_cols] = scaler.transform(train_df[feature_cols])
    test_scaled[feature_cols] = scaler.transform(test_df[feature_cols])

    return train_scaled, test_scaled, scaler


def scale_without_leakage(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str],
    scaler_type: str = "standard",
) -> Tuple[pd.DataFrame, pd.DataFrame, Any]:
    """Pipeline B (CHUẨN - CORRECT): Fit scaler CHỈ trên tập train, sau đó dùng tham số đã học để transform test."""
    scaler = _get_scaler(scaler_type)
    scaler.fit(train_df[feature_cols])

    train_scaled = train_df.copy()
    test_scaled = test_df.copy()

    train_scaled[feature_cols] = scaler.transform(train_df[feature_cols])
    test_scaled[feature_cols] = scaler.transform(test_df[feature_cols])

    return train_scaled, test_scaled, scaler
