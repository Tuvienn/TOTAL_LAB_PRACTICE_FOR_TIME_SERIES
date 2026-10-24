# Nhiệm vụ: Triển khai các phương pháp chia tập dữ liệu: Temporal Split (chuẩn) và Random Split (sai lệch để so sánh trong E2).
from typing import Optional, Tuple
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
        timestamp_col: Cột thời gian dùng để xác nhận thứ tự.
        
    Returns:
        Tuple gồm (train_df, test_df).
    """
    pass


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
    pass
