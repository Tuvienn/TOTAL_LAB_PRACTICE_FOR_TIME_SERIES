# Dashboard kết quả — Practice 3

Đây là trang mục lục để mở kết quả diễn giải của từng Phase. Mỗi Phase có một
file Markdown riêng, trong đó nối tới notebook, source code, tests, artifact,
figure và execution evidence tương ứng.

<p>
<a href="../../notebooks/Practice_3_present.ipynb" style="color:#1f6feb; font-weight:600;">🔗 Mở Notebook chính</a>
&nbsp; · &nbsp;
<a href="../../README.md" style="color:#1f6feb; font-weight:600;">🔗 Mở README Practice 3</a>
&nbsp; · &nbsp;
<a href="../plans/PROJECT_OVERVIEW.md" style="color:#1f6feb; font-weight:600;">🔗 Xem Project Overview</a>
&nbsp; · &nbsp;
<a href="../status/current_status.md" style="color:#1f6feb; font-weight:600;">🔗 Xem Current Status</a>
</p>

## Kết quả theo Phase

| Phase | Nội dung | Trạng thái | Kết quả |
|---|---|---|---|
| <a href="phase_00_problem_definition.md" style="color:#1f6feb;">Phase 0</a> | Problem Definition | PASS | <a href="phase_00_problem_definition.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_01_data_preparation.md" style="color:#1f6feb;">Phase 1</a> | Structural Data Preparation | PASS | <a href="phase_01_data_preparation.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_02_temporal_split.md" style="color:#1f6feb;">Phase 2</a> | Temporal Split và Validation | PASS | <a href="phase_02_temporal_split.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_03_eda.md" style="color:#1f6feb;">Phase 3</a> | TRAIN-only EDA | PASS | <a href="phase_03_eda.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_04_feature_engineering.md" style="color:#1f6feb;">Phase 4</a> | Feature Engineering | PASS | <a href="phase_04_feature_engineering.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_05_supervised_dataset.md" style="color:#1f6feb;">Phase 5</a> | X/y Construction | PASS | <a href="phase_05_supervised_dataset.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_06_model_selection.md" style="color:#1f6feb;">Phase 6</a> | Model Selection và Model Lock | PASS | <a href="phase_06_model_selection.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_07_evaluation.md" style="color:#1f6feb;">Phase 7</a> | Final Forecasting và Evaluation | PASS | <a href="phase_07_evaluation.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_08_error_interpretation.md" style="color:#1f6feb;">Phase 8</a> | Error và Interpretation | PASS | <a href="phase_08_error_interpretation.md" style="color:#1f6feb;">Mở kết quả</a> |
| <a href="phase_09_final_conclusion.md" style="color:#1f6feb;">Phase 9</a> | Final Conclusion và Handoff | PASS | <a href="phase_09_final_conclusion.md" style="color:#1f6feb;">Mở kết quả</a> |

## Kết quả model chính

Model được khóa là `xgboost_tuned`. Các metric lấy từ official artifacts của
Phase 7 và được diễn giải trong Phase 9:

| Protocol | MAE (MW) | RMSE (MW) |
|---|---:|---:|
| One-step historical holdout | 102,841 | 137,929 |
| Recursive 24-hour pooled | 509,652 | 720,451 |

- <a href="../../outputs/results/phase_07_one_step_metrics.json" style="color:#1f6feb;">One-step metrics</a>
- <a href="../../outputs/results/phase_07_recursive_metrics.json" style="color:#1f6feb;">Recursive metrics</a>
- <a href="../../outputs/results/phase_09_final_conclusion.json" style="color:#1f6feb;">Final conclusion JSON</a>

## Quy ước thư mục

- `docs/results/`: một trang kết quả diễn giải cho mỗi Phase và trang mục lục này.
- `docs/phase_details/`: protocol, thiết kế và acceptance criteria.
- `docs/logs/`: execution evidence dạng Markdown.
- `runs/`: raw runtime log và artifact theo run ID nếu có.
- `outputs/results/`: JSON/CSV machine-readable.
- `outputs/figures/`: hình official.
- `notebooks/Practice_3_present.ipynb`: notebook trình bày chung cho toàn bộ Phase.

## Cảnh báo khoa học

Historical holdout không phải truly unseen test set. Practice 3 chưa benchmark
ARIMA trên cùng folds, timestamps và metrics, vì vậy không được tuyên bố
XGBoost vượt ARIMA bằng thực nghiệm. Recursive error tăng theo horizon và
supplemental experiments chỉ là development-only evidence.
