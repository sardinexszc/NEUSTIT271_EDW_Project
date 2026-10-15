-- Governance and access control.
--
-- Group roles (what a job needs):
--   driw_executive  aggregated marts only
--   driw_analyst    star schema + marts + data-quality scorecards
--   driw_regional   star schema rows for their own region(s) only (row-level security)
--   driw_steward    raw, staging, reference data and quarantine; may fix alias mappings
--
-- Demo personas (NOLOGIN) belong to the groups and are used with SET ROLE in tests and
-- demonstrations, so no passwords exist. In production, real login users or Supabase
-- authenticated users would be granted the group roles instead.
--
-- Grants on dbt-built objects (staging, dq, dw, mart, secure) are applied by dbt on every
-- build (see `grants` in dbt_project.yml); this migration covers schemas and the tables
-- dbt does not manage.

do $$
declare
    r text;
begin
    foreach r in array array['driw_executive', 'driw_analyst', 'driw_regional', 'driw_steward'] loop
        if not exists (select 1 from pg_roles where rolname = r) then
            execute format('create role %I nologin', r);
        end if;
    end loop;
end $$;

do $$
declare
    p record;
begin
    for p in select * from (values
        ('driw_demo_executive', 'driw_executive'),
        ('driw_demo_analyst',   'driw_analyst'),
        ('driw_demo_bicol',     'driw_regional'),
        ('driw_demo_cagayan',   'driw_regional'),
        ('driw_demo_steward',   'driw_steward')
    ) as t(persona, grp) loop
        if not exists (select 1 from pg_roles where rolname = p.persona) then
            execute format('create role %I nologin', p.persona);
        end if;
        execute format('grant %I to %I', p.grp, p.persona);
    end loop;
end $$;

create schema if not exists governance;
create schema if not exists secure;   -- region-scoped views for regional users (built by dbt)

-- Which region(s) each regional user may see.
create table if not exists governance.region_access (
    role_name    text     not null,
    region_code  char(10) not null,
    granted_by   text     not null default current_user,
    granted_at   timestamptz not null default now(),
    primary key (role_name, region_code)
);
insert into governance.region_access (role_name, region_code) values
    ('driw_demo_bicol',   '0500000000'),   -- Bicol Region
    ('driw_demo_cagayan', '0200000000')    -- Cagayan Valley
on conflict do nothing;

-- Regions the current user may see. A view (not a SECURITY DEFINER function): inside a
-- view current_user is the querying user, while the view reads the mapping table with its
-- owner's rights. Regional users can therefore see their own regions but not the mapping.
create or replace view governance.my_regions with (security_barrier = true) as
select region_code from governance.region_access where role_name = current_user;

-- Schema access per group role.
grant usage on schema mart       to driw_executive, driw_analyst;
grant usage on schema dw         to driw_analyst, driw_regional;
grant usage on schema secure     to driw_regional, driw_analyst;
grant usage on schema dq         to driw_analyst, driw_steward;
grant usage on schema staging, raw, ref, meta to driw_steward;
grant usage on schema governance to driw_executive, driw_analyst, driw_regional, driw_steward;
grant select on governance.my_regions to driw_regional, driw_analyst;

-- Tables loaded by Python (not dbt): stewards read them; future tables included.
grant select on all tables in schema raw, ref, meta to driw_steward;
alter default privileges in schema raw, ref, meta grant select on tables to driw_steward;
-- Stewards maintain the alias maps that fix recurring data-quality issues.
grant insert, update, delete on ref.location_alias, ref.organization_alias, ref.resource_item_alias to driw_steward;
grant select on governance.region_access to driw_steward;

-- Effective access, for documentation and audits: a role can read an object only if it
-- has USAGE on the schema and SELECT on the object.
create or replace view governance.v_access_matrix as
select
    r.rolname   as role_name,
    n.nspname   as schema_name,
    c.relname   as object_name,
    case c.relkind when 'r' then 'table' when 'v' then 'view' when 'm' then 'materialized view' end as object_type,
    has_schema_privilege(r.rolname, n.oid, 'USAGE') and has_table_privilege(r.rolname, c.oid, 'SELECT') as can_select,
    c.relrowsecurity as row_level_security
from pg_roles r
cross join pg_class c
join pg_namespace n on n.oid = c.relnamespace
where r.rolname in ('driw_executive', 'driw_analyst', 'driw_regional', 'driw_steward')
  and n.nspname in ('raw', 'ref', 'meta', 'staging', 'dq', 'dw', 'mart', 'secure', 'governance')
  and c.relkind in ('r', 'v', 'm');
grant select on governance.v_access_matrix to driw_executive, driw_analyst, driw_steward;
