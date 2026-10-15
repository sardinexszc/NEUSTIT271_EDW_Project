-- SCD Type 2 integrity per PSGC code: versions must not overlap, must leave no gaps,
-- and exactly one version must be current.
with ordered as (
    select
        psgc_code, valid_from, valid_to, is_current,
        lead(valid_from) over (partition by psgc_code order by valid_from) as next_from
    from {{ ref('dim_location') }}
)
select psgc_code, 'overlap or gap' as problem
from ordered
where next_from is not null and next_from <> valid_to + 1
union all
select psgc_code, 'current versions: ' || count(*) filter (where is_current)
from ordered
group by psgc_code
having count(*) filter (where is_current) <> 1
