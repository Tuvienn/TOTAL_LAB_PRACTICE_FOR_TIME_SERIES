from typing import Any, List, Optional
import numpy as np
import pandas as pd

try:
    from sklearn.linear_model import LinearRegression as SkLinearRegression
    from sklearn.linear_model import Ridge as SkRidge
    HAS_SKLEARN_LM = True
except ImportError:
    HAS_SKLEARN_LM = False


class _NumpyRidge:
    def __init__(self, alpha: float = 1.0, fit_intercept: bool = True, **kwargs: Any) -> None:
        self.alpha = float(alpha)
        self.fit_intercept = fit_intercept
        self.coef_: Optional[np.ndarray] = None
        self.intercept_: float = 0.0

    def fit(self, X: Any, y: Any) -> "_NumpyRidge":
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float).ravel()
        n, p = X_arr.shape
        if self.fit_intercept:
            X_mean = np.mean(X_arr, axis=0)
            y_mean = np.mean(y_arr)
            X_c = X_arr - X_mean
            y_c = y_arr - y_mean
            A = X_c.T @ X_c + self.alpha * np.eye(p)
            self.coef_ = np.linalg.solve(A, X_c.T @ y_c)
            self.intercept_ = float(y_mean - X_mean @ self.coef_)
        else:
            A = X_arr.T @ X_arr + self.alpha * np.eye(p)
            self.coef_ = np.linalg.solve(A, X_arr.T @ y_arr)
            self.intercept_ = 0.0
        return self

    def predict(self, X: Any) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return X_arr @ self.coef_ + self.intercept_


class _NumpyLinearRegression:
    def __init__(self, fit_intercept: bool = True, **kwargs: Any) -> None:
        self.fit_intercept = fit_intercept
        self.coef_: Optional[np.ndarray] = None
        self.intercept_: float = 0.0

    def fit(self, X: Any, y: Any) -> "_NumpyLinearRegression":
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float).ravel()
        if self.fit_intercept:
            X_aug = np.column_stack([X_arr, np.ones(len(X_arr))])
        else:
            X_aug = X_arr
        w, _, _, _ = np.linalg.lstsq(X_aug, y_arr, rcond=None)
        if self.fit_intercept:
            self.coef_ = w[:-1]
            self.intercept_ = float(w[-1])
        else:
            self.coef_ = w
            self.intercept_ = 0.0
        return self

    def predict(self, X: Any) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return X_arr @ self.coef_ + self.intercept_


def create_lag_features(
    series: pd.Series,
    lags: List[int],
    prefix: str = "lag_",
) -> pd.DataFrame:
    """Tạo các đặc trưng độ trễ (Lag Features) hoàn toàn hướng về quá khứ, không gây rò rỉ tương lai."""
    df_lags = pd.DataFrame(index=series.index)
    for lag in lags:
        if lag <= 0:
            raise ValueError(f"Lag must be positive, got {lag}")
        df_lags[f"{prefix}{lag}"] = series.shift(lag)
    return df_lags


class TimeSeriesForecaster:
    """Mô hình dự báo máy học (Ridge / Linear Regression) với đặc trưng độ trễ và hỗ trợ Recursive Multi-step."""

    def __init__(self, model_type: str = "ridge", alpha: float = 1.0, **model_params: Any) -> None:
        self.model_type = model_type
        self.alpha = alpha
        self.model_params = model_params
        if model_type == "ridge":
            self.model = SkRidge(alpha=alpha, **model_params) if HAS_SKLEARN_LM else _NumpyRidge(alpha=alpha, **model_params)
        elif model_type == "linear":
            self.model = SkLinearRegression(**model_params) if HAS_SKLEARN_LM else _NumpyLinearRegression(**model_params)
        else:
            raise ValueError(f"Unsupported model_type: {model_type}. Choose 'ridge' or 'linear'.")
        self.feature_names: Optional[List[str]] = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "TimeSeriesForecaster":
        """Huấn luyện mô hình trên ma trận đặc trưng và nhãn của tập train."""
        self.feature_names = list(X.columns)
        self.model.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Dự báo 1 bước hoặc theo lô trên ma trận đặc trưng X."""
        if self.model is None or self.feature_names is None:
            raise RuntimeError("Model must be fitted before predict.")
        return np.asarray(self.model.predict(X[self.feature_names]), dtype=float)

    def predict_recursive(
        self,
        last_history: pd.Series,
        horizon: int,
        lags: List[int],
        prefix: str = "lag_",
    ) -> np.ndarray:
        """Thực hiện dự báo đa bước cuốn chiếu (Recursive Forecasting) từ h=1 đến h=horizon.
        
        Ở mỗi bước t+h, giá trị dự báo y_hat_{t+h-1} được đẩy vào lịch sử để tính các lag tiếp theo,
        tuyệt đối không dùng giá trị thực tế của tập test.
        """
        if self.model is None:
            raise RuntimeError("Model must be fitted before predict_recursive.")
        if horizon <= 0:
            raise ValueError(f"Horizon must be positive, got {horizon}")

        max_lag = max(lags)
        if len(last_history) < max_lag:
            raise ValueError(
                f"last_history length ({len(last_history)}) must be at least max lag ({max_lag})"
            )

        # Lấy lịch sử gần nhất để cuốn chiếu
        history = list(last_history.iloc[-max_lag:].to_numpy(dtype=float))
        predictions: List[float] = []

        for h in range(1, horizon + 1):
            # Xây dựng vector feature từ đuôi của history
            feature_dict = {}
            for lag in lags:
                col_name = f"{prefix}{lag}"
                # lag 1 là phần tử cuối cùng của history: history[-1]
                feature_dict[col_name] = history[-lag]

            X_step = pd.DataFrame([feature_dict])
            pred_val = float(self.predict(X_step)[0])
            predictions.append(pred_val)
            history.append(pred_val)

        return np.array(predictions, dtype=float)
