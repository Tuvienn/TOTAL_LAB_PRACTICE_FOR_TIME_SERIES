# Practice 4 — Kế hoạch theo cụm stage

Ngày soạn: **2026-11-17**. Revision: **R1**. Trạng thái: **PLANNING — DRAFT, CHỜ HUMAN REVIEW**.

Human cho phép soạn plan, file map và tối đa ba vòng subagent review. Quyền này cho phép cập nhật bộ tài liệu kế hoạch; không cho phép tải dataset, cài dependencies, triển khai pipeline hoặc huấn luyện. Điểm reviewer không thay thế Human approval.

## 1. Mục tiêu, phạm vi và hiện trạng

Hoàn thành multivariate one-step forecasting: lịch sử điện năng và thời tiết → điện năng giờ kế tiếp; so sánh VAR, XGBoost và LSTM bằng RMSE/MAE/MAPE. Dataset Spain **Hourly energy demand, generation and weather** là nguồn chính được tài liệu hiện có ghi nhận Human đã chọn. Chọn nguồn không xác nhận schema, đơn vị, weather aggregation hoặc missing-value policy.

Bản này thay thế roadmap cũ trong chính `plan_overview.md`, giữ thứ tự **Phase 0–10**, chia thành **9 cụm / 18 stage**. [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) giữ bối cảnh/lịch sử; [file_map.csv](file_map.csv) giữ đường dẫn/trách nhiệm; [plan_review.md](plan_review.md) giữ đánh giá. Stage dưới đây là work packages, không phải approved phase specifications. Chỉ thiết kế specification/before-process plan của phase đến lượt, không tạo trước tất cả.

Ngoài phạm vi: traffic METR-LA/PEMS-BAY, forecasting nhiều bước, web/deployment, model khác, Practice khác và rules chung. Mở rộng cần scope mới.

### 1.1 Hiện trạng kiểm tra trực tiếp

- Trước lần soạn: 23 file; bốn `__init__.py` chỉ có docstring; notebook template có 12 Markdown cells, 0 code cells.
- Không có raw/processed dataset, runnable tests, dependency manifest, training configuration, metrics hoặc execution evidence.
- PROJECT_OVERVIEW và current_status nói `LD2011_2014.txt` hiện có; inventory không thấy. Không suy diễn nguyên nhân/tự khôi phục.
- Mô tả cũ “chưa viết notebook” cần sửa thành “đã có template, chưa có executable/final notebook”. Giao A01 xử lý drift.
- Số dòng/missing từ preliminary inspection cũ chưa được tái lập; B01 đo lại từ version khóa.
- Trong lần này chỉ sửa ba file tại docs/plans; các thay đổi source/README/status trong roadmap là tương lai.

### 1.2 Truy vết yêu cầu từ đề [S1]

| ID | Yêu cầu | Trang | Owner |
|---|---|---|---|
| R01 | 4 biến load/temperature/humidity/wind_speed; lịch sử24h; dự báo load bước sau | 1–2 | A02, B02, E01 |
| R02 | Missing/outliers/daily-weekly seasonality; load plot, load–temperature, correlation | 1 | D01 |
| R03 | StandardScaler, temporal split70/15/15, không shuffle | 1–2 | C01, D02 |
| R04 | Lag24; XGB thêm mean6h, std24h, load(t)−load(t−24) | 2 | E01–E02 |
| R05 | VAR: ADF, differencing nếu cần, AIC/BIC; chấm riêng load | 2 | F02 |
| R06 | XGB: max_depth/n_estimators, validation early stopping | 2 | G01 |
| R07 | LSTM: (N,24,4),64→32→Dense1, MSE/Adam | 3 | G02 |
| R08 | Walk-forward cả3 model; RMSE/MAE/MAPE | 3 | C02, H01 |
| R09 | Sáu câu hỏi phân tích, so sánh kết quả | 3 | H02, I01–I02 |

## 2. Kiến trúc ownership và artifacts

