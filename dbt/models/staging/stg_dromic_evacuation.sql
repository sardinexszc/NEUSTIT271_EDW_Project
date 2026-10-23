-- DSWD DROMIC daily evacuation-center reports, typed and checked. One row per raw row.

with src as (
    select r.*, {{ date_format_of('r.report_date') }} as date_format
    from {{ source('raw', 'dromic_evacuation') }} r
),

-- each field office (workbook) has one habitual date format
dominant_format as (
    select _source_file, mode() within group (order by date_format) as dominant_date_format
    from src
    group by 1
),

typed as (
    select
        s._batch_id,
        s._source_file,
        s._row_number,
        s.report_date                         as raw_report_date,
        s.date_format,
        d.dominant_date_format,
        {{ parse_any_date('s.report_date') }} as report_date,
        trim(s.disaster_name)                 as disaster_name,
        s.province,
        s.municipality                        as raw_municipality,
        trim(s.barangay)                      as barangay,
        nullif(trim(s.ec_code), '')           as raw_ec_code,
        trim(s.ec_name)                       as ec_name,
        trim(s.ec_type)                       as ec_type,
        {{ clean_int('s.capacity_families') }} as capacity_families,
        {{ clean_int('s.families_inside') }}   as families_inside,
        {{ clean_int('s.persons_inside') }}    as persons_inside
    from src s
    join dominant_format d using (_source_file)
),

resolved as (
    select t.*, loc.psgc_code, loc.match_method as location_match_method, ev.event_key
    from typed t
    left join {{ ref('stg_location_resolution') }} loc
        on loc.raw_province = t.province and loc.raw_name = t.raw_municipality
    {{ event_lookup('t.disaster_name', 't.report_date', 'ev') }}
),

-- a center's code can be recovered when the same (place, name, barangay) always carries one code
known_centers as (
    select psgc_code, ec_name, barangay, min(raw_ec_code) as ec_code, count(distinct raw_ec_code) as codes
    from resolved
    where raw_ec_code is not null
    group by 1, 2, 3
),

checked as (
    select
        r.*,
        coalesce(r.raw_ec_code, case when k.codes = 1 then k.ec_code end) as ec_code,
        array_remove(array[
            case when r.date_format is distinct from r.dominant_date_format and r.report_date is not null
                 then 'DATE_FORMAT_INCONSISTENT' end,
            case when r.report_date is null then 'DATE_UNPARSEABLE' end,
            case when r.raw_ec_code is null and k.codes = 1 then 'EC_CODE_IMPUTED' end,
            case when r.raw_ec_code is null and k.codes is distinct from 1 then 'EC_CODE_UNRESOLVED' end,
            case when r.families_inside > r.capacity_families then 'EC_OVER_CAPACITY' end,
            case when r.persons_inside < r.families_inside then 'PERSONS_LT_FAMILIES' end,
            case when r.location_match_method in ('normalized', 'fuzzy') then 'LOC_NAME_VARIANT' end,
            case when r.psgc_code is null then 'LOC_UNMATCHED' end,
            case when r.event_key is null then 'EVENT_UNRESOLVED' end
        ], null) as dq_issues
    from resolved r
    left join known_centers k
        on k.psgc_code = r.psgc_code and k.ec_name = r.ec_name and k.barangay = r.barangay
)

select
    *,
    {{ dq_status('dq_issues',
                 ['DATE_UNPARSEABLE', 'EC_CODE_UNRESOLVED', 'PERSONS_LT_FAMILIES', 'LOC_UNMATCHED', 'EVENT_UNRESOLVED'],
                 ['EC_CODE_IMPUTED', 'EC_OVER_CAPACITY']) }} as dq_status
from checked
