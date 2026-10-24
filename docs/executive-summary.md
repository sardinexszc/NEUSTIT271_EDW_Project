# Executive Summary

**Problem.** A Philippine typhoon or monsoon flood is reported by several agencies at once:
NDRRMC (damage and lifelines), DSWD (people displaced in and outside evacuation centers), NGOs, UN
agencies and LGUs (relief), PAGASA (the hazard) and LGUs (response requests). Their systems share no place codes, event names or units, so
leadership cannot answer cross-agency questions such as "which provinces got the least relief per
affected person?" without weeks of manual reconciliation.

**Solution.** DRIW, the Disaster Response Intelligence Warehouse, integrates the five sources
into one dimensional model on PostgreSQL 17: six star schemas (transaction, periodic-snapshot
and accumulating-snapshot facts) over ten conformed dimensions, including a Type 2 slowly
changing location dimension. A Python and dbt ETL pipeline cleans and conforms the data with
45 data-quality rules; eight ROLAP marts (`GROUP BY CUBE` and `GROUPING SETS`) feed Executive,
Operations and Logistics dashboards. Besides damage, casualties, evacuation, relief and response,
they report the measures disaster-risk practice asks for: deaths and affected people per 100,000
(Sendai Framework), people displaced outside evacuation centers, the restoration of roads,
bridges, power, water and communications, and the cost of assistance by provider. A PHP back-end on XAMPP serves them live through a
read-only login, and row-level security limits regional users to their own region.

## What is real and what is simulated

**Table: What is real and what is synthetic in DRIW.** Everything that shows the warehouse works is real; only the operational figures, and the source files that carry them, are generated.

| Real | Simulated (synthetic) |
|---|---|
| The architecture, ETL pipeline, data-quality rules, star schema, marts, security and dashboards: built and run exactly as they would be on agency data | Every damage, casualty, evacuation, relief and response **figure** in this report and on the dashboards |
| The 31 events (PAGASA names and dates, 2020–2025) | The source files themselves (CSV, Excel, JSON) and their data-entry defects |
| All geography: PSA PSGC, 17 regions, 81 provinces, 1,634 cities and municipalities, 42,046 barangays | |

Agency operational data is not public, so the figures are generated (seed 271), scaled to
population and storm strength. **The numbers demonstrate the warehouse; they are not findings
about real disasters.** Synthetic data has one advantage: 9,995 defects of 19 known types were
planted on purpose, so the ETL can be proven correct by counting. Nothing in the pipeline depends
on the data being synthetic: replacing the generator with real agency extracts changes the input
files only (see the Privacy section of Chapter 6).

## Results

**Table: Headline results of the project.** Each result is measured by an automated test or report described in Chapter 8.

| Measure | Result |
|---|---|
| Source rows integrated | 113,191 from 5 systems in 4 formats |
| Planted defects detected | 19 of 19 types, each at the exact count (9,995 defects) |
| Location names matched to PSGC | 63,347 rows, 0 false matches |
| Automated checks | 117 dbt checks and 91 end-to-end, governance, API and data-exchange tests, all passing |
| Query performance | 14 of 14 sample queries within 1 s (slowest about 34 ms); marts about 80× faster than the facts |
| Access control | 4 roles; row-level security verified per role |

## How to read this report

The Requirements Coverage page that follows maps each item of the project brief to the chapter
that meets it, and the List of Abbreviations explains the agency and technical acronyms. Chapters
1–2 cover the business case and the design, 3–5 the metadata, ETL and data quality, 6 governance
and privacy, 7 the analytics, 8 testing, 9 how to run the live demo, 10 the warehouse's place in
the enterprise and its data exchange with LGUs, and 11 the conclusions and recommendations. The
References list the standards and sources cited, and Appendix A lists the sample queries.
