# Executive Summary

## Problem

A Philippine typhoon or monsoon flood is reported by several agencies at once: NDRRMC (damage and
lifelines), DSWD (people displaced inside and outside evacuation centers), NGOs, UN agencies and
LGUs (relief), PAGASA (the hazard) and LGUs (response requests). Their systems share no place
codes, event names or units. Leadership therefore cannot answer cross-agency questions such as
"which provinces got the least relief per affected person?" without weeks of manual
reconciliation.

## Proposed solution

DRIW, the Disaster Response Intelligence Warehouse, is an enterprise data warehouse that
integrates the five sources into one dimensional model. A batch ETL pipeline cleans the source
files, conforms them to official place codes and event names, and checks them against
data-quality rules. The cleaned data is stored as star schemas: fact tables of measures that
share conformed dimensions such as date, place and event. Pre-aggregated marts serve
dashboards for three audiences: executives, operations managers and logistics officers.
Besides damage, casualties, evacuation, relief and response, the dashboards report measures that
disaster-risk practice asks for: deaths and affected people per 100,000 (Sendai Framework
targets A and B; UNDRR, 2015), people displaced outside evacuation centers, the restoration of roads,
bridges, power, water and communications, and the cost of assistance by provider.

The system is built with free, widely used tools: PostgreSQL 17 as the warehouse, Python and dbt
for the ETL and its tests, and a PHP back-end on XAMPP that serves the dashboards through a
read-only database login. Chapter 2 explains why each was chosen.

## What is real and what is synthetic

Agency operational data is not public, so the operational figures are generated (seed 271),
scaled to population and storm strength. Everything else is real or built exactly as it would
be on agency data. [Table](#table-what-is-real-and-what-is-synthetic-in-driw) separates the two.

**Table: What is real and what is synthetic in DRIW.** Everything that shows the warehouse works is real; only the operational figures, and the source files that carry them, are generated.

| Real | Simulated (synthetic) |
|---|---|
| The architecture, ETL pipeline, data-quality rules, star schema, marts, security and dashboards: built and run exactly as they would be on agency data | Every damage, casualty, evacuation, relief and response **figure** in this report and on the dashboards |
| The 31 events (PAGASA names and dates, 2020–2025) | The source files themselves (CSV, Excel, JSON) and their data-entry defects |
| All geography: PSA PSGC, 17 regions, 81 provinces, 1,634 cities and municipalities, 42,046 barangays | |

**The numbers demonstrate what the warehouse can do; they are not findings about real
disasters.** Synthetic data has one advantage for testing: 9,995 defects of 19 known types were
planted on purpose, so the ETL can be shown to be correct by counting what it finds.

## Key evidence

Each claim in [Table](#table-headline-results-of-the-project) is measured by an automated test or
a repeatable report described in Chapter 8, run on the submitted version of the project.

**Table: Headline results of the project.** The evidence column names how each result was measured.

| Measure | Result | Evidence |
|---|---|---|
| Source rows integrated | 113,191 from 5 systems in 4 formats | Row counts per raw table (Chapter 4) |
| Planted defects detected | 19 of 19 types, each at the exact count (9,995 defects) | `dq.dq_reconciliation` (Chapter 5) |
| Place names matched to official codes | 63,347 rows checked against known true codes, 0 false matches | dbt test on every LGU and DROMIC row that carries a true code (Chapter 5) |
| Automated checks | 117 dbt checks and 91 end-to-end, governance, API and data-exchange tests, all passing | Test reports (Chapter 8) |
| Query performance | 14 of 14 sample queries within 1 s (slowest about 34 ms); marts about 60–80× faster than the facts | Benchmark on a laptop, 5 timed runs per query (Chapter 8) |
| Access control | 4 roles; row-level security by region | Per-role access tests (Chapter 6) |

## Limitations

- **Synthetic figures.** The dashboard findings show the analysis the warehouse supports, not
  real outcomes. Replacing the generator with agency extracts changes the input files only.
- **Estimated population.** Per-100,000 rates use a population estimate (barangay count × 2,600)
  until the PSA census file is loaded, so they compare events with each other.
- **No live agency connection.** Data exchange is file-based: Excel templates and checked
  uploads, tested with sample files. No agency system is connected to DRIW.
- **Tested, not audited.** The security tests show the designed access rules hold; they are not
  a security audit or penetration test.
- **Batch loads.** The warehouse is reloaded in full on each run; incremental, scheduled loads
  are future work.

## How to read this report

The Requirements Coverage page that follows maps each item of the project brief to the chapter
that meets it, and the List of Abbreviations explains the agency and technical acronyms. Chapters
1–2 cover the business case and the design, 3–5 the metadata, ETL and data quality, 6 governance
and privacy, 7 the analytics, 8 testing, 9 how to run the live demo, 10 the warehouse's place in
the enterprise and its data exchange with LGUs, and 11 the conclusions and recommendations. The
References list the standards and sources cited, and Appendix A lists the sample queries.
