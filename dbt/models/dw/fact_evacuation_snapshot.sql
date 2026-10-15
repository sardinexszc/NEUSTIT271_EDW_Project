-- Grain: one row per evacuation center x day x event (periodic snapshot).
-- A center can shelter evacuees of two overlapping events on the same day (Nov 2024).
-- families_inside / persons_inside are SEMI-ADDITIVE: sum across centers or places,
-- never across days (use the daily total's max or average over a period).

select
    {{ date_key('s.report_date') }}   as snapshot_date_key,
    loc.location_key,
    ev.event_key,
    ec.evacuation_center_key,
    org.organization_key,                                 -- DSWD reports DROMIC
    s._batch_id::int                  as source_key,
    s.families_inside,
    s.persons_inside,
    s.capacity_families,
    s.families_inside > s.capacity_families as is_over_capacity
from {{ ref('stg_dromic_evacuation') }} s
{{ location_as_of('s.psgc_code', 's.report_date') }}
join {{ ref('dim_event') }} ev on ev.event_code = s.event_key
join {{ ref('dim_evacuation_center') }} ec on ec.ec_code = s.ec_code
join {{ ref('dim_organization') }} org on org.org_code = 'DSWD'
where s.dq_status in ('valid', 'warning')
