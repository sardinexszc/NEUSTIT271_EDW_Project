select
    row_number() over (order by category, item_code)::int as resource_key,
    item_code,
    item_name,
    category,
    standard_unit,
    unit_cost_php
from {{ source('ref', 'resource_item') }}