File map dùng path tương đối Practice_4 root, dấu `/`. EXISTING=đã thấy lúc soạn; PLANNED=chưa tạo. FAMILY=tập file tên biến thiên, không phải file đã tồn tại. first_stage là lần tạo/chỉnh đầu tiên, không phải consumer duy nhất.

| Owner | Trách nhiệm | Ranh giới |
|---|---|---|
| src/practice_4/data/ | Ingest, canonical integration, split, causal preprocessing, model-ready data | Không fit model |
| src/practice_4/analysis/ | EDA, metrics, baselines, VAR/XGB/LSTM, walk-forward, error analysis | Không tải raw trong notebook |
| src/practice_4/visualization/ | Vẽ từ dữ liệu/artifacts được phép | Không tự fit/đổi split |
| src/practice_4/pipeline.py | CLI điều phối stage và xác nhận gates | Không duplicate thuật toán modules |
| config/ | Config được duyệt, protocol/seed/budget | Không secrets/absolute machine paths |
| datasets/raw/ | CSV nguồn bất biến | Không sửa/fill |
| datasets/processed/ | Derived datasets có lineage | Không ghi đè raw |
| runs/<run_id>/ | Config/environment snapshot, scaler/model/trials | Không tự thành official results |
| outputs/ | Official figures/tables/predictions từ accepted run | Không ghi đè ngầm |
| docs/phase_details/ | Phase specification + before-process plan đến lượt | Không tự duyệt phase sau |
| docs/results/, docs/logs/ | Kết luận, evidence và approval references | Không kết luận từ output chưa chạy |
| notebooks/ | Presentation approved artifacts ở Phase10 | Không download/fit/tuning lại |

Dependency direction: notebook → official artifacts; pipeline → data/analysis/visualization; analysis → data/metrics. Modules không import notebook/pipeline. CLI import model backends khi gọi model stage, để data/tests không buộc có DL backend.

Mỗi Phase n có một `docs/phase_details/phase_<nn>.md`: specification, before-process plan, impacted files, validation commands, stop conditions, approval record. Chỉ tạo khi phase đến lượt. Approval phải có người duyệt, ngày và tham chiếu message/record thật; thiếu thì gate đóng.

Mỗi stage có `docs/logs/<stage_id>_<run_id>.md` ghi config/input hashes, command, exit status, counts/checks, artifact paths, limitations. Mỗi run ID duy nhất, giữ failed runs. `runs/<run_id>/manifest.json` ghi run/stage/schema_version, input/config hashes, output checksums, environment và approval reference. Chỉ promote official outputs sau validation/Human review; promotion ghi source run/checksum, không sửa trial evidence.

## 3. Roadmap: 9 cụm, 18 stage

Chuỗi bắt buộc:

**A01 → A02 → B01 → B02 → C01 → C02 → D01 → D02 → E01 → E02 → F01 → F02 → G01 → G02 → H01 → H02 → I01 → I02**.

Predecessor phải đạt gate trước khi stage sau bắt đầu. Mỗi lần chuyển Phase phải có Human review phase cũ + approved specification/before-process plan phase mới. D01→D02, F02→G01, G01→G02 cũng là chuyển phase dù chung cụm. Hiện tất cả stage NOT_STARTED; chỉ một implementation stage IN_PROGRESS tại một thời điểm.

### Cụm A — Bài toán và nền tảng dự án (Phase 0)

| Stage | Input và việc cần làm | Output / owner | Tiêu chí đạt |
|---|---|---|---|
| A01 — Scope và ownership | Đề/rules/overview/inventory; sửa drift; review file map và module owners | phase_00 specification; cập nhật overview/README/status; architecture approval trong phase_00 | Human duyệt scope, dataset source, R01–R09, map; không còn mô tả file tồn tại sai |
| A02 — Problem Definition | A01 accepted; định nghĩa5W1H, provisional I/O/origin, success criteria, risk/decision register | docs/results/problem_definition.md | Human duyệt; phân biệt requirement/proposal/việc phải đo; không xử lý dữ liệu |

