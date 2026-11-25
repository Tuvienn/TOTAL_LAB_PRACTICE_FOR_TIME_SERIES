# QUY TẮC WORKFLOW — PRACTICE 3 V2

## 1. Chu kỳ triển khai phase

```text
kiểm tra evidence hiện tại
→ thảo luận quyết định còn mở
→ thiết kế phase detail
→ Human duyệt
→ triển khai đúng phase
→ chạy và kiểm tra
→ báo cáo kết quả
→ Human review
→ chuyển sang phase kế tiếp
```

Không triển khai phase sau khi validation gate của phase hiện tại chưa đạt.

## 2. Thiết kế tuần tự

Implementation plan tổng thể đã được Human duyệt trên chat. Phase-detail document chỉ được tạo cho phase sắp triển khai; không thiết kế chi tiết toàn bộ phase cùng lúc.

## 3. Git và external actions

Không commit, push, đổi branch hoặc xóa legacy evidence nếu chưa được Human yêu cầu hoặc phê duyệt rõ ràng. Training dài hoặc bước mở holdout phải được Human thực hiện hay xác nhận theo phase detail tương ứng.

## 4. Trạng thái

`docs/status/current_status.md` phải phản ánh bằng chứng đã tồn tại. Không ghi `PASS`, `READY` hoặc `COMPLETE` dựa trên kế hoạch hay dự đoán.
