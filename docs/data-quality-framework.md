# Data Quality Framework

How DRIW detects, corrects, flags and quarantines bad source data before it reaches the
star schema, and how we prove the rules work.

## Where data quality happens

```
raw.*  ──▶  staging.stg_*  ──────────────▶  dw.*  (valid + warning rows only)
 (text,      typed, conformed, every row
  as-is)     tagged with dq_issues/dq_status
                     │
                     ├──▶ dq.dq_issue_log       one row per issue (rule, field, source file, row)
                     ├──▶ dq.dq_rule_summary    scorecard per rule
                     ├──▶ dq.dq_quarantine      rejected rows + reasons
                     └──▶ dq.dq_reconciliation  planted vs detected (synthetic-data proof)
```

Staging models never drop rows. Each raw row keeps its lineage (`_batch_id`, `_source_file`,
`_row_number`) and gets.

[Table](#table-data-quality-columns-added-to-every-staging-row) defines the two columns.

**Table: Data-quality columns added to every staging row.** Together they tell the loader which rows may reach the warehouse, and record why the others did not.

| Column | Meaning |
|---|---|
| `dq_issues` | Array of rule codes that fired, e.g. `{LOC_NAME_VARIANT, MISSING_VALUE:dead}` |
| `dq_status` | `valid` · `warning` · `rejected` · `duplicate` |

## Severity policy

Each rule has a severity, and [Table](#table-severity-policy-of-the-data-quality-rules) gives the action each severity triggers.

**Table: Severity policy of the data-quality rules.** The severity decides whether a problem is corrected, flagged or quarantined.

| Severity | Action | Reaches the warehouse? | Example |
|---|---|---|---|
| **info** | Corrected automatically | Yes | `Naga City` → PSGC *City of Naga*; `1,234` → 1234; `R50` sacks → kg |
| **warning** | Kept and flagged | Yes | Evacuation center over capacity; required measure blank |
| **reject** | Quarantined in `dq.dq_quarantine` | No | Negative cost; arrival before dispatch; unknown item code |

The full catalog (45 rules across 5 sources, including lifeline and outside-evacuation-center checks) is
[`dbt/seeds/dq_rules.csv`](../dbt/seeds/dq_rules.csv). A dbt test fails the build if a
staging model emits a rule that is not in the catalog, or if a row's `dq_status` disagrees
with the severities of its issues.

## Key techniques

**Location conformance (PSGC).** Every distinct (province, city/municipality) pair from
all sources is resolved once in `stg_location_resolution`, always within the reported province:

1. **Exact** official name.
2. **Normalized**: case, spacing, `ñ`→`n`, `City of X` / `X City`, `Sto.`/`Sta.`.
3. **Fuzzy**: Levenshtein distance ≤ 2 on normalized and letters-only keys. The best
   candidate must be unique; ties (e.g. `Malniao` is equally close to *Malinao* and *Manito*)
   stay unmatched for a data steward instead of being guessed.

**How "0 false matches" is validated.** Two sources carry the true place code inside another
field: every LGU request ID and every DROMIC evacuation-center code begins with the 7-digit PSGC
prefix of the city or municipality it belongs to. That prefix is the ground truth. The dbt test
`assert_location_matching_is_accurate` compares it with the place the matcher chose for **every**
such row, not a sample: 32,748 LGU rows and 30,599 DROMIC rows, 63,347 in all. A row fails if the
two disagree; none do. The test runs on every build, so a change to the matcher that caused a
wrong match would fail the build.

Two limits apply. Rows from NDRRMC, NGO and the outside-evacuation-center reports carry no
embedded code, so they are not checked directly; they go through the same matcher, which resolves
each distinct (province, city/municipality) pair once for all sources. And the misspellings were
planted by the generator, so real reports may contain kinds of errors it did not plant. Names the
matcher cannot resolve with confidence are left unmatched for a data steward rather than guessed.

**Event conformance.** Sources refer to events by local name (*Kristine*), international
name (*Trami*), `TY KRISTINE` or the key `TC2024-KRISTINE`. `stg_event_alias` lists every
form; matches must also fall within the event's time window, because PAGASA reuses names.

**Unit standardization.** Partner item codes map to canonical items with a conversion factor
(`R50`: 1 sack = 50 kg), so quantities and PHP values are comparable across organizations.

**Imputation.** A missing evacuation-center code is recovered when the same
place + center name + barangay always carries a single code elsewhere; otherwise it's rejected.

**De-duplication.** Exact duplicate sitrep rows and re-issued PAGASA bulletins are marked
`duplicate` and excluded.

## Proof: reconciliation against planted defects

The synthetic generator records every defect it plants in `_defect_manifest.json`
(loaded to `meta.defect_manifest`). `dq.dq_reconciliation` compares that with detected issues.

[Table](#table-reconciliation-of-planted-and-detected-defects) gives the result.

**Table: Reconciliation of planted and detected defects.** Every planted defect type is found at exactly the planted count, and no row is rejected without a planted cause.

| Result (seed 271) | |
|---|---|
| Defect types planted | 19 |
| Exactly reconciled | **19 / 19** |
| Rejected rows not explained by a planted defect | 0 |

Load rates after data quality: NDRRMC 98.2%, DROMIC 99.6%, NGO lines 97.7%, LGU 98.8%; the
outside-evacuation-center and lifeline reports load in full (100%).

A warn-level test (`warn_unplanted_rejections`) flags reject rules firing with no planted
cause. During development it caught a real parsing bug: monsoon incidents named
*"Southwest Monsoon (Habagat) Carina (Gaemi)"* were matched on the first parentheses
instead of the last, wrongly rejecting 1,244 rows.

## Running

```bash
.venv/Scripts/python ingestion/pipeline.py          # everything
.venv/Scripts/python ingestion/pipeline.py dbt      # rebuild staging + dq and run all tests
```

Useful queries:

```sql
select * from dq.dq_reconciliation;                       -- planted vs detected
select * from dq.dq_rule_summary where issue_count > 0;   -- scorecard
select * from dq.dq_quarantine limit 50;                  -- what was rejected and why
```
