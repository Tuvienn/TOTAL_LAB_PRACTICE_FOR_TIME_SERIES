# EXERCISE 05 — VẤN ĐỀ ĐỒNG BỘ NOTEBOOK

## Trạng thái

```text
Issue: RESOLVED_AND_VALIDATED
Scope: Exercise 5 only
Approved remediation: docs/plans/exercise_05_before_process.md
Human approval: 2026-10-20
```

## Hành vi quan sát được

- Tiêu đề notebook trộn ARIMA với SARIMA dù SARIMA thuộc E6.
- Model order bị hard-code thay vì đọc validated handoff từ E4.
- Model fitting, residual diagnostics, forecast alignment, baseline logic và metrics
  chỉ tồn tại trong notebook cell.
- Residual diagnostics còn bao gồm residual thuộc initialization burn-in.
- Inverse-log policy và giới hạn bias chưa được ghi rõ.
- Trend policy của integrated ARIMA dựa vào default của thư viện, khiến việc không
  dùng drift và tác động lên long-horizon forecast không rõ với người đọc.
- Chưa có CSV output, exported figure và targeted test bắt buộc cho E5.

## Hành vi kỳ vọng

- E5 phải đọc E4 candidate artifact và fit các level train đã log-transform.
- Logic tái sử dụng và ảnh hưởng tính đúng đắn phải nằm trong `src/practice_2/`.
- Residual diagnostics phải dùng post-burn-in residual và ghi lại cấu hình Ljung–Box.
- Forecast và metrics phải dùng đúng holdout 41 tháng đã alignment.
- Inverse policy phải được khóa và ghi lại trước formal evaluation.
- Cấu hình no-drift phải tường minh trong source, fit evidence và phần diễn giải.
- Notebook chỉ điều phối và trình bày verified artifact.

## Kết quả sửa lỗi

E5 plan đã được triển khai với forecasting source owner, targeted test, CSV output ổn
định, exported figure và notebook section ngắn gọn. E6 không bị thực thi hoặc chỉnh
sửa trong lần xác nhận E5. Residual autocorrelation còn lại là giới hạn khoa học,
không phải implementation error, và ngăn việc tuyên bố final model adequate.

ARIMA implementation hiện ghi rõ `trend='n'`; notebook cũng liên hệ no-drift
specification với forecast gần như phẳng trên horizon 41 tháng.
