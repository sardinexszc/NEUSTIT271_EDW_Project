# Data Dictionary and Metadata

Generated from the live PostgreSQL catalog by `docs/build/data_dictionary.py` on 2026-10-23 22:59. Names, types, keys and nullability come from the database; descriptions are curated. Row counts are from the current build (seed 271).

Last successful load: 2026-10-23 22:54.

## Schemas (layers)

| Schema | Purpose | Objects |
|---|---|---:|
| `raw` | Landing zone. Source extracts exactly as received, every business column as text, plus lineage columns `_batch_id`, `_source_file`, `_row_number`. Loaded by `ingestion/load_raw.py` (full reload). | 5 |
| `ref` | Master and reference data: PSGC geography, canonical organizations and relief items, and the alias maps that conform source spellings to them. | 7 |
| `meta` | Pipeline metadata: one row per loaded file (`load_batch`), applied migrations, and the defect manifest written by the synthetic generator. | 3 |
| `staging` | Cleansed and conformed source data (dbt). Keeps every raw row and adds `dq_issues` (rules that fired) and `dq_status` (valid, warning, rejected, duplicate). | 7 |
| `dq` | Data-quality layer (dbt): rule catalog, issue log, scorecard, quarantine and reconciliation. | 5 |
| `dw` | Enterprise star schema (dbt): conformed dimensions and fact tables. Only valid/warning rows load. | 13 |
| `mart` | Data marts (dbt materialized views) shaped for the dashboards, including ROLAP aggregates. | 6 |
| `secure` | Region-scoped views for regional users; they run with the caller's rights (row-level security). | 2 |

## Lineage

| Source system | Source file(s) | Raw table | Staging model | Warehouse fact |
|---|---|---|---|---|
| NDRRMC situation reports | `ndrrmc/sitreps_<event>.csv` | `raw.ndrrmc_damage_report` | `staging.stg_ndrrmc_damage` | `dw.fact_damage_assessment` |
| DSWD DROMIC | `dromic/dromic_<event>.xlsx` | `raw.dromic_evacuation` | `staging.stg_dromic_evacuation` | `dw.fact_evacuation_snapshot` |
| NGO / agency partners | `ngo/distributions_<year>.json` | `raw.ngo_distribution` | `staging.stg_ngo_distribution_line` | `dw.fact_resource_distribution` |
| PAGASA | `pagasa/tc_bulletins.csv` | `raw.pagasa_event` | `staging.stg_pagasa_event` | `dw.dim_event` |
| LGU / MDRRMO | `lgu/response_logs.csv` | `raw.lgu_response_log` | `staging.stg_lgu_response` | `dw.fact_response_action` |
| PSA PSGC (community API) | `psgc_api/*.json` | `ref.psgc` | `staging.stg_location_resolution` | `dw.dim_location` |

Every fact row carries `source_key` → `dw.dim_source_system` (the file and batch it came from), and every raw row keeps its `_batch_id`, `_source_file` and `_row_number`.

## `dw` · Star schema

### `dw.dim_damage_category`

Population, Housing, Infrastructure, Agriculture. *table, 4 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `damage_category_key` | integer | PK | no | Surrogate key of dim_damage_category. |
| `damage_category` | text |  | yes | Population, Housing, Infrastructure or Agriculture. |
| `description` | text |  | yes | Description of the category. |
| `has_cost` | boolean |  | yes | Whether the category carries a PHP cost. |

### `dw.dim_date`

Calendar, 2019–2026, plus member -1 (“Not yet occurred”) for open milestones. Type 0. *table, 2,923 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `date_key` | integer | PK | no | Surrogate key of dim_date, YYYYMMDD (-1 = not yet occurred). |
| `full_date` | date |  | yes | Calendar date. |
| `day_of_month` | integer |  | yes | Day of the month, 1–31. |
| `day_name` | text |  | yes | Weekday name. |
| `day_of_week` | integer |  | yes | ISO weekday, 1 (Monday) to 7 (Sunday). |
| `is_weekend` | boolean |  | yes | Saturday or Sunday. |
| `iso_week` | integer |  | yes | ISO week number. |
| `month_number` | integer |  | yes | Month, 1–12. |
| `month_name` | text |  | yes | Month name. |
| `year_month` | text |  | yes | YYYY-MM. |
| `quarter_number` | integer |  | yes | Quarter, 1–4. |
| `quarter_name` | text |  | yes | Q1–Q4. |
| `year_number` | integer |  | yes | Calendar year. |
| `is_typhoon_season` | boolean |  | yes | June–November. |