Gate A chỉ tài liệu: không tải CSV, checksum raw, cài package, split hay training. Thành công là thực nghiệm đúng protocol và giải thích có bằng chứng; không bắt buộc model phức tạp thắng baseline.

### Cụm B — Nguồn dữ liệu và tích hợp (Phase 1)

| Stage | Input và việc cần làm | Output / owner | Tiêu chí đạt |
|---|---|---|---|
| B01 — Raw provenance và audit | Problem Definition; duyệt dependency setup trước tạo pyproject/lock/config/CLI; lấy2CSV Spain, kiểm version/license/retrieval/checksum/schema/unit/timezone/gaps/city-hour duplicates | data/ingestion.py; pyproject.toml, requirements.lock.txt, config/practice_4.json, pipeline.py; raw CSV/source_manifest.json; docs/results/data_audit.md | Clean-env import/smoke; raw unchanged; có unit/source evidence; đo lại counts/missing, không dùng số cũ |
| B02 — Canonical contract | Audit; thiết kế/duyệt dedup, city normalization, weather proxy, hourly timestamp join; derived copy | data/integration.py; canonical_hourly.csv; docs/results/data_contract.md | UTC sorted unique step1h; join không nhân dòng; coverage/units rõ; giữ missing load; Human duyệt contract |

Đề xuất weather proxy=mean không trọng số các thành phố, chỉ áp sau kiểm duplicate consistency và coverage. Nếu weather duplicates xung đột, thiếu coverage/unit: dừng B02, chuẩn bị policy/evidence cho Human; không tự lấy dòng đầu/mean conflict/fill. UTC là index đề xuất; daily/weekly interpretation dùng timezone địa phương đã kiểm chứng. B audit metadata/quality toàn raw, chưa EDA relationships hoặc chọn treatment từ held-out distributions.

### Cụm C — Thiết kế thực nghiệm và đánh giá (Phase 2)

| Stage | Input và việc cần làm | Output / owner | Tiêu chí đạt |
|---|---|---|---|
| C01 — Temporal partition | Canonical; split row timeline trước drop/window: train=floor(.70N),val=floor(.15N),test=phần còn lại; lưu inclusive boundaries/counts | data/splitting.py; split_manifest.json | Không overlap/mất timestamp; sum=N; split hash khóa; target timestamp quyết định sample membership |
| C02 — Evaluation contract | C01; khóa origin eligibility, context boundary, update/refit, metric/tie/MAPE và budgets; hand-check fixtures | analysis/metrics.py, analysis/walk_forward.py; evaluation_contract.md; tests metrics/walk-forward | Human duyệt trước modeling; fixtures xác minh prediction-before-reveal, masks/original-scale metrics; chưa mở test cho selection |

Eligibility rule khóa ở C02; E02 hiện thực train/validation origins sau D02 theo cùng rule, không dựa model errors. Test origin list materialize sau authorization H01.

### Cụm D — Hiểu và chuẩn bị dữ liệu (Phase 3–4)

| Stage | Input và việc cần làm | Output / owner | Tiêu chí đạt |
|---|---|---|---|
| D01 — Training-only EDA (P3) | Train và raw audit; missing/outliers, daily-weekly profiles, load–temp, correlation/temporal dependence | analysis/eda.py, visualization/plots.py; EDA figures, eda_findings.md | Inspect figures; findings có artifact/config; không causal claim; timezone rõ; Human review treatment proposals |
| D02 — Causal preprocessing (P4) | EDA accepted; duyệt missing/anomaly/max-gap/contiguous-VAR policy; StandardScaler fit chỉ train | data/preprocessing.py; prepared_hourly.csv; scaler/state trong run; preprocessing_audit.md | Raw truth/mask bất biến; không điền scoring labels; train cutoff đúng; scan causal; không bfill/two-sided interpolation; inverse-scale fixture đạt tolerance đã khóa |

