-- Operations mart: critical infrastructure and basic services per event x lifeline.
-- How many places lost each lifeline, how many are back, and how fast service was restored.

select
    e.event_code,
    ll.lifeline_code,
    ll.lifeline_name,
    ll.lifeline_sector,
    ll.unit_of_measure,
    count(*)                                                    as places_disrupted,
    sum(f.units_affected)                                       as units_affected,
    count(*) filter (where f.is_restored)                       as places_restored,
    count(*) filter (where not f.is_restored)                   as places_still_down,
    count(*) filter (where f.hours_to_restore <= 72)            as restored_within_72h,
    round(count(*) filter (where f.hours_to_restore <= 72)::numeric / count(*), 4) as share_restored_within_72h,
    round(percentile_cont(0.5) within group (order by f.hours_to_restore)::numeric, 1) as median_hours_to_restore,
    round(percentile_cont(0.9) within group (order by f.hours_to_restore)::numeric, 1) as p90_hours_to_restore
from {{ ref('fact_lifeline_disruption') }} f
join {{ ref('dim_event') }} e using (event_key)
join {{ ref('dim_lifeline') }} ll using (lifeline_key)
group by e.event_code, ll.lifeline_key, ll.lifeline_code, ll.lifeline_name, ll.lifeline_sector, ll.unit_of_measure
