# EXERCISE 04 — NHẬT KÝ TRIỂN KHAI VÀ XÁC MINH

## 1. Phạm vi

```text
Ngày: 2026-10-12
Notebook: notebooks/practice_1_present.ipynb
Cell sửa: 32–44
Cell chạy: 0–44
E5 được sửa/chạy: KHÔNG
Trạng thái: HOÀN_THÀNH_VÀ_XÁC_MINH
```

## 2. Implementation

- tạo `analysis/data_quality.py` cho masking, treatments, comparison/MAE và IQR;
- bổ sung ba reusable plotting functions;
- tạo `tests/test_data_quality.py`;
- mask đúng sáu timestamp, bảo toàn ground truth;
- dùng forward-fill và `interpolate(method="time", limit_area="inside")`;
- dùng IQR 1.5 trên validated log-STL residual E3;
- chỉ flag/inspect, không clipping hoặc xóa observation.

## 3. Kết quả

```text
Original missing count: 0
Simulated missing count: 6
Forward-fill MAE: 47.833333
Time-interpolation MAE: 39.713638
Potential outlier candidates: 14
IQR lower fence: -0.038284
IQR upper fence: 0.037951
```

Forward-fill tốt hơn tại `1959-04`; interpolation tốt hơn tại `1952-03`,
`1956-06`, `1956-07`, `1956-08`; hai phương pháp bằng nhau tại `1954-11`.

## 4. Outputs

```text
10_missing_values_simulation.png
SHA-256: 335d19df14ea6abdf63980b84e461f9a825eb0a889a0721065744a09f92b1783

11_missing_treatment_comparison.png
SHA-256: cfab8227647298083cceda7efdeb1f1b349f30dab99feaddfe1c97d50915557f

12_outlier_analysis.png
SHA-256: f820c101649bfa6791b1b185f2acf90d741989529959252f022f250343176a02

missing_value_comparison.csv
SHA-256: cf602ef3a1fa366338eb9649bc1c728bdbb6ce7f333e3dd86eaf417ff0bc51e1
Shape: 6 × 6

outlier_candidates.csv
SHA-256: 6f08fd16b5dd2c240801a83dc78b675302ad6e916dddb0ef8634c3611df77c39
Shape: 14 × 9
```

Ba figure đã được inspect; không có nhãn/panel bị cắt và không có after-clipping
plot.

## 5. Validation

```text
pytest: 23 passed
Notebook code execution counts: 1–28
Notebook error outputs: 0
git diff --check: passed
Raw SHA-256: bdb98adbd418a6de6842a742e0602f363c3b841c26677e7e61a1e055e9509bd8
E1–E2 source/type: baa231632af529bcf729d6b0f7278f25c63219e44c8211d73fa587dca586fe2d
E3 source/type: f09125cf3fc9fcfc518bf9efa59d134b72a465d7486625e57b5000761c6d57a7
E4 source/type: 80cb3cd00e131de8af96f55305d96d596394263ce0f0f68dfa82d93c1257dc0d
E5 source/type: ecdf85193fb3d913deee457b75529dbe594d7af93babeba95a8af0fed7cbae50
Notebook SHA-256: a5bd9901cd7e4444e2fd9f3f463eec4a9be728c172e137a643d32952a30666cf
```

E4 hoàn tất. E5 chưa được phép triển khai.

