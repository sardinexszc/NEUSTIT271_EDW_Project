"""Apply supabase/migrations/*.sql in filename order, once each.

The same files can later be pushed to a Supabase project with `supabase db push`,
so local development and the cloud deployment share one schema history.
"""

from common import MIGRATIONS_DIR, connect


def main() -> None:
    with connect() as conn:
        conn.execute("create schema if not exists meta")
        conn.execute(
            """create table if not exists meta.schema_migration (
                   version    text primary key,
                   applied_at timestamptz not null default now())"""
        )
        applied = {r[0] for r in conn.execute("select version from meta.schema_migration")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.stem in applied:
                continue
            print(f"applying {path.name}")
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute("insert into meta.schema_migration (version) values (%s)", (path.stem,))
        conn.commit()
    print("migrations up to date")


if __name__ == "__main__":
    main()
