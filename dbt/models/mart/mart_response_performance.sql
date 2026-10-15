-- Operations mart: response timeliness. GROUPING SETS gives detail and roll-ups in one pass:
-- event x type x priority, event x type, event, type x priority, type, and the overall total.
-- 'All' marks a rolled-up dimension.

select
    case when grouping(e.event_code) = 1 then 'All' else e.event_code end              as event_code,
    case when grouping(rt.response_type_name) = 1 then 'All' else rt.response_type_name end as response_type,
    case when grouping(f.priority) = 1 then 'All' else f.priority end                   as priority,
    count(*)                                                                    as requests,
    round(percentile_cont(0.5) within group (order by f.hours_to_dispatch)::numeric, 2)  as median_hours_to_dispatch,
    round(percentile_cont(0.9) within group (order by f.hours_to_dispatch)::numeric, 2)  as p90_hours_to_dispatch,
    round(percentile_cont(0.5) within group (order by f.hours_to_arrive)::numeric, 2)    as median_hours_to_arrive,
    round(percentile_cont(0.5) within group (order by f.hours_to_complete)::numeric, 2)  as median_hours_to_complete,
    round(avg(f.is_completed::int)::numeric, 4)                                 as completion_rate,
    sum(f.personnel_count)                                                      as personnel_deployed
from {{ ref('fact_response_action') }} f
join {{ ref('dim_event') }} e using (event_key)
join {{ ref('dim_response_type') }} rt using (response_type_key)
group by grouping sets (
    (e.event_code, rt.response_type_name, f.priority),
    (e.event_code, rt.response_type_name),
    (e.event_code),
    (rt.response_type_name, f.priority),
    (rt.response_type_name),
    ()
)
