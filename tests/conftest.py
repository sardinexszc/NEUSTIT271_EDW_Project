"""Shared fixtures for the end-to-end and governance tests.

By default the whole pipeline (migrations -> reference -> PSGC -> generate -> raw -> dbt ->
export) is run once into a fresh database, `driw_e2e`, with sources and exports written to a
temporary folder, so the working copy and the `driw` database are never touched.

Set DRIW_TEST_DB=<existing database> to skip the rebuild and test that database instead.
"""

import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
E2E_DB = "driw_e2e"

load_dotenv(ROOT / ".env")


def connect(dbname: str, autocommit: bool = False) -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=dbname,
        sslmode=os.environ.get("PGSSLMODE", "prefer"),
        autocommit=autocommit,
    )


@pytest.fixture(scope="session")
def warehouse(tmp_path_factory):
    """Name of a fully built warehouse database plus the folders the pipeline wrote to."""
    existing = os.environ.get("DRIW_TEST_DB")
    if existing:
        return {"db": existing, "export_dir": ROOT / "web" / "src" / "data", "pipeline_output": ""}

    work = tmp_path_factory.mktemp("pipeline")
    export_dir, sources_dir, intake_dir = work / "export", work / "sources", work / "intake"

    with connect("postgres", autocommit=True) as admin:
        admin.execute(f"drop database if exists {E2E_DB} with (force)")
        admin.execute(f"create database {E2E_DB}")

    # submitted files go to a throwaway folder too, so the working copy's data/intake/ is never loaded
    env = {**os.environ, "PGDATABASE": E2E_DB, "DRIW_EXPORT_DIR": str(export_dir), "DRIW_SOURCES_DIR": str(sources_dir),
           "DRIW_INTAKE_DIR": str(intake_dir)}
    result = subprocess.run(
        [PYTHON, str(ROOT / "ingestion" / "pipeline.py")],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0, f"pipeline failed:\n{result.stdout[-4000:]}\n{result.stderr[-4000:]}"
    return {"db": E2E_DB, "export_dir": export_dir, "sources_dir": sources_dir, "intake_dir": intake_dir,
            "pipeline_output": result.stdout, "env": env}


@pytest.fixture
def db(warehouse):
    """A connection as the warehouse owner; rolled back after each test."""
    conn = connect(warehouse["db"])
    yield conn
    conn.rollback()
    conn.close()


def scalar(conn, sql: str, params=None):
    return conn.execute(sql, params).fetchone()[0]
