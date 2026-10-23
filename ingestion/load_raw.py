"""Extract step: land every file in data/sources/ and data/intake/ into the raw.* tables, untouched.

data/sources/ holds the synthetic source extracts; data/intake/ holds reports that LGUs and
agencies submitted through the Data exchange page (ingestion/intake.py writes them in the same
standard layouts). Each file becomes one meta.load_batch row, marked with its origin; each landed
row keeps its batch id, source file name and row number so any warehouse figure can be traced
back to its origin. This is a full reload: raw tables are emptied first.
"""

import csv
import json
from datetime import date, datetime

from openpyxl import load_workbook

from common import INTAKE_DIR, SOURCES_DIR, connect

RAW_TABLES = ["ndrrmc_damage_report", "ndrrmc_lifeline_status", "dromic_evacuation", "dromic_displaced_outside",
              "ngo_distribution", "pagasa_event", "lgu_response_log"]
DROMIC_COLUMNS = ["report_date", "disaster_name", "region", "province", "municipality", "barangay",
                  "ec_code", "ec_name", "ec_type", "capacity_families", "families_inside", "persons_inside"]
DROMIC_OUTSIDE_COLUMNS = ["report_date", "disaster_name", "region", "province", "municipality",
                          "families_outside", "persons_outside"]


def as_text(v) -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def csv_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, [[r[c] or None for c in reader.fieldnames] for r in reader]


def xlsx_rows(path):
    ws = load_workbook(path, read_only=True).active
    rows = ws.iter_rows(min_row=2, values_only=True)
    return DROMIC_COLUMNS, [[as_text(v) for v in r] for r in rows]


def xlsx_outside_rows(path):
    """Second DROMIC sheet: families displaced outside evacuation centers (absent in older or
    submitted workbooks, which then contribute no rows)."""
    wb = load_workbook(path, read_only=True)
    if "Outside ECs" not in wb.sheetnames:
        return DROMIC_OUTSIDE_COLUMNS, []
    rows = wb["Outside ECs"].iter_rows(min_row=2, values_only=True)
    return DROMIC_OUTSIDE_COLUMNS, [[as_text(v) for v in r] for r in rows]


def json_rows(path):
    records = json.loads(path.read_text(encoding="utf-8"))
    return ["record"], [[json.dumps(r, ensure_ascii=False)] for r in records]


SOURCES = [  # (source system, folder/glob, raw table, reader)
    ("PAGASA", "pagasa/*.csv", "pagasa_event", csv_rows),
    ("NDRRMC", "ndrrmc/*.csv", "ndrrmc_damage_report", csv_rows),
    ("NDRRMC", "ndrrmc/lifelines/*.csv", "ndrrmc_lifeline_status", csv_rows),
    ("DSWD_DROMIC", "dromic/*.xlsx", "dromic_evacuation", xlsx_rows),
    ("DSWD_DROMIC", "dromic/*.xlsx", "dromic_displaced_outside", xlsx_outside_rows),
    ("NGO", "ngo/*.json", "ngo_distribution", json_rows),
    ("LGU", "lgu/*.csv", "lgu_response_log", csv_rows),
]


def main() -> None:
    with connect() as conn:
        conn.execute("truncate " + ", ".join(f"raw.{t}" for t in RAW_TABLES))
        for system, pattern, table, reader in SOURCES:
            files = [(p, "synthetic") for p in sorted(SOURCES_DIR.glob(pattern))]
            if not files:
                raise SystemExit(f"no files for {pattern}; run generate_sources.py first")
            files += [(p, "intake") for p in sorted(INTAKE_DIR.glob(pattern))]
            total = 0
            for path, origin in files:
                columns, rows = reader(path)
                batch_id = conn.execute(
                    "insert into meta.load_batch (source_system, source_file, origin) values (%s, %s, %s) "
                    "returning batch_id",
                    (system, path.name, origin),
                ).fetchone()[0]
                cols = ", ".join(columns + ["_batch_id", "_source_file", "_row_number"])
                with conn.cursor().copy(f"copy raw.{table} ({cols}) from stdin") as copy:
                    for n, row in enumerate(rows, start=1):
                        copy.write_row(row + [batch_id, path.name, n])
                conn.execute(
                    "update meta.load_batch set row_count = %s, finished_at = now(), status = 'succeeded' "
                    "where batch_id = %s",
                    (len(rows), batch_id),
                )
                total += len(rows)
            print(f"raw.{table:<26} {total:>8,} rows from {len(files)} file(s)")

        manifest = json.loads((SOURCES_DIR / "_defect_manifest.json").read_text(encoding="utf-8"))
        conn.execute("truncate meta.defect_manifest")
        for key, count in manifest["planted_defects"].items():
            source, defect = key.split(".", 1)
            conn.execute("insert into meta.defect_manifest (source_system, defect, planted_count, seed) "
                         "values (%s, %s, %s, %s)", (source, defect, count, manifest["seed"]))
        print(f"meta.defect_manifest      {len(manifest['planted_defects']):>8} defect types")
        conn.commit()


if __name__ == "__main__":
    main()
