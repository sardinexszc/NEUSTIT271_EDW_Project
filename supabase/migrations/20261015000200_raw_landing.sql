-- Raw landing tables, one per simulated source system.
-- Every business column is TEXT on purpose: the landing zone must accept whatever the
-- source sends ("1,234", "N/A", "23-Oct-2024") so that nothing is lost before data-quality
-- rules run in the staging layer. Each row carries lineage (batch, file, row number).

-- NDRRMC situation reports: cumulative damage/casualty figures per sitrep.
create table if not exists raw.ndrrmc_damage_report (
    sitrep_no          text,
    report_date        text,
    incident_name      text,
    region             text,
    province           text,
    city_muni          text,
    damage_category    text,
    dead               text,
    injured            text,
    missing            text,
    affected_families  text,
    affected_persons   text,
    houses_partial     text,
    houses_total       text,
    cost_php           text,
    remarks            text,
    _batch_id          bigint not null references meta.load_batch (batch_id),
    _source_file       text   not null,
    _row_number        integer not null
);

-- DSWD DROMIC: daily evacuation-center occupancy (received as Excel workbooks).
create table if not exists raw.dromic_evacuation (
    report_date        text,
    disaster_name      text,
    region             text,
    province           text,
    municipality       text,
    barangay           text,
    ec_code            text,
    ec_name            text,
    ec_type            text,
    capacity_families  text,
    families_inside    text,
    persons_inside     text,
    _batch_id          bigint not null references meta.load_batch (batch_id),
    _source_file       text   not null,
    _row_number        integer not null
);

-- NGO relief distribution: semi-structured JSON from partner APIs, kept as-is.
create table if not exists raw.ngo_distribution (
    record             jsonb  not null,
    _batch_id          bigint not null references meta.load_batch (batch_id),
    _source_file       text   not null,
    _row_number        integer not null
);

-- PAGASA tropical cyclone / weather event bulletins.
create table if not exists raw.pagasa_event (
    local_name         text,
    international_name text,
    category           text,
    max_wind_kph       text,
    max_signal         text,
    start_date         text,
    end_date           text,
    affected_areas     text,
    _batch_id          bigint not null references meta.load_batch (batch_id),
    _source_file       text   not null,
    _row_number        integer not null
);

-- LGU / MDRRMO response logs: one row per assistance request, with milestone timestamps.
create table if not exists raw.lgu_response_log (
    request_id         text,
    incident           text,
    province           text,
    lgu_name           text,
    request_type       text,
    priority           text,
    requested_at       text,
    dispatched_at      text,
    arrived_at         text,
    completed_at       text,
    responding_unit    text,
    personnel_count    text,
    _batch_id          bigint not null references meta.load_batch (batch_id),
    _source_file       text   not null,
    _row_number        integer not null
);
