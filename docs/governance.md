# Governance and Access Control

Who may see what in DRIW, how it is enforced inside PostgreSQL, and how it is tested.
Everything is enforced by the database itself, so it holds for any client: dashboards,
SQL tools, BI software or scripts.

## Roles

Access is granted to **group roles** that describe a job. People (or service accounts)
are made members of a group; nobody is granted on objects directly.

| Role | Stakeholder (proposal §4.1) | Can read | Cannot read |
|---|---|---|---|
| `driw_executive` | Executive leadership | `mart.*` aggregates | warehouse detail, staging, raw, quarantine |
| `driw_analyst` | Data analysts | `dw.*` (all rows), `mart.*`, `secure.*`, DQ scorecards (`dq_rule_summary`, `dq_reconciliation`) | raw, staging, quarantine |
| `driw_regional` | Operational managers in a region | `dw.*` and `secure.*`, **only rows in their own region(s)** | marts (cross-region), other regions, the region mapping |
| `driw_steward` | Support staff / data engineers | `raw`, `staging`, `ref`, `meta`, all of `dq` incl. quarantine; may edit alias maps in `ref` | `dw`, `mart` |

This follows **least privilege**: executives see conclusions, analysts see detail,
regional officers see their own area, and stewards work on data quality without
browsing the finished warehouse.

Demo personas used in tests and the presentation (NOLOGIN, used with `SET ROLE`):
`driw_demo_executive`, `driw_demo_analyst`, `driw_demo_bicol`, `driw_demo_cagayan`,
`driw_demo_steward`.

## Row-level security (regional users)

`governance.region_access` maps a role to the region(s) it may see:

| role_name | region_code | region |
|---|---|---|
| driw_demo_bicol | 0500000000 | Bicol Region |
| driw_demo_cagayan | 0200000000 | Cagayan Valley |

Each fact table has row-level security enabled with two policies
([`dbt/macros/row_security.sql`](../dbt/macros/row_security.sql)):

```sql
create policy analyst_all_rows on dw.fact_damage_assessment
    for select to driw_analyst using (true);

create policy regional_own_region on dw.fact_damage_assessment
    for select to driw_regional
    using (location_key in (
        select l.location_key from dw.dim_location l
        where l.region_code in (select region_code from governance.my_regions)));
```

- **Default deny.** A regional user not yet mapped to a region sees zero rows, not everything.
- **The mapping stays private.** `governance.my_regions` is a view that shows each user only
  their own regions. Inside a view `current_user` is the querying user, while the view reads
  the mapping table with its owner's rights. A `SECURITY DEFINER` function was tried first and
  rejected: inside one, `current_user` is the function's owner, so no user ever matched (the
  governance tests caught this).
- **Secure views inherit it.** The views in `secure` (`regional_event_impact`,
  `regional_response_summary`) are `security_invoker`, so the same view shows Bicol to the
  Bicol officer, Cagayan Valley to the Cagayan officer, and everything to an analyst.
- **Marts are excluded on purpose.** Materialized views cannot carry row-level security, so
  regional users are not granted the marts; the secure views serve them instead.

Granting a new regional officer:

```sql
grant driw_regional to new_officer;
insert into governance.region_access (role_name, region_code) values ('new_officer', '0800000000');
```

## Surviving rebuilds

dbt rebuilds tables on every run, which would normally drop privileges. Grants are declared
in [`dbt_project.yml`](../dbt/dbt_project.yml) (`+grants`) and row-level security is a
post-hook on each fact, so both are re-applied on every build. The end-to-end tests run a
second `dbt build` and check that policies and grants are still in place.

## Auditing access

`governance.v_access_matrix` lists, for every role and every object, whether the role can
actually read it (schema `USAGE` and object `SELECT`) and whether row-level security
applies. It is the access matrix above, generated from the database itself:

```sql
select role_name, schema_name, count(*) filter (where can_select) as readable, count(*) as objects
from governance.v_access_matrix group by 1, 2 order by 1, 2;
```

## Supabase

The same migrations run on Supabase. There, signed-in users connect as Supabase's
`authenticated` role, so the regional mapping would key on the user's id (`auth.uid()`)
or a JWT claim instead of `current_user`; the policies keep the same shape.

## Standards alignment

This supports the UNDRR Data Strategy and Roadmap 2023–2027 emphasis on data governance:
defined roles and responsibilities (stewardship), controlled access to sensitive
operational data (casualties by locality), and auditable, reproducible data handling.
