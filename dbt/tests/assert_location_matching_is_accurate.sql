-- Ground truth: LGU request ids and DROMIC center codes embed the true 7-digit PSGC prefix.
-- Any normalized or fuzzy match that lands on a different place is a false match.
select 'lgu' as source_system, request_id as record_key, psgc_code
from {{ ref('stg_lgu_response') }}
where psgc_code is not null and left(psgc_code, 7) <> left(request_id, 7)
union all
select 'dromic', raw_ec_code, psgc_code
from {{ ref('stg_dromic_evacuation') }}
where psgc_code is not null and raw_ec_code is not null and left(psgc_code, 7) <> substr(raw_ec_code, 4, 7)
