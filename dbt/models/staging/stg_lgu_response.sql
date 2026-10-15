-- LGU / MDRRMO response requests with milestone timestamps, typed and checked.

{%- set standard_types = ['RESCUE', 'MEDEVAC', 'EVAC_ASSIST', 'ROAD_CLEAR', 'RELIEF_DELIV'] %}
{%- set ts_pattern = '^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}$' %}

with typed as (
    select
        _batch_id,
        _source_file,
        _row_number,
        trim(request_id)          as request_id,
        trim(incident)            as incident,
        province,
        lgu_name                  as raw_lgu_name,
        trim(request_type)        as raw_request_type,
        case
            when upper(trim(request_type)) in ('{{ standard_types | join("', '") }}') then upper(trim(request_type))
            when upper(trim(request_type)) = 'RESQ' then 'RESCUE'
            when upper(trim(request_type)) = 'MEDICAL' then 'MEDEVAC'
        end                       as request_type,
        trim(priority)            as priority,
        {%- for col in ['requested_at', 'dispatched_at', 'arrived_at', 'completed_at'] %}
        case when {{ col }} ~ '{{ ts_pattern }}' then to_timestamp({{ col }}, 'YYYY-MM-DD HH24:MI')::timestamp end
            as {{ col }},
        {%- endfor %}
        trim(responding_unit)     as responding_unit,
        {{ clean_number('personnel_count') }}::int as personnel_count
    from {{ source('raw', 'lgu_response_log') }}
),

resolved as (
    select t.*, loc.psgc_code, loc.match_method as location_match_method, ev.event_key
    from typed t
    left join {{ ref('stg_location_resolution') }} loc
        on loc.raw_province = t.province and loc.raw_name = t.raw_lgu_name
    {{ event_lookup('t.incident', 't.requested_at::date', 'ev') }}
),

checked as (
    select
        *,
        round(extract(epoch from dispatched_at - requested_at) / 3600.0, 2) as hours_to_dispatch,
        round(extract(epoch from arrived_at - dispatched_at) / 3600.0, 2)   as hours_to_arrive,
        round(extract(epoch from completed_at - arrived_at) / 3600.0, 2)    as hours_on_site,
        round(extract(epoch from completed_at - requested_at) / 3600.0, 2)  as hours_to_complete,
        array_remove(array[
            case when request_type is not null
                  and upper(raw_request_type) not in ('{{ standard_types | join("', '") }}')
                 then 'REQUEST_TYPE_MAPPED' end,
            case when request_type is null then 'REQUEST_TYPE_UNKNOWN' end,
            case when completed_at is null then 'REQUEST_OPEN' end,
            case when arrived_at < dispatched_at then 'ARRIVAL_BEFORE_DISPATCH' end,
            case when requested_at is null or dispatched_at is null then 'TIMESTAMP_UNPARSEABLE' end,
            case when location_match_method in ('normalized', 'fuzzy') then 'LOC_NAME_VARIANT' end,
            case when psgc_code is null then 'LOC_UNMATCHED' end,
            case when event_key is null then 'EVENT_UNRESOLVED' end
        ], null) as dq_issues
    from resolved
)

select
    *,
    {{ dq_status('dq_issues',
                 ['REQUEST_TYPE_UNKNOWN', 'ARRIVAL_BEFORE_DISPATCH', 'TIMESTAMP_UNPARSEABLE',
                  'LOC_UNMATCHED', 'EVENT_UNRESOLVED'],
                 []) }} as dq_status
from checked
