# EXERCISE 04 — PHÂN TÍCH HIỆN TRẠNG NOTEBOOK

## 1. Thông tin vấn đề

```text
Practice: Practice_1
Exercise: 04 — Time Series Data Quality
Notebook chính: notebooks/practice_1_present.ipynb
Phạm vi cell: 32–44
Exercise 5 bắt đầu: cell 45
Trạng thái phân tích: ĐÃ_PHÂN_TÍCH
Trạng thái triển khai: ĐÃ_HOÀN_THÀNH_VÀ_XÁC_MINH
Human authorization: CÓ — 2026-10-12
```

## 2. Phần đang làm tốt và cần giữ

- thí nghiệm được tạo trên working copy;
- chuỗi original được giữ lại;
- forward-fill và interpolation dùng hai treatment copy riêng;
- phần giải thích nhận diện đúng plateau của forward-fill và tính hai phía của interpolation;
- công thức IQR multiplier 1.5 đúng;
- phần kết luận đã cảnh báo seasonal peak không tự động là outlier;
- bố cục before/after có giá trị trình bày.

## 3. Điểm chưa phù hợp

### Missing-value experiment

```text
Observed: mask 4 vị trí positional index [10, 25, 50, 80]
Expected: mask đúng 6 timestamp đã khóa
```

Bốn vị trí cũ tương ứng `1949-11`, `1951-02`, `1953-03`, `1955-09`; không khớp
protocol. Notebook chưa ghi existing missing count trước masking, chưa tạo ground-truth
table, chưa so sánh tại masked positions và chưa tính MAE.

Cell 35 dùng `method="linear"`; contract yêu cầu:

```python
interpolate(method="time", limit_area="inside")
```

### Outlier analysis

Cell 42 áp dụng IQR trên passenger series đã interpolation thay vì log-STL residual
từ E3. Cell 43 tự động clipping, trái rule `flag and inspect only`. Cell 39–40 dùng
centered rolling statistics ngoài protocol E4 và trùng phạm vi E5.

### Presentation và outputs

Notebook thiếu heading E4, reusable source owner, tests, actual metric và 12 câu trả
lời. Các output sau chưa tồn tại:

```text
10_missing_values_simulation.png
11_missing_treatment_comparison.png
12_outlier_analysis.png
missing_value_comparison.csv
outlier_candidates.csv
```

## 4. Baseline chẩn đoán

Với sáu timestamp đã khóa:

```text
Forward-fill MAE: 47.833333
Time-interpolation MAE: 39.713638
Forward-fill tốt hơn: 1959-04
Interpolation tốt hơn: 1952-03, 1956-06, 1956-07, 1956-08
Hai method bằng nhau: 1954-11
```

IQR multiplier 1.5 trên log-STL residual tạo 14 potential candidates. Đây chỉ là
baseline chẩn đoán; output chính thức phải đến từ execution đã kiểm thử.

## 5. Ranh giới bảo vệ

```text
Cell E1–E3: không sửa
Cell E4: chỉ 32–44
Cell E5: 45 trở đi không sửa
Raw dataset: không sửa
Validated E1–E3 outputs: không ghi đè
Không thêm dependency
Không tự động xóa hoặc replace outlier
```

Checksum baseline:

```text
E4 source/type: c21872e27ca88a048599d0950d30d732ae9b45a90f4ed66d25606ed30843087e
E5 source/type: ecdf85193fb3d913deee457b75529dbe594d7af93babeba95a8af0fed7cbae50
Raw data: bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8
```

## 6. Quyết định

```text
Error analysis reviewed by Human: CÓ
Fix plan authorized: CÓ
Cho phép triển khai E4: CÓ
```

## 7. Kết quả xử lý

E4 đã được đồng bộ và xác minh ngày 2026-10-12. Notebook chạy sạch đến cell 44,
23 test đạt, ba figure và hai CSV đã được inspect. Raw data, E1–E3 và E5 không đổi.
Chi tiết tại `docs/logs/exercise_04_execution.md`.

