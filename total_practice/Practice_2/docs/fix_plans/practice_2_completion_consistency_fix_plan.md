# Fix Plan — Đồng bộ trạng thái hoàn thành Practice 2

## 1. Trạng thái kế hoạch

- **Trạng thái:** `COMPLETED_HANDOFF_APPROVED`
- **Phạm vi:** E1–E6, tài liệu tổng hợp và notebook presentation state
- **Error analysis liên quan:** `docs/error_analysis/practice_2_completion_consistency_issue.md`
- **Không bao gồm:** push GitHub, thay đổi model order hoặc thay đổi kết quả khoa học E1–E5

## 2. Mục tiêu

Đưa source code, notebook, artifact và tài liệu của Practice 2 về cùng một trạng thái có thể kiểm chứng; đồng thời không tuyên bố E6 hoàn thành trước khi đủ approval, implementation, test và evidence.

## 3. Trình tự triển khai

### Giai đoạn 1 — Đồng bộ tài liệu và trạng thái

**Trạng thái:** `COMPLETED`

1. Cập nhật `README.md` để không còn mô tả project ở trạng thái khởi tạo.
2. Cập nhật `docs/status/current_status.md` theo trạng thái thực tế của từng Exercise.
3. Cập nhật `docs/report.md`:
   - loại bỏ candidate ARIMA `(4, 1, 1)` đã lỗi thời;
   - dùng đúng metrics và residual diagnostics hiện hành;
   - sửa kết luận E6 để khớp với Ljung–Box và forecast metrics đã xác nhận.
4. Điều chỉnh cách diễn đạt E2: dùng kết luận “chưa đủ bằng chứng để xem chuỗi là stationary” thay cho phát biểu tuyệt đối khi ADF p-value lớn hơn `0.05`.
5. Không đánh dấu E6 `COMPLETED` trong giai đoạn này.

### Giai đoạn 2 — Chuẩn hóa notebook presentation state

**Trạng thái:** `COMPLETED — final clean-run đạt 27/27 và 10/10 code cells, không có lỗi`

1. Giữ nguyên logic và kết quả E1–E5.
2. Sau khi hoàn tất các chỉnh sửa đã được duyệt, chạy sạch notebook trong môi trường Practice 2.
3. Xác nhận execution count tăng tuần tự, không có traceback và output không bị stale.
4. So sánh lại các artifact quan trọng với kết quả trước khi sửa.

### Giai đoạn 3 — Chốt phạm vi E6

**Trạng thái:** `COMPLETED — Human chọn Phương án A`

#### Phương án A — Giữ E6 exploratory — ĐÃ CHỌN

1. Giữ implementation hiện tại trong advanced notebook.
2. Ghi rõ E6 là phần mở rộng, chưa formalize.
3. Không tạo các artifact còn thiếu chỉ để hợp thức hóa trạng thái.
4. Không đánh dấu E6 hoàn thành chính thức.

#### Phương án B — Formalize E6 — KHÔNG CHỌN

1. Human phê duyệt toàn bộ E6 specification/before-process scope.
2. Chuyển logic tái sử dụng từ notebook vào owner phù hợp trong `src/practice_2/`:
   - validation và temporal split;
   - ADF/differencing;
   - ACF/PACF candidate diagnostics;
   - ARIMA/SARIMA fitting và forecasting;
   - evaluation metrics và residual diagnostics.
3. Notebook chỉ gọi reusable implementation và trình bày kết quả.
4. Bổ sung test cho full E6 workflow, không chỉ residual fix.
5. Sinh và kiểm tra đầy đủ 10 artifact đã liệt kê trong error analysis.
6. Chạy clean-run notebook và toàn bộ test suite.
7. Chỉ sau Human review mới cập nhật E6 thành `COMPLETED`.

### Giai đoạn 4 — Chuẩn hóa ngôn ngữ

**Trạng thái:** `COMPLETED`

