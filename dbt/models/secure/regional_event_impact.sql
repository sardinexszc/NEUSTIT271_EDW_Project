{{ config(post_hook="{{ security_invoker() }}") }}

-- Event x province impact and relief for the querying user's region(s).
-- No region filter is written here: the fact tables' row-level security does it, because
-- the view runs with the caller's privileges (security_invoker). The same view therefore
-- shows Bicol to a Bicol officer, Cagayan Valley to a Cagayan officer, and everything to
-- an analyst.

with damage as (
    select f.event_key, l.region_name, l.province_name,
           sum(f.dead) as dead,
           sum(f.affected_persons) as affected_persons,
           sum(f.houses_totally_damaged) as houses_totally_damaged,
           sum(f.cost_php) as damage_cost_php
    from {{ ref('fact_damage_assessment') }} f
    join {{ ref('dim_location') }} l using (location_key)
    group by 1, 2, 3
),

relief as (
    select f.event_key, l.province_name,
           sum(f.value_php) as relief_value_php,
           sum(f.beneficiary_families) as family_servings
    from {{ ref('fact_resource_distribution') }} f
    join {{ ref('dim_location') }} l using (location_key)
    group by 1, 2
)

select
    e.event_code,
    e.event_name,
    d.region_name,
    d.province_name,
    d.dead,
    d.affected_persons,
    d.houses_totally_damaged,
    d.damage_cost_php,
    coalesce(r.relief_value_php, 0) as relief_value_php,
    coalesce(r.family_servings, 0)  as family_servings
from damage d
join {{ ref('dim_event') }} e using (event_key)
left join relief r using (event_key, province_name)
