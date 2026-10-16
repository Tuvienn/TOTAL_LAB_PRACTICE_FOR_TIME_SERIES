# Time Series Practice 2

## Trạng thái

```text
Practice: Practice_2
Stage: INITIALIZED
Dataset: chưa chốt
Exercise scope: chưa chốt
Implementation: chưa bắt đầu
```

Practice 2 đã có documentation, execution evidence và notebook workflow cho E01–E03.
E03 đang bị chặn bởi stationarity evidence sau first differencing; E04 chưa được mở.

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

## Nguyên tắc khởi tạo

- Không sao chép dataset, notebook, code, outputs hoặc logs của Practice khác.
- Raw data phải được giữ bất biến sau khi nguồn dữ liệu được phê duyệt.
- Logic tái sử dụng đặt trong `src/practice_2/`; notebook chỉ điều phối và trình bày.
- Mọi bước triển khai phải tuân theo rule và approval workflow của repository.
