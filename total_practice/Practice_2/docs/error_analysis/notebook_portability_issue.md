# PRACTICE 2 — VẤN ĐỀ PORTABILITY CỦA NOTEBOOK

## 1. Thông tin vấn đề

```text
Practice: Practice_2
Scope: notebooks/Practice_2_present.ipynb
Issue type: Reproducibility and environment portability
Observed state: CONFIRMED
Downstream impact: clean-kernel execution is not reproducible across machines
```

## 2. Hành vi kỳ vọng

Notebook phải dùng package `practice_2` đã cài từ `pyproject.toml`, tìm dữ liệu theo
project-relative path và chạy bằng kernel riêng của Practice 2. Notebook không được
sửa `sys.path`, hard-code đường dẫn của máy cá nhân hoặc phụ thuộc hidden state.

## 3. Hành vi quan sát được

Notebook hiện có hai machine-specific bootstrap paths:

```text
D:\TimeSeries_Data\total_practice\Practice_2\src
D:\TimeSeries_Data\total_practice\Practice_2\datasets\raw\a10.csv
```

Cell khởi tạo còn chèn thư mục Windows vào `sys.path`. E04 tải lại `a10.csv` bằng
đường dẫn tuyệt đối thay vì tái sử dụng `RAW_PATH` đã được xác định từ project root.
Persisted output cũng cho thấy notebook trước đây được chạy trong môi trường Windows
Python 3.11.9, không phải môi trường Python 3.12 của Practice 2 hiện tại.

## 4. Nguyên nhân gốc

Notebook được ghép từ các lần chạy trên nhiều máy và giữ lại bootstrap code phục vụ
một môi trường Windows cụ thể. Package chưa từng là dependency owner duy nhất của
notebook, nên các cell đã tự sửa import path và tự chỉ định dataset path.

## 5. Tác động

- Kernel mới trên macOS không thể dùng các đường dẫn Windows.
- Clean execution phụ thuộc vào package từng được cài ở môi trường khác.
- E04 có thể đọc dataset từ vị trí ngoài canonical project root.
- Persisted output không đủ chứng minh notebook hiện tại chạy tuần tự trong môi
  trường Practice 2 đã chuẩn hóa.

Vấn đề này không chứng minh các con số E01–E06 sai, nhưng ngăn việc tái lập và xác
minh chúng từ kernel sạch.

## 6. Ranh giới sửa lỗi đã được phê duyệt

Human đã duyệt Step 2 — chuẩn hóa notebook ngày 2026-10-20. Fix chỉ được phép:

1. thay bootstrap cell bằng kiểm tra Python 3.12;
2. import package trực tiếp từ `.venv` đã cài editable;
3. xác định project root bằng relative path discovery;
4. thay E04 absolute dataset path bằng canonical `RAW_PATH`;
5. cập nhật tài liệu issue/fix tương ứng.

Không thay đổi ADF, differencing, ACF/PACF, candidate, model, residual, forecast,
metric hoặc kết luận E01–E06 trong fix này.
