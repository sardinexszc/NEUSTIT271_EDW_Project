# Implementation and Live Demo Guide

## 1. Technology stack

**Table: Technology stack.** Every component is open source or free and runs on one laptop or an agency server.

| Layer | Technology |
|---|---|
| Data warehouse | PostgreSQL 17.11 (local) |
| ETL | Python 3.13 (extraction, loading), dbt Core 1.12 (transformation, data quality, tests) |
| OLAP | ROLAP in PostgreSQL: star schema, materialized views, `CUBE` / `ROLLUP` / `GROUPING SETS` |
| Back-end | PHP 8.1 on XAMPP (Apache) with `pdo_pgsql` |
| Dashboards | Next.js (static build) served by Apache |
| Version control and CI | GitHub (`sardinexszc/NEUSTIT271_EDW_Project`), GitHub Actions |

## 2. Repository layout

**Table: Repository layout.** Each folder holds one part of the system; the documentation and its generators live with the code.

| Folder | Contents |
|---|---|
| `ingestion/` | Python pipeline: migrations, reference loads, synthetic generator, raw loader, export, benchmark, web role |
| `supabase/migrations/` | SQL schema history (schemas, raw tables, reference tables, roles, governance) |
| `dbt/` | Staging, data-quality, warehouse and mart models; tests; rule catalog |
| `data/reference/` | Real reference data (events, PSGC-derived geography, organizations, relief items) |
| `web/` | Dashboards (Next.js) and the PHP API (`web/php/api`) |
| `tests/` | End-to-end, governance and API tests (pytest) |
| `docs/` | This documentation, diagrams and their generators |

## 3. Build and run

```bash
# 1. Python environment and database connection (.env holds PG* settings)
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt

# 2. Build the warehouse end to end (about 1 minute)
.venv/Scripts/python ingestion/pipeline.py

# 3. Validate
.venv/Scripts/python -m pytest tests

# 4. Excel templates and the Data exchange catalog (after the warehouse is built)
.venv/Scripts/python ingestion/intake.py templates

# 5. Web back-end login + PHP config (once), then publish to XAMPP
.venv/Scripts/python ingestion/setup_web_role.py
cd web && npm install && npm run deploy:xampp
```

XAMPP's `php.ini` needs `extension=pdo_pgsql` and `extension=pgsql` enabled, and Apache restarted.

## 4. Live demo script

1. **Warehouse.** In pgAdmin or psql, show the layers (`raw` → `staging` → `dw` → `mart`) and
   the ER diagram of a star (pgAdmin draws it from the real PK/FK constraints).
2. **Data quality.** `select * from dq.dq_reconciliation;` shows all 19 planted defect types
   detected at the exact count; `select * from dq.dq_quarantine limit 10;` shows rejected rows
   with reasons.
3. **OLAP.** Run Q02 (roll-up), Q03 (drill-down), Q05 (cube) and Q06 (semi-additive peak) from
   `docs/sample-queries.sql`.
4. **SCD Type 2.** `select * from dw.dim_location where city_muni_name = 'Parang' and psgc_code like '19038%';`
   shows Maguindanao before and Maguindanao del Norte after 18 Sep 2022.
5. **Security.**
   `begin; set local role driw_demo_bicol; select count(*) from dw.fact_damage_assessment; rollback;`
   returns only Bicol's rows; as `driw_demo_executive` the same query is refused.
6. **Dashboards.** Open `http://localhost/driw/`: Executive, then Operations for Kristine
   (`/driw/operations/?event=TC2024-KRISTINE`), then Logistics. Point out the footer
   ("Live from the PostgreSQL warehouse … as read-only role driw_web") and Download CSV.
7. **Data exchange.** Open `http://localhost/driw/exchange/`, download a template, then check
   `data/intake-samples/albay-pdrrmo-kristine-evacuation.xlsx` with the *Albay PDRRMO* layout: the
   report shows names matched to the PSGC, a recovered center code, overcrowding, and three rejected
   rows with reasons. Download the Excel workbook for Kristine.
8. **API.** `http://localhost/driw/api/health.php` and
   `http://localhost/driw/api/marts.php?name=mart_event_summary`.
