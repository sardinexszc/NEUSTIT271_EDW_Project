-- Hazard events (PAGASA). One row per event.

select
    row_number() over (order by start_date, event_key)::int as event_key,
    event_key                                    as event_code,
    local_name,
    international_name,
    local_name || ' (' || international_name || ')' as event_name,
    case when category ilike '%monsoon%' then 'Flood' else 'Tropical Cyclone' end as hazard_type,
    category,
    case category
        when 'Tropical Depression' then 1
        when 'Tropical Storm' then 2
        when 'Severe Tropical Storm' then 3
        when 'Typhoon' then 4
        when 'Super Typhoon' then 5
    end                                          as category_rank,
    max_wind_kph,
    max_signal,
    start_date,
    end_date,
    end_date - start_date + 1                    as duration_days,
    extract(year from start_date)::int           as event_year,
    affected_areas
from {{ ref('stg_pagasa_event') }}
where dq_status = 'valid'
