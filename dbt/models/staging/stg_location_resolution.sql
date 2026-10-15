-- Resolves every distinct (province, city/municipality) pair seen in any source to a PSGC code.
-- Match order:  1. exact official name   2. normalized name (case, spacing, "City of", Sto./Sta., ñ)
--               3. fuzzy: Levenshtein distance <= 2, best match must be unique (ties stay unmatched).
--                  Distance is the smallest of: normalized names, letters-only full names, and
--                  letters-only "<name>city" (catches "Tuguegarao Ctiy", "Cityo f Legazpi").
-- Matching is always within the reported province, so same-named towns elsewhere cannot collide.

with official as (
    select
        psgc_code,
        name as official_name,
        province_name,
        {{ norm_name('province_name') }} as province_key,
        {{ norm_name('name') }}          as name_key,
        {{ loose_key('name') }}          as loose_name
    from {{ source('ref', 'psgc') }}
    where geographic_level in ('City', 'Mun')
),

-- normalized keys that point to exactly one place in their province
official_unique as (
    select o.*
    from official o
    join (
        select province_key, name_key
        from official
        group by 1, 2
        having count(*) = 1
    ) u using (province_key, name_key)
),

raw_pairs as (
    select province as raw_province, city_muni as raw_name from {{ source('raw', 'ndrrmc_damage_report') }}
    union
    select province, municipality from {{ source('raw', 'dromic_evacuation') }}
    union
    select record -> 'location' ->> 'province', record -> 'location' ->> 'municipality'
    from {{ source('raw', 'ngo_distribution') }}
    union
    select province, lgu_name from {{ source('raw', 'lgu_response_log') }}
),

keyed as (
    select
        raw_province,
        raw_name,
        {{ norm_name('raw_province') }} as province_key,
        {{ norm_name('raw_name') }}     as name_key,
        {{ loose_key('raw_name') }}     as loose_name
    from raw_pairs
    where raw_name is not null
),

exact_match as (
    select k.raw_province, k.raw_name, o.psgc_code, o.official_name, 'exact' as match_method, 0 as edit_distance
    from keyed k
    join official o on o.province_key = k.province_key and o.official_name = k.raw_name
),

normalized_match as (
    select k.raw_province, k.raw_name, o.psgc_code, o.official_name, 'normalized', 0
    from keyed k
    join official_unique o using (province_key, name_key)
    where not exists (select 1 from exact_match e
                      where e.raw_province = k.raw_province and e.raw_name = k.raw_name)
),

unresolved as (
    select k.*
    from keyed k
    where not exists (select 1 from exact_match e where e.raw_province = k.raw_province and e.raw_name = k.raw_name)
      and not exists (select 1 from normalized_match n where n.raw_province = k.raw_province and n.raw_name = k.raw_name)
),

fuzzy_candidates as (
    select
        u.raw_province,
        u.raw_name,
        o.psgc_code,
        o.official_name,
        least(
            extensions.levenshtein(u.name_key, o.name_key),
            extensions.levenshtein(u.loose_name, o.loose_name),
            extensions.levenshtein(u.loose_name, replace(o.name_key, ' ', '') || 'city')
        ) as edit_distance
    from unresolved u
    join official_unique o on o.province_key = u.province_key
),

fuzzy_ranked as (
    select
        *,
        rank() over (partition by raw_province, raw_name order by edit_distance) as rnk,
        count(*) over (partition by raw_province, raw_name, edit_distance)       as ties
    from fuzzy_candidates
    where edit_distance <= 2
),

fuzzy_match as (
    select raw_province, raw_name, psgc_code, official_name, 'fuzzy', edit_distance
    from fuzzy_ranked
    where rnk = 1 and ties = 1
)

select * from exact_match
union all
select * from normalized_match
union all
select * from fuzzy_match
union all
select u.raw_province, u.raw_name, null, null, 'unmatched', null
from unresolved u
where not exists (select 1 from fuzzy_match f where f.raw_province = u.raw_province and f.raw_name = u.raw_name)
