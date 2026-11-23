# Stage S2 — Canonical Hourly Data Contract (v2)

- **Canonical CSV:** `canonical_hourly.csv` (SHA256: `85c575e07cc1e7be7d913e882122360ba0f536c531227c0e9087a26ff1311542`)
- **Source UCI SHA256:** `d51565f2cb5a6b768d06ba1bbd3c084c6e2f3aab07f00c6f2dcb80e90175124b`
- **Source Weather SHA256:** `ed0e577dff8e93ae0a0eac31bafa2a5fde91325cb9b499e2b7308262267df19b`
- **Rows:** **26,304** contiguous 1-hour UTC steps (`2012-01-01T00:00:00+00:00` → `2014-12-31T23:00:00+00:00`)
- **Stable Client Cohort:** **321 / 370** clients active in Jan 2012 (eliminates 2011 onboarding step-jump).
- **DST Handling (`Europe/Lisbon`):** Spring-forward non-existent zero-padded local hour excluded naturally upon UTC mapping; Fall-back doubled local hour halved across its two UTC hours (`6` flagged hours).
- **Weather Proxy:** Population-weighted ERA5 mean (Lisbon 0.50, Porto 0.35, Coimbra 0.15). Physical anomaly hours: `0`.

| Column | Unit / Type | Range / Summary |
|---|---|---|
| `timestamp_utc` | ISO-8601 UTC (`1h`) | `2012-01-01T00:00:00+00:00` .. `2014-12-31T23:00:00+00:00` |
| `load` | kW (`float64`) | min `75,765.82`, mean `203,577.33`, max `446,935.42`, missing `0` |
| `temp` | °C (`float64`) | `0.39` .. `35.99` |
| `humidity` | % (`float64`) | `21.90` .. `100.00` |
| `wind_speed` | m/s (`float64`) | `0.30` .. `14.02` |
| `load_observed` | `bool` | Exact mask of observed raw target |
| `dst_fallback_split` | `bool` | Marks October fall-back split hours |
| `weather_physical_anomaly` | `bool` | Marks physical out-of-range weather hours |
