# Fix Plans

Thư mục này lưu kế hoạch sửa các issue đã được phân tích trong
`docs/error_analysis/`.

## Naming convention

```text
exercise_<số>_<tên_lỗi>_fix_plan.md
```

Ví dụ:

```text
exercise_02_acf_confidence_interval_fix_plan.md
```

Tên exercise và tên lỗi phải khớp với issue report tương ứng.

## Required content

Mỗi fix plan phải ghi:

- đường dẫn issue report;
- correction objective;
- confirmed scope và exclusions;
- affected code, notebook, tests và outputs;
- ordered implementation steps;
- tests và validation cần chạy;
- downstream exercises cần review hoặc chạy lại;
- stop conditions và completion criteria;
- confirmation state.

Fix plan không phải execution evidence. Sau khi thực thi, bằng chứng phải được ghi tại
`docs/logs/`, và `docs/status/current_status.md` phải được cập nhật khi trạng thái hoặc
dependency thay đổi.
