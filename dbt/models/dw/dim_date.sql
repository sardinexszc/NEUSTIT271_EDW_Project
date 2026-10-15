-- Calendar dimension, 2019-2026, plus a -1 member for milestones that have not happened yet
-- (e.g. the completed date of a response request that is still open).

with days as (
    select d::date as full_date
    from generate_series(date '2019-01-01', date '2026-12-31', interval '1 day') d
)

select
    to_char(full_date, 'YYYYMMDD')::int          as date_key,
    full_date,
    extract(day from full_date)::int             as day_of_month,
    trim(to_char(full_date, 'Day'))              as day_name,
    extract(isodow from full_date)::int          as day_of_week,
    extract(isodow from full_date) in (6, 7)     as is_weekend,
    extract(week from full_date)::int            as iso_week,
    extract(month from full_date)::int           as month_number,
    trim(to_char(full_date, 'Month'))            as month_name,
    to_char(full_date, 'YYYY-MM')                as year_month,
    extract(quarter from full_date)::int         as quarter_number,
    'Q' || extract(quarter from full_date)       as quarter_name,
    extract(year from full_date)::int            as year_number,
    -- most tropical cyclones and the southwest monsoon fall in June-November
    extract(month from full_date) between 6 and 11 as is_typhoon_season
from days

union all

select -1, null, null, 'Not yet occurred', null, null, null, null, 'Not yet occurred', null, null, null, null, null
