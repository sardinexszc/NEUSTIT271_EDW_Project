{{ config(post_hook="{{ security_invoker() }}") }}

-- Response timeliness per event and response type for the querying user's region(s);
-- filtered by the fact table's row-level security (see regional_event_impact).

select
    e.event_code,
    e.event_name,
    l.region_name,
    rt.response_type_name                                                       as response_type,
    count(*)                                                                    as requests,
    round(percentile_cont(0.5) within group (order by f.hours_to_dispatch)::numeric, 2) as median_hours_to_dispatch,
    round(avg(f.is_completed::int)::numeric, 4)                                 as completion_rate
from {{ ref('fact_response_action') }} f
join {{ ref('dim_event') }} e using (event_key)
join {{ ref('dim_location') }} l using (location_key)
join {{ ref('dim_response_type') }} rt using (response_type_key)
group by e.event_code, e.event_name, l.region_name, rt.response_type_name