### `dw.dim_evacuation_center`

Evacuation centers from DROMIC reports. SCD Type 1 (latest attributes). *table, 1,751 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `evacuation_center_key` | integer | PK | no | Surrogate key of dim_evacuation_center. |
| `ec_code` | text |  | yes | Evacuation-center code from DROMIC (natural key). |
| `ec_name` | text |  | yes | Evacuation-center name. |
| `ec_type` | text |  | yes | School, covered court, gymnasium, barangay hall or church. |
| `barangay` | text |  | yes | Barangay where the center is located. |
| `psgc_code` | character |  | yes | Philippine Standard Geographic Code, 10 digits (natural key). |
| `capacity_families` | integer |  | yes | Families the evacuation center can hold. |

### `dw.dim_event`

Hazard events (tropical cyclones and monsoon floods) from PAGASA bulletins. *table, 31 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `event_key` | integer | PK | no | Surrogate key of dim_event. |
| `event_code` | text |  | yes | Event natural key, TC<year>-<LOCAL NAME> (e.g. TC2024-KRISTINE); 'All' in roll-up rows. |
| `local_name` | text |  | yes | PAGASA local storm name. |
| `international_name` | text |  | yes | International (JMA) storm name. |
| `event_name` | text |  | yes | Local name with international name, e.g. Kristine (Trami). |
| `hazard_type` | text |  | yes | Tropical Cyclone or Flood (southwest monsoon). |
| `category` | text |  | yes | Category: storm category for events, resource category for relief items. |
| `category_rank` | integer |  | yes | Storm category as a number, 1 (tropical depression) to 5 (super typhoon). |
| `max_wind_kph` | integer |  | yes | Maximum sustained winds, km/h. |
| `max_signal` | integer |  | yes | Highest tropical cyclone wind signal raised. |
| `start_date` | date |  | yes | First day of the event. |
| `end_date` | date |  | yes | Last day of the event. |
| `duration_days` | integer |  | yes | Event length in days, inclusive. |
| `event_year` | integer |  | yes | Year the event started. |
| `affected_areas` | text |  | yes | Provinces named in the PAGASA bulletin, as published. |

### `dw.dim_location`

