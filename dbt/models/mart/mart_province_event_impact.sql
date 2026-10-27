-- Event x province: impact next to relief delivered, for spotting under-served provinces.
-- Province is the one in force at the time (SCD2), e.g. Maguindanao del Sur for Paeng.
-- Rates per 100,000 use the whole province's population as it stood at the event.

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

province_population as (
    select e.event_key, l.province_name, sum(l.population) as province_population
    from {{ ref('dim_event') }} e
    join {{ ref('dim_location') }} l on e.start_date between l.valid_from and l.valid_to
    group by 1, 2
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
    pp.province_population,
    round(d.dead * 100000.0 / nullif(pp.province_population, 0), 2)             as dead_per_100k,
    round(d.affected_persons * 100000.0 / nullif(pp.province_population, 0), 0) as affected_per_100k,
    coalesce(r.relief_value_php, 0) as relief_value_php,
    coalesce(r.families_served, 0)  as families_served,
    round(coalesce(r.relief_value_php, 0) / nullif(d.affected_persons, 0), 2) as relief_php_per_affected_person,
    round(coalesce(r.families_served, 0)::numeric / nullif(d.affected_families, 0), 4) as family_coverage_ratio
from damage d
join {{ ref('dim_event') }} e using (event_key)
left join province_population pp using (event_key, province_name)
left join relief r using (event_key, province_name)
