# Practice 4 — Machine-readable results

Thư mục này chứa các artifact được notebook sinh ra trong lần chạy gần nhất.

Dashboard diễn giải theo Phase nằm tại
<a href="../docs/results/README.md" style="color:#1f6feb;">../docs/results/README.md</a>.

## Artifact chính

- `model_evaluation.csv`: bảng metrics Validation/Test của VAR, XGBoost và LSTM.
- `model_evaluation.xlsx`: cùng bảng metrics ở định dạng Excel.
- `validation_ranking.csv`: xếp hạng model trên Validation.
- `test_ranking.csv`: xếp hạng model trên Test.
- `model_summaries/`: summary và training history của từng model.

Các file trong thư mục này là output máy đọc được, không thay thế execution log
tại <a href="../docs/logs/practice4.log" style="color:#1f6feb;">../docs/logs/practice4.log</a> hoặc các trang kết
quả diễn giải trong `docs/results/`.