City/municipality, keyed on PSGC code. SCD Type 2: one row per period of unchanged attributes (valid_from–valid_to). *table, 1,671 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `location_key` | integer | PK | no | Surrogate key of dim_location (the SCD2 version valid on the fact's date). |
| `psgc_code` | character |  | yes | Philippine Standard Geographic Code, 10 digits (natural key). |
| `city_muni_name` | text |  | yes | Official PSGC name of the city or municipality. |
| `lgu_type` | text |  | yes | City or Municipality. |
| `province_name` | text |  | yes | Province in force on the fact's date (e.g. Maguindanao del Sur after Sep 2022). |
| `region_code` | character(10) |  | yes | PSGC region code. |
| `region_name` | text |  | yes | Region name. |
| `valid_from` | date |  | yes | SCD2: first day this version applies. |
| `valid_to` | date |  | yes | SCD2: last day this version applies (9999-12-31 = current). |
| `is_current` | boolean |  | yes | Whether this SCD2 version is the current one. |

### `dw.dim_organization`

Responding and reporting organizations (government, NGO, international, LGU). *table, 13 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `organization_key` | integer | PK | no | Surrogate key of dim_organization. |
| `org_code` | text |  | yes | Organization code (natural key). |
| `org_name` | text |  | yes | Organization name. |
| `org_type` | text |  | yes | National Government, NGO, International or LGU. |
| `parent_agency` | text |  | yes | Department the organization belongs to. |

### `dw.dim_resource`

Relief items with category, standard unit and unit cost. *table, 10 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `resource_key` | integer | PK | no | Surrogate key of dim_resource. |
| `item_code` | text |  | yes | Canonical relief item code. |
| `item_name` | text |  | yes | Relief item name. |
| `category` | text |  | yes | Category: storm category for events, resource category for relief items. |
| `standard_unit` | text |  | yes | Unit all quantities are converted to (pack, kg, liter, kit, piece). |
| `unit_cost_php` | numeric(12,2) |  | yes | Indicative unit cost, PHP. |

### `dw.dim_response_type`

Response request types and their cluster. *table, 5 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `response_type_key` | integer | PK | no | Surrogate key of dim_response_type. |
| `response_type_code` | text |  | yes | Response type code, e.g. RESCUE. |
| `response_type_name` | text |  | yes | Response type name. |
| `response_cluster` | text |  | yes | Life-saving, Logistics, or Access and infrastructure. |

### `dw.dim_source_system`

Lineage: one row per loaded source file (batch). *table, 703 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `source_key` | integer | PK | no | Surrogate key of dim_source_system (lineage to the loaded file). |
| `source_system` | text |  | yes | NDRRMC, DSWD_DROMIC, NGO, PAGASA or LGU. |
| `source_file` | text |  | yes | Source file name. |
| `loaded_at` | timestamp with time zone |  | yes | When the batch was loaded. |
| `row_count` | integer |  | yes | Rows in the source file. |

### `dw.fact_damage_assessment`

Grain: event × city/municipality × damage category (latest valid sitrep). Transaction fact. *table, 8,806 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `report_date_key` | integer | FK → dim_date | yes | Date of the sitrep the figures come from (dim_date). |
| `location_key` | integer | FK → dim_location | yes | Surrogate key of dim_location (the SCD2 version valid on the fact's date). |
| `event_key` | integer | FK → dim_event | yes | Surrogate key of dim_event. |
| `damage_category_key` | integer | FK → dim_damage_category | yes | Surrogate key of dim_damage_category. |
| `source_key` | integer | FK → dim_source_system | yes | Surrogate key of dim_source_system (lineage to the loaded file). |
| `sitrep_no` | integer |  | yes | NDRRMC situation-report number (degenerate dimension). |
| `dead` | numeric |  | yes | Deaths. |
| `injured` | numeric |  | yes | Injured persons. |
| `missing` | numeric |  | yes | Missing persons. |
| `affected_families` | numeric |  | yes | Families affected (NDRRMC). |
| `affected_persons` | numeric |  | yes | Persons affected (NDRRMC). |
| `houses_partially_damaged` | numeric |  | yes | Houses partially damaged. |
| `houses_totally_damaged` | numeric |  | yes | Houses totally destroyed. |
| `cost_php` | numeric |  | yes | Damage cost, PHP (Housing, Infrastructure, Agriculture rows). |

### `dw.fact_evacuation_snapshot`

Grain: evacuation center × day × event. Periodic snapshot; occupancy measures are semi-additive (never sum across days). *table, 31,110 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `snapshot_date_key` | integer | FK → dim_date | yes | Date of the snapshot (dim_date). |
| `location_key` | integer | FK → dim_location | yes | Surrogate key of dim_location (the SCD2 version valid on the fact's date). |
| `event_key` | integer | FK → dim_event | yes | Surrogate key of dim_event. |
| `evacuation_center_key` | integer | FK → dim_evacuation_center | yes | Surrogate key of dim_evacuation_center. |
| `organization_key` | integer | FK → dim_organization | yes | Surrogate key of dim_organization. |
| `source_key` | integer | FK → dim_source_system | yes | Surrogate key of dim_source_system (lineage to the loaded file). |
| `families_inside` | integer |  | yes | Families inside the center (semi-additive). |
| `persons_inside` | integer |  | yes | Persons inside the center (semi-additive). |
| `capacity_families` | integer |  | yes | Families the evacuation center can hold. |
| `is_over_capacity` | boolean |  | yes | Families inside exceeded the center's capacity. |

### `dw.fact_resource_distribution`

Grain: one relief item in one distribution. Transaction fact; quantities in standard units. *table, 11,179 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `distribution_date_key` | integer | FK → dim_date | yes | Date of the distribution (dim_date). |
| `location_key` | integer | FK → dim_location | yes | Surrogate key of dim_location (the SCD2 version valid on the fact's date). |
| `event_key` | integer | FK → dim_event | yes | Surrogate key of dim_event. |
| `organization_key` | integer | FK → dim_organization | yes | Surrogate key of dim_organization. |
| `resource_key` | integer | FK → dim_resource | yes | Surrogate key of dim_resource. |
| `source_key` | integer | FK → dim_source_system | yes | Surrogate key of dim_source_system (lineage to the loaded file). |
| `distribution_id` | text |  | yes | Source distribution identifier (degenerate dimension). |
| `line_no` | integer |  | yes | Line number within the distribution. |
| `quantity` | numeric |  | yes | Quantity in the item's standard unit. |
| `value_php` | numeric |  | yes | Value of the line, PHP. |
| `beneficiary_families` | integer |  | yes | Families served by the whole distribution; stored on its first line only so it stays additive. |

### `dw.fact_response_action`

Grain: one response request. Accumulating snapshot with four milestone dates. *table, 32,347 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `requested_date_key` | integer | FK → dim_date | yes | Date of the request (role-playing dim_date). |
| `dispatched_date_key` | integer | FK → dim_date | yes | Date a unit was dispatched (role-playing dim_date). |
| `arrived_date_key` | integer | FK → dim_date | yes | Date the responding unit arrived (role-playing dim_date; -1 = not yet). |
| `completed_date_key` | integer | FK → dim_date | yes | Date the request was completed (role-playing dim_date; -1 = not yet). |
| `location_key` | integer | FK → dim_location | yes | Surrogate key of dim_location (the SCD2 version valid on the fact's date). |
| `event_key` | integer | FK → dim_event | yes | Surrogate key of dim_event. |
| `response_type_key` | integer | FK → dim_response_type | yes | Surrogate key of dim_response_type. |
| `organization_key` | integer | FK → dim_organization | yes | Surrogate key of dim_organization. |
| `source_key` | integer | FK → dim_source_system | yes | Surrogate key of dim_source_system (lineage to the loaded file). |
| `request_id` | text |  | yes | Source request identifier (degenerate dimension). |
| `priority` | text |  | yes | P1 critical, P2 urgent, P3 routine ('All' in roll-up rows). |
| `requested_at` | timestamp without time zone |  | yes | Timestamp of the request. |
| `completed_at` | timestamp without time zone |  | yes | Timestamp the request was completed (null while open). |
| `hours_to_dispatch` | numeric |  | yes | Hours from request to dispatch. |
| `hours_to_arrive` | numeric |  | yes | Hours from dispatch to arrival. |
| `hours_on_site` | numeric |  | yes | Hours from arrival to completion. |
| `hours_to_complete` | numeric |  | yes | Hours from request to completion. |
| `personnel_count` | integer |  | yes | Personnel sent on the request. |
| `is_completed` | boolean |  | yes | Whether the request has been completed. |

## `mart` · Data marts

### `mart.mart_evacuation_daily`

Evacuation-center load per event per day (summed across centers only). *materialized view, 372 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `event_code` | text |  | yes | Event natural key, TC<year>-<LOCAL NAME> (e.g. TC2024-KRISTINE); 'All' in roll-up rows. |
| `snapshot_date` | date |  | yes | Date of the daily snapshot. |
| `day_of_event` | integer |  | yes | Days since the event started (negative = pre-emptive evacuation). |
| `centers_open` | bigint |  | yes | Evacuation centers with evacuees that day. |
| `families_inside` | bigint |  | yes | Families inside the center (semi-additive). |
| `persons_inside` | bigint |  | yes | Persons inside the center (semi-additive). |
| `capacity_families` | bigint |  | yes | Families the evacuation center can hold. |
| `centers_over_capacity` | bigint |  | yes | Centers where families inside exceeded capacity that day. |
| `occupancy_rate` | numeric |  | yes | Families inside divided by capacity, across open centers. |

### `mart.mart_event_summary`

One row per event: headline damage, evacuation, relief and response figures. *materialized view, 31 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `event_code` | text |  | yes | Event natural key, TC<year>-<LOCAL NAME> (e.g. TC2024-KRISTINE); 'All' in roll-up rows. |
| `event_name` | text |  | yes | Local name with international name, e.g. Kristine (Trami). |
| `local_name` | text |  | yes | PAGASA local storm name. |
| `international_name` | text |  | yes | International (JMA) storm name. |
| `hazard_type` | text |  | yes | Tropical Cyclone or Flood (southwest monsoon). |
| `category` | text |  | yes | Category: storm category for events, resource category for relief items. |
| `category_rank` | integer |  | yes | Storm category as a number, 1 (tropical depression) to 5 (super typhoon). |
| `max_signal` | integer |  | yes | Highest tropical cyclone wind signal raised. |
| `start_date` | date |  | yes | First day of the event. |
| `end_date` | date |  | yes | Last day of the event. |
| `event_year` | integer |  | yes | Year the event started. |
| `dead` | numeric |  | yes | Deaths. |
| `injured` | numeric |  | yes | Injured persons. |
| `missing` | numeric |  | yes | Missing persons. |
| `affected_families` | numeric |  | yes | Families affected (NDRRMC). |
| `affected_persons` | numeric |  | yes | Persons affected (NDRRMC). |
| `houses_partially_damaged` | numeric |  | yes | Houses partially damaged. |
| `houses_totally_damaged` | numeric |  | yes | Houses totally destroyed. |
| `damage_cost_php` | numeric |  | yes | Total damage cost, PHP. |
| `housing_cost_php` | numeric |  | yes | Housing damage, PHP. |
| `infrastructure_cost_php` | numeric |  | yes | Infrastructure damage, PHP. |
| `agriculture_cost_php` | numeric |  | yes | Agricultural damage, PHP. |
| `cities_municipalities_affected` | bigint |  | yes | Distinct cities/municipalities with reported damage. |
| `provinces_affected` | bigint |  | yes | Distinct provinces with reported damage. |
| `peak_persons_in_centers` | bigint |  | yes | Highest daily total of persons in centers (sum across centers, max across days). |
| `peak_families_in_centers` | bigint |  | yes | Highest daily total of families in centers. |
| `days_with_evacuees` | bigint |  | yes | Days on which any center held evacuees. |
| `centers_used` | bigint |  | yes | Distinct evacuation centers used during the event. |
| `over_capacity_center_days` | bigint |  | yes | Center-days in which a center was over capacity. |
| `relief_value_php` | numeric |  | yes | Relief value, PHP (standard quantity × unit cost). |
| `families_served` | bigint |  | yes | Sum of beneficiary families over distributions (a family can be served more than once). |
| `distributions` | bigint |  | yes | Number of distinct distributions. |
| `relief_php_per_affected_person` | numeric |  | yes | Relief value divided by persons affected, PHP. |
| `response_requests` | bigint |  | yes | Number of response requests. |
| `median_hours_to_dispatch` | numeric |  | yes | Median hours from request to dispatch. |
| `median_hours_to_arrive` | numeric |  | yes | Median hours from dispatch to arrival. |
| `completion_rate` | numeric |  | yes | Share of requests completed, 0–1. |

### `mart.mart_impact_cube`

GROUP BY CUBE over year × region × hazard type: every subtotal, labelled by grouping_level. *materialized view, 160 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `grouping_level` | text |  | yes | Which dimensions a CUBE row is broken down by: year, region, hazard, combinations, or grand_total. |
| `event_year` | integer |  | yes | Year the event started. |
| `region_name` | text |  | yes | Region name. |
| `hazard_type` | text |  | yes | Tropical Cyclone or Flood (southwest monsoon). |
| `events` | bigint |  | yes | Number of distinct events. |
| `dead` | numeric |  | yes | Deaths. |
| `affected_persons` | numeric |  | yes | Persons affected (NDRRMC). |
| `houses_totally_damaged` | numeric |  | yes | Houses totally destroyed. |
| `damage_cost_php` | numeric |  | yes | Total damage cost, PHP. |

### `mart.mart_province_event_impact`

Event × province impact next to relief delivered (coverage). *materialized view, 168 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `event_code` | text |  | yes | Event natural key, TC<year>-<LOCAL NAME> (e.g. TC2024-KRISTINE); 'All' in roll-up rows. |
| `event_name` | text |  | yes | Local name with international name, e.g. Kristine (Trami). |
| `event_year` | integer |  | yes | Year the event started. |
| `region_name` | text |  | yes | Region name. |
| `province_name` | text |  | yes | Province in force on the fact's date (e.g. Maguindanao del Sur after Sep 2022). |
| `dead` | numeric |  | yes | Deaths. |
| `affected_persons` | numeric |  | yes | Persons affected (NDRRMC). |
| `affected_families` | numeric |  | yes | Families affected (NDRRMC). |
| `houses_totally_damaged` | numeric |  | yes | Houses totally destroyed. |
| `damage_cost_php` | numeric |  | yes | Total damage cost, PHP. |
| `relief_value_php` | numeric |  | yes | Relief value, PHP (standard quantity × unit cost). |
| `families_served` | bigint |  | yes | Sum of beneficiary families over distributions (a family can be served more than once). |
| `relief_php_per_affected_person` | numeric |  | yes | Relief value divided by persons affected, PHP. |
| `family_coverage_ratio` | numeric |  | yes | Family servings divided by affected families. |

### `mart.mart_relief_by_org_category`

Relief delivered per event × organization × resource category. *materialized view, 730 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `event_code` | text |  | yes | Event natural key, TC<year>-<LOCAL NAME> (e.g. TC2024-KRISTINE); 'All' in roll-up rows. |
| `org_code` | text |  | yes | Organization code (natural key). |
| `org_name` | text |  | yes | Organization name. |
| `org_type` | text |  | yes | National Government, NGO, International or LGU. |
| `resource_category` | text |  | yes | Food, Water, Non-Food, Medical or Shelter. |
| `distributions` | bigint |  | yes | Number of distinct distributions. |
| `line_items` | bigint |  | yes | Number of distribution lines. |
| `relief_value_php` | numeric |  | yes | Relief value, PHP (standard quantity × unit cost). |
| `families_served` | bigint |  | yes | Sum of beneficiary families over distributions (a family can be served more than once). |

### `mart.mart_response_performance`

Response timeliness with GROUPING SETS roll-ups; 'All' marks a rolled-up value. *materialized view, 671 rows.*

| Column | Type | Key | Null | Description |
|---|---|---|---|---|
| `event_code` | text |  | yes | Event natural key, TC<year>-<LOCAL NAME> (e.g. TC2024-KRISTINE); 'All' in roll-up rows. |
| `response_type` | text |  | yes | Response type name ('All' in roll-up rows). |
| `priority` | text |  | yes | P1 critical, P2 urgent, P3 routine ('All' in roll-up rows). |
| `requests` | bigint |  | yes | Number of requests. |
| `median_hours_to_dispatch` | numeric |  | yes | Median hours from request to dispatch. |
| `p90_hours_to_dispatch` | numeric |  | yes | 90th-percentile hours from request to dispatch. |
| `median_hours_to_arrive` | numeric |  | yes | Median hours from dispatch to arrival. |
| `median_hours_to_complete` | numeric |  | yes | Median hours from request to completion. |
| `completion_rate` | numeric |  | yes | Share of requests completed, 0–1. |
| `personnel_deployed` | bigint |  | yes | Total personnel sent. |

## Supporting layers

Column-level detail for these layers is in the database itself; summarized here.

| Object | Kind | Rows | Columns |
|---|---|---:|---|
| `raw.dromic_evacuation` | table | 31,241 | report_date, disaster_name, region, province, municipality, barangay, ec_code, ec_name, ec_type, capacity_families, families_inside, persons_inside, _batch_id, _source_file, _row_number |
| `raw.lgu_response_log` | table | 32,749 | request_id, incident, province, lgu_name, request_type, priority, requested_at, dispatched_at, arrived_at, completed_at, responding_unit, personnel_count, _batch_id, _source_file, _row_number |
| `raw.ndrrmc_damage_report` | table | 16,151 | sitrep_no, report_date, incident_name, region, province, city_muni, damage_category, dead, injured, missing, affected_families, affected_persons, houses_partial, houses_total, cost_php, remarks, _batch_id, _source_file, _row_number |
| `raw.ngo_distribution` | table | 5,661 | record, _batch_id, _source_file, _row_number |
| `raw.pagasa_event` | table | 39 | local_name, international_name, category, max_wind_kph, max_signal, start_date, end_date, affected_areas, _batch_id, _source_file, _row_number |
| `ref.location_alias` | table | 0 | alias_name, alias_scope, psgc_code, match_method |
| `ref.organization` | table | 13 | org_code, org_name, org_type, parent_agency |
| `ref.organization_alias` | table | 42 | alias_name, org_code |
| `ref.psgc` | table | 43,793 | psgc_code, name, geographic_level, region_code, province_code, city_muni_code, city_class, income_class, urban_rural, population, population_census, publication, province_name |
| `ref.psgc_changes` | table | 37 | psgc_code, city_muni_name, attribute, old_value, new_value, effective_date, reference |
| `ref.resource_item` | table | 10 | item_code, item_name, category, standard_unit, unit_cost_php |
| `ref.resource_item_alias` | table | 25 | source_item_code, item_code, source_unit, to_standard_factor |
| `meta.defect_manifest` | table | 19 | source_system, defect, planted_count, seed, loaded_at |
| `meta.load_batch` | table | 703 | batch_id, source_system, source_file, row_count, started_at, finished_at, status, origin |
| `meta.schema_migration` | table | 7 | version, applied_at |
| `staging.stg_dromic_evacuation` | table | 31,241 | _batch_id, _source_file, _row_number, raw_report_date, date_format, dominant_date_format, report_date, disaster_name, province, raw_municipality, barangay, raw_ec_code, ec_name, ec_type, capacity_families, families_inside, persons_inside, psgc_code, location_match_method, event_key, ec_code, dq_issues, dq_status |
| `staging.stg_event_alias` | table | 124 | event_key, alias, start_date, end_date |
| `staging.stg_lgu_response` | table | 32,749 | _batch_id, _source_file, _row_number, request_id, incident, province, raw_lgu_name, raw_request_type, request_type, priority, requested_at, dispatched_at, arrived_at, completed_at, responding_unit, personnel_count, psgc_code, location_match_method, event_key, org_code, hours_to_dispatch, hours_to_arrive, hours_on_site, hours_to_complete, dq_issues, dq_status |
| `staging.stg_location_resolution` | table | 2,969 | raw_province, raw_name, psgc_code, official_name, match_method, edit_distance |
| `staging.stg_ndrrmc_damage` | table | 16,151 | _batch_id, _source_file, _row_number, copy_number, sitrep_no, report_date, incident_name, province, raw_city_muni, damage_category, dead, injured, missing, affected_families, affected_persons, houses_partial, houses_total, cost_php, remarks, raw_dead, raw_injured, raw_missing, raw_affected_families, raw_affected_persons, raw_houses_partial, raw_houses_total, raw_cost_php, psgc_code, location_match_method, event_key, dq_issues, dq_status |
| `staging.stg_ngo_distribution_line` | table | 11,529 | _batch_id, _source_file, _row_number, line_no, distribution_id, distributed_on, event_key, raw_event_ref, org_code, raw_organization, psgc_code, province, raw_municipality, location_match_method, beneficiary_families, item_code, source_item_code, source_unit, source_quantity, to_standard_factor, standard_unit, quantity_standard, value_php, header_issues, line_issues, dq_issues, dq_status |
| `staging.stg_pagasa_event` | table | 39 | _batch_id, _source_file, _row_number, local_name, international_name, category, max_wind_kph, max_signal, start_date, end_date, affected_areas, event_key, copy_number, key_rank, dq_issues, dq_status |
| `dq.dq_issue_log` | table | 17,722 | source_system, rule_code, field_name, severity, _batch_id, _source_file, _row_number, line_no |
| `dq.dq_quarantine` | table | 925 | source_system, _source_file, _row_number, line_no, reject_reasons, all_issues, batch_source, batch_loaded_at |
| `dq.dq_reconciliation` | table | 19 | source_system, planted_defect, detected_by, planted_count, detected_count, reconciliation_status |
| `dq.dq_rule_summary` | table | 41 | source_system, rule_code, severity, action, description, issue_count, affected_rows, source_rows, pct_rows_affected |
| `dq.dq_rules` | table | 41 | source_system, rule_code, severity, action, description, planted_defect |
| `secure.regional_event_impact` | view | 168 | event_code, event_name, region_name, province_name, dead, affected_persons, houses_totally_damaged, damage_cost_php, relief_value_php, family_servings |
| `secure.regional_response_summary` | view | 450 | event_code, event_name, region_name, response_type, requests, median_hours_to_dispatch, completion_rate |
