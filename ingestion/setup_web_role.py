"""Create the database login used by the PHP back-end, and write its PHP config.

The web back-end connects as `driw_web`, a member of `driw_executive` only: it can read the
aggregated marts and nothing else (no star-schema detail, staging, raw data or quarantine).

    python ingestion/setup_web_role.py              # config -> C:\\xampp\\driw-config\\config.php
    XAMPP_ROOT=D:\\xampp python ingestion/setup_web_role.py

The password is generated once and kept in .env as DRIW_WEB_PASSWORD (git-ignored).
The config is written OUTSIDE htdocs, so Apache can never serve it.
"""

import os
import secrets
from pathlib import Path

from psycopg import sql

from common import ROOT, connect

ROLE = "driw_web"
XAMPP_ROOT = Path(os.environ.get("XAMPP_ROOT", r"C:\xampp"))
CONFIG_PATH = XAMPP_ROOT / "driw-config" / "config.php"


def web_password() -> str:
    password = os.environ.get("DRIW_WEB_PASSWORD")
    if not password:
        password = secrets.token_urlsafe(24)  # letters, digits, - and _ only: safe inside PHP quotes
        with open(ROOT / ".env", "a", encoding="utf-8") as env:
            env.write(f"\n# Login for the PHP back-end (role {ROLE}); written by setup_web_role.py\n"
                      f"DRIW_WEB_PASSWORD={password}\n")
        print(f"generated a password for {ROLE} and saved it to .env")
    return password


def main() -> None:
    password = web_password()
    with connect(autocommit=True) as conn:
        exists = conn.execute("select 1 from pg_roles where rolname = %s", (ROLE,)).fetchone()
        verb = "alter" if exists else "create"
        conn.execute(sql.SQL(verb + " role {} login password {}").format(sql.Identifier(ROLE), sql.Literal(password)))
        conn.execute(sql.SQL("grant driw_executive to {}").format(sql.Identifier(ROLE)))
        # a runaway dashboard query must not tie up the warehouse
        conn.execute(sql.SQL("alter role {} set statement_timeout = '10s'").format(sql.Identifier(ROLE)))
        conn.execute(sql.SQL("alter role {} connection limit 20").format(sql.Identifier(ROLE)))
    print(f"role {ROLE}: {verb}d, member of driw_executive (marts only)")

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        "<?php\n"
        "// Written by ingestion/setup_web_role.py. Kept outside htdocs so Apache never serves it.\n"
        "return [\n"
        f"    'host' => '{os.environ.get('PGHOST', 'localhost')}',\n"
        f"    'port' => {int(os.environ.get('PGPORT', '5432'))},\n"
        f"    'dbname' => '{os.environ['PGDATABASE']}',\n"
        f"    'user' => '{ROLE}',\n"
        f"    'password' => '{password}',\n"
        "];\n",
        encoding="utf-8",
    )
    print(f"PHP config written to {CONFIG_PATH}")


if __name__ == "__main__":
    main()
