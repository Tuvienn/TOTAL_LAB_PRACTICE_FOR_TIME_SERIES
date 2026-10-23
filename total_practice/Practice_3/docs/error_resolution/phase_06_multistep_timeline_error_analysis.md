# PHASE 06 — PHÂN TÍCH LỖI TIMELINE MULTI-STEP

## Hiện tượng

Run `P6_final_evaluation_20261022_234000_26d167d7` hoàn thành năm one-step units nhưng dừng trước multi-step với lỗi:

```text
ValueError: Target series must use a complete hourly timeline.
```

## Nguyên nhân gốc

Phase 3 dùng common validity mask để chỉ giữ các hàng có target và đủ 168 lag features. Vì vậy supervised dataset có 116.675 hàng hợp lệ nhưng `DatetimeIndex` không còn liên tục tuyệt đối. Trong final-test calendar có 169 giờ không thuộc supervised population quanh khoảng thiếu dữ liệu tháng 03/2018.

Phase 6 truyền trực tiếp sparse supervised target vào `build_eligible_origins()`. Hàm này yêu cầu một hourly grid hoàn chỉnh trước khi chạy quy tắc loại origin, nên dừng trước khi có thể ghi nhận các block/history không hợp lệ.

Đây là implementation bug của Phase 6, không phải lỗi dữ liệu, model, Phase 3 validity mask hoặc kết quả one-step.

## Phạm vi ảnh hưởng

- Năm one-step units đã tạo đúng trên common population 8.592 hàng và có checksum.
- Chưa có multi-step unit nào chạy.
- Chưa có official Phase 6 artifact nào được promote.
- Final test đã có đúng một opening event và không được tạo opening event thứ hai.

## Kết luận

Multi-step target phải được reindex về hourly grid đầy đủ; giờ không thuộc supervised population được biểu diễn bằng `NaN`. Sau đó eligible-origin rule hiện có sẽ loại toàn bộ origin có future block hoặc required history không finite.
