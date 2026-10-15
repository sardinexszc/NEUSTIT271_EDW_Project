-- Rows that reach the warehouse must have a sensible timeline.
select request_id, hours_to_dispatch, hours_to_arrive, hours_on_site
from {{ ref('stg_lgu_response') }}
where dq_status in ('valid', 'warning')
  and (hours_to_dispatch < 0 or hours_to_arrive < 0 or hours_on_site < 0)
