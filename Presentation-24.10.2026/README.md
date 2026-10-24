# PRACTICE 2 — TOPIC 5: ĐÁNH GIÁ MÔ HÌNH DỰ BÁO ĐÚNG CÁCH: DATA LEAKAGE VÀ BACKTESTING

## 1. Giới thiệu tổng quan

Tài liệu này là đặc tả tiền dự án cho **Practice 2** (thuộc Topic 5 theo tài liệu hướng dẫn: *"Đánh giá mô hình dự báo đúng cách: Data Leakage và Backtesting"*).

Dự án tập trung vào phương pháp luận và kỹ thuật đánh giá mô hình chuỗi thời gian (Time Series) một cách khoa học, trung thực và không bị sai lệch (unbiased), ngăn ngừa triệt để rò rỉ dữ liệu tương lai (Data Leakage) và đánh giá độ ổn định qua thời gian thông qua Backtesting.

## 2. Mục tiêu nghiên cứu & thực nghiệm

1. **Phần Lý thuyết (Theory / Research)**: Nghiên cứu chuyên sâu 10 chủ đề cốt lõi theo khung chuẩn **5W1H Research Template** (What, Why, When, Where, Who, How, Example/Illustration, Advantages & Limitations):
   - Mục 1: Tổng quan về đánh giá mô hình dự báo chuỗi thời gian.
   - Mục 2: Random Split vs Temporal Split.
   - Mục 3: Data Leakage trong Time Series.
   - Mục 4: Scaling Leakage (Rò rỉ chuẩn hóa dữ liệu).
   - Mục 5: Backtesting (Kiểm chứng lịch sử đa mốc).
   - Mục 6: Rolling Window vs Expanding Window Backtesting.
   - Mục 7: Đánh giá bằng sai số: MAE, RMSE, MAPE và giới hạn.
   - Mục 8: Baseline Forecast (Naive và Seasonal Naive).
   - Mục 9: Đánh giá theo chân trời dự báo (Forecast Horizon $h=1..H$).
   - Mục 10: Quy trình đánh giá chuẩn (Correct Evaluation Workflow).

2. **Phần Thực nghiệm (Practical Experiments - E1 đến E6)**:
   - **E1 — Data Understanding**: Khảo sát kích thước, timestamp, target, frequency, date range, missing values, tính liên tục và mùa vụ.
   - **E2 — Random Split vs Temporal Split**: Thực nghiệm chứng minh vì sao chia ngẫu nhiên gây sai lệch lạc quan phi thực tế.
   - **E3 — Scaling Data Leakage**: So sánh Pipeline A (rò rỉ: fit trên toàn bộ dataset) vs Pipeline B (chuẩn: fit trên train, transform test).
   - **E4 — Baseline vs Forecasting Model**: So sánh mô hình dự báo với mốc tham chiếu Naive / Seasonal Naive.
   - **E5 — Backtesting**: Đánh giá mô hình qua nhiều fold với Expanding Window (bắt buộc) và Rolling Window (mở rộng).
   - **E6 — Forecast Horizon Evaluation**: Đo lường sai số phân rã theo từng bước dự báo $h = 1, 2, \dots, H$.

## 3. Cấu trúc thư mục Practice 2

```text
Practice_2/
├── .gitignore
├── README.md
├── pyproject.toml
├── config/
│   └── practice_2_config.json
├── datasets/
│   ├── README.md
│   ├── raw/
│   └── processed/
├── docs/
│   ├── theory/            # 10 file nghiên cứu lý thuyết theo chuẩn 5W1H
│   ├── plans/             # Master plan và 6 kế hoạch chi tiết cho E1..E6
│   └── status/            # Trạng thái tiến độ dự án
├── notebooks/
│   └── 01_topic_5_data_leakage_and_backtesting.ipynb
├── outputs/
│   ├── figures/           # 7 visual artifacts cho thuyết trình
│   └── results/           # Bảng số liệu, metrics, comparison tables
├── src/
│   └── practice_2/
│       ├── data/          # Loader & split modules
│       ├── preprocessing/ # Scaling modules (leakage vs correct)
│       ├── models/        # Baseline & forecaster modules
│       ├── evaluation/    # Backtesting, metrics & horizon modules
│       └── visualization/ # Diagnostic & presentation plots
└── tests/                 # Unit tests xác thực các module
```

## 4. Nguyên tắc thực nghiệm cốt lõi

- **Không bắt đầu từ kết luận mong muốn**: Mọi kết luận phải tuân theo luồng `Question -> Experiment -> Result -> Verification -> Interpretation -> Conclusion`.
- **Dữ liệu thô bất biến**: Không can thiệp hoặc sửa đổi trực tiếp file dữ liệu gốc.
- **Tôn trọng tính tuần tự thời gian**: Tuyệt đối không xáo trộn ngẫu nhiên dữ liệu chuỗi thời gian khi đánh giá dự báo.
- **Phòng ngừa Data Leakage**: Bất kỳ bước học tham số nào (imputation, scaling, feature selection) chỉ được fit trên tập train quá khứ.
- **Tiền dự án (Pre-project phase)**: Mã nguồn tại thư mục `src/` hiện tại chỉ chứa các khai báo hàm nguyên mẫu với thân hàm `pass` và dòng ghi chú nhiệm vụ đầu file; chưa tiến hành huấn luyện hay chạy thực nghiệm cho đến khi được Human phê duyệt.