Giữ riêng `load_observed` và working `load_input`. Input/VAR training có thể dùng causal filling nếu policy được duyệt và bias/counts được ghi; imputed label không thành truth. Không tự xóa outlier có thật hoặc drop hàng giữa để giả VAR hourly. Nếu không có contiguous train domain đủ dài: dừng, trình phương án giữ block liên tục hoặc đổi policy. Fit-range khác biệt phải được báo trong comparison; downstream chỉ chạy sau approval.

### Cụm E — Feature và model-ready inputs (Phase 5)

| Stage | Input và việc cần làm | Output / owner | Tiêu chí đạt |
|---|---|---|---|
| E01 — Feature dictionary | Prepared + protocol; khóa tên/order/timestamp, lag/rolling/trend/target; synthetic ramp fixtures | data/features.py; feature_dictionary.md; feature tests | Đúng24observations; trend lag24 thật; mọi source timestamp≤origin; hand-check chống off-by-one |
| E02 — Aligned inputs | E01; sequences, flat features, VAR contiguous vector; common eligibility/masks/timestamps | model_inputs.npz, origin_manifest.csv; alignment_audit.md | LSTM(N,24,4), XGB96lags+3derived=99 theo đề xuất; cùng targets/rawtruth/origins; exclusions có reason/count; Human review |

E02 chỉ lưu train/validation arrays và schema/rule cho test. Không materialize full test tensors trước H01. XGB/LSTM chỉ fit samples có observed training labels; historic context có thể qua boundary khi hợp lệ. Không đổi chronology để ép shapes.

### Cụm F — Baselines và thống kê (Phase 6)

| Stage | Input và việc cần làm | Output / owner | Tiêu chí đạt |
|---|---|---|---|
| F01 — Simple baselines | E02; shared validation metrics/walk-forward; persistence yhat(t+1)=load(t), seasonal24 yhat(t+1)=load(t−23) | analysis/baselines.py; validation predictions/metrics trong run | Formula hand-check; causal history; original scale; đủ2baseline trước model phức tạp |
| F02 — VAR | Baseline+E02; train-only ADF, d∈{0,1}, p∈1..24 bằng AIC hoặc BIC đã chọn trong config; forecast vector rồi inverse-diff/scale và lấy load | analysis/var_model.py; state/ADF/lag/diagnostics; var_findings.md | Không chọn từ test; inverse fixture đúng; report stationarity/stability/residual limitations; Human review/lock model hash |

Không tự tăng d, seasonal difference hoặc thay model khi assumptions/singular matrix fail. Ghi failure evidence, trình phương án. Không thắng baseline vẫn là kết quả hợp lệ nếu protocol đúng.

### Cụm G — Mô hình phi tuyến ML/DL (Phase 7–8)

| Stage | Input và việc cần làm | Output / owner | Tiêu chí đạt |
|---|---|---|---|
| G01 — XGBoost (P7) | Finite grid max_depth/n_estimators, validation early stop; weather-vs-load-only ablation cùng origins/budget | analysis/xgboost_model.py; trials/booster/predictions; xgboost_findings.md | Budget trước fit; no shuffle; saved best_iteration khớp predictions; ablation chỉ validation; Human lock |
| G02 — LSTM (P8) | Sequences; LSTM64 return_sequences=True → LSTM32 → Dense1; MSE/Adam, shuffle=False, early stop val_loss/restore_best_weights | analysis/lstm_model.py; model/history/seeds/metrics; lstm_findings.md | Architecture/shape đúng; no test early stop; saved checkpoint tái lập trong tolerance; overfit evidence; Human lock |

Backend/version/hardware compatibility phải được duyệt trong design trước cài/fit. Finite candidates, seeds, epochs/patience/lr/batch/resource budget ghi trước chạy. Đề xuất official seed42; seed khác chỉ robustness đã duyệt, không chọn seed tốt nhất. Hết budget thì báo limitation, không âm thầm mở rộng search.

