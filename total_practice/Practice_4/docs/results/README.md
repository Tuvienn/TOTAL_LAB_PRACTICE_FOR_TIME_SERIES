# Dashboard kết quả — Practice 4

Đây là trang điều hướng tới kết quả diễn giải của từng Phase. Các giá trị dưới
đây lấy từ lần chạy hiện tại của
<a href="../../notebooks/practice4.ipynb" style="color:#1f6feb;">notebooks/practice4.ipynb</a> và là kết quả của lần chạy hiện tại.

## Kết quả theo Phase

| Phase | Nội dung | Trạng thái | Kết quả |
|---|---|---|---|
| <a href="phase_01_data_preparation.md" style="color:#1f6feb;">Phase 1</a> | Data Preparation | Đã chạy | <a href="phase_01_data_preparation.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_02_split_validation.md" style="color:#1f6feb;">Phase 2</a> | Temporal Split và Validation | Đã chạy | <a href="phase_02_split_validation.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_03_eda.md" style="color:#1f6feb;">Phase 3</a> | Training-only EDA | Đã chạy | <a href="phase_03_eda.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_04_preprocessing.md" style="color:#1f6feb;">Phase 4</a> | Preprocessing và Scaling | Đã chạy | <a href="phase_04_preprocessing.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_05_feature_engineering.md" style="color:#1f6feb;">Phase 5</a> | Feature Engineering | Đã chạy | <a href="phase_05_feature_engineering.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_06_var.md" style="color:#1f6feb;">Phase 6</a> | VAR | Đã chạy | <a href="phase_06_var.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_07_xgboost.md" style="color:#1f6feb;">Phase 7</a> | XGBoost | Đã chạy | <a href="phase_07_xgboost.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_08_lstm.md" style="color:#1f6feb;">Phase 8</a> | LSTM | Đã chạy | <a href="phase_08_lstm.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_09_evaluation.md" style="color:#1f6feb;">Phase 9</a> | Walk-forward Evaluation | Đã chạy | <a href="phase_09_evaluation.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_10_final_report.md" style="color:#1f6feb;">Phase 10</a> | Results và Final Report | Đã hoàn tất | <a href="phase_10_final_report.md" style="color:#1f6feb;">Mở kết quả</a> |

## Kết quả model hiện tại

| Model | Test RMSE | Test MAE | Test MAPE |
|---|---:|---:|---:|
| XGBoost | 3664.4820 | 2935.2076 | 9.9482% |
| LSTM | 4855.8257 | 3884.7037 | 13.3496% |
| VAR | 4614.2743 | 3952.8715 | 13.9444% |

## Artifact nhanh

- <a href="../../results/model_evaluation.csv" style="color:#1f6feb;">Bảng đánh giá CSV</a>
- <a href="../../results/model_evaluation.xlsx" style="color:#1f6feb;">Bảng đánh giá Excel</a>
- <a href="../../results/validation_ranking.csv" style="color:#1f6feb;">Validation ranking</a>
- <a href="../../results/test_ranking.csv" style="color:#1f6feb;">Test ranking</a>
- <a href="../../results/model_summaries/" style="color:#1f6feb;">Model summaries</a>
- <a href="../logs/practice4.log" style="color:#1f6feb;">Runtime log</a>
- <a href="../status/current_status.md" style="color:#1f6feb;">Current status và provenance</a>
