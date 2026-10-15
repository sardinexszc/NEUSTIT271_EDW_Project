"""Export the mart layer to JSON for the web dashboards (web/src/data/).

The dashboards are deployed on Vercel, which cannot reach the local PostgreSQL server,
so the marts are published as a static snapshot at build time. Moving the warehouse to
Supabase later only changes web/src/lib/data.ts to query the marts live.
"""

import json
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from common import ROOT, connect

OUT_DIR = Path(os.environ.get("DRIW_EXPORT_DIR", ROOT / "web" / "src" / "data"))
MARTS = [
    "mart_event_summary",
    "mart_impact_cube",
    "mart_province_event_impact",
    "mart_evacuation_daily",
    "mart_response_performance",
    "mart_relief_by_org_category",
]


def to_json(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(type(value))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        for mart in MARTS:
            # order by every column so identical warehouses export byte-identical files
            # (tests/test_end_to_end.py compares the committed snapshot with a fresh build)
            ncols = len(conn.execute(f"select * from mart.{mart} limit 0").description)
            order_by = ", ".join(str(i) for i in range(1, ncols + 1))
            cur = conn.execute(f"select * from mart.{mart} order by {order_by}")
            columns = [c.name for c in cur.description]
            rows = [dict(zip(columns, r)) for r in cur.fetchall()]
            path = OUT_DIR / f"{mart}.json"
            path.write_text(json.dumps(rows, default=to_json, separators=(",", ":")), encoding="utf-8")
            print(f"{mart:<30} {len(rows):>6,} rows  {path.stat().st_size / 1024:>7.1f} KB")
    meta = {"exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "marts": MARTS}
    (OUT_DIR / "export_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
