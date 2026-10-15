-- Executive mart: one row per event with headline figures from all four facts.

with damage as (
    select
        f.event_key,
        sum(f.dead)                     as dead,
        sum(f.injured)                  as injured,
        sum(f.missing)                  as missing,
        sum(f.affected_families)        as affected_families,
        sum(f.affected_persons)         as affected_persons,
        sum(f.houses_partially_damaged) as houses_partially_damaged,
        sum(f.houses_totally_damaged)   as houses_totally_damaged,
        sum(f.cost_php)                                                          as damage_cost_php,
        sum(f.cost_php) filter (where dc.damage_category = 'Housing')        as housing_cost_php,
        sum(f.cost_php) filter (where dc.damage_category = 'Infrastructure') as infrastructure_cost_php,
        sum(f.cost_php) filter (where dc.damage_category = 'Agriculture')    as agriculture_cost_php,
        count(distinct l.psgc_code)     as cities_municipalities_affected,
        count(distinct l.province_name) as provinces_affected
    from {{ ref('fact_damage_assessment') }} f
    join {{ ref('dim_damage_category') }} dc using (damage_category_key)
    join {{ ref('dim_location') }} l using (location_key)
    group by 1
),

-- semi-additive: total across centers per day, then the peak day
evac_daily as (
    select event_key, snapshot_date_key, sum(persons_inside) as persons, sum(families_inside) as families
    from {{ ref('fact_evacuation_snapshot') }}
    group by 1, 2
),

evacuation as (
    select
        d.event_key,
        max(d.persons)  as peak_persons_in_centers,
        max(d.families) as peak_families_in_centers,
        count(*)        as days_with_evacuees,
        (select count(distinct evacuation_center_key) from {{ ref('fact_evacuation_snapshot') }} s
         where s.event_key = d.event_key) as centers_used,
        (select count(*) from {{ ref('fact_evacuation_snapshot') }} s
         where s.event_key = d.event_key and s.is_over_capacity) as over_capacity_center_days
    from evac_daily d
    group by 1
),

relief as (
    select
        event_key,
        sum(value_php)                  as relief_value_php,
        sum(beneficiary_families)       as families_served,
        count(distinct distribution_id) as distributions
    from {{ ref('fact_resource_distribution') }}
    group by 1
),

response as (
    select
        event_key,
        count(*)                                                        as response_requests,
        percentile_cont(0.5) within group (order by hours_to_dispatch)  as median_hours_to_dispatch,
        percentile_cont(0.5) within group (order by hours_to_dispatch + hours_to_arrive) as median_hours_to_arrive,
        avg(is_completed::int)                                          as completion_rate
    from {{ ref('fact_response_action') }}
    group by 1
)

select
    e.event_code,
    e.event_name,
    e.local_name,
    e.international_name,
    e.hazard_type,
    e.category,
    e.category_rank,
    e.max_signal,
    e.start_date,
    e.end_date,
    e.event_year,
    d.dead, d.injured, d.missing,
    d.affected_families, d.affected_persons,
    d.houses_partially_damaged, d.houses_totally_damaged,
    d.damage_cost_php, d.housing_cost_php, d.infrastructure_cost_php, d.agriculture_cost_php,
    d.cities_municipalities_affected, d.provinces_affected,
    ev.peak_persons_in_centers, ev.peak_families_in_centers, ev.days_with_evacuees,
    ev.centers_used, ev.over_capacity_center_days,
    r.relief_value_php, r.families_served, r.distributions,
    round(r.relief_value_php / nullif(d.affected_persons, 0), 2) as relief_php_per_affected_person,
    rs.response_requests,
    round(rs.median_hours_to_dispatch::numeric, 2) as median_hours_to_dispatch,
    round(rs.median_hours_to_arrive::numeric, 2)   as median_hours_to_arrive,
    round(rs.completion_rate::numeric, 4)          as completion_rate
from {{ ref('dim_event') }} e
left join damage d using (event_key)
left join evacuation ev using (event_key)
left join relief r using (event_key)
left join response rs using (event_key)
