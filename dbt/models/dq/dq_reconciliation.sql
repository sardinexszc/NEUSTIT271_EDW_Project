-- Proof that the data-quality layer works: every defect the generator planted
-- (meta.defect_manifest) is compared with what the rules detected in the synthetic extracts.
-- Files submitted through the Data exchange page (origin 'intake') are not part of the proof.

with synthetic_issues as (
    select i.source_system, i.rule_code, count(*) as issue_count
    from {{ ref('dq_issue_log') }} i
    join {{ source('meta', 'load_batch') }} b on b.batch_id = i._batch_id and b.origin = 'synthetic'
    group by 1, 2
),

detected as (
    select r.source_system, r.planted_defect, coalesce(sum(s.issue_count), 0) as detected_count,
           string_agg(r.rule_code, ' + ' order by r.rule_code) as detected_by
    from {{ ref('dq_rules') }} r
    left join synthetic_issues s using (source_system, rule_code)
    where r.planted_defect is not null
    group by 1, 2
)

select
    coalesce(m.source_system, d.source_system)  as source_system,
    coalesce(m.defect, d.planted_defect)        as planted_defect,
    d.detected_by,
    coalesce(m.planted_count, 0)                as planted_count,
    coalesce(d.detected_count, 0)               as detected_count,
    case
        when coalesce(m.planted_count, 0) = coalesce(d.detected_count, 0) then 'match'
        else 'mismatch'
    end                                         as reconciliation_status
from {{ source('meta', 'defect_manifest') }} m
full join detected d on d.source_system = m.source_system and d.planted_defect = m.defect
order by 1, 2
