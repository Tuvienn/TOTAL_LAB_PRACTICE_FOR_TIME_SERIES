# Phase 9 — Walk-forward Evaluation và Error Analysis

## Mục tiêu

Đánh giá ba mô hình trên cùng các mốc Validation/Test bằng recursive rolling
one-step-ahead và so sánh RMSE, MAE, MAPE trên thang đo load ban đầu. Prediction
được append vào history; không retrain sau mỗi bước.

## Kết quả Test

| Hạng | Model | RMSE | MAE | MAPE |
|---:|---|---:|---:|---:|
| 1 | XGBoost | 3664.4820 | 2935.2076 | 9.9482% |
| 2 | LSTM | 4855.8257 | 3884.7037 | 13.3496% |
| 3 | VAR | 4614.2743 | 3952.8715 | 13.9444% |

XGBoost đứng đầu theo cả ba metrics trên Test trong lần chạy hiện tại. Đây là kết quả của
lần chạy notebook hiện tại.

## Artifact

- <a href="../../results/model_evaluation.csv" style="color:#1f6feb;">Model evaluation CSV</a>
- <a href="../../results/model_evaluation.xlsx" style="color:#1f6feb;">Model evaluation Excel</a>
- <a href="../../results/validation_ranking.csv" style="color:#1f6feb;">Validation ranking</a>
- <a href="../../results/test_ranking.csv" style="color:#1f6feb;">Test ranking</a>
- <a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">Notebook</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>

## Trạng thái

`Đã chạy`.
