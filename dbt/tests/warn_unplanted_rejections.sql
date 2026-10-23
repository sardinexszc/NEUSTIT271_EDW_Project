{{ config(severity='warn') }}
-- With synthetic data every rejection should trace to a planted defect. Reject rules with no
-- planted counterpart (e.g. EVENT_UNRESOLVED) firing usually means a parsing bug in staging,
-- not bad source data -- this caught the "Southwest Monsoon (Habagat) Carina (Gaemi)" bug.
-- Submitted files (origin 'intake') are real-world data and are excluded.
select i.source_system, i.rule_code, count(*) as issue_count
from {{ ref('dq_issue_log') }} i
join {{ source('meta', 'load_batch') }} b on b.batch_id = i._batch_id and b.origin = 'synthetic'
join {{ ref('dq_rules') }} r on r.source_system = i.source_system and r.rule_code = i.rule_code
where r.severity = 'reject' and r.planted_defect is null
group by 1, 2
