-- Support objects for the data-quality layer.

-- Levenshtein distance for fuzzy matching of misspelled place names.
-- Installed in an `extensions` schema, the same convention Supabase uses.
create schema if not exists extensions;
create extension if not exists fuzzystrmatch with schema extensions;

-- Province (or "Metro Manila") for cities/municipalities, so sources that report
-- "province + municipality" can be matched without re-deriving the hierarchy.
alter table ref.psgc add column if not exists province_name text;

-- What the synthetic generator says it planted, so detected defects can be reconciled.
create table if not exists meta.defect_manifest (
    source_system   text    not null,     -- ndrrmc | dromic | ngo | lgu | pagasa
    defect          text    not null,
    planted_count   integer not null,
    seed            integer not null,
    loaded_at       timestamptz not null default now(),
    primary key (source_system, defect)
);
