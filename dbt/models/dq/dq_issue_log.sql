-- One row per detected issue: which rule fired, on which raw record (and field / item line).
-- Traceable back to the source file and row through the lineage columns.

with issues as (
    select 'pagasa' as source_system, _batch_id, _source_file, _row_number, null::int as line_no, i as issue
    from {{ ref('stg_pagasa_event') }}, unnest(dq_issues) i

    union all
    select 'ndrrmc', _batch_id, _source_file, _row_number, null, i
    from {{ ref('stg_ndrrmc_damage') }}, unnest(dq_issues) i

    union all
    select 'ndrrmc', _batch_id, _source_file, _row_number, null, i
    from {{ ref('stg_ndrrmc_lifeline') }}, unnest(dq_issues) i

    union all
    select 'dromic', _batch_id, _source_file, _row_number, null, i
    from {{ ref('stg_dromic_evacuation') }}, unnest(dq_issues) i

    union all
    select 'dromic', _batch_id, _source_file, _row_number, null, i
    from {{ ref('stg_dromic_displaced_outside') }}, unnest(dq_issues) i

    -- header issues are repeated on every line of a record; log them once per record
    union all
    select distinct 'ngo', _batch_id, _source_file, _row_number, null::int, i
    from {{ ref('stg_ngo_distribution_line') }}, unnest(header_issues) i

    union all
    select 'ngo', _batch_id, _source_file, _row_number, line_no, i
    from {{ ref('stg_ngo_distribution_line') }}, unnest(line_issues) i

    union all
    select 'lgu', _batch_id, _source_file, _row_number, null, i
    from {{ ref('stg_lgu_response') }}, unnest(dq_issues) i
)

select
    i.source_system,
    split_part(i.issue, ':', 1)                  as rule_code,
    nullif(split_part(i.issue, ':', 2), '')      as field_name,
    r.severity,
    i._batch_id,
    i._source_file,
    i._row_number,
    i.line_no
from issues i
left join {{ ref('dq_rules') }} r
    on r.source_system = i.source_system and r.rule_code = split_part(i.issue, ':', 1)
