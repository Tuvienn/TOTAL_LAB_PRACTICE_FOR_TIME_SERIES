# Stage S1 — Raw Provenance & Data Quality Audit (v2)

- **Dataset:** UCI ElectricityLoadDiagrams20112014 + Open-Meteo ERA5 Portugal
- **UCI URL:** https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip (`CC BY 4.0`)
- **UCI Archive SHA256:** `f6c4d0e0df12ecdb9ea008dd6eef3518adb52c559d04a9bac2e1b81dcfc8d4e1`
- **UCI `LD2011_2014.txt` SHA256:** `d51565f2cb5a6b768d06ba1bbd3c084c6e2f3aab07f00c6f2dcb80e90175124b`
- **Weather Source:** Open-Meteo ERA5 Historical Archive (`CC BY 4.0 (ECMWF ERA5 via Open-Meteo)`)
- **Weather CSV SHA256:** `ed0e577dff8e93ae0a0eac31bafa2a5fde91325cb9b499e2b7308262267df19b`

## 1. UCI ElectricityLoadDiagrams20112014 Raw Quality

- Rows: **140,256** (15-min intervals), Clients: **370**
- Local span: `2011-01-01 00:15:00` → `2015-01-01 00:00:00`
- Ordered: `True`, Duplicate timestamps: `0`
- Missing cells: `0`, Negative cells: `0`
- Total active power (kW): min `342.60`, mean `195,556.94`, max `452,652.60`

### Active Clients by Year (Onboarding Regime Check)

| Year | 15-min Rows | Min Active | Median Active | Max Active | Mean Total kW | Zero-Total Rows |
|---:|---:|---:|---:|---:|---:|---:|
| 2011 | 35,039 | 155 | 158.0 | 160 | 122,716.7 | 0 |
| 2012 | 35,136 | 119 | 323.0 | 332 | 212,317.4 | 0 |
| 2013 | 35,040 | 128 | 336.0 | 349 | 222,736.8 | 0 |
| 2014 | 35,040 | 117 | 364.0 | 369 | 224,410.9 | 0 |
| 2015 | 1 | 367 | 367.0 | 367 | 124,214.2 | 0 |

## 2. Open-Meteo ERA5 Portugal Weather Raw Quality

- Rows: **105,264** (`2011-01-01T00:00:00+00:00` → `2015-01-01T23:00:00+00:00`), Duplicate city-hour: `0`

| Variable | Min | Max | Unit | Physical Bounds Pass |
|---|---:|---:|---|---|
| `temp_c` | -2.900 | 39.300 | °C | `True` |
| `humidity` | 14.000 | 100.000 | % | `True` |
| `wind_speed` | 0.000 | 16.020 | m/s | `True` |

| City | Weight | Rows | Unique Timestamps | Missing (T/H/W) |
|---|---:|---:|---:|---|
| Coimbra | 0.15 | 35,088 | 35,088 | 0/0/0 |
| Lisbon | 0.50 | 35,088 | 35,088 | 0/0/0 |
| Porto | 0.35 | 35,088 | 35,088 | 0/0/0 |
