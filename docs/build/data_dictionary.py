"""Generate docs/data-dictionary.md from the live database catalog.

Column names, types, keys and nullability come from PostgreSQL itself, so the dictionary
always matches the warehouse; the business descriptions below are curated.

    python docs/build/data_dictionary.py
"""

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ingestion"))
from common import connect  # noqa: E402

OUT = ROOT / "docs" / "data-dictionary.md"

SCHEMAS = {
    "raw": "Landing zone. Source extracts exactly as received, every business column as text, plus lineage "
           "columns `_batch_id`, `_source_file`, `_row_number`. Loaded by `ingestion/load_raw.py` (full reload).",
    "ref": "Master and reference data: PSGC geography, canonical organizations and relief items, and the alias "
           "maps that conform source spellings to them.",
    "meta": "Pipeline metadata: one row per loaded file (`load_batch`), applied migrations, and the defect "
            "manifest written by the synthetic generator.",
    "staging": "Cleansed and conformed source data (dbt). Keeps every raw row and adds `dq_issues` (rules that "
               "fired) and `dq_status` (valid, warning, rejected, duplicate).",
    "dq": "Data-quality layer (dbt): rule catalog, issue log, scorecard, quarantine and reconciliation.",
    "dw": "Enterprise star schema (dbt): conformed dimensions and fact tables. Only valid/warning rows load.",
    "mart": "Data marts (dbt materialized views) shaped for the dashboards, including ROLAP aggregates.",
    "secure": "Region-scoped views for regional users; they run with the caller's rights (row-level security).",
}

TABLES = {
    "dim_date": "Calendar, 2019–2026, plus member -1 (“Not yet occurred”) for open milestones. Type 0.",
    "dim_location": "City/municipality, keyed on PSGC code. SCD Type 2: one row per period of unchanged "
                    "attributes (valid_from–valid_to).",
    "dim_event": "Hazard events (tropical cyclones and monsoon floods) from PAGASA bulletins.",
    "dim_organization": "Responding and reporting organizations (government, NGO, international, LGU).",
    "dim_resource": "Relief items with category, standard unit and unit cost.",
    "dim_evacuation_center": "Evacuation centers from DROMIC reports. SCD Type 1 (latest attributes).",
    "dim_damage_category": "Population, Housing, Infrastructure, Agriculture.",
    "dim_response_type": "Response request types and their cluster.",
    "dim_source_system": "Lineage: one row per loaded source file (batch).",
    "dim_lifeline": "Lifelines tracked in NDRRMC sitreps: roads, bridges, power, water and communications.",
    "fact_damage_assessment": "Grain: event × city/municipality × damage category (latest valid sitrep). "
                              "Transaction fact.",
    "fact_evacuation_snapshot": "Grain: evacuation center × day × event. Periodic snapshot; occupancy measures "
                                "are semi-additive (never sum across days).",
    "fact_resource_distribution": "Grain: one relief item in one distribution. Transaction fact; quantities in "
                                  "standard units.",
    "fact_response_action": "Grain: one response request. Accumulating snapshot with four milestone dates.",
    "fact_displacement_outside": "Grain: city/municipality × day × event. Periodic snapshot of families displaced "
                                 "outside evacuation centers (with relatives or friends); semi-additive.",
    "fact_lifeline_disruption": "Grain: event × city/municipality × lifeline. Accumulating snapshot: opens when the "
                                "lifeline goes down, closes when service is restored.",
    "mart_event_summary": "One row per event: headline damage, evacuation, relief and response figures.",
    "mart_impact_cube": "GROUP BY CUBE over year × region × hazard type: every subtotal, labelled by grouping_level.",
    "mart_province_event_impact": "Event × province impact next to relief delivered (coverage).",
    "mart_evacuation_daily": "Evacuation-center load per event per day (summed across centers only).",
    "mart_response_performance": "Response timeliness with GROUPING SETS roll-ups; 'All' marks a rolled-up value.",
    "mart_relief_by_org_category": "Relief delivered per event × organization × resource category.",
    "mart_displacement_daily": "Everyone displaced per event per day: inside evacuation centers plus outside.",
    "mart_lifeline_restoration": "Per event × lifeline: places disrupted, restored, still down, and hours to restore.",
}

