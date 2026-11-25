# E02 — Kiểm định ADF trên chuỗi gốc

## Kết luận

ADF được chạy trên original training series gồm 163 observations. Với
`p-value = 0.998907`, chưa đủ bằng chứng bác bỏ giả thuyết chuỗi có unit root.
Chuỗi train gốc được xem là chưa dừng ở mức ý nghĩa 5%.

## Kết quả

| Chỉ số | Giá trị |
|---|---:|
| ADF statistic | 2.230893 |
| p-value | 0.998907 |
| Lag sử dụng | 14 |
| Alpha | 0.05 |
| Quyết định | Không bác bỏ H0 |

## Evidence

- <a href="../logs/exercise_02_execution.md" style="color:#1f6feb;">Execution evidence E02</a>
- <a href="../../notebooks/Practice_2_Exercise.ipynb" style="color:#1f6feb;">Notebook core</a>
