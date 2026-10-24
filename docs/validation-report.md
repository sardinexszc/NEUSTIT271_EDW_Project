# Testing and Validation Report

How DRIW was tested, and the results. Data seed 271, run on PostgreSQL 17.11.

## Summary

[Table](#table-test-suites-and-their-results) summarizes every test suite and its result.

**Table: Test suites and their results.** Every suite passes; together they cover completeness, correctness, consistency, model integrity, reproducibility, data exchange and security.

| Suite | Checks | Result |
|---|---|---|
| dbt build (39 models, 2 seeds, 76 data tests) | 117 | **117 pass** |
| End-to-end tests (`tests/test_end_to_end.py`) | 36 | **36 pass** |
| Governance tests (`tests/test_governance.py`) | 27 | **27 pass** |
| PHP API tests (`tests/test_php_api.py`) | 15 | **15 pass** (skipped where PHP is not installed, e.g. CI) |
| Data exchange tests (`tests/test_intake.py`) | 13 | **13 pass** |
| Query performance (`ingestion/benchmark_queries.py`) | 14 queries | **14 within the 1 s budget**, slowest about 34 ms |
| Dashboards (`npm run lint`, `npm run build`) | lint + type check + static build | **pass** |

Run everything with `.venv/Scripts/python -m pytest tests`. It builds a brand-new database
(`driw_e2e`) from nothing through the whole pipeline (migrations, reference data, PSGC,
generation, raw load, dbt, export), runs every check, then rebuilds dbt a second time.
Duration: about one and a half minutes. GitHub Actions runs the same suite and the dashboard
build on every push (`.github/workflows/ci.yml`). Query timings are in
[query-performance.md](query-performance.md).

## What is validated

### 1. Completeness: nothing is lost between layers
- Every raw row reaches staging (7 raw tables from 5 sources; NGO checked at item-line level).
- Every staged row has a status; every rejected row is in quarantine.
- Every valid/warning row reaches its fact table (dbt `assert_facts_reconcile_to_staging`).
- Every layer, fact and mart is non-empty.

### 2. Correctness: data quality is proven, not assumed
- **19/19 planted defect types detected at exactly the planted count**
  (`dq.dq_reconciliation`).
- Place-name matching checked against ground truth: **0 false matches** across ~63,000 rows.
- Every rejection traces to a planted defect (`warn_unplanted_rejections`).

### 3. Consistency: aggregates agree with detail
- Damage totals are equal in facts, the event mart and the CUBE grand total.
- Every mart adds back up to its facts (`assert_marts_reconcile_to_facts`).
- Exported JSON row counts equal mart row counts, and the dashboard data committed in
  `web/src/data/` is identical to a fresh build (fails if someone forgets to re-export).

### 4. Model integrity
- Primary and foreign keys on the star schema (10 PKs, 38 FKs).
- One row per declared grain in each fact.
- SCD Type 2: no overlapping or missing validity periods, exactly one current version;
  Typhoon Paeng (Oct 2022) rolls up to Maguindanao del Norte/del Sur.

### 5. Reproducibility
- The generator is deterministic: two runs with the same seed produce identical content.
- A fresh database built from scratch matches the working database row for row
  (111,763 fact rows, 1,548 Bicol damage rows in both).
- A second dbt build gives identical fact counts and keeps grants and row-level security.

### 6. Data exchange (see Chapter 10)
- Every Excel template has its instructions, the expected headings and drop-down lists.
- The Albay sample, in Albay's own layout, gets the expected verdict on every one of its 10 rows.
- Checking a file never changes the warehouse; a file missing required columns is refused whole.
- A submitted file loads with every warehouse check still passing: valid rows reach the facts,
  the rest are quarantined with reasons, and the synthetic-data reconciliation stays 19/19.
- Submitting the same file again replaces it instead of duplicating it.
- The Excel export has every mart, a data dictionary, frozen headings and filters.

### 7. Security (see [governance.md](governance.md))
- Executive reads marts only; denied on warehouse detail, staging, raw, quarantine.
- Analyst sees every fact row, marts and DQ scorecards; denied raw and quarantine.
- Regional officers (Bicol, Cagayan Valley) see exactly their region's rows in all six
  facts and in the secure views, and zero rows from other regions.
- An unmapped regional user sees zero rows (default deny).
- Regional users cannot read the mapping, grant themselves roles, or edit their mapping.
- Stewards work on raw, staging and quarantine, may fix alias maps, and are denied the warehouse.

## Defects found by testing (and fixed)

Testing earned its keep. Each of these was caught by a test, not by inspection.

[Table](#table-defects-found-by-testing-and-their-fixes) lists the defects the tests found during development and how each was fixed.

**Table: Defects found by testing, and their fixes.** Each was caught by an automated test or a review, not by chance, which shows the tests do real work.

| Found by | Problem | Fix |
|---|---|---|
| DQ reconciliation | Generator counted the placeholder "-" as a negative number | Count only real numbers as negative |
| Unplanted-rejection check | Monsoon incidents named "Southwest Monsoon (Habagat) Carina (Gaemi)" matched the first parentheses; 1,244 rows wrongly rejected | Match the last parentheses |
| Location accuracy test | Letter swaps inside "City of" (e.g. "Cityo f Legazpi") went unmatched | Letters-only fuzzy key |
| Governance tests | Regional users saw **zero** rows: a `SECURITY DEFINER` function sees its owner as `current_user` | Region lookup moved into a view |
| Governance tests | `SET ROLE` escalation test passed for the wrong reason (checked against the session user) | Test escalation via `GRANT` and mapping writes instead |
| Browser review | "Family coverage 101%" double-counted repeat distributions | Relabeled "servings per affected family" |
| Paper review | Logistics "Distributions" counted a distribution once per resource category (9,782 instead of 5,529) | Count from the event summary |
| Data exchange test | One impossible date ("10/32/2024") in a submitted file made `to_date` fail the whole staging model, which would block every load | Error-tolerant `meta.try_to_date` / `try_to_timestamp` and a range-checked integer cast; the row is flagged instead |
| Data exchange test | Rows that synthetic data never contains could break or silently drop out of a load (unknown responding unit, dispatch before request, unknown damage category, conflicting event dates) | Five new reject rules (36 → 41) |
| Browser test | Re-checking an already submitted file flagged all its rows as already reported | A resubmission now replaces its earlier version |

## Known limitations

- All operational figures are synthetic; magnitudes are calibrated to look plausible,
  not to match official NDRRMC totals.
- City population is estimated from barangay counts (the PSA workbook with census
  population could not be downloaded automatically).
- The PSGC source predates the 2022 Maguindanao split; the split is applied through the
  SCD2 change log.
- Seven misspelled place names are equally close to two real towns and stay unmatched by
  design, for a data steward to resolve.
- On XAMPP the dashboards read the marts live through the PHP API; elsewhere (a static host)
  they show the bundled snapshot.
- The Data exchange upload is limited to the server itself until the site has sign-in.
