# Business Case and Requirements Analysis

## 1. Enterprise domain

**Government: disaster risk reduction and management (DRRM) in the Philippines.**

The Philippines is struck by around twenty tropical cyclones a year, plus monsoon floods.
Responding to one event involves many agencies, each with its own system:

| Organization | Role in a disaster | System of record (simulated) |
|---|---|---|
| NDRRMC / Office of Civil Defense | Consolidates damage and casualty figures | Situation reports (CSV), cumulative, re-issued per event |
| DSWD (DROMIC) | Runs and reports evacuation centers | Daily Excel workbooks per field office |
| NGOs and UN agencies (PRC, Caritas, WFP, UNICEF) and DSWD | Distribute relief goods | Partner reports (nested JSON) with their own item codes and units |
| PAGASA | Names and tracks hazard events | Weather bulletins (CSV) |
| LGUs / MDRRMOs | Rescue, evacuation, road clearing, relief delivery | Response request logs (CSV) |

These systems share no place codes, event names or units. Leadership therefore cannot answer
cross-agency questions without manual reconciliation in spreadsheets.

**Scope.** Tropical cyclones and southwest-monsoon floods, 2020–2025: 31 events. Event names
and dates (PAGASA) and all geography (PSA PSGC: 17 regions, 81 provinces, 1,634 cities and
municipalities, 42,046 barangays) are real. Operational figures are synthetic, generated with
counted, planted defects (85,841 source rows; 9,995 defects of 19 types), because agency data is
not public and known defects let the ETL be proven correct.

## 2. Stakeholders and BI objectives

| Stakeholder | Needs | BI objective | Served by |
|---|---|---|---|
| Executive leadership (NDRRMC council, agency heads) | Overall impact, trends, where to invest | Single view of damage, casualties and relief across all agencies and years | Executive dashboard, `mart_event_summary`, `mart_impact_cube` |
| Operations managers (regional DRRM offices) | During and after an event: evacuation load, response speed | Per-event evacuation and response performance | Operations dashboard, `secure.*` views for their region |
| Logistics officers | Whether relief matched need | Relief by organization and resource, coverage per province | Logistics dashboard, `mart_province_event_impact` |
| Data analysts | Ad-hoc analysis, forecasting inputs | Clean, conformed star schema with history | `dw.*`, sample queries |
| Data stewards / IT | Data quality, reconciliation, operations | Measurable data quality with traceability to source | `dq.*`, quarantine, lineage |

## 3. Key business questions

| # | Business question | Answered by |
|---|---|---|
| BQ1 | Which events caused the most damage, deaths and displacement? | Q01, Q13; Executive dashboard |
| BQ2 | How does damage trend by year and category, and how did each year compare with the last? | Q02, Q05, Q12; Executive dashboard |
| BQ3 | Within an event, which regions, provinces and towns were hit hardest? | Q03 (drill-down) |
| BQ4 | Which regions suffer most from typhoons versus monsoon floods? | Q04, Q05 (cube); Executive dashboard |
| BQ5 | How many people were displaced at the peak, in evacuation centers and outside them, and for how long? | Q06; Operations dashboard |
| BQ6 | Which evacuation centers are repeatedly overcrowded? | Q07; Operations dashboard |
| BQ7 | How quickly are response teams dispatched, by request type and priority, and where is it slowest? | Q08, Q09; Operations dashboard |
| BQ8 | Did relief reach provinces in proportion to impact? Which were under-served? | Q10; Logistics dashboard |
| BQ9 | Which organizations delivered which kinds of relief, and who paid for it (DSWD, LGUs, NGOs, international)? | Q11; Logistics dashboard |
| BQ10 | How reliable is the data: what was rejected, and why? | Q14; `dq.dq_reconciliation` |
| BQ11 | Which events hit hardest relative to the population (deaths and affected per 100,000, Sendai targets A and B)? | `mart_event_summary`; Executive dashboard |
| BQ12 | How long were roads, bridges, power, water and communications down, and which take longest to restore? | `mart_lifeline_restoration`; Operations dashboard |

