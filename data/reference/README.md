# Reference data

| File | Origin | Notes |
|---|---|---|
| `events.csv` | Real PAGASA event names and dates, 2020–2025 | `affected_provinces`, `max_signal` and `severity_weight` are approximations that drive the synthetic generator. Rows with `verified = N` still need checking against PAGASA/NDRRMC records. |
| `organizations.csv` | Hand-curated | Canonical response organizations plus the name variants that sources use for them. |
| `resource_items.csv` | Hand-curated | Canonical relief items, standard units, indicative PHP unit costs, and partner item codes (`CODE:unit:factor`). |
| `psgc_api/*.json` | [PSGC community API](https://psgc.gitlab.io/api/), a public mirror of PSA codes | **Current source.** Cached, not committed. Loaded by `python ingestion/load_psgc_api.py`. Has no population figures. |
| `PSGC-*-Publication-Datafile.xlsx` | [PSA PSGC](https://psa.gov.ph/classification/psgc) | Optional official alternative with census population (`python ingestion/load_psgc.py`). Not committed; the PSA site blocks automated downloads. |
| `psgc_citymun.csv`, `psgc_barangay.csv` | Derived by either PSGC loader | Committed so the generator runs without network access. With the API source, `population` is an **estimate** (barangay count × 2,600, ×1.6 for cities, capped at 1M) used only to scale synthetic figures. |

**Known gap:** the API release predates the 2022 split of Maguindanao into Maguindanao del Norte and del Sur, so events use "Maguindanao". The split is a planned SCD Type 2 demonstration in `dim_location`.

All damage, evacuation, distribution and response **figures** in this project are synthetic.
