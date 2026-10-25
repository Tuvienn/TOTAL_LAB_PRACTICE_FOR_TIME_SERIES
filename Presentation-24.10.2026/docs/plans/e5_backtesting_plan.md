# E5 PLAN — BACKTESTING (EXPANDING & ROLLING WINDOW)

## 1. Trạng thái thực hiện
- **Trạng thái**: `[COMPLETED]`
- **Thời điểm hoàn thành**: 2026-10-25
- **Chiến lược thực hiện**: Expanding Window Backtesting qua 6 folds độc lập hàng năm (1955 đến 1960).
- **Cấu hình chi tiết**: `initial_train_size = 72` (6 năm đầu 1949–1954), `horizon = 12` (1 năm), `step_size = 12` (dịch chuyển 1 năm/fold).

## 2. Mục tiêu
Đánh giá độ ổn định và khả năng khái quát hóa của mô hình qua nhiều mốc thời gian trong lịch sử thay vì chỉ dựa vào một lần chia train/test duy nhất.

## 3. Thiết lập thực nghiệm
- **Nguyên tắc chống rò rỉ**: Mỗi fold fit riêng scaler và mô hình trên tập train của fold đó, không sử dụng bất kỳ thông tin nào của validation fold hay tương lai.
- **Chiến lược đa bước**: Recursive Forecasting cho toàn bộ $h=1..12$ bước của từng fold.
- **Tổng hợp thống kê**: Tính toán Mean, Standard Deviation, Min, Max của các chỉ số qua toàn bộ 6 folds.

## 4. Kết quả thực nghiệm đối chứng
### 4.1. Thống kê tổng hợp qua 6 Folds (`backtesting_statistical_summary.csv`)
| Metric | Mean ($\mu$) | Std ($\sigma$) | Min | Max | Đánh giá độ ổn định |
|---|:---:|:---:|:---:|:---:|---|
| **MAE** | **19.01** | 9.84 | 10.00 | 36.77 | Sai số tương đối ổn định, fold 6 gặp biên độ mùa hè cao |
| **RMSE** | **21.19** | 9.94 | 11.34 | 38.96 | Khoảng cách RMSE - MAE nhỏ (2.18), ít lỗi đột biến lớn |
| **MAPE (%)** | **5.34%** | 2.94% | 2.90% | 9.84% | Sai số phần trăm luôn được kiểm soát dưới 10% ở mọi fold |

### 4.2. Chi tiết từng Fold (`backtesting_folds_summary.csv`)
- **Fold 1** (Train: 1949–1954, Val: 1955): Train 72, Val 12 $\rightarrow$ MAE = 10.00, RMSE = 11.34, MAPE = 3.63%.
- **Fold 2** (Train: 1949–1955, Val: 1956): Train 84, Val 12 $\rightarrow$ MAE = 12.00, RMSE = 14.86, MAPE = 3.51%.
- **Fold 3** (Train: 1949–1956, Val: 1957): Train 96, Val 12 $\rightarrow$ MAE = 10.93, RMSE = 12.98, MAPE = 2.90% (Fold ổn định nhất).
- **Fold 4** (Train: 1949–1957, Val: 1958): Train 108, Val 12 $\rightarrow$ MAE = 15.65, RMSE = 18.06, MAPE = 3.97%.
- **Fold 5** (Train: 1949–1958, Val: 1959): Train 120, Val 12 $\rightarrow$ MAE = 28.69, RMSE = 30.93, MAPE = 6.84%.
- **Fold 6** (Train: 1949–1959, Val: 1960): Train 132, Val 12 $\rightarrow$ MAE = 36.77, RMSE = 38.96, MAPE = 9.84% (Đỉnh tăng trưởng ngành hàng không).

## 5. Output bàn giao thực tế
- [x] `backtesting_folds_summary.csv`: Bảng tổng hợp chi tiết phạm vi thời gian và metrics của 6 folds.
- [x] `backtesting_statistical_summary.csv`: Bảng tổng hợp Mean, Std, Min, Max của MAE, RMSE, MAPE.
- [x] `05_backtesting_folds.png` (Visual 5): Sơ đồ các fold kiểm chứng Expanding Window qua dòng thời gian.
- [x] `06_performance_across_folds.png` (Visual 6): Biểu đồ đường biểu thị sự biến thiên hiệu năng giữa Model và Seasonal Naive qua 6 folds.
- [x] **Kết luận E5**: Backtesting đa mốc chứng minh mô hình duy trì MAPE trung bình 5.34%, vượt trội hơn hẳn Seasonal Naive ở mọi fold, và chỉ ra thách thức khi biên độ mùa vụ bùng nổ ở các năm cuối.

