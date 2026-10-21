# PRACTICE 2 — KẾ HOẠCH SỬA PORTABILITY CỦA NOTEBOOK

## 1. Thông tin kế hoạch

```text
Practice: Practice_2
Issue source: docs/error_analysis/notebook_portability_issue.md
Plan type: Reproducibility remediation
Status: IMPLEMENTED_AND_VALIDATED
Human approval date: 2026-10-20
Scientific logic changes: NOT ALLOWED
Full notebook execution: DEFERRED
```

## 2. Mục tiêu

Chuẩn hóa phần khởi tạo của canonical notebook để dùng Python 3.12, package
`practice_2` đã cài trong local `.venv` và canonical project-relative dataset paths.

## 3. Thay đổi được phép

```text
notebooks/Practice_2_present.ipynb
docs/error_analysis/notebook_portability_issue.md
docs/fix_plans/notebook_portability_fix_plan.md
```

Không sửa raw datasets, source logic, tests, outputs, Exercise specifications,
execution logs, status, report hoặc README trong step này.

## 4. Các bước triển khai

1. Thay cell sửa `sys.path` bằng Python-version guard cho Python 3.12.
2. Giữ direct package imports thông qua editable installation từ `pyproject.toml`.
3. Tìm project root từ current working directory và toàn bộ parent directories.
4. Tạo `RAW_PATH`, `FIGURES_DIR` và `RESULTS_DIR` từ project root.
5. Thay E04 absolute Windows dataset path bằng `RAW_PATH`.
6. Clear execution state chỉ ở các cell bị chỉnh sửa.
7. Quét toàn bộ code-cell source để xác nhận không còn Windows absolute path hoặc
   `sys.path` mutation.
8. Chạy import check, full test suite và pipeline smoke test bằng `.venv`.

## 5. Công việc trì hoãn

Không chạy toàn bộ notebook ở Step 2 vì E04–E06 còn các vấn đề khoa học đã được
review riêng. Clean-kernel Run All và làm mới toàn bộ outputs chỉ thực hiện sau khi
E04–E06 được sửa và xác minh.

## 6. Tiêu chí nghiệm thu

```text
[x] Notebook code-cell source không còn D:\ absolute path
[x] Notebook code-cell source không còn sys.path mutation
[x] E04 uses canonical RAW_PATH
[x] Notebook metadata uses practice2-timeseries kernel
[x] Package import check passes in Practice_2/.venv
[x] Full current test suite passes
[x] E01–E06 scientific logic and persisted notebook results remain unchanged
[x] Step 2 diff is limited to approved files; prior environment changes remain separate
```

## 7. Bản ghi xác nhận

```text
Python: 3.12.15
Kernel: practice2-timeseries / Python (Practice 2)
Notebook source portability scan: PASS
Notebook setup and E04 input smoke test: PASS
Dataset 1 observations: 204
Training observations: 163
Test observations: 41
E04 transformed training observations: 162
Current test suite: 11 passed
Dependency check: no broken requirements
Full notebook Run All: deferred by approved plan
```
