-- Operations mart: evacuation-center load per event per day (sums across centers only).

select
    e.event_code,
    d.full_date                                   as snapshot_date,
    d.full_date - e.start_date                    as day_of_event,
    count(*)                                      as centers_open,
    sum(f.families_inside)                        as families_inside,
    sum(f.persons_inside)                         as persons_inside,
    sum(f.capacity_families)                      as capacity_families,
    count(*) filter (where f.is_over_capacity)    as centers_over_capacity,
    round(sum(f.families_inside)::numeric / nullif(sum(f.capacity_families), 0), 4) as occupancy_rate
from {{ ref('fact_evacuation_snapshot') }} f
join {{ ref('dim_event') }} e using (event_key)
join {{ ref('dim_date') }} d on d.date_key = f.snapshot_date_key
group by e.event_code, d.full_date, e.start_date
