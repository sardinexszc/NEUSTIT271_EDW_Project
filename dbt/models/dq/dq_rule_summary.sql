-- Data-quality scorecard: how often each rule fired, against how many source rows.

with row_counts as (
    select 'pagasa' as source_system, count(*) as source_rows from {{ ref('stg_pagasa_event') }}
    union all select 'ndrrmc', count(*) from {{ ref('stg_ndrrmc_damage') }}
    union all select 'dromic', count(*) from {{ ref('stg_dromic_evacuation') }}
    union all select 'ngo', count(*) from {{ ref('stg_ngo_distribution_line') }}
    union all select 'lgu', count(*) from {{ ref('stg_lgu_response') }}
),

fired as (
    select
        source_system,
        rule_code,
        count(*) as issue_count,
        count(distinct (_batch_id, _row_number, line_no)) as affected_rows
    from {{ ref('dq_issue_log') }}
    group by 1, 2
)

select
    r.source_system,
    r.rule_code,
    r.severity,
    r.action,
    r.description,
    coalesce(f.issue_count, 0)   as issue_count,
    coalesce(f.affected_rows, 0) as affected_rows,
    c.source_rows,
    round(100.0 * coalesce(f.affected_rows, 0) / nullif(c.source_rows, 0), 2) as pct_rows_affected
from {{ ref('dq_rules') }} r
left join fired f using (source_system, rule_code)
left join row_counts c using (source_system)
order by r.source_system, case r.severity when 'reject' then 1 when 'warning' then 2 else 3 end, r.rule_code