COLUMNS = {
    "affected_areas": "Provinces named in the PAGASA bulletin, as published.",
    "affected_families": "Families affected (NDRRMC).",
    "affected_persons": "Persons affected (NDRRMC).",
    "agriculture_cost_php": "Agricultural damage, PHP.",
    "arrived_date_key": "Date the responding unit arrived (role-playing dim_date; -1 = not yet).",
    "barangay": "Barangay where the center is located.",
    "beneficiary_families": "Families served by the whole distribution; stored on its first line only so it stays additive.",
    "capacity_families": "Families the evacuation center can hold.",
    "category": "Category: storm category for events, resource category for relief items.",
    "category_rank": "Storm category as a number, 1 (tropical depression) to 5 (super typhoon).",
    "centers_open": "Evacuation centers with evacuees that day.",
    "centers_over_capacity": "Centers where families inside exceeded capacity that day.",
    "centers_used": "Distinct evacuation centers used during the event.",
    "cities_municipalities_affected": "Distinct cities/municipalities with reported damage.",
    "city_muni_name": "Official PSGC name of the city or municipality.",
    "completed_at": "Timestamp the request was completed (null while open).",
    "completed_date_key": "Date the request was completed (role-playing dim_date; -1 = not yet).",
    "completion_rate": "Share of requests completed, 0–1.",
    "cost_php": "Damage cost, PHP (Housing, Infrastructure, Agriculture rows).",
    "damage_category": "Population, Housing, Infrastructure or Agriculture.",
    "damage_category_key": "Surrogate key of dim_damage_category.",
    "damage_cost_php": "Total damage cost, PHP.",
    "date_key": "Surrogate key of dim_date, YYYYMMDD (-1 = not yet occurred).",
    "day_name": "Weekday name.",
    "day_of_event": "Days since the event started (negative = pre-emptive evacuation).",
    "day_of_month": "Day of the month, 1–31.",
    "day_of_week": "ISO weekday, 1 (Monday) to 7 (Sunday).",
    "days_with_evacuees": "Days on which any center held evacuees.",
    "dead": "Deaths.",
    "description": "Description of the category.",
    "dispatched_date_key": "Date a unit was dispatched (role-playing dim_date).",
    "distribution_date_key": "Date of the distribution (dim_date).",
    "distribution_id": "Source distribution identifier (degenerate dimension).",
    "distributions": "Number of distinct distributions.",
    "duration_days": "Event length in days, inclusive.",
    "ec_code": "Evacuation-center code from DROMIC (natural key).",
    "ec_name": "Evacuation-center name.",
    "ec_type": "School, covered court, gymnasium, barangay hall or church.",
    "end_date": "Last day of the event.",
    "evacuation_center_key": "Surrogate key of dim_evacuation_center.",
    "event_code": "Event natural key, TC<year>-<LOCAL NAME> (e.g. TC2024-KRISTINE); 'All' in roll-up rows.",
    "event_key": "Surrogate key of dim_event.",
    "event_name": "Local name with international name, e.g. Kristine (Trami).",
    "event_year": "Year the event started.",
    "events": "Number of distinct events.",
    "families_inside": "Families inside the center (semi-additive).",
    "families_served": "Sum of beneficiary families over distributions (a family can be served more than once).",
    "family_coverage_ratio": "Family servings divided by affected families.",
    "full_date": "Calendar date.",
    "grouping_level": "Which dimensions a CUBE row is broken down by: year, region, hazard, combinations, or grand_total.",
    "has_cost": "Whether the category carries a PHP cost.",
    "hazard_type": "Tropical Cyclone or Flood (southwest monsoon).",
    "hours_on_site": "Hours from arrival to completion.",
    "hours_to_arrive": "Hours from dispatch to arrival.",
    "hours_to_complete": "Hours from request to completion.",
    "hours_to_dispatch": "Hours from request to dispatch.",
    "houses_partially_damaged": "Houses partially damaged.",
    "houses_totally_damaged": "Houses totally destroyed.",
    "housing_cost_php": "Housing damage, PHP.",
    "infrastructure_cost_php": "Infrastructure damage, PHP.",
    "injured": "Injured persons.",
    "international_name": "International (JMA) storm name.",
    "is_completed": "Whether the request has been completed.",
    "is_current": "Whether this SCD2 version is the current one.",
    "is_over_capacity": "Families inside exceeded the center's capacity.",
    "is_typhoon_season": "June–November.",
    "is_weekend": "Saturday or Sunday.",
    "iso_week": "ISO week number.",
    "item_code": "Canonical relief item code.",
    "item_name": "Relief item name.",
    "lgu_type": "City or Municipality.",
    "line_items": "Number of distribution lines.",
    "line_no": "Line number within the distribution.",
    "loaded_at": "When the batch was loaded.",
    "local_name": "PAGASA local storm name.",
    "location_key": "Surrogate key of dim_location (the SCD2 version valid on the fact's date).",
    "max_signal": "Highest tropical cyclone wind signal raised.",
    "max_wind_kph": "Maximum sustained winds, km/h.",
    "median_hours_to_arrive": "Median hours from dispatch to arrival.",
    "median_hours_to_complete": "Median hours from request to completion.",
    "median_hours_to_dispatch": "Median hours from request to dispatch.",
    "missing": "Missing persons.",
    "month_name": "Month name.",
    "month_number": "Month, 1–12.",
    "occupancy_rate": "Families inside divided by capacity, across open centers.",
    "org_code": "Organization code (natural key).",
    "org_name": "Organization name.",
    "org_type": "National Government, NGO, International or LGU.",
    "organization_key": "Surrogate key of dim_organization.",
    "over_capacity_center_days": "Center-days in which a center was over capacity.",
    "p90_hours_to_dispatch": "90th-percentile hours from request to dispatch.",
    "parent_agency": "Department the organization belongs to.",
    "peak_families_in_centers": "Highest daily total of families in centers.",
    "peak_persons_in_centers": "Highest daily total of persons in centers (sum across centers, max across days).",
    "personnel_count": "Personnel sent on the request.",
    "personnel_deployed": "Total personnel sent.",
    "persons_inside": "Persons inside the center (semi-additive).",
    "priority": "P1 critical, P2 urgent, P3 routine ('All' in roll-up rows).",
    "province_name": "Province in force on the fact's date (e.g. Maguindanao del Sur after Sep 2022).",
    "provinces_affected": "Distinct provinces with reported damage.",
    "psgc_code": "Philippine Standard Geographic Code, 10 digits (natural key).",
    "quantity": "Quantity in the item's standard unit.",
    "quarter_name": "Q1–Q4.",
    "quarter_number": "Quarter, 1–4.",
    "region_code": "PSGC region code.",
    "region_name": "Region name.",
    "relief_php_per_affected_person": "Relief value divided by persons affected, PHP.",
    "relief_value_php": "Relief value, PHP (standard quantity × unit cost).",
    "report_date_key": "Date of the sitrep the figures come from (dim_date).",
    "request_id": "Source request identifier (degenerate dimension).",
    "requested_at": "Timestamp of the request.",
    "requested_date_key": "Date of the request (role-playing dim_date).",
    "requests": "Number of requests.",
    "resource_category": "Food, Water, Non-Food, Medical or Shelter.",
    "resource_key": "Surrogate key of dim_resource.",
    "response_cluster": "Life-saving, Logistics, or Access and infrastructure.",
    "response_requests": "Number of response requests.",
    "response_type": "Response type name ('All' in roll-up rows).",
    "response_type_code": "Response type code, e.g. RESCUE.",
    "response_type_key": "Surrogate key of dim_response_type.",
    "response_type_name": "Response type name.",
    "row_count": "Rows in the source file.",
    "sitrep_no": "NDRRMC situation-report number (degenerate dimension).",
    "snapshot_date": "Date of the daily snapshot.",
    "snapshot_date_key": "Date of the snapshot (dim_date).",
    "source_file": "Source file name.",
    "source_key": "Surrogate key of dim_source_system (lineage to the loaded file).",
    "source_system": "NDRRMC, DSWD_DROMIC, NGO, PAGASA or LGU.",
    "standard_unit": "Unit all quantities are converted to (pack, kg, liter, kit, piece).",
    "start_date": "First day of the event.",
    "unit_cost_php": "Indicative unit cost, PHP.",
    "valid_from": "SCD2: first day this version applies.",
    "valid_to": "SCD2: last day this version applies (9999-12-31 = current).",
    "value_php": "Value of the line, PHP.",
    "year_month": "YYYY-MM.",
    "year_number": "Calendar year.",
    "affected_area_population": "Population of the cities/municipalities that reported damage (denominator of the per-100k rates).",
    "affected_per_100k": "Persons affected per 100,000 population of the affected places (Sendai target B).",
    "dead_per_100k": "Deaths per 100,000 population (Sendai target A); event: affected places, province: whole province.",
    "dead_per_100k_national": "Deaths per 100,000 of the national population.",
    "families_outside": "Families displaced outside evacuation centers (semi-additive).",
    "hours_to_restore": "Hours from interruption to restoration (null while still down).",
    "interrupted_at": "Timestamp the lifeline went down.",
    "interrupted_date_key": "Date the lifeline went down (role-playing dim_date).",
    "is_restored": "Whether service has been restored.",
    "lifeline": "Lifeline code as reported: ROAD, BRIDGE, POWER, WATER or COMMS.",
    "lifeline_code": "Lifeline code (natural key): ROAD, BRIDGE, POWER, WATER or COMMS.",
    "lifeline_disruptions": "Places × lifelines that went down during the event.",
    "lifeline_key": "Surrogate key of dim_lifeline.",
    "lifeline_name": "Lifeline name, e.g. Road sections not passable.",
    "lifeline_sector": "Transport or Utilities.",
    "lifelines_still_down": "Disruptions not yet restored at the latest sitrep.",
    "median_hours_to_restore": "Median hours from interruption to restoration.",
    "missing_per_100k": "Missing persons per 100,000 population of the affected places.",
    "p90_hours_to_restore": "90th-percentile hours from interruption to restoration.",
    "peak_persons_displaced": "Highest daily total of persons displaced, inside plus outside centers.",
    "peak_persons_outside_centers": "Highest daily total of persons displaced outside centers.",
    "persons_displaced": "Persons inside plus outside evacuation centers that day.",
    "persons_outside": "Persons displaced outside evacuation centers (semi-additive).",
    "places_disrupted": "Cities/municipalities where the lifeline went down.",
    "places_restored": "Of those, places where service was restored.",
    "places_still_down": "Places still without the lifeline at the latest sitrep.",
    "population": "Residents (estimate: barangay count × 2,600 unless a census figure is loaded).",
    "population_census": "Source of the population figure (census name or 'Estimate').",
    "population_source": "Source of the population figure (census name or 'Estimate').",
    "province_population": "Population of the whole province at the time of the event.",
    "relief_international_php": "Relief value provided by international organizations (UN), PHP.",
    "relief_lgu_php": "Relief value provided by local government units, PHP.",
    "relief_national_government_php": "Relief value provided by national government (DSWD), PHP.",
    "relief_ngo_php": "Relief value provided by NGOs, PHP.",
    "restored_at": "Timestamp service was restored (null while still down).",
    "restored_date_key": "Date service was restored (role-playing dim_date; -1 = not yet).",
    "restored_within_72h": "Places where service came back within 72 hours.",
    "share_outside_centers": "Share of displaced persons staying outside centers, 0–1.",
    "share_restored_within_72h": "Share of disrupted places restored within 72 hours, 0–1.",
    "unit_of_measure": "What units_affected counts: road sections, bridges or barangays.",
    "units_affected": "Road sections, bridges or barangays affected.",
}


