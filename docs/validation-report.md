# Testing and Validation Report

How DRIW was tested, and the results. Data seed 271, run on PostgreSQL 17.11.

## Summary

| Suite | Checks | Result |
|---|---|---|
| dbt build (models + data tests) | 99 | **99 pass** |
| End-to-end tests (`tests/test_end_to_end.py`) | 28 | **28 pass** |
| Governance tests (`tests/test_governance.py`) | 21 | **21 pass** |
| Dashboards (`npm run lint`, `npm run build`) | lint + type check + static build | **pass** |

Run everything with `.venv/Scripts/python -m pytest tests`. It builds a brand-new database
(`driw_e2e`) from nothing through the whole pipeline (migrations, reference data, PSGC,
generation, raw load, dbt, export), runs every check, then rebuilds dbt a second time.
Duration: about one minute. GitHub Actions runs the same suite and the dashboard build on
every push (`.github/workflows/ci.yml`).

## What is validated

### 1. Completeness: nothing is lost between layers
- Every raw row reaches staging (5 sources; NGO checked at item-line level).
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
- Primary and foreign keys on the star schema (9 PKs, 26 FKs).
- One row per declared grain in each fact.
- SCD Type 2: no overlapping or missing validity periods, exactly one current version;
  Typhoon Paeng (Oct 2022) rolls up to Maguindanao del Norte/del Sur.

### 5. Reproducibility
- The generator is deterministic: two runs with the same seed produce identical content.
- A fresh database built from scratch matches the working database row for row
  (83,442 fact rows, 1,548 Bicol damage rows in both).
- A second dbt build gives identical fact counts and keeps grants and row-level security.

### 6. Security (see [governance.md](governance.md))
- Executive reads marts only; denied on warehouse detail, staging, raw, quarantine.
- Analyst sees every fact row, marts and DQ scorecards; denied raw and quarantine.
- Regional officers (Bicol, Cagayan Valley) see exactly their region's rows in all four
  facts and in the secure views, and zero rows from other regions.
- An unmapped regional user sees zero rows (default deny).
- Regional users cannot read the mapping, grant themselves roles, or edit their mapping.
- Stewards work on raw, staging and quarantine, may fix alias maps, and are denied the warehouse.

## Defects found by testing (and fixed)

Testing earned its keep. Each of these was caught by a test, not by inspection:

| Found by | Problem | Fix |
|---|---|---|
| DQ reconciliation | Generator counted the placeholder "-" as a negative number | Count only real numbers as negative |
| Unplanted-rejection check | Monsoon incidents named "Southwest Monsoon (Habagat) Carina (Gaemi)" matched the first parentheses; 1,244 rows wrongly rejected | Match the last parentheses |
| Location accuracy test | Letter swaps inside "City of" (e.g. "Cityo f Legazpi") went unmatched | Letters-only fuzzy key |
| Governance tests | Regional users saw **zero** rows: a `SECURITY DEFINER` function sees its owner as `current_user` | Region lookup moved into a view |
| Governance tests | `SET ROLE` escalation test passed for the wrong reason (checked against the session user) | Test escalation via `GRANT` and mapping writes instead |
| Browser review | "Family coverage 101%" double-counted repeat distributions | Relabelled "servings per affected family" |

## Known limitations

- All operational figures are synthetic; magnitudes are calibrated to look plausible,
  not to match official NDRRMC totals.
- City population is estimated from barangay counts (the PSA workbook with census
  population could not be downloaded automatically).
- The PSGC source predates the 2022 Maguindanao split; the split is applied through the
  SCD2 change log.
- Seven misspelled place names are equally close to two real towns and stay unmatched by
  design, for a data steward to resolve.
- Dashboards read a JSON snapshot of the marts; live querying needs the warehouse on
  Supabase (one file, `web/src/lib/data.ts`).