### Cụm H — Final evaluation và giải thích (Phase 9)

| Stage | Input và việc cần làm | Output / owner | Tiêu chí đạt |
|---|---|---|---|
| H01 — Test-opening/walk-forward | Human duyệt lock của2baseline+3model, preprocessor/config hashes; materialize test tại từng origin, predict trước reveal; metrics/promote | analysis/walk_forward.py; official predictions.csv, metrics.csv, evaluation_manifest.json | Không tuning/refit; đủ5models cùng origins/rawtruth; missing truth không chấm; masks/counts/hashes khớp; nonfinite forecast=fail |
| H02 — Error analysis | Official predictions; error theo hour/day/season/peak/weather; bins train-defined; actual/predicted/residual plots | analysis/error_analysis.py; model_comparison.md và figures | Claim có artifact; không chọn lại config từ test; bug→invalidate run, trình fix scope, giữ run cũ |

### Cụm I — Bàn giao và tái lập (Phase 10)

| Stage | Input và việc cần làm | Output / owner | Tiêu chí đạt |
|---|---|---|---|
| I01 — Notebook/report | Approved P0–9 artifacts, phase-by-phase evidence, sáu câu hỏi | practice_4_end_to_end.ipynb; final_report.md | Chỉ đọc official artifacts; không fit/download/duplicate pipeline; limitations weather/window/metrics rõ |
| I02 — Reproduction/handoff | Locks/hashes/manifests; chạy presentation từ local accepted artifacts, deterministic fixtures | README/status/file-map updates; docs/logs/reproduction.md | Clean-env commands; notebook run-all offline đọc artifacts; raw unchanged; Human nghiệm thu |

I02 không tự rerun training/test. Scientific replay cần approval riêng, run ID mới và locked protocol; không dùng rerun để tuning sau test.

## 4. Contract đề xuất cần khóa ở gate tương ứng

Tất cả lựa chọn thiết kế phần này là **ĐỀ XUẤT**, chưa phải đã được Human phê duyệt hoặc đã kiểm chứng. Khi duyệt ghi version trong config/contract.

### 4.1 Indexing, context và fairness

Origin t là cuối giờ đã quan sát; `[X(t−23),…,X(t)] → load(t+1)` có24hourly rows. Trend XGB `load(t)−load(t−24)` cần25rows; giữ công thức đề. LSTM vẫn24rows/4vars; XGB có derived features theo đề. Report khác biệt information set này, không claim exact feature parity.

Đề xuất mean load(t−5:t), std load(t−23:t), ddof0, tính trên train-scaled working load; flatten time-major, variable order [load,temperature,humidity,wind_speed]. Không dùng weather(t+1). E01 khóa bằng hand-check fixture.

VAR d≤1,p≤24 có thể cần25rawrows cho24differences. Common warm-up đề xuất25 cho mọi model; nếu F02 đổi requirement thì quay C02/E02 xin duyệt, rebuild manifests trước dependent fits. Target timestamp quyết định split; context≤origin có thể qua boundary. Báo cả raw row ratios và sample counts sau masks.

### 4.2 Validation/test và cập nhật thông tin

Đề xuất rolling-origin one-step với **fixed weights, fixed train-fitted transformations**, không refit train+val trước test. Mỗi bước: history đã reveal → predict → score nếu raw target observed → reveal observation cho bước sau. Không đưa forecast thay truth vào history trong protocol chính. Weather/load được giả định có ngay cuối giờ; đây là lab availability assumption, không claim production-ready.

Validation: fit train, chọn hyperparameters/early stopping từ val, cùng history semantics. Test không dùng EDA/tuning; transform test causal chỉ sau H01. B được audit toàn raw schema/missing coverage; C01 dùng timestamps/counts; không dùng held-out target distributions/correlation chọn treatment/model.

