"""Load hand-curated master data (organizations, relief items) and their source aliases into ref.*."""

import csv

from common import REFERENCE_DIR, connect


def read_csv(name: str) -> list[dict]:
    with open(REFERENCE_DIR / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    orgs = read_csv("organizations.csv")
    items = read_csv("resource_items.csv")

    with connect() as conn:
        conn.execute("truncate ref.organization_alias, ref.organization, ref.resource_item_alias, ref.resource_item")

        for o in orgs:
            conn.execute(
                "insert into ref.organization values (%s, %s, %s, %s)",
                (o["org_code"], o["org_name"], o["org_type"], o["parent_agency"] or None),
            )
            for alias in o["source_aliases"].split(";"):
                conn.execute(
                    "insert into ref.organization_alias values (%s, %s)",
                    (alias.strip().lower(), o["org_code"]),
                )

        for i in items:
            conn.execute(
                "insert into ref.resource_item values (%s, %s, %s, %s, %s)",
                (i["item_code"], i["item_name"], i["category"], i["standard_unit"], i["unit_cost_php"]),
            )
            # alias format: SOURCE_CODE:source_unit:factor_to_standard_unit
            for alias in i["source_aliases"].split(";"):
                code, unit, factor = alias.split(":")
                conn.execute(
                    "insert into ref.resource_item_alias values (%s, %s, %s, %s)",
                    (code, i["item_code"], unit, factor),
                )
        conn.commit()

    print(f"loaded {len(orgs)} organizations, {len(items)} resource items")


if __name__ == "__main__":
    main()
