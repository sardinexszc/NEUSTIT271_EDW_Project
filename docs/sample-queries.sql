-- DRIW sample analytical queries
-- =============================
-- Each query answers one key business question (BQ, see docs/business-case.md) and shows an
-- OLAP operation. Run any of them in psql or pgAdmin against the `driw` database.
-- `ingestion/benchmark_queries.py` runs every query below and times it (docs/query-performance.md).
--
-- Format used by the benchmark: a line `-- @query <id> | <title> | <OLAP operation>` starts a query.


-- @query Q01 | Costliest events and their human toll (BQ1) | Ranking (top-N)
select e.event_name,
       e.category,
       sum(f.cost_php)          as damage_cost_php,
       sum(f.dead)              as dead,
       sum(f.affected_persons)  as affected_persons
from dw.fact_damage_assessment f
join dw.dim_event e using (event_key)
group by e.event_name, e.category
order by damage_cost_php desc
limit 10;


-- @query Q02 | Damage by year and category, with yearly subtotals (BQ2) | Roll-up (GROUP BY ROLLUP)
select coalesce(e.event_year::text, 'All years')            as event_year,
       coalesce(dc.damage_category, 'All categories')       as damage_category,
       sum(f.cost_php)                                      as damage_cost_php
from dw.fact_damage_assessment f
join dw.dim_event e using (event_key)
join dw.dim_damage_category dc using (damage_category_key)
group by rollup (e.event_year, dc.damage_category)
order by e.event_year nulls last, dc.damage_category nulls last;


-- @query Q03 | Drill-down: region -> province -> city/municipality for one event (BQ3) | Drill-down
select l.region_name,
       l.province_name,
       l.city_muni_name,
       sum(f.affected_persons) as affected_persons,
       sum(f.cost_php)         as damage_cost_php
from dw.fact_damage_assessment f
join dw.dim_location l using (location_key)
join dw.dim_event e using (event_key)
where e.event_code = 'TC2024-KRISTINE'
group by l.region_name, l.province_name, l.city_muni_name
order by affected_persons desc
limit 15;


-- @query Q04 | Tropical cyclone vs monsoon flood impact per region (BQ4) | Pivot (FILTER) / dice
select l.region_name,
       sum(f.affected_persons) filter (where e.hazard_type = 'Tropical Cyclone')
           as cyclone_affected,
       sum(f.affected_persons) filter (where e.hazard_type = 'Flood')
           as flood_affected,
       sum(f.affected_persons) as total_affected
from dw.fact_damage_assessment f
join dw.dim_event e using (event_key)
join dw.dim_location l using (location_key)
group by l.region_name
order by total_affected desc;


-- @query Q05 | Every subtotal of impact by year x region x hazard (BQ2, BQ4) | Cube (GROUP BY CUBE)
select e.event_year, l.region_name, e.hazard_type,
       grouping(e.event_year, l.region_name, e.hazard_type) as grouping_id,
       sum(f.dead)            as dead,
       sum(f.affected_persons) as affected_persons,
       sum(f.cost_php)        as damage_cost_php
from dw.fact_damage_assessment f
join dw.dim_event e using (event_key)
join dw.dim_location l using (location_key)
group by cube (e.event_year, l.region_name, e.hazard_type);


-- @query Q06 | Peak evacuees per event (semi-additive measure) (BQ5) | Aggregate over a snapshot
select e.event_name,
       max(daily.persons) as peak_persons_in_centers,
       count(*)           as days_with_evacuees
from (
    -- sum across centers per day
    select event_key, snapshot_date_key, sum(persons_inside) as persons
    from dw.fact_evacuation_snapshot
    group by event_key, snapshot_date_key
) daily
join dw.dim_event e using (event_key)
group by e.event_name   -- then MAX over days, never SUM
order by peak_persons_in_centers desc
limit 10;


-- @query Q07 | Evacuation centers most often over capacity (BQ6) | Slice (is_over_capacity)
select c.ec_name, c.ec_type, l.province_name,
       count(*) filter (where f.is_over_capacity) as over_capacity_days,
       max(f.families_inside)                     as max_families,
       c.capacity_families
