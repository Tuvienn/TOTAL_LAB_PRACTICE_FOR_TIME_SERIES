# EXERCISE 04 — VẤN ĐỀ ĐỒNG BỘ ACF/PACF

## Trạng thái

```text
Issue: RESOLVED_AND_VALIDATED
Scope: Exercise 4 only
Approved remediation: docs/plans/exercise_04_before_process.md
Human approval: 2026-10-20
```

## Hành vi quan sát được

- Bảng ACF/PACF trong notebook dùng xấp xỉ cố định `1.96 / sqrt(n)`, trong khi
  biểu đồ `statsmodels` dùng confidence interval thay đổi theo từng lag.
- Notebook liệt kê ba ARIMA candidate tạm thời dù contract E4 chỉ cho phép một hoặc hai.
- Phần diễn giải nói ACF cắt sau lag 1 dù output đã lưu có correlation mùa vụ mạnh
  tại lag 12, 24 và 36.
- Chưa có source module, test, CSV result hoặc exported figure riêng cho E4.

## Hành vi kỳ vọng

- Bảng, significance flag và figure phải dùng chung confidence interval 95% do
  `statsmodels` tính toán.
- E4 chỉ phân tích 162 giá trị của chuỗi train sau natural-log first differencing từ E3.
- Candidate selection phải dựa trên evidence đã kiểm tra, giữ trạng thái provisional
  và chỉ gồm một hoặc hai candidate `(p,1,q)`.
- Reusable computation thuộc `src/practice_2/`; notebook chỉ điều phối và trình bày
  verified result.

## Tác động

Các cell cũ hữu ích cho exploratory analysis nhưng chưa tạo thành một E4 handoff đã
được xác nhận. Candidate rationale và significance label không thể được xem là một
kết quả khoa học nhất quán, có thể tái tạo.

## Ranh giới sửa lỗi

Áp dụng E4 before-process plan đã được phê duyệt. Không fit model, mở test set để
selection, sửa E3, triển khai E5/E6 hoặc tuyên bố final ARIMA model trong bản sửa này.

## Kết quả sửa lỗi

- Bảng ACF/PACF hiện dùng confidence interval 95% từ `statsmodels`.
- Exported figure được render từ cùng các bảng kết quả.
- E4 bàn giao đúng hai provisional candidate.
- Đã bổ sung source logic, test, CSV artifact và figure riêng.
- Canonical setup cùng E4 chạy không có notebook error; E5/E6 không được chạy trong
  lần xác nhận E4.
