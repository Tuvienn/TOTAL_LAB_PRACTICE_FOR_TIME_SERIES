# Phase 1 — Canonical data contract

Trạng thái: **APPROVED / COMPLETED**, B02 run `20261118_system312_b02_01`.
Human duyệt B02, canonical dataset, data contract và Phase 1 ngày 2026-11-18
qua yêu cầu `Close Phase 1 (Gate B02) & Draft Phase 2 Specification`. Header này
được cập nhật sau run; B02 manifest giữ hash contract tại thời điểm execution.

## Nguồn và lineage

Human cung cấp dataset Kaggle version 1, ngày tải 2026-11-17, CC0; upstream
được Human xác nhận là ENTSO-E Transparency Platform và OpenWeatherMap. Metadata
Kaggle và archive hash chưa kiểm chứng độc lập. Hash raw SHA256: energy
`14cd13e020d87af0ab49db8e0f1e4d308320ec5b8d2dec23bab4d27c75c7733a`, weather
`3566c3c21179d4fc6691eec6d37a6cfe8fe6a4d9e097f95e4fda4a29dc683b18`. Tất cả raw CSV bất biến.
Source manifest và B01 manifest được xác thực hash trước B02; run manifest B02
ghi config, inputs, outputs và hashes. Giá trị đầu vào đo được và artifacts này
không phải evidence cho model hoặc kết luận nhân quả.

## Schema và timestamp

CSV `datasets/processed/canonical_hourly.csv` có 35064 rows,
được sắp tăng, unique, liên tục 1 giờ UTC từ 2014-12-31 23:00:00+00:00 tới
2018-12-31 22:00:00+00:00. Timestamps nguồn có explicit offset; parse về UTC
trước join. Source timezone/DST và units theo xác nhận Human.

| Column | Ý nghĩa | Unit / kiểu |
|---|---|---|
| `timestamp_utc` | Thời điểm quan sát theo offset UTC | ISO 8601 UTC |
| `load` | `total load actual` gốc | MW; numeric hoặc missing |
| `temp` | Mean unweighted của 5 city | K; numeric |
| `humidity` | Mean unweighted của 5 city | %; numeric |
| `wind_speed` | Mean unweighted của 5 city | m/s; numeric |
| `load_observed` | `load` có quan sát | Boolean `True`/`False` |

`load` có 36 missing values, CSV biểu diễn bằng empty field;
mask là False đúng tại các hàng này. Không impute, filter, clip hay scale.

## Policy và kiểm tra

City labels được strip leading/trailing whitespace trên derived copy; exact set
là Madrid, Barcelona, Valencia, Seville, Bilbao. Mỗi city-hour chỉ deduplicate
sau kiểm tra temp/humidity/wind_speed đồng nhất, fail nếu conflict; đã bỏ
3076 duplicate rows khỏi bản làm việc.
Sau kiểm coverage 5 city mỗi giờ, tính mean không trọng số và 1:1 join với
35064 energy rows; output 35064 rows.
Source weather có 178396 rows.

Unweighted mean không đại diện chính xác phân bố dân số, phụ tải hay địa lý
toàn quốc; cần diễn giải như weather proxy, không suy luận quan hệ nhân quả.
Raw wind_speed max 133.0 m/s và temp max
315.6 K được giữ nguyên trong input và phép mean; wind_speed
133 m/s là raw extreme cần D01 training-only EDA và D02 causal anomaly policy,
không tự xác định là lỗi. Một raw extreme có thể không xuất hiện nguyên giá trị
trong proxy vì proxy là mean. Không có split, scaling, imputation hoặc clipping.
