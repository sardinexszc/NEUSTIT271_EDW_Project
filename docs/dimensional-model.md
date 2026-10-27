# DRIW Dimensional Model

Star schema in the `dw` schema, built by dbt from the cleansed staging layer
(only rows with `dq_status` valid or warning). All facts share conformed dimensions,
so damage, evacuation, relief and response can be analyzed side by side for the same
event and place.

## Fact tables

[Table](#table-fact-tables-with-grain-and-row-counts) gives the grain and current row count of each fact table.

**Table: Fact tables with grain and row counts.** The row counts are the volume each star holds after data-quality filtering (seed 271).

| Fact | Type | Grain (one row per…) | Rows* | Measures |
|---|---|---|---|---|
| `fact_damage_assessment` | Transaction | event × city/municipality × damage category | 8,806 | dead, injured, missing, affected families/persons, houses partially/totally damaged, cost (PHP) |
| `fact_evacuation_snapshot` | Periodic snapshot | evacuation center × day × event | 31,110 | families inside, persons inside, capacity, over-capacity flag |
| `fact_resource_distribution` | Transaction | distribution line item | 14,927 | quantity (standard unit), value (PHP), beneficiary families |
| `fact_response_action` | Accumulating snapshot | response request | 32,347 | hours to dispatch / arrive / on site / complete, personnel, completed flag |
| `fact_displacement_outside` | Periodic snapshot | city/municipality × day × event | 21,896 | families and persons displaced outside evacuation centers (with relatives or friends) |
| `fact_lifeline_disruption` | Accumulating snapshot | event × city/municipality × lifeline | 2,677 | units affected, hours to restore, restored flag |

\* Seed 271.

### Design decisions

- **Damage uses the latest sitrep only.** NDRRMC situation reports are cumulative, so
  summing every sitrep would double-count. The fact keeps the latest *valid* sitrep per
  event × place × category.
- **Evacuation grain includes the event.** Overlapping events (Nika, Ofel and Pepito,
  Nov 2024) can fill the same center on the same day.
- **Evacuation measures are semi-additive.** Sum across centers or places for one day; across
  days use the peak (MAX of daily totals) or the average, never the sum. The same holds for
  displacement outside centers; total displacement = inside + outside on the same day.
- **Displacement outside centers is its own fact.** DSWD DROMIC reports families staying with
  relatives or friends per city/municipality, not per center, so it cannot share the
  evacuation-center grain. Usually more people are displaced outside centers than inside.
- **Lifelines are an accumulating snapshot.** A disruption opens when a road, bridge, power,
  water or communication line goes down and closes when service is restored
  (`restored_date_key = -1` while still down).
- **Rates per 100,000 (Sendai Framework targets A and B).** `dim_location.population` is the
  denominator. The PSGC API has no census figures, so it is an estimate (barangay count × 2,600,
  labelled in `population_source`); rates compare events with each other rather than give
  official figures. Loading the PSA workbook (`load_psgc.py`) swaps in census population.
- **Cost of assistance by provider.** LGU relief (MDRRMO/CDRRMO/PDRRMO) arrives through the same
  distribution feed, so relief splits by `dim_organization.org_type`: national government (DSWD),
  LGU, NGO and international, as DROMIC reports it.
- **Header measures stay additive.** `beneficiary_families` belongs to a whole distribution, so
  it is stored on the record's first valid line only.
- **Open milestones.** A response request not yet completed has `completed_date_key = -1`
  ("Not yet occurred"), so foreign keys are never null; a later load fills it in.
- **Degenerate dimensions:** `sitrep_no`, `distribution_id` + `line_no`, `request_id`, `priority`.

## Dimensions

[Table](#table-dimension-tables-with-natural-keys-and-row-counts) describes each dimension and its size.

**Table: Dimension tables with natural keys and row counts.** Location is the only Type 2 dimension; the date dimension includes the member −1 for milestones not yet reached.

| Dimension | Natural key | Rows | Notes |
|---|---|---|---|
| `dim_date` | calendar date | 2,923 | 2019–2026 + member −1. Month, quarter, year, weekend, typhoon-season flag. Role-plays four times in `fact_response_action`. |
| `dim_location` | PSGC code | 1,671 | Region → province → city/municipality, population (type 1). **SCD Type 2** (see the next subsection). |
| `dim_event` | event code (`TC2024-KRISTINE`) | 31 | Local + international name, hazard type, category and rank, max wind, max signal, dates, duration. |
| `dim_organization` | org code | 13 | Government, NGO, international, LGU; source name variants resolved via aliases. |
| `dim_resource` | item code | 10 | Category (Food, Water, Non-Food, Medical, Shelter), standard unit, unit cost. |
| `dim_evacuation_center` | EC code | 1,751 | Type, barangay, capacity, PSGC of its city/municipality. SCD Type 1. |
| `dim_damage_category` | category | 4 | Population, Housing, Infrastructure, Agriculture. |
| `dim_response_type` | type code | 5 | Response type and cluster (life-saving, logistics, access). |
| `dim_lifeline` | lifeline code | 5 | Roads, bridges, power, water, communications; sector and unit of measure. |
| `dim_source_system` | batch id | per load | Lineage: source system and file each fact row came from. |

### SCD Type 2: `dim_location`

Provinces change. On 17 September 2022 a plebiscite ratified **RA 11550** (Republic Act No. 11550, 2021), splitting
Maguindanao into *Maguindanao del Norte* and *Maguindanao del Sur*. The change log
[`dbt/seeds/psgc_changes.csv`](../dbt/seeds/psgc_changes.csv) records each affected
city/municipality with its new province and effective date (2022-09-18). `dim_location`
turns it into versions.

[Table](#table-scd-type-2-versions-of-parang-maguindanao) shows the two versions of one affected town.

**Table: SCD Type 2 versions of Parang, Maguindanao.** The same PSGC code has two versions; a fact joins to the one valid on its own date, so history is reported under the provinces of the time.

| psgc_code | city_muni_name | province_name | valid_from | valid_to | is_current |
|---|---|---|---|---|---|
| 1903811000 | Parang | Maguindanao | 1900-01-01 | 2022-09-17 | false |
| 1903811000 | Parang | Maguindanao del Norte | 2022-09-18 | 9999-12-31 | true |

Facts join to the version **valid on the fact's own date**, so Typhoon Paeng (Oct 2022)
reports under the new provinces, while any earlier event would still roll up to
"Maguindanao". New PSGC releases are handled by appending rows to the change log.

## Bus matrix

[Table](#table-bus-matrix-of-facts-and-conformed-dimensions) is the bus matrix: which dimensions each fact uses.

**Table: Bus matrix of facts and conformed dimensions.** A tick means the fact uses the dimension. Dimensions ticked for several facts (date, location, event, organization, source) are the conformed dimensions that integrate the stars.

| Fact \ Dimension | Date | Location | Event | Organization | Resource | Evac Center | Damage Cat | Response Type | Lifeline | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| Damage Assessment | ✓ | ✓ | ✓ | | | | ✓ | | | ✓ |
| Evacuation Snapshot | ✓ | ✓ | ✓ | ✓ | | ✓ | | | | ✓ |
| Displacement Outside | ✓ | ✓ | ✓ | ✓ | | | | | | ✓ |
| Resource Distribution | ✓ | ✓ | ✓ | ✓ | ✓ | | | | | ✓ |
| Response Action | ✓ ×4 | ✓ | ✓ | ✓ | | | | ✓ | | ✓ |
| Lifeline Disruption | ✓ ×2 | ✓ | ✓ | ✓ | | | | | ✓ | ✓ |

## Physical design and tests

Every dimension has a primary key and every fact has foreign keys to its dimensions
(38 in total), so ERD tools such as pgAdmin or DBeaver draw the star directly. dbt tests
check that:

- keys are unique and not null, and each fact has one row per declared grain;
- every row that passed data quality reaches its fact, so inner joins drop nothing silently;
- SCD2 versions never overlap or leave gaps, and exactly one version per place is current;
- Paeng's damage in the former Maguindanao rolls up to the new provinces.

## Data marts (`mart` schema)

Materialized views refreshed by every `dbt build`, each shaped for a dashboard. A dbt test
checks that every mart adds back up to the facts it summarizes.

[Table](#table-data-marts-and-the-dashboards-they-feed) lists the eight marts, their grain and the dashboards they serve.

**Table: Data marts and the dashboards they feed.** Each materialized view pre-aggregates one view of the facts, so the dashboards never scan the facts directly.

| Mart | Grain | Used by |
|---|---|---|
| `mart_event_summary` | event | Executive: headline figures from every fact, deaths and affected per 100,000, peak displaced, relief by provider type, lifeline restoration |
| `mart_impact_cube` | `GROUP BY CUBE (year, region, hazard)`: every subtotal, labelled by `grouping_level` | Executive: region totals |
| `mart_province_event_impact` | event × province (SCD2 province at the time) | Logistics: relief vs impact; deaths and affected per 100,000 of the province |
| `mart_evacuation_daily` | event × day (sum across centers only) | Operations |
| `mart_response_performance` | `GROUPING SETS` over event, response type, priority (`All` = rolled up) | Operations |
| `mart_relief_by_org_category` | event × organization × resource category | Logistics (incl. cost of assistance by provider) |
| `mart_displacement_daily` | event × day: inside + outside evacuation centers | Operations |
| `mart_lifeline_restoration` | event × lifeline: places disrupted, restored within 72 h, median / p90 hours | Operations |

The dashboards read these marts live through the PHP API on XAMPP (`/driw/api/marts.php`),
as the read-only role `driw_web`. A JSON snapshot of the marts (`ingestion/export_marts.py` →
`web/src/data/`) is bundled as a fallback for when the warehouse is unreachable.

## Example: OLAP with `GROUP BY CUBE`

```sql
select d.year_number, r.category, sum(f.value_php) as relief_value_php
from dw.fact_resource_distribution f
join dw.dim_date d on d.date_key = f.distribution_date_key
join dw.dim_resource r using (resource_key)
group by cube (d.year_number, r.category);      -- every subtotal plus the grand total
```
