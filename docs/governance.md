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

### The web back-end's login

The PHP API (`web/php/api`, served by XAMPP) connects as `driw_web`, a LOGIN role whose only
membership is `driw_executive`. A bug or an injection in the web tier can therefore reach the
aggregated marts but never warehouse detail, raw data or quarantine (tested in
`tests/test_php_api.py`). It also has a 10-second statement timeout and a 20-connection limit.
Its password lives only in the git-ignored `.env` and in a PHP config outside the web root
(`C:\xampp\driw-config\config.php`), both written by `ingestion/setup_web_role.py`.

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

## Privacy

The governing law is the **Data Privacy Act of 2012 (Republic Act 10173)** and its implementing
rules. DRIW is designed so that it holds no personal information at all.

**Data classification**

| Class | Examples in DRIW | Handling |
|---|---|---|
| Public | Event names and dates, PSGC geography, organization names | No restriction |
| Internal (aggregated operational) | Damage costs, relief values, response times | Role-based access (Executive, Analyst) |
| Sensitive (aggregated) | Deaths, injured, missing, persons in evacuation centers, by city/municipality | Analysts and the region's own officers only (row-level security); executives see marts only |
| Personal information | Names, addresses, contact details or health data of affected people or responders | **Not collected.** Never enters the warehouse. |

**Privacy principles applied**

- **Data minimization.** Sources are reduced to counts at the lowest level the analysis needs
  (city/municipality, evacuation center, request). No evacuee rosters, victim lists or patient
  records are loaded; a response request carries a request id, type, timestamps and team size,
  never the requester's identity.
- **Aggregation and small counts.** Casualty figures are aggregated per city/municipality and
  event. Before any public release, counts below 5 should be suppressed or rounded to prevent
  re-identification in small barangays (a reporting rule for published outputs).
- **Purpose limitation.** Data is used only for disaster-response analysis and planning, as
  stated in the business case.
- **Least privilege and need to know.** Four roles; regional officers see only their region;
  the web back-end logs in as `driw_web`, which can read only aggregated marts.
- **Security of processing.** Credentials are never in source code (git-ignored `.env`, PHP
  config outside the web root); the API accepts only allow-listed, validated GET requests; all
  access is enforced inside PostgreSQL, so it holds for every client.
- **Retention.** Raw extracts are replaced on every load (full reload). Warehouse history is kept
  for the analysis period (2020 onwards); source files under `data/sources/` are regenerable and
  not retained in version control.
- **Transparency.** Every published figure is traceable to its source file and row (lineage), and
  every rejected row is kept with its reasons (quarantine).
- **Synthetic data.** In this implementation all operational figures are synthetic; no real
  person's data was processed at any stage.

**If real data is onboarded:** sign data-sharing agreements with each agency, register the
processing with the National Privacy Commission where required, appoint a data protection
officer, run a privacy impact assessment, and enable PostgreSQL connection and statement logging
(`log_connections`, `pgaudit`) for an access audit trail.

## Supabase

The same migrations run on Supabase. There, signed-in users connect as Supabase's
`authenticated` role, so the regional mapping would key on the user's id (`auth.uid()`)
or a JWT claim instead of `current_user`; the policies keep the same shape.

## Standards alignment

This supports the UNDRR Data Strategy and Roadmap 2023–2027 emphasis on data governance:
defined roles and responsibilities (stewardship), controlled access to sensitive
operational data (casualties by locality), and auditable, reproducible data handling.
