-- Logistics mart: relief delivered per event x organization x resource category.

select
    e.event_code,
    o.org_code,
    o.org_name,
    o.org_type,
    r.category                         as resource_category,
    count(distinct f.distribution_id)  as distributions,
    count(*)                           as line_items,
    sum(f.value_php)                   as relief_value_php,
    sum(f.beneficiary_families)        as families_served
from {{ ref('fact_resource_distribution') }} f
join {{ ref('dim_event') }} e using (event_key)
join {{ ref('dim_organization') }} o using (organization_key)
join {{ ref('dim_resource') }} r using (resource_key)
group by e.event_code, o.org_code, o.org_name, o.org_type, r.category
