-- PAGASA bulletins, typed. One row per raw bulletin; re-issued bulletins are flagged
-- as duplicates (only the first copy is a valid event).

with typed as (
    select
        _batch_id,
        _source_file,
        _row_number,
        initcap(trim(local_name))          as local_name,
        initcap(trim(international_name))  as international_name,
        trim(category)                     as category,
        {{ clean_number('max_wind_kph') }}::int as max_wind_kph,
        {{ clean_number('max_signal') }}::int   as max_signal,
        case when start_date ~ '^[A-Za-z]{3} \d{1,2}, \d{4}$' then to_date(start_date, 'Mon DD, YYYY') end as start_date,
        case when end_date ~ '^[A-Za-z]{3} \d{1,2}, \d{4}$' then to_date(end_date, 'Mon DD, YYYY') end as end_date,
        trim(affected_areas)               as affected_areas
    from {{ source('raw', 'pagasa_event') }}
),

ranked as (
    select
        *,
        'TC' || extract(year from start_date)::int || '-' || upper(local_name) as event_key,
        row_number() over (
            partition by upper(local_name), upper(international_name), start_date
            order by _batch_id, _row_number
        ) as copy_number
    from typed
),

checked as (
    select
        *,
        array_remove(array[
            case when copy_number > 1 then 'PAGASA_DUPLICATE_BULLETIN' end,
            case when start_date is null or end_date is null then 'EVENT_DATE_UNPARSEABLE' end
        ], null) as dq_issues
    from ranked
)

select
    *,
    case
        when 'EVENT_DATE_UNPARSEABLE' = any(dq_issues) then 'rejected'
        when copy_number > 1 then 'duplicate'
        else 'valid'
    end as dq_status
from checked
