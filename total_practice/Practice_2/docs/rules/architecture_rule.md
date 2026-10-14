# TIME SERIES PRACTICE 02 — QUY TẮC KIẾN TRÚC

## 1. Danh tính và trạng thái

```text
Document ID: TS-PRACTICE-02-ARCHITECTURE-v2.0
Phạm vi: total_practice/Practice_2
Trạng thái: APPROVED_AND_ACTIVE
Ngày đồng bộ: 2026-10-14
```

Tài liệu này quy định cấu trúc, quyền sở hữu dữ liệu và code, hướng dependency,
ranh giới notebook, output và validation cho Practice 2.

Thứ tự ưu tiên tài liệu:

1. rule cấp repository được nạp từ `.agents/RULES_INDEX.md`;
2. file này và `rule_code.md`;
3. `docs/plans/project_overview.md`;
4. `docs/plans/plan_overview.md`;
5. plan hoặc specification riêng của Exercise nếu được tạo và phê duyệt.

Nếu các nguồn xung đột, phải dừng và xin Human quyết định.

---

## 2. Phạm vi khoa học

Practice 2 bao gồm:

- E01: khám phá và chuẩn bị chuỗi Monthly Retail Sales;
- E02: kiểm định ADF trên chuỗi training gốc;
- E03: sai phân và kiểm định lại tính dừng;
- E04: ACF/PACF và đề xuất ARIMA candidates;
- E05: fit ARIMA, chẩn đoán phần dư, forecast và đánh giá;
- E06: mở rộng SARIMA trên AirPassengers và so sánh với ARIMA.

Machine Learning, Deep Learning và việc mở rộng ngoài E01–E06 không thuộc phạm vi
nếu chưa có phê duyệt riêng.

---

## 3. Canonical Root và cấu trúc

Root chuẩn:

```text
total_practice/Practice_2/
```

Cấu trúc sở hữu:

```text
Practice_2/
├── config/                    # cấu hình ổn định, được phê duyệt
├── datasets/
│   ├── raw/                   # dữ liệu nguồn bất biến
│   └── processed/             # dữ liệu dẫn xuất khi thực sự cần lưu
├── docs/
│   ├── plans/                 # project overview và implementation plan
│   ├── exercise_details/      # specification tùy chọn
│   ├── error_analysis/        # bằng chứng điều tra lỗi
│   ├── fix_plans/             # kế hoạch sửa lỗi đã duyệt
│   ├── status/                # trạng thái dự án khi được tạo
│   └── logs/                  # execution log có giá trị truy vết
├── notebooks/                 # điều phối, trình bày và diễn giải
├── src/practice_2/
│   ├── data/                  # load và validate dữ liệu
│   ├── analysis/              # statistical/modeling logic
│   └── visualization/         # reusable plotting logic
├── outputs/
│   ├── figures/               # biểu đồ export
│   └── results/               # CSV/JSON kết quả máy đọc được
├── tests/                     # kiểm thử reusable logic
├── pyproject.toml
└── README.md
```

Không tạo thư mục song song có cùng trách nhiệm nếu chưa được duyệt.

---

## 4. Quyền sở hữu dữ liệu

- `datasets/raw/a10.csv` là Dataset 1 cho E01–E05.
- `datasets/raw/airline-passengers.csv` là Dataset 2 cho E06.
- Raw files là source of truth và không được chỉnh sửa bởi notebook hoặc code.
- Parse, sort, differencing, split và transformation phải thực hiện trên object
  trong bộ nhớ hoặc artifact dẫn xuất có provenance rõ ràng.
- Không ghi đè raw data bằng cleaned, transformed hoặc forecast data.

Luồng dữ liệu chuẩn:

```text
raw data
→ schema/time-index validation
→ chronological working series
→ training/test boundary
→ training-only analysis and fitting
→ sealed test evaluation
→ verified outputs
```

---

## 5. Time-series và holdout boundary

Mọi xử lý phải bảo toàn chronological order, timestamp semantics, monthly
frequency, lag direction và missing/duplicate awareness.

