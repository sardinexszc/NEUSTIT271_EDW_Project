{{ config(severity='warn') }}
-- With synthetic data every rejection should trace to a planted defect. Reject rules with no
-- planted counterpart (e.g. EVENT_UNRESOLVED) firing usually means a parsing bug in staging,
-- not bad source data -- this caught the "Southwest Monsoon (Habagat) Carina (Gaemi)" bug.
select s.source_system, s.rule_code, s.issue_count
from {{ ref('dq_rule_summary') }} s
join {{ ref('dq_rules') }} r using (source_system, rule_code)
where r.severity = 'reject' and r.planted_defect is null and s.issue_count > 0
