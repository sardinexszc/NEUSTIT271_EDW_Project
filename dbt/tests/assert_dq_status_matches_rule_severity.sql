-- A row is 'rejected' if and only if at least one reject-severity rule fired on it
-- (duplicates are removed regardless and are excluded here).
{% set models = ['stg_ndrrmc_damage', 'stg_ndrrmc_lifeline', 'stg_dromic_evacuation', 'stg_dromic_displaced_outside',
                  'stg_ngo_distribution_line', 'stg_lgu_response'] %}
{% set sources = ['ndrrmc', 'ndrrmc', 'dromic', 'dromic', 'ngo', 'lgu'] %}
with rows as (
    {%- for m in models %}
    select '{{ sources[loop.index0] }}' as source_system, _source_file, _row_number,
           {{ 'line_no' if m == 'stg_ngo_distribution_line' else 'null::bigint' }} as line_no,
           dq_issues, dq_status
    from {{ ref(m) }}
    where dq_status <> 'duplicate'
    {{ 'union all' if not loop.last }}
    {%- endfor %}
),
judged as (
    select
        r.*,
        exists (
            select 1 from unnest(r.dq_issues) i
            join {{ ref('dq_rules') }} q
              on q.source_system = r.source_system and q.rule_code = split_part(i, ':', 1)
            where q.severity = 'reject'
        ) as has_reject_issue
    from rows r
)
select *
from judged
where (dq_status = 'rejected') <> has_reject_issue