Common mask: raw target observed AND đủ causal input context theo approved policy. Tất cả models phải forecast được trên cùng origin set; model failure/nonfinite **không** được silently drop để giao lại common mask mà làm H01 fail. Eligibility quyết định trước scoring, không theo errors. Missing truth/input exclusions có reason/count; zero eligible points=fail. Model-specific training exclusions công bố.

### 4.3 Metrics/selection

Original verified load unit: MAE=mean(abs(y−yhat)); RMSE=sqrt(mean((y−yhat)^2)); MAPE=100×mean(abs((y−yhat)/y)) trên y≠0. Báo n_scored/n_zero_excluded/n_missing_excluded/n_input_excluded. All scored y=0→MAPE=NA có lý do; không epsilon bí mật. Near-zero sensitivity báo riêng, không đổi threshold sau test.

Đề xuất primary=validation RMSE; nếu abs(deltaRMSE)≤1e−6 load unit dùng MAE; vẫn hòa ưu tiên persistence→seasonal24→VAR→XGB→LSTM. Trials cùng model hòa thì ít parameters/trees/epochs hơn rồi trial_id nhỏ hơn. MAPE bổ sung. C02 khóa trước fit; report test ranking chỉ mô tả, không chọn lại configuration từ test.

### 4.4 Missing và inverse transforms

Raw truth/mask bất biến; D02 chỉ chọn causal max-gap/anomaly policy từ train EDA rồi Human duyệt. Không impute labels để scoring. StandardScaler fit train working four-var levels; val/test dùng cùng state. F02 lưu d-map cho từng biến; differences trên scaled levels được inverse-diff với last prepared history về scaled level rồi inverse-scale về unit gốc. d0 không cộng history. Kiểm bằng numerical fixture. Không clip predictions âm/đổi unit ngầm.

## 5. Decision register

| ID | Quyết định | Owner / deadline | Evidence / block |
|---|---|---|---|
| Q01 | Source Spain thay UCI, scope/R01–09, owners/map | A01–A02 trước B01 | Existing decision record + Human approval; UCI không đủ weather[S2] |
| Q02 | Archive/license/units/timestamp availability | B01 trước B02 | Source manifest/unit evidence; chưa rõ→block |
| Q03 | Dedup/proxy/timezone/DST/join | B02 trước canonical release | Audit+policy+Human; không lấy số cũ làm evidence |
| Q04 | Split rounding/context/common eligibility rule | C01–C02 trước D01 | Toy timeline, boundary/nonoverlap tests |
| Q05 | Update/refit/metrics/MAPE/ties và budgets | C02 trước F01 | Approved evaluation contract; không để đến test mới chọn |
| Q06 | Missing/anomaly/max-gap/VAR contiguous domain | D02 trước E01 | Train-only EDA+causal fixtures |
| Q07 | Exact24rows/extra trend context/order/ddof | E01 trước samples | Approved dictionary+ramp fixtures |
| Q08 | ADF options/d-map/lag criterion/search bound | F02 design trước fit | Train diagnostics/finite candidates |
| Q09 | XGB trials/early stop, LSTM backend/hyperparams/seeds/budget | G01/G02 design trước fit | Compatibility+approved finite trial registry |
| Q10 | Model lock/test access/eligibility version | H01 trước test scoring | Model+config hashes/Human approval; thiếu model→block |

Không ép Human đoán Q02/Q03/Q06 trước audit. Stage phải chuẩn bị evidence và alternatives cho review. Thay upstream locked contract→change request, xác định downstream invalidation, xin duyệt rebuild; không dùng mixed artifact versions.

## 6. Validation và execution

### 6.1 Interface dự kiến, chưa có code

B01 mới tạo CLI sau approved phase design:

```text
python -m pip install -r requirements.lock.txt
python -m pip install --no-deps -e .
python -m pytest tests/test_ingestion.py tests/test_pipeline.py
python -m practice_4.pipeline --stage B01 --config config/practice_4.json --run-id <unique_id>
```

