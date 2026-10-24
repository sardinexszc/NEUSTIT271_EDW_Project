-- Grain: one row per event x city/municipality x lifeline (accumulating snapshot).
-- A disruption opens when the lifeline goes down and closes when service is restored;
-- restored_date_key = -1 while it is still down at the latest sitrep.

select
    {{ date_key('s.interrupted_at::date') }} as interrupted_date_key,
    {{ date_key('s.restored_at::date') }}    as restored_date_key,
    loc.location_key,
    ev.event_key,
    ll.lifeline_key,
    org.organization_key,                                 -- OCD / NDRRMC reports lifelines
    s._batch_id::int                         as source_key,
    s.interrupted_at,
    s.restored_at,
    s.units_affected,
    round((extract(epoch from s.restored_at - s.interrupted_at) / 3600)::numeric, 2) as hours_to_restore,
    s.restored_at is not null                as is_restored
from {{ ref('stg_ndrrmc_lifeline') }} s
{{ location_as_of('s.psgc_code', 's.interrupted_at::date') }}
join {{ ref('dim_event') }} ev on ev.event_code = s.event_key
join {{ ref('dim_lifeline') }} ll on ll.lifeline_code = s.lifeline
join {{ ref('dim_organization') }} org on org.org_code = 'OCD'
where s.dq_status in ('valid', 'warning')
