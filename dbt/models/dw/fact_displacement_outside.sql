-- Grain: one row per city/municipality x day x event (periodic snapshot).
-- Families displaced OUTSIDE evacuation centers (with relatives or friends), from DROMIC.
-- Together with fact_evacuation_snapshot this gives total displacement.
-- families_outside / persons_outside are SEMI-ADDITIVE: sum across places, never across days.

select
    {{ date_key('s.report_date') }}   as snapshot_date_key,
    loc.location_key,
    ev.event_key,
    org.organization_key,                                 -- DSWD reports DROMIC
    s._batch_id::int                  as source_key,
    s.families_outside,
    s.persons_outside
from {{ ref('stg_dromic_displaced_outside') }} s
{{ location_as_of('s.psgc_code', 's.report_date') }}
join {{ ref('dim_event') }} ev on ev.event_code = s.event_key
join {{ ref('dim_organization') }} org on org.org_code = 'DSWD'
where s.dq_status in ('valid', 'warning')
