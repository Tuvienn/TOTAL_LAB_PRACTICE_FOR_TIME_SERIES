# Time Series Practice 2

## Trạng thái hiện tại

```text
Practice: Practice_2
Dataset chính: a10.csv
Phạm vi chính thức: Exercise 1–5
Trạng thái E1–E5: đã triển khai và kiểm tra
Phần nâng cao E6: exploratory, không thuộc formal completion
Trạng thái bàn giao: HANDOFF_APPROVED
```

Practice 2 thực hiện EDA, kiểm định ADF, differencing, phân tích ACF/PACF,
huấn luyện ARIMA và đánh giá forecast trên dữ liệu tháng. E1–E5 sử dụng
`a10.csv`; E6 sử dụng AirPassengers để so sánh ARIMA với SARIMA ở mức
phân tích mở rộng.

Kết quả chi tiết được trình bày tại:

- [Notebook chính — E1 đến E5](./notebooks/Practice_2_present.ipynb)
- [Notebook nâng cao — E6](./notebooks/Practice_2_advanced_sarima.ipynb)
- [Báo cáo kết quả](./docs/report.md)
- [Trạng thái thực hiện](./docs/status/current_status.md)

## Cấu trúc

```text
Practice_2/
├── config/
├── datasets/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── error_analysis/
│   ├── exercise_details/
│   ├── fix_plans/
│   ├── logs/
│   ├── plans/
│   ├── rules/
│   └── status/
├── notebooks/
├── outputs/
│   ├── figures/
│   └── results/
├── src/
│   └── practice_2/
│       ├── analysis/
│       ├── data/
│       └── visualization/
└── tests/
```

## Nguyên tắc thực hiện

- Raw data được giữ bất biến sau khi dataset được phê duyệt.
- Temporal split luôn giữ nguyên thứ tự thời gian và không shuffle.
- Logic tái sử dụng của phạm vi chính thức được đặt trong `src/practice_2/`;
  notebook dùng để điều phối và trình bày kết quả.
- Kết luận thống kê phải nêu rõ giả thuyết, ngưỡng `alpha` và giới hạn của bằng chứng.
- E6 được giữ ở mức exploratory: kết quả có thể trình bày nhưng không được ghi là
  một Exercise đã formalize hoặc hoàn thành chính thức.
- Mọi thay đổi tiếp theo phải tuân theo rule và approval workflow của repository.