Đối với E01–E05:

- E01 xác lập chronological split khoảng 80% train và 20% test;
- không shuffle;
- E02–E04 chỉ sử dụng training series;
- test set được mở ở E05 cho đánh giá cuối;
- preprocessing hoặc model selection không được học từ test set.

E06 phải tạo split riêng cho AirPassengers. ARIMA và SARIMA phải dùng cùng train,
test và forecast horizon để so sánh công bằng.

Bị cấm: future leakage, random split, silent interpolation/resampling, silent
timestamp repair và lựa chọn mô hình dựa trên test performance.

---

## 6. Ranh giới source code và notebook

Notebook sở hữu narrative, orchestration, bảng/biểu đồ trình bày và interpretation.
Reusable hoặc correctness-critical logic thuộc `src/practice_2/`.

Notebook và tests import qua package public, ví dụ:

```python
from practice_2.analysis import ...
```

Không dùng absolute machine path, `sys.path` mutation hoặc phụ thuộc hidden
notebook state. Notebook phải chạy tuần tự từ kernel sạch.

Hướng dependency được phép:

```text
notebooks → practice_2 package
tests → practice_2 package
practice_2.analysis → practice_2.data
practice_2.visualization → validated data/analysis objects
outputs ← execution
docs ← verified project state
```

Source package không được phụ thuộc notebook hoặc generated outputs.

---

## 7. Môi trường và dependency

`pyproject.toml` là nguồn chính thức cho package metadata, Python compatibility,
runtime và test dependencies. Local `.venv`, cache và notebook checkpoints không
được commit.

Môi trường phải đủ để tái tạo E01–E06. Việc thêm hoặc đổi dependency phải được
ghi rõ và kiểm tra import trước khi thực thi notebook.

---

## 8. Output và bằng chứng

- Biểu đồ export thuộc `outputs/figures/`.
- Bảng và machine-readable summaries thuộc `outputs/results/`.
- Notebook output hỗ trợ trình bày nhưng không thay thế source code hoặc test.
- Không ghi output giả, placeholder được trình bày như kết quả thật, hoặc số liệu
  chưa được tạo từ execution.
- Mỗi kết luận ADF, ACF/PACF, residual diagnostics và forecast metrics phải truy
  vết được về dữ liệu, tham số và code đã chạy.

---

## 9. Testing và validation

Ưu tiên test cho:

- schema, datetime parsing, chronological order và monthly continuity;
- train/test boundary và leakage prevention;
- differencing alignment;
- metric calculation và forecast-index alignment;
- reusable model/diagnostic helpers.

Không tạo test hình thức. Validation phải tương xứng với rủi ro khoa học.

---

## 10. Exercise và approval gates

Thứ tự core là E01 → E02 → E03 → E04 → E05. E06 là advanced extension độc lập
trên Dataset 2 và không thay thế trạng thái core.

Một Exercise chỉ bắt đầu khi scope tương ứng trong plan đã được Human duyệt,
input contract rõ ràng và upstream evidence sẵn có. File specification riêng là
tùy chọn; chỉ bắt buộc khi Human yêu cầu hoặc khi scope chưa đủ rõ trong plan.

Không chuyển Exercise khi output hoặc validation của Exercise trước chưa đạt.

---

## 11. Change control và stop conditions

Phải xin duyệt trước khi thay đổi dataset identity, split/evaluation protocol,
Exercise boundary, package ownership hoặc cấu trúc top-level.

Dừng triển khai nếu:

- schema hoặc timestamp không khớp input contract;
- xuất hiện leakage hay alignment không giải thích được;
- statistical/modeling protocol mơ hồ;
- kết quả không tái tạo được;
- rule hoặc approved plan xung đột.

---

## 12. Activation Gate

```text
ARCHITECTURE_RULE_CREATED=true
ARCHITECTURE_RULE_APPROVED=true
IMPLEMENTATION_GOVERNED_BY_THIS_RULE=true
```

Human approval recorded for Practice 2 architecture governance.
