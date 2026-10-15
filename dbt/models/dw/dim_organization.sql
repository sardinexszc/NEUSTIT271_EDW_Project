select
    row_number() over (order by org_code)::int as organization_key,
    org_code,
    org_name,
    org_type,
    parent_agency
from {{ source('ref', 'organization') }}