Lệnh từ Practice_4 root trong env đã tạo. CLI nhận từng execution stage thuộc B01–I02 ở mục3, từ chối ID không map; A01/A02 là documentation review. Trước run xác nhận phase approval/predecessor manifest/input hashes, không tự ghi approved=true. Exact validation commands thuộc phase specification khi source đến lượt, không pretend chúng đang chạy được hôm nay.

B01 pin Python/package/backend versions đã kiểm tra, dependency resolution, CPU/GPU và env commands; /stable/ docs không phải version pin. Data fixture tests không cần DL backend. Tests trọng tâm: DST/duplicate conflicts/join cardinality/split boundary/causal filling/feature offset/inverse transforms/streaming reveal/metric masks. Model smoke train-save-load-predict trên tiny train-only fixtures; không dùng test thật.

### 6.2 Gate chung

1. Approved current-phase specification/before-process plan, predecessor accepted, scope/file map đúng.
2. Relevant tests/commands thành công; inspect schema/shapes/time boundaries và figures.
3. Raw checksum trước/sau data work; git diff --check khi đổi tracked files.
4. Log/manifest/limitations/approval references; cập nhật status/map khi file đã tạo thật.
5. Human review trước chuyển Phase; static inspection không là model-execution evidence.

Stop: rules conflict, source license/unit/schema unclear, input hash drift, causal availability violated, unapproved dependency, unexplained test fail, quality case chưa có policy, hoặc hết budget. Không đổi dataset/method/treatment âm thầm. Giữ failed run; ba materially similar failures theo repository escalation.

## 7. Evidence trả lời sáu câu hỏi

| Câu hỏi | Evidence | Owner |
|---|---|---|
| Weather nào liên hệ mạnh nhất? | Train relationships+validation ablation; predictive association không causality | D01,G01,H02 |
| VAR thất bại khi nào? | ADF/stability/residuals/error regimes so baseline | F02,H02 |
| XGB học gì từ weather? | Load-only vs weather validation ablation, ranking có correlation limitations | G01 |
| LSTM học ngày/tuần? | Train profiles/held-out temporal errors; có thể kết luận chưa đủ evidence tuần | D01,G02,H02 |
| LSTM overfit? | Train/val curves, gap/best checkpoint | G02 |
| ML và DL khác gì? | Original-scale metrics/input structure/run time/hardware/budget/interpretability | G01–I02 |

Không bắt buộc LSTM thắng hoặc học tuần. Kết luận âm tính có evidence vẫn hợp lệ.

## 8. Nguồn tham khảo để lập kế hoạch

Web sources mở ngày **2026-11-17**. Fixed weights, weather mean, warm-up25 và thresholds là đề xuất của plan, không phải quy định nguyên văn của sources.

