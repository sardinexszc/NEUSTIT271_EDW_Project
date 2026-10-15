-- Aggregates must add back up to the facts they summarize.
with fact as (
    select sum(cost_php) as cost, sum(dead) as dead from {{ ref('fact_damage_assessment') }}
),
checks as (
    select 'cube grand total cost' as check_name,
           (select damage_cost_php from {{ ref('mart_impact_cube') }} where grouping_level = 'grand_total') as mart_value,
           (select cost from fact) as fact_value
    union all
    select 'cube sum of yearly subtotals (dead)',
           (select sum(dead) from {{ ref('mart_impact_cube') }} where grouping_level = 'year'),
           (select dead from fact)
    union all
    select 'event summary cost',
           (select sum(damage_cost_php) from {{ ref('mart_event_summary') }}),
           (select cost from fact)
    union all
    select 'province impact cost',
           (select sum(damage_cost_php) from {{ ref('mart_province_event_impact') }}),
           (select cost from fact)
    union all
    select 'relief value by org/category',
           (select sum(relief_value_php) from {{ ref('mart_relief_by_org_category') }}),
           (select sum(value_php) from {{ ref('fact_resource_distribution') }})
    union all
    select 'response overall requests',
           (select requests from {{ ref('mart_response_performance') }}
            where event_code = 'All' and response_type = 'All' and priority = 'All'),
           (select count(*) from {{ ref('fact_response_action') }})
)
select * from checks where mart_value is distinct from fact_value
