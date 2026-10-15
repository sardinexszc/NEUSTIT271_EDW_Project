"""Access control: each persona sees exactly what its role allows, and nothing else.

Personas are NOLOGIN roles; tests switch into them with SET ROLE inside a transaction
that is rolled back, so nothing persists.
"""

import psycopg
import pytest
from psycopg import errors

from conftest import scalar

FACTS = ["fact_damage_assessment", "fact_evacuation_snapshot", "fact_resource_distribution", "fact_response_action"]
BICOL, CAGAYAN = "0500000000", "0200000000"


def as_role(db, role):
    db.execute(f"set local role {role}")


def denied(db, sql) -> bool:
    """True if the statement fails with a privilege error (the transaction is rolled back to a savepoint)."""
    db.execute("savepoint probe")
    try:
        db.execute(sql).fetchall()
        db.execute("release savepoint probe")
        return False
    except errors.InsufficientPrivilege:
        db.execute("rollback to savepoint probe")
        return True


def owner_count(db, fact, region=None):
    sql = f"select count(*) from dw.{fact} f join dw.dim_location l using (location_key)"
    return scalar(db, sql + (" where l.region_code = %s" if region else ""), (region,) if region else None)


# ---------------------------------------------------------------- executive

def test_executive_reads_marts_only(db):
    as_role(db, "driw_demo_executive")
    assert scalar(db, "select count(*) from mart.mart_event_summary") == 31
    assert denied(db, "select * from dw.fact_damage_assessment limit 1")
    assert denied(db, "select * from staging.stg_lgu_response limit 1")
    assert denied(db, "select * from raw.lgu_response_log limit 1")
    assert denied(db, "select * from dq.dq_quarantine limit 1")


# ---------------------------------------------------------------- analyst

@pytest.mark.parametrize("fact", FACTS)
def test_analyst_sees_every_fact_row(db, fact):
    expected = owner_count(db, fact)
    as_role(db, "driw_demo_analyst")
    assert scalar(db, f"select count(*) from dw.{fact}") == expected


def test_analyst_reads_marts_and_dq_scorecards_but_not_raw_or_quarantine(db):
    as_role(db, "driw_demo_analyst")
    assert scalar(db, "select count(*) from mart.mart_impact_cube") > 0
    assert scalar(db, "select count(*) from dq.dq_reconciliation") == 19
    assert denied(db, "select * from dq.dq_quarantine limit 1")
    assert denied(db, "select * from raw.ngo_distribution limit 1")


# ---------------------------------------------------------------- regional (row-level security)

@pytest.mark.parametrize("persona,region", [("driw_demo_bicol", BICOL), ("driw_demo_cagayan", CAGAYAN)])
@pytest.mark.parametrize("fact", FACTS)
def test_regional_sees_only_own_region(db, persona, region, fact):
    expected = owner_count(db, fact, region)
    as_role(db, persona)
    visible = scalar(db, f"select count(*) from dw.{fact}")
    assert visible == expected and visible > 0
    other = scalar(db, f"select count(*) from dw.{fact} f join dw.dim_location l using (location_key) "
                       "where l.region_code <> %s", (region,))
    assert other == 0


@pytest.mark.parametrize("persona,region_name", [("driw_demo_bicol", "Bicol Region"), ("driw_demo_cagayan", "Cagayan Valley")])
def test_secure_views_follow_the_callers_region(db, persona, region_name):
    as_role(db, persona)
    regions = {r[0] for r in db.execute("select distinct region_name from secure.regional_event_impact").fetchall()}
    assert regions == {region_name}
    regions = {r[0] for r in db.execute("select distinct region_name from secure.regional_response_summary").fetchall()}
    assert regions == {region_name}


def test_regional_role_without_a_region_sees_nothing(db):
    """Default deny: a regional user not yet mapped to any region gets zero rows, not everything."""
    as_role(db, "driw_regional")
    for fact in FACTS:
        assert scalar(db, f"select count(*) from dw.{fact}") == 0


def test_regional_cannot_read_marts_mapping_or_escalate(db):
    as_role(db, "driw_demo_bicol")
    assert denied(db, "select * from mart.mart_event_summary limit 1")    # cross-region aggregates
    assert denied(db, "select * from governance.region_access")            # who sees what
    assert scalar(db, "select count(*) from governance.my_regions") == 1   # but knows its own
    # cannot widen its own access (SET ROLE is checked against the session user, so the
    # meaningful escalation tests are GRANT and writing the mapping table)
    db.execute("savepoint probe")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("grant driw_analyst to driw_demo_bicol")
    db.execute("rollback to savepoint probe")
    assert denied(db, "insert into governance.region_access (role_name, region_code) "
                      "values ('driw_demo_bicol', '0200000000')")


# ---------------------------------------------------------------- data steward

def test_steward_works_on_source_quality_not_the_warehouse(db):
    as_role(db, "driw_demo_steward")
    assert scalar(db, "select count(*) from raw.ndrrmc_damage_report") > 0
    assert scalar(db, "select count(*) from dq.dq_quarantine") > 0
    assert scalar(db, "select count(*) from staging.stg_location_resolution where match_method = 'unmatched'") >= 0
    assert denied(db, "select * from dw.fact_damage_assessment limit 1")
    assert denied(db, "select * from mart.mart_event_summary limit 1")


def test_steward_can_fix_alias_mappings(db):
    as_role(db, "driw_demo_steward")
    code = scalar(db, "select psgc_code from ref.psgc where name = 'Malinao' and province_name = 'Albay'")
    db.execute("insert into ref.location_alias (alias_name, alias_scope, psgc_code, match_method) "
               "values ('Malniao', 'CityMun', %s, 'manual')", (code,))
    assert scalar(db, "select count(*) from ref.location_alias where alias_name = 'Malniao'") == 1
    # (rolled back by the fixture)


def test_access_matrix_is_documented(db):
    rows = db.execute("select role_name, schema_name, bool_and(can_select) from governance.v_access_matrix "
                      "where schema_name in ('mart', 'dw', 'raw') group by 1, 2").fetchall()
    matrix = {(r[0], r[1]): r[2] for r in rows}
    assert matrix[("driw_executive", "mart")] and not matrix[("driw_executive", "dw")]
    assert matrix[("driw_regional", "dw")] and not matrix[("driw_regional", "mart")]
    assert matrix[("driw_steward", "raw")] and not matrix[("driw_steward", "dw")]
