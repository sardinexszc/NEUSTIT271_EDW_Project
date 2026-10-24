# Conclusion and Recommendations

## 1. Summary

The project set out to give Philippine disaster managers one trusted view of an event that five
agencies report separately. DRIW does this. It integrates NDRRMC situation reports and lifeline
status, DSWD DROMIC evacuation reports (inside and outside evacuation centers), NGO, UN and LGU
relief records, PAGASA bulletins and LGU response logs into one dimensional model. Every row is
traceable to its source file, checked by 45 data-quality rules, and served to three audiences through
dashboards, CSV and Excel exports and an API.

**Table: Project objectives and what was achieved.** Each objective of the business case (Chapter 1)
is matched with the evidence that it was reached; the evidence is detailed in the chapter named.

| Objective | Outcome | Evidence |
|---|---|---|
| Integrate the agencies' data in their native formats | 113,191 source rows from 5 systems (CSV, Excel, JSON) in one model | Chapter 4 |
| Conform places, events, organizations and units | All sources matched to PSGC codes with 0 false matches; event aliases, item units converted | Chapters 4–5 |
| Prove data quality, not assume it | 19 of 19 planted defect types detected at the exact count (9,995 defects) | Chapter 5 |
| Model the business for analysis | Six star schemas, ten conformed dimensions, SCD Type 2 location history | Chapter 2 |
| Answer the business questions quickly | 14 of 14 sample queries under 1 second; eight marts for the dashboards | Chapters 7–8 |
| Protect the data | Four roles, row-level security by region, read-only web login, no personal data | Chapter 6 |
| Exchange data with LGUs and agencies | Excel templates, layout profiles, checked uploads, Excel export | Chapter 10 |
| Rebuild and verify with one command | 117 dbt checks and 91 automated tests pass on every build | Chapter 8 |

## 2. What the analysis shows

On the synthetic data, the warehouse answers all twelve business questions. The figures illustrate
the analysis, not real outcomes, but the patterns are the ones the dashboards are built to expose:

- **Cost and mortality rank events differently.** The costliest event is not the deadliest per
  100,000 people, so leadership needs both views (BQ1, BQ11).
- **Most displaced people are outside evacuation centers.** Counting only centers would miss more
  than half of the people who need relief (BQ5).
- **Overcrowding is a landfall-day problem**, and dispatch is slowest for logistics requests, not
  rescues (BQ6, BQ7).
- **Relief is uneven across provinces**, even within one storm, and the least-served provinces are
  visible at a glance (BQ8, BQ9).
- **Bridges and water take longest to restore**, and they decide how long communities stay cut off
  (BQ12).

## 3. Limitations

The operational figures are synthetic, because agency data is not public; population is estimated
from barangay counts until the PSA census file is loaded; loads are full batch reloads; and uploads
are limited to the server until the site has sign-in. The Known limitations section of Chapter 8
lists them in full. None of them requires a change to the design: replacing the generator with real
extracts changes only the input files.

## 4. Recommendations

**For the agencies using DRIW**

1. Adopt the PSGC code as the required place identifier in every report form. Most data-quality
   work in this project is spent matching place names that a code would make unnecessary.
2. Report displacement outside evacuation centers and lifeline status on the same schedule as
   evacuation figures, so total displacement and recovery can be tracked daily.
3. Open overflow evacuation centers and pre-position relief before landfall, and pre-position bridge
   modules and water-treatment units in the areas most often hit.
4. Use the least-served-provinces ranking to direct the next relief allocation during a response.

**For the next version of the system**

1. Load the PSA census population so the per-100,000 rates become official figures.
2. Add sign-in mapped to the database roles, so LGU officers can upload from anywhere and see only
   their region.
3. Move from full reloads to scheduled, incremental loads as volumes grow, with indexes on the most
   filtered fact keys and partitioning by event year.
4. Publish aggregated, anonymized indicators in the shape of the Sendai Framework targets.

DRIW shows that a governed, tested enterprise data warehouse can turn five agencies' reports into
one consistent picture of a disaster, and that its correctness can be demonstrated, not just
claimed.
