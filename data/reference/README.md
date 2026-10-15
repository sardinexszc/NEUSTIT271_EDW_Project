# Reference data

| File | Origin | Notes |
|---|---|---|
| `events.csv` | Real PAGASA event names and dates, 2020–2025 | `affected_provinces`, `max_signal` and `severity_weight` are approximations that drive the synthetic generator. Rows with `verified = N` still need checking against PAGASA/NDRRMC records. |
| `organizations.csv` | Hand-curated | Canonical response organizations plus the name variants that sources use for them. |
| `resource_items.csv` | Hand-curated | Canonical relief items, standard units, indicative PHP unit costs, and partner item codes (`CODE:unit:factor`). |
| `PSGC-*-Publication-Datafile.xlsx` | [PSA PSGC](https://psa.gov.ph/classification/psgc) | **Not committed** (download manually; the PSA site blocks automated downloads). Load it with `python ingestion/load_psgc.py`. |
| `psgc_citymun.csv`, `psgc_barangay.csv` | Derived from the PSA workbook by `load_psgc.py` | Committed so the generator runs without the workbook. |

All damage, evacuation, distribution and response **figures** in this project are synthetic.
