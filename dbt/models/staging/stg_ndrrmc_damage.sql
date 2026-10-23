{%- set required = {
    'dead': ['Population'], 'injured': ['Population'], 'missing': ['Population'],
    'affected_families': ['Population'], 'affected_persons': ['Population'],
    'houses_partial': ['Housing'], 'houses_total': ['Housing'],
    'cost_php': ['Housing', 'Infrastructure', 'Agriculture'],
} -%}

-- NDRRMC situation-report lines, typed and checked. One row per raw row.
-- Sitreps are cumulative: the fact load keeps only the latest valid sitrep per
-- event x city/municipality x damage category.

with src as (
    select
        r.*,
        row_number() over (
            partition by _source_file, sitrep_no, report_date, incident_name, province, city_muni,
                         damage_category, dead, injured, missing, affected_families, affected_persons,
                         houses_partial, houses_total, cost_php, remarks
            order by _row_number
        ) as copy_number
    from {{ source('raw', 'ndrrmc_damage_report') }} r
),

typed as (
    select
        s._batch_id,
        s._source_file,
        s._row_number,
        s.copy_number,
        {{ clean_int("regexp_replace(s.sitrep_no, '\D', '', 'g')") }} as sitrep_no,
        {{ parse_any_date('s.report_date') }}                     as report_date,
        s.incident_name,
        s.province,
        s.city_muni                                               as raw_city_muni,
        s.damage_category,
        {%- for field in required %}
        {{ clean_number('s.' ~ field) }} as {{ field }},
        {%- endfor %}
        s.remarks,
        {%- for field in required %}
        s.{{ field }} as raw_{{ field }}{{ ',' if not loop.last }}
        {%- endfor %}
    from src s
),

resolved as (
    select
        t.*,
        loc.psgc_code,
        loc.match_method as location_match_method,
        ev.event_key
    from typed t
    left join {{ ref('stg_location_resolution') }} loc
        on loc.raw_province = t.province and loc.raw_name = t.raw_city_muni
    {#- the international name is the LAST parenthesised part: "Southwest Monsoon (Habagat) Carina (Gaemi)" #}
    {{ event_lookup("substring(t.incident_name from '\\(([^)]+)\\)\\s*$')", 't.report_date', 'ev') }}
),

checked as (
    select
        *,
        array_remove(array[
            case when copy_number > 1 then 'NDRRMC_DUPLICATE_ROW' end,
            {%- for field, categories in required.items() %}
            case when damage_category in ('{{ categories | join("', '") }}') and {{ field }} is null
                 then 'MISSING_VALUE:{{ field }}' end,
            case when raw_{{ field }} like '%,%' then 'NUMBER_FORMAT:{{ field }}' end,
            {%- endfor %}
            case when damage_category is null
                   or damage_category not in ('Population', 'Housing', 'Infrastructure', 'Agriculture')
                 then 'DAMAGE_CATEGORY_UNKNOWN' end,
            case when cost_php < 0 then 'NEGATIVE_VALUE' end,
            case when affected_persons < affected_families then 'PERSONS_LT_FAMILIES' end,
            case when location_match_method in ('normalized', 'fuzzy') then 'LOC_NAME_VARIANT' end,
            case when psgc_code is null then 'LOC_UNMATCHED' end,
            case when event_key is null then 'EVENT_UNRESOLVED' end
        ], null) as dq_issues
    from resolved
)

select
    *,
    case
        when copy_number > 1 then 'duplicate'
        else {{ dq_status('dq_issues',
                          ['DAMAGE_CATEGORY_UNKNOWN', 'NEGATIVE_VALUE', 'PERSONS_LT_FAMILIES', 'LOC_UNMATCHED',
                           'EVENT_UNRESOLVED'],
                          ['MISSING_VALUE']) }}
    end as dq_status
from checked
