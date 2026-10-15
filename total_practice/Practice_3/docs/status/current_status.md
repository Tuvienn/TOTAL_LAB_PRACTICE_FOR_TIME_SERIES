# PRACTICE 3 — CURRENT STATUS

## 1. Status Identity

```text
Practice: Practice_3
Current stage: PHASE_01_APPROVED_WAITING_IMPLEMENTATION_SETUP
Primary dataset: datasets/raw/AEP_hourly.csv
Implementation started: NO
Active implementation phase: NONE
Detailed phase design: PHASE_01_PHASE_02_PHASE_04_PHASE_05_PHASE_06_AND_PHASE_07_APPROVED
Next target: approve the runtime dependency strategy, then implement Phase 1
```

Tài liệu này ghi trạng thái thực tế của Practice 3. Không dùng trạng thái dự đoán để tuyên bố một phase đã được phép hoặc đã hoàn thành.

---

## 2. Completed Planning Work

```text
[COMPLETED] Practice 3 scaffold exists
[COMPLETED] Source exercise requirements reviewed
[COMPLETED] Dataset selected and placed under datasets/raw
[COMPLETED] Dataset contract recorded in the planning documents
[COMPLETED] Architecture rule aligned with Practice 3
[COMPLETED] Code and execution rule aligned with Practice 3
[COMPLETED] Plan overview aligned with the approved architecture
[COMPLETED] Project workflow mapped to seven delivery phases
[COMPLETED] Phase 1 detailed design reviewed and approved by Human
[COMPLETED] Phase 2 detailed design reviewed and approved by Human
[COMPLETED] Phase 4 detailed design reviewed and approved by Human
[COMPLETED] Phase 5 detailed design reviewed and approved by Human
[COMPLETED] Phase 6 detailed design reviewed and approved by Human
[COMPLETED] Phase 7 detailed design reviewed and approved by Human
```

No notebook, source implementation, processed dataset, trained model or result output has been completed.

---

## 3. Current Evidence

Read-only pre-audit đã xác nhận:

```text
Columns: Datetime, AEP_MW
Rows: 121273
Timestamp parse failures: 0
Missing cell values: 0
Raw chronological order: not monotonic
Duplicate timestamps: present
Missing hourly timestamps: present
```

Các quan sát này chỉ là input cho Phase 1. Chưa có data-quality treatment nào được phê duyệt và raw dataset chưa bị sửa.

---

## 4. Delivery Phase Status

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | Data Preparation | APPROVED_NOT_STARTED |
| Phase 2 | Feature Engineering | APPROVED_WAITING_PHASE_01 |
| Phase 3 | X/y Preparation | DESIGN_REVIEWED_WAITING_APPROVAL |
| Phase 4 | Time-Based Split và TimeSeriesSplit Design | APPROVED_WAITING_PHASE_03 |
| Phase 5 | Model Training và Tuning | APPROVED_WAITING_PHASE_04 |
| Phase 6 | Forecasting và Evaluation | APPROVED_WAITING_PHASE_05 |
| Phase 7 | Interpretation và Final Conclusion | APPROVED_WAITING_PHASE_06 |

---

## 5. Readiness Review

```text
Practice-specific architecture rule: READY
Practice-specific code rule: READY
Dataset contract: READY
Plan overview: READY
Project workflow: READY
Seven-phase delivery mapping: READY
Phase 1 detailed design: READY
Phase 1 implementation authorization: GRANTED
Phase 2 detailed design: READY
Phase 2 implementation authorization: GRANTED_AFTER_PHASE_01_PASS
Phase 3 detailed design: REVIEWED_WAITING_APPROVAL
Phase 3 implementation authorization: NOT_GRANTED
Phase 4 detailed design: READY
Phase 4 implementation authorization: GRANTED_AFTER_PHASE_03_PASS
Phase 5 detailed design: READY
Phase 5 implementation authorization: GRANTED_AFTER_PHASE_04_PASS
Phase 6 detailed design: READY
Phase 6 implementation authorization: GRANTED_AFTER_PHASE_05_PASS
Phase 7 detailed design: READY
Phase 7 implementation authorization: GRANTED_AFTER_PHASE_06_PASS
Runtime dependency strategy: WAITING_HUMAN_DECISION
```

Repository hiện có thư mục untracked `docs/phase_details/` gồm bảy phase files. Phase 1, Phase 2, Phase 4, Phase 5, Phase 6 và Phase 7 đã được Human review và phê duyệt. Phase 4 chỉ được thực thi sau khi Phase 3 `PASS`; Phase 5 chỉ được thực thi sau khi Phase 4 `PASS`; Phase 6 chỉ được thực thi sau khi Phase 5 `PASS`; Phase 7 chỉ được thực thi sau khi Phase 6 `PASS`. Thiết kế Phase 3 đã được thảo luận và cập nhật nhưng vẫn chờ Human phê duyệt implementation. Phase 2 chỉ được triển khai sau khi Phase 1 `PASS`.

Kết luận readiness:

```text
READY to implement Phase 1 after the runtime dependency strategy is approved
NOT READY to create processed data
NOT READY to begin modeling
```

---

## 6. Next Step

Thứ tự tiếp theo:

```text
1. Decide whether Practice 3 will use pandas/pytest or a standard-library-only implementation.
2. Do not add dependencies or silently change the approved DataFrame contract before Human approval.
3. Implement Phase 1 only after the runtime dependency strategy is approved.
4. Run the approved validation and preserve the raw checksum.
5. Do not begin Phase 2 until Phase 1 passes its validation gate.
```

---

## 7. State Update Rule

Cập nhật file này khi:

```text
a phase plan is created or approved
a phase starts, blocks or completes validation
a data or modeling protocol changes
a new blocker appears or is resolved
implementation authorization changes
```

Mọi cập nhật phải dựa trên evidence thực tế trong repository.
