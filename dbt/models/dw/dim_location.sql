-- City/municipality dimension, SCD Type 2.
-- Natural key: PSGC code. Base attributes come from ref.psgc; dated attribute changes come
-- from the change log (seed psgc_changes), e.g. the 2022 split of Maguindanao into
-- Maguindanao del Norte / del Sur. Each change closes the open version and starts a new one,
-- so every fact keeps the province that was in force on its own date.

with places as (
    select
        p.psgc_code,
        p.name             as city_muni_name,
        p.geographic_level,
        p.province_name,
        p.region_code,
        r.name             as region_name
    from {{ source('ref', 'psgc') }} p
    left join {{ source('ref', 'psgc') }} r on r.psgc_code = p.region_code
    where p.geographic_level in ('City', 'Mun')
),

changes as (
    select
        lpad(psgc_code::text, 10, '0') as psgc_code,
        attribute,
        new_value,
        effective_date::date           as effective_date
    from {{ ref('psgc_changes') }}
),

-- every date on which an attribute of a place changes starts a new version
version_starts as (
    select psgc_code, date '1900-01-01' as valid_from from places
    union
    select psgc_code, effective_date from changes
),

versions as (
    select
        psgc_code,
        valid_from,
        coalesce(lead(valid_from) over (partition by psgc_code order by valid_from) - 1,
                 date '9999-12-31') as valid_to
    from version_starts
)

select
    row_number() over (order by v.psgc_code, v.valid_from)::int as location_key,
    v.psgc_code,
    p.city_muni_name,
    case p.geographic_level when 'City' then 'City' else 'Municipality' end as lgu_type,
    coalesce(
        (select c.new_value
         from changes c
         where c.psgc_code = v.psgc_code and c.attribute = 'province_name' and c.effective_date <= v.valid_from
         order by c.effective_date desc
         limit 1),
        p.province_name
    )                                   as province_name,
    p.region_code,
    p.region_name,
    v.valid_from,
    v.valid_to,
    v.valid_to = date '9999-12-31'      as is_current
from versions v
join places p using (psgc_code)
