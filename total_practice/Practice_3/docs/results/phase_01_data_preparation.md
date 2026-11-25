# Phase 1 — Structural Data Preparation

## Mục tiêu

Đọc raw AEP dataset, giữ nguyên timeline và tạo processed dataset có audit máy
đọc được.

## Kết quả chính

- Prepared dataset: `121,296` rows, hourly timeline liên tục.
- Missing target được giữ lại: `27`; không imputation target.
- Raw và processed checksum được ghi trong current status và data-quality audit.

## Evidence

- <a href="../../notebooks/Practice_3_present.ipynb" style="color:#1f6feb;">Notebook chính — cells 3–5</a>
- <a href="../../src/practice_3_v2/data/data_preparation.py" style="color:#1f6feb;">Source: data_preparation.py</a>
- <a href="../../tests/test_data_preparation.py" style="color:#1f6feb;">Tests</a>
- <a href="../../outputs/results/phase_01_data_quality.json" style="color:#1f6feb;">Data-quality JSON</a>
- <a href="../phase_details/PHASE_01_STRUCTURAL_DATA_PREPARATION.md" style="color:#1f6feb;">Phase detail</a>
- <a href="../logs/PHASE_01_EXECUTION.md" style="color:#1f6feb;">Execution log</a>

## Figures và raw log

Phase 1 không có figure riêng và chưa có raw `.log`; Markdown execution log là
evidence thực thi chính.

## Trạng thái

`PASS` — Processed dataset sẵn sàng cho Phase 2.
