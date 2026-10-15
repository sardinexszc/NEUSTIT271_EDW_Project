-- Each raw (province, name) pair must resolve to exactly one row, or staging rows would multiply.
select raw_province, raw_name, count(*)
from {{ ref('stg_location_resolution') }}
group by 1, 2
having count(*) > 1
