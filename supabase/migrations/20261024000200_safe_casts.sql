-- Error-tolerant conversions for the staging layer. A submitted file can hold an impossible
-- date ("10/32/2024") or time; Postgres's to_date/to_timestamp raise an error on it, which would
-- fail the whole staging model and block every load. These return NULL instead, and the
-- data-quality rules then flag the row (e.g. DATE_UNPARSEABLE, TIMESTAMP_UNPARSEABLE).
create or replace function meta.try_to_date(value text, fmt text)
returns date
language plpgsql
immutable
as $$
begin
    return to_date(value, fmt);
exception when others then
    return null;
end
$$;

create or replace function meta.try_to_timestamp(value text, fmt text)
returns timestamp
language plpgsql
immutable
as $$
begin
    return to_timestamp(value, fmt)::timestamp;
exception when others then
    return null;
end
$$;

grant usage on schema meta to driw_steward, driw_analyst, driw_regional, driw_executive;
grant execute on function meta.try_to_date(text, text), meta.try_to_timestamp(text, text)
    to driw_steward, driw_analyst, driw_regional, driw_executive;