def main() -> None:
    with connect() as conn:
        tables = conn.execute("""
            select n.nspname, c.relname, c.relkind, c.reltuples::bigint
            from pg_class c join pg_namespace n on n.oid = c.relnamespace
            where n.nspname = any (%s) and c.relkind in ('r', 'v', 'm')
            order by array_position(%s, n.nspname::text), c.relname""",
                             (list(SCHEMAS), list(SCHEMAS))).fetchall()
        columns = conn.execute("""
            select n.nspname, c.relname, a.attname, replace(format_type(a.atttypid, a.atttypmod), 'bpchar', 'character'), a.attnotnull
            from pg_attribute a join pg_class c on c.oid = a.attrelid join pg_namespace n on n.oid = c.relnamespace
            where n.nspname = any (%s) and c.relkind in ('r', 'v', 'm') and a.attnum > 0 and not a.attisdropped
            order by n.nspname, c.relname, a.attnum""", (list(SCHEMAS),)).fetchall()
        keys = conn.execute("""
            select n.nspname, c.relname, a.attname, k.contype, k.confrelid::regclass::text
            from pg_constraint k join pg_class c on c.oid = k.conrelid join pg_namespace n on n.oid = c.relnamespace
            join pg_attribute a on a.attrelid = k.conrelid and a.attnum = any (k.conkey)
            where n.nspname = any (%s) and k.contype in ('p', 'f')""", (list(SCHEMAS),)).fetchall()
        counts = {(s, t): conn.execute(f'select count(*) from "{s}"."{t}"').fetchone()[0] for s, t, _, _ in tables}
        last_load = conn.execute("select max(finished_at) from meta.load_batch where status = 'succeeded'").fetchone()[0]

    cols_by_table, key_marks = {}, {}
    for s, t, col, typ, notnull in columns:
        cols_by_table.setdefault((s, t), []).append((col, typ, notnull))
    for s, t, col, kind, ref in keys:
        mark = "PK" if kind == "p" else f"FK → {ref.split('.')[-1]}"
        key_marks[(s, t, col)] = (key_marks.get((s, t, col), "") + ", " + mark).strip(", ")

    kinds = {"r": "table", "v": "view", "m": "materialized view"}
    lines = [
        "# Data Dictionary and Metadata",
        "",
        f"Generated from the live PostgreSQL catalog by `docs/build/data_dictionary.py` on "
        f"{datetime.now():%Y-%m-%d %H:%M}. Names, types, keys and nullability come from the database; "
        "descriptions are curated. Row counts are from the current build (seed 271).",
        "",
        f"Last successful load: {last_load:%Y-%m-%d %H:%M}." if last_load else "",
        "",
        "## Schemas (layers)",
        "",
        "**Table: Database schemas and the layer each one holds.** Each schema is one layer of the "
        "architecture, from raw extracts to the marts the dashboards read; *Objects* counts its tables "
        "and views.",
        "",
        "| Schema | Purpose | Objects |",
        "|---|---|---:|",
    ]
    for s, purpose in SCHEMAS.items():
        n = sum(1 for t in tables if t[0] == s)
        lines.append(f"| `{s}` | {purpose} | {n} |")

    lines += ["", "## Lineage", "",
              "**Table: Lineage from each source file to its warehouse table.** Read a row left to right to "
              "follow one source through the raw, staging and warehouse layers; the same path can be followed "
              "backwards from any figure on a dashboard.", "",
              "| Source system | Source file(s) | Raw table | Staging model | Warehouse fact |",
              "|---|---|---|---|---|",
              "| NDRRMC situation reports | `ndrrmc/sitreps_<event>.csv` | `raw.ndrrmc_damage_report` | "
              "`staging.stg_ndrrmc_damage` | `dw.fact_damage_assessment` |",
              "| NDRRMC lifeline status | `ndrrmc/lifelines/lifelines_<event>.csv` | `raw.ndrrmc_lifeline_status` | "
              "`staging.stg_ndrrmc_lifeline` | `dw.fact_lifeline_disruption` |",
              "| DSWD DROMIC | `dromic/dromic_<event>.xlsx` | `raw.dromic_evacuation` | `staging.stg_dromic_evacuation` | "
              "`dw.fact_evacuation_snapshot` |",
              "| DSWD DROMIC, sheet *Outside ECs* | `dromic/dromic_<event>.xlsx` | `raw.dromic_displaced_outside` | "
              "`staging.stg_dromic_displaced_outside` | `dw.fact_displacement_outside` |",
              "| NGO / agency partners | `ngo/distributions_<year>.json` | `raw.ngo_distribution` | "
              "`staging.stg_ngo_distribution_line` | `dw.fact_resource_distribution` |",
              "| PAGASA | `pagasa/tc_bulletins.csv` | `raw.pagasa_event` | `staging.stg_pagasa_event` | `dw.dim_event` |",
              "| LGU / MDRRMO | `lgu/response_logs.csv` | `raw.lgu_response_log` | `staging.stg_lgu_response` | "
              "`dw.fact_response_action` |",
              "| PSA PSGC (community API) | `psgc_api/*.json` | `ref.psgc` | `staging.stg_location_resolution` | "
              "`dw.dim_location` |",
              "",
              "Every fact row carries `source_key` → `dw.dim_source_system` (the file and batch it came from), and "
              "every raw row keeps its `_batch_id`, `_source_file` and `_row_number`.", ""]

    for schema in ["dw", "mart"]:
        lines += [f"## `{schema}` · {'Star schema' if schema == 'dw' else 'Data marts'}", ""]
        for s, t, kind, _ in tables:
            if s != schema:
                continue
            lines += [f"### `{s}.{t}`", "",
                      f"**Table: Columns of `{s}.{t}`.** {TABLES.get(t, '')} *{kinds[kind].capitalize()}, "
                      f"{counts[(s, t)]:,} rows.* PK and FK mark the primary and foreign keys; *Null* says "
                      "whether a value may be missing.", "",
                      "| Column | Type | Key | Null | Description |", "|---|---|---|---|---|"]
            for col, typ, notnull in cols_by_table[(s, t)]:
                lines.append(f"| `{col}` | {typ} | {key_marks.get((s, t, col), '')} | "
                             f"{'no' if notnull else 'yes'} | {COLUMNS.get(col, '')} |")
            lines.append("")

    lines += ["## Supporting layers", "",
              "Column-level detail for these layers is in the database itself; summarized here.", "",
              "**Table: Supporting objects in the raw, reference, staging, data-quality and governance "
              "layers.** These feed or protect the star schema; users of the dashboards never read them "
              "directly.", "",
              "| Object | Kind | Rows | Columns |", "|---|---|---:|---|"]
    for s, t, kind, _ in tables:
        if s in ("dw", "mart"):
            continue
        names = ", ".join(c for c, _, _ in cols_by_table[(s, t)])
        lines.append(f"| `{s}.{t}` | {kinds[kind]} | {counts[(s, t)]:,} | {names} |")
    lines.append("")
    missing = sorted({c for (s, _), cs in cols_by_table.items() if s in ("dw", "mart") for c, _, _ in cs} - set(COLUMNS))
    if missing:
        print("columns without a description:", ", ".join(missing))
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
