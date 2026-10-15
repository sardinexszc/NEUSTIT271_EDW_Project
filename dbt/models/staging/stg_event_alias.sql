-- Every way a source may refer to an event: local name, international name,
-- "TY <LOCAL>", or the event key itself. Lower-cased for matching.

with events as (
    select event_key, local_name, international_name, start_date, end_date
    from {{ ref('stg_pagasa_event') }}
    where dq_status = 'valid'
)

select distinct event_key, alias, start_date, end_date
from events
cross join lateral (values
    (lower(local_name)),
    (lower(international_name)),
    ('ty ' || lower(local_name)),
    (lower(event_key))
) as a(alias)
