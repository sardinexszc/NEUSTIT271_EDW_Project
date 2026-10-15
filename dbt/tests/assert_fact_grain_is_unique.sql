-- Each fact table must have exactly one row per its declared grain.
select 'fact_damage_assessment' as fact, count(*) as duplicates
from (select event_key, location_key, damage_category_key from {{ ref('fact_damage_assessment') }}
      group by 1, 2, 3 having count(*) > 1) d
having count(*) > 0
union all
select 'fact_evacuation_snapshot', count(*)
from (select evacuation_center_key, snapshot_date_key, event_key from {{ ref('fact_evacuation_snapshot') }}
      group by 1, 2, 3 having count(*) > 1) d
having count(*) > 0
union all
select 'fact_resource_distribution', count(*)
from (select distribution_id, line_no from {{ ref('fact_resource_distribution') }}
      group by 1, 2 having count(*) > 1) d
having count(*) > 0
