-- Grain: one row per distribution line item (one relief item in one distribution).
-- Quantities are in the item's standard unit, so different partners' units can be summed.
-- beneficiary_families belongs to the whole distribution; it is stored on line 1 only
-- so it stays additive.

with valid_lines as (
    select
        s.*,
        min(s.line_no) over (partition by s._batch_id, s._row_number) as first_valid_line
    from {{ ref('stg_ngo_distribution_line') }} s
    where s.dq_status in ('valid', 'warning')
)

select
    {{ date_key('s.distributed_on') }} as distribution_date_key,
    loc.location_key,
    ev.event_key,
    org.organization_key,
    res.resource_key,
    s._batch_id::int                   as source_key,
    s.distribution_id,                                    -- degenerate dimension
    s.line_no,
    s.quantity_standard                as quantity,
    s.value_php,
    case when s.line_no = s.first_valid_line then s.beneficiary_families end as beneficiary_families
from valid_lines s
{{ location_as_of('s.psgc_code', 's.distributed_on') }}
join {{ ref('dim_event') }} ev on ev.event_code = s.event_key
join {{ ref('dim_organization') }} org on org.org_code = s.org_code
join {{ ref('dim_resource') }} res on res.item_code = s.item_code
