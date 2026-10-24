-- DSWD DROMIC "Outside ECs" sheet: families staying with relatives or friends, per
-- city/municipality per day, typed and checked. One row per raw row.

with typed as (
    select
        _batch_id,
        _source_file,
        _row_number,
        report_date                                 as raw_report_date,
        {{ parse_any_date('report_date') }}         as report_date,
        trim(disaster_name)                         as disaster_name,
        province,
        municipality                                as raw_municipality,
        {{ clean_number('families_outside') }}::int as families_outside,
        {{ clean_number('persons_outside') }}::int  as persons_outside
    from {{ source('raw', 'dromic_displaced_outside') }}
),

resolved as (
    select t.*, loc.psgc_code, loc.match_method as location_match_method, ev.event_key
    from typed t
    left join {{ ref('stg_location_resolution') }} loc
        on loc.raw_province = t.province and loc.raw_name = t.raw_municipality
    {{ event_lookup('t.disaster_name', 't.report_date', 'ev') }}
),

checked as (
    select
        *,
        array_remove(array[
            case when report_date is null then 'DATE_UNPARSEABLE' end,
            case when persons_outside < families_outside then 'PERSONS_LT_FAMILIES' end,
            case when location_match_method in ('normalized', 'fuzzy') then 'LOC_NAME_VARIANT' end,
            case when psgc_code is null then 'LOC_UNMATCHED' end,
            case when event_key is null then 'EVENT_UNRESOLVED' end
        ], null) as dq_issues
    from resolved
)

select
    *,
    {{ dq_status('dq_issues',
                 ['DATE_UNPARSEABLE', 'PERSONS_LT_FAMILIES', 'LOC_UNMATCHED', 'EVENT_UNRESOLVED'],
                 []) }} as dq_status
from checked
