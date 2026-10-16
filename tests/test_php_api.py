"""The PHP back-end (web/php/api) serves the marts exactly as the warehouse holds them,
connects with least privilege, and rejects bad requests.

Runs PHP's built-in server against the e2e warehouse. Skipped where PHP with pdo_pgsql is not
installed (e.g. CI) or the web role has no password yet (run ingestion/setup_web_role.py).
"""

import json
import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request

import psycopg
import pytest
from psycopg import errors

from conftest import ROOT

MARTS = ["mart_event_summary", "mart_impact_cube", "mart_province_event_impact",
         "mart_evacuation_daily", "mart_response_performance", "mart_relief_by_org_category"]


def php_binary():
    for candidate in (os.environ.get("DRIW_PHP"), r"C:\xampp\php\php.exe", shutil.which("php")):
        if candidate and os.path.exists(candidate):
            modules = subprocess.run([candidate, "-m"], capture_output=True, text=True).stdout
            if "pdo_pgsql" in modules:
                return candidate
    return None


@pytest.fixture(scope="module")
def api(warehouse, tmp_path_factory):
    php = php_binary()
    password = os.environ.get("DRIW_WEB_PASSWORD")
    if not php or not password:
        pytest.skip("needs PHP with pdo_pgsql and DRIW_WEB_PASSWORD (run ingestion/setup_web_role.py)")

    config = tmp_path_factory.mktemp("php") / "config.php"
    config.write_text(
        "<?php return ['host' => '%s', 'port' => %s, 'dbname' => '%s', 'user' => 'driw_web', 'password' => '%s'];"
        % (os.environ["PGHOST"], os.environ.get("PGPORT", "5432"), warehouse["db"], password),
        encoding="utf-8",
    )
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = subprocess.Popen(
        [php, "-S", f"127.0.0.1:{port}", "-t", str(ROOT / "web" / "php")],
        env={**os.environ, "DRIW_CONFIG": str(config)},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}/api/"
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "health.php", timeout=1)
            break
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.1)
    yield {"base": base, "warehouse": warehouse, "password": password}
    server.terminate()


def get(api, path):
    try:
        with urllib.request.urlopen(api["base"] + path, timeout=10) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def test_health_reports_the_read_only_role(api):
    status, body = get(api, "health.php")
    assert status == 200 and body["role"] == "driw_web" and body["database"] == api["warehouse"]["db"]


@pytest.mark.parametrize("mart", MARTS)
def test_api_returns_exactly_what_the_snapshot_export_writes(api, mart):
    """Same rows, types and order as ingestion/export_marts.py, so the dashboards can use either."""
    status, rows = get(api, f"marts.php?name={mart}")
    exported = json.loads((api["warehouse"]["export_dir"] / f"{mart}.json").read_text(encoding="utf-8"))
    assert status == 200 and rows == exported


def test_event_filter(api):
    status, rows = get(api, "marts.php?name=mart_evacuation_daily&event=TC2024-KRISTINE")
    assert status == 200 and rows and {r["event_code"] for r in rows} == {"TC2024-KRISTINE"}


@pytest.mark.parametrize("path", [
    "marts.php?name=pg_user",                                   # not an allowed mart
    "marts.php?name=mart_event_summary%3Bdrop%20table%20x",     # injection attempt
    "marts.php?name=mart_impact_cube&event=TC2024-KRISTINE",    # mart without event_code
    "marts.php?name=mart_event_summary&event=x%27%3B--",        # malformed event
])
def test_bad_requests_are_rejected(api, path):
    status, body = get(api, path)
    assert status == 400 and "error" in body


def test_web_role_cannot_read_beyond_the_marts(api):
    """Least privilege: even with its own password, the web role sees no detail or raw data."""
    with psycopg.connect(host=os.environ["PGHOST"], port=os.environ.get("PGPORT", "5432"),
                         dbname=api["warehouse"]["db"], user="driw_web", password=api["password"]) as conn:
        for table in ["dw.fact_damage_assessment", "raw.lgu_response_log", "dq.dq_quarantine"]:
            with pytest.raises(errors.InsufficientPrivilege):
                conn.execute(f"select 1 from {table} limit 1")
            conn.rollback()
