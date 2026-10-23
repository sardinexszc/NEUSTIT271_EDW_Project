"""Shared paths and database connection for the DRIW ingestion scripts."""

from pathlib import Path
import os

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DIR = ROOT / "data" / "reference"
# overridable so tests can run the pipeline without touching the working copy
SOURCES_DIR = Path(os.environ.get("DRIW_SOURCES_DIR", ROOT / "data" / "sources"))
# files submitted by LGUs and agencies through the Data exchange page (git-ignored: may be real data)
INTAKE_DIR = Path(os.environ.get("DRIW_INTAKE_DIR", ROOT / "data" / "intake"))
MIGRATIONS_DIR = ROOT / "supabase" / "migrations"

load_dotenv(ROOT / ".env")


def connect(autocommit: bool = False, dbname: str | None = None) -> psycopg.Connection:
    """Connect using the standard PG* variables from .env (local Postgres or Supabase).
    `dbname` overrides PGDATABASE (the intake validator uses a separate sandbox database)."""
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=dbname or os.environ["PGDATABASE"],
        sslmode=os.environ.get("PGSSLMODE", "prefer"),
        autocommit=autocommit,
    )