The Q-numbers refer to [`sample-queries.sql`](sample-queries.sql).

## 4. Functional requirements

| # | Requirement | How it is met | Status |
|---|---|---|---|
| FR1 | Ingest data from the five agency systems in their native formats (CSV, Excel, JSON). | `ingestion/load_raw.py` lands every file in `raw.*` unchanged. | Met |
| FR2 | Keep lineage from every warehouse row to its source file and row. | `meta.load_batch`, `_batch_id/_source_file/_row_number`, `dim_source_system`. | Met |
| FR3 | Conform place names to the official PSGC codes. | `stg_location_resolution`: exact, normalized, fuzzy; 0 false matches on ground truth. | Met |
| FR4 | Conform event names, organizations and relief units across sources. | Event aliases with time windows; organization and item alias maps; unit conversion. | Met |
| FR5 | Detect, correct, flag or quarantine data-quality defects, with reasons. | 45 rules in `dq_rules`; `dq_quarantine`; 19/19 planted defect types reconciled. | Met |
| FR6 | Store integrated data in a dimensional model with conformed dimensions. | Star schema: 4 facts, 9 dimensions (`docs/warehouse-design.md`). | Met |
| FR7 | Preserve history when administrative boundaries change. | SCD Type 2 `dim_location` (2022 Maguindanao split). | Met |
| FR8 | Support OLAP analysis: roll-up, drill-down, slice, dice, pivot. | `GROUP BY CUBE / ROLLUP / GROUPING SETS`, marts, sample queries Q01–Q14. | Met |
| FR9 | Provide dashboards for executive, operational and logistics users. | Next.js dashboards on XAMPP: Executive, Operations, Logistics. | Met |
| FR10 | Let users filter by event, share views and export data. | `?event=` links, CSV download on every chart table. | Met |
| FR11 | Restrict data by role, including region-level restriction. | 4 roles, row-level security, `driw_web` least-privilege login. | Met |
| FR12 | Rebuild the warehouse end to end with one command. | `python ingestion/pipeline.py`. | Met |

## 5. Non-functional requirements

| # | Requirement | Target | Evidence | Status |
|---|---|---|---|---|
| NFR1 | Data accuracy | Every planted defect type detected at the exact planted count | `dq.dq_reconciliation`: 19/19 match | Met |
| NFR2 | Query performance | Analytical queries under 1 second | `docs/query-performance.md`: 14/14, slowest about 32 ms | Met |
| NFR3 | Security | Least privilege; regional row-level restriction; no credentials in code | `docs/governance.md`; 21 per-role access tests + web-role test | Met |
| NFR4 | Privacy | No personal data in the warehouse; casualty data aggregated | `docs/governance.md` § Privacy | Met |
| NFR5 | Reliability | A failed source row never stops the load; rejected rows are kept with reasons | Quarantine design; staging keeps every row | Met |
| NFR6 | Reproducibility | Same inputs produce the same warehouse | Deterministic generator (seed 271); e2e test rebuilds from nothing | Met |
| NFR7 | Maintainability | Version-controlled, tested, documented | GitHub repo, dbt tests, CI on every push, generated data dictionary | Met |
| NFR8 | Usability and accessibility | Readable on desktop and phone; color-blind-safe charts; table view for every chart | Validated palette, legends, "Show table", responsive layout | Met |
| NFR9 | Portability | Run on the agency's own infrastructure without cloud services | Local PostgreSQL 17 + XAMPP (Apache, PHP); migrations also run on Supabase | Met |

## 6. Assumptions and constraints

- Operational figures are synthetic; they are scaled to population and storm strength to be
  plausible, not to match official NDRRMC totals.
- City population is estimated from barangay counts, because the PSA workbook with census
  population could not be downloaded automatically.
- Loads are batch (full reload), not real time; near-real-time feeds are future work.
- Standards followed: UNDRR Global Framework for Disaster-Related Statistics, Sendai Framework
  2015–2030, UNDRR Data Strategy and Roadmap 2023–2027, PSA PSGC, Data Privacy Act of 2012 (RA 10173).
