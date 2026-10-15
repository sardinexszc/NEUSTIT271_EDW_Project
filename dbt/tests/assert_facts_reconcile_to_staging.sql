-- Every row that passed data quality must land in its fact table (no silent drops from
-- inner joins to dimensions). Damage keeps one row per event x place x category.
with expected as (
    select 'fact_damage_assessment' as fact, count(distinct (event_key, psgc_code, damage_category)) as n
    from {{ ref('stg_ndrrmc_damage') }} where dq_status in ('valid', 'warning')
    union all
    select 'fact_evacuation_snapshot', count(*)
    from {{ ref('stg_dromic_evacuation') }} where dq_status in ('valid', 'warning')
    union all
    select 'fact_resource_distribution', count(*)
    from {{ ref('stg_ngo_distribution_line') }} where dq_status in ('valid', 'warning')
    union all
    select 'fact_response_action', count(*)
    from {{ ref('stg_lgu_response') }} where dq_status in ('valid', 'warning')
),
actual as (
    select 'fact_damage_assessment' as fact, count(*) as n from {{ ref('fact_damage_assessment') }}
    union all select 'fact_evacuation_snapshot', count(*) from {{ ref('fact_evacuation_snapshot') }}
    union all select 'fact_resource_distribution', count(*) from {{ ref('fact_resource_distribution') }}
    union all select 'fact_response_action', count(*) from {{ ref('fact_response_action') }}
)
select e.fact, e.n as expected_rows, a.n as actual_rows
from expected e
join actual a using (fact)
where e.n <> a.n
