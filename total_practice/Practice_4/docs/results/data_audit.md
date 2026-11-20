# B01 — Raw provenance và data audit

Run: `20261118_system312_01`. Trạng thái: **PENDING HUMAN REVIEW**.

Nguồn, version 1, CC0, ngày tải 2026-11-17, units và timestamp semantics do Human xác nhận; Kaggle page/API metadata không đọc được trong môi trường này. Không khẳng định đã xác minh độc lập archive. Nguồn upstream theo Human: ENTSO-E Transparency Platform và OpenWeatherMap API.

## Raw quality

- Energy: 35064 rows, 29 columns, UTC 2014-12-31 23:00:00+00:00 đến 2018-12-31 22:00:00+00:00; 35064 timestamps duy nhất, 0 missing hours, 0 duplicate timestamps; ordered=True.
- Weather: 178396 rows, 17 columns, UTC 2014-12-31 23:00:00+00:00 đến 2018-12-31 22:00:00+00:00; 21 duplicate full rows, 2798 duplicate city-hour groups, 3076 extra rows, 0 groups xung đột trong ba weather variables.
- Missing: `total load actual` 36; temp 0, humidity 0, wind_speed 0.

| Trường | Min | Max | Unit Human xác nhận | Basic range check |
|---|---:|---:|---|---|
| total load actual | 18041.0 | 41015.0 | MW | True |
| temp | 262.24 | 315.6 | K | True |
| humidity | 0.0 | 100.0 | % | True |
| wind_speed | 0.0 | 133.0 | m/s | True |

Basic checks chỉ kiểm load/wind không âm, Kelvin dương và humidity 0–100; không chứng minh đơn vị hoặc xác nhận outlier. Nhiệt độ tối đa 315,6 K cao hơn mốc xấp xỉ 315 trong yêu cầu; wind speed tối đa cần review vì nonnegative không chứng minh hợp lý.

## City coverage

| City label gốc | Rows | Unique timestamps | Thiếu so với energy | Thừa so với energy |
|---|---:|---:|---:|---:|
| ` Barcelona` | 35476 | 35064 | 0 | 0 |
| `Bilbao` | 35951 | 35064 | 0 | 0 |
| `Madrid` | 36267 | 35064 | 0 | 0 |
| `Seville` | 35557 | 35064 | 0 | 0 |
| `Valencia` | 35145 | 35064 | 0 | 0 |

## B02 policy proposals — CHỜ HUMAN DUYỆT

- Strip whitespace city names trên derived copy; kiểm tra va chạm tên.
- Deduplicate city-hour chỉ sau khi xác nhận các biến bắt buộc nhất quán; dừng nếu có conflict, không tự chọn first row khi conflict.
- Unweighted mean của năm city làm national weather proxy; nêu giới hạn đại diện.
- Parse explicit offsets sang UTC và align hourly bằng join đã kiểm cardinality/coverage.
- Giữ nguyên missing `total load actual` và observed mask; không impute truth.

Chưa thực hiện B02, tạo canonical hoặc phê duyệt policy. Counts, columns, missing và hashes đầy đủ trong run artifacts. UTC parsing không tự chứng minh timezone nguồn; semantics do Human xác nhận.
