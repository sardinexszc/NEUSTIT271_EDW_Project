-- Typhoon Paeng (Oct 2022) struck after the Maguindanao split (Sep 2022): its damage in the
-- former province must roll up to Maguindanao del Norte / del Sur, not "Maguindanao".
select l.psgc_code, l.city_muni_name, l.province_name
from {{ ref('fact_damage_assessment') }} f
join {{ ref('dim_location') }} l using (location_key)
join {{ ref('dim_event') }} e using (event_key)
where e.event_code = 'TC2022-PAENG'
  and l.psgc_code like '19038%'
  and l.province_name not in ('Maguindanao del Norte', 'Maguindanao del Sur')
