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
 5 simulated source systems          PostgreSQL 17 (local)                             Presentation
 ┌───────────────────────┐   extract  ┌─────┐  dbt   ┌─────────┐  dbt  ┌────┐  dbt  ┌──────┐   Next.js
 │ NDRRMC sitreps and    │ ─────────▶ │ raw │ ─────▶ │ staging │ ────▶ │ dw │ ────▶ │ mart │ ─▶ dashboards
 │  lifelines (CSV)      │            └─────┘        └─────────┘       └────┘       └──────┘   (XAMPP)
 │ DSWD DROMIC (Excel)   │               │            data-quality       star        ROLAP
 │ NGO/LGU relief (JSON) │               │            rules → dq.*       schema      aggregates
 │ PAGASA, LGU logs (CSV)│           meta.load_batch (lineage)          ref.* (PSGC, aliases)
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

**Submission report:** [docs/submission/DRIW_Final_Report.pdf](docs/submission/DRIW_Final_Report.pdf)
(and `.docx`), compiled from the documents below by `docs/build/build_report.py`:
[business case](docs/business-case.md), [warehouse design](docs/warehouse-design.md) (conceptual,
logical, physical, ER diagrams), [data dictionary](docs/data-dictionary.md),
[ETL design](docs/etl-design.md), [analytics](docs/analytics.md),
[sample queries](docs/sample-queries.sql), [query performance](docs/query-performance.md),
[implementation and demo](docs/implementation.md), [requirements coverage](docs/requirements-traceability.md).

See [docs/dimensional-model.md](docs/dimensional-model.md) for grain statements and the bus matrix,
and [docs/data-quality-framework.md](docs/data-quality-framework.md) for the 45 data-quality rules
and their reconciliation against the planted defects (19/19 defect types detected exactly).
[docs/governance.md](docs/governance.md) covers roles and row-level security, and
[docs/validation-report.md](docs/validation-report.md) the test results.

## Repository layout

```
ingestion/            Python: migrations, reference loads, synthetic source generator, raw loader
supabase/migrations/  SQL schema history (runs on local Postgres and Supabase)
data/reference/       real reference data (events, PSGC-derived geography, master data)
data/sources/         generated source extracts (git-ignored; regenerate any time)
dbt/                  transformations, data-quality tests, docs
web/                  Next.js dashboards and the PHP API (hosted on XAMPP)
docs/                 model documentation
```

## Running locally

Requires PostgreSQL 17 and Python 3.11+.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # Windows (use .venv/bin/ on macOS/Linux)
cp .env.example .env                               # then set PGPASSWORD
createdb driw

.venv/Scripts/python ingestion/pipeline.py         # run every step below, then dbt build

# or step by step:
.venv/Scripts/python ingestion/migrate.py          # create schemas and tables
.venv/Scripts/python ingestion/load_reference.py   # organizations, relief items
.venv/Scripts/python ingestion/load_psgc_api.py    # PSGC geography (see data/reference/README.md)
.venv/Scripts/python ingestion/generate_sources.py # synthetic source files + defect manifest
.venv/Scripts/python ingestion/load_raw.py         # land sources into raw.*
.venv/Scripts/python ingestion/pipeline.py dbt     # staging, data quality, star schema, marts + all tests
.venv/Scripts/python ingestion/pipeline.py export  # snapshot the marts to web/src/data/ for the dashboards
```

### Tests

```bash
.venv/Scripts/python -m pytest tests                # fresh database end to end + access control (~1 min)
```

Builds a new `driw_e2e` database through the whole pipeline, then checks completeness,
data-quality reconciliation, aggregate consistency, determinism, a second rebuild, and that
each role (executive, analyst, regional, steward) sees exactly what it should. GitHub Actions
runs it, plus the dashboard build, on every push.

### Dashboards

```bash
cd web && npm install && npm run dev               # http://localhost:3000
```

**Hosting on XAMPP (Apache).** Build the dashboards as plain static files and publish them to
`C:\xampp\htdocs\driw`, then open <http://localhost/driw/> with Apache running:

```bash
cd web && npm run deploy:xampp                     # XAMPP_HTDOCS=<path> if XAMPP is elsewhere
```

Re-run it after every `pipeline.py export`. The script only replaces a `driw` folder it created
itself, and writes an `.htaccess` for the 404 page and the preview image.

**PHP back-end (live data).** `web/php/api` is published to `htdocs/driw/api` and serves the
marts straight from the PostgreSQL warehouse. The dashboards load it at runtime and fall back to
the bundled snapshot if the warehouse is down; the footer says which. One-time setup:

1. In `C:\xampp\php\php.ini`, enable `extension=pdo_pgsql` and `extension=pgsql`, then restart Apache.
2. Create the web login and its config (written outside `htdocs`):

   ```bash
   .venv/Scripts/python ingestion/setup_web_role.py
   ```

| Endpoint | Returns |
|---|---|
| `GET /driw/api/health.php` | database, connected role, PostgreSQL version |
| `GET /driw/api/marts.php?name=<mart>[&event=TC2024-KRISTINE]` | one mart as JSON (allow-listed names) |

The API connects as `driw_web`, a member of `driw_executive` only: it can read the marts and
nothing else (see [docs/governance.md](docs/governance.md)).

| Page | For | Shows |
|---|---|---|
| `/` Executive | leadership | Total damage, casualties, peak displaced, deaths per 100,000 (Sendai target A), cost by year and category, costliest events, regions (from the CUBE mart) |
| `/operations` | operations managers | Per event: people displaced inside and outside evacuation centers per day, over-capacity centers, roads/bridges/power/water/communications restoration, dispatch times by type and priority |
| `/logistics` | logistics | Relief by organization and resource category, cost of assistance by provider (DSWD, LGU, NGO, international), least-served provinces (PHP per affected person) |
| `/exchange` | LGUs and agencies | Excel templates, check and submit a report (per-row validation report), Excel export of the marts |
| `/about` | everyone | Architecture, fact grains, source systems, data-quality proof |

The pages are static files; their data comes from the PHP API, or from the exported JSON
snapshot when the warehouse is down.
The selected event is part of the URL, so views can be shared (for example
`/operations?event=TC2024-KRISTINE`), and every chart table has a **Download CSV** with the
raw, unformatted values. If you rebuild the warehouse, re-run the `export` step and commit
`web/src/data/`; the test suite fails when the committed data is stale.

### Data exchange (Excel in and out)

```bash
.venv/Scripts/python ingestion/intake.py templates      # Excel templates + page catalog (after a build)
.venv/Scripts/python ingestion/intake.py validate --type dromic --profile albay-pdrrmo-evacuation     --file data/intake-samples/albay-pdrrmo-kristine-evacuation.xlsx      # per-row report (JSON)
.venv/Scripts/python ingestion/intake.py submit ...      # same, then store under data/intake/ and reload
.venv/Scripts/python ingestion/export_xlsx.py --event TC2024-KRISTINE --out kristine.xlsx
```

Checking runs the warehouse's own dbt staging models on the upload in a sandbox database
(`<db>_intake`), so it never changes the warehouse. LGU layouts are described in
`ingestion/intake_profiles/*.json`. On XAMPP the same runs from the **Data exchange** page through
`api/intake.php` and `api/export.php`; uploads are accepted from the server itself only. See
[docs/enterprise-positioning.md](docs/enterprise-positioning.md).

## Standards

- UNDRR Global Framework for Disaster-Related Statistics
- Sendai Framework for Disaster Risk Reduction 2015–2030
- UNDRR Data Strategy and Roadmap 2023–2027
- PSA Philippine Standard Geographic Code (PSGC)