from dw.fact_evacuation_snapshot f
join dw.dim_evacuation_center c using (evacuation_center_key)
join dw.dim_location l using (location_key)
group by c.ec_name, c.ec_type, l.province_name, c.capacity_families
having count(*) filter (where f.is_over_capacity) > 0
order by over_capacity_days desc, max_families desc
limit 10;


-- @query Q08 | Dispatch time by response type and priority (BQ7) | Accumulating snapshot analysis
select rt.response_type_name,
       f.priority,
       count(*) as requests,
       round(percentile_cont(0.5) within group (order by f.hours_to_dispatch)::numeric, 2)
           as median_hours_to_dispatch,
       round(percentile_cont(0.9) within group (order by f.hours_to_dispatch)::numeric, 2)
           as p90_hours_to_dispatch,
       round(100.0 * avg(f.is_completed::int), 1) as pct_completed
from dw.fact_response_action f
join dw.dim_response_type rt using (response_type_key)
group by rt.response_type_name, f.priority
order by rt.response_type_name, f.priority;


-- @query Q09 | Slowest-responding cities/municipalities for life-saving requests (BQ7) | Slice + ranking
select l.province_name, l.city_muni_name,
       count(*) as life_saving_requests,
       round(percentile_cont(0.5) within group (order by f.hours_to_dispatch)::numeric, 2)
           as median_hours_to_dispatch
from dw.fact_response_action f
join dw.dim_response_type rt using (response_type_key)
join dw.dim_location l using (location_key)
where rt.response_cluster = 'Life-saving'
group by l.province_name, l.city_muni_name
having count(*) >= 20
order by median_hours_to_dispatch desc
limit 10;


-- @query Q10 | Least relief per affected person, by province (BQ8) | Integration of two facts
with impact as (
    select l.province_name, sum(f.affected_persons) as affected
    from dw.fact_damage_assessment f join dw.dim_location l using (location_key)
    group by l.province_name
), relief as (
    select l.province_name, sum(f.value_php) as relief_php
    from dw.fact_resource_distribution f join dw.dim_location l using (location_key)
    group by l.province_name
)
select i.province_name, i.affected, coalesce(r.relief_php, 0) as relief_php,
       round(coalesce(r.relief_php, 0) / nullif(i.affected, 0), 2) as relief_php_per_person
from impact i left join relief r using (province_name)
order by relief_php_per_person
limit 10;


-- @query Q11 | Relief mix by organization and resource category (BQ9) | Dice (org x category)
select o.org_name, r.category,
       sum(f.quantity)  as quantity_standard_units,
       sum(f.value_php) as relief_value_php
from dw.fact_resource_distribution f
join dw.dim_organization o using (organization_key)
join dw.dim_resource r using (resource_key)
group by o.org_name, r.category
order by o.org_name, relief_value_php desc;


-- @query Q12 | Year-over-year change in damage cost (BQ2) | Window function (LAG)
select event_year,
       damage_cost_php,
       round(100.0 * (damage_cost_php - lag(damage_cost_php) over (order by event_year))
             / nullif(lag(damage_cost_php) over (order by event_year), 0), 1)
           as pct_change_vs_prior_year
from (
    select e.event_year, sum(f.cost_php) as damage_cost_php
    from dw.fact_damage_assessment f join dw.dim_event e using (event_key)
    group by e.event_year
) yearly
order by event_year;


-- @query Q13 | Dashboard query served from a mart (BQ1, BQ5, BQ8) | Pre-aggregated ROLAP mart
select event_name, damage_cost_php, peak_persons_in_centers, relief_php_per_affected_person
from mart.mart_event_summary
order by damage_cost_php desc
limit 10;


-- @query Q14 | What data was rejected, and why? (BQ10) | Data-quality audit
select source_system, reject_reasons, count(*) as rows_quarantined
from dq.dq_quarantine
group by source_system, reject_reasons
order by rows_quarantined desc;
