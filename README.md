# Disaster Response Intelligence Warehouse (DRIW)

IT271 Enterprise Data Warehousing project by Ivan Christian Salinas.

An enterprise data warehouse that integrates fragmented disaster-response data
(damage reports, evacuation-center occupancy, relief distribution, response logs and
weather-event bulletins) into one dimensional model for impact, response, evacuation
and logistics analytics. Scope: tropical cyclones and monsoon floods in the
Philippines, 2020–2025.

> **Data notice.** Event names/dates and PSGC geography are real. All damage, evacuation,
> distribution and response figures are **synthetic**, generated for demonstration.

## Architecture

```
 5 simulated source systems          PostgreSQL 17 (local → Supabase)                  Presentation
 ┌───────────────────────┐   extract  ┌─────┐  dbt   ┌─────────┐  dbt  ┌────┐  dbt  ┌──────┐   Next.js
 │ NDRRMC sitreps (CSV)  │ ─────────▶ │ raw │ ─────▶ │ staging │ ────▶ │ dw │ ────▶ │ mart │ ─▶ dashboards
 │ DSWD DROMIC (Excel)   │            └─────┘        └─────────┘       └────┘       └──────┘   (Vercel)
 │ NGO distribution(JSON)│               │            data-quality       star        ROLAP
 │ PAGASA bulletins (CSV)│               │            rules → dq.*       schema      aggregates
 │ LGU response logs(CSV)│           meta.load_batch (lineage)          ref.* (PSGC, aliases)
 └───────────────────────┘
```

| Layer | Schema | Built by |
|---|---|---|
| Landing zone (as received, all text) | `raw` | `ingestion/load_raw.py` |
| Master data: PSGC geography, canonical orgs/items + aliases | `ref` | `ingestion/load_psgc.py`, `ingestion/load_reference.py` |
| Cleansed, typed, conformed | `staging` | dbt |
| Data-quality results and quarantine | `dq` | dbt |
| Star schema (conformed dimensions + facts) | `dw` | dbt |
| Data marts / ROLAP aggregates | `mart` | dbt |

See [docs/dimensional-model.md](docs/dimensional-model.md) for grain statements and the bus matrix.

## Repository layout

```
ingestion/            Python: migrations, reference loads, synthetic source generator, raw loader
supabase/migrations/  SQL schema history (runs on local Postgres and Supabase)
data/reference/       real reference data (events, PSGC-derived geography, master data)
data/sources/         generated source extracts (git-ignored; regenerate any time)
dbt/                  transformations, data-quality tests, docs
web/                  Next.js dashboards (deployed on Vercel)
docs/                 model documentation
```

## Running locally

Requires PostgreSQL 17 and Python 3.11+.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # Windows (use .venv/bin/ on macOS/Linux)
cp .env.example .env                               # then set PGPASSWORD
createdb driw

.venv/Scripts/python ingestion/migrate.py          # create schemas and tables
.venv/Scripts/python ingestion/load_reference.py   # organizations, relief items
.venv/Scripts/python ingestion/load_psgc_api.py    # PSGC geography (see data/reference/README.md)
.venv/Scripts/python ingestion/generate_sources.py # synthetic source files + defect manifest
.venv/Scripts/python ingestion/load_raw.py         # land sources into raw.*
```

## Standards

- UNDRR Global Framework for Disaster-Related Statistics
- Sendai Framework for Disaster Risk Reduction 2015–2030
- UNDRR Data Strategy and Roadmap 2023–2027
- PSA Philippine Standard Geographic Code (PSGC)
