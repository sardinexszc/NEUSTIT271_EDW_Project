"""Run the DRIW pipeline end to end, or selected steps.

    python ingestion/pipeline.py                  # all steps
    python ingestion/pipeline.py dbt              # only the dbt build
    python ingestion/pipeline.py generate raw dbt # regenerate sources, reload, rebuild

Steps: migrate, reference, psgc, generate, raw, dbt, export
"""

import sys

from dbt.cli.main import dbtRunner

import export_marts
import generate_sources
import load_psgc_api
import load_raw
import load_reference
import migrate
from common import ROOT  # also loads .env, which dbt's profile reads via env_var()

DBT_DIR = str(ROOT / "dbt")


def run_dbt() -> None:
    result = dbtRunner().invoke(["build", "--project-dir", DBT_DIR, "--profiles-dir", DBT_DIR])
    if not result.success:
        raise SystemExit("dbt build failed")


STEPS = {
    "migrate": migrate.main,
    "reference": load_reference.main,
    "psgc": load_psgc_api.main,
    "generate": lambda: generate_sources.generate(seed=271),
    "raw": load_raw.main,
    "dbt": run_dbt,
    "export": export_marts.main,
}


def main(selected: list[str]) -> None:
    unknown = set(selected) - STEPS.keys()
    if unknown:
        raise SystemExit(f"unknown step(s): {', '.join(sorted(unknown))}; choose from {', '.join(STEPS)}")
    for name, step in STEPS.items():
        if not selected or name in selected:
            print(f"\n=== {name} ===")
            step()


if __name__ == "__main__":
    main(sys.argv[1:])
