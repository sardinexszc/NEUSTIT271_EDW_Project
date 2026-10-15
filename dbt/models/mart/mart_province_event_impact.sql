-- Event x province: impact next to relief delivered, for spotting under-served provinces.
-- Province is the one in force at the time (SCD2), e.g. Maguindanao del Sur for Paeng.

with damage as (
    select
        f.event_key,
        l.province_name,
        l.region_name,
        sum(f.dead)                   as dead,
        sum(f.affected_persons)       as affected_persons,
        sum(f.affected_families)      as affected_families,
        sum(f.houses_totally_damaged) as houses_totally_damaged,
        sum(f.cost_php)               as damage_cost_php
    from {{ ref('fact_damage_assessment') }} f
    join {{ ref('dim_location') }} l using (location_key)
    group by 1, 2, 3
),

relief as (
    select
        f.event_key,
        l.province_name,
        sum(f.value_php)            as relief_value_php,
        sum(f.beneficiary_families) as families_served
    from {{ ref('fact_resource_distribution') }} f
    join {{ ref('dim_location') }} l using (location_key)
    group by 1, 2
)

select
    e.event_code,
    e.event_name,
    e.event_year,
    d.region_name,
    d.province_name,
    d.dead,
    d.affected_persons,
    d.affected_families,
    d.houses_totally_damaged,
    d.damage_cost_php,
    coalesce(r.relief_value_php, 0) as relief_value_php,
    coalesce(r.families_served, 0)  as families_served,
    round(coalesce(r.relief_value_php, 0) / nullif(d.affected_persons, 0), 2) as relief_php_per_affected_person,
    round(coalesce(r.families_served, 0)::numeric / nullif(d.affected_families, 0), 4) as family_coverage_ratio
from damage d
join {{ ref('dim_event') }} e using (event_key)
left join relief r using (event_key, province_name)
