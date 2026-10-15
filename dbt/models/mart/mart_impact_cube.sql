-- ROLAP cube of disaster impact: year x region x hazard type with every subtotal
-- (GROUP BY CUBE). grouping_level says which dimensions a row is aggregated over,
-- e.g. 'year' = per year across all regions and hazards, 'grand_total' = everything.

select
    case
        when grouping(e.event_year, l.region_name, e.hazard_type) = 7 then 'grand_total'
        else concat_ws('+',
            case when grouping(e.event_year) = 0 then 'year' end,
            case when grouping(l.region_name) = 0 then 'region' end,
            case when grouping(e.hazard_type) = 0 then 'hazard' end)
    end                                  as grouping_level,
    e.event_year,
    l.region_name,
    e.hazard_type,
    count(distinct e.event_key)          as events,
    sum(f.dead)                          as dead,
    sum(f.affected_persons)              as affected_persons,
    sum(f.houses_totally_damaged)        as houses_totally_damaged,
    sum(f.cost_php)                      as damage_cost_php
from {{ ref('fact_damage_assessment') }} f
join {{ ref('dim_event') }} e using (event_key)
join {{ ref('dim_location') }} l using (location_key)
group by cube (e.event_year, l.region_name, e.hazard_type)
