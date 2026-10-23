# Requirements Traceability Matrix

Each requirement of the IT271 semester project brief, and where this submission meets it.

| Brief section | Requirement | Where it is met |
|---|---|---|
| 1. Overview | Requirements gathering and BI objectives | Chapter 1 (Business Case), §2–§5 |
| 1. Overview | Data modeling: conceptual, logical, physical | Chapter 2 (Warehouse Design), §1–§3 |
| 1. Overview | ETL processes | Chapter 4 (ETL Design) |
| 1. Overview | OLAP cube or star/snowflake schema | Chapter 2 (four star schemas); Chapter 7 (ROLAP cube) |
| 1. Overview | Data governance and security | Chapter 6 (Governance, Security and Privacy) |
| 1. Overview | Analytics, dashboards, reports | Chapter 7 (Analytics) |
| 2A | Description of the enterprise domain | Chapter 1 §1 |
| 2A | Key business questions | Chapter 1 §3 (BQ1–BQ10) |
| 2A | Functional and non-functional requirements | Chapter 1 §4 (FR1–FR12), §5 (NFR1–NFR9) |
| 2A | Schema design: star or snowflake (fact + dimension tables) | Chapter 2 §2; Chapter 2 (dimensional model detail) |
| 2A | ER/UML diagrams of the warehouse design | Chapter 2: conceptual diagram and four ER diagrams |
| 2A | Data dictionary and metadata documentation | Chapter 3 (generated from the catalog; lineage, row counts, load times) |
| 2A | ETL: sources of data (mock or real) | Chapter 4 §2 |
| 2A | ETL: transformation logic (cleaning, integration, aggregation) | Chapter 4 §4; Chapter 5 |
| 2A | ETL workflow diagram | Chapter 4 §1 |
| 2A | Governance: security, privacy, access controls | Chapter 6 (roles, row-level security, web login, Privacy section) |
| 2A | Governance: data quality management strategy | Chapter 5 (Data Quality Framework) |
| 2B | Warehouse on SQL Server, Oracle, PostgreSQL, MySQL or cloud DW | PostgreSQL 17 (Chapter 2 §3, Chapter 9) |
| 2B | ETL pipelines (tools or custom Python/SQL) | Python + dbt, `ingestion/pipeline.py` (Chapter 4) |
| 2B | OLAP cube / analytical queries | `mart_impact_cube` (CUBE), GROUPING SETS, 14 sample queries (Chapter 7, Appendix A) |
| 2B | Reports/dashboards (Power BI, Tableau or similar) | Executive, Operations, Logistics dashboards on XAMPP, with a screenshot and discussion of every page (Chapter 7 §2) |
| 2C | Validation of ETL: completeness, correctness, accuracy | Chapter 8 (99 dbt checks, 28 end-to-end, 19/19 reconciliation, 0 false matches) |
| 2C | Test reports for data consistency and query performance | Chapter 8 (consistency); Query Performance Test Report |
| 2D | Live demo | Chapter 9 §4 (demo script) |
| 2D | Showcase of sample queries, OLAP analysis, dashboards | Appendix A, Chapter 7 |
| 2D | Defense of design choices | Chapter 2 (star vs snowflake, ROLAP), dimensional-model design decisions, Chapter 4 (full reload, quarantine) |
| 2D | Enterprise positioning | Why an EDW needs no CMS; Excel data exchange with LGUs and agencies: templates, layout profiles, checked uploads, Excel export (Chapter 10) |
