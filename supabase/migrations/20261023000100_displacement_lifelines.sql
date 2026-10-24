-- Landing tables for two more source feeds (all business columns TEXT, as in 20261015000200).

-- DSWD DROMIC, sheet "Outside ECs": families staying with relatives or friends, per
-- city/municipality per day. Usually far more people than inside evacuation centers.
create table if not exists raw.dromic_displaced_outside (
    report_date        text,
    disaster_name      text,
    region             text,
    province           text,
    municipality       text,
    families_outside   text,
    persons_outside    text,
    _batch_id          bigint not null references meta.load_batch (batch_id),
    _source_file       text   not null,
    _row_number        integer not null
);

-- NDRRMC sitrep lifelines: roads and bridges not passable, power, water and communication
-- outages per city/municipality, with the time service was restored (blank = not yet).
create table if not exists raw.ndrrmc_lifeline_status (
    incident_name      text,
    region             text,
    province           text,
    city_muni          text,
    lifeline           text,
    units_affected     text,
    interrupted_at     text,
    restored_at        text,
    _batch_id          bigint not null references meta.load_batch (batch_id),
    _source_file       text   not null,
    _row_number        integer not null
);
