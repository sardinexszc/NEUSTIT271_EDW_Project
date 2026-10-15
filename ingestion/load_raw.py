"""Extract step: land every file in data/sources/ into the raw.* tables, untouched.

Each file becomes one meta.load_batch row; each landed row keeps its batch id, source
file name and row number so any warehouse figure can be traced back to its origin.
This is a full reload: raw tables are emptied first.
"""

import csv
import json
from datetime import date, datetime

from openpyxl import load_workbook

from common import SOURCES_DIR, connect

RAW_TABLES = ["ndrrmc_damage_report", "dromic_evacuation", "ngo_distribution", "pagasa_event", "lgu_response_log"]
DROMIC_COLUMNS = ["report_date", "disaster_name", "region", "province", "municipality", "barangay",
                  "ec_code", "ec_name", "ec_type", "capacity_families", "families_inside", "persons_inside"]


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


def json_rows(path):
    records = json.loads(path.read_text(encoding="utf-8"))
    return ["record"], [[json.dumps(r, ensure_ascii=False)] for r in records]


SOURCES = [  # (source system, folder/glob, raw table, reader)
    ("PAGASA", "pagasa/*.csv", "pagasa_event", csv_rows),
    ("NDRRMC", "ndrrmc/*.csv", "ndrrmc_damage_report", csv_rows),
    ("DSWD_DROMIC", "dromic/*.xlsx", "dromic_evacuation", xlsx_rows),
    ("NGO", "ngo/*.json", "ngo_distribution", json_rows),
    ("LGU", "lgu/*.csv", "lgu_response_log", csv_rows),
]


def main() -> None:
    with connect() as conn:
        conn.execute("truncate " + ", ".join(f"raw.{t}" for t in RAW_TABLES))
        for system, pattern, table, reader in SOURCES:
            files = sorted(SOURCES_DIR.glob(pattern))
            if not files:
                raise SystemExit(f"no files for {pattern}; run generate_sources.py first")
            total = 0
            for path in files:
                columns, rows = reader(path)
                batch_id = conn.execute(
                    "insert into meta.load_batch (source_system, source_file) values (%s, %s) returning batch_id",
                    (system, path.name),
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
            print(f"raw.{table:<22} {total:>8,} rows from {len(files)} file(s)")
        conn.commit()


if __name__ == "__main__":
    main()