1. Source code, identifier, comment, docstring và thông báo kỹ thuật trong code dùng tiếng Anh.
2. File Markdown dùng tiếng Việt; giữ nguyên các thuật ngữ chuyên ngành tiếng Anh khi dịch làm giảm độ chính xác.
3. Không thay đổi logic trong quá trình chuẩn hóa ngôn ngữ.

### Giai đoạn 5 — Bổ sung 5W1H và provenance

**Trạng thái:** `COMPLETED — 5W1H và provenance theo đề bài đã được bổ sung vào hai notebook`

1. Bổ sung phần 5W1H ngắn gọn cho cả hai notebook.
2. Ghi link dataset chỉ sau khi link được xác minh hoặc được Human xác nhận.
3. Phân biệt rõ dataset identity đã được project phê duyệt với thông tin có thể kiểm chứng trực tiếp từ raw file.

### Giai đoạn 6 — Trình bày bảng output

**Trạng thái:** `COMPLETED — hai notebook dùng chung theme light/dark, có caption và highlight có chọn lọc`

1. Chỉ style các bảng output hiện có; không thêm chart ngoài yêu cầu bài.
2. Dùng style đọc được trên cả light theme và dark theme.
3. Mỗi bảng có caption hoặc mô tả ngắn để người đọc biết bảng thể hiện gì.
4. Không để styling làm thay đổi dữ liệu, precision dùng cho tính toán hoặc artifact CSV.

### Giai đoạn 7 — Final review và chốt trạng thái bàn giao

**Trạng thái:** `COMPLETED — HANDOFF_APPROVED`

1. Toàn bộ test suite đạt `30 passed`.
2. Hai notebook chạy tuần tự từ kernel sạch, không có traceback hoặc stale output.
3. Artifact E1–E5 khớp với notebook và tài liệu sau khi đồng bộ các sai lệch số học nhỏ.
4. E6 giữ đúng ranh giới `EXPLORATORY_ONLY` của Phương án A.
5. Không commit hoặc push trước khi có yêu cầu riêng của Human.

## 4. File dự kiến được phép chỉnh sửa

- `README.md`
- `docs/report.md`
- `docs/status/current_status.md`
- các file Markdown có nội dung tiếng Anh cần đồng bộ ngôn ngữ
- `notebooks/Practice_2_present.ipynb`
- advanced notebook hiện hành
- file trong `src/practice_2/`, `tests/`, `figures/` và `results/` **chỉ khi Human chọn Phương án B cho E6**

Nếu phát hiện cần chỉnh một file ngoài danh sách này, phải dừng và báo Human trước.

## 5. Tiêu chí nghiệm thu

1. Toàn bộ test suite pass.
2. Hai notebook chạy sạch từ đầu đến cuối.
3. Không có execution count rỗng hoặc thứ tự thực thi bị lệch trong notebook bàn giao.
4. E1–E5 giữ nguyên split, model order và verified metrics trừ khi một error analysis mới chứng minh có lỗi.
5. `README.md`, `report.md`, `current_status.md` không còn mâu thuẫn.
6. Kết luận E6 khớp với Ljung–Box và forecast metrics hiện hành.
7. E6 chỉ được đánh dấu hoàn thành nếu Phương án B đã được phê duyệt và đủ source, test, artifact, clean run và Human review.
8. Code dùng tiếng Anh; Markdown dùng tiếng Việt theo phạm vi đã thống nhất.
9. Hai notebook có 5W1H, provenance và bảng output dễ đọc mà không thêm chart ngoài yêu cầu.

## 6. Điều kiện dừng

Dừng triển khai và báo Human nếu:

- không xác minh được link nguồn dataset;
- kết quả clean run khác verified metrics hiện tại;
- cần thay đổi model order, split hoặc scientific conclusion;
- E6 chưa được Human chọn Phương án A hoặc B;
- xuất hiện xung đột giữa specification, before-process plan và rule hiện hành.

## 7. Approval gate

- [x] Human phê duyệt fix plan này.
- [x] Human chọn Phương án A — giữ E6 ở mức exploratory.
- [x] Phương án B không được chọn; không mở phạm vi full E6.
- [x] Human xác nhận trạng thái bàn giao cuối.
