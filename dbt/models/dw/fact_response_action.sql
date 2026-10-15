-- Grain: one row per response request (accumulating snapshot).
-- Four role-playing dates track the request's milestones; a milestone that has not happened
-- yet points to the dim_date -1 member and is filled in when a later load brings it.

select
    {{ date_key('s.requested_at::date') }}  as requested_date_key,
    {{ date_key('s.dispatched_at::date') }} as dispatched_date_key,
    {{ date_key('s.arrived_at::date') }}    as arrived_date_key,
    {{ date_key('s.completed_at::date') }}  as completed_date_key,
    loc.location_key,
    ev.event_key,
    rt.response_type_key,
    org.organization_key,
    s._batch_id::int                        as source_key,
    s.request_id,                                         -- degenerate dimension
    s.priority,                                           -- degenerate dimension
    s.requested_at,
    s.completed_at,
    s.hours_to_dispatch,
    s.hours_to_arrive,
    s.hours_on_site,
    s.hours_to_complete,
    s.personnel_count,
    s.completed_at is not null              as is_completed
from {{ ref('stg_lgu_response') }} s
{{ location_as_of('s.psgc_code', 's.requested_at::date') }}
join {{ ref('dim_event') }} ev on ev.event_code = s.event_key
join {{ ref('dim_response_type') }} rt on rt.response_type_code = s.request_type
join {{ source('ref', 'organization_alias') }} oa on oa.alias_name = lower(s.responding_unit)
join {{ ref('dim_organization') }} org on org.org_code = oa.org_code
where s.dq_status in ('valid', 'warning')
