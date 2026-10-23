-- NDRRMC lifeline status per city/municipality x lifeline (roads, bridges, power, water,
-- communications), typed and checked. One row per raw row. A blank restored_at means the
-- service was still down at the final sitrep.

{%- set lifelines = ['ROAD', 'BRIDGE', 'POWER', 'WATER', 'COMMS'] %}
{%- set ts_pattern = '^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}$' %}

with typed as (
    select
        _batch_id,
        _source_file,
        _row_number,
        incident_name,
        province,
        city_muni                                      as raw_city_muni,
        upper(trim(lifeline))                          as lifeline,
        {{ clean_number('units_affected') }}::int      as units_affected,
        {%- for col in ['interrupted_at', 'restored_at'] %}
        case when {{ col }} ~ '{{ ts_pattern }}' then to_timestamp({{ col }}, 'YYYY-MM-DD HH24:MI')::timestamp end
            as {{ col }},
        {%- endfor %}
        nullif(trim(restored_at), '')                  as raw_restored_at
    from {{ source('raw', 'ndrrmc_lifeline_status') }}
),

resolved as (
    select t.*, loc.psgc_code, loc.match_method as location_match_method, ev.event_key
    from typed t
    left join {{ ref('stg_location_resolution') }} loc
        on loc.raw_province = t.province and loc.raw_name = t.raw_city_muni
    {#- same incident naming as the damage sitreps: the international name is the last (...) #}
    {{ event_lookup("substring(t.incident_name from '\\(([^)]+)\\)\\s*$')", 't.interrupted_at::date', 'ev') }}
),

checked as (
    select
        *,
        array_remove(array[
            case when lifeline not in ('{{ lifelines | join("', '") }}') or lifeline is null
                 then 'LIFELINE_UNKNOWN' end,
            case when interrupted_at is null or (raw_restored_at is not null and restored_at is null)
                 then 'TIMESTAMP_UNPARSEABLE' end,
            case when restored_at < interrupted_at then 'RESTORED_BEFORE_INTERRUPTED' end,
            case when restored_at is null and interrupted_at is not null and raw_restored_at is null
                 then 'LIFELINE_NOT_RESTORED' end,
            case when location_match_method in ('normalized', 'fuzzy') then 'LOC_NAME_VARIANT' end,
            case when psgc_code is null then 'LOC_UNMATCHED' end,
            case when event_key is null then 'EVENT_UNRESOLVED' end
        ], null) as dq_issues
    from resolved
)

select
    *,
    {{ dq_status('dq_issues',
                 ['LIFELINE_UNKNOWN', 'TIMESTAMP_UNPARSEABLE', 'RESTORED_BEFORE_INTERRUPTED',
                  'LOC_UNMATCHED', 'EVENT_UNRESOLVED'],
                 []) }} as dq_status
from checked
