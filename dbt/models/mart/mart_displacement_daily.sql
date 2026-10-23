-- Operations mart: everyone displaced per event per day, inside evacuation centers and outside
-- (with relatives or friends). Sums across places only; both facts are semi-additive over days.

with inside as (
    select event_key, snapshot_date_key, sum(families_inside) as families, sum(persons_inside) as persons
    from {{ ref('fact_evacuation_snapshot') }}
    group by 1, 2
),

outside as (
    select event_key, snapshot_date_key, sum(families_outside) as families, sum(persons_outside) as persons
    from {{ ref('fact_displacement_outside') }}
    group by 1, 2
),

daily as (
    select
        coalesce(i.event_key, o.event_key)                 as event_key,
        coalesce(i.snapshot_date_key, o.snapshot_date_key) as snapshot_date_key,
        coalesce(i.families, 0) as families_inside,
        coalesce(i.persons, 0)  as persons_inside,
        coalesce(o.families, 0) as families_outside,
        coalesce(o.persons, 0)  as persons_outside
    from inside i
    full join outside o using (event_key, snapshot_date_key)
)

select
    e.event_code,
    d.full_date                                    as snapshot_date,
    d.full_date - e.start_date                     as day_of_event,
    x.families_inside,
    x.persons_inside,
    x.families_outside,
    x.persons_outside,
    x.persons_inside + x.persons_outside           as persons_displaced,
    round(x.persons_outside::numeric / nullif(x.persons_inside + x.persons_outside, 0), 4) as share_outside_centers
from daily x
join {{ ref('dim_event') }} e using (event_key)
join {{ ref('dim_date') }} d on d.date_key = x.snapshot_date_key
