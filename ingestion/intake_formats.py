"""The five report types DRIW accepts, in one place.

Each report type lists its standard columns: the column names of its raw landing table, the
header shown in the Excel template, whether a value is required, how to read it, and the drop-down
list it takes in the template. The Excel templates, the column-mapping profiles, the intake
validator and the writer of submitted files all work from these definitions.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str              # standard name = column of the raw landing table
    label: str             # header in the Excel template
    required: bool
    kind: str              # text | int | number | date | datetime
    help: str
    choices: str | None = None   # list on the template's Lists sheet
    example: str = ""


@dataclass(frozen=True)
class ReportType:
    key: str               # also the folder under data/sources/ and data/intake/
    title: str
    issuer: str
    source_system: str     # meta.load_batch.source_system / dq_rules.source_system
    rules_source: str
    raw_table: str
    staging_model: str
    output: str            # file the loader reads: xlsx | csv | json
    description: str
    columns: tuple[Column, ...]
    id_column: str | None = None   # must be unique across the warehouse

    def column(self, name: str) -> Column:
        return next(c for c in self.columns if c.name == name)


EVACUATION = ReportType(
    key="dromic",
    title="Evacuation center report",
    issuer="DSWD DROMIC / LGU social welfare office",
    source_system="DSWD_DROMIC",
    rules_source="dromic",
    raw_table="dromic_evacuation",
    staging_model="stg_dromic_evacuation",
    output="xlsx",
    description="One row per evacuation center per day: families and persons inside.",
    columns=(
        Column("report_date", "Report date", True, "date", "Date the count was taken.", example="2024-10-23"),
        Column("disaster_name", "Disaster", True, "text", "Event name (local or international).", "events", "Kristine"),
        Column("region", "Region", False, "text", "Region name.", "regions", "Bicol Region"),
        Column("province", "Province", True, "text", "Province (or Metro Manila).", "provinces", "Albay"),
        Column("municipality", "City/Municipality", True, "text", "City or municipality.", "cities", "City of Legazpi"),
        Column("barangay", "Barangay", False, "text", "Barangay of the evacuation center.", example="Bitano"),
        Column("ec_code", "Evacuation center code", False, "text",
               "The center's code. If blank, DRIW recovers it from other rows of the same center.", example="EC-ALB-001"),
        Column("ec_name", "Evacuation center", True, "text", "Name of the center.", example="Bitano Elementary School"),
        Column("ec_type", "Center type", False, "text", "School, covered court, gymnasium…", "ec_types", "School"),
        Column("capacity_families", "Capacity (families)", True, "int", "Families the center can hold.", example="120"),
        Column("families_inside", "Families inside", True, "int", "Families inside on the report date.", example="96"),
        Column("persons_inside", "Persons inside", True, "int", "Persons inside on the report date.", example="430"),
    ),
)

DAMAGE = ReportType(
    key="ndrrmc",
    title="Damage and casualty situation report",
    issuer="NDRRMC / OCD, PDRRMO, MDRRMO",
    source_system="NDRRMC",
    rules_source="ndrrmc",
    raw_table="ndrrmc_damage_report",
    staging_model="stg_ndrrmc_damage",
    output="csv",
    description="One row per city/municipality per damage category, as of one situation report.",
    columns=(
        Column("sitrep_no", "Sitrep number", True, "text", "Situation report number.", example="SitRep No. 3"),
        Column("report_date", "Report date", True, "date", "Date of the situation report.", example="2024-10-25"),
        Column("incident_name", "Incident", True, "text",
               "Incident with the international name in parentheses, e.g. Severe Tropical Storm Kristine (Trami).",
               "incidents", "Severe Tropical Storm Kristine (Trami)"),
        Column("region", "Region", False, "text", "Region name.", "regions", "Bicol Region"),
        Column("province", "Province", True, "text", "Province (or Metro Manila).", "provinces", "Albay"),
        Column("city_muni", "City/Municipality", True, "text", "City or municipality.", "cities", "Daraga"),
        Column("damage_category", "Damage category", True, "text",
               "Population, Housing, Infrastructure or Agriculture.", "damage_categories", "Population"),
        Column("dead", "Dead", False, "int", "Population rows only.", example="2"),
        Column("injured", "Injured", False, "int", "Population rows only.", example="15"),
        Column("missing", "Missing", False, "int", "Population rows only.", example="0"),
        Column("affected_families", "Affected families", False, "int", "Population rows only.", example="5400"),
        Column("affected_persons", "Affected persons", False, "int", "Population rows only.", example="23100"),
        Column("houses_partial", "Houses partially damaged", False, "int", "Housing rows only.", example="820"),
        Column("houses_total", "Houses totally damaged", False, "int", "Housing rows only.", example="96"),
        Column("cost_php", "Cost (PHP)", False, "number", "Housing, Infrastructure and Agriculture rows.", example="24000000"),
        Column("remarks", "Remarks", False, "text", "Free text.", example="Validation ongoing"),
    ),
)

RESPONSE = ReportType(
    key="lgu",
    title="Response operations log",
    issuer="LGU / MDRRMO / CDRRMO",
    source_system="LGU",
    rules_source="lgu",
    raw_table="lgu_response_log",
    staging_model="stg_lgu_response",
    output="csv",
    description="One row per request for assistance, with its four milestone times.",
    id_column="request_id",
    columns=(
        Column("request_id", "Request ID", True, "text", "Unique ticket or reference number.", example="QC-2024-0001"),
        Column("incident", "Incident", True, "text", "Event name (local or international).", "events", "Carina"),
        Column("province", "Province", True, "text", "Province (or Metro Manila).", "provinces", "Metro Manila"),
        Column("lgu_name", "City/Municipality", True, "text", "City or municipality of the request.", "cities", "Quezon City"),
        Column("request_type", "Request type", True, "text",
               "RESCUE, MEDEVAC, EVAC_ASSIST, ROAD_CLEAR or RELIEF_DELIV.", "request_types", "RESCUE"),
        Column("priority", "Priority", True, "text", "P1 (critical), P2 (urgent) or P3 (routine).", "priorities", "P1"),
        Column("requested_at", "Requested at", True, "datetime", "Date and time the request came in.", example="2024-07-24 08:15"),
        Column("dispatched_at", "Dispatched at", True, "datetime", "Date and time a team was dispatched.", example="2024-07-24 08:40"),
        Column("arrived_at", "Arrived at", False, "datetime", "Date and time the team arrived.", example="2024-07-24 09:30"),
        Column("completed_at", "Completed at", False, "datetime", "Blank while the request is still open.", example="2024-07-24 12:05"),
        Column("responding_unit", "Responding unit", True, "text", "Team or agency that responded.", "units", "MDRRMO Rescue Team"),
        Column("personnel_count", "Personnel", False, "int", "Number of responders.", example="8"),
    ),
)

EVENTS = ReportType(
    key="pagasa",
    title="Hazard event bulletin",
    issuer="PAGASA",
    source_system="PAGASA",
    rules_source="pagasa",
    raw_table="pagasa_event",
    staging_model="stg_pagasa_event",
    output="csv",
    description="One row per tropical cyclone or monsoon event.",
    columns=(
        Column("local_name", "Local name", True, "text", "PAGASA local name.", example="Kristine"),
        Column("international_name", "International name", True, "text", "International name.", example="Trami"),
        Column("category", "Category", True, "text", "Tropical Depression … Super Typhoon, or Southwest Monsoon (Habagat).",
               "categories", "Severe Tropical Storm"),
        Column("max_wind_kph", "Max wind (km/h)", False, "int", "Maximum sustained winds.", example="110"),
        Column("max_signal", "Max signal", False, "int", "Highest wind signal raised (1–5).", example="3"),
        Column("start_date", "Start date", True, "date", "First day in the Philippine Area of Responsibility.", example="2024-10-22"),
        Column("end_date", "End date", True, "date", "Last day.", example="2024-10-25"),
        Column("affected_areas", "Affected areas", False, "text", "Provinces, comma-separated.", example="Albay, Camarines Sur"),
    ),
)

RELIEF = ReportType(
    key="ngo",
    title="Relief distribution report",
    issuer="DSWD, NGOs and international partners",
    source_system="NGO",
    rules_source="ngo",
    raw_table="ngo_distribution",
    staging_model="stg_ngo_distribution_line",
    output="json",
    description="One row per relief item in a distribution; rows with the same distribution ID form one distribution.",
    id_column="distribution_id",
    columns=(
        Column("distribution_id", "Distribution ID", True, "text", "Same ID on every item row of one distribution.", example="PRC-20241024-0001"),
        Column("organization", "Organization", True, "text", "Organization that distributed.", "organizations", "Philippine Red Cross"),
        Column("event_ref", "Event", True, "text", "Event name (local or international).", "events", "Kristine"),
        Column("distributed_on", "Distributed on", True, "date", "Date of the distribution.", example="2024-10-24"),
        Column("province", "Province", True, "text", "Province (or Metro Manila).", "provinces", "Albay"),
        Column("municipality", "City/Municipality", True, "text", "City or municipality.", "cities", "Guinobatan"),
        Column("beneficiary_families", "Beneficiary families", False, "int", "Families served by the distribution.", example="350"),
        Column("item_code", "Item code", True, "text", "Relief item code, e.g. FFP (family food pack).", "item_codes", "FFP"),
        Column("unit", "Unit", True, "text", "Unit of the quantity, e.g. pack, kg, sack.", "units_of_measure", "pack"),
        Column("quantity", "Quantity", True, "number", "Quantity in that unit.", example="350"),
    ),
)

REPORT_TYPES: dict[str, ReportType] = {t.key: t for t in (EVACUATION, DAMAGE, RESPONSE, EVENTS, RELIEF)}

# Values every template offers as drop-downs that are not read from the warehouse
FIXED_LISTS = {
    "damage_categories": ["Population", "Housing", "Infrastructure", "Agriculture"],
    "request_types": ["RESCUE", "MEDEVAC", "EVAC_ASSIST", "ROAD_CLEAR", "RELIEF_DELIV"],
    "priorities": ["P1", "P2", "P3"],
    "ec_types": ["School", "Covered Court", "Gymnasium", "Barangay Hall", "Church", "Other"],
    "categories": ["Tropical Depression", "Tropical Storm", "Severe Tropical Storm", "Typhoon", "Super Typhoon",
                   "Southwest Monsoon (Habagat)"],
}
