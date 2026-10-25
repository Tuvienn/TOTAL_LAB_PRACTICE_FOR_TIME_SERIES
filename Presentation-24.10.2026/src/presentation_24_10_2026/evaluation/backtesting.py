# Nhiệm vụ: Triển khai quy trình kiểm chứng lịch sử đa mốc: Expanding Window Backtesting và Rolling Window Backtesting (E5).
from typing import Any, Callable, Dict, List
import numpy as np
import pandas as pd


def expanding_window_backtest(
    df: pd.DataFrame,
    initial_train_size: int,
    horizon: int,
    step_size: int,
    model_trainer_fn: Callable[[pd.DataFrame, pd.DataFrame, int], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Thực hiện Expanding Window Backtesting: Kích thước train mở rộng dần theo thời gian.
    
    Quy tắc an toàn: Mỗi fold fit riêng scaler/model trên tập train của fold đó, không dùng dữ liệu tương lai.
    """
    n = len(df)
    results: List[Dict[str, Any]] = []
    fold_idx = 1

    train_end = initial_train_size
    while train_end + horizon <= n:
        train_fold = df.iloc[:train_end].copy()
        val_fold = df.iloc[train_end : train_end + horizon].copy()

        fold_meta = {
            "fold": fold_idx,
            "strategy": "expanding",
            "train_start": str(train_fold.index[0]),
            "train_end": str(train_fold.index[-1]),
            "val_start": str(val_fold.index[0]),
            "val_end": str(val_fold.index[-1]),
            "train_size": int(len(train_fold)),
            "val_size": int(len(val_fold)),
        }

        eval_res = model_trainer_fn(train_fold, val_fold, horizon)
        fold_meta.update(eval_res)
        results.append(fold_meta)

        train_end += step_size
        fold_idx += 1

    return results


def rolling_window_backtest(
    df: pd.DataFrame,
    window_size: int,
    horizon: int,
    step_size: int,
    model_trainer_fn: Callable[[pd.DataFrame, pd.DataFrame, int], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Thực hiện Rolling Window Backtesting: Kích thước tập train cố định, loại bỏ dữ liệu cũ nhất khi dịch về phía trước."""
    n = len(df)
    results: List[Dict[str, Any]] = []
    fold_idx = 1

    train_end = window_size
    while train_end + horizon <= n:
        train_start = train_end - window_size
        train_fold = df.iloc[train_start:train_end].copy()
        val_fold = df.iloc[train_end : train_end + horizon].copy()

        fold_meta = {
            "fold": fold_idx,
            "strategy": "rolling",
            "train_start": str(train_fold.index[0]),
            "train_end": str(train_fold.index[-1]),
            "val_start": str(val_fold.index[0]),
            "val_end": str(val_fold.index[-1]),
            "train_size": int(len(train_fold)),
            "val_size": int(len(val_fold)),
        }

        eval_res = model_trainer_fn(train_fold, val_fold, horizon)
        fold_meta.update(eval_res)
        results.append(fold_meta)

        train_end += step_size
        fold_idx += 1

    return results


def summarize_backtest_results(fold_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Tổng hợp mean, standard deviation, min, max của các metric qua tất cả các fold backtest."""
    df_folds = pd.DataFrame(fold_results)
    metric_cols = [col for col in ["MAE", "RMSE", "MAPE"] if col in df_folds.columns]

    if not metric_cols:
        return df_folds

    summary = pd.DataFrame(
        {
            "mean": df_folds[metric_cols].mean(),
            "std": df_folds[metric_cols].std(),
            "min": df_folds[metric_cols].min(),
            "max": df_folds[metric_cols].max(),
        }
    )
    return summary
