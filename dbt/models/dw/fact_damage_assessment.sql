-- Grain: one row per event x city/municipality x damage category.
-- Transaction fact. NDRRMC sitreps are cumulative, so only the latest valid sitrep counts;
-- summing every sitrep would double-count.

with latest_sitrep as (
    select distinct on (event_key, psgc_code, damage_category) *
    from {{ ref('stg_ndrrmc_damage') }}
    where dq_status in ('valid', 'warning')
    order by event_key, psgc_code, damage_category, sitrep_no desc, report_date desc
)

select
    {{ date_key('s.report_date') }}   as report_date_key,
    loc.location_key,
    ev.event_key,
    dc.damage_category_key,
    s._batch_id::int                  as source_key,
    s.sitrep_no,                                          -- degenerate dimension
    s.dead,
    s.injured,
    s.missing,
    s.affected_families,
    s.affected_persons,
    s.houses_partial                  as houses_partially_damaged,
    s.houses_total                    as houses_totally_damaged,
    s.cost_php
from latest_sitrep s
{{ location_as_of('s.psgc_code', 's.report_date') }}
join {{ ref('dim_event') }} ev on ev.event_code = s.event_key
join {{ ref('dim_damage_category') }} dc on dc.damage_category = s.damage_category
