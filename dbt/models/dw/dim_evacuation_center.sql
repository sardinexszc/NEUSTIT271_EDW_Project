-- Evacuation centers as reported by DROMIC (SCD Type 1: latest known attributes).
-- The center's city/municipality is kept as a PSGC code (outrigger to dim_location).

with reports as (
    select ec_code, ec_name, ec_type, barangay, psgc_code, capacity_families, report_date
    from {{ ref('stg_dromic_evacuation') }}
    where dq_status in ('valid', 'warning')
),

latest as (
    select distinct on (ec_code) *
    from reports
    order by ec_code, report_date desc
)

select
    row_number() over (order by ec_code)::int as evacuation_center_key,
    ec_code,
    ec_name,
    ec_type,
    barangay,
    psgc_code,
    capacity_families
from latest
