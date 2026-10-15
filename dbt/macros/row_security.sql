{#- Row-level security on a fact table (post-hook).
    Analysts see every row; regional users see only rows whose location falls in a region
    granted to them in governance.region_access. Anyone else with SELECT sees nothing
    (RLS denies by default). The table owner (the ETL role) is not restricted. -#}
{% macro region_row_security() -%}
alter table {{ this }} enable row level security;
create policy analyst_all_rows on {{ this }}
    for select to driw_analyst
    using (true);
create policy regional_own_region on {{ this }}
    for select to driw_regional
    using (location_key in (
        select l.location_key
        from {{ ref('dim_location') }} l
        where l.region_code in (select region_code from governance.my_regions)
    ));
{%- endmacro %}

{#- Views in `secure` run with the querying user's privileges, so the fact tables'
    row-level security still applies through them. -#}
{% macro security_invoker() -%}
alter view {{ this }} set (security_invoker = true)
{%- endmacro %}
