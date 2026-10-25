# Nhiệm vụ: Tải dữ liệu chuỗi thời gian, kiểm tra timestamp, tần suất và đánh giá chất lượng dữ liệu ban đầu (E1).
from pathlib import Path
from typing import Any, Optional
import numpy as np
import pandas as pd


def load_time_series_data(
    file_path: str,
    timestamp_col: str = "date",
    target_col: str = "value",
    date_format: Optional[str] = None,
) -> pd.DataFrame:
    """Tải dữ liệu từ tệp tin, phân tích định dạng timestamp và sắp xếp thứ tự thời gian.
    
    Hỗ trợ cả trường hợp dữ liệu có cột ngày chuẩn hoặc dữ liệu gốc dạng fractional year.
    
    Args:
        file_path: Đường dẫn tệp CSV dữ liệu.
        timestamp_col: Tên cột thời gian (mặc định: 'date').
        target_col: Tên cột giá trị chuỗi thời gian cần dự báo (mặc định: 'value').
        date_format: Định dạng ngày giờ nếu cần thiết.
        
    Returns:
        DataFrame đã được sắp xếp tăng dần theo thời gian với DatetimeIndex.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {file_path}")

    raw = pd.read_csv(path)

    # Xử lý trường hợp AirPassengers gốc từ R (có cột 'time' là fractional year: 1949, 1949.083...)
    if timestamp_col not in raw.columns and "time" in raw.columns:
        if len(raw) == 144 and np.isclose(raw["time"].iloc[0], 1949.0):
            dates = pd.date_range("1949-01-01", periods=144, freq="MS")
            raw[timestamp_col] = dates
        else:
            # Chuyển đổi tổng quát từ decimal year sang datetime
            years = raw["time"].astype(int)
            months = np.round((raw["time"] - years) * 12).astype(int) + 1
            raw[timestamp_col] = pd.to_datetime(
                years.astype(str) + "-" + months.astype(str).str.zfill(2) + "-01"
            )
    elif timestamp_col in raw.columns:
        raw[timestamp_col] = pd.to_datetime(raw[timestamp_col], format=date_format)
    else:
        raise KeyError(f"Timestamp column '{timestamp_col}' not found in dataset columns: {raw.columns.tolist()}")

    if target_col not in raw.columns:
        # Nếu target_col không tìm thấy nhưng có 'passengers_thousands' hoặc 'value'
        numeric_candidates = [c for c in raw.columns if c not in [timestamp_col, "rownames", "time"]]
        if len(numeric_candidates) == 1:
            raw[target_col] = raw[numeric_candidates[0]]
        else:
            raise KeyError(f"Target column '{target_col}' not found in dataset columns: {raw.columns.tolist()}")

    df = raw[[timestamp_col, target_col]].copy()
    df[target_col] = pd.to_numeric(df[target_col], errors="raise").astype(float)
    df = df.sort_values(by=timestamp_col).reset_index(drop=True)
    df.index = pd.DatetimeIndex(df[timestamp_col], freq="MS")
    return df


def validate_time_index(
    df: pd.DataFrame,
    timestamp_col: str = "date",
    expected_freq: Optional[str] = "MS",
) -> dict[str, Any]:
    """Kiểm tra tính hợp lệ của trục thời gian: trùng lặp, tính liên tục và khoảng cách thời gian."""
    series_ts = df[timestamp_col] if timestamp_col in df.columns else pd.Series(df.index)
    has_duplicates = bool(series_ts.duplicated().any())
    is_monotonic = bool(series_ts.is_monotonic_increasing)
    total_periods = int(len(series_ts))
    start_date = str(series_ts.min())
    end_date = str(series_ts.max())

    inferred_freq = pd.infer_freq(pd.DatetimeIndex(series_ts))
    is_regular = inferred_freq is not None

    missing_timestamps = 0
    if expected_freq is not None and len(series_ts) > 1:
        full_range = pd.date_range(series_ts.min(), series_ts.max(), freq=expected_freq)
        missing_timestamps = int(len(full_range) - len(series_ts))

    return {
        "total_periods": total_periods,
        "start_date": start_date,
        "end_date": end_date,
        "has_duplicates": has_duplicates,
        "is_monotonic_increasing": is_monotonic,
        "inferred_freq": str(inferred_freq),
        "expected_freq": str(expected_freq),
        "is_regular": is_regular,
        "missing_timestamps": missing_timestamps,
    }


def check_data_quality(
    df: pd.DataFrame,
    target_col: str = "value",
) -> dict[str, Any]:
    """Đánh giá chất lượng dữ liệu: số lượng missing values, outliers sơ bộ, min, max, mean, std."""
    values = df[target_col].to_numpy(dtype=float)
    total_rows = int(len(values))
    missing_values = int(np.isnan(values).sum())

    q25, q75 = np.percentile(values, [25, 75])
    iqr = q75 - q25
    lower_bound = q25 - 1.5 * iqr
    upper_bound = q75 + 1.5 * iqr
    outlier_count = int(np.sum((values < lower_bound) | (values > upper_bound)))

    return {
        "total_rows": total_rows,
        "missing_values": missing_values,
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=1)),
        "q25": float(q25),
        "median": float(np.median(values)),
        "q75": float(q75),
        "iqr": float(iqr),
        "outlier_count": outlier_count,
    }
