-- NGO / agency relief distributions: nested JSON flattened to one row per item line.
-- Header problems (organization, event, location) reject every line of the record;
-- line problems (item code, unit) reject only that line.

with header as (
    select
        _batch_id,
        _source_file,
        _row_number,
        record ->> 'distribution_id'                         as distribution_id,
        trim(record ->> 'organization')                      as raw_organization,
        record ->> 'event_ref'                               as raw_event_ref,
        (record ->> 'distributed_on')::date                  as distributed_on,
        record -> 'location' ->> 'province'                  as province,
        record -> 'location' ->> 'municipality'              as raw_municipality,
        (record -> 'beneficiaries' ->> 'families')::int      as beneficiary_families,
        record -> 'items'                                    as items
    from {{ source('raw', 'ngo_distribution') }}
),

header_resolved as (
    select
        h.*,
        org.org_code,
        o.org_name,
        loc.psgc_code,
        loc.match_method as location_match_method,
        ev.event_key
    from header h
    left join {{ source('ref', 'organization_alias') }} org on org.alias_name = lower(h.raw_organization)
    left join {{ source('ref', 'organization') }} o on o.org_code = org.org_code
    left join {{ ref('stg_location_resolution') }} loc
        on loc.raw_province = h.province and loc.raw_name = h.raw_municipality
    {{ event_lookup('h.raw_event_ref', 'h.distributed_on', 'ev') }}
),

header_checked as (
    select
        *,
        array_remove(array[
            case when org_code is not null and raw_organization <> org_name then 'ORG_NAME_STANDARDIZED' end,
            case when org_code is null then 'ORG_UNKNOWN' end,
            case when event_key is null then 'EVENT_UNRESOLVED' end,
            case when raw_municipality is null then 'LOCATION_MISSING' end,
            case when location_match_method in ('normalized', 'fuzzy') then 'LOC_NAME_VARIANT' end,
            case when raw_municipality is not null and psgc_code is null then 'LOC_UNMATCHED' end
        ], null) as header_issues
    from header_resolved
),

lines as (
    select
        h.*,
        item.line_no::int                          as line_no,
        item.value ->> 'item_code'                 as source_item_code,
        item.value ->> 'unit'                      as source_unit,
        (item.value ->> 'quantity')::numeric       as source_quantity
    from header_checked h
    cross join lateral jsonb_array_elements(h.items) with ordinality as item(value, line_no)
),

line_resolved as (
    select
        l.*,
        a.item_code,
        a.to_standard_factor,
        ri.standard_unit,
        l.source_quantity * a.to_standard_factor                  as quantity_standard,
        l.source_quantity * a.to_standard_factor * ri.unit_cost_php as value_php,
        array_remove(array[
            case when a.item_code is null then 'ITEM_CODE_UNKNOWN' end,
            case when a.item_code is not null and a.source_unit <> l.source_unit then 'UNIT_MISMATCH' end,
            case when a.item_code is not null and a.source_unit = l.source_unit and a.to_standard_factor <> 1
                 then 'UNIT_CONVERTED' end
        ], null) as line_issues
    from lines l
    left join {{ source('ref', 'resource_item_alias') }} a on a.source_item_code = l.source_item_code
    left join {{ source('ref', 'resource_item') }} ri on ri.item_code = a.item_code
)

select
    _batch_id, _source_file, _row_number, line_no,
    distribution_id, distributed_on, event_key, raw_event_ref,
    org_code, raw_organization,
    psgc_code, province, raw_municipality, location_match_method,
    beneficiary_families,
    item_code, source_item_code, source_unit, source_quantity, to_standard_factor,
    standard_unit, quantity_standard, value_php,
    header_issues,
    line_issues,
    header_issues || line_issues as dq_issues,
    {{ dq_status('header_issues || line_issues',
                 ['ORG_UNKNOWN', 'EVENT_UNRESOLVED', 'LOCATION_MISSING', 'LOC_UNMATCHED',
                  'ITEM_CODE_UNKNOWN', 'UNIT_MISMATCH'],
                 []) }} as dq_status
from line_resolved
