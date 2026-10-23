# PHASE 06 — FIX PLAN CHO TIMELINE MULTI-STEP

**Human approval:** `GRANTED`
**Scope:** chỉ sửa implementation bug của Phase 6; không đổi model lock, feature configuration, hyperparameters, split hoặc forecasting protocol.

## Các thay đổi được duyệt

1. Tạo hourly grid từ timestamp đầu đến timestamp cuối của supervised target.
2. Reindex target lên grid này và giữ giờ thiếu dưới dạng `NaN`; không impute target.
3. Giữ nguyên eligible-origin rule: loại full 24-hour block nếu future target thiếu và loại origin nếu 168-hour history không đầy đủ/finite.
4. Bổ sung kiểm thử cho sparse target và xác minh final-test contract tạo 350 eligible origins từ 365 scheduled origins.
5. Chuyển failed run sang trạng thái resumable bằng migration audit có old/new execution identity; giữ nguyên opening event và chỉ tái sử dụng unit có checksum hợp lệ.
6. Không promote output cho đến khi đủ 10/10 units và transactional promotion PASS.

## Điều kiện xác nhận

- Toàn bộ automated tests PASS.
- Dry-run vẫn báo final test đã được kiểm soát theo approved contract.
- Run migration giữ `opening_event_count = 1`.
- Năm one-step artifacts cũ vượt qua checksum trước khi được tái sử dụng.
- Resume không tạo run mới hoặc opening event mới.