| ID | Nguồn | Dùng cho phần nào / giới hạn |
|---|---|---|
| S1 | [Đề Practice4](../../../../references/practice%204.pdf),trang1–3 | R01–R09; indexing/walk-forward có ambiguity cần contract |
| S2 | [UCI ElectricityLoadDiagrams](https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014) | 370clients/15min; xác định mismatch dataset bốn biến theo giờ |
| S3 | [Spain energy/weather — tác giả Kaggle](https://www.kaggle.com/datasets/nicholasjhana/energy-consumption-generation-prices-and-weather) | Link nguồn repo chọn; mở được nhưng không readable body lần này; archive/version/license/units chưa kiểm, giao B01 |
| S4 | [pandas time series](https://pandas.pydata.org/docs/user_guide/timeseries.html) | Parsing/timezone/DST/frequency B; không tự quyết raw policy |
| S5 | [scikit-learn pitfalls12.2](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage) | Split trước learned preprocessing, train-only fit ở C/D |
| S6 | [statsmodels VAR](https://www.statsmodels.org/stable/vector_ar.html) | Stationarity/lag/forecast/diagnostics F02; không chứng minh data này stationary |
| S7 | [XGBoost Early Stopping](https://xgboost.readthedocs.io/en/stable/python/sklearn_estimator.html#early-stopping) | Validation eval_set/best iteration G01. Không copy random split/test-named eval_set của ví dụ docs |
| S8 | [Keras LSTM](https://keras.io/api/layers/recurrent_layers/lstm/),[EarlyStopping](https://keras.io/api/callbacks/early_stopping/) | Stacked output/checkpoint G02; chưa pin backend/version |
| S9 | [Forecasting: Principles and Practice,chương5](https://otexts.com/fpp3/toolbox.html) | 5.2 naive/seasonal;5.8 accuracy;5.10 rolling-origin C/F/H; links tscv/accuracy cũ redirect về đây |
| S10 | [AGENTS](../../../../AGENTS.md),[working_rule](../../../../working_rule.md),[RULES_INDEX](../../../../.agents/RULES_INDEX.md) | Governance/approval/scope/routing |
| S11 | [GENERAL](../../../../.agents/rules/GENERAL_RULES.md),[CODE](../../../../.agents/rules/CODE_RULES.md),[TIME_SERIES](../../../../.agents/rules/TIME_SERIES_RULES.md),[WORKFLOW](../../../../.agents/workflows/WORKFLOW.md) | Stage gates/raw integrity/chronology/baseline/evidence |
| S12 | [PROJECT_OVERVIEW](PROJECT_OVERVIEW.md),[notebooks README](../../notebooks/README.md) | Source selection/Phase0–10/presentation-only notebook; drift mục1.1 giao A01 |

## 9. Chấm độc lập tối đa ba vòng

Một reviewer subagent chấm plan+map theo đề/rules; main sửa trong scope. Một vòng=reviewer chấm một revision đã lưu. Startup và main CSV checks không tính vòng; không đổi rubric để lấy điểm.

- 1: rời rạc, thiếu architecture/cohesion/info.
- 5: đủ thông tin nhưng ambiguous để thực thi.
- 8: ổn nhưng còn flaws cần giải quyết trước thực hiện.
- >8: đủ rõ đường đi/architecture để tiếp tục approval gates; không phải implementation approval.
- 10: đầy đủ/nhất quán/truy vết tốt; không hứa hết rủi ro thực nghiệm.

Năm tiêu chí tối đa2đ mỗi tiêu chí: coverage/source fidelity; architecture/cohesion/file ownership; dependency/I-O/acceptance; scientific correctness/leakage/evaluation; reproducibility/decision closure. Tổng1–10, có thập phân. Blocker chronology/test leakage/ownership conflict→tối đa8 cho đến khi giải quyết.

Lưu điểm/findings thực nhận, revision và SHA256 plan/map trong plan_review.md. **Score>8 có thể dừng; score≤8 sửa rồi chấm lại; hết vòng3 luôn dừng**, còn issues thì báo rõ. Substantive edit sau lần chấm cuối làm điểm chỉ áp dụng revision cũ, phải công bố chưa re-review; không chạy vòng4.

## 10. Acceptance của lần soạn này

- Có9cụm/18stage, ánh xạ đủ Phase0–10 và R01–R09.
- File map phủ toàn existing files và planned owners, lifecycle/dependencies/verification; không gán PLANNED thành EXISTING.
- Sources có link/mục đích/mức kiểm; không bịa data/performance.
- Có1–3vòng review thực tế và stop đúng rule.
- CSV parse được; paths unique/relative; inventory coverage100%; stage IDs/dependencies không dangling; local links tồn tại hoặc mapped PLANNED.
- Chỉ thay docs/plans/plan_overview.md, file_map.csv, plan_review.md; không triển khai source/data/tests.

Change R1: roadmap theo cụm stage, thêm contracts/ownership/references/review loop. Reason: skeleton cần đường đi truy vết. Impact: chỉ planning documents, chưa data/model execution.
