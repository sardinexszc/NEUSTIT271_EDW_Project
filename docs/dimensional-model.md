# DRIW Dimensional Model

Star schema in the `dw` schema, built by dbt from the cleansed staging layer
(only rows with `dq_status` valid or warning). All facts share conformed dimensions,
so damage, evacuation, relief and response can be analysed side by side for the same
event and place.

## Fact tables

| Fact | Type | Grain (one row per…) | Rows* | Measures |
|---|---|---|---|---|
| `fact_damage_assessment` | Transaction | event × city/municipality × damage category | 8,810 | dead, injured, missing, affected families/persons, houses partially/totally damaged, cost (PHP) |
| `fact_evacuation_snapshot` | Periodic snapshot | evacuation center × day × event | 31,290 | families inside, persons inside, capacity, over-capacity flag |
| `fact_resource_distribution` | Transaction | distribution line item | 13,614 | quantity (standard unit), value (PHP), beneficiary families |
| `fact_response_action` | Accumulating snapshot | response request | 32,043 | hours to dispatch / arrive / on site / complete, personnel, completed flag |

\* Seed 271.

### Design decisions

- **Damage uses the latest sitrep only.** NDRRMC situation reports are cumulative, so
  summing every sitrep would double-count. The fact keeps the latest *valid* sitrep per
  event × place × category.
- **Evacuation grain includes the event.** Overlapping events (Nika, Ofel and Pepito,
  Nov 2024) can fill the same center on the same day.
- **Evacuation measures are semi-additive.** Sum across centers or places for one day; across
  days use the peak (MAX of daily totals) or the average, never the sum.
- **Header measures stay additive.** `beneficiary_families` belongs to a whole distribution, so
  it is stored on the record's first valid line only.
- **Open milestones.** A response request not yet completed has `completed_date_key = -1`
  ("Not yet occurred"), so foreign keys are never null; a later load fills it in.
- **Degenerate dimensions:** `sitrep_no`, `distribution_id` + `line_no`, `request_id`, `priority`.

## Dimensions

| Dimension | Natural key | Rows | Notes |
|---|---|---|---|
| `dim_date` | calendar date | 2,923 | 2019–2026 + member −1. Month, quarter, year, weekend, typhoon-season flag. Role-plays four times in `fact_response_action`. |
| `dim_location` | PSGC code | 1,671 | Region → province → city/municipality. **SCD Type 2** (see below). |
| `dim_event` | event code (`TC2024-KRISTINE`) | 31 | Local + international name, hazard type, category and rank, max wind, max signal, dates, duration. |
| `dim_organization` | org code | 13 | Government, NGO, international, LGU; source name variants resolved via aliases. |
| `dim_resource` | item code | 10 | Category (Food, Water, Non-Food, Medical, Shelter), standard unit, unit cost. |
| `dim_evacuation_center` | EC code | 1,796 | Type, barangay, capacity, PSGC of its city/municipality. SCD Type 1. |
| `dim_damage_category` | category | 4 | Population, Housing, Infrastructure, Agriculture. |
| `dim_response_type` | type code | 5 | Response type and cluster (life-saving, logistics, access). |
| `dim_source_system` | batch id | per load | Lineage: source system and file each fact row came from. |

### SCD Type 2: `dim_location`

Provinces change. On 17 September 2022 a plebiscite ratified **RA 11550**, splitting
Maguindanao into *Maguindanao del Norte* and *Maguindanao del Sur*. The change log
[`dbt/seeds/psgc_changes.csv`](../dbt/seeds/psgc_changes.csv) records each affected
city/municipality with its new province and effective date (2022-09-18). `dim_location`
turns it into versions:

| psgc_code | city_muni_name | province_name | valid_from | valid_to | is_current |
|---|---|---|---|---|---|
| 1903811000 | Parang | Maguindanao | 1900-01-01 | 2022-09-17 | false |
| 1903811000 | Parang | Maguindanao del Norte | 2022-09-18 | 9999-12-31 | true |

Facts join to the version **valid on the fact's own date**, so Typhoon Paeng (Oct 2022)
reports under the new provinces, while any earlier event would still roll up to
"Maguindanao". New PSGC releases are handled by appending rows to the change log.

## Bus matrix

| Fact \ Dimension | Date | Location | Event | Organization | Resource | Evac Center | Damage Cat | Response Type | Source |
|---|---|---|---|---|---|---|---|---|---|
| Damage Assessment | ✓ | ✓ | ✓ | | | | ✓ | | ✓ |
| Evacuation Snapshot | ✓ | ✓ | ✓ | ✓ | | ✓ | | | ✓ |
| Resource Distribution | ✓ | ✓ | ✓ | ✓ | ✓ | | | | ✓ |
| Response Action | ✓ ×4 | ✓ | ✓ | ✓ | | | | ✓ | ✓ |

## Physical design and tests

Every dimension has a primary key and every fact has foreign keys to its dimensions
(26 in total), so ERD tools such as pgAdmin or DBeaver draw the star directly. dbt tests
check that:

- keys are unique and not null, and each fact has one row per declared grain;
- every row that passed data quality reaches its fact, so inner joins drop nothing silently;
- SCD2 versions never overlap or leave gaps, and exactly one version per place is current;
- Paeng's damage in the former Maguindanao rolls up to the new provinces.

## Example: OLAP with `GROUP BY CUBE`

```sql
select d.year_number, r.category, sum(f.value_php) as relief_value_php
from dw.fact_resource_distribution f
join dw.dim_date d on d.date_key = f.distribution_date_key
join dw.dim_resource r using (resource_key)
group by cube (d.year_number, r.category);      -- every subtotal plus the grand total
```
