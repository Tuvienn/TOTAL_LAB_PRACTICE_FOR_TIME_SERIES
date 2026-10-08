# Error Analysis

Thư mục này lưu tài liệu phân tích các bug hoặc scientific issue không trivial của
Practice 1 trước khi lập kế hoạch sửa.

## Naming convention

```text
exercise_<số>_<tên_lỗi>_issue.md
```

Ví dụ:

```text
exercise_02_acf_confidence_interval_issue.md
```

## Required content

Mỗi issue report phải ghi:

- observed behavior;
- expected behavior;
- evidence và cách tái hiện;
- root cause đã xác định hoặc giới hạn điều tra hiện tại;
- affected files và outputs;
- downstream impact;
- correction requirements.

Issue report không phải implementation plan và không cho phép agent tự sửa file.
Fix plan tương ứng phải được tạo trong `docs/fix_plans/` và được Human phê duyệt trước
khi triển khai.
