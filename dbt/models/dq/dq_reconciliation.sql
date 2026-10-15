-- Proof that the data-quality layer works: every defect the generator planted
-- (meta.defect_manifest) is compared with what the rules detected.

with detected as (
    select r.source_system, r.planted_defect, sum(s.issue_count) as detected_count,
           string_agg(r.rule_code, ' + ' order by r.rule_code) as detected_by
    from {{ ref('dq_rules') }} r
    join {{ ref('dq_rule_summary') }} s using (source_system, rule_code)
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
