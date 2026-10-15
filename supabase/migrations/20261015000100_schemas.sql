-- DRIW layered architecture: one schema per warehouse layer.
-- Plain PostgreSQL 17; runs unchanged on local Postgres and on Supabase.

create schema if not exists meta;     -- ETL batch audit + migration history
create schema if not exists raw;      -- landing zone: source data exactly as received (all text)
create schema if not exists ref;      -- master/reference data (PSGC geography, canonical codes, alias maps)
create schema if not exists dq;       -- data-quality results + quarantined records
create schema if not exists staging;  -- cleansed, typed, standardized (built by dbt)
create schema if not exists dw;       -- enterprise star schema: dimensions + facts (built by dbt)
create schema if not exists mart;     -- departmental data marts / ROLAP aggregates (built by dbt)

comment on schema raw     is 'Landing zone. Source extracts stored as text, untouched, with lineage columns.';
comment on schema ref     is 'Master data: PSGC geography, canonical organizations/resources and their source aliases.';
comment on schema dq      is 'Data-quality rule results and quarantined (rejected) records.';
comment on schema staging is 'Cleansed and conformed source data (dbt views).';
comment on schema dw      is 'Enterprise Data Warehouse: conformed dimensions and fact tables (star schema).';
comment on schema mart    is 'Data marts and pre-aggregated ROLAP views for dashboards.';

-- Every ETL run is a batch; every raw row points back to the batch that loaded it.
create table if not exists meta.load_batch (
    batch_id        bigint generated always as identity primary key,
    source_system   text        not null,          -- NDRRMC | DSWD_DROMIC | NGO | PAGASA | LGU
    source_file     text        not null,
    row_count       integer,
    started_at      timestamptz not null default now(),
    finished_at     timestamptz,
    status          text        not null default 'running'
                    check (status in ('running', 'succeeded', 'failed'))
);
