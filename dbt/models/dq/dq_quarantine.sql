-- Rejected records, held back from the warehouse with the reasons they failed.
-- Data stewards fix them at source (or add an alias in ref.*) and reload.

with rejected as (
    select 'pagasa' as source_system, _batch_id, _source_file, _row_number, null::int as line_no, dq_issues
    from {{ ref('stg_pagasa_event') }} where dq_status = 'rejected'
    union all
    select 'ndrrmc', _batch_id, _source_file, _row_number, null, dq_issues
    from {{ ref('stg_ndrrmc_damage') }} where dq_status = 'rejected'
    union all
    select 'dromic', _batch_id, _source_file, _row_number, null, dq_issues
    from {{ ref('stg_dromic_evacuation') }} where dq_status = 'rejected'
    union all
    select 'ngo', _batch_id, _source_file, _row_number, line_no, dq_issues
    from {{ ref('stg_ngo_distribution_line') }} where dq_status = 'rejected'
    union all
    select 'lgu', _batch_id, _source_file, _row_number, null, dq_issues
    from {{ ref('stg_lgu_response') }} where dq_status = 'rejected'
)

select
    r.source_system,
    r._source_file,
    r._row_number,
    r.line_no,
    (select string_agg(distinct split_part(i, ':', 1), ', ')
     from unnest(r.dq_issues) i
     join {{ ref('dq_rules') }} q
       on q.source_system = r.source_system and q.rule_code = split_part(i, ':', 1)
     where q.severity = 'reject')                  as reject_reasons,
    array_to_string(r.dq_issues, ', ')             as all_issues,
    b.source_system                                as batch_source,
    b.started_at                                   as batch_loaded_at
from rejected r
join {{ source('meta', 'load_batch') }} b on b.batch_id = r._batch_id
